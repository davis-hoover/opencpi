#-----------------------------------------------------------------------------
#
# (c) Copyright 2012-2012 Xilinx, Inc. All rights reserved.
#
# This file contains confidential and proprietary information
# of Xilinx, Inc. and is protected under U.S. and
# international copyright and other intellectual property
# laws.
#
# DISCLAIMER
# This disclaimer is not a license and does not grant any
# rights to the materials distributed herewith. Except as
# otherwise provided in a valid license issued to you by
# Xilinx, and to the maximum extent permitted by applicable
# law: (1) THESE MATERIALS ARE MADE AVAILABLE "AS IS" AND
# WITH ALL FAULTS, AND XILINX HEREBY DISCLAIMS ALL WARRANTIES
# AND CONDITIONS, EXPRESS, IMPLIED, OR STATUTORY, INCLUDING
# BUT NOT LIMITED TO WARRANTIES OF MERCHANTABILITY, NON-
# INFRINGEMENT, OR FITNESS FOR ANY PARTICULAR PURPOSE; and
# (2) Xilinx shall not be liable (whether in contract or tort,
# including negligence, or under any other theory of
# liability) for any loss or damage of any kind or nature
# related to, arising under or in connection with these
# materials, including for any direct, or any indirect,
# special, incidental, or consequential loss or damage
# (including loss of data, profits, goodwill, or any type of
# loss or damage suffered as a result of any action brought
# by a third party) even if such damage or loss was
# reasonably foreseeable or Xilinx had been advised of the
# possibility of the same.
#
# CRITICAL APPLICATIONS
# Xilinx products are not designed or intended to be fail-
# safe, or for use in any application requiring fail-safe
# performance, such as life-support or safety devices or
# systems, Class III medical devices, nuclear facilities,
# applications related to the deployment of airbags, or any
# other applications that could lead to death, personal
# injury, or severe property or environmental damage
# (individually and collectively, "Critical
# Applications"). Customer assumes the sole risk and
# liability of any use of Xilinx products in Critical
# Applications, subject only to applicable laws and
# regulations governing limitations on product liability.
#
# THIS COPYRIGHT NOTICE AND DISCLAIMER MUST BE RETAINED AS
# PART OF THIS FILE AT ALL TIMES.
#
# ##############################################################################
# User Configuration
# Link Width   - x1
# Link Speed   - gen2
# Family       - artix7
# Part         - xc7a50t
# Package      - csg325
# Speed grade  - -2
# PCIe Block   - X0Y0
# ##############################################################################

# ########################################################################################################################
# PCIE Core Constraints
# ########################################################################################################################

# ##############################################################################
# Pinout and Related I/O Constraints
# ##############################################################################
# SYS reset (input) signal.  The sys_reset_n signal is generated
# by the PCI Express interface (PERST#).
set_property PACKAGE_PIN A10 [get_ports sys_rst_n]
set_property IOSTANDARD LVCMOS33 [get_ports sys_rst_n]
set_property PULLDOWN true [get_ports sys_rst_n]

# SYS clock 100 MHz (input) signal. The SYS_CLK_P and SYS_CLK_N
# signals are the PCI Express reference clock. 
set_property PACKAGE_PIN B6 [get_ports sys_clkp]
set_property PACKAGE_PIN B5 [get_ports sys_clkn]

#set_property IOSTANDARD LVDS_25 [get_ports sys_clkp]
#set_property IOSTANDARD LVDS_25 [get_ports sys_clkn]

# clkreq_l is active low clock request for M.2 card to
# request PCI Express reference clock
set_property PACKAGE_PIN A9 [get_ports clkreq_n]
set_property IOSTANDARD LVCMOS33 [get_ports clkreq_n]
set_property PULLDOWN true [get_ports clkreq_n]

# PCIe x1 link
set_property PACKAGE_PIN G4 [get_ports pcie_rxp]
set_property PACKAGE_PIN G3 [get_ports pcie_rxn]
set_property PACKAGE_PIN B2 [get_ports pcie_txp]
set_property PACKAGE_PIN B1 [get_ports pcie_txn]

#set_property PACKAGE_PIN G4 [get_ports PCIE_RX_P]
#set_property PACKAGE_PIN G3 [get_ports PCIE_RX_N]
#set_property PACKAGE_PIN B2 [get_ports PCIE_TX_P]
#set_property PACKAGE_PIN B1 [get_ports PCIE_TX_N]


# MGT Loopback
#set_property PACKAGE_PIN C4 [get_ports loop_mgt_rxp]
#set_property PACKAGE_PIN C3 [get_ports loop_mgt_rxn]
#set_property PACKAGE_PIN D2 [get_ports loop_mgt_txp]
#set_property PACKAGE_PIN D1 [get_ports loop_mgt_txn]

# ##############################################################################
# Timing Constraints
# ##############################################################################

create_clock -period 10.000 -name sys_clk [get_ports sys_clkp]
# create_clock -period 10.000 -name sys_clk [get_ports sys_clkp]

# ##############################################################################
# Physical Constraints
###############################################################################

# Input reset is resynchronized within FPGA design as necessary
set_false_path -from [get_ports sys_rst_n]

# ########################################################################################################################
# End PCIe Core Constraints
# ########################################################################################################################


# ##############################################################################
# NanoEVB, PicoEVB common I/O
# ##############################################################################

set_property PACKAGE_PIN V14 [get_ports {GPIO_LED_2_LS}]
set_property PACKAGE_PIN V13 [get_ports {GPIO_LED_1_LS}]
set_property PACKAGE_PIN V12 [get_ports {GPIO_LED_0_LS}]
set_property IOSTANDARD LVCMOS33 [get_ports {GPIO_LED_2_LS}]
set_property IOSTANDARD LVCMOS33 [get_ports {GPIO_LED_1_LS}]
set_property IOSTANDARD LVCMOS33 [get_ports {GPIO_LED_0_LS}]
set_property PULLUP true [get_ports {GPIO_LED_2_LS}]
set_property PULLUP true [get_ports {GPIO_LED_1_LS}]
set_property PULLUP true [get_ports {GPIO_LED_0_LS}]
set_property DRIVE 8 [get_ports {GPIO_LED_2_LS}]
set_property DRIVE 8 [get_ports {GPIO_LED_1_LS}]
set_property DRIVE 8 [get_ports {GPIO_LED_0_LS}]

#   # Current unused I/Os
#   # clkreq_l is active low clock request for M.2 card to
#   # request PCI Express reference clock
#   set_property PACKAGE_PIN A9 [get_ports clkreq_l]
#   set_property IOSTANDARD LVCMOS33 [get_ports clkreq_l]
#   set_property PULLDOWN true [get_ports clkreq_l]
#   
#      # Auxillary I/O Connector
#      # auxio[0] - conn pin 1
#      # auxio[1] - conn pin 2
#      # auxio[2] - conn pin 4
#      # auxio[3] - conn pin 5
#      # Note: These I/O may be re-purposed to use with XADC as analog inputs
#      set_property PACKAGE_PIN A14 [get_ports auxio_tri_io[0]]
#      set_property PACKAGE_PIN A13 [get_ports auxio_tri_io[1]]
#      set_property PACKAGE_PIN B12 [get_ports auxio_tri_io[2]]
#      set_property PACKAGE_PIN A12 [get_ports auxio_tri_io[3]]
#      set_property IOSTANDARD LVCMOS33 [get_ports auxio_tri_io[0]]
#      set_property IOSTANDARD LVCMOS33 [get_ports auxio_tri_io[1]]
#      set_property IOSTANDARD LVCMOS33 [get_ports auxio_tri_io[2]]
#      set_property IOSTANDARD LVCMOS33 [get_ports auxio_tri_io[3]]
#   
#      ###############################################################################
#      # PicoEVB-specific I/O
#      # Digital IO on PCIe edge connector (PicoEVB Rev.D and newer)
#      ###############################################################################
#      set_property PACKAGE_PIN K2 [get_ports di_edge[0]]
#      set_property PACKAGE_PIN K1 [get_ports di_edge[1]]
#      set_property PACKAGE_PIN V2 [get_ports do_edge[0]]
#      set_property PACKAGE_PIN V3 [get_ports do_edge[1]]
#      set_property IOSTANDARD LVCMOS33 [get_ports di_edge[0]]
#      set_property IOSTANDARD LVCMOS33 [get_ports di_edge[1]]
#      set_property IOSTANDARD LVCMOS33 [get_ports do_edge[0]]
#      set_property IOSTANDARD LVCMOS33 [get_ports do_edge[1]]
#   
#      ###############################################################################
#      # SPI
#      ###############################################################################
#      set_property PACKAGE_PIN K16 [get_ports {SPI_0_io0_io}]
#      set_property PACKAGE_PIN L17 [get_ports {SPI_0_io1_io}]
#      set_property PACKAGE_PIN J15 [get_ports {SPI_0_io2_io}]
#      set_property PACKAGE_PIN J16 [get_ports {SPI_0_io3_io}]
#      set_property PACKAGE_PIN L15 [get_ports {SPI_0_ss_io}]
#   
#      set_property IOSTANDARD LVCMOS33 [get_ports {SPI_0_io0_io}]
#      set_property IOSTANDARD LVCMOS33 [get_ports {SPI_0_io1_io}]
#      set_property IOSTANDARD LVCMOS33 [get_ports {SPI_0_io2_io}]
#      set_property IOSTANDARD LVCMOS33 [get_ports {SPI_0_io3_io}]
#      set_property IOSTANDARD LVCMOS33 [get_ports {SPI_0_ss_io}]
#   
#      #set_property PACKAGE_PIN L15 [get_ports {real_spi_ss}]
#      #set_property IOSTANDARD LVCMOS33 [get_ports {real_spi_ss}]


# ##############################################################################
# ##############################################################################
# ##############################################################################
# PCIe Pinout and Related I/O Constraints
# ##############################################################################
#
# Transceiver instance placement.  This constraint selects the
# transceivers to be used, which also dictates the pinout for the
# transmit and receive differential pairs.  Please refer to the
# Virtex-7 GT Transceiver User Guide (UG) for more information.
#

# PCIe Lane 0
set_property LOC GTPE2_CHANNEL_X0Y3 [get_cells {ftop/pfconfig_i/picoevb_i/worker/bridge_pcie_axi/axi_pcie_inst/inst/comp_axi_enhanced_pcie/comp_enhanced_core_top_wrap/axi_pcie_enhanced_core_top_i/pcie_7x_v2_0_2_inst/pcie_top_with_gt_top.gt_ges.gt_top_i/pipe_wrapper_i/pipe_lane[0].gt_wrapper_i/gtp_channel.gtpe2_channel_i}]

# GTP Common Placement
#set_property LOC GTPE2_COMMON_X0Y1 [get_cells {ftop/pfconfig_i/picoevb_i/worker/bridge_pcie_axi/axi_pcie_inst/inst/comp_axi_enhanced_pcie/comp_enhanced_core_top_wrap/axi_pcie_enhanced_core_top_i/pcie_7x_v2_0_2_inst/pcie_top_with_gt_top.gt_ges.gt_top_i/pipe_wrapper_i/pipe_lane[0].pipe_quad.pipe_common.qpll_wrapper_i/gtp_common.gtpe2_common_i}]
set_property LOC GTPE2_COMMON_X0Y0 [get_cells {ftop/pfconfig_i/picoevb_i/worker/bridge_pcie_axi/axi_pcie_inst/inst/comp_axi_enhanced_pcie/comp_enhanced_core_top_wrap/axi_pcie_enhanced_core_top_i/pcie_7x_v2_0_2_inst/pcie_top_with_gt_top.gt_ges.gt_top_i/pipe_wrapper_i/pipe_lane[0].pipe_quad.gt_common_enabled.gt_common_int.gt_common_i/qpll_wrapper_i/gtp_common.gtpe2_common_i}]

#
# PCI Express Block placement. This constraint selects the PCI Express
# Block to be used.
#

set_property LOC PCIE_X0Y0 [get_cells {ftop/pfconfig_i/picoevb_i/worker/bridge_pcie_axi/axi_pcie_inst/inst/comp_axi_enhanced_pcie/comp_enhanced_core_top_wrap/axi_pcie_enhanced_core_top_i/pcie_7x_v2_0_2_inst/pcie_top_with_gt_top.pcie_top_i/pcie_7x_i/pcie_block_i}]

#
# BlockRAM placement
#

set_property LOC RAMB36_X0Y24 [get_cells {ftop/pfconfig_i/picoevb_i/worker/bridge_pcie_axi/axi_pcie_inst/inst/comp_axi_enhanced_pcie/comp_enhanced_core_top_wrap/axi_pcie_enhanced_core_top_i/pcie_7x_v2_0_2_inst/pcie_top_with_gt_top.pcie_top_i/pcie_7x_i/pcie_bram_top/pcie_brams_rx/brams[0].ram/use_tdp.ramb36/genblk*.bram36_tdp_bl.bram36_tdp_bl}]
set_property LOC RAMB36_X0Y23 [get_cells {ftop/pfconfig_i/picoevb_i/worker/bridge_pcie_axi/axi_pcie_inst/inst/comp_axi_enhanced_pcie/comp_enhanced_core_top_wrap/axi_pcie_enhanced_core_top_i/pcie_7x_v2_0_2_inst/pcie_top_with_gt_top.pcie_top_i/pcie_7x_i/pcie_bram_top/pcie_brams_rx/brams[1].ram/use_tdp.ramb36/genblk*.bram36_tdp_bl.bram36_tdp_bl}]
set_property LOC RAMB36_X0Y21 [get_cells {ftop/pfconfig_i/picoevb_i/worker/bridge_pcie_axi/axi_pcie_inst/inst/comp_axi_enhanced_pcie/comp_enhanced_core_top_wrap/axi_pcie_enhanced_core_top_i/pcie_7x_v2_0_2_inst/pcie_top_with_gt_top.pcie_top_i/pcie_7x_i/pcie_bram_top/pcie_brams_tx/brams[0].ram/use_tdp.ramb36/genblk*.bram36_tdp_bl.bram36_tdp_bl}]
set_property LOC RAMB36_X0Y20 [get_cells {ftop/pfconfig_i/picoevb_i/worker/bridge_pcie_axi/axi_pcie_inst/inst/comp_axi_enhanced_pcie/comp_enhanced_core_top_wrap/axi_pcie_enhanced_core_top_i/pcie_7x_v2_0_2_inst/pcie_top_with_gt_top.pcie_top_i/pcie_7x_i/pcie_bram_top/pcie_brams_tx/brams[1].ram/use_tdp.ramb36/genblk*.bram36_tdp_bl.bram36_tdp_bl}]

# ##############################################################################
# Timing Constraints
# ##############################################################################
#
create_clock -name txoutclk -period 10 [get_pins ftop/pfconfig_i/picoevb_i/worker/bridge_pcie_axi/axi_pcie_inst/inst/comp_axi_enhanced_pcie/comp_enhanced_core_top_wrap/axi_pcie_enhanced_core_top_i/pcie_7x_v2_0_2_inst/pcie_top_with_gt_top.gt_ges.gt_top_i/pipe_wrapper_i/pipe_lane[0].gt_wrapper_i/gtp_channel.gtpe2_channel_i/TXOUTCLK]
#

#
set_false_path -to [get_pins {ftop/pfconfig_i/picoevb_i/worker/bridge_pcie_axi/axi_pcie_inst/inst/comp_axi_enhanced_pcie/comp_enhanced_core_top_wrap/axi_pcie_enhanced_core_top_i/pcie_7x_v2_0_2_inst/pcie_top_with_gt_top.gt_ges.gt_top_i/pipe_wrapper_i/pipe_clock_int.pipe_clock_i/pclk_i1_bufgctrl.pclk_i1/S*}]
#
#The following constraints are used to constrain the output of the BUFGMUX.
#This constraint is set for 250MHz because when the PCIe core is operating in Gen2
#mode, the 250MHz clock is selected.  Without these constraints, it is possible that
#static timing analysis could anayze the design using the 125MHz clock instead of the
#250MHz clock.
#
#
create_generated_clock -name clk_125mhz_mux_X0Y0 \
                        -source [get_pins ftop/pfconfig_i/picoevb_i/worker/bridge_pcie_axi/axi_pcie_inst/inst/comp_axi_enhanced_pcie/comp_enhanced_core_top_wrap/axi_pcie_enhanced_core_top_i/pcie_7x_v2_0_2_inst/pcie_top_with_gt_top.gt_ges.gt_top_i/pipe_wrapper_i/pipe_clock_int.pipe_clock_i/pclk_i1_bufgctrl.pclk_i1/I0] \
                        -divide_by 1 \
                        [get_pins ftop/pfconfig_i/picoevb_i/worker/bridge_pcie_axi/axi_pcie_inst/inst/comp_axi_enhanced_pcie/comp_enhanced_core_top_wrap/axi_pcie_enhanced_core_top_i/pcie_7x_v2_0_2_inst/pcie_top_with_gt_top.gt_ges.gt_top_i/pipe_wrapper_i/pipe_clock_int.pipe_clock_i/pclk_i1_bufgctrl.pclk_i1/O]
#
create_generated_clock -name clk_250mhz_mux_X0Y0 \
                        -source \
                        [get_pins ftop/pfconfig_i/picoevb_i/worker/bridge_pcie_axi/axi_pcie_inst/inst/comp_axi_enhanced_pcie/comp_enhanced_core_top_wrap/axi_pcie_enhanced_core_top_i/pcie_7x_v2_0_2_inst/pcie_top_with_gt_top.gt_ges.gt_top_i/pipe_wrapper_i/pipe_clock_int.pipe_clock_i/pclk_i1_bufgctrl.pclk_i1/I1] \
                        -divide_by 1 -add \
                        -master_clock \
                        [get_clocks -of [get_pins ftop/pfconfig_i/picoevb_i/worker/bridge_pcie_axi/axi_pcie_inst/inst/comp_axi_enhanced_pcie/comp_enhanced_core_top_wrap/axi_pcie_enhanced_core_top_i/pcie_7x_v2_0_2_inst/pcie_top_with_gt_top.gt_ges.gt_top_i/pipe_wrapper_i/pipe_clock_int.pipe_clock_i/pclk_i1_bufgctrl.pclk_i1/I1]] \
                        [get_pins ftop/pfconfig_i/picoevb_i/worker/bridge_pcie_axi/axi_pcie_inst/inst/comp_axi_enhanced_pcie/comp_enhanced_core_top_wrap/axi_pcie_enhanced_core_top_i/pcie_7x_v2_0_2_inst/pcie_top_with_gt_top.gt_ges.gt_top_i/pipe_wrapper_i/pipe_clock_int.pipe_clock_i/pclk_i1_bufgctrl.pclk_i1/O]
#
set_clock_groups -name pcieclkmux -physically_exclusive -group clk_125mhz_mux_X0Y0 -group clk_250mhz_mux_X0Y0
#
create_generated_clock -name oobclk_125mhz_master_lane0_X0Y0 \
                       -source [get_pins {ftop/pfconfig_i/picoevb_i/worker/bridge_pcie_axi/axi_pcie_inst/inst/comp_axi_enhanced_pcie/comp_enhanced_core_top_wrap/axi_pcie_enhanced_core_top_i/pcie_7x_v2_0_2_inst/pcie_top_with_gt_top.gt_ges.gt_top_i/pipe_wrapper_i/pipe_lane[0].pipe_user_i/oobclk_div.oobclk_reg/C}] \
                       -divide_by 2 -add \
                       -master_clock clk_125mhz_mux_X0Y0 \
                       [get_pins {ftop/pfconfig_i/picoevb_i/worker/bridge_pcie_axi/axi_pcie_inst/inst/comp_axi_enhanced_pcie/comp_enhanced_core_top_wrap/axi_pcie_enhanced_core_top_i/pcie_7x_v2_0_2_inst/pcie_top_with_gt_top.gt_ges.gt_top_i/pipe_wrapper_i/pipe_lane[0].pipe_user_i/oobclk_div.oobclk_reg/Q}]
#
create_generated_clock -name oobclk_250mhz_master_lane0_X0Y0 \
                       -source [get_pins {ftop/pfconfig_i/picoevb_i/worker/bridge_pcie_axi/axi_pcie_inst/inst/comp_axi_enhanced_pcie/comp_enhanced_core_top_wrap/axi_pcie_enhanced_core_top_i/pcie_7x_v2_0_2_inst/pcie_top_with_gt_top.gt_ges.gt_top_i/pipe_wrapper_i/pipe_lane[0].pipe_user_i/oobclk_div.oobclk_reg/C}] \
                       -divide_by 4 -add \
                       -master_clock clk_250mhz_mux_X0Y0 \
                       [get_pins {ftop/pfconfig_i/picoevb_i/worker/bridge_pcie_axi/axi_pcie_inst/inst/comp_axi_enhanced_pcie/comp_enhanced_core_top_wrap/axi_pcie_enhanced_core_top_i/pcie_7x_v2_0_2_inst/pcie_top_with_gt_top.gt_ges.gt_top_i/pipe_wrapper_i/pipe_lane[0].pipe_user_i/oobclk_div.oobclk_reg/Q}]
#

#
# ##############################################################################
# Physical Constraints

#------------------------------------------------------------------------------
# Asynchronous Paths
#------------------------------------------------------------------------------

set_false_path -through [get_pins -filter {REF_PIN_NAME=~RXELECIDLE} -of_objects [get_cells -hierarchical -filter { PRIMITIVE_TYPE =~ IO.gt.* }]]
set_false_path -through [get_pins -filter {REF_PIN_NAME=~TXPHINITDONE} -of_objects [get_cells -hierarchical -filter { PRIMITIVE_TYPE =~ IO.gt.* }]]
set_false_path -through [get_pins -filter {REF_PIN_NAME=~TXPHALIGNDONE} -of_objects [get_cells -hierarchical -filter { PRIMITIVE_TYPE =~ IO.gt.* }]]
set_false_path -through [get_pins -filter {REF_PIN_NAME=~TXDLYSRESETDONE} -of_objects [get_cells -hierarchical -filter { PRIMITIVE_TYPE =~ IO.gt.* }]]
set_false_path -through [get_pins -filter {REF_PIN_NAME=~RXDLYSRESETDONE} -of_objects [get_cells -hierarchical -filter { PRIMITIVE_TYPE =~ IO.gt.* }]]
set_false_path -through [get_pins -filter {REF_PIN_NAME=~RXPHALIGNDONE} -of_objects [get_cells -hierarchical -filter { PRIMITIVE_TYPE =~ IO.gt.* }]]
set_false_path -through [get_pins -filter {REF_PIN_NAME=~RXCDRLOCK} -of_objects [get_cells -hierarchical -filter { PRIMITIVE_TYPE =~ IO.gt.* }]]
set_false_path -through [get_pins -filter {REF_PIN_NAME=~CFGMSGRECEIVEDPMETO} -of_objects [get_cells -hierarchical -filter { PRIMITIVE_TYPE =~ * }]]
set_false_path -through [get_pins -filter {REF_PIN_NAME=~PLL0LOCK} -of_objects [get_cells -hierarchical -filter { PRIMITIVE_TYPE =~ IO.gt.* }]]
set_false_path -through [get_pins -filter {REF_PIN_NAME=~RXPMARESETDONE} -of_objects [get_cells -hierarchical -filter { PRIMITIVE_TYPE =~ IO.gt.* }]]
set_false_path -through [get_pins -filter {REF_PIN_NAME=~RXSYNCDONE} -of_objects [get_cells -hierarchical -filter { PRIMITIVE_TYPE =~ IO.gt.* }]]
set_false_path -through [get_pins -filter {REF_PIN_NAME=~TXSYNCDONE} -of_objects [get_cells -hierarchical -filter { PRIMITIVE_TYPE =~ IO.gt.* }]]

# ##############################################################################
# End axi_pcie insertion
# ##############################################################################
# ##############################################################################
# ##############################################################################


# ##############################################################################
# Additional design / project settings
# ##############################################################################

# Power down on overtemp
set_property BITSTREAM.CONFIG.OVERTEMPPOWERDOWN ENABLE [current_design]

# High-speed configuration so FPGA is up in time to negotiate with PCIe root complex
set_property BITSTREAM.CONFIG.CONFIGRATE 66 [current_design]
set_property BITSTREAM.CONFIG.SPI_BUSWIDTH 4 [current_design]
set_property CONFIG_MODE SPIx4 [current_design]
set_property BITSTREAM.CONFIG.SPI_FALL_EDGE YES [current_design]
set_property BITSTREAM.GENERAL.COMPRESS TRUE [current_design]

set_property CONFIG_VOLTAGE 3.3 [current_design]
set_property CFGBVS VCCO [current_design]
