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
name=gtest
version=1.8.1
#version=1.10.0  # latest as of 09/02/2020
pkg_name="release-$version"
description='Google C++ Test Library'
dl_url="https://github.com/google/googletest/archive/${pkg_name}.tar.gz"
extracted_dir="googletest-$pkg_name"
cross_build=1

# Download and extract source
source "$OCPI_CDK_DIR/scripts/setup-prerequisite.sh" \
       "$target_platform" \
       "$name" \
       "$description" \
       "${dl_url%/*}" \
       "${dl_url##*/}" \
       "$extracted_dir"\
       "$cross_build"

# According to their readme, they recommend simply compiling gtest-all.cc or
# using cmake. They have older autotools stuff but declare that legacy and
# unmaintained. We use the first recommended way, which is SIMPLEST. Their code
# does not use config.h etc.
dir=../googletest # srcdir
dynlib="libgtest$OcpiDynamicLibrarySuffix"
"$CXX" -fPIC "-I$dir/include" "-I$dir" -c "$dir/src/gtest-all.cc"
"$AR" -rs libgtest.a gtest-all.o
# shellcheck disable=SC2086
"$CXX" $OcpiDynamicLibraryFlags -o"$dynlib" gtest-all.o -lpthread
relative_link "$dir/include" "$OcpiInstallDir" # each platform creates this same link
relative_link libgtest.a "$OcpiInstallExecDir/lib"
relative_link "$dynlib" "$OcpiInstallExecDir/lib"
