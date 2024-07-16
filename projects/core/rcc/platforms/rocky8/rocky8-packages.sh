#!/bin/sh
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
# Install or list required and available packages for Rocky 8.X
#
# The packages are really in five categories (and in 4 variables PKGS_{R,D,S,E})
# R. Simply required packages that can be yum-installed and rpm-required for runtime
#    -- note the driver package has separate requirements for driver rebuilding etc.
# D. Simply required packages that can be yum-installed and rpm-required for devel
# S. Convenience packages that will be yum-installed, but not rpm-required
#    -- Generally useful in a source installation, like rpmbuild, etc.
# E. Packages from other repos that are enabled as category #2 (e.g. use epel)
#    -- assumed needed for devel
#    -- thus they are installed after category #2 is installed

# 32 bit cross-architecture packages that, when rpm-required,
#    -- can only be rpm-required by mentioning some individual file in the package
#    -- we encode them as <package-name-for-yum>=<some-file-in-package-for-rpm>

##########################################################################################
# R. yum-installed and rpm-required for runtime - minimal
#    linux basics for general runtime scripts
PKGS_R+=(util-linux coreutils ed findutils initscripts)
#    for JTAG loading of FPGA bitstreams
#    AV-3053 libusb.so is required to communicate with Xilinx programming dongle
#    For some reason, that is only in the libusb-devel package in CentOS X.
#    N.B.: libusb and libusbx can coexist just fine.
#    libusb-devel is in the PowerTools repo (not enabled by default)
PKGS_R+=(libusb-devel)
#    for bitstream manipulation at least
PKGS_R+=(unzip)

##########################################################################################
# D. yum-installed and rpm-required for devel (when users are doing their development).
#    for ACI and worker builds (and to support our project workers using autotools :-( )
PKGS_D+=(cmake make autoconf automake libtool gcc-c++)
#    for our development scripts
PKGS_D+=(which)
#    for development and solving the "/lib/cpp failed the sanity check" a long shot
#    glibc-static is in the PowerTools repo (not enabled by default)
PKGS_D+=(glibc-static glibc-devel binutils)
#    for various building scripts for timing commands
PKGS_D+=(time)
#    enable the epel repo, which contains some packages required for devel
PKGS_D+=(epel-release)
#    for various 32-bit software tools we end up supporting (e.g. modelsim) in devel (AV-567)
#    -- for rpm-required, we need a file-in-this-package too
PKGS_D+=(glibc.i686=/lib/ld-linux.so.2
         redhat-lsb-core.i686=/lib/ld-lsb.so.3
         ncurses-libs.i686=/usr/lib/libncurses.so.5
         libXft.i686=/usr/lib/libXft.so.2
         libXext.i686=/usr/lib/libXext.so.6)
#    for Quartus Pro 17 (AV-4318), we need specifically the 1.2 version of libpng
#    Revisit this if/when we upgrade the Intel tools: current version is 1.6, and
#    Rocky 8.X provides both 1.2 and 1.5 for old binaries.
PKGS_D+=(libpng12)
#    to cleanup multiple copies of Linux kernel, etc. (AV-4802)
PKGS_D+=(hardlink)
# docker container missing this	libXdmcp.i686=/lib/libXdmcp.so.6) # AV-3645
#    for bash completion - a noarch package  (AV-2398)
PKGS_D+=(bash-completion=/etc/profile.d/bash_completion.sh)
#    Needed to build gdb
PKGS_D+=(bison flex)
#    for asciidoc3 man page generation (asciidoc3 is a prereq)
PKGS_D+=(docbook-style-xsl libxslt)
#    for sphinxcontrib.spelling extension (RST doc support)
PKGS_D+=(enchant2)
#    for xilinx tool installation script
PKGS_D+=(expect)
#    for ocpilint
PKGS_D+=(emacs cppcheck clang)


##########################################################################################
# S. yum-installed and but not rpm-required - conveniences or required for source environment
# While some manual installations require git manually installed before this,
# in other scenarios (bare docker containers), the git clone happens outside the container
# and thus we need to explicitly ask for git inside the container
PKGS_S+=(git)
#    for prerequisite downloading and building:
PKGS_S+=(patch)
#    for building kernel drivers (separate from driver RPM)
PKGS_S+=(kernel-devel elfutils-libelf-devel)
#    for "make rpm":
PKGS_S+=(rpm-build)
#    for general configuration/installation flexibility - note nfs-utils-lib exists on early centos7.1
PKGS_S+=(nfs-utils)
#    for the inode64 prerequisite build (from source)
PKGS_S+=(glibc-devel.i686)
#    for the OpenCPI GUI installation and tutorials
PKGS_S+=(tree)

##########################################################################################
# E. installations that have to happen after we run yum-install once, and also rpm-required
#    for devel.  For RPM installations we somehow rely on the user pre-installing epel.
# NOTE: "rocky8" supports python36, python38, and python39, but only the first and second
# are *fully* supported from an OpenCPI perspective (required add-on packages).  Specifying
# "python3" gets you version 3.6.8, and we want at least python 3.8.X for OpenCPI v3.0.0+.
# Use ${python3_ver} to get the needed packages.
python3_ver=python38
#    for serial console terminal emulation
PKGS_E+=(screen)
#    for the OpenCPI GUI installation and tutorials (still needed?)
PKGS_E+=(oxygen-icon-theme)
#    for creating swig
PKGS_E+=(swig)
#    for ocpidev
PKGS_E+=(${python3_ver} ${python3_ver}-devel ${python3_ver}-jinja2)
#    for various testing scripts
PKGS_E+=(${python3_ver}-numpy ${python3_ver}-scipy ${python3_ver}-tkinter python3-matplotlib)
#    for building init root file systems for embedded systems (enabled in devel?)
PKGS_E+=(fakeroot)
#    for OpenCL support (the switch for different actual drivers that are not installed here)
PKGS_E+=(ocl-icd)
#    Needed to build gpsd
PKGS_E+=(python3-scons)
#    Needed to build certain linux kernels or u-boot.
PKGS_E+=(dtc openssl-devel)
#    Need to build plutosdr osp 
PKGS_E+=(perl-ExtUtils-MakeMaker)
#    Needed to generate gitlab-ci yaml
PKGS_E+=(python38-PyYAML)

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

# Different package listing options:
#     list: RPMs with names replaced by <file> where <pkg>=<file> was specified
#     yumlist: RPMs with names replaced by <pkg> where <pkg>=<file> was specified
[ "$1" = list ] && rpkgs PKGS_R && rpkgs PKGS_D && rpkgs PKGS_S && rpkgs PKGS_E && exit 0
[ "$1" = yumlist ] && ypkgs PKGS_R && ypkgs PKGS_D && ypkgs PKGS_S && ypkgs PKGS_E && exit 0

# Docker doesn't have sudo installed by default and we run as root inside
# a container anyway.  If we are NOT running as root AND the local python3
# version is NOT 3.8.X, ask permission before installing 3.8.X and making
# that the system default python3.
SUDO=
if [ "$(whoami)" != root ]; then
  # Check python3 version: looking for 3.8.X.
  echo "Checking python3 version..."
  if python3 -c "\
import sys; \
sys.exit(0 if sys.hexversion < 0x030800f0 or sys.hexversion >= 0x030900f0 else 1)\
"; then
    read -p "OK to install Python 3.8.X as system default python3 (Y/n)? " P_AUTH
    [ "$P_AUTH" = "n" ] && exit 1 || true
  else
    echo "python3 is version 3.8.X"
  fi
  SUDO=$(command -v sudo)
  [ $? -ne 0 ] && bad "\
Could not find 'sudo' and you are not root. Installing packages requires root
permissions."
fi

# Ensure the PowerTools repo is enabled (disabled by default).
# rockylinux:8 container does not have the config-manager plugin,
# so must install that first.
$SUDO dnf -y install 'dnf-command(config-manager)'
$SUDO dnf config-manager --set-enabled powertools

# Install required packages, packages needed for development, and packages
# needed for building from source.  The "--allowerasing" is needed for
# container environments where "coreutils-single" is installed and we
# want "coreutils".
$SUDO dnf --allowerasing -y install $(ypkgs PKGS_R) $(ypkgs PKGS_D) $(ypkgs PKGS_S)
[ $? -ne 0 ] && bad "Installing required packages failed"

# Now those that depend on epel
$SUDO dnf -y install $(ypkgs PKGS_E)
[ $? -ne 0 ] && bad "Installing EPEL packages failed"

# A distasteful thing to do, but needed in case python 3.6.8
# was installed before this script was executed, i.e., python3
# must point to python3.8.
$SUDO alternatives --set python3 /usr/bin/python3.8

exit 0
