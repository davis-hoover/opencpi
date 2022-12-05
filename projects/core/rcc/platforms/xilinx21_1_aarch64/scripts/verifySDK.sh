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

# This script works around the fact Yocto SDK's use absolute paths. OpenCPI CI
# moves artifacts between jobs and runners which break paths to the toolchain.
# Before compiling this script is ran to validate the path, if it's not valid
# extract the SDK again to correct them.

set -e

#echo "Checking for valid SDK"

if [ ! -d $SDKTARGETSYSROOT ]
then
  SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
  platform_dir=$( dirname "$SCRIPT_DIR" )
  #echo "Invalid SDK detected"
  #echo "Removing old SDK"
  rm -rf $platform_dir/gen/sdk
  #echo "Re-Extracting SDK"
  $platform_dir/gen/petalinux-glibc-x86_64-meta-toolchain-cortexa72-cortexa53-zynqmp-generic-toolchain-2021.1.sh -y -d $platform_dir/gen/sdk
  source $platform_dir/gen/sdk/environment-setup*
  #echo "Re-Prepare Kernel"
  make -C $platform_dir/gen/sdk/sysroots/cortexa9t2hf-neon-oe-linux-gnueabi/lib/modules/5.10.0-xilinx-v2021.1/build scripts
  make -C $platform_dir/gen/sdk/sysroots/cortexa72-cortexa53-xilinx-linux/lib/modules/5.10.0-xilinx-v2021.1/build prepare
fi
