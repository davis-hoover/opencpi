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

HdlLibraries= ocpi axi sdp platform cdc

VivadoPcieTargets= artix7
OnlyTargets=$(VivadoPcieTargets)

# We need to include this file before hdl-library.mk to preprocess the platforms and targets (at least)
include $(OCPI_CDK_DIR)/include/hdl/hdl-make.mk
$(eval $(HdlPreprocessTargets))

ifneq ($(filter $(OnlyTargets),$(HdlTargets) $(foreach p,$(HdlPlatforms),$(HdlTarget_$p))),)

   XilinxCoreName=axi_pcie
   ################################################################################
   # These are used by the generic code below
   ISEWrapperModule=$(XilinxCoreName)

   ################################################################################
   VivadoIpDir=$(call OcpiXilinxVivadoDir,infox)/data/ip/xilinx
   VivadoPcieCore=axi_pcie_v2_9

   VivadoPcieSources=$(foreach f,rfs,\
                       $(VivadoIpDir)/$(VivadoPcieCore)/hdl/$(VivadoPcieCore)_$f.vhd) \
                     $(VivadoWrapperFile)

   ifeq ($(filter clean%,$(MAKECMDGOALS))$(if $(HdlTargets),,a),)
     ifndef UseISE                            # if non-ISE targets
       VivadoWrapperFile=$(wildcard gen/synth/$(XilinxCoreName)*.v)
       ifeq ($(VivadoWrapperFile),) # if wrapper-module not determined yet
         $(if $(call DoShell,\
                 rm -r -f gen && mkdir -p gen && cd gen && rm -r -f tmp && mkdir tmp && \
                 (cd tmp && \
                              $(call OcpiXilinxVivadoInit) && \
                              vivado -mode batch -source ../../gen_ip.tcl \
                                     -tclargs $(XilinxCoreName) xc7a50tcsg325-2 \
                             ) > gen-pcie.log, MyError), $(error $(MyError))) 
                             #) > gen-pcie.log && rm -r -f tmp,MyError), $(error $(MyError))) 
       endif # if need to get the wrapper
     endif # if non-ISE targets
     VivadoWrapperModule:=$(basename $(notdir $(VivadoWrapperFile)))
     WrapperModule=$(if $(UseISE),$(ISEWrapperModule),$(VivadoWrapperModule))
   endif # if not cleaning 

   # ################################################################################
   GenPcieSources=$(wildcard gen/*_stub.vhdl) $(wildcard gen/*.edf) $(wildcard gen/*.xdc) 
   SourceFiles=generic_pcie_pkg.vhd generic_pcie.vhd $(GenPcieSources)

else
  $(info No HDL platforms or targets specified are in our OnlyTargets list: $(OnlyTargets))
endif

include $(OCPI_CDK_DIR)/include/hdl/hdl-library.mk
