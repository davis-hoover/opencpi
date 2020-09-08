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
name=myhostname
version=  # no version info
pkg_name="$name"
description='Library to inject a specific hostname by intercepting gethostname'
dl_url="./${pkg_name}.c"
extracted_dir=.
cross_build=0

# Download and extract source
source "$OCPI_CDK_DIR/scripts/setup-prerequisite.sh" \
       "$target_platform" \
       "$name" \
       "$description" \
       "${dl_url%/*}" \
       "${dl_url##*/}" \
       "$extracted_dir" \
       "$cross_build"

# Only build/use this for centos for now
if [[ "$OcpiPlatformOs" != linux || "$OcpiPlatformOsVersion" != c* ]]; then
  echo "The myhostname package is not built for $OcpiPlatform, only CentOS*. \
Skipping it."
  exit 0
fi

# This is quite linux x86-specific.  LD_PRELOAD has one way to use a library in
# a hierarchy of processes that are a mix of 64 and 32 bit executables, by
# using ${LIB} in the string expanded as lib64 for x86_64 and lib for x86_32.
gcc -Wall -fPIC -shared ../myhostname.c -o lib64myhostname.so
gcc -Wall -m32 -fPIC -shared ../myhostname.c -o libmyhostname.so
relative_link lib64myhostname.so "$OcpiInstallExecDir/lib"
relative_link libmyhostname.so "$OcpiInstallExecDir/lib"
