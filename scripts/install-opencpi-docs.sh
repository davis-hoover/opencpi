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

################################################################################

set -e

function usage {
  echo "\
This script installs packages required to build OpenCPI documentation and then
builds the documents in the framework and builtin projects, both tex and odt.
It does not depend on the framework or projects being built, although it usually
runs after install-opencpi.sh

This script is only supported on centos7.

Usage: $(basename $0) [--no-build]

  --no-build  Only install packages
"
  exit 1
}

# Parse args
case "$1" in
  --no-build)  no_build=1 ;;
  '') ;;
  *)  usage ;;
esac

# Docker doesn't have sudo installed by default and we run as root inside
# a container anyway
SUDO=
if [ "$(whoami)" != root ]; then
  SUDO=$(command -v sudo)
  [ $? -ne 0 ] && echo "\
Error: Could not find 'sudo' and you are not root. Installing packages requires
root permissions." && exit 1
fi

if ! grep -q 'CentOS Linux release 7' /etc/redhat-release ; then
  echo 'This sript only works on CentOS 7, sorry!'
  exit 1
fi

echo 'Installing all the standard packages required to build OpenCPI'
echo "documentation using '$SUDO yum install'..."
sanity=--setopt=skip_missing_names_on_install=False
$SUDO yum install -y $sanity epel-release
$SUDO yum install -y $sanity ghostscript git libreoffice-writer make \
  python34 python34-jinja2 rubber texlive texlive-appendix texlive-latex \
  texlive-multirow texlive-placeins texlive-titlesec texlive-xstring unoconv \
  https://downloads.sourceforge.net/project/mscorefonts2/rpms/msttcore-fonts-installer-2.6-1.noarch.rpm
echo 'Packages required to build OpenCPI documentation have been installed.'

if [ -n "$no_build" ]; then
  echo 'To build OpenCPI documentation, run `make doc`.'
  exit 0
fi

# Just check if it looks like we are in the source tree.
[ -d runtime -a -d build -a -d scripts -a -d tools ] || {
  echo "Error:  this script ($0) is not being run from the top level of the OpenCPI source tree."
  exit 1
}

# Ensure exports (or cdk) exists and has scripts
source ./scripts/init-opencpi.sh
echo 'Building documentation using `make doc`.'
make doc
