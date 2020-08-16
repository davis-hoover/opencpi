#!/bin/bash --noprofile
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

##########################################################################################
# Utility functions for platform exports.
#
# The sorry state of POSIX/BSD/LINUX/MACOS command compatibility
if [ `uname -s` = Darwin ]; then
  extended="-E ."
else
  extended="-regextype posix-extended"
fi

# Return relative path from canonical absolute dir path $1 to canonical
# absolute dir path $2 ($1 and/or $2 may end with one or no "/").
# Does only need POSIX shell builtins (no external command)
relPath () {
    local common path up
    common=${1%/} path=${2%/}/
    while test "${path#"$common"/}" = "$path"; do
        common=${common%/*} up=../$up
    done
    path=$up${path#"$common"/}; path=${path%/}; printf %s "${path:-.}"
}

# From:
# https://stackoverflow.com/questions/2564634
# Return relative path from dir $1 to dir $2 (Does not impose any
# restrictions on $1 and $2 but requires GNU Core Utility "readlink"
# HINT: busybox's "readlink" does not support option '-m', only '-f'
#       which requires that all but the last path component must exist)
# Try greadlink in case there are GNU utilities separate from BSD-ish ones
if ! readlinkm=$(command -v greadlink || command -v readlink); then
    echo No readlink command found >&2
    exit 1
fi
if ! $readlinkm --version > /dev/null 2>&1; then
    echo No GNU-style readlink command available;
    exit 1
fi
relpath () {
    #echo relpath: from \"$1\" to \"$2\" is $rc >&2
    local rc=$(relPath "$($readlinkm -m "$2")" "$($readlinkm -m "$1")")
    echo $rc
}

# match_pattern: Find the files that match the pattern:
#  - use default bash glob, and also
#  - avoids looking at ./exports/
#  - consolidate files that are hard or soft linked into single (first in inode sort order) file
#  - following links so that patterns can match against the link path
function match_pattern {
  local arg=$1
  if [[ $arg == \|* ]]; then
    arg=$(echo "$arg" | sed 's=^|\(.*\)$=./\1=') # add ./ prefix for find command, replacing |
    arg=$(find $extended -regex "$arg")   # expand using find with extended regex
  else
    arg="$(echo $arg)" # normal shell glob behavior
  fi
  local matches=$(shopt -s nullglob; for i in $arg; do echo $i | grep -v '#$' | grep -v '^./exports/'; done)
  [ -z "$matches" ] && return 0
  ls -L -i -d $matches 2>/dev/null | sort -n -b -u | sed 's/^ *[0-9]* *//;s/^\.\///'
}

# Check the exclusion in $1 against the path in $2
# The exclusion might be shorter than the path
# No wild carding here (yet)
function match_filter {
  # echo match_filter $1 $2
  local -a edirs pdirs
  edirs=(${1//\// })
  pdirs=(${2//\// })
  for ((i=0; i<${#pdirs[*]}; i++)); do
    # echo MF:$i:${edirs[$i]}:${pdirs[$i]}:
    if [[ "${edirs[$i]}" == "" ]]; then
      return 0
    elif [[ "${edirs[$i]}" == target-* ]]; then
      if [[ "${pdirs[$i]}" != target-* ]]; then
        return 1
      fi
    elif [[ "${edirs[$i]}" != "${pdirs[$i]}" ]]; then
      return 1
    fi
  done
  return 0
}

# Args: <to> <from> <warn-if-not-there>
# <to> is the thing the symlink will point to
# <from> is where the link should be
# <warn-if-not-there> is non-empty it means its not ok for the target of the link to be non-existent
function make_relative_link {
  # echo make_relative_link $1 $2
  if [ ! -e $1 -a -n "$3" ]; then
    echo Warning: link source $1 does not '(yet?)' exist. >&2
    return
  fi
  # Figure out what the relative prefix should be
  local up
#  [[ $1 =~ ^/ ]] || up=$(echo $2 | sed 's-[^/]*$--' | sed 's-[^/]*/-../-g')
#  link=${up}$1
  link=$(relpath $(dirname $1) $(dirname $2))
  link+=/$(basename $1)
  # echo make_relative_link $1 $2 up:$up link:$link > /dev/tty
  if [ -L $2 ]; then
    L=$(ls -l $2|sed 's/^.*-> *//')
    if [ "$L" = "$link" ]; then
      # echo Symbolic link already correct from $2 to $1.
      return 0
    else
      echo "Symbolic link wrong from $2 to $1 (via $link) (was $L), replacing it."
      rm $2
    fi
  elif [ -e $2 ]; then
    if [ -d $2 ]; then
      echo Link $2 already exists, as a directory. >&2
      echo '   ' when trying to link to $1 >&2
      exit 1
    fi
    echo Link $2 already exists, as a regular file. >&2
    echo '   ' when trying to link to $1 >&2
    # Perhaps the tree has been de-linked (symlinks followed)
    # if contents are the same, reinstate the symlink
    cmp -s $1 $2 || diff -u $1 $2 || exit 1
    echo '   ' but contents are the same.  Link is recreated. >&2
    rm $2
  fi
  mkdir -p $(dirname $2)
  # If the source does not exist, do not create the symlink.
  if [ -e $1 ]; then
    # echo ln -s $link $2
    ln -s $link $2
  else
    echo "Warning: link target path created, but link source $1 does not '(yet?)' exist." >&2
  fi
  set +vx
}

# link to source ($1) from link($2) if neither are filtered
# $3 is the type of object
# $4 is warn-if-not-there
# exclusions can be filtered by source or target
function make_filtered_link {
  #echo MAKE_FILTERED:$*
  local e;
  local -a edirs
  for e in $exclusions; do
    local -a both=($(echo $e | tr : ' '))
    # echo EXBOTH=${both[0]}:${both[1]}:$3:$1:$2
    [ -z "${both[1]}" ] && bad UNEXPECTED EMPTY LINK TYPE
    [ "${both[1]}" != "-" -a "${both[1]}" != "$3" ] && continue
    # echo EXBOTH1=${both[0]}:${both[1]}:$3:$1:$2
    edirs=(${both[0]/\// })
    if [ ${edirs[0]} = exports ]; then
       if match_filter ${both[0]} $2; then [ -n "$verbose" ] && echo Filtered: $2 >&2 || : ; return; fi
    else
       if match_filter ${both[0]} $1; then [ -n "$verbose" ] && echo Filtered: $1 >&2 || : ; return; fi
    fi
  done
  # No exclusions matched.  Make the directory for the link
  make_relative_link $1 $2 $4
}

# process an addition ($1), and $2 is non-blank for runtime (-- for deploy)
# Arg 3 is platformm or hyphen for bootstrapping, no-platform mode
# Arg 4 is platform-dir
function do_addition {
  local addition=$1
  local type=$2
  local platform=$3  # might be hyphen
  local platform_dir=$4
  local bootstrap
  [ $platform != - ] || bootstrap=1
  set -f
  local -a both=($(echo $1 | tr : ' '))
  [ "$platform" = - ] && case $addition in
      *\<target\>*|*\<platform\>*|*\<platform[-_]dir\>*) set +f; return;;
  esac
  if [[  "$type" == "--"  && "${both[2]}" != "" && "$1" == \<rcc[-_]platform[-_]dir\>* ]]; then
      set +f
      return # ignore cross-platform here
  fi
  exp=${both[1]}
  [ -z "$exp" ] && echo UNEXPECTED EMPTY SECOND FIELD && exit 1
  if [ "$exp" = - ]; then # process defaults for exported location
      if [  "$type" != "--"  -a -n "${both[2]}" ]; then # platform-specific defaults to platform subdir
	  exp="<platform>/"
      else
	  exp=/                                      # normal is top of exports or top of sdcard
      fi
  elif [ -n "${both[2]}" -a "$type" != -- ]; then # If platform specific, and not deployment, prepend platform name
    exp="<platform>/"$exp
  fi
  rawsrc=${both[0]}
  if [[ $rawsrc == \<platform[-_]dir\>/* ]]; then
    # This is an export from a platform's own directory, which is already pre-staged for us in the
    # platform's own exports dir
    rawsrc=${exp#<platform>}
    [[ "$exp" == */ ]] && rawsrc+=$(basename ${both[0]}) # if RHS was just a dir with trailing slash...
    if [ "$type" == "--" ]; then
      rawsrc=deploy/${rawsrc#/} # deployment comes FROM prestaged deployment
    fi
    rawsrc=$platform_dir/$rawsrc    # otherwise just use the platform's dir
  fi
  rawsrc=${rawsrc//<target>/$platform}
  rawsrc=${rawsrc//<platform>/$platform}
  [ -n "$rcc_platform_dir" ] && rawsrc=${rawsrc/#<rcc[-_]platform[-_]dir>/$rcc_platform_dir}
  [ -n "$rcc_platform" ] && rawsrc=${rawsrc//<rcc[-_]platform>/$rcc_platform}
  if [ "$type" = -- ]; then
      exp=deploy/$platform/${exp#/}
  fi
  exp=${exp//<platform>/$platform}
  exp=${exp//<target>/$platform}
  if [ -n "$rcc_platform" ]; then
     exp=${exp//<rcc[-_]platform>/$rcc_platform}
  fi
  set +f
  targets=$(match_pattern "$rawsrc")
  for src in $targets; do
    # echo do_addition $1 $2 SRC:$src > /dev/tty
    if [ -e $src ]; then
      # figure out the directory for the export
      local dir=
      local srctmp=$src
      if [ -n "${both[2]}" ]; then  # a platform-specific export
        srctmp=${src=#$platform_dir/=}
      fi
      if [[ -z "$exp" ]]; then
        : # [[ $srctmp == */* ]] && dir+=$(dirname $srctmp)/
      elif [[ $exp =~ /$ ]]; then
        dir+=$exp
      else
        dir+=$(dirname $exp)/
      fi
      # figure out the basename of the export
      local base=$(basename $src)
      local suff=$(echo $base | sed -n '/\./s/.*\(\.[^.]*\)$/\1/p')
      [[ "$exp" && ! $exp =~ /$ ]] && base=$(basename $exp)
      base=${base//<suffix>/$suff}
      #echo For $addition $type
      #echo dir=$dir base=$base
      make_filtered_link $src exports/$dir$base "" $bootstrap
      [ -n "$type" ] && [ "$type" = "-" ] && make_filtered_link $src exports/runtime/$dir$base  "" $bootstrap || :
      # Calling make_filtered_link for @ (deployment)
      [ -n "$type" ] && [ "$type" = "--" ] && make_filtered_link $src exports/$dir$base  "" $bootstrap ||:
    else
      [ "$3" = - ] || echo Warning: link source $src does not '(yet?)' exist. >&2
    fi
  done
}

function bad {
    echo Error: $* 1>&2
    exit 1
}
# This function reads an exports file for a certain type of entry and adds entries to the
# requested variable ($1)
# Args are:
# 1. variable name to set with the entries found
# 2. leading character to look for
# 3. file name to read
# 4. a flag indicating platform-specific entries
function readExport {
  set -f
  local entries=($(egrep '^[[:space:]]*\'$2 $3 |
                   sed 's/^[ 	]*'$2'[ 	]*\([^ 	#]*\)[ 	]*\([^ 	#]*\).*$/\1:\2/'))
  # echo For "$1($3:$4) got ${#entries[@]} entries"
  # make sure there is a second field
  entries=(${entries[@]/%:/:-})
  # add a third field for platform-specifics
  [ -n "$4" ] && entries=(${entries[@]/%/:-})
  eval $1+=\" ${entries[@]}\"
  # eval echo \$1 is now:\${$1}:
  set +f
}
