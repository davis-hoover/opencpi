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
# Install or list required and available packages for Centos6
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
PKGS_D+=(which wget)
#    for development and solving the "/lib/cpp failed the sanity check" a long shot
PKGS_D+=(glibc-static glibc-devel binutils)
#    for various building scripts for timing commands
PKGS_D+=(time)
#    although no longer needed for testing scripts, the next two
#    packages are required for SCons installation and the "gpsd"
#    build (both require python2)
PKGS_D+=(python python-pip)
#    for building init root file systems for embedded systems (enabled in devel?)
PKGS_D+=(fakeroot)
#    enable other packages in the epel repo, some required for devel (e.g. python34)
PKGS_D+=(epel-release ca-certificates)
#    for various 32-bit software tools we end up supporting (e.g. modelsim) in devel (AV-567)
#    -- for rpm-required, we need a file-in-this-package too
PKGS_D+=(glibc.i686=/lib/ld-linux.so.2
         # This must be here to be sure libgcc.x86_64 stays in sync with libgcc.i686
         libgcc
         libgcc.i686=/lib/libgcc_s.so.1
         redhat-lsb-core.i686=/lib/ld-lsb.so.3
         ncurses-libs.i686=/lib/libncurses.so.5
         libXft.i686=/usr/lib/libXft.so.2
         libXext.i686=/usr/lib/libXext.so.6)
#    for Quartus Pro 17 (AV-4318), we need specifically the 1.2 version of libpng
#    -- this seems to be the default version for CentOS 6
PKGS_D+=(libpng)
#    to cleanup multiple copies of Linux kernel, etc. (AV-4802)
PKGS_D+=(hardlink)
#    Needed to build gdb
PKGS_D+=(bison flex)
#    Needed by Xilinx ISE
PKGS_D+=(libSM libXi libXrandr libXrender)

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
#    for general configuration/installation flexibility
PKGS_S+=(nfs-utils nfs-utils-lib)
#    for the inode64 prerequisite build (from source)
PKGS_S+=(glibc-devel.i686)
#    for the AV GUI installation and tutorials
#PKGS_S+=(oxygen-icon-theme jre tree)
#    for serial console terminal emulation
PKGS_S+=(screen)
#    for python3 matplotlib build/install using "pip3"
PKGS_S+=(freetype-devel libpng-devel)
#    for python3 scipy build/install using "pip3"
PKGS_S+=(blas openblas-serial openblas-threads lapack atlas)
PKGS_S+=(blas-devel lapack-devel atlas-devel)

##########################################################################################
# E. installations that have to happen after we run yum-install once, and also rpm-required
#    for devel.  For RPM installations we somehow rely on the user pre-installing epel.
# NOTE: only use ${python3_ver} package name prefix for add-on packages not provided in
# CentOS 6 repo (which is pretty much everything, unfortunately).
python3_ver=python34
#    for ocpidev
PKGS_E+=(${python3_ver} ${python3_ver}-devel ${python3_ver}-jinja2)
#    for various testing scripts
PKGS_E+=(${python3_ver}-numpy ${python3_ver}-numpy-f2py ${python3_ver}-pip)
#    for OpenCL support (the switch for different actual drivers that are not installed here)
PKGS_E+=(ocl-icd)
#    for bash completion - a noarch package  (AV-2398)
PKGS_E+=(bash-completion=/etc/profile.d/bash_completion.sh)

##########################################################################################
# P. python3 packages that must be installed using pip3, which we have available
#    after installing python3-pip (see PKGS_E).  "pip3" will select the latest
#    version of a given package unless otherwise specified: this is important
#    because many current python3 packages require python3 >= 3.5 and we are
#    stuck with 3.4 on CentOS 6.  These packages are needed for testing scripts.
PKGS_P+=('kiwisolver==1.0.1' 'scipy==1.2.2' 'matplotlib==2.2.5')

# SEE BELOW: "scons" installation is a mess on this platform.  The first
# version of SCons with support for python3 is 3.0.0, and it requires
# python2 >= 2.7 and python3 >= 3.5, so we cannot get there from here
# without upgrading the entire python ecosystem, and that will NOT be
# happening.  The "python2" version of "pip" botches the installation
# of "scons==2.5.1" (required because of bugs in the earlier versions)
# unless invoked with "--egg".

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

function install_scons {
  # 
  # This should not be necessary, and exists only because the
  # current python2 version of "pip" is busticated.  Problems
  # include (1) "pip search x" does not work; and (2) attempts
  # to run "pip install 'scons==2.5.1'" result in an error:
  # "option --single-version-externally-managed not recognized"
  #
  local need_scons=1

  if rpm -q scons &> /dev/null; then
    # RPM is installed: remove and install scons manually
    # as this version does not work with gpsd.
    $SUDO yum -y erase scons
  elif command -v scons &> /dev/null; then
    # SCons is in path: get the version info (maj.min.rev).
    SC_VER=`scons --version | grep script | cut -f2 -d'v'`
    SC_MAJ=`echo $SC_VER | cut -f1 -d'.'`
    SC_MIN=`echo $SC_VER | cut -f2 -d'.'`
    SC_REV=`echo $SC_VER | cut -f3 -d'.' | cut -f1 -d','`
    # The following version check code is minimal,
    # because 2.5.1 is the only version that works.
    [ $SC_MAJ -eq 2 -a $SC_MIN -eq 5 -a $SC_REV -eq 1 ] && need_scons=0
  fi

  # Install "scons" with "pip install --egg".
  if [ $need_scons -eq 1 ]; then
    $SUDO pip install --egg 'scons==2.5.1'
  fi
}

function install_swig3 {
  #
  # Need SWIG 3.0.12 for this platform, and it is only available
  # from an "untrusted" third-party repository.  Attempting to
  # install the yum repository RPM for Springdale Computational
  # fails due to dependencies on packages within that repo, so
  # we will download and install the needed packages manually.
  #
  local need_swig3=1

  [ -f /usr/local/swig/3.0.12/bin/swig ] && need_swig3=0

  if [ $need_swig3 -eq 1 ]
  then
    pushd /tmp
    wget \
http://springdale.princeton.edu/data/springdale/6/x86_64/os/Computational/swig3012-3.0.12-3.sdl6.x86_64.rpm \
http://springdale.princeton.edu/data/springdale/6/x86_64/os/Computational/swig3012-doc-3.0.12-3.sdl6.noarch.rpm
    $SUDO yum -y install ./swig3012-3.0.12-3.sdl6.x86_64.rpm ./swig3012-doc-3.0.12-3.sdl6.noarch.rpm
    rm -f ./swig3012-3.0.12-3.sdl6.x86_64.rpm ./swig3012-doc-3.0.12-3.sdl6.noarch.rpm
    popd
  fi
}

# Different package listing options:
#     list: RPMs with names replaced by <file> where <pkg>=<file> was specified
#     yumlist: RPMs with names replaced by <pkg> where <pkg>=<file> was specified
#     piplist: packages handled by pip3
# The list for RPMs: first line
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
$SUDO yum -y install $(ypkgs PKGS_R) $(ypkgs PKGS_D) $(ypkgs PKGS_S) --setopt=skip_missing_names_on_install=False
[ $? -ne 0 ] && bad "Installing required packages failed"

# Now those that depend on epel
$SUDO yum -y install $(ypkgs PKGS_E) --setopt=skip_missing_names_on_install=False
[ $? -ne 0 ] && bad "Installing EPEL packages failed"

# And finally, install the remaining python3 packages
$SUDO pip3 install ${PKGS_P[*]}

# On CentOS 6.X, SCons has to be installed manually.  The
# CentOS 6 RPM is not new enough, and the python2 version
# of "pip" is broken.  SCons is needed by gpsd.
install_scons

# Similar story for SWIG: need at least version 3.0.12, and it is
# only available from a third-party repo (Springdale Computational).
install_swig3

exit 0
