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

####################################################################################################
# Create the local exports in a platform directory, under the directory specified in $1, usually lib/
# I.e. everything that needs to be exposed to users is made available here, and this is what will
# be exported/visible from outside the project.
# This is a precursor to the Framework-level cdk exporting that is done per-platform.
# and which is where these exports are placed according to the + or = or @ tag in the exports file.
# If something specified in <platform>.exports is not coming from this platform directory at all
# (the LHS in the file is not <platform-dir>), we ignore it here.
# All deployment exports are put under $1/deploy/ here, at a link indicated the RHS

# We process the .exports file to get the "union" of all the exports for devel, runtime, deploy
lib=$1
shift # the remaining files are simple development exports
set -e
shopt -s extglob
base=$(basename `pwd`)
[ $base = lib ] && cd ..
platform=$(basename `pwd`)
exports=$platform.exports
echo Performing local exports into the $lib/ subdirectory for platform $platform.
[ -e $exports ] && echo Exports file \"$exports\" will be processed || :

# FIXME: Share this functionality with makeExportLinks.sh or makeProjectExports.sh
function make_link {
  # echo make_link $1 $2
  # Figure out what the relative prefix should be
  local L
  from=$2
  [[ $2 == */ ]] && mkdir -p $2
  if [ -L $2 ]; then
    L=$(readlink $2)
  elif [ -d $2 ]; then
    from=${2%/}/$(basename $1)
    if [ -L $from ]; then
	L=$(readlink $from)
    elif [ -e $from ]; then
      echo "File '$from' already exists and is not a symbolic link (when doing $2 -> $1)"
      exit 1
    fi
  elif [ -e $2 ]; then
    echo File $2 already exists, as a regular file, when trying to link to $1
    exit 1
  fi
  if [ "$L" = "$1" ]; then
      echo Exports link already correct from $from to $1.
      return 0
  elif [ -n "$L" ]; then
      echo Exports link is wrong from $from to $1 \(was $L\), replacing it.
      rm $from
  fi
  [[ $from == */* ]] && mkdir -p $(dirname $from)
  # echo ln -s $1 $from
  ln -s $1 $from
}

[ -e $exports ] && sed -n 's/^ *\([+=@]\) *\([^#]*\).*$/\1 \2/p' $exports | while read tag local export deploy; do
  # echo "tag: '$tag' local: '$local' export: '$export' deploy: '$deploy'"
  # For runtime or devel, the RHS (export) is relative to the CDK top, which usually means
  # the platform's subdir - i.e. a leading <target> or <platform>
  [ -z "$local" ] && continue;                     # blank lines
  [[ $local != \<platform[-_]dir\>* ]] && continue # RHS is not a platform file
  local=${local#*/}                                # strip <platform[-_]dir>/ from the LHS
  case $tag in
      (+|=) # development or runtime, ultimately in CDK under a platform's dir
       case $export in
	   (\<target\>*|\<platform\>*)             # leading <platform> or <target>
	       export=${export#*/};;               # strip leading <platform> or <target>
       esac;;
      (@) # deployment
        [[ "$export" == \<[a-z]*[-_]platform[-_]dir\> ]] && continue # skip cross-platform exports here
        [ -z "$export" ] && export=/ || :
	[[ "$export" == /* ]] && export=${export#/} # root is permissable, and stripped here
	export=deploy/$export  # deployment exports are put in their own subdir: deploy, under the local dir
        ;;
  esac
  local=${local//<platform>/$platform}
  local=${local//<target>/$platform}
  if [[ "$export" == */ ]]; then
     mkdir -p $lib/${export%/}
  elif [[ "$export" == */* ]]; then
     mkdir -p $lib/$(dirname $export)
  else
     mkdir -p $lib
  fi
  # add ../ for each level that is in the export that is in subdirs
  prefix=
  [[ "$export" == */* ]] && tmp=${export%%+([^/])} && prefix=$(echo $tmp|sed 's/[^/][^/]*\//..\//g')
  for i in $(shopt -s nullglob; echo $local); do
      make_link ../$prefix$i $lib${export:+/}$export
  done
done
# Export the default files that should not be mentioned in the exports file
# This list is the union of common files to export from all types of platforms
for i in $platform.exports $platform.mk $platform-check.sh $platform-packages.sh $*; do
    [ -e $i ] && make_link ../$i $lib || :
done
echo Exports for the \"$platform\" platform created in its local directory: \"$lib\".
