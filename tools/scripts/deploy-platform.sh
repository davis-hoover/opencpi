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

####################################################################################################
# This internal script creates a directory that can be copied
# to bootable media for a system consisting of platforms.
# The first argument is the primary RCC platform, and the rest
# are other platforms.
# Initially the only real supported combination is a standalone
# RCC platform or an RCC platform combined with an HDL platform.
# It is expected/assumed that all mentioned platforms have already
# been installed independently, so in fact, all the inputs should
# be in the CDK/framework tree already.
# It is expected to be called with OCPI_CDK_DIR set as normal.
#
[ "$1" = -v ] && verbose=-v && shift
rcc_platform=$1 && shift
[ -n "$1" ] && hdl_platform=$1 && shift

set -e

source $OCPI_CDK_DIR/scripts/util.sh

function getvars {
  setVarsFromMake $OCPI_CDK_DIR/include/hdl/hdl-targets.mk ShellHdlTargetsVars=1
  setVarsFromMake $OCPI_CDK_DIR/include/rcc/rcc-targets.mk ShellRccTargetsVars=1
  if isPresent $rcc_platform $RccAllPlatforms; then
    v=RccPlatDir_$rcc_platform
    rcc_platform_dir=`echo ${!v} | sed 's=^.*/projects/=./projects/='`
  else
    echo "Error: invalid RCC platform \"$rcc_platform\"" >&2
    return 1
  fi
  if [ "$hdl_platform" ]; then
    if isPresent $hdl_platform $HdlAllPlatforms; then
      v=HdlPlatformDir_$hdl_platform
      hdl_platform_dir=`echo ${!v} | sed 's=^.*/projects/=./projects/='`
    else
      echo "Error: invalid HDL platform \"$hdl_platform\"" >&2
      return 1
    fi
  fi
  return 0
}

# copied functions
function found_in {
  local look=$1
  shift
  for i in $*; do [ $i = $look ] && return 0; done
  return 1
}

function is_platform {
 found_in `basename $1` $RccAllPlatforms || found_in `basename $1` $HdlAllPlatforms
}

#
# Need to be in the "opencpi" base directory for
# the calls to "export-platform-to-framework.sh"
# which relies on "build/places".
#
cd $OCPI_CDK_DIR/..

#
# Check validity of platform arguments, and
# set a few variables we will need later.
#
getvars

#
# Next commented-out section for diagnosing export-related
# issues.  Does not hurt to re-export things, but we should
# not have to, i.e., everything we need should already be
# exported as a consequence of installing the platforms.
#
# Redo exports for the platforms of interest before we do anything else.
#
#$OCPI_CDK_DIR/scripts/export-platform-to-framework.sh $verbose rcc $rcc_platform $rcc_platform_dir
#[ -z "$hdl_platform" ] || \
#  $OCPI_CDK_DIR/scripts/export-platform-to-framework.sh $verbose hdl $hdl_platform $hdl_platform_dir

#
# Everything below this point is done from the CDK directory.
#
cd $OCPI_CDK_DIR

####################################################################################################
# The basic idea here is to establish the SD card contents with the files from the software platform
# as a baseline, and then overlay any hardware platform files on top of that.

# create the dir for the SD card
sd=$hdl_platform/sdcard-$rcc_platform
rm $verbose -rf $sd
mkdir $verbose -p $sd/opencpi
# Add a proper first "release" argument when we have that file in the source tree
if [ "$verbose" ]
then
  echo "Release is \"opencpi-v2.0.0 $rcc_platform $hdl_platform\"."
fi
echo opencpi-v2.0.0 $rcc_platform $hdl_platform  > $sd/opencpi/release

####################################################################################################
# Prepare the "boot" or SD root directory from various sources.  These are not OpenCPI files.

# 1. move the RCC platform's generic (hw-independent) deploy files into the SD root, if any
[ ! -d deploy/$rcc_platform ] || cp $verbose -R -L deploy/$rcc_platform/* $sd

# 2. move hw-specific files from the RCC platform's *development* exports into the SD root, if any
[ -z "$hdl_platform" -o ! -d $rcc_platform/hdl/$hdl_platform/boot ] ||
    cp $verbose -R -L -H $rcc_platform/hdl/$hdl_platform/boot/* $sd

# 3. move the top level deploy sw files from the HW platform's deployment into the SD root, if any
[ -z "$hdl_platform" -o ! -d deploy/$hdl_platform/$rcc_platform ] ||
    cp $verbose -R -L deploy/$hdl_platform/$rcc_platform/* $sd

# 4. move the top level hw files (not specific to any SW platform) into the SD root, if any
[ -z "$hdl_platform" ] || for f in $(shopt -s nullglob; echo deploy/$hdl_platform/*); do
  is_platform $f && continue;
  cp $verbose -R -L -H $f $sd
done

####################################################################################################
# Prepare the opencpi/ directory on the SD card, which is the deployed CDK

# 1. copy sw runtime files into $sd/opencpi/, preserving links that are within the same directory and
#    skipping some things, like anything for other platforms.  This is somewhat redundant with how
#    the runtime packaging prepare-list works...

for f in runtime/*; do
  is_platform $f && [ $(basename $f) != $rcc_platform ] && continue; # Skip all platforms except our RCC
  (cd runtime;
   for x in $(find -L $(basename $f)); do
       case $x in *env*|*include*) continue;; esac # not sure how to explain this
       if [ -d $x ]; then
	  mkdir $verbose ../$sd/opencpi/$x
       elif [ -L $x ] && [[ $(readlink $x) != */* ]]; then
	  cp $verbose -R $x ../$sd/opencpi/$x # keep symlink as is
       else
	  cp $verbose -R -H -L $x ../$sd/opencpi/$x # copy following links
       fi
   done)
done

# 2. move any SW-specific system.xml into $sd/opencpi
[ ! -f runtime/$rcc_platform/system.xml ] || cp $verbose -R -L -H runtime/$rcc_platform/system.xml $sd/opencpi

# 3. copy in one bit stream file for loading and testing
[ -n "$hdl_platform" ] || exit 0
mkdir $verbose -p $sd/opencpi/artifacts
cp $verbose -L ../projects/assets/hdl/assemblies/testbias/container-testbias_${hdl_platform}_base/target-*/*.bitz \
   $sd/opencpi/artifacts
