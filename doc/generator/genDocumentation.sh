#!/bin/bash
# This file is protected by Copyright. Please refer to the COPYRIGHT file
# distributed with this source distribution.
#
# This file is part of OpenCPI <http://www.opencpi.org>
#
# OpenCPI is free software: you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# OpenCPI is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.

# Generate PDFs from all tex and odt files.
# This script will generate all PDFs using makepdf.sh and then makepdf.sh will
# call optpdf.sh to shrink the size of the files. All three of these .sh files
# should be located in the same directory.

###
# Sends help message to STDERR
# Globals:
#   None
# Arguments:
#   $1: Error string to print before help (optional)
# Returns:
#   Ends script with success or failure depending on $1 presence
###
function show_help {
  local msg="$1"
  enable_color
  [ -n "$msg" ] && printf "\n${RED}ERROR: %s\n\n${RESET}" "$msg"
  cat <<EOF >&2
This genDocumentation script creates PDFs for OpenCPI.
Usage: $(basename "$0") [-h] [-r] [-o] [-d]

  -r / --repopath          Use the repo location provided
  -o / --outputpath        Use the provided location for output
  -d / --dirsearch         Instead of using our automatic directory list to search
                             for documents to build, provide your own. If you want
                             to provide more than one directory, provide them as a
                             space separated string. Note that it will only look in
                             subdirectories named 'doc[s]' within the given path(s).
  -h / --help              Display the help screen
EOF
  [ -n "$msg" ] && exit 1
  exit 0
}

# Enables color variables BOLD, RED, and RESET
function enable_color {
  if [[ -n "$(command -v tput)" && -n "${TERM}" ]]; then
    export BOLD="$(tput bold 2>/dev/null)"
    export RED="${BOLD}$(tput setaf 1 2>/dev/null)"
    export RESET="$(tput sgr0 2>/dev/null)"
  fi
}

###
# Creates PDF from LaTeX source
# Globals:
#   OUTPUT_PATH - The path where the PDFs are
# Arguments:
#   $1: path to doc
#   $2: output prefix
#   $3: log directory
# Returns:
#   Nothing
###
function tex_kernel {
  local doc="$1"
  local prefix="$2"
  local log_dir="$3"
  local fail=0

  # Skip these items
  [[ "${doc}" == */snippets/* ]] && return

  echo "${BOLD}LaTeX: ${doc} (output prefix=${prefix})${RESET}"

  # Go into subdir if present
  pushd "$(dirname "${doc}")" > /dev/null || return

  # Get name of file, removing extension
  local ofile="${doc##*/}"
  ofile="${ofile%.*}"

  # Convert to PDF
  [ -f Makefile ] && make
  rubber -d "${doc}" || fail=1
  if [[ ! -f "${ofile}.pdf" || "${fail}" = 1 ]]; then
    echo "${RED}Error creating ${ofile}.pdf${RESET}"
    echo "Error creating ${ofile}.pdf (${doc})" >> "${OUTPUT_PATH}/errors.log"
    rubber-info --errors "${doc}" >> "${OUTPUT_PATH}/errors.log"
    return
  fi

  # Generate some log output
  rubber-info --boxes "${doc}" >> "${log_dir}/${ofile}_boxes.log" 2>&1
  rubber-info --check "${doc}" >> "${log_dir}/${ofile}_warnings.log" 2>&1
  rubber-info --warnings "${doc}" >> "${log_dir}/${ofile}_warnings.log" 2>&1
  mv -f "${ofile}.log" "${log_dir}/${ofile}.log"

  # Clean up
  rm -f "${ofile}".{aux,out,log,lof,lot,toc,dvi,synctex.gz}

  # Move PDF to output location
  mv "${ofile}.pdf" "${OUTPUT_PATH}/${prefix}/"

  popd > /dev/null || return
}

###
# Creates PDF from msoffice or libreoffice source
# Globals:
#   OUTPUT_PATH - The path where the PDFs are
# Arguments:
#   $1: path to doc
#   $2: output prefix
#   $3: log directory
# Returns:
#   Nothing
###
function office_kernel {
  local doc="$1"
  local prefix="$2"
  local log_dir="$3"
  local rv=0

  echo "${BOLD}office: ${doc} (output prefix=${prefix})${RESET}"

  # Get name of file, removing extension
  local ofile="${doc##*/}"
  ofile="${ofile%.*}"

  echo 'Removing tracked changes'
  cp "${doc}" "${doc}.orig"  # save original file to restore later (way easier, trust me)
  "${REMOVE_TRACKED_CHANGES_PY}" "${doc}"

  # Tutorials produce two different pdfs, one for cli and one for gui
  echo 'Creating PDF'
  if [ "${prefix}" = tutorials ]; then
    bash "${GEN_CG_PDFS_SH}" "${doc}" "${doc%/*}" >> "${log_dir}/${ofile}.log" 2>&1
    rv=$?
  else
    unoconv -vvv "${doc}" >> "${log_dir}/${ofile}.log" 2>&1
    rv=$?
  fi
  mv -f "${doc}.orig" "${doc}"  # restore original file

  # If the pdf was created then copy it out
  if [ "${rv}" = 0 ]; then
    # The *.pdf is needed because the tutorial pdfs have a *_CLI.pdf
    # and *_GUI.pdf suffix
    mv ./*.pdf "${OUTPUT_PATH}/${prefix}"
  else
    echo "${RED}Error creating ${ofile}.pdf${RESET}"
    echo "Error creating ${ofile}.pdf (${d})" >> "${OUTPUT_PATH}/errors.log"
  fi
}

###
# Main workhorse function
# Convert docs to PDFs
# Globals:
#   MYLOC - The path of the directory that contains this script
#   OUTPUT_PATH - The path where the PDFs are to be written
#   REPO_PATH - The path where the opencpi repo is located
# Arguments:
#   $1: If $1 is provided it means we want to use our own search path for
#       dirs_to_search instead of the provided ones we use
# Returns:
#   None - Some stuff will be returned but it is all garbage and should not be
#          used.
###
function generate_pdfs {
  shopt -s nullglob
  local search_path="$1"
  local dirs_to_search=()

  if [ -z "$search_path" ]; then
    echo "${BOLD}Building PDFs from '${REPO_PATH}' with results in '${OUTPUT_PATH}'${RESET}"
    #
    # Skip directories under "${REPO_PATH}/doc" that do not exist.
    # The "tex" subdirectory went away when the old GUI user guide
    # was deleted.
    #
    for d in "briefings" "av/tex" "reference" "tex" "tutorials"; do
      if [ -e "${REPO_PATH}/doc/${d}" ]; then
        dirs_to_search+=("${REPO_PATH}/doc/${d}")
      fi
    done

    #
    # Loop over projects, skipping inactive
    #
    # FIXME: OTHERs (other projects) require special
    # handling because they are not in the "projects"
    # directory as OSPs and COMPs are.  Note that we
    # we do not treat COMPs in a manner similar to OSPs,
    # mostly because COMPs docs are in RST format only.
    #
    mapfile -t < <(find "${REPO_PATH}/projects" \
      -mindepth 1 -maxdepth 1 -type d ; \
      echo "${REPO_PATH}/ie-gui")
    for proj in "${MAPFILE[@]}"; do
      #
      # Must check for existence of project
      # because of OTHERs being hard-coded.
      #
      if [ -e "${proj}" ]; then
        case "$(basename "${proj}")" in
          inactive) continue ;;
          *) ;;
        esac
        mapfile -t < <(find "${proj}" -type d \( -name doc -o -name docs \))
        dirs_to_search+=("${MAPFILE[@]}")
      fi
    done
  else # given directories to search
    local tmp_array=("$search_path")
    for dir in "${tmp_array[@]}"; do
      if [ -e "$dir" ]; then
        # Code elsewhere requires absolute paths, like REPO_PATH is above
        mapfile -t dirs_to_search < <(find "$(readlink -e "${dir}")" \
          -type d \( -name doc -o -name docs \) -printf '%p\n')
      else
        echo "${RED}Error: provided directory: $dir does not exist${RESET}"
      fi
    done
  fi

  # There is a bug with unoconv where it doesn't work the first time it is
  # ran so we kick start it here
  # https://github.com/dagwieers/unoconv/issues/241
  unoconv /dev/null > /dev/null 2>&1 || :

  for d in "${dirs_to_search[@]}"; do
    echo "${BOLD}Directory: ${d}${RESET}"

    # Go into directory to make later commands less verbose
    pushd "${d}" > /dev/null || return 1

    # Get OSP name (the name part of ocpi.osp.name).
    # If not an osp, then "" is returned.
    local osp_name="$(get_osp_name "${d}")"

    # Prefix determines where the pdfs are placed in OUTPUT_PATH
    #   ${OUTPUT_PATH}/${prefix}/name.pdf
    local prefix=.
    if [ -n "${osp_name}" ]; then
      prefix="osp_${osp_name}"
    else
      case "${d}" in
        */doc/briefings) prefix=briefings ;;
        */doc/tutorials) prefix=tutorials ;;
        */projects/*)
          # This will extract the project name from a path.
          # If $d is "/path/to/projects/proj_name/path/to/doc"
          # then prefix=proj_name
          prefix="${d#*/projects/}"
          prefix="${prefix%%/*}"
          ;;
      esac
    fi

    local log_dir="${OUTPUT_PATH}/${prefix}/logs"
    mkdir -p "${log_dir}"

    # Convert msoffice and libreoffice files to pdf
    # We are in the directory with the files to convert
    for doc in *docx *pptx *odt *odp; do
      office_kernel "${PWD}/${doc}" "${prefix}" "${log_dir}"
    done

    # Convert tex files to pdf
    mapfile -t < <(find "${d}" -type f -name '*.tex')
    for doc in "${MAPFILE[@]}"; do
      tex_kernel "${doc}" "${prefix}" "${log_dir}"
    done

    popd > /dev/null || return 1
  done
}

###
# Checks if a directory is an OSP. If it is, attempts to figure out a "pretty"
# name based on repository name, e.g. XXX.osp.YYY => YYY
# Globals:
#   REPO_PATH - The path where the opencpi repo is located
# Arguments:
#   Path to check
# Returns:
#   string; empty if not a OSP, YYY if it is
###
function get_osp_name {
  local path="$1"
  if [ -z "$1" ]; then
    echo
    return 0
  fi

  if [[ "${path}" != */projects/osps/* ]]; then
    echo
    return 0
  fi

  # Extract osp project id
  # if path = "/path/to/projects/osps/some.osp.id/path/to/doc"
  # then osp_id = "some.osp.id" after these two trim operations
  local osp_id="${path#*/projects/osps/}"  # trim beginning of string
  osp_id="${osp_id%%/*}"  # trim end of string

  # Now check for ".osp."
  if [[ "${osp_id}" != *.osp.* ]]; then
    echo
    return 0
  fi

  # Return last part of osp id
  # if osp_id = "some.osp.id" then "id" is returned
  echo "${osp_id##*.}"
  return 0
}

##### MAIN #####

# Ensure variable is set
[ -z "${JOBS}" ] && JOBS=$(nproc --all)

# Figure out where we were called from in relation to caller
# Exporting MYLOC so when we call otpdf.sh it can find pdfmarks
export MYLOC="$(readlink -e "$(dirname "$0")")"

# Defaults:
REPO_PATH="$(readlink -e .)"
OUTPUT_PATH="${REPO_PATH}/doc/pdfs/"

while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help)
      show_help
      ;;
    -r|--repopath)
      REPO_PATH="$(readlink -e "$2")"
      shift 2
      ;;
    -o|--outputpath)
      OUTPUT_PATH="$(readlink -f "$2")"
      shift 2
      ;;
    -d|--dirsearch)
      dirsearch="$2"
      shift 2
      ;;
    *)
      show_help "Unknown argument $1"
      ;;
  esac
done
# Do not try to access parameters to the script past this

GEN_CG_PDFS_SH="${REPO_PATH}/doc/tutorials/gen-cg-pdfs.sh"
REMOVE_TRACKED_CHANGES_PY="${REPO_PATH}/doc/generator/remove-tracked-changes.py"

enable_color

# Failures
if [ ! -r "${REPO_PATH}" ]; then
  show_help "Unable to read '${REPO_PATH}'."
fi
if [ ! -d "${REPO_PATH}/doc/av" ]; then
  show_help "'${REPO_PATH}' doesn't seem to be correct. Could not find \
doc/av/."
fi
if [ -d "${OUTPUT_PATH}" ]; then
  show_help "'${OUTPUT_PATH}' already exists."
fi
mkdir -p "${OUTPUT_PATH}" || exit 1
if [ ! -w "${OUTPUT_PATH}" ]; then
  show_help "Cannot write to '${OUTPUT_PATH}'."
fi
if [ ! -f "$GEN_CG_PDFS_SH" ]; then
  echo "Could not find ${GEN_GEN_CG_PDFS_SH}."
  echo "This script is required to properly convert the tutorials to pdfs."
  exit 1
fi
if [ ! -f "${REMOVE_TRACKED_CHANGES_PY}" ]; then
  echo "Could not find ${REMOVE_TRACKED_CHANGES_PY}."
  echo "This script is required to properly convert the tutorials to pdfs."
  exit 1
fi


# Warnings
echo -n "${RED}"
if [ -z "$(command -v rubber)" ]; then
  echo "
The 'rubber' command was not found - will not be able to convert LaTeX => PDF!
"
fi
if [ -z "$(command -v gs)" ]; then  # XXX: remove this
  echo "
The 'gs' command was not found - will not be able to optimize PDF!
"
fi
if [ -z "$(command -v unoconv)" ]; then
  echo "
The 'unoconv' command was not found - will not be able to convert Open/LibreOffice => PDF!
"
fi
echo -n "${RESET}"

generate_pdfs "${dirsearch}"

# If errors...
if [ -f "${OUTPUT_PATH}/errors.log" ]; then
  echo "${RED}Errors were detected:${RESET}"
  cat "${OUTPUT_PATH}/errors.log"
  exit 1
fi

echo "PDFs now available at '${OUTPUT_PATH}'"
exit 0
