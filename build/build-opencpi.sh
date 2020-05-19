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
# Build the framework and the projects

# Ensure CDK and TOOL variables
source ./cdk/opencpi-setup.sh -e

# Ensure TARGET variables
source "$OCPI_CDK_DIR/scripts/ocpitarget.sh" "$1"

set -e
echo ================================================================================
echo "We are running in $(pwd) where the git clone of opencpi has been placed."
echo ================================================================================

# If the platform itself needs to be "built", do it now.
if [ -f "$OCPI_TARGET_PLATFORM_DIR/Makefile" ]; then
  echo "Building/preparing the software platform '$OCPI_TARGET_PLATFORM' which will enable building other assets for it."
  make -C "$OCPI_TARGET_PLATFORM_DIR"
elif [ -f "$OCPI_TARGET_PLATFORM_DIR/${OCPI_TARGET_PLATFORM}.exports" ]; then
  echo "Exporting files from the software platform '$OCPI_TARGET_PLATFORM' which will enable building other assets for it."
  (cd "$OCPI_TARGET_PLATFORM_DIR"; "$OCPI_CDK_DIR/scripts/export-platform.sh" lib)
fi

# Export ocpi python libraries needed in later steps
if ! make exports &> /tmp/tmp.$$; then
  echo 'Error running "make exports":'
  cat /tmp/tmp.$$
  rm -f /tmp/tmp.$$
  exit 1
fi
rm -f /tmp/tmp.$$

# Export platform from its project
echo "Exporting the platform '$OCPI_TARGET_PLATFORM' from its project."
project=$(cd "$OCPI_TARGET_PLATFORM_DIR/../../.."; pwd)
project=${project%/exports}
make -C "$project" exports

# Build the framework
echo "Now we will build the OpenCPI framework libraries and utilities for $OCPI_TARGET_PLATFORM"
make
[ -n "$2" ] && exit 0

# Build kernel module
echo ================================================================================
if [ -n "$OcpiCrossCompile" -a -z "$OcpiKernelDir" ]; then
  echo "This cross-compiled platform does not indicate where kernel headers are found."
  echo "I.e. the OcpiKernelDir variable is not set in the software platform definition."
  echo "Thus building the OpenCPI kernel device driver for $OCPI_TARGET_PLATFORM is skipped."
else
  echo "Next, we will build the OpenCPI kernel device driver for $OCPI_TARGET_PLATFORM"
  make driver
fi

Projects="core platform assets inactive"
# Build built-in RCC components
echo ================================================================================
echo "Now we will build the built-in RCC '(software)' components for $OCPI_TARGET_PLATFORM"
for p in $Projects; do make -C projects/$p rcc; done

# Build built-in OCL components
echo ================================================================================
echo "Now we will build the built-in OCL '(GPU)' components for the available OCL platforms"
for p in $Projects; do make -C projects/$p ocl; done

# Build built-in HDL components
[ -n "$HdlPlatforms" -o -n "$HdlPlatform" ] && {
  echo ================================================================================
  echo "Since HdlPlatform(s) are specified, we will build the built-in HDL components for: $HdlPlatform $HdlPlatforms"
  for p in $Projects; do make -C projects/$p hdl; done
}

# Build tests
echo ================================================================================
echo "Now we will build the tests and examples for $OCPI_TARGET_PLATFORM"
make -C projects/core test
make -C projects/assets applications
make -C projects/inactive applications

# Ensure any framework exports that depend on built projects happen
make exports Platforms="$OCPI_TARGET_PLATFORM"

echo ================================================================================
echo "OpenCPI has been built for $OCPI_TARGET_PLATFORM, with software components, examples and kernel driver"
