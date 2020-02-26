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

####################################################################################################
# Create a software platform using the standard xilinx offerings:
# Eventually this will be some sort of ocpidev command.
# For now it will be a top-level script
#
# Args are:
# 1. project in which to create the platform
# 2. Xilinx-style release identifier (e.g. 2019.2)
# 3. processor architecture (aarch32 or aarch64 for now)
# 4. kernel repo linux tag (defaults)
# 5. kernel repo u-boot tag (defaults)
# 6. tool-prefix?

set -e
[ -z "$1" -o "$1" = --help ] && {
  cat <<-EOF
	Create a Xilinx RCC Software Platform.
	This command must run in the top level of the OpenCPI source tree.
	Usage is: $(basename $0) <project> <xilinx-release> <arch> [<linux-repo-tag> [<uboot-repo-tag>]]
	<arch> is arm, aarch32 or aarch64
EOF
  exit 1
}
[ -z "$OCPI_CDK_DIR" ] && echo Cannot run without OCPI_CDK_DIR. && exit 1
source $OCPI_CDK_DIR/scripts/util.sh
project=$1
release=$2
arch=$3
tag=$4
utag=$5
export OCPI_XILINX_VIVADO_SDK_VERSION=$2
setVarsFromMake $OCPI_CDK_DIR/include/xilinx/xilinx.mk ShellIseVars=1
sdk=$OcpiXilinxSdkDir
if [ -z "$sdk" ] ; then
  echo Could not find Xilinx SDK installed for Xilinx release $release.
  err=1
else
  echo Xilinx SDK for release $release found here: $sdk.
fi
xilinx_releases=$OCPI_XILINX_ZYNQ_RELEASE_DIR
[ -z $OCPI_XILINX_ZYNQ_RELEASE_DIR ] && xilinx_releases=$OcpiXilinxDir/ZynqReleases || :
if [ -d $xilinx_releases ]; then
    if [ -d "$xilinx_releases/$release" ]; then
	echo "Xilinx Zynq binary release(s) found in $xilinx_releases/${release}"
    else
	echo Error:  No Xilinx Zynq Release $release found at $xilinx_releases && err=1
	err=1
    fi
else
  echo No Xilinx Zynq releases found at $xilinx_releases
  err=1
fi
[ -n "$err" ] && echo Errors found.  &&exit 1
projdir=projects/$project
[ -d $projdir ] || (echo Project does not exists: $project && exit 1)
yq=${release#20}
version=${yq/\./_}
platform=xilinx${version}_$arch
echo Creating RCC platform \"$platform\" in project \"${project}\"
dir=$projdir/rcc/platforms/$platform
[ -d $dir ] && echo The platform directory $dir already exists. && exit 1
mkdir -p $dir
cat > $dir/Makefile <<-EOF
	include \$(OCPI_CDK_DIR)/include/xilinx/xilinx-rcc-platform.mk
	EOF
cat > $dir/$platform.mk <<-EOF
	${tag:+OcpiXilinxLinuxRepoTag:=}$tag
	${utag:+OcpiXilinxUbootRepoTag:=}$utag
	include \$(OCPI_CDK_DIR)/include/xilinx/xilinx-rcc-platform-definition.mk
	OcpiPlatformOs:=linux
	OcpiPlatformOsVersion:=$version
	OcpiPlatformArch:=$arch
	EOF
cat > $dir/$platform.exports <<-EOF
	# kernel exports for driver building - just the headers package, and only for development
	+<platform-dir>/gen/kernel-artifacts/kernel-headers.tgz <target>/

	# Release files for hdl platforms for this rcc platform
	# This assumes that all the files from release artifacts are hdl platform-specific
	# earlier releases had platform-agnostic boot files, but they are normalized when imported
	# so in all cases boot files appear hdl-platfform-specific
	# These (development) files will be used during deployment to create SD card (boot) files
	# This implies you need a development package to make the SD cards
	+<platform-dir>/gen/release-artifacts/* <target>/hdl/

	# sdk - just the libs, needed at runtime for ocpiremote, and for deployment
	=<platform-dir>/gen/sdk-artifacts/lib <target>/sdk/


	# Use the default zynq file unless overridden by hardware
	=platforms/zynq/zynq_system.xml <target>/system.xml
	EOF
make -C $projdir exports # pre local exports (no lib/)
make -C $dir exports
make -C $projdir exports # post local exports

