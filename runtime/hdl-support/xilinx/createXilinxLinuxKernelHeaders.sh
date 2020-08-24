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

# See the "usage" message below
# "make" will run in parallel unless you set MAKE_PARALLEL to blank or null string (but defined)
# We set the default to 4 since using "-j" by itself blows up (infinite forks) on some systems.
export MAKE_PARALLEL=${MAKE_PARALLEL--j4}
set -e

if test "$1" = "" -o "$1" = "--help" -o "$1" = "-help" -o "$2" = ""; then
  cat <<EOF
The purpose of this script is to create and capture artifacts based on configuring and building
the linux kernel and u-boot from the Xilinx git repository.
It results in a "kernel headers" package necessary to build the OpenCPI linux kernel driver and 
a few other files necessary for later processing (e.g. tools for manipulating image files).

It assumes:
- a git repo for Xilinx linux kernel and u-boot has been established (cloned) in the git/ subdirectory
  of where the Xilinx tools are installed, e.g. /tools/Xilinx/git
- a Xilinx EDK (ISE) or SDK (Vivado) installation for OpenCPI exists in the environment
- the OCPI_CDK_DIR environment variable points to an OpenCPI installation
  (i.e. opencpi-setup.sh has been sourced)

It does these things:
- Checks out the previously downloaded git source repo with the tag for a release
- Builds u-boot and the linux kernel (and various device tree binaries).
- Creates a sparse "kernel-headers" subset of the built linux source tree.
- Captures several other tools and files from the build process

The result of this script is a directory with artifacts that are needed to:
- Build the OpenCPI linux kernel driver (thus completing the framework build for zynq)
- Create a bootable SD card (necessary files, not sufficient)

Usage is: createLinuxKernelHeaders.sh <arch> <linux-tag> <uboot-tag> <repo-dir> <out-dir> <config> <local>

The release name can be the same as the tag, but it is usually the associated
Xilinx tool release associated with the tag unless it is between releases etc.
E.g. if the Xilinx release is 2013.4, the repo tag is xilinx-v2013.4, and the
OpenCPI Zynq RCC platform name is 13_4.
Note the repo tag used should be what is documented at the xilinx wiki for the binary release.
Thus while this script does not use the binary release, it *does* use the repo tag associated with the
binary release (as stated on the wiki page)
It adds a few configuration options for the kernel beyond the Xilinx minimal default unless
it is supplied with a kernel config file directly.

When this script is complete, it leaves the repo in a built state checked out with the
given tags.
EOF
  exit 1
fi
arch=$1
shift
linux_tag=$1
uboot_tag=$2
case $3 in (/*) gdir=$3 ;; (*) gdir=`pwd`/$3;; esac
case $4 in (/*) RELDIR=$4;; (*) RELDIR=`pwd`/$4;; esac
config=$5
localversion=-$6
if test ! -d $gdir/linux-xlnx; then
  echo The source directory $3/linux-xlnx does not exist. Run getXilinxLinuxSources.sh\?
  exit 1
fi
case $arch in
    (arm)
      karch=arm
      uarch=arm
      kconfig=xilinx_zynq_defconfig
      uconfig="zynq_zed_config zynq_zed_defconfig"
      kargs="UIMAGE_LOADADDR=0x8000 uImage"

      ;;
    (aarch32)
      karch=arm
      uarch=arm
      kconfig=xilinx_zynq_defconfig
      uconfig=zynq_zed_defconfig
      kargs="UIMAGE_LOADADDR=0x8000 uImage"
      ;;
    (aarch64)
      karch=arm64
      uarch=arm
      kconfig=xilinx_zynqmp_defconfig
      uconfig="xilinx_zynqmp_ep_defconfig xilinx_zynqmp_mini_defconfig" # set of possibilities
      kargs=Image.gz
      ;;
    (*)
      echo Unknown/unsupported architecture: $arch
      exit 1
      ;;
esac
source $OCPI_CDK_DIR/scripts/ocpitarget.sh $(basename `pwd`)
CROSS_COMPILE=$OCPI_TARGET_CROSS_COMPILE
echo Cross compiler prefix being used is: $CROSS_COMPILE
# Start fresh
rm -r -f $RELDIR
mkdir -p $RELDIR
cd $gdir/u-boot-xlnx
git reset --hard origin/master
git clean -ffdx
echo ==============================================================================
echo Using the tag '"'$uboot_tag'"' for the Xilinx u-boot source repository.
make clean CROSS_COMPILE=$CROSS_COMPILE
make distclean CROSS_COMPILE=$CROSS_COMPILE
echo Checking out the Xilinx u-boot using the repository label '"'$uboot_tag'"'.
if ! git checkout -f tags/$uboot_tag; then
  echo Checkout in u-boot repo for tag $uboot_tag failed.  If the tag is recent, perhaps you need to git pull.
  exit 1
fi
# There is no stability in the uboot zynqmp configurations, but we are not typically using the
# actual u-boot that is getting built so its not critical that it always be the same
if [ $arch = aarch64 ]; then
    if [ ! -r configs/$uconfig ]; then
	uconfig=xilinx_xynqmp_ep_defconfig
	if [ ! -r configs/$uconfig ]; then
	    uconfig=xilinx_zynqmp_zcu104_revC_defconfig
	fi
    fi
fi
echo ==============================================================================
echo Building u-boot to get the mkimage and other commands.
found=
# Look where later u-boots want it
for c in $uconfig; do
    ([ -e configs/$c ] ||
	 ( [ -e boards.cfg ] && grep -q '[^#]*[ 	][ 	]*'${c%_config}'[ 	]' boards.cfg)) &&
	found=$c
done
[ -z "$found" ] && echo No u-boot configs found among: $uconfig && exit 1
make ARCH=$uarch $found CROSS_COMPILE=$CROSS_COMPILE
make ARCH=$uarch CROSS_COMPILE=$CROSS_COMPILE ${MAKE_PARALLEL}
cp tools/mkimage $RELDIR
if [ -f tools/fit_info ]; then
    cp tools/fit_info $RELDIR
else
    echo Warning: there is no \"fit_info\" program in this version of u-boot.
fi
echo ==============================================================================
echo The u-boot build is complete.  Starting linux build.
echo ==============================================================================
echo Using the tag '"'$linux_tag'"' for the Xilinx linux kernel source repository.
cd ../linux-xlnx
git reset --hard origin/master
git clean -ffdx
echo Checking out the Xilinx Linux kernel using the repository label '"'$linux_tag'"'.
if ! git checkout -f tags/$linux_tag; then
  echo Checkout in linux repo for tag $linux_tag failed.  If the tag is recent, perhaps you need to git pull.
  exit 1
fi
if test $linux_tag = xilinx-v14.7; then
    git checkout xilinx-v2013.4 drivers/usb/phy/phy-zynq-usb.c
    echo Patching zed device tree for ethernet phy issue.
    ed arch/arm/boot/dts/zynq-zed.dts <<EOF
   134
   s/phy@7/phy@0/p
    137
    s/<7>/<0>/p
    305
    s/host/otg/p
    w
EOF
fi
if [ -n "$config" ]; then
  echo ============================================================================================
  echo Copying kernel config from $config
  cp $config .config
  make Q= V=2 ARCH=$karch CROSS_COMPILE=$CROSS_COMPILE oldconfig
else
  echo ============================================================================================
  echo Adding support for USB Ethernet Dongles if not there already
  ed arch/arm/configs/xilinx_zynq_defconfig <<-EOF
	g/CONFIG_USB_USBNET/d
	g/CONFIG_USB_ZYNQ_PHY/d
	g/CONFIG_USB_NET_AX8817X/d
	$
	a
	CONFIG_USB_USBNET=y
	CONFIG_USB_ZYNQ_PHY=y
	CONFIG_USB_NET_AX8817X=y
	.
	w
	EOF
  echo ============================================================================================
  echo Configuring the Xilinx linux kernel using their default configuration for zynq....
  make Q= V=2 ARCH=$karch $kconfig
fi
echo ============================================================================================
echo Building the Xilinx linux kernel for zynq to create the kernel-headers tree.
################################################################################
# We need to make sure the kernel version string matches the deployed kernel.
# How this happens has evolved over various kernel and xilinx versions
# There are two parts:
# 1. There is the part that comes from the linux kernel build's idea of the "state of the scm tree".
# Presumably the Xilinx build in production is a clean tree, so we emulate that by forcing
# the SCM part of the version string to be empty by:
cat /dev/null > .scmversion # cannot use touch in case it was there already
# 2. There is the "local version" part of the release string.
# this is passed in as an argument
# First, suppress any SCM/git-based kernel version strings since we must match the

# deployed kernel.
yes "" | PATH="$PATH:`pwd`/../u-boot-xlnx/tools" \
   make Q= V=2 ARCH=$karch CROSS_COMPILE=$CROSS_COMPILE ${MAKE_PARALLEL} LOCALVERSION=$localversion \
        $kargs dtbs modules # why modules?
ocpi_kernel_release=$(< include/config/kernel.release)-$(echo $linux_tag | sed 's/^xilinx-//')
echo ============================================================================================
cd $RELDIR
echo Capturing the built Linux uImage file and the zynq device trees in directory: $RELDIR
mkdir dts
(shopt -s nullglob; cp $gdir/linux-xlnx/arch/$karch/boot/dts/{,xilinx/}zynq*.dt* dts) # needed?
(shopt -s nullglob; cp $gdir/linux-xlnx/arch/$karch/boot/{u,}Image* .)
echo ============================================================================================
echo Preparing the kernel-headers tree based on the built kernel.
rm -r -f kernel-headers-$tag kernel-headers
mkdir kernel-headers
# copy that avoids errors when caseinsensitive file systems are used (MacOS...)
# otherwise it would be:
#    cp -R ../git/linux-xlnx/{Makefile,Module.symvers,include,scripts,arch} kernel-headers
(cd $gdir/linux-xlnx;
  for f in Makefile Module.symvers include scripts arch/$karch arch/arm .config; do
    find $f -type d -exec mkdir -p $RELDIR/kernel-headers/{} \;
    find $f -type f -exec sh -c \
     "if test -e $RELDIR/kernel-headers/{}; then
        echo File {} has a case sensitive duplicate which will be overwritten.
        rm -f $RELDIR/kernel-headers/{}
      fi
      cp {} $RELDIR/kernel-headers/{}" \;
  done
  for i in $(find -name 'Kconfig*'); do
    mkdir -p $RELDIR/kernel-headers/$(dirname $i)
    cp $i $RELDIR/kernel-headers/$(dirname $i)
  done
)
# Remove all other architectures
find kernel-headers/arch -mindepth 1 -maxdepth 1 -type d ! -path "*/arch/arm*" ! -name x86 -exec rm -r {} \;
rm -r -f kernel-headers/arch/$karch/boot
rm kernel-headers/scripts/{basic,mod}/.gitignore
# Record the kernel release AND the repo tag used, both inside the kernel headers and at the top-level
# of the release (so that you do not need to unpack the kernel headers just to find it)
echo $ocpi_kernel_release > ocpi-release
cp ocpi-release kernel-headers
echo Removing *.cmd
find kernel-headers -name '*.cmd' -o -name '*.o' -delete
echo Removing x86_64 binaries
find kernel-headers/scripts | xargs file | grep "ELF 64-bit" | cut -f1 -d: | xargs -tr -n1 rm
#echo Removing auto.conf
#rm kernel-headers/include/config/auto.conf
echo Restoring source to removed binaries
(cd $gdir/linux-xlnx;
  for f in $(find scripts/ -name '*.c' -o -name 'zconf.tab'); do
    mkdir -p $RELDIR/kernel-headers/$(dirname $f)
    cp $f $RELDIR/kernel-headers/$(dirname $f)
  done
  mkdir -p $RELDIR/kernel-headers/tools/include
  cp -R tools/include/tools $RELDIR/kernel-headers/tools/include
)
echo Removing unused large headers
rm -rf kernel-headers/include/linux/{mfd,platform_data}
echo Creating the compressed archive for kernel headers
tar -c -z -f kernel-headers.tgz kernel-headers
rm -r -f kernel-headers
