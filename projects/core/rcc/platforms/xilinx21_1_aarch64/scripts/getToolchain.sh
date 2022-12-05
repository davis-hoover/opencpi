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
gen_dir=gen

mkdir -p $gen_dir

toolchain_filename=petalinux-glibc-x86_64-meta-toolchain-cortexa72-cortexa53-zynqmp-generic-toolchain-2021.1.sh

if [ ! -f "gen/$toolchain_filename" ]; then

  # Downloading Petalinux Toolchain 
  cd $gen_dir
  curl https://opencpi-public.s3.us-east-2.amazonaws.com/toolchain/xilinx21_1_aarch64/$toolchain_filename \
         --output $toolchain_filename
  chmod a+x $toolchain_filename

else
    echo "Toolchain file found, skipping download."
fi
