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

##########################################################################################
# Install or list required and available packages for Ubuntu 18_4
#
# The packages are really in four categories (and in 4 variables PKG{1,2,3,4}
# R. Simply required packages that can be apt-installed and deb-required for runtime
#    -- note the driver package has separate requirements for driver rebuilding etc.
# D. Simply required packages that can be apt-installed and deb-required for devel
# S. Convenience packages that will be apt-installed, but not deb-required
#    -- Generally useful in a source installation, like rpmbuild, etc.
# E. Packages from other repos that are enabled as category #2 (e.g. use epel)
#    -- assumed needed for devel
#    -- thus they are installed after category #2 is installed

# 32 bit cross-architecture packages that, when deb-required,
#    -- can only be deb-required by mentioning some individual file in the package
#    -- we encode them as <package-name-for-apt>=<some-file-in-package-for-deb>

##########################################################################################
# R. apt-installed and deb-required for runtime - minimal
#    linux basics for general runtime scripts
PKGS_R+=(util-linux coreutils ed findutils)
#TODO find replacement for initscripts
#    for JTAG loading of FPGA bitstreams
#    AV-3053 libusb.so is required to communicate with Xilinx programming dongle
#    For some reason, that is only in the libusb-devel package in both C6 and C7
PKGS_R+=(libusb-dev)
#    for bitstream manipulation at least
PKGS_R+=(unzip)
#    for python and swig testing
PKGS_R+=(python)

##########################################################################################
# D. apt-installed and deb-required for devel (when users are doing their development).
#    for ACI and worker builds (and to support our project workers using autotools :-( )
PKGS_D+=(make autoconf automake libtool build-essential g++)
#    for our development scripts
PKGS_D+=(curl wget)
#    for development and solving the "/lib/cpp failed the sanity check" a long shot
PKGS_D+=(libc6-dev binutils)
#    for various building scripts for timing commands
PKGS_D+=(time)
#    for various project testing scripts - to allow users to use python2 - (we migrate to 3)
#    -- (AV-1261, AV-1299): still python 2 or just for users?
#    -- note that we also need python3 but that is from epel - below in $#4
PKGS_D+=(python-matplotlib python-scipy python-numpy)
#    enable other packages in the epel repo, some required for devel (e.g. python34) TODO remove me
#    PKGS_D+=(epel-release)
#    for various 32-bit software tools we end up supporting (e.g. modelsim) in devel (AV-567)
#    -- for rpm-required, we need a file-in-this-package too
#PKGS_D+=(glibc.i686=/lib/ld-linux.so.2   TODO
#         redhat-lsb-core.i686=/lib/ld-lsb.so.3
#         ncurses-libs.i686=/usr/lib/libncurses.so.5
#         libXft.i686=/usr/lib/libXft.so.2
#         libXext.i686=/usr/lib/libXext.so.6)
#    for Quartus Pro 17 (AV-4318), we need specifically the 1.2 version of libpng TODO
#PKGS_D+=(libpng12)
#    to cleanup multiple copies of Linux kernel, etc. (AV-4802)
PKGS_D+=(hardlink)
# docker container missing this	libXdmcp.i686=/lib/libXdmcp.so.6) # AV-3645
#    for bash completion - a noarch package  (AV-2398)
PKGS_D+=(bash-completion=/etc/profile.d/bash_completion.sh)
#    Needed to build gdb
PKGS_D+=(bison)
#    Needed to build gdb
PKGS_D+=(flex)

##########################################################################################
# S. apt-installed and but not deb-required - conveniences or required for source environment
# While some manual installations require git manually installed before this,
# in other scenarios (bare docker containers), the git clone happens outside the container
# and thus we need to explicitly ask for git inside the container
PKGS_S+=(git)
#    for prerequisite downloading and building:
PKGS_S+=(patch)
#    for building kernel drivers (separate from driver RPM)
PKGS_S+=(linux-headers-$(uname -r))
#    for "make rpm":
#PKGS_S+=(rpm-build)
#    for creating swig
PKGS_S+=(swig python-dev)
#    for general configuration/installation flexibility - note nfs-utils-lib exists on early centos7.1
PKGS_S+=(nfs-kernel-server)
#    for the inode64 prerequisite build (from source) TODO
#PKGS_S+=(glibc-devel.i686)
#    for the AV GUI installation and tutorials
PKGS_S+=(default-jre tree) 
#TODO missing oxygen-icon-theme
#    for serial console terminal emulation
PKGS_S+=(screen)

python3_ver=python3
#    for ocpidev
PKGS_S+=(${python3_ver} ${python3_ver}-jinja2)
#    for various testing scripts
#    AV-5478: If the minor version changes here, fix script below
PKGS_S+=(${python3_ver}-numpy ${python3_ver}-pip)
#    for building init root file systems for embedded systems (enabled in devel?)
PKGS_S+=(fakeroot)
#    for OpenCL support (the switch for different actual drivers that are not installed here)
PKGS_S+=(ocl-icd-dev)
#    Needed to build gpsd
PKGS_S+=(scons libsystemd-dev)
#    Needed to build certain linux kernels or u-boot, at least Xilinx 2015.4
PKGS_S+=(device-tree-compiler)

# functions to deal with arrays with <pkg>=<file> syntax
function rpkgs {
  eval echo \${$1[@]/#*=}
}

function ypkgs {
  eval echo \${$1[@]/%=*}
}

function bad {
  echo Error: $* >&2
  exit 1
}

# The list for RPMs: first line
[ "$1" = list ] && rpkgs PKGS_R && rpkgs PKGS_D && rpkgs PKGS_S && exit 0
[ "$1" = aptlist ] && ypkgs PKGS_R && ypkgs PKGS_D && ypkgs PKGS_S && exit 0

# Docker doesn't have sudo installed by default and we run as root inside
# a container anyway
SUDO=
if [ "$(whoami)" != root ]; then
  SUDO=$(command -v sudo)
  [ $? -ne 0 ] && bad "\
Could not find 'sudo' and you are not root. Installing packages requires root
permissions."
fi

# Install required packages, packages needed for development, and packages
# needed for building from source
$SUDO apt -y install $(ypkgs PKGS_R) $(ypkgs PKGS_D) $(ypkgs PKGS_S) 
#TODO what does this option do --setopt=skip_missing_names_on_install=False
[ $? -ne 0 ] && bad "Installing required packages failed"

exit 0
