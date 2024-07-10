#!/bin/bash
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

set -e

echo Building Xilinx Yocto

cd gen/yocto

# add bitbake to path
#export PATH=$PWD/bitbake/bin:$OCPI_CDK_DIR/../prerequisites/tar/$OCPI_TOOL_DIR/bin:$PATH
source setupsdk

echo "MACHINE = \"zynqmp-generic\"" >> conf/local.conf
echo "XILINX_SDK_TOOLCHAIN = \"/mnt/ssd/tools/Xilinx/petalinux/2021.1/tools/xsct/\"" >> conf/local.conf

# kickoff yocto build
#./meta-ettus/contrib/build_imgs_package.sh n3xx v4.0.0.0 $PWD
bitbake petalinux-image-minimal

# add kernel sources to SDK
echo "TOOLCHAIN_TARGET_TASK_append = \" kernel-devsrc\"" >> build/conf/local.conf


# build toolchain
cd build
bitbake meta-toolchain
