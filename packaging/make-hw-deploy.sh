#!/bin/bash -e
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
[ -z "$1" ] && echo "Do not run this script by hand; it is a utility script for make rpm and make deploy" && exit 1
verbose=--quiet
[ "$1" = -v ] && verbose=-vv && shift
platform=$1 && shift
cross=0
[ -n "$1" ] && cross=1
shift
rcc_platform=$1 && shift
set -e
# If there is no rcc platform set hdl_rcc_platform to no_sw
[ "$rcc_platform" = "-" ] && rcc_platform=
cross=1
platforms=$platform
# copied functions
function found_in {
  local look=$1
  shift
  for i in $*; do [ $i = $look ] && return 0; done
  return 1
}

function is_platform {
 found_in `basename $1` $OCPI_ALL_RCC_PLATFORMS || found_in `basename $1` $OCPI_ALL_HDL_PLATFORMS
}

# 1. create the dir for the SD card
sd=`pwd`/cdk/$platform/sdcard-$rcc_platform
rm -r -f $sd
mkdir -p $sd/opencpi
# 2. copy runtime files into opencpi, preserving links that are within the same directory and skipping
#    some things.  This is somewhat redundant with how the runtime packaging prepare-list works...
for f in cdk/runtime/*; do
  is_platform $f && [ $(basename $f) != $rcc_platform ] && continue; # Skip all platforms except our RCC
  (cd cdk/runtime;
   for x in $(find $(basename $f)); do
       case $x in *env*|*include*) continue;; esac # not sure how to explain this
       if [ -d $x ]; then
	  mkdir $sd/opencpi/$x
       elif [ -L $x ] && [[ $(readlink $x) != */* ]]; then
	  cp -R $x $sd/opencpi/$x # keep symlink as is
       else
	  cp -R -H -L $x $sd/opencpi/$x # copy following links
       fi
   done)
done
# 3. move the sw deploy files into root
[ -d cdk/deploy/$rcc_platform ] && cp -R -L cdk/deploy/$rcc_platform/* $sd
# 4. mv the top level sw files on the hw deployment into root
[ -d cdk/deploy/$platform/$rcc_platform ] && cp -R -L cdk/deploy/$platform/$rcc_platform/* $sd
# 5. move any SW-specific system.xml into $sd/opencpi
[ -f cdk/runtime/$rcc_platform/system.xml ] && cp -R -L -H cdk/runtime/$rcc_platform/system.xml $sd/opencpi || :
# 6. copy hw-specific files from the rcc platform
[ -d cdk/$rcc_platform/hdl/$platform/boot ] && cp -R -L -H cdk/$rcc_platform/hdl/$platform/boot/* $sd || :
# 7. mv the top level hw files into root
for f in $(shopt -s nullglob; echo cdk/deploy/$platform/*); do
  is_platform $f && continue;
  cp -R -L -H $f $sd
done
