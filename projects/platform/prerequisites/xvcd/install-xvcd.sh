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
# Compile and install Xilinx Virtual Cable Driver (xvcd) to support programming 
# of flash and fpga for the picoevb platform. 
################################################################################
[ -z "$OCPI_CDK_DIR" ] && echo 'Environment variable OCPI_CDK_DIR not set' && exit 1

# determine this script location
scriptDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
xvcdPackage=xvcd
xvcdDescription="Xilinx Virtual Cable Driver"

################################################################################
# 1. Download/clone and setup directories in the prereq area
################################################################################
COMMIT_ID=d42b07f70cffd9e53f41c33b3960e1474cfbfc04
source $OCPI_CDK_DIR/scripts/setup-prerequisite.sh \
       "$1" \
       xvcd \
       "Xilinx Virtual Cable Driver" \
       https://github.com/RHSResearchLLC/xvcd.git \
       $COMMIT_ID \
       xvcd \
       0

# since this package does not use automake, it is not prepared for vpath mode
# (using ../configure from a build directory), so we have to snapshot the code for each platform
echo Copying git repo checkout contents for building in `pwd`
base=$(basename `pwd`)
(cd ..; cp -R $(ls . | grep -v ocpi-build-) $base)

# save variables for future use since there's a prereq in a prereq 
xvcdInstallDir=$OcpiInstallDir
xvcdInstallExecDir=$OcpiInstallExecDir
xvcdBuildDir=$OCPI_PREREQUISITES_BUILD_DIR
xvcdInstallDir=$OCPI_PREREQUISITES_INSTALL_DIR

################################################################################
# 2. download, patch, and build libftdi 
################################################################################
# download and extract source within xcvd dir 
export OCPI_PREREQUISITES_BUILD_DIR=$OCPI_PREREQUISITES_BUILD_DIR/$xvcdPackage/lib
export OCPI_PREREQUISITES_INSTALL_DIR=$OcpiInstallDir/lib

source "$OCPI_CDK_DIR/scripts/setup-prerequisite.sh" \
       "$1" \
       "libftdi" \
       "XVCD libftdi prerequisite library" \
       https://www.intra2net.com/en/developer/libftdi/download/ \
       libftdi-0.20.tar.gz \
       libftdi-0.20 \
       0

# since this package does not use automake, it is not prepared for vpath mode
# (using ../configure from a build directory), so we have to snapshot the code for each platform
echo Copying git repo checkout contents for building in `pwd`
base=$(basename `pwd`)
(cd ..; cp -R $(ls . | grep -v ocpi-build-) $base)

# patch libftdi 
echo Patching libftdi
dir=.
patch -p0 < $scriptDir/libftdi.patch || {
	  echo "*******************************************************" >&2
  echo "ERROR: patch applied by libftdi.patch failed!!" >&2
    echo "*******************************************************" >&2
      exit 1
      }

echo Performing '"./configure"'
./configure ${OcpiCrossHost:+--host=$OcpiCrossHost} \
	  --prefix=$OcpiInstallDir --exec-prefix=$OcpiInstallExecDir \
	    --includedir=$OcpiInstallDir/include --with-async-mode\
	      CFLAGS=-g CXXFLAGS=-g 
make
make install

libftdiInstallDir=$OcpiInstallDir
libftdiInstallExecDir=$OcpiInstallExecDir

################################################################################
# 3. build xvcd
################################################################################
# find way back to top level prereq 
xvcdBuildDir=$xvcdBuildDir/$xvcdPackage/$xvcdPackage/ocpi-build-$OCPI_TARGET_DIR
cd $xvcdBuildDir/linux/src

echo Building xvcd
C_INCLUDE_PATH=$libftdiInstallDir/include LIBRARY_PATH=$libftdiInstallExecDir/lib make

# move binary to appropriate location
mkdir -p $xvcdInstallExecDir/bin
cp xvcd $xvcdInstallExecDir/bin/$xvcdPackage

# rewrite variables 
export description=$xvcdDescription
export package=$xvcdPackage
