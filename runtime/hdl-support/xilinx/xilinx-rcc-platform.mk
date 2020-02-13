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

####################################################################################################
# This makefile fragment is meant to be included in a RCC/SW platform's Makefile using:

# include $(OCPI_CDK_DIR)/include/xilinx-rcc-platform.mk

# (This file is *NOT* intended to be included by the platform's definition file (<platform>.mk).)

# It is for software platforms for Xilinx Zynq and ZymqMP SoCs that are based solely on things
# delivered directly from Xilinx:
#   1. The EDK or SDK (from ISE or Vivado) that contains the cross-compilation toolchain.
#   2. The released Linux and U-Boot source trees on github.com
#   3. The binary software release from http://www.wiki.xilinx.com.
# All three of these things will come from a common (the same) Xilinx release, e.g. 2017.4

# This file implements make targets that create the one-time files to support an OpenCPI software
# platform for Zynq, which will be locked to a specific Xilinx release and (ARM) CPU architecture
# (aarch32 vs. aarch64).
# Thus "make" here will make things that should end up being added to the OpenCPI git repo since
# creating them depends on things OUTSIDE the repo that are not necessarily always present.
# I.e. we do not want to insist on Xilinx linux and u-boot sources or binary releases be present
# to build OpenCPI.  We of source do expect that the EDK/SDK is always present.

# The prerequisites for a xilinx-rcc-platform are three things from Xilinx
# 1. The software tools installation (ISE/EDK or Vivado/SDK)
# 2. The Xilinx binary release (which also implies a specific kernel source repo tag)
# 3. The Xilinx linux kernel git repo (which is checked out ffor the specific repo tag)
# Thus the same Xilinx release version is used for all of them (e.g. 2019.1)

# Using this file assumes that the platform name is of the form xilinx<year>_<quarter>_<arch>.
# As a sort of special case, the last ISE release, which was version 14.7, is considered released
# on 2013.4, and there was no support for the 64 bit ARM architecture then so that one would be named
# xilinx13_4_aarch32.

# This file is not intended to be used for non-Xilinx-based platforms (e.g. Yocto).

# There are three main activities implemented here:

# 1. The make target "kernel-artifacts" - the stuff we need from the Xilinx Linux Kernel and U-boot repos.
#    Using the cross-tools in the Xilinx ISE/EDK or Vivado/SDK release, with a possibly-patched
#    kernel code and configuration, using the repo tag associated with this Xilinx binary release,
#    build u-boot (and some associated tools), the kernel and the kernel-headers.
#    See the createXilinxLinuxKernelHeaders.sh script for more details.
#
#    This make target does not use make dependencies and "just does it from scratch"


# Two environment variable settings locate where xilinx source code and biniary releases are stored:
# OCPI_XILINX_GIT_REPOSITORY is where the github u-boot and linux repos are (where they have been cloned).
# If this is not set, this will be done locally in this directory, which is not ideal...
# OCPI_XILINX_ZYNQ_RELEASE_DIR iis where the Xilinx binary release tarballs are downloaded.

AT=@
all:
.DELETE_ON_ERROR:
$(if $(wildcard $(OCPI_CDK_DIR)),,$(error OCPI_CDK_DIR not set or non-existent.  This file requires it.))

include $(notdir $(CURDIR)).mk
repo_tag:=xilinx-v20$(subst _,.,$(xilinx_sw_version))
linux_repo_tag:=$(or $(OcpiXilinxLinuxRepoTag),$(repo_tag))
uboot_repo_tag:=$(or $(OcpiXilinxUbootRepoTag),$(repo_tag))
local_repo:=$(or $(OCPI_XILINX_GIT_REPOSITORY),$(call OcpiXilinxDir)/git)
xilinx_releases:=$(or $(OCPI_XILINX_ZYNQ_RELEASE_DIR),$(call OcpiXilinxDir,warning)/ZynqReleases)
kernel_headers:=$(OcpiKernelDir).tgz
kernel_config:=$(and $(wildcard kernel.config),$(CURDIR)/kernel.config)
binary_release:=/home/jek/mac/Xilinx/ZynqReleases/2019.1-zed-release-dir/2019.1-zed-release
# kernel file from gen/patch_ub_image
kernel_image:=../uImage

# use default exports.
#ifeq ($(wildcard $(xilinx_sw_platform).exports),)

all: gen

get-kernel-repos:
	echo Retrieving/downloading the Xilinx source trees for the linux kernel and u-boot into $(local_repo)
	$(OCPI_CDK_DIR)/scripts/xilinx/getXilinxLinuxSources.sh $(local_repo)
	echo Listing Xilinx linux kernel repo tags in chronological order:
	$(OCPI_CDK_DIR)/scripts/xilinx/showXilinxLinuxTags.sh $(local_repo)
	echo The above listing is all tags in chronological order.
	echo To redo this listing (e.g. with grep), use this command:
	echo $(OCPI_CDK_DIR)/scripts/xilinx/showXilinxLinuxTags.sh $(local_repo)

# Retrieve/patch/build artifacts we need from the kernel+u-boot source repo, which is at OCPI_
# Note top level kernel-headers.tgz link until we get all the exports in the lib subdir
kernel-artifacts: | $(local_repo)
	$(AT)echo Retrieving/patching/building needed artifacts from the Xilinx kernel and u-boot source repos.
	$(AT)bash $(OCPI_CDK_DIR)/scripts/xilinx/createXilinxLinuxKernelHeaders.sh $(xilinx_sw_arch) \
		$(linux_repo_tag) $(uboot_repo_tag) $(local_repo) gen/kernel-artifacts "$(kernel_config)"
	$(AT)mkdir -p lib && rm -f lib/kernel-headers.tgz && ln -s ../gen/kernel-artifacts/kernel-headers.tgz lib
	$(AT)rm -f kernel-headers.tgz && ln -s lib/kernel-headers.tgz .
	$(AT)echo The kernel-headers has been created.
	$(AT)echo It is now ready for building the OpenCPI linux kernel driver for this platform

# Retrieve and/or build artifacts we need from the EDK/SDK, essentially c++ runtime libraries.
sdk-artifacts:
	$(AT)$(OCPI_CDK_DIR)/scripts/xilinx/importSDKartifacts.sh $(OcpiCrossCompile) gen/sdk-artifacts
	$(AT)mkdir -p lib && rm -f lib/lib && ln -s ../gen/sdk-artifacts/lib lib/lib
	$(AT)echo Libraries from the SDK have been captured for SD cards, valgrind etc.

# Retrieve the artifacts we need from the Xilinx Zynq binary release
release-artifacts:
	$(AT)$(OCPI_CDK_DIR)/scripts/xilinx/importXilinxRelease.sh $(xilinx_version_tag) $(xilinx_releases) gen/release-artifacts $(local_repo)

# Do the one-time work to create SD card artifacts for booting this platform
.PHONY: deploy cleandeploy
cleandeploy:
	rm -r -f deploy

# Put the appropriate release files in the "deploy" directory based on a Xilinx binary release
deploy: # $(kernel_headers) $(binary_release)
	$(OCPI_CDK_DIR)/scripts/xilinx/patchXilinxInitRamFS.sh $(xilinx_version_tag) $(xilinx_releases) deploy


# Unpack the root file system from the binary release
root:
	rm -r -f root
	mkdir -p root

ifneq (,)
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

endif

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
