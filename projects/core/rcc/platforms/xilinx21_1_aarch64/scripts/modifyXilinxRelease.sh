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

cd gen/release-artifacts

# Download generic kernel and rootfs built using yocto petalinux flow
# this is necessary due to Xilinx artifacts no longer matching linux-xlnx tags 
# as well as Xilinx not providing a sufficient rootfs 
echo Downloading Kernel and root filesystem 
curl https://opencpi-public.s3.us-east-2.amazonaws.com/toolchain/xilinx21_1_aarch64/zynqmp-generic-artifacts.tar.gz > zynqmp-generic-artifacts.tar.gz

# Extract tar ball 
echo Extracting downloaded Kernel and root filesystem
tar xvzf zynqmp-generic-artifacts.tar.gz

removeFiles="bl31.elf image.ub pmufw.elf system.bit u-boot.elf zynqmp_fsbl.elf"

# Remove extraneous files and add generic kernel and rootfsversion
for i in ./*; do
  if [ -d $i ]; then
    plat=$(basename $i)
    echo Replacing kernel and rootfs for $plat 
    cd $plat/boot
    rm -f $removeFiles
    cp ../../Image .
    cp ../../rootfs.cpio.gz.u-boot .
    cd ../.. 
  fi
done
