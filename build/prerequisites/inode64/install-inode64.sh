#!/bin/bash --noprofile
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
source $OCPI_CDK_DIR/scripts/setup-prerequisite.sh \
       "$1" \
       inode64 \
       "fix for 32 bit binaries running on 64-bit-inode file systems" \
       https://www.mjr19.org.uk/sw \
       inode64.c \
       . \
       0
# Only build/use this for centos for now
[[ "$OcpiPlatformOs" != linux || "$OcpiPlatformOsVersion" != c* ]] &&
  echo The inode64 package is not built for $OcpiPlatform, only CentOS*. Skipping it. &&
    exit 0
# Extract the version script from the comment
ed -s ../inode64.c <<-EOF
	/^GLIBC/
	ka
	/^};/
	'a,.w vers
	EOF
# These are from the comments in the source file
gcc -c -fPIC -m32 ../inode64.c
ld -shared -melf_i386 --version-script vers -o inode64.so inode64.o
relative_link inode64.so $OcpiInstallExecDir/lib

