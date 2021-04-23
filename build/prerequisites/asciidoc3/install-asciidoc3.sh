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

# asciidoc3 package installed just for man page production

version=3.2.2

# Download and extract source
# The + below means create a directory for the tarball extraction
source "$OCPI_CDK_DIR/scripts/setup-prerequisite.sh" \
       "$1" \
       "asciidoc3" \
       'AsciiDoc3.org package used for man pages' \
       https://asciidoc3.org \
       asciidoc3-$version.tar.gz \
       +ad3 \
       0

cd ../..

# So uses of this use $OCPI_PREREQUISITES_DIR/asciidoc3/ad3/<whatever>
relative_link ad3 "$OcpiInstallDir" # each platform creates this same link
rmdir "$OcpiInstallExecDir"
