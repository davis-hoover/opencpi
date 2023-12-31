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
# Install or list required and available packages for Centos7
#
# The packages are really in five categories (and in 5 variables PKGS_{R,D,S,E,P})
# R. Simply required packages that can be yum-installed and rpm-required for runtime
#    -- note the driver package has separate requirements for driver rebuilding etc.
# D. Simply required packages that can be yum-installed and rpm-required for devel
# S. Convenience packages that will be yum-installed, but not rpm-required
#    -- Generally useful in a source installation, like rpmbuild, etc.
# E. Packages from other repos that are enabled as category #2 (e.g. use epel)
#    -- assumed needed for devel
#    -- thus they are installed after category #2 is installed
# P. Python3 packages that must be installed with pip3 because they
#    are not available as RPMs.

# 32 bit cross-architecture packages that, when rpm-required,
#    -- can only be rpm-required by mentioning some individual file in the package
#    -- we encode them as <package-name-for-yum>=<some-file-in-package-for-rpm>

##########################################################################################
# R. yum-installed and rpm-required for runtime - minimal
#    linux basics for general runtime scripts
PKGS_R+=(util-linux coreutils ed findutils initscripts)
#    for JTAG loading of FPGA bitstreams
#    AV-3053 libusb.so is required to communicate with Xilinx programming dongle
#    For some reason, that is only in the libusb-devel package in both C6 and C7
PKGS_R+=(libusb-devel)
#    for bitstream manipulation at least
PKGS_R+=(unzip)

##########################################################################################
# D. yum-installed and rpm-required for devel (when users are doing their development).
#    for ACI and worker builds (and to support our project workers using autotools :-( )
PKGS_D+=(make autoconf automake libtool gcc-c++)
#    for our development scripts
PKGS_D+=(which)
#    for development and solving the "/lib/cpp failed the sanity check" a long shot
PKGS_D+=(glibc-static glibc-devel binutils)
#    for various building scripts for timing commands
PKGS_D+=(time)
#    enable the epel repo, which contains some packages required for devel (e.g. python36)
PKGS_D+=(epel-release)
#    for various 32-bit software tools we end up supporting (e.g. modelsim) in devel (AV-567)
#    -- for rpm-required, we need a file-in-this-package too
PKGS_D+=(glibc.i686=/lib/ld-linux.so.2
         redhat-lsb-core.i686=/lib/ld-lsb.so.3
         ncurses-libs.i686=/usr/lib/libncurses.so.5
         libXft.i686=/usr/lib/libXft.so.2
         libXext.i686=/usr/lib/libXext.so.6)
#    for Quartus Pro 17 (AV-4318), we need specifically the 1.2 version of libpng
PKGS_D+=(libpng12)
#    to cleanup multiple copies of Linux kernel, etc. (AV-4802)
PKGS_D+=(hardlink)
# docker container missing this	libXdmcp.i686=/lib/libXdmcp.so.6) # AV-3645
#    for bash completion - a noarch package  (AV-2398)
PKGS_D+=(bash-completion=/etc/profile.d/bash_completion.sh)
#    Needed to build gdb
PKGS_D+=(bison)
#    Needed to build gdb
PKGS_D+=(flex)
#    Needed by Xilinx ISE 14.7
PKGS_D+=(libSM libXi libXrandr)
#    for the new "xilinx19_2_aarch*" platforms
PKGS_D+=(openssl-devel)
#    for asciidoc3 man page generation (asciidoc3 is a prereq)
PKGS_D+=(docbook-style-xsl)
#    for sphinxcontrib.spelling extension (RST doc support)
PKGS_D+=(enchant)

##########################################################################################
# S. yum-installed and but not rpm-required - conveniences or required for source environment
# While some manual installations require git manually installed before this,
# in other scenarios (bare docker containers), the git clone happens outside the container
# and thus we need to explicitly ask for git inside the container
PKGS_S+=(git)
#    for prerequisite downloading and building:
PKGS_S+=(patch)
#    for building kernel drivers (separate from driver RPM)
PKGS_S+=(kernel-devel)
#    for "make rpm":
PKGS_S+=(rpm-build)
#    for general configuration/installation flexibility - note nfs-utils-lib exists on early centos7.1
PKGS_S+=(nfs-utils)
#    for the inode64 prerequisite build (from source)
PKGS_S+=(glibc-devel.i686)
#    for the AV GUI installation and tutorials
PKGS_S+=(oxygen-icon-theme jre tree)
#    for serial console terminal emulation
PKGS_S+=(screen)

##########################################################################################
# E. installations that have to happen after we run yum-install once, and also rpm-required
#    for devel.  For RPM installations we somehow rely on the user pre-installing epel.
# NOTE: only use ${python3_ver} package name prefix for add-on packages not provided in
# CentOS 7 repo.  Known packages in this category are "python3-jinja2", "python3-numpy",
# "python3-scipy", and "python3-scons".
python3_ver=python36
#    for ocpidev
PKGS_E+=(python3 python3-devel ${python3_ver}-jinja2)
#    for various testing scripts
PKGS_E+=(${python3_ver}-numpy ${python3_ver}-scipy python3-tkinter python3-pip)
#    for building yaml-cpp
PKGS_E+=(cmake3)
#    for building init root file systems for embedded systems (enabled in devel?)
PKGS_E+=(fakeroot)
#    for OpenCL support (the switch for different actual drivers that are not installed here)
PKGS_E+=(ocl-icd)
#    Needed to build gpsd
PKGS_E+=(${python3_ver}-scons)
#    Needed to build certain linux kernels or u-boot, at least Xilinx 2015.4
PKGS_E+=(dtc openssl-devel)
#    Needed to build plutosdr osp 
PKGS_E+=(perl-ExtUtils-MakeMaker)
#    Needed to build ettus_n310 osp
PKGS_E+=(chrpath diffstat texinfo)
#    Needed to generate gitlab-ci yaml
PKGS_E+=(python36-PyYAML)
#    Needed to build pillow >= 8.4.0 dependency for matplotlib
PKGS_E+=(libjpeg-turbo-devel)

##########################################################################################
# P. python3 packages that must be installed using pip3, which we have available
#    after installing python3-pip (see PKGS_E).  "pip3" will select the latest
#    version of a given package unless otherwise specified: this is important
#    because many current python3 packages require python3 >= 3.5.  This will
#    not be an issue for CentOS 7 as long as we have python36 installed.  For
#    now, assume the justification for a package in this category is the same
#    as for its python2 counterpart as given above.
PKGS_P+=(matplotlib)
#    These next packages will be installed in a python36
#    virtual environment for "ocpidoc" vs. "system-wide".
#PKGS_P+=(sphinx sphinx_rtd_theme sphinxcontrib_spelling)

#
# Because long option strings impair readability.
# Verified it is safe to invoke "yum" this way
# regardless of the command (list, install, erase).
#  
YUM="yum --assumeyes --setopt=skip_missing_names_on_install=False"

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

function install_swig3 {
  #
  # Need SWIG 3.0.12 for this platform, and the "swig3" package
  # conflicts with the "swig" package that is probably already
  # installed.  Figure out whether we have the correct version,
  # and go from there.
  #
  local need_swig3=1

  [ -d /usr/share/swig/3.0.12 ] && need_swig3=0

  if [ $need_swig3 -eq 1 ]
  then
    $SUDO $YUM list swig3 > /dev/null 2>&1 || bad "swig3 package unavailable"
    $SUDO $YUM erase swig
    $SUDO $YUM install swig3
  fi
}

# Different package listing options:
#     list: RPMs with names replaced by <file> where <pkg>=<file> was specified
#     yumlist: RPMs with names replaced by <pkg> where <pkg>=<file> was specified
#     piplist: packages handled by pip3
[ "$1" = list ] && rpkgs PKGS_R && rpkgs PKGS_D && rpkgs PKGS_S && rpkgs PKGS_E && exit 0
[ "$1" = yumlist ] && ypkgs PKGS_R && ypkgs PKGS_D && ypkgs PKGS_S && ypkgs PKGS_E && exit 0
[ "$1" = piplist ] && echo ${PKGS_P[*]} && exit 0

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
$SUDO $YUM install $(ypkgs PKGS_R) $(ypkgs PKGS_D) $(ypkgs PKGS_S)
[ $? -ne 0 ] && bad "Installing required packages failed"

# Now those that depend on epel
$SUDO $YUM install $(ypkgs PKGS_E)
[ $? -ne 0 ] && bad "Installing EPEL packages failed"

# SWIG is a special case on CentOS 7
install_swig3

# And finally, install the remaining python3 packages
$SUDO pip3 install ${PKGS_P[*]}
[ $? -ne 0 ] && bad "Installing pip3 packages failed"

exit 0
