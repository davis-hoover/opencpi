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

# Generate PDFs from all tex, odt files
# This script will generate all PDFs using makepdf.sh and then makepdf.sh will call optpdf.sh to shrink
# the size of the files. All three of these .sh files should be located in the same directory. Finally,
# after the PDFs are generated and moved to a specfic output location, an index.html will be generated
# listing all of the PDFs in the same output location.

# Check MAKEFLAGS for "n" because the way we "cheat" at top-level Makefile, we
# will be run even if "make -n" which means DO NOT RUN
[ -n "$(echo "${MAKEFLAGS}" | perl -ne '/\bn\b/ && print 1')" ] && exit 0
# Ensure variable is set
[ -z "${JOBS}" ] && JOBS=$(nproc --all)

# Lookup table for OSP names (defaults to just capitalization) (AV-4753)
declare -A osp_aliases
osp_aliases["e3xx"]="Ettus E310/E312/E313"
osp_aliases["picoflexor"]="DRS Picoflexor S1T6A/S3T6A"

# Disables experimental HTML output
export EXPERIMENTAL_HTML=TESTCODEDOESNOTRUN

# Enables color variables BOLD, RED, and RESET
enable_color() {
  if [ -n "$(command -v tput)" -a -n "${TERM}" ]; then
    export BOLD=$(tput bold 2>/dev/null)
    export RED=${BOLD}$(tput setaf 1 2>/dev/null)
    export RESET=$(tput sgr0 2>/dev/null)
  fi
}

###
# Add a new section to the table in index.html
# Globals:
#   None
# Arguments:
#   $1: NAME
#       Name of the documentation
#   $2: LOCATION
#       The locations of the PDFs to be added
#       to the table
# Returns:
#   An HTML list of documents to standard output (with header)
###
add_new_list() {
    # If directory is empty do not create an entry for it
    if compgen -o filenames -G $2/'*.pdf' > /dev/null; then
        # Header and start list
        printf '<h3 style="text-align: center">%s</h3>\n<ul class="collist">\n' "$1"
        for pdf in $2/*.pdf; do
            file_name=$(basename -s .pdf $pdf)
            printf '<li><a href="%s">%s</a></li>\n' "${pdf}" "$(echo ${file_name} | tr '_' ' ')"
        done
        echo "</ul>"
    fi
}

###
# Created index.html with links to documents
# Globals:
#   OUTPUT_PATH
#       The path where the PDFs are to be written
#   OSPS
#        Array of the available osps (filtered)
#   MYLOC
#       The path of the directory that contains this script
# Arguments:
#   None
# Returns:
#   All of the documents in an html file to standard out
###
create_index() {
    cd ${OUTPUT_PATH}
    av_pdf_loc="."
    asset_pdf_loc="./assets"
    asset_ts_pdf_loc="./assets_ts"
    core_pdf_loc="./core"

    # Bring in start of index.html
    cat ${MYLOC}/listing_header.html

    add_new_list "Main Documentation" "${av_pdf_loc}"
    add_new_list "Assets Project Documentation" "${asset_pdf_loc}"
    add_new_list "Assets_TS Project Documentation" "${asset_ts_pdf_loc}"
    add_new_list "Core Project Documentation" "${core_pdf_loc}"

    for d in ${OSPS[*]}; do
      osp_name=$(get_osp_name $d)
      osp_prettyname="${osp_name^}" # Capitalize
      [ -n "${osp_aliases[${osp_name}]}" ] && osp_prettyname="${osp_aliases[${osp_name}]}"
      add_new_list "${osp_prettyname} Board Support Package (OSP) Project Documentation" "./osp_${osp_name}"
    done

    # Bring in ending of index.html
    cat ${MYLOC}/listing_footer.html
}

###
# Throws warnings if file exists
# Globals:
#   None
# Arguments:
#   $1: Output directory
#   $2: Output file basename (pdf added)
#   $3: Caller directory
# Returns:
#   True if there is a file already (usage: warn_existing_pdf && continue when looping over files)
#       Will write to the screen and top-level errors.log
###
warn_existing_pdf() {
    if [ -e "${OUTPUT_PATH}/${prefix}/${ofile}.pdf" ]; then
        echo "${RED}Output file $(readlink -e ${OUTPUT_PATH}/${prefix}/${ofile}.pdf) already exists! Skipping!${RESET}"
        echo "Output file $(readlink -e ${OUTPUT_PATH}/${prefix}/${ofile}.pdf) already exists when parsing ${d}/${ofile}. Skipping!" >> ${OUTPUT_PATH}/errors.log
    else
        false
    fi
}

###
# Creates PDF from LaTeX source
# Globals:
#   OUTPUT_PATH
#       The path where the PDFs are
# Arguments:
#   $1: directory ($d)
#   $2: prefix ($prefix)
#   $3: log directory ($log_dir)
#   $4: tex or subdir ($tex)
# Returns:
#   Lots of stuff
###
tex_kernel() {
  d=$1
  prefix=$2
  log_dir=$3
  tex=$4
  [ "${prefix}" == . ] && unset prefix
  echo $tex | grep -iq '^snippets/' && return # Skip snippets
  echo $tex | grep -iq '_header\.tex' && return # Skip headers
  echo $tex | grep -iq '_footer\.tex' && return # Skip footers
  echo $tex | grep -iq '_template\.tex' && return # Skip templates
  echo "${BOLD}LaTeX: $d/$tex ${prefix+(output prefix=${prefix})}${RESET}"
  # Jump into subdir if present (note: $tex is no longer valid - use ofile.tex)
  expr match $tex '.*/' >/dev/null && cd "$(dirname $tex)"
  ofile=$(basename -s .tex $tex)
  warn_existing_pdf "${OUTPUT_PATH}/${prefix}" ${ofile} $d && return
  [ -f Makefile ] && make
  rubber -d $ofile.tex || FAIL=1
  # If the pdf was created then copy it out
  if [ ! -f $ofile.pdf -o -n "${FAIL}" ]; then
    echo "${RED}Error creating $ofile.pdf${RESET}"
    echo "Error creating $ofile.pdf ($d)" >> ${OUTPUT_PATH}/errors.log
    rubber-info --errors $ofile.tex >> ${OUTPUT_PATH}/errors.log
    return
  fi
  mv ${ofile}.log ${log_dir}/${ofile}.log 2>&1
  rubber-info --boxes $ofile.tex >> ${log_dir}/${ofile}_boxes.log 2>&1
  rubber-info --check $ofile.tex >> ${log_dir}/${ofile}_warnings.log 2>&1
  rubber-info --warnings $ofile.tex >> ${log_dir}/${ofile}_warnings.log 2>&1
  rm -f ${ofile}.{aux,out,log,lof,lot,toc,dvi,synctex.gz}
  mv ${ofile}.pdf ${OUTPUT_PATH}/${prefix}/
  # expr match ${tex} '.*/' >/dev/null && cd ..
} # tex_kernel

###
# Convert files to PDFs and if it is converting
# tex docs make sure to shrink in size
# Globals:
#   MYLOC
#       The path of the directory that contains this script
#   OUTPUT_PATH
#       The path where the PDFs are to be written
#   REPO_PATH
#       The path where the opencpi repo is located
#   OSPS
#       Array of the available osps (filtered)
# Arguments:
#   $1: If $1 is provided it means we want to use our own search path for
#         dirs_to_search instead of the provided ones we use
# Returns:
#   None
#       Some stuff will be returned but it is all garbage and
#       should not be used.
###
generate_pdfs() {
    make -C ${REPO_PATH}/projects/assets/components/misc_comps/data_src.test/doc/
    make -C ${REPO_PATH}/projects/assets/components/util_comps/fifo.test/doc/
    make -C ${REPO_PATH}/projects/assets/components/util_comps/iqstream_max_calculator.test/doc/
    make -C ${REPO_PATH}/projects/assets/components/util_comps/timestamper_scdcd.test/doc/
    make -C ${REPO_PATH}/projects/assets/components/util_comps/tx_event_ctrlr.test/doc/
    make -C ${REPO_PATH}/projects/assets/components/dsp_comps/real_digitizer.test/doc/
    make -C ${REPO_PATH}/projects/assets/hdl/devices/data_sink_dac.test/doc/
    make -C ${REPO_PATH}/projects/assets/hdl/devices/data_src_adc.test/doc/
    shopt -s nullglob
    local search_path="$1"

    # TODO: remove core/assets and have it just walk projects/ skipping osps and inactive
    if [ -z "$search_path" ]; then
        echo "${BOLD}Building PDFs from '${REPO_PATH}' with results in '${OUTPUT_PATH}'${RESET}"
        dirs_to_search=()
        dirs_to_search+=("${REPO_PATH}/doc/briefings")
        dirs_to_search+=("${REPO_PATH}/doc/av/tex")
        dirs_to_search+=("${REPO_PATH}/doc/odt")
        dirs_to_search+=("${REPO_PATH}/doc/tex")
        dirs_to_search+=("${REPO_PATH}/doc/tutorials")
        dirs_to_search+=($(find ${REPO_PATH}/projects/assets -type d \( -name doc -o -name docs \)))
        dirs_to_search+=($(find ${REPO_PATH}/projects/assets_ts -type d \( -name doc -o -name docs \)))
        dirs_to_search+=($(find ${REPO_PATH}/projects/core -type d -name doc))
        # Searching for osps done differently due to possibility of shared osps
        for osp in ${OSPS[@]}; do
            dirs_to_search+=($(find ${REPO_PATH}/projects/osps/${osp} -type d -name doc))
        done
    else # given directories to search
        dirs_to_search=()
        tmp_array=($search_path)
        for dir in ${tmp_array[@]}; do
            if [ -e "$dir" ]; then
             # Code elsewhere requires absolute paths, like REPO_PATH is above
             dirs_to_search+=($(find "$(readlink -e ${dir})" -type d \( -name doc -o -name docs \)))
            else
              echo "${RED}Error: provided directory: $dir does not exist${RESET}"
            fi
        done
    fi

    # There is a bug with unoconv where it doesn't work the first time it is
    # ran so we kick start it here
    # https://github.com/dagwieers/unoconv/issues/241
    unoconv /dev/null > /dev/null 2>&1 || :

    for d in ${dirs_to_search[*]}; do
        # This should be an error post-AV-5448
        [ ! -d "$d" ] && echo "${RED}Directory $d does not exist! Skipping!${RESET}" && continue
        echo "${BOLD}Directory: $d${RESET}"
        pushd "$d" || return 1
        prefix=.
        osp_name="$(get_osp_name $d)"
        if expr match $d '.*projects/assets_ts' > /dev/null; then
            prefix=assets_ts
        elif expr match $d '.*projects/assets' > /dev/null; then
            prefix=assets
        elif expr match $d '.*projects/core' > /dev/null; then
            prefix=core
        elif expr match $d '.*tutorials' > /dev/null; then
            prefix=tutorials
        elif expr match $d '.*briefings' > /dev/null; then
            prefix=briefings
        elif [ -n "${osp_name}" ]; then
            prefix=osp_${osp_name}
        fi

        log_dir=${OUTPUT_PATH}/${prefix}/logs
        mkdir -p "${log_dir}"

        for ext in *docx *pptx *odt *odp; do
            # Get the name of the file without the file extension
            ofile=${ext%.*}
            echo "${BOLD}office: ${d}/${ext} ${prefix+(output prefix=${prefix})}${RESET}"
            warn_existing_pdf "${OUTPUT_PATH}/${prefix}" "${ofile}" "${d}" && continue
            rv=0
            if [ "${prefix}" = tutorials ]; then
              bash "${GEN_CG_PDFS_SH}" "${ext}" "${PWD}" >> "${log_dir}/${ofile}.log" 2>&1
              rv=$?
            else
              unoconv -vvv "${ext}" >> "${log_dir}/${ofile}.log" 2>&1
              rv=$?
            fi

            # If the pdf was created then copy it out
            if [ ${rv} -eq 0 ]; then
              mv ./*.pdf "${OUTPUT_PATH}/${prefix}"
            else
              echo "${RED}Error creating ${ofile}.pdf${RESET}"
              echo "Error creating ${ofile}.pdf (${d})" >> "${OUTPUT_PATH}/errors.log"
            fi
        done

        # There are a few places where it is doc/XXX/*.tex so captures both, removing XXX
        export -f tex_kernel warn_existing_pdf
        export OUTPUT_PATH
        texfs=$(echo *tex */*tex)
        if [ -n "${texfs}" ]; then
          if [ -z "$(command -v parallel)" -o -n "${JENKINS_HOME}" ]; then
            echo "${texfs// /$'\n'}" | xargs -I+ bash -c "tex_kernel $d $prefix $log_dir +"
          else
            echo "${texfs// /$'\n'}" | parallel -j ${JOBS} tex_kernel $d $prefix $log_dir
          fi
        fi

        popd || return 1
    done
}

###
# Compresses resulting PDFs
# Globals:
#   MYLOC
#       The path where the compression script is located
#   OUTPUT_PATH
#       The path where the PDFs are
# Arguments:
#   None
# Returns:
#   None; prints to the screen a lot
###
compress_kernel() {
  echo "$(basename $1): Original $(stat -c "%s" $1) bytes"
  while ${MYLOC}/optpdf.sh $1;do :;done
}
compress_pdfs() {
  echo -n "Compressing output PDFs"
  export -f compress_kernel
  export MYLOC
  if [ -z "$(command -v parallel)" -o -n "${JENKINS_HOME}" ]; then
    echo "..."
    find "${OUTPUT_PATH}" -name '*.pdf' -print0 | xargs -r -0 -I+ bash -c "compress_kernel +"
  else
    echo " (in parallel)..."
    find "${OUTPUT_PATH}" -name '*.pdf' -print0 | parallel -r -0 compress_kernel
  fi
}

###
# Removes any duplicate packages in osp subdirectory and stores the filtered list in OSPS
# This is needed for when multiple platforms may check out the same source repository
# Globals:
#   None
# Arguments:
#   Two paths, will return true if both are git checkouts with same remote URL for 'origin'
# Returns:
#   true/false
###
same_git_repo() {
  [ -e $1/.git ] &&
  [ -e $2/.git ] &&
  [ "$(git --git-dir=$1/.git config --get remote.origin.url)" = \
    "$(git --git-dir=$2/.git config --get remote.origin.url)" ]
}

###
# Checks if a directory is an OSP. If it is, attempts to figure out a "pretty" name based on
# repository name, e.g. XXX.osp.YYY => YYY
# Globals:
#   REPO_PATH
#       The path where the opencpi repo is located
# Arguments:
#   Path to check (defaults to cwd)
# Returns:
#   string; empty if not a OSP, YYY if it is
###
get_osp_name() {
  dir=.
  [ -n "$1" ] && dir=$1
  # Check if "here" or in projects/osps/
  [ -e ${dir} ] || dir=${REPO_PATH}/projects/osps/$1
  outname=$(basename "$(realpath ${dir})")
  # Does it have /projects/bsps/ in its path? If not, bail.
  [ "$(expr match "$(realpath ${dir})" '.*/projects/bsps/')" = 0 ] && echo "" && return
  git_url=$(cd "$(realpath ${dir})" && git config --get remote.origin.url)
  # Does it have .osp. in its git URL? (The extra . at end captures first letter for substring)
  git_url_offset=$(expr match "${git_url}" '.*\.osp\..')
  [ "${git_url_offset}" = 0 ] && echo "" && return
  git_url=$(expr substr "${git_url}" ${git_url_offset} 1000)
  git_url_offset=$(( $(expr match "${git_url}" '.*\.git$') - 4 ))
  git_url=$(expr substr "${git_url}" 1 ${git_url_offset})
  # Does it look decent?
  [ -z "${git_url}" ] && echo "" && return
  echo "${git_url}"
}

###
# Removes any duplicate packages in osp subdirectory and stores the filtered list in OSPS
# This is needed for when multiple platforms may check out the same source repository
# Globals:
#   REPO_PATH
#   OSPS
# Arguments:
#   None
# Returns:
#   The correct list of OSPS to use in the global variable OSPS
###
find_osps() {
    shared_osp=()
    tmp_osps=($(find ${REPO_PATH}/projects/osps/ -mindepth 1 -maxdepth 1 \
                -type d -printf '%f\n'))

    # If the list of tmp_osps is greater than one it is possible that we have shared_osps so we need to find them here
    [ ${#tmp_osps[@]} -gt 1 ] &&
    for ((i=0; i<${#tmp_osps[@]}-1; i+=1)); do
        for ((j=i+1; j<${#tmp_osps[@]}; j+=1)); do
            # If there exists any two projects that both have the same remote.origin.url we can assume that they are a shared_osp; add the
            # second occurring one to the shared_osp array which will later be used to remove opss from OSPS
            same_git_repo ${REPO_PATH}/projects/osps/${tmp_osps[$i]} \
                          ${REPO_PATH}/projects/osps/${tmp_osps[$j]} &&
              shared_osp+=(${tmp_osps[$j]})
        done
    done

    # Making array unique
    shared_osp=($(echo "${shared_osp[@]}" | tr ' ' '\n' | sort -u | tr '\n' ' '))

    # Add all of the osps to OSP if they are not in shared_osp
    for osp in ${tmp_osps[@]}; do
        multiple_occurences=false
        for unincluded_osp in ${shared_osp[@]}; do
            [ $osp = $unincluded_osp ] && multiple_occurences=true
        done
        [ "$multiple_occurences" = false ] && OSPS+=($osp) || echo "${RED}${osp} is a duplicate OSP and we are not including it in the output${RESET}"
    done
}

###
# Sends help message to STDERR
# Globals:
#   None
# Arguments:
#   $1: Error string to print before help (optional)
# Returns:
#   Ends script with success or failure depending on $1 presence
###
show_help() {
    enable_color
    [ -n "$1" ] && printf "\n${RED}ERROR: %s\n\n${RESET}" "$1"
    cat <<EOF >&2
${BOLD}This genDocumentation script creates PDFs for OpenCPI.
Usage is: $0 [-h] [-r] [-o] [-d]

  -r / --repopath          Use the repo location provided
  -o / --outputpath        Use the provided location for output
  -d / --dirsearch         Instead of using our automatic directory list to search
                             for documents to build, provide your own. If you want
                             to provide more than one directory, provide them as a
                             space separated string. Note that it will only look in
                             subdirectories named 'doc[s]' within the given path(s).
  -h / --help              Display the help screen${RESET}
EOF
    [ -n "$1" ] && exit 99
    exit 0
}

# Figure out where we were called from in relation to caller
# Exporting MYLOC so when we call otpdf.sh it can find pdfmarks
export MYLOC=$(readlink -e "$(dirname $0)")

# Defaults:
REPO_PATH="$(readlink -e .)"
OUTPUT_PATH="${REPO_PATH}/doc/pdfs/"
index_file="index.html"

while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -h|--help)
            show_help
            ;;
        -r|--repopath)
            REPO_PATH=$(readlink -e "$2")
            shift # past argument
            shift # past value
            ;;
        -o|--outputpath)
            OUTPUT_PATH=$(readlink -f "$2")
            shift # past argument
            shift # past value
            ;;
        -d|--dirsearch)
            dirsearch="$2"
            shift # past argument
            shift # past value
            ;;
        *)  # unknown option
            show_help "Unknown argument $key"
            ;;
    esac
done
# Do not try to access parameters to the script past this

GEN_CG_PDFS_SH="${REPO_PATH}/doc/tutorials/gen-cg-pdfs.sh"

enable_color
# Failures
[ ! -r ${REPO_PATH} ] && show_help "\"${REPO_PATH}\" not readable by $USER. Consider using a different repo path."
[ ! -d "${REPO_PATH}/doc/av" ] && show_help "\"${REPO_PATH}\" doesn't seem to be correct. Could not find doc/av/."
[ -d "${OUTPUT_PATH}" ] && show_help "\"${OUTPUT_PATH}\" already exists"
if [ ! -f "$GEN_CG_PDFS_SH" ]; then
  echo "Could not find $GEN_GEN_CG_PDFS_SH"
  echo "This script is required to properly convert the tutorials to pdfs"
  exit 1
fi

# Warnings
echo -n "${RED}"
[ -z "$(command -v rubber)" ] && printf "\nThe 'rubber' command was not found - will not be able to convert LaTeX => PDF!\n\n"
[ -z "$(command -v gs)" ] && printf "\nThe 'gs' command was not found - will not be able to optimize PDF!\n\n"
[ -z "$(command -v unoconv)" ] && printf "\nThe 'unoconv' command was not found - will not be able to convert Open/LibreOffice => PDF!\n\n"
echo -n "${RESET}"

mkdir -p ${OUTPUT_PATH} > /dev/null 2>&1
touch ${OUTPUT_PATH}/${index_file} > /dev/null 2>&1
[ ! -w ${OUTPUT_PATH}/${index_file} ] && show_help "\"${OUTPUT_PATH}\" not writable by $USER. Consider using a different output path."
rm ${OUTPUT_PATH}/${index_file}
OSPS=()
[ -z "${dirsearch}" ] && find_osps
generate_pdfs "${dirsearch}"

[ -z "${dirsearch}" ] && create_index > ${OUTPUT_PATH}/${index_file}
#compress_pdfs

# If errors...
if [ -f ${OUTPUT_PATH}/errors.log ]; then
  echo "${RED}Errors were detected! errors.log:${RESET}"
  cat ${OUTPUT_PATH}/errors.log
  exit 2
fi

echo "PDFs now available in '${OUTPUT_PATH}'"

if [ "${REPO_PATH}/doc/pdfs/" == "${OUTPUT_PATH}" -a \
  -z "${JENKINS_HOME}" -a \
  -n "$(command -v cpio)" -a \
  -n "$(command -v docker)" -a \
  -z "${EXPERIMENTAL_HTML}" -a \
  -n "$(command -v find)" \
  ]; then
  echo "${BOLD}Creating HTML versions in 3 seconds${RESET}"
  sleep 3
  cd ${OUTPUT_PATH}
  shopt -s globstar nullglob
  for pdf in **/*.pdf; do
    echo "${BOLD}${pdf}${RESET}"
    # TODO: Localize this https://imagelayers.io/?images=bwits%2Fpdf2htmlex
    docker run -u "$(id -u):$(id -g)" -it --rm -v "$(dirname $(realpath ${pdf}))":/pdf bwits/pdf2htmlex pdf2htmlEX --zoom 1.5 --clean-tmp 0 "$(basename ${pdf})"
  done
  echo "${BOLD}Moving to ${REPO_PATH}/doc/html/${RESET}"
  find . -name '*.html' | cpio -vpdm ${REPO_PATH}/doc/html/
  find . -name '*.html' -not -name 'index.html' -delete
  echo "${BOLD}Fixing ${REPO_PATH}/doc/html/index.html${RESET}"
  sed -i -e 's|\(\./.*\)\.pdf|\1.html|g' ${REPO_PATH}/doc/html/index.html
fi
