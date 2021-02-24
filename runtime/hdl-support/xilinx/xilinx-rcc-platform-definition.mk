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

# This makefile fragment is meant to be included by the Xilinx-based RCC/SW platform's definition file using:
# include $(OCPI_CDK_DIR)/include/xilinx-rcc-platform-definition.mk
# (This file is NOT intended to be included by the platform's Makefile)
# It provides some consistent functionality common to all such platforms.
# - Determines proper proper tool version
# - Checks that tools are installed

# Get platform from the filename that included this one
xilinx_sw_platform:=$(basename $(notdir $(lastword $(filter-out $(lastword $(MAKEFILE_LIST)),$(MAKEFILE_LIST)))))
xilinx_sw_fields:=$(subst _, ,$(subst xilinx,,$(xilinx_sw_platform)))
xilinx_sw_version:=$(word 1,$(xilinx_sw_fields))_$(word 2,$(xilinx_sw_fields))
xilinx_sw_arch:=$(word 3,$(xilinx_sw_fields))

xilinx_version_tag:=20$(subst _,.,$(xilinx_sw_version))
$(shell echo Xilinx RCC platform is: $(xilinx_sw_platform).  Version is: $(xilinx_sw_version).  Architecture is: $(xilinx_sw_arch) > /dev/stderr)
ifndef xilinx_sw_tool_dir
  ifndef OCPI_XILINX_VIVADO_SDK_VERSION
    OCPI_XILINX_VIVADO_SDK_VERSION:=$(xilinx_version_tag)
  endif
  include $(OCPI_CDK_DIR)/include/hdl/xilinx.mk
  xilinx_sdk_dir:=$(call OcpiXilinxSdkDir,$(if $(filter deploy clean%,$(MAKECMDGOALS)),warning,error))/gnu
  xilinx_lin:=$(strip\
    $(or $(wildcard $(xilinx_sdk_dir)/$(xilinx_sw_arch)),\
	 $(and $(filter aarch32,$(xilinx_sw_arch)),$(wildcard $(xilinx_sdk_dir)/arm)),\
         $(error Could not find an architecture directory for "$(xilinx_sw_arch)" in $(xilinx_sdk_dir))))/lin
  ifeq ($(xilinx_sw_arch),aarch64)
    xilinx_sw_tool_dir:=$(xilinx_lin)/aarch64-linux/bin
    xilinx_sw_tool_prefix:=aarch64-linux-gnu-
  else ifeq ($(xilinx_sw_arch),aarch32)
    xilinx_sw_tool_dir:=$(xilinx_lin)/gcc-arm-linux-gnueabi/bin
    xilinx_sw_tool_prefix:=arm-linux-gnueabihf-
  else ifeq ($(xilinx_sw_arch),arm)
    xilinx_sw_tool_dir:=$(xilinx_lin)/bin
    xilinx_sw_tool_prefix:=arm-xilinx-linux-gnueabi-
  endif
else
  include $(OCPI_CDK_DIR)/include/hdl/xilinx.mk
endif
ifeq ($(filter deploy clean%,$(MAKECMDGOALS))$(wildcard $(xilinx_sw_tool_dir)),)
  $(error When setting up to build for zynq for $(xilinx_sw_platform), cannot find $(xilinx_sw_tool_dir). Perhaps the SDK was not installed\
          when Xilinx tools were installed? The non-default Xilinx environment settings were: \
          $(foreach v,$(filter OCPI_XILINX%,$(.VARIABLES)), $v=$($v)))
endif
# For now these next three are in fact rewritten in each definition file...
OcpiPlatformOs:=linux
OcpiPlatformOsVersion:=x$(xilinx_version)
OcpiPlatformArch:=$(xilinx_sw_arch)
OcpiKernelDir:=kernel-headers
OcpiCrossCompile:=$(xilinx_sw_tool_dir)/$(xilinx_sw_tool_prefix)
