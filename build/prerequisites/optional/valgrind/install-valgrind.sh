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

# This server is unavailable:       https://ftp.gnu.org/gnu/gmp
# Since we don't look at multiple URLs/mirrors (yet)
# The one below is one of the advertised mirrors
me=valgrind
v=3.15.0
[ -z "$OCPI_CDK_DIR" ] && echo Environment variable OCPI_CDK_DIR not set && exit 1
source $OCPI_CDK_DIR/scripts/setup-prerequisite.sh \
       "$1" \
       $me \
       "Valgrind Memory Checker" \
       https://sourceware.org/pub/$me \
       $me-$v.tar.bz2 \
       valgrind-$v \
       1

# We need to do autoconf, since we are patching at that level
here=`pwd`
cd ..
# remove compiler flags so we control them from our platform definition file
ed -s Makefile.all.am<<EOF
g/-marm -mcpu=cortex-a8/s///
w
EOF
# allow our (xilinx-style) arm type
ed -s configure.ac<<EOF
g/armv7\*)/s/armv7/arm/
w
EOF
./autogen.sh
cd $here
../configure --target=$OcpiCrossHost --host=$OcpiCrossHost CFLAGS="$OcpiCFlags" \
             --prefix=$OcpiInstallDir --exec-prefix=$OcpiInstallExecDir
make -j && make install
