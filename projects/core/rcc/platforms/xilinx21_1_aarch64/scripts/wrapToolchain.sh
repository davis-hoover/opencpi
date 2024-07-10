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

sdk_dir=gen/sdk

# extract SDK
if [ -d $sdk_dir ]
then
  echo "SDK detected"
else
  mkdir -p $sdk_dir
  # extract SDK
  ./gen/petalinux-glibc-x86_64-meta-toolchain-cortexa72-cortexa53-zynqmp-generic-toolchain-2021.1.sh -y -d $sdk_dir
fi

# create wrappers
if [ ! -d gen/opencpi-bin ]
then
  mkdir -p gen/opencpi-bin
fi

cur_path=$PWD
root_path=${cur_path#"$OCPI_ROOT_DIR/"}
./scripts/mkwrapped aarch64-xilinx-linux- $root_path gen/opencpi-bin

