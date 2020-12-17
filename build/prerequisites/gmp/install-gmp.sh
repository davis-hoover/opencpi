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
name=gmp
version=6.2.0  # latest as of 09/02/2020
pkg_name="$name-$version"
description='Extended Precision Numeric library'
dl_url="https://ftp.gnu.org/gnu/$name/${pkg_name}.tar.xz"
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
  $([ -z "$OcpiCrossHost" -a "$OCPI_DISTRO_BUILD" = "1" ] && \
    ( case "$OcpiPlatformOs" in
	# older bash versions require the ( in this particular case
        (macos) echo "--build=x86_64-unknown-darwin-gnu" ;;
        (linux) echo "--build=x86_64-unknown-linux-gnu" ;;
      esac ) || true) \
  --prefix="$OcpiInstallDir" --exec-prefix="$OcpiInstallExecDir" \
  --enable-fat=yes --enable-cxx=yes --with-pic
make -j4
make install

# Cleanup
rm -f "${OcpiInstallExecDir:?}/lib/*.la"
