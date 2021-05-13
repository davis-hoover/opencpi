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

# Ensure exports and python
source ./scripts/init-opencpi.sh
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

# Export ocpi python libraries needed in later steps, avoiding any platform exports
if ! ./scripts/export-framework.sh - &> /tmp/tmp.$$; then
  echo 'Error running "export-framework.sh -":'
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
echo "Now we will build the OpenCPI framework libraries and utilities for $OCPI_TARGET_DIR"
make
# Build the man pages
echo "Now we will build the OpenCPI manual pages for command line utilities"
make man

[ -n "$2" ] && exit 0

# Build kernel module
echo ================================================================================
if [[ -n "$OcpiCrossCompile" && -z "$OcpiKernelDir" ]]; then
  echo "This cross-compiled platform does not indicate where kernel headers are found."
  echo "I.e. the OcpiKernelDir variable is not set in the software platform definition."
  echo "Thus building the OpenCPI kernel device driver for $OCPI_TARGET_PLATFORM is skipped."
elif [[ (-e /.dockerenv || -e /run/.containerenv) && -z "$OcpiCrossCompile" ]]; then
  echo "Docker, or docker like, environment detected. Building kernel device"
  echo "driver is not supported in this environment. Thus building the OpenCPI"
  echo "kernel device driver for $OCPI_TARGET_PLATFORM is skipped."
else
  echo "Next, we will build the OpenCPI kernel device driver for $OCPI_TARGET_PLATFORM"
  make driver
fi

Projects="core platform assets assets_ts inactive tutorial"
# Build built-in RCC components
echo ================================================================================
echo "Now we will build the built-in RCC '(software)' components for $OCPI_TARGET_DIR"
for p in $Projects; do make -C projects/$p rcc; done

# Build built-in OCL components
echo ================================================================================
echo "Now we will build the built-in OCL '(GPU)' components for the available OCL platforms"
for p in $Projects; do make -C projects/$p ocl; done

# Build built-in HDL components
# [ -n "$HdlPlatforms" -o -n "$HdlPlatform" ] && {
  echo ================================================================================
  echo "Now we will build the built-in HDL components for platforms: $HdlPlatform $HdlPlatforms"
  echo "Even if there are no HDL platforms, this step is still needed to build proxies"
  for p in $Projects; do make -C projects/$p hdl HdlPlatforms="$HdlPlatforms $HdlPlatform"; done
# }

# Build tests
echo ================================================================================
echo "Now we will build the core tests for $OCPI_TARGET_DIR"
make -C projects/core test
echo ================================================================================
echo "Now we will build the example applications in assets and inactive projects for $OCPI_TARGET_DIR"
make -C projects/assets applications
make -C projects/inactive applications

# Ensure any framework exports that depend on built projects happen
make exports Platforms="$OCPI_TARGET_DIR"

echo ================================================================================
echo "OpenCPI has been built for $OCPI_TARGET_DIR, with software components, examples and kernel driver"
