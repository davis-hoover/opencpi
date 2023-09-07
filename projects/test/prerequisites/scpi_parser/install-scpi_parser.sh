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
name=scpi-parser
prereq_name=scpi_parser  # enforce asset naming rules: no hyphens allowed
version=2.2  # latest as of 12/06/2022
pkg_name="v$version" # yes this is correct, yes it is weird
description='SCPI instrumentation protocol'
dl_url="https://github.com/j123b567/$name/archive/refs/tags/$pkg_name.tar.gz"
extracted_dir="$name-$version"  # yes this is correct, yes it is weird
cross_build=0

# Download and extract source
source "$OCPI_CDK_DIR/scripts/setup-prerequisite.sh" \
       "$target_platform" \
       "$prereq_name" \
       "$description" \
       "${dl_url%/*}" \
       "${dl_url##*/}" \
       "$extracted_dir" \
       "$cross_build"

make -j4 -C ..
make PREFIX=$OcpiInstallDir LIBDIR=$OcpiInstallExecDir/lib -C .. install