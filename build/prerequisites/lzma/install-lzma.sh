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
name=lzma
version=5.2.5  # latest as of 09/02/2020
pkg_name="xz-$version"
description='LZMA2 compression library'
dl_url="https://opencpi-repo.s3.us-east-2.amazonaws.com/prerequisites/${pkg_name}.tar.gz"
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

# Configure/Make/Install
../configure "${OcpiCrossHost:+--host=$OcpiCrossHost}" \
  --prefix="$OcpiInstallDir" --exec-prefix="$OcpiInstallExecDir" \
  --enable-shared=yes --enable-static --disable-symbol-versions \
  --disable-xz --disable-xzdec --disable-lzmadec --disable-lzmainfo --disable-lzma-links \
  --disable-scripts --disable-doc \
  --with-pic=liblzma \
  CFLAGS="-g -fPIC" CXXFLAGS="-g -fPIC" # why doesn't with-pic to this?
make -j4
make install

# Cleanup
# lzma creates an empty directory even when we have disabled the executables
rm -rf "${OcpiInstallExecDir:?}/bin"
rm -rf "${OcpiInstallExecDir:?}/lib/pkgconfig"
rm  -f "${OcpiInstallExecDir:?}/lib/*.la"
rm -rf "${OcpiInstallDir:?}/share"
