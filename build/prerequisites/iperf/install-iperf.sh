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

[ -z "$OCPI_CDK_DIR" ] && echo 'Environment variable OCPI_CDK_DIR not set' && exit 1

target_platform="$1"
name=iperf
version=3.9  # latest as of 08/17/2020 is 3.9
pkg_name="$name-$version"
description="Network measurement"
dl_url="https://github.com/esnet/iperf/archive/$version.tar.gz"
extracted_dir="$pkg_name"
cross_build=1

# Download and extract source
source "$OCPI_CDK_DIR/scripts/setup-prerequisite.sh" \
       "$target_platform" \
       "$name" \
       "$description" \
       "${dl_url%/*}" \
       "${dl_url##*/}" \
       "$extracted_dir" \
       "$cross_build"

echo Performing '"./configure"'

../configure --host=$OcpiCrossHost --without-openssl --prefix=$OcpiInstallDir --exec-prefix=$OcpiInstallExecDir --enable-static --disable-shared

make -j4
make install

rm -r -f "$OcpiInstallExecDir/lib" #comment out if you want to keep the libraries.
echo rm -r -f "$OcpiInstallExecDir/lib"
