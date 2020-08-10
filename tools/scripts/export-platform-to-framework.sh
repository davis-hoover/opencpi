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
# Populate the framework-level exports tree with the links for files in a platform in a project.
#
# This script is done in the context of a particular platform, as its first argument.
#
[ -z "$OCPI_CDK_DIR" ] && echo "This script ($0) expects the environment to be set up with OCPI_CDK_DIR" && exit 1
set -e

if test "$*" = ""; then
  echo "Usage is: export-platform-framework.sh <model> <platform> <platform-dir>"
  echo 'This script is typically used internally by "make exports"'
  echo 'It is designed to be run repeatedly, making links to whatever exists.'
  echo 'Thus it is run several times during the build process.'
  exit 1
fi
if [ "$1" = "-v" -o "$OCPI_EXPORTS_VERBOSE" = 1 ]; then
  verbose=-v
  [ "$1" = "-v" ] && shift
fi
model=$1
platform=$2
platform_dir=$3
[ -n "$verbose" ] && echo Doing platform exports for $model $platform at $platform_dir

# The only things we currently need from ocpitarget.sh is OcpiPlatformOs and OcpiPlatformPrerequisites
[ "$model" = rcc ] && source $OCPI_CDK_DIR/scripts/ocpitarget.sh $platform
source $OCPI_CDK_DIR/scripts/export-utils.sh
mkdir -p exports
platform_exports=$platform_dir/$platform.exports
[ -f $platform_exports ] || platform_exports=
if [ -z "$platform_exports" ];  then
  echo No exports file found for $model platform $platform in $platform_dir
else
  echo Using extra exports file for platform $platform: $platform_exports
  readExport additions + $platform_exports -
  readExport runtimes = $platform_exports -
  readExport deployments @ $platform_exports -
  readExport exclusions - $platform_exports -
fi
# Do the ad-hoc export links
[ -n "$verbose" ] && echo Processing cdk additions
for a in $additions; do
  do_addition $a "" $platform $platform_dir
done
[ -n "$verbose" ] && echo Processing runtime additions
for a in $runtimes; do
  do_addition $a - $platform $platform_dir
done
[ -n "$verbose" ] && echo Processing deployment additions
for a in $deployments; do
  do_addition $a -- $platform $platform_dir
done

if [ $model = hdl ]; then
  tbz=projects/assets/exports/artifacts/ocpi.assets.testbias_${platform}_base.hdl.0.${platform}.bitz
  if [ -f $tbz ]; then
    make_relative_link $tbz exports/$platform/$(basename $tbz)
  else
    echo The file \"$tbz\" is not present, which is a failure for hdl platforms.
    exit 1
  fi
fi
[ $model != rcc ] && exit 0

[ -n "$verbose" ] && echo Processing framework source-code-based links for rcc platform $platform
while read path opts; do
  case "$path" in
    \#*|""|end-of-runtime-for-tools|prerequisites) continue;;
  esac
  directory= library=$(basename $path) dest=lib options=($opts) foreign= tools= driver= useobjs=
  library=${library//-/_}
  exclude= includes= libs= xincludes= runtime=
  while [ -n "$options" ] ; do
    case $options in
      -l) library=${options[1]}; unset options[1];;
      -d) directory=${options[1]}/; unset options[1];;
      -n) dest=noinst;;
      -f) foreign=1;;
      -D) defs="$defs -D${options[1]}"; unset options[1];;
      -t) tools=1;;
      -v) driver=1;;
      -s) useobjs=1;;
      -L) lib=${options[1]}; unset options[1]
	  case $lib in
	      /*|@*|*/*);;
	      *) lib=libocpi_$lib;;
	  esac
	  libs+=" $lib";;
      -I) xincludes="$xincludes ${options[1]}"; unset options[1];;
      -x) exclude="$exclude -not -regex ${options[1]} -a"; unset options[1];;
      -T) tops="$tops ${options[1]}"; unset options[1];;
      -r) runtime=1;;
      -*) bad Invalid option: $options;;
      *)  bad Unexpected value in options: $options;;
    esac
    unset options[0]
    options=(${options[*]})
  done
  programs=`find -H $path $exclude -name "[a-zA-Z]*_main.cxx"|sed 's=.*src/\(.*\)_main.c.*$=\1='`
  swig=`find -H $path $exclude -path "*/src/*.i"`
  api_incs=`find -H $path $exclude \( -path "*/include/*Api.h" -o -path "*/include/*Api.hh" \)`
  [ -n "$driver" ] && drivers+=" $(basename $path)"
  # echo LIB:$library PATH:$path PROGRAMS:$programs DIRECTORY:$directory
  for p in $programs; do
    dir=$directory
    for t in $tops; do
      if [ "$t" = $p ]; then
        dir=
        break
      fi
    done
    file=build/autotools/target-$platform/staging/bin/$dir$p
#    [ -x $file -a "$dir" != internal/ ] && {
    [ "$dir" != internal/ ] && {
	make_filtered_link $file exports/$platform/bin/$dir$p
        [ -z "$tools" -o -n "$runtime" ] &&
	    make_filtered_link $file exports/runtime/$platform/bin/$dir$p
    }
  done
  shopt -s nullglob
  if [ "$dest" = lib ]; then
    for f in build/autotools/target-$platform/staging/lib/libocpi_${library}{,_s,_d}.* ; do
      make_filtered_link $f exports/$platform/lib/$(basename $f)
      [ -n "$driver" ] &&
        make_filtered_link $f exports/runtime/$platform/lib/$(basename $f)
    done
  fi
  [ -n "$swig" ] && {
    base=$(basename $swig .i)
    fromdir=build/autotools/target-$platform/staging/lib
    file=_$base.so
    if [ -f $fromdir/$file ]; then
        make_filtered_link $fromdir/$file exports/$platform/lib/opencpi/$file
        make_filtered_link $fromdir/$base.py exports/$platform/lib/opencpi/$base.py
        # swig would be runtime on systems with python and users' ACI programs that used it
        [ -z "$tools" ] && {
	    make_filtered_link $fromdir/$file exports/runtime/$platform/lib/opencpi/$file
            make_filtered_link $fromdir/$base.py exports/$platform/lib/opencpi/$base.py
	}
    fi
    file=_${base}2.so
    if [ -f $fromdir/$file ]; then
        make_filtered_link $fromdir/$file exports/$platform/lib/opencpi2/_${base}.so
        make_filtered_link $fromdir/$base.py exports/$platform/lib/opencpi2/$base.py
        [ -z "$tools" ] && {
	    make_filtered_link $fromdir/$file exports/runtime/$platform/lib/opencpi2/$file
            make_filtered_link $fromdir/$base.py exports/$platform/lib/opencpi2/$base.py
	}
    fi
  }
  shopt -u nullglob
  [ -n "$api_incs" ] && {
      for i in $api_incs; do
        make_filtered_link $i exports/include/aci/$(basename $i)
      done
  }
done < build/places

# Put the check file into the runtime platform dir
# FIXME: make sure if/whether this is really required and why
# Maybe: when the runtime is really a runtime config of a dev host?
check=$platform_dir/${platform}-check.sh
[ -r "$check" ] && {
  to=$(python3 -c "import os.path; print(os.path.relpath('"$check"', '.'))")
  make_relative_link $to exports/runtime/$platform/$(basename $check)
  # FIXME: make sure this is actually used and needed or maybe it should be used and isn't?
  cat <<-EOF > exports/runtime/$platform/${platform}-init.sh
	# This is the minimal setup required for runtime
	export OCPI_TOOL_PLATFORM=$platform
	export OCPI_TOOL_OS=$OcpiPlatformOs
	export OCPI_TOOL_DIR=$platform
	EOF
}
# Put the minimal set of artifacts to support the built-in runtime tests or
# any apps that rely on software components in the core project
rm -r -f exports/runtime/$platform/artifacts exports/$platform/artifacts
mkdir exports/runtime/$platform/artifacts exports/$platform/artifacts
for a in projects/core/artifacts/ocpi.core.*; do
  [ -f $a ] || continue
  link=`readlink -n $a`
  [[ $link == */target-*${platform}/* ]] && {
    make_relative_link $a exports/runtime/$platform/artifacts/$(basename $a)
    make_relative_link $a exports/$platform/artifacts/$(basename $a)
  }
done

# Ensure driver list is exported
mkdir -p exports/runtime/$platform/lib exports/$platform/lib
echo $drivers>exports/runtime/$platform/lib/driver-list
echo $drivers>exports/$platform/lib/driver-list

# Enable prerequisite libraries to be found/exported in our lib directory
function liblink {
  local dest=$2/$platform/lib/$(basename $1)
  if [ -L $1 ] ; then
    local L=$(readlink $1)
    if [[ "$L" != */* ]]; then
      [ ! -L $dest ] || [ "$L" != $(readlink $dest) ] || return 0
      rm -f $dest
      cp -R -P $1 $dest
      return
    fi
  fi
  make_relative_link $1 $dest
}
# Enable prerequisites to be found/exported in directory of choosing
function anylink {
  local base=$(basename $2)
  if [[ -L $2 && $(readlink $2) != */* ]]; then
    cp -R -P $2 $3/$platform/$1/$base
  else
    make_relative_link $2 $3/$platform/$1/$base
  fi
}
shopt -s nullglob
for p in prerequisites/*; do
  for l in $p/$platform/lib/*; do
    liblink $l exports
    if [[ $l == *.so || $l == *.so.* || $l == *.dylib ]]; then
       liblink $l exports/runtime
    fi
  done
done
# if some platform-specific prereqs need to be part of our exports... exporting those here
for p in $OcpiPlatformPrerequisites; do
  # Prerequisites can be in the form: <prerequisite>:<platform>
  # Below we are removing the : and everything after it so we are left with only the prereq
  p="prerequisites/${p%%:*}"
  for l in $p/$platform/*; do
    if [[ "$l" = *conf ]]; then
      for f in $l/*; do
        anylink "" $f exports
        anylink "" $f exports/runtime
      done
    elif [[ "$l" = *bin ]]; then
      for f in $l/*; do
        anylink bin $f exports
        anylink bin $f exports/runtime
      done
    fi
  done
done
