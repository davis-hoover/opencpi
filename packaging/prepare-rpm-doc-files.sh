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

##########################################################################################
# This script, executed within the doc RPM spec file, is a greatly
# simplified version of the more generic "prepare-rpm-files.sh".
#
# Note the following significant differences from "prepare-rpm-files.sh":
# (1) No "package" arg (passed as "$1") because this script
#     is only for the doc RPM.  Other positional parameters
#     are as for "prepare-rpm-files.sh" but shifted by one.
# (2) The "cross" argument is expected and consumed for the
#     sake of consistency, but it is not used.
# (3) There is no "$builddir/$package-files" file produced.
# (4) We need an extra "version" arg (passed as "$6") because
#     RPM_VERSION is not in the passed environment.
#
platform=$1
cross=
[ "$2" = 1 ] && cross=1 
buildroot=$3
prefix=$4
builddir=$5
version=$6
[ -z "${builddir}" ] && echo "Don't run this by hand." && exit 1
#
# In lieu of creating a proper "SOURCES" tarball, use "tar"
# as a symlink-resolving "cp" with complete control over the
# working directories at each end of the copy.
#
# The target directory for extraction needs to be where
# "%setup -c -q" would put things, which is derived from
# the name of the file in "SOURCES" (if we had created it).
#
mkdir -p $builddir/opencpi-doc-$version
tar -chf - -C exports/ doc/ | tar xf - -C $builddir/opencpi-doc-$version
#
# We have effectively implemented/bypassed "%prep" and "%build",
# just as "prepare-rpm-files.sh" does.  Now "%install" continues.
#
