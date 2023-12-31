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

# Just check if it looks like we are in the source tree.
[ -d runtime -a -d build -a -d scripts -a -d tools ] || {
  echo "Error:  this script ($0) is not being run from the top level of the OpenCPI source tree."
  exit 1
}
set -e

#
# Quick and dirty argument parsing:
# getopt(s) overhead not required.
#
PARAMS=""

while (( "$#" )); do
  case "$1" in
    -d|--distro)
      export OCPI_DISTRO_BUILD=1
      shift
      ;;
    --minimal)
      minimal=1
      shift
      ;;
    --no-kernel)
      nokernel=1 # use ${nokernel:+whatever}
      shift
      ;;
    -*) # unsupported flags
      echo "Error: Unsupported flag $1" >&2
      exit 1
      ;;
    *) # preserve positional arguments
      PARAMS="$PARAMS \"$1\""
      shift
      ;;
  esac
done

# set positional arguments in their proper place
eval set -- "$PARAMS"
unset PARAMS

# We do some bootstrapping here (that is also done in the scripts we call), in order to know
# the platform we are building

# Ensure exports (or cdk) exists and has scripts
echo "Initializing OpenCPI CDK" in $(pwd -P)
source ./scripts/init-opencpi.sh

#
# At this point, if the first positional parameter is either not
# set or is set and NULL, we may safely assume this is a framework
# installation on a local RCC development platform.  In a probably
# futile attempt to protect users from themselves, try to unset
# "OCPI_*" environment variables that may negatively affect the
# installation process.
#
if [ -z "$1" ]; then
  echo "Target platform not specified: assuming framework installation on local RCC development platform"
  echo "Cleaning OpenCPI environment..."
  source ./cdk/opencpi-setup.sh -i -v
fi

# Ensure CDK and TOOL variables
OCPI_BOOTSTRAP="$(pwd)/cdk/scripts/ocpibootstrap.sh"; source "$OCPI_BOOTSTRAP"

source $OCPI_CDK_DIR/scripts/util.sh
# This will set OCPI_TARGET_* vars
echo -n "Finding target platform ... "
source "$OCPI_CDK_DIR/scripts/ocpitarget.sh" "$1" -
if [ -z "$OCPI_TARGET_PLATFORM_DIR" ]; then
  echo "Cannot find platform '$1'"
  exit 1
fi
echo "Found '$OCPI_TARGET_PLATFORM' ($OCPI_TARGET_PLATFORM_DIR)"

[ -n "$1" ] && shift
if [ -n "$OCPI_TARGET_PLATFORM" -a "$OCPI_TOOL_PLATFORM" != "$OCPI_TARGET_PLATFORM" ]; then
  echo "Assuming development host platform $OCPI_TOOL_PLATFORM is already installed."
fi

# Allow this to build for platforms defined in the inactive project or in osps
# that are not already registered
[ -z "$OCPI_PROJECT_PATH" ] && export OCPI_PROJECT_PATH="$(pwd)/projects/inactive"
registry=$(getProjectRegistryDir)
for i in $(shopt -s nullglob; echo projects/osps/*); do
  direct=$(cd $i; pwd -P)
  for p in $(shopt -s nullglob; echo $registry/*); do
    [ "$direct" = "$(cd $p; pwd -P)" ] && echo OSP $i already registered && continue 2
  done
  [ -d "$i/rcc/platforms" ] && OCPI_PROJECT_PATH="$OCPI_PROJECT_PATH:$(pwd)/$i"
done

# Make sure we are running in a mode without any platform exports since this installation phase
# should *not* depend on platform exports.  This essentially unexports the platform
OCPI_TARGET_PLATFORM_DIR="${OCPI_TARGET_PLATFORM_DIR%/lib}"
rm -r -f "${OCPI_TARGET_PLATFORM_DIR:?}/lib"


# We assume that install-packages.sh and install-prerequisites.sh do NOT depend on the platform's exports
./build/install-packages.sh "$OCPI_TARGET_PLATFORM"
# Export RCC platform
$OCPI_CDK_DIR/scripts/enable-rcc-platform.sh "$OCPI_TARGET_PLATFORM"
./build/install-prerequisites.sh "$OCPI_TARGET_DIR"

# Build framework and built-in projects for target platform
eval $* ./build/build-opencpi.sh ${minimal:+--minimal} ${nokernel:+--no-kernel} "$OCPI_TARGET_DIR"

# Run RCC unit tests
if [ -n "$OCPI_TARGET_PLATFORM" -a "$OCPI_TOOL_PLATFORM" != "$OCPI_TARGET_PLATFORM" ]; then
  echo "When building/installing for cross-compiled platform $OCPI_TARGET_DIR, we are skipping tests."
elif [ -n "$minimal" ]; then
  echo "Avoiding installation tests since the --minimal option was given."
  echo 'Installation tests may be run at any time using the "ocpitest --nohdl" command.'
else
  eval $* ./scripts/test-opencpi.sh --no-hdl ${nokernel:+--no-kernel}
fi
