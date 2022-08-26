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

# The "verilog-ethernet" library is used by the dgrdma primitive library to
# provide an Ethernet MAC implementation.

[ -z "$OCPI_CDK_DIR" ] && echo "Environment variable OCPI_CDK_DIR not set" && exit 1

OCPI_VERILOG_ETHERNET_VERSION=4af058fbdc49d6e8ff23db616160a112ec2393af

# Download and extract source
source "$OCPI_CDK_DIR/scripts/setup-prerequisite.sh" \
       "$1" \
       "verilog_ethernet" \
       "Verilog Ethernet Components used for DGRDMA" \
       https://github.com/alexforencich/verilog-ethernet.git \
       $OCPI_VERILOG_ETHERNET_VERSION \
       verilog-ethernet \
       0

# Patch the source
patch -p0 -d .. < $OcpiThisPrerequisiteDir/verilog-ethernet.patch || {
  echo "*******************************************************" >&2
  echo "ERROR: patch applied by verilog-ethernet.patch failed!!" >&2
  echo "*******************************************************" >&2
  exit 1
}

# Link the source into the installation directory
relative_link ../../verilog-ethernet "$OcpiInstallDir"
rmdir "$OcpiInstallExecDir"
