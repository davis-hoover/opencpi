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
# We do some bootstrapping here (that is also done in the scripts we call), in order to know
# whether the platform we are building

# Ensure exports (or cdk) exists and has scripts
source ./scripts/init-opencpi.sh
# Ensure CDK and TOOL variables
OCPI_BOOTSTRAP=`pwd`/cdk/scripts/ocpibootstrap.sh; source $OCPI_BOOTSTRAP
platform=$1
[ -n "$1" ] && shift
if test -n "$platform" -a "$OCPI_TOOL_PLATFORM" != "$platform"; then
  echo Assuming development host platform $OCPI_TOOL_PLATFORM is already installed.
#  ./scripts/install-packages.sh $OCPI_TOOL_PLATFORM
  # This should check if a successful prereq install has been done
  # It should also just to "host" prerequisites, not "runtime" or "project" prerequisites
#  ./scripts/install-prerequisites.sh $OCPI_TOOL_PLATFORM
#  ./build/build-opencpi.sh "" -
fi
# Allow this to build for platforms defined in the inactive project or in osps
[ -z "$OCPI_PROJECT_PATH" ] && export OCPI_PROJECT_PATH=`pwd`/projects/inactive
for i in $(shopt -s nullglob; echo projects/osps/*); do
  [ -d $i/rcc/platforms ] && OCPI_PROJECT_PATH=$OCPI_PROJECT_PATH:`pwd`/$i
done
# Finding the platform should not depend on whether it is exported or not
source $OCPI_CDK_DIR/scripts/ocpitarget.sh $platform
[ -z "$OCPI_TARGET_PLATFORM_DIR" ] && echo Cannot find platform $platform && exit 1
# Make sure we are running in a mode without any platform exports since this installation phase
# should *not* depend on platform exports.  This essentially unexports the platform
OCPI_TARGET_PLATFORM_DIR=${OCPI_TARGET_PLATFORM_DIR%/lib}
rm -r -f $OCPI_TARGET_PLATFORM_DIR/lib
# We assume that install-packages.sh and install-prerequisites.sh do NOT depend on the platform's exports
./build/install-packages.sh $platform
./build/install-prerequisites.sh $platform
# If the platform itself needs to be "built", do it now.
if [ -f $OCPI_TARGET_PLATFORM_DIR/Makefile ]; then
  echo Building/preparing the software platform \"$platform\" which will enable building other assets for it.
  make -C $OCPI_TARGET_PLATFORM_DIR
elif [ -f $OCPI_TARGET_PLATFORM_DIR/$platform.exports ]; then
  echo Exporting files from the software platform \"$platform\" which will enable building other assets for it.
  (cd $OCPI_TARGET_PLATFORM_DIR; $OCPI_CDK_DIR/scripts/export-platform.sh lib)
fi
echo Exporting the platform \"$platform\" from its project.
project=$(cd $OCPI_TARGET_PLATFORM_DIR/../../..; pwd)
project=${project%/exports}
make -C $project exports
eval $* ./build/build-opencpi.sh $platform
if [ -n "$platform" -a "$OCPI_TOOL_PLATFORM" != "$platform" ]; then
  echo When building/installing for cross-compiled platform $platform, we are skipping tests.
else
  eval $* ./scripts/test-opencpi.sh --no-hdl
fi
