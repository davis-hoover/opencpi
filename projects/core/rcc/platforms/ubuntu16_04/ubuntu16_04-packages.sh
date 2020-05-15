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

#
# This is a work in progress, and will doubtless change as deficiencies are
# identified.  For now, preserve all the CentOS 7 semantics we can.  The notion
# of package categories being "runtime", "development", "source_env", and "extra"
# is potentially useful on non-CentOS systems.  *ubuntu distros customarily have
# at least one "extras" repo (partner) that is not enabled by default.  Note that
# "bash" is required: "/bin/sh" points to "dash" on *ubuntu 16.04 LTS systems.
#
##########################################################################################
# Install or list required and available packages for *ubuntu 16.04 LTS
#
# The packages are really in four categories (and in 4 variables PKGS_{R,D,S,E})
# R. Simply required packages for runtime
#    -- note the driver package has separate requirements for driver rebuilding etc.
# D. Simply required packages for devel
# S. Convenience packages, normally not required by either of the above categories
#    -- Generally useful in a source installation, like rpmbuild, etc.
# E. Packages from other repos that are enabled as category 'D' (e.g. use epel)
#    -- assumed needed for devel
#    -- thus they are installed after category 'D' is installed

# Add 32-bit cross-architecture packages as required: *ubuntu has multi-arch support

##########################################################################################
# R. runtime - minimal
#    linux basics for general runtime scripts
PKGS_R+=(util-linux coreutils ed findutils initscripts curl)
#    for JTAG loading of FPGA bitstreams
#    AV-3053 libusb.so is required to communicate with Xilinx programming dongle
#    For some reason, that is only in the libusb development package
PKGS_R+=(libusb-dev)
#    for bitstream manipulation at least
PKGS_R+=(unzip)

##########################################################################################
# D. devel (when users are doing their development).
#    for ACI and worker builds (and to support our project workers using autotools :-( )
PKGS_D+=(make autoconf automake libtool g++)
#    for our development scripts
#    for CentOS7, "which" is in a separate package: *ubuntu has it in debianutils
PKGS_D+=(debianutils wget)
#    for development and solving the "/lib/cpp failed the sanity check" a long shot
#    *ubuntu library packages include the static versions
PKGS_D+=(libc6-dev binutils)
#    for various building scripts for timing commands
PKGS_D+=(time)
#    for various 32-bit software tools we end up supporting (e.g. modelsim) in devel (AV-567)
#    -- for rpm-required, we need a file-in-this-package too
#    -- leaving the next several lines as a reminder of why we need the packages
#PKGS_D+=(glibc.i686=/lib/ld-linux.so.2
#         redhat-lsb-core.i686=/lib/ld-lsb.so.3
#         ncurses-libs.i686=/usr/lib/libncurses.so.5
#         libXft.i686=/usr/lib/libXft.so.2
#         libXext.i686=/usr/lib/libXext.so.6)
#    for *ubuntu 16_04 LTS, installing "lsb" covers most of what we need
PKGS_D+=(lsb lib32ncurses5 libxft2:i386 libxext6:i386)
#    for Quartus Pro 17 (AV-4318), we need specifically the 1.2 version of libpng
PKGS_D+=(libpng12-0)
#    to cleanup multiple copies of Linux kernel, etc. (AV-4802)
PKGS_D+=(hardlink)
# docker container missing this	libXdmcp.i686=/lib/libXdmcp.so.6) # AV-3645
#    for bash completion - a noarch package  (AV-2398)
PKGS_D+=(bash-completion)
#    Needed to build gdb
PKGS_D+=(bison)
#    Needed to build gdb
PKGS_D+=(flex)

##########################################################################################
# S. conveniences or required for source environment
# While some manual installations require git manually installed before this,
# in other scenarios (bare docker containers), the git clone happens outside the container
# and thus we need to explicitly ask for git inside the container
PKGS_S+=(git)
#    for prerequisite downloading and building:
PKGS_S+=(patch)
#    for building kernel drivers (separate from pre-packaged driver)
#    N.B.: "linux-headers-`uname -r`" is probably the only required
#    package, and normally gets installed with kernel upgrades, i.e.,
#    it should already be present.
#KVER=`uname -r | cut -f1 -d'-'`
#PKGS_S+=(linux-source-$KVER)
#    for "make rpm":
#      does not necessarily make sense for debian-based
#      distros, but will include for completeness
PKGS_S+=(rpm)
#    for general configuration/installation flexibility
PKGS_S+=(nfs-common nfs-kernel-server)
#    for the inode64 prerequisite build (from source)
PKGS_S+=(libc6-dev-i386)
#    for the AV GUI installation and tutorials
PKGS_S+=(oxygen5-icon-theme default-jre tree)
#    for serial console terminal emulation
PKGS_S+=(screen)

##########################################################################################
# E. installations that have to happen after we run "apt-get install" once, and also
#    install the required "devel" packages.  At this point, we rely on any extra
#    repos that are needed being enabled.  With respect to Python 3, it would seem
#    the minimum required version is 3.4.  For *ubuntu 16.04 LTS, "python3" maps to
#    "python3.5" by default as of March 2020.
#
#    for creating swig
#    -- see note about installing/enabling TimSC PPA below
PKGS_E+=(swig)
#    for ocpidev
PKGS_E+=(python3 python3-dev python3-jinja2)
#    for various testing scripts
PKGS_E+=(python3-numpy python3-scipy python3-matplotlib)
#    for OpenCL support (the switch for different actual drivers that are not installed here)
PKGS_E+=(ocl-icd-libopencl1)
#    Needed to build gpsd
PKGS_E+=(scons)

#
# Comments around/within the next two functions are for my own
# edification.  The original Bourne shell had no support for
# arrays other than positional parameters (assigned with "set")
# and having the restrictions of (a) not being able to directly
# access any parameters beyond the 9th; and (b) having to use
# "shift" to get to the parameters beyond the 9th.  Likewise,
# there were no convenient built-in methods of performing string
# operations (matching, substring extraction, substitution, etc.).
# For our purposes, ASSuming "/bin/sh" is "bash" or compatible
# with "bash" is probably safe: one source claims we left the
# dark ages behind when Solaris 11 was released, at which time
# "/bin/sh" became POSIX sh.
#
# functions to deal with arrays with <pkg>=<file> syntax
function rpkgs {
  # This function prints the portion of each array
  # element to the right of the '=', i.e., <file>.
  # "#*=" means "remove prefix ending in '='"
  eval echo \${$1[@]/#*=}
}

function ypkgs {
  # This function prints the portion of each array
  # element to the left of the '=', i.e., <pkg>.
  # "%=*" means "remove suffix starting with '='"
  eval echo \${$1[@]/%=*}
}

function bad {
  echo Error: $* >&2
  exit 1
}

# For now, leave "list" and "yumlist" alone, even though
# the latter makes no sense in a Debian environment.

# The list for packages: first line
[ "$1" = list ] && rpkgs PKGS_R && rpkgs PKGS_D && rpkgs PKGS_S && rpkgs PKGS_E && exit 0
[ "$1" = yumlist ] && ypkgs PKGS_R && ypkgs PKGS_D && ypkgs PKGS_S && ypkgs PKGS_E && exit 0

# Docker doesn't have sudo installed by default and we run as root inside
# a container anyway
SUDO=
if [ "$(whoami)" != root ]; then
  SUDO=$(command -v sudo)
  [ $? -ne 0 ] && bad "\
Could not find 'sudo' and you are not root. Installing packages requires root
permissions."
fi

# Enable TimSC Personal Package Archive (PPA): needed for "swig"
if [ ! -f /etc/apt/sources.list.d/timsc-ubuntu-swig-3_0_12-xenial.list ]
then
  $SUDO add-apt-repository --yes ppa:timsc/swig-3.0.12
  $SUDO apt-get update
fi

# Install required packages, packages needed for development, and packages
# needed for building from source.  Specify "--no-act" for debugging.
$SUDO apt-get --yes install $(ypkgs PKGS_R) $(ypkgs PKGS_D) $(ypkgs PKGS_S)
[ $? -ne 0 ] && bad "Installing required packages failed"

# Now install those packages that depend on "extras" repos.
# Again, specify "--no-act" for debugging.
$SUDO apt-get --yes install $(ypkgs PKGS_E)
[ $? -ne 0 ] && bad "Installing extra packages failed"

exit 0
