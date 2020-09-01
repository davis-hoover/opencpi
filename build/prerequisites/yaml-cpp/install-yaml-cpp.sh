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

[ -z "$OCPI_CDK_DIR" ] && echo Environment variable OCPI_CDK_DIR not set && exit 1

name=yaml-cpp
version=0.6.3
description="YAML parsing and emitting library for C++"
dl_url=https://github.com/jbeder/yaml-cpp/archive/yaml-cpp-0.6.3.tar.gz
dir="$name-$version"
extracted_dir="$name-$name-$version"  # yes this is correct, yes it is werid
cross_build=0  # disabled until needed. Update `build/places` when enabled.
target_platform="$1"

# Download and extract source
source "$OCPI_CDK_DIR/scripts/setup-prerequisite.sh" \
       "$target_platform" \
       "$name" \
       "$description" \
       "$(dirname "$dl_url")" \
       "$(basename "$dl_url")" \
       "$extracted_dir" \
       "$cross_build"

# CentOS 7 needs to use `cmake3` as `cmake` is cmake 2. All other OS's have
# `cmake` as cmake 3.
CMAKE=cmake
if [ -n "$(command -v cmake3)" ]; then
  CMAKE=cmake3
fi

# Build/Test/Install (static lib)
# usually with cmake you mkdir build && cd build. However, we are already in
# an empty directory for the target platform so we will use that instead.
"$CMAKE" -DCMAKE_INSTALL_PREFIX="$OcpiInstallExecDir" \
  -DYAML_CPP_BUILD_TESTS=OFF -DYAML_BUILD_SHARED_LIBS=OFF ..
make -j4
make install

# Build/Test/Install (shared lib)
# Shared lib must be built separately as there is not the option to build
# both static and shared at same time.
make clean
"$CMAKE" -DCMAKE_INSTALL_PREFIX="$OcpiInstallExecDir" \
  -DYAML_CPP_BUILD_TESTS=OFF -DYAML_BUILD_SHARED_LIBS=ON ..
make -j4
make install
