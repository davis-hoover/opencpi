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

HdlLibraries=fixed_float ocpi axi sdp platform

VivadoZynqTargets=zynq xsim
ISEZynqTargets=zynq_ise isim
OnlyTargets=$(VivadoZynqTargets) $(ISEZynqTargets)

# We need to include this file before hdl-library.mk to preprocess the platforms and targets (at least)
include $(OCPI_CDK_DIR)/include/hdl/hdl-make.mk
$(eval $(HdlPreprocessTargets))
MyTargets:=$(sort $(HdlTargets))
ifneq ($(and $(filter $(ISEZynqTargets),$(MyTargets)),$(filter $(VivadoZynqTargets),xsim,$(MyTargets))),)
  $(error The zynq primitive library cannot be built for zynq_ise/isim and zynq/xsim at the same time (yet))
endif
UseISE:=$(filter $(ISEZynqTargets),$(HdlTargets))

XilinxCoreName=processing_system7
################################################################################
# ISE method of getting the Zynq PS core
ISEIpDir=$(call OcpiXilinxIseEdkDir,infox)/hw/XilinxProcessorIPLib/pcores
ISEZynqCore=processing_system7_v4_03_a
# These are used by the generic code below
ISEWrapperModule=$(XilinxCoreName)
ISEZynqSources=$(foreach f,atc aw_atc b_atc processing_system7 trace_buffer w_atc,\
                  $(ISEIpDir)/$(ISEZynqCore)/hdl/verilog/$f.v)

################################################################################
# Vivado method of getting the Zynq PS core.  We let tcl determine the version and get the wrapper
VivadoIpDir=$(call OcpiXilinxVivadoDir,infox)/data/ip/xilinx
# Core name is derived from the wrapper name returned by tcl
VivadoZynqCore=$(VivadoWrapperModule:%_processing_system7=%)
VivadoZynqSources=$(foreach f,atc aw_atc b_atc trace_buffer w_atc,\
                    $(VivadoIpDir)/$(VivadoZynqCore)/hdl/verilog/$(VivadoZynqCore)_$f.v) \
                  $(VivadoWrapperFile)
# The TCL script that gets the wrapper verilog code also determines the version and module name.
# Since this determines the file name of the wrapper code, we do it here on the first pass of make
# so the "SourceFiles" to build includes the module whose name is determined by the tcl.
# It actually depends on the tcl script (which is in ../zynq) and of course the particular
# version of Vivado installed. If either of those changes a clean build here is required.
ifeq ($(filter clean%,$(MAKECMDGOALS))$(if $(HdlTargets),,z),)  # if not cleaning and building hdl target
  ifndef UseISE                            			# if non-ISE targets
    VivadoWrapperFile=$(wildcard gen/$(XilinxCoreName)*.v)
    ifeq ($(VivadoWrapperFile),) # if wrapper-module not determined yet
      $(info Generating the verilog wrapper for the Zynq 7000 PS (PS7 primitive).)
      $(if $(call DoShell,\
              mkdir -p gen && cd gen && rm -r -f tmp && mkdir tmp && \
              (cd tmp && \
                           $(call OcpiXilinxVivadoInit) && \
                           vivado -mode batch -source ../../vivado-gen-ps.tcl \
                                  -tclargs $(XilinxCoreName) xc7z020-clg484-1 \
                          ) > vivado-gen-ps7.log && \
                           rm -r -f tmp,MyError),\
           $(error $(MyError)))
      VivadoWrapperFile:=$(shell echo gen/$(XilinxCoreName)*.v)
    endif # if need to get the wrapper
  endif # if non-ISE targets
  VivadoWrapperModule:=$(basename $(notdir $(VivadoWrapperFile)))
  WrapperModule=$(if $(UseISE),$(ISEWrapperModule),$(VivadoWrapperModule))
  $(info The Zynq 7000 PS wrapper module name is: $(WrapperModule))
endif # if not cleaning

################################################################################
# Generic, VIVADO or ISE
SourceFiles=zynq_pkg.vhd $(if $(UseISE),$(ISEZynqSources),$(VivadoZynqSources)) zynq_ps.cpp_vhd zynq_sdp.vhd
OcpiCPPDefines=$(and $(UseISE),XILINX_ISE=1) PS7_WRAPPER_MODULE=$(WrapperModule)

include $(OCPI_CDK_DIR)/include/hdl/hdl-library.mk
