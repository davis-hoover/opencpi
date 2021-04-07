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
# See README in this directory for more info about this library

include $(OCPI_CDK_DIR)/include/hdl/xilinx.mk

ExcludeTargets=zynq zynq_ise zynq_ultra isim xsim virtex5 virtex6 modelsim stratix4 stratix5 cyclone arria10soc arria10soc_std

# HdlLibraries= ocpi axi sdp platform
HdlLibraries= ocpi axi sdp platform

VivadoPcieTargets= artix7 
OnlyTargets=$(VivadoPcieTargets)

# We need to include this file before hdl-library.mk to preprocess the platforms and targets (at least)
include $(OCPI_CDK_DIR)/include/hdl/hdl-make.mk
# $(eval $(HdlPreprocessTargets))

XilinxCoreName=axi_pcie
################################################################################
# These are used by the generic code below
ISEWrapperModule=$(XilinxCoreName)

################################################################################
# Vivado method of getting the IP core.  We let tcl determine the version and get the wrapper
VivadoIpDir=$(call OcpiXilinxVivadoDir,infox)/data/ip/xilinx
# Core name is derived from the wrapper name returned by tcl
# ## VivadoPcieCore=$(VivadoWrapperModule:%_processing_system7=%)
VivadoPcieCore="$(VivadoWrapperModule)"
# VivadoPcieSources=$(foreach f,atc aw_atc b_atc trace_buffer w_atc,\

VivadoPcieSources=$(foreach f,stub,\
                    $(VivadoIpDir)/$(VivadoPcieCore)/hdl/$(VivadoPcieCore)_$f.vhd) \
                  $(VivadoWrapperFile)

ifeq ($(filter clean%,$(MAKECMDGOALS))$(if $(HdlTargets),,z),)  # if not cleaning and building hdl target
  ifndef UseISE                            			# if non-ISE targets
    VivadoWrapperFile=$(wildcard gen/synth/$(XilinxCoreName)*.v)
    ifeq ($(VivadoWrapperFile),) # if wrapper-module not determined yet
      $(if $(call DoShell,\
              rm -r -f gen && mkdir -p gen && cd gen && rm -r -f tmp && mkdir tmp && \
              (cd tmp && \
                           $(call OcpiXilinxVivadoInit) && \
                           vivado -mode batch -source ../../gen_ip.tcl \
                                  -tclargs $(XilinxCoreName) xc7a50tcpg236-3 \
                          ) > gen-pcie.log && \
                           rm -r -f tmp,MyError),\
           $(error $(MyError)))
    endif # if need to get the wrapper
  endif # if non-ISE targets
  VivadoWrapperModule:=$(basename $(notdir $(VivadoWrapperFile)))
  WrapperModule=$(if $(UseISE),$(ISEWrapperModule),$(VivadoWrapperModule))
  $(info The IP wrapper module name is: $(WrapperModule))
endif # if not cleaning

# ################################################################################
# # Generic, VIVADO or ISE
GenPcieSources=$(wildcard gen/hdl/lib_*) $(wildcard gen/hdl/axi_*)  
#$(info GenPcieSources: $(GenPcieSources))
SourceFiles=generic_pcie_pkg.vhd
# ##### SourceFiles=generic_pcie_pkg.vhd $(GenPcieSources) $(VivadoWrapperFile) generic_pcie.vhd
# OcpiCPPDefines=$(and $(UseISE),XILINX_ISE=1) PS7_WRAPPER_MODULE=$(WrapperModule)
#
include $(OCPI_CDK_DIR)/include/hdl/hdl-library.mk
