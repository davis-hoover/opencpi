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

include $(OCPI_CDK_DIR)/include/hdl/xilinx.mk
OnlyTargets=zynq_ultra
include $(OCPI_CDK_DIR)/include/hdl/hdl-make.mk
ifeq ($(filter clean%,$(MAKECMDGOALS))$(if $(HdlTargets),,z),)  # if not cleaning and building hdl target
  $(info Generating the Xilinx RF Data Converter IP.)
  $(if $(call DoShell,\
      mkdir -p gen && cd gen && rm -r -f tmp && mkdir tmp && \
      (cd tmp && \
      $(call OcpiXilinxVivadoInit) && \
      vivado -mode batch -source ../../vivado-gen-rfdc.tcl \
      -tclargs xczu48dr-ffve1156-2-i \
      ) > vivado-gen-rfdc.log && \
      rm -r -f tmp,MyError),\
      $(error $(MyError)))
endif # if not cleaning
SourceFiles=rfdc_pkg.vhd gen/rfdc_ip.v gen/rfdc_ip.xdc gen/rfdc_ip_address_decoder.v gen/rfdc_ip_axi_lite_ipif.v gen/rfdc_ip_bgt_fsm.v gen/rfdc_ip_block.v gen/rfdc_ip_clk_detection.v gen/rfdc_ip_clocks.xdc gen/rfdc_ip_constants_config.sv gen/rfdc_ip_counter_f.v gen/rfdc_ip_device_rom.sv gen/rfdc_ip_drp_access_ctrl.v gen/rfdc_ip_drp_arbiter.v gen/rfdc_ip_drp_arbiter_adc.v gen/rfdc_ip_drp_control.v gen/rfdc_ip_drp_control_top.v gen/rfdc_ip_irq_req_ack.v gen/rfdc_ip_irq_sync.v gen/rfdc_ip_ooc.xdc gen/rfdc_ip_overvol_irq.v gen/rfdc_ip_por_fsm.sv gen/rfdc_ip_por_fsm_disabled.sv gen/rfdc_ip_por_fsm_top.sv gen/rfdc_ip_powerup_state_irq.v gen/rfdc_ip_pselect_f.v gen/rfdc_ip_register_decode.v gen/rfdc_ip_rf_wrapper.v gen/rfdc_ip_rst_cnt.v gen/rfdc_ip_slave_attachment.v gen/rfdc_ip_tile_config.sv gen/rfdc_ipbufg_gt_ctrl.v rfdc_prim.vhd
include $(OCPI_CDK_DIR)/include/hdl/hdl-library.mk
