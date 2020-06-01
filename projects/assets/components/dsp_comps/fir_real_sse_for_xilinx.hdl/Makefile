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

include $(OCPI_CDK_DIR)/include/hdl/xilinx.mk

VivadoZynqTargets=zynq xsim 
ISEZynqTargets=zynq_ise isim
OnlyTargets=$(VivadoZynqTargets)

# We need to include this file before worker.mk to preprocess the platforms and targets (at least) 
include $(OCPI_CDK_DIR)/include/hdl/hdl-make.mk
$(eval $(HdlPreprocessTargets))
MyTargets:=$(sort $(HdlTargets))
IsXSim=$(filter xsim,$(HdlTargets))
ifneq ($(and $(filter $(ISEZynqTargets),$(MyTargets)),$(filter $(VivadoZynqTargets),xsim,$(MyTargets))),)
  $(error The zynq primitive library cannot be built for zynq_ise/isim and zynq/xsim at the same time (yet))
endif
UseISE:=$(filter $(ISEZynqTargets),$(HdlTargets))

XilinxCoreName=fir_compiler

ifeq ($(filter clean%,$(MAKECMDGOALS)),) # if not cleaning 
  ifndef UseISE				 # if non-ISE targets 
    VivadoWrapperFile=$(wildcard gen/vivado_ip/$(XilinxCoreName)*.vhd)
    ifeq ($(VivadoWrapperFile),) # if wrapper file not generated yet 
      $(info running TCL script)
      $(if $(call DoShell,\
	mkdir -p gen/vivado_ip && cd gen/vivado_ip && rm -r -f tmp && mkdir tmp && \
	(cd tmp && \
		$(call OcpiXilinxVivadoInit) && \
		vivado -mode batch -source ../../../vivado-gen-fir.tcl \
			-tclargs $(XilinxCoreName) xc7z020-clg484-1 \
			) > vivado-gen-fir.log && \
			rm -r -f tmp && \
                        ../../generate_reload_rom.py -a_bw 7 -d_bw 8 \
                        ./$(XilinxCoreName)_0_reload_order.txt ../fir_real_sse_for_xilinx_reload_order_rom.vhd ,MyError),\
	$(error $(MyError)))
    endif # if need to get the wrapper 
  endif # if non-ISE targets 
endif # if not cleaning 

SimSourceFiles=./gen/vivado_ip/fir_compiler_0_sim.vhd 
SynthSourceFiles=./gen/vivado_ip/fir_compiler_0_stub.vhd 
SynthCoreFiles=./gen/vivado_ip/fir_compiler_0.edf

SourceFiles=./gen/fir_real_sse_for_xilinx_reload_order_rom.vhd $(if $(IsXSim),$(SimSourceFiles),$(SynthSourceFiles))
ifeq ($(IsXSim),) # if not xsim set cores for synthesis 
  Cores=$(SynthCoreFiles)
endif

include $(OCPI_CDK_DIR)/include/worker.mk

