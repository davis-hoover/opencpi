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

# This makefile fragment is meant to be included in a RCC/SW platform's Makefile using

# include $(OCPI_CDK_DIR)/include/xilinx-rcc-platform.mk

# (This file is NOT intended to be included by the platform's definition file (<platform>.mk).)

# It is for software platforms for Xilinx Zynq SoCs that are based solely on things delivered directly from Xilinx:
# 1. The EDK or SDK that contains the cross-compilation toolchain
# 2. The released Linux and U-Boot source trees on github.com
# 3. The binary software release from http://www.wiki.xilinx.com.

# This file implements make goals that creates the one-time files to support an OpenCPI software platform for Zynq.

# It creates two things to support OpenCPI
# 1. A kernel headers tree (compressed) that allows the OpenCPI kernel driver to be built.
# 2. The files necessary to create a bootable SD card, including the linux kernel

# It adds a few configuration options for the kernel beyond the Xilinx minimal default.
# It adds a few patches to the Xilinx-provided root file system.

# Using this file assumes that the platform name is of the form xilinx<year>_<quarter>_<arch>.
# As a sort of special case, the last ISE release, which was version 14.7, is considered released
# on 2013.4, and there was no support for the 64 bit ARM architecture then so that one would be named
# xilinx13_4_aarch32.

# This file is not intended to be used for non-Xilinx-based platforms (e.g. Yocto).

AT=@
all:
.DELETE_ON_ERROR:
$(if $(OCPI_CDK_DIR),,$(error OCPI_CDK_DIR not set.  This file requires it.))

include $(notdir $(CURDIR)).mk
repo_tag:=xilinx-v20$(subst _,.,$(xilinx_sw_version))
linux_repo_tag:=$(or $(OcpiXilinxLinuxRepoTag),$(repo_tag))
uboot_repo_tag:=$(or $(OcpiXilinxUbootRepoTag),$(repo_tag))
local_repo:=$(or $(OCPI_XILINX_GIT_REPOSITORY),xilinx-github)
kernel_headers:=$(OcpiKernelDir).tgz
kernel_config:=$(and $(wildcard kernel-config),$(CURDIR)/kernel-config)
binary_release:=/home/jek/mac/Xilinx/ZynqReleases/2019.1-zed-release-dir/2019.1-zed-release
# kernel file from gen/patch_ub_image
kernel_image:=../uImage
# The kernel headers necessary to build the kernel driver
$(kernel_headers): | $(local_repo)
	$(OCPI_CDK_DIR)/scripts/xilinx/createLinuxKernelHeaders.sh $(linux_repo_tag) $(uboot_repo_tag) $(local_repo) $(kernel_config)
	mkdir -p c++
	cp -R -P gen/lib/libstdc++.so* c++ # need -R and -P for BSD/Macos

gen/binary-release:
	$(OCPI_CDK_DIR)/scripts/xilinx/getXilinxLinuxBinaryRelease.sh $(xilinx_sw_platform) $url $(local_repo)


# The boot files necessary to make a bootable SD card
boot: $(kernel_headers) $(binary_release)
	mkdir -p boot
	cp $(binary_release)/* boot
	echo Here is original boot dir:
	ls -l boot
	mkdir -p gen/patch_ub_image
	mv boot/image.ub gen/patch_ub_image
	set -evx; cd gen/patch_ub_image; \
	PATH=$$PATH:$(local_repo)/u-boot-xlnx/tools:$(local_repo)/linux-xlnx/scripts/dtc; \
	echo Dumping metadata for image.ub; \
	dumpimage -l image.ub; \
	dumpimage -T flat_dt -i image.ub -p 0 old-kernel; \
	dumpimage -T flat_dt -i image.ub -p 1 old-dtb; \
	dumpimage -T flat_dt -i image.ub -p 2 uramdisk.image.gz; \
	dumpimage -i $(kernel_image) -p 0 new-kernel; \
	cmp ../../boot/system.dtb old-dtb; \
	cp ../../test.its test.its; \
	mkimage -f test.its new_image.ub; \
	dumpimage -l new_image.ub; \
	cp new_image.ub ../../boot/image.ub

#	$(OCPI_CDK_DIR)/scripts/xilinx/createLinuxRootFS.sh $(xilinx_sw_platform) $(binary_release)

$(local_repo):
	mkdir $@
	$(OCPI_CDK_DIR)/scripts/xilinx/getXilinxLinuxSources.sh $(local_repo)

# Dump out things about the compiler
dump:
	$(AT)mkdir -p gen
	$(AT)$(OcpiCrossCompile)gcc -Q --help=target > gen/gcc-target-options
	$(AT)echo 'void x() { }' > gen/t.c
	$(AT)$(OcpiCrossCompile)gcc -c -dD -E gen/t.c > gen/gcc-predefined-macros
	$(AT)$(OcpiCrossCompile)gcc -dumpspecs > gen/gcc-specs
	$(AT)echo 'The gen/ subdir now has gcc-target-options, gcc-predefined-macros and gcc-specs'

all: $(kernel_headers)

# Clean the repo if it is local
# Do not clean the kernel headers, they are expected to be added to the repo with git add
clean:
	rm -r -f xilinx-github gen

cleaneverything distclean: clean
	rm -f $(kernel_headers)

