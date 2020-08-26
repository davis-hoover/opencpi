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
Libraries=ocpi platform fixed_float cdc

include $(OCPI_CDK_DIR)/include/hdl/xilinx.mk

VivadoZynqTargets=zynq xsim
ISEZynqTargets=zynq_ise isim
OnlyTargets=$(VivadoZynqTargets) $(ISEZynqTargets) modelsim

# We need to include this file before hdl-library.mk to preprocess the platforms and targets (at least)
include $(OCPI_CDK_DIR)/include/hdl/hdl-make.mk
$(eval $(HdlPreprocessTargets))
MyTargets:=$(sort $(HdlTargets))
ifneq ($(and $(filter $(ISEZynqTargets),$(MyTargets)),$(filter $(VivadoZynqTargets),xsim,$(MyTargets))),)
  $(error The clocking primitive library cannot be built for zynq_ise/isim and zynq/xsim at the same time (yet))
endif
UseISE:=$(filter $(ISEZynqTargets),$(HdlTargets))
UseVIVADO:=$(filter $(VivadoZynqTargets),$(HdlTargets))

XilinxCoreName=clk_wiz
XilinxClockPrimitive=mmcm pll

# The TCL script that gets generates the clk_wiz
ifeq ($(filter clean%,$(MAKECMDGOALS)),)   # if not cleaning
  ifdef UseVIVADO                          # if non-ISE targets
    ifeq ($(wildcard vivado_clk_wiz/timestamp-clk_wiz),) # if it hasn't been generated
      $(info Generating Zynq 7000 clk_wiz.)
      $(if $(call DoShell,\
	            mkdir -p vivado_clk_wiz/tmp && cd vivado_clk_wiz && rm -r -f tmp && mkdir tmp && for prim in $(XilinxClockPrimitive) ; do \
	            (cd tmp && \
	                         $(call OcpiXilinxVivadoInit) && \
													 vivado -mode batch -source ../vivado-gen-clk_wiz.tcl \
													 				-tclargs $(XilinxCoreName) $$prim \
																	$${prim}e2 xc7z020-clg484-1 \
													) > clk_wiz.log && \
													 patch -F 5 < $${prim}e2.patch && patch < $${prim}e2_sim.patch && \
													 mv $${prim}e2.v ../zynq/$${prim}e2.v && mv $${prim}e2_sim.vhd ../xsim/$${prim}e2.vhd && \
													 rm -r -f $${prim}e2.v.orig; done && \
													 date > timestamp-clk_wiz && \
	                         rm -r -f tmp,MyError),\
	         $(error $(MyError)))
    endif
  else ifdef UseISE
    ifeq ($(wildcard ise_clk_wiz/timestamp-clk_wiz),)
      $(info Generating Zynq 7000 clk_wiz.)
      $(if $(call DoShell,\
		  		 mkdir -p ise_clk_wiz/tmp && cd ise_clk_wiz && rm -r -f tmp && mkdir tmp && for prim in $(XilinxClockPrimitive) ; do\
		  	   (cd tmp && \
			     							$(call OcpiXilinxIseInit) && \
												coregen -b ../ise-gen-clk_wiz-$${prim}-coregen-commands \
											 ) > clk_wiz.log && cp tmp/managed_ip_project/$${prim}e2.vhd . && \
											  patch < $${prim}e2.patch && \
											  cp $${prim}e2.vhd ../isim/$${prim}e2.vhd && \
											  mv $${prim}e2.vhd ../zynq_ise/$${prim}e2.vhd; done && \
												date > timestamp-clk_wiz && \
												rm -r -f tmp,MyError),\
		 $(error $(MyError)))
    endif
  endif
endif # if not cleaning

include $(OCPI_CDK_DIR)/include/hdl/hdl-library.mk

clean::
	$(AT)rm -rf vivado_clk_wiz/tmp; \
			 rm -f vivado_clk_wiz/clk_wiz.log; \
			 rm -rf ise_clk_wiz/tmp; \
		 	 rm -f ise_clk_wiz/clk_wiz.log;
