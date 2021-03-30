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
include $(OCPI_CDK_DIR)/include/hdl/altera.mk

VivadoZynqTargets=zynq
ISEZynqTargets=zynq_ise isim
VivadoZynqUltraPlusTargets=zynq_ultra
VivadoXsimTargets=xsim
QuartusCyclone5Targets=cyclone5
ModelsimTargets=modelsim
OnlyTargets=zynq $(ISEZynqTargets) zynq_ultra cyclone5 modelsim xsim

# We need to include this file before hdl-library.mk to preprocess the platforms and targets (at least)
include $(OCPI_CDK_DIR)/include/hdl/hdl-make.mk
$(eval $(HdlPreprocessTargets))
MyTargets:=$(sort $(HdlTargets))
ifneq ($(and $(filter $(ISEZynqTargets),$(MyTargets)),$(filter $(VivadoZynqTargets),xsim,$(MyTargets)),$(filter $(VivadoZynqUltraPlusTargets),xsim,$(MyTargets))),)
  $(error The clocking primitive library cannot be built for zynq_ise/isim, zynq/xsim, and zynq_ultra/xsim at the same time (yet))
endif
UseISE:=$(filter $(ISEZynqTargets),$(HdlTargets))
UseVIVADOZynq:=$(filter $(VivadoZynqTargets),$(HdlTargets))
UseVIVADOZynqUltraPlus:=$(filter $(VivadoZynqUltraPlusTargets),$(HdlTargets))
UseVIVADOXsim:=$(filter $(VivadoXsimTargets),$(HdlTargets))
UseQUARTUSCycloneV:=$(filter $(QuartusCyclone5Targets),$(HdlTargets))
UseModelsim:=$(filter $(ModelsimTargets),$(HdlTargets))

ifeq ($(filter clean%,$(MAKECMDGOALS)),)   # if not cleaning
  ifdef UseVIVADOZynqUltraPlus
    ifeq ($(wildcard ip_gen/vivado_ip/timestamp-zynq_ultra_clk_wiz),) # if it hasn't been generated
     $(info ==============================================)
     $(info  Generating Zynq UltraScale Plus clk_wiz.)
     $(info ==============================================)
     $(if $(call DoShell,cd ip_gen && $(call OcpiXilinxVivadoInit) && ./generate_clk_gen_ip.sh zynq_ultra, MyError),$(error $(MyError)))
     $(info Generation of IP Succeeded.)
  endif
  else ifdef UseVIVADOZynq
   ifeq ($(wildcard ip_gen/vivado_ip/timestamp-zynq_clk_wiz),) # if it hasn't been generated
     $(info ==============================================)
     $(info       Generating Zynq 7000 clk_wiz.)
     $(info ==============================================)
     $(if $(call DoShell,cd ip_gen && $(call OcpiXilinxVivadoInit) && ./generate_clk_gen_ip.sh zynq, MyError),$(error $(MyError)))
     $(info Generation of IP Succeeded.)
  endif
  else ifdef UseVIVADOXsim
    ifeq ($(wildcard ip_gen/vivado_ip/timestamp-zynq_ultra_clk_wiz),) # if it hasn't been generated
     $(info ==============================================)
     $(info  Generating Zynq UltraScale Plus clk_wiz.)
     $(info ==============================================)
     $(if $(call DoShell,cd ip_gen && $(call OcpiXilinxVivadoInit) && ./generate_clk_gen_ip.sh zynq_ultra, MyError),$(error $(MyError)))
     $(info Generation of IP Succeeded.)
    endif
    ifeq ($(wildcard ip_gen/vivado_ip/timestamp-zynq_clk_wiz),) # if it hasn't been generated
     $(info ==============================================)
     $(info       Generating Zynq 7000 clk_wiz.)
     $(info ==============================================)
     $(if $(call DoShell,cd ip_gen && $(call OcpiXilinxVivadoInit) && ./generate_clk_gen_ip.sh zynq, MyError),$(error $(MyError)))
     $(info Generation of IP Succeeded.)
    endif
  else ifdef UseISE
    ifeq ($(wildcard ip_gen/ise_ip/timestamp-zynq_ise_clk_wiz),) # if it hasn't been generated
     $(info ==============================================)
     $(info       Generating Zynq 7000 clk_wiz.)
     $(info ==============================================)
     $(if $(call DoShell,cd ip_gen && $(call OcpiXilinxIseInit) && ./generate_clk_gen_ip.sh zynq_ise, MyError),$(error $(MyError)))
     $(info Generation of IP Succeeded.)
    endif
  # Enable this once Quartus is installed on the runners for the pipeline
  # else ifdef UseQUARTUSCycloneV
  #   ifeq ($(wildcard ip_gen/quartus_ip/timestamp-cyclone5_altera_pll),) # if it hasn't been generated
  #    $(info ==============================================)
  #    $(info       Generating Cyclone V altera_pll.)
  #    $(info ==============================================)
  #    $(if $(call DoShell,cd ip_gen && ./generate_clk_gen_ip.sh cyclone5 $(OcpiAlteraQuartusDir) $(OcpiAlteraLicenseFile), MyError),$(error $(MyError)))
  #    $(info Generation of IP Succeeded.)
  #   endif
  # else ifdef UseModelsim
  #   ifeq ($(wildcard ip_gen/quartus_ip/timestamp-cyclone5_altera_pll),) # if it hasn't been generated
  #    $(info ==============================================)
  #    $(info       Generating Cyclone V altera_pll.)
  #    $(info ==============================================)
  #    $(if $(call DoShell,cd ip_gen && ./generate_clk_gen_ip.sh cyclone5 $(OcpiAlteraQuartusDir) $(OcpiAlteraLicenseFile), MyError),$(error $(MyError)))
  #    $(info Generation of IP Succeeded.)
  #   endif
  endif
endif

include $(OCPI_CDK_DIR)/include/hdl/hdl-library.mk

clean::
	$(AT)rm -rf ip_gen/vivado_ip/tmp; \
       rm -f  ip_gen/vivado_ip/zynq_mmcm_clk_wiz.log; \
       rm -f  ip_gen/vivado_ip/zynq_pll_clk_wiz.log; \
       rm -f  ip_gen/vivado_ip/zynq_ultra_mmcm_clk_wiz.log; \
       rm -f  ip_gen/vivado_ip/zynq_ultra_pll_clk_wiz.log; \
			 rm -rf ip_gen/ise_ip/tmp; \
       rm -f  ip_gen/ise_ip/zynq_ise_mmcm_clk_wiz.log; \
       rm -f  ip_gen/ise_ip/zynq_ise_pll_clk_wiz.log; \
		 	 rm -rf ip_gen/quartus_ip/tmp; \
       rm -f  ip_gen/quartus_ip/cyclone5_altera_pll.log;