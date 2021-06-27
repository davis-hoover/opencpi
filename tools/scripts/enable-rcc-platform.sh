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
# This internal scripts calls the platform Makefile if it exists 
# in prepartion of enabling the platform.
# The first and only argument is platform name to be enabled. 
#

# Ensure CDK and TOOL variables
source ./cdk/opencpi-setup.sh -r

# Ensure TARGET variables
source "$OCPI_CDK_DIR/scripts/ocpitarget.sh" "$1"

set -e
echo ================================================================================
echo "We are running in $(pwd) where the git clone of opencpi has been placed."
echo ================================================================================

# If the platform itself needs to be "built", do it now.
if [ -f "$OCPI_TARGET_PLATFORM_DIR/Makefile" ] && [ ! -f "$OCPI_TARGET_PLATFORM_DIR/lib/$1.mk" ]; then
  echo "Building/preparing the software platform '$OCPI_TARGET_PLATFORM' which will enable building other assets for it."
  make -C "$OCPI_TARGET_PLATFORM_DIR"
elif [ -f "$OCPI_TARGET_PLATFORM_DIR/${OCPI_TARGET_PLATFORM}.exports" ]; then
  echo "Exporting files from the software platform '$OCPI_TARGET_PLATFORM' which will enable building other assets for it."
  (cd "$OCPI_TARGET_PLATFORM_DIR"; "$OCPI_CDK_DIR/scripts/export-platform.sh" lib)
fi
