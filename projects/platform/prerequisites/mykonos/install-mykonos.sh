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

################################################################################
# Import and prepare the ADI "no_OS" library for using the ad9371 with OpenCPI
# ADI calls this library/interface "mykonos".
# We build the C code into an external library to incorporate into proxies.
# We also derive the xml properties file from the ADI headers.
# The API headers need some tweaks to not introduce bad namespace pollution
# Priorities are:
#   Allow use of their API to program the device
#   Try not to touch their SW at all.
#   Enable repeated installation, refresh etc.
#   Support host and cross compilation
#   Be similar to all other such prereq/import/cross-compilations
################################################################################
# 1. Download/clone and setup directories in the prereq area
################################################################################
OCPI_MYKONOS_CURRENT_GIT_COMMIT_ID=master
OCPI_MYKONOS_VERSION=$OCPI_MYKONOS_CURRENT_GIT_COMMIT_ID
[ -z "$OCPI_CDK_DIR" ] && echo Environment variable OCPI_CDK_DIR not set && exit 1
source $OCPI_CDK_DIR/scripts/setup-prerequisite.sh \
       "$1" \
       mykonos \
       "ADI mykonos library for ad9371" \
       https://github.com/analogdevicesinc/no-OS.git \
       $OCPI_MYKONOS_VERSION \
       no-OS \
       1
pwd
cp -r ../projects/ad9371/src/devices/{adi_hal,mykonos} .

################################################################################
# 2. Patch their API headers so they actually act like API headers
#    I.e. the patched version doesn't pollute the caller's namespace
################################################################################
echo Patching API headers
# dir=.
# patch -p0 < $OcpiThisPrerequisiteDir/mykonos.patch || {
#   echo "*******************************************************" >&2
#   echo "ERROR: patch applied by mykonos.patch failed!!" >&2
#   echo "*******************************************************" >&2
#   exit 1
# }
#################################################################################
# 3. Compile code into the library
################################################################################
# We are not depending on their IP
cd mykonos
DEFS=
SRCS=(*.c)
INCS=(mykonos.h ../adi_hal/common.h)
echo $CC -std=c99 -fPIC -I. -I../adi_hal $DEFS -c ${SRCS[@]}
$CC -std=c99 -fPIC -I. -I../adi_hal $DEFS -c ${SRCS[@]}
$AR -rs libmykonos.a ${SRCS[@]/%.c/.o}

################################################################################
# 4. Install the deliverables:  OPS file, headers and library
################################################################################
relative_link libmykonos.a $OcpiInstallExecDir/lib
for i in ${INCS[@]}; do
  relative_link $i $OcpiInstallDir/include/mykonos/
done
