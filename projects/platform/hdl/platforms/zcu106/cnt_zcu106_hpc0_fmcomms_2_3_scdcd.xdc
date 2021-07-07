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

# Extracted from the zcu104 XDC file 
############################################################################
# Clock constraints                                                        #
############################################################################
# 10 ns period = 100000 KHz
create_clock -name clk_fpga_0 -period 10.000 [get_pins -hier * -filter {NAME =~ */ps/U0/PS8_i/PLCLK[0]}]

# ----------------------------------------------------------------------------
# Clock constraints - platform_ad9361_data_sub.hdl
# ----------------------------------------------------------------------------

# FMCOMMS2/3 AD9361 DATA_CLK_P
# create_clock command defaults to 50% duty cycle when -waveform is not specified
# from AD9361 datasheet
#set AD9361_LVDS_t_CP_ns 4.069
#create_clock -period $AD9361_LVDS_t_CP_ns -name FMC_LA00_CC_P [get_ports {FMC_LA00_CC_P}]

# max supported AD9361 DATA_CLK period of data_src_qadc_ad9361_sub.hdl on
# ZCU104/FMCOMMS2/3 for which slack will be 0
create_clock -period 5.712 -name FMC_HPC0_LA00_CC_P [get_ports {FMC_HPC0_LA00_CC_P}]

# FMCOMMS2/3 AD9361 FB_CLK_P (forwarded version of DATA_CLK_P)
create_generated_clock -name FMC_HPC0_LA08_P -source [get_pins {ftop/FMC_HPC0_platform_ad9361_data_sub_i/worker/mode7.data_clk_buf_i/O}] -divide_by 1 -invert [get_ports {FMC_HPC0_LA08_P}]

# Generate DAC one sample per clock constraints
# almost exactly the design methodology outlined in "Figure 3-70: Generated Clock in the Fanout Of
# Master Clock" in
# https://www.xilinx.com/support/documentation/sw_manuals/xilinx2017_1/ug949-vivado-design-methodology.pdf
create_generated_clock -name FMC_HPC0_LA08_P_DAC_CLK_DIV4 -divide_by 2 -source [get_pins {ftop/FMC_HPC0_data_sink_qdac_ad9361_sub_i/worker/data_mode_lvds.wsi_clk_gen/clock_manager/second_divider/divider_type_register.routability_global.divisor_2.reg_out_reg/C}] [get_pins {ftop/FMC_HPC0_data_sink_qdac_ad9361_sub_i/worker/data_mode_lvds.wsi_clk_gen/clock_manager/second_divider/divider_type_register.routability_global.divisor_2.reg_out_reg/Q}]

# following methodology in "Figure 3-77: Muxed Clocks" / "Case in which only the paths A or B or C exist" in https://www.xilinx.com/support/documentation/sw_manuals/xilinx2017_1/ug949-vivado-design-methodology.pdf
create_generated_clock -name dac_clkdiv2_mux -divide_by 1 -source [get_pins {ftop/FMC_HPC0_data_sink_qdac_ad9361_sub_i/worker/data_mode_lvds.wsi_clk_gen/clock_manager/first_divider/divider_type_buffer.routability_regional.buffer_and_divider/O}] [get_pins {ftop/FMC_HPC0_data_sink_qdac_ad9361_sub_i/worker/data_mode_lvds.wsi_clk_gen/clock_manager/clock_selector/bufgmux/O}]
create_generated_clock -name dac_clkdiv4_mux -divide_by 1 -add -master_clock FMC_HPC0_LA08_P_DAC_CLK_DIV4 -source [get_pins {ftop/FMC_HPC0_data_sink_qdac_ad9361_sub_i/worker/data_mode_lvds.wsi_clk_gen/clock_manager/second_divider/divider_type_register.routability_global.divisor_2.reg_out_reg/Q}] [get_pins {ftop/FMC_HPC0_data_sink_qdac_ad9361_sub_i/worker/data_mode_lvds.wsi_clk_gen/clock_manager/clock_selector/bufgmux/O}]
set_clock_groups -physically_exclusive -group dac_clkdiv2_mux -group dac_clkdiv4_mux

# Generate ADC one sample per clock constraints
# both of these create_generated_clock constraints, as well as their corresponding circuits, follow
# almost exactly the design methodology outlined in "Figure 3-70: Generated Clock in the Fanout Of
# Master Clock" in
# https://www.xilinx.com/support/documentation/sw_manuals/xilinx2017_1/ug949-vivado-design-methodology.pdf
create_generated_clock -name FMC_HPC0_LA08_P_ADC_CLK_DIV2 -divide_by 2 -source [get_pins {ftop/FMC_HPC0_data_src_qadc_ad9361_sub_i/worker/sample_clk_gen/clock_manager/first_divider/divider_type_register.routability_global.divisor_2.reg_out_reg/C}] [get_pins {ftop/FMC_HPC0_data_src_qadc_ad9361_sub_i/worker/sample_clk_gen/clock_manager/first_divider/divider_type_register.routability_global.divisor_2.reg_out_reg/Q}]
create_generated_clock -name FMC_HPC0_LA08_P_ADC_CLK_DIV4 -divide_by 2 -source [get_pins {ftop/FMC_HPC0_data_src_qadc_ad9361_sub_i/worker/sample_clk_gen/clock_manager/second_divider/divider_type_register.routability_global.divisor_2.reg_out_reg/C}] [get_pins {ftop/FMC_HPC0_data_src_qadc_ad9361_sub_i/worker/sample_clk_gen/clock_manager/second_divider/divider_type_register.routability_global.divisor_2.reg_out_reg/Q}]

# following methodology in "Figure 3-77: Muxed Clocks" / "Case in which only the paths A or B or C exist" in https://www.xilinx.com/support/documentation/sw_manuals/xilinx2017_1/ug949-vivado-design-methodology.pdf
create_generated_clock -name adc_clkdiv2_mux -divide_by 1 -source [get_pins {ftop/FMC_HPC0_data_src_qadc_ad9361_sub_i/worker/sample_clk_gen/clock_manager/first_divider/divider_type_register.routability_global.divisor_2.reg_out_reg/Q}] [get_pins {ftop/FMC_HPC0_data_src_qadc_ad9361_sub_i/worker/sample_clk_gen/clock_manager/clock_selector/bufgmux/O}]
create_generated_clock -name adc_clkdiv4_mux -divide_by 1 -add -master_clock FMC_HPC0_LA08_P_ADC_CLK_DIV4 -source [get_pins {ftop/FMC_HPC0_data_src_qadc_ad9361_sub_i/worker/sample_clk_gen/clock_manager/second_divider/divider_type_register.routability_global.divisor_2.reg_out_reg/Q}] [get_pins {ftop/FMC_HPC0_data_src_qadc_ad9361_sub_i/worker/sample_clk_gen/clock_manager/clock_selector/bufgmux/O}]
set_clock_groups -physically_exclusive -group adc_clkdiv2_mux -group adc_clkdiv4_mux

# ----------------------------------------------------------------------------
# FMC Expansion Connector 
# ---------------------------------------------------------------------------- 
set_property PACKAGE_PIN E14 [get_ports {FMC_HPC0_CLK0_M2C_N}];  # "FMC-CLK0_N"
set_property PACKAGE_PIN E15 [get_ports {FMC_HPC0_CLK0_M2C_P}];  # "FMC-CLK0_P"
set_property PACKAGE_PIN F16 [get_ports {FMC_HPC0_LA00_N_CC}];  # "FMC-LA00_CC_N"
set_property PACKAGE_PIN F17 [get_ports {FMC_HPC0_LA00_P_CC}];  # "FMC-LA00_CC_P"
set_property PACKAGE_PIN H17 [get_ports {FMC_HPC0_LA01_N_CC}];  # "FMC-LA01_CC_N"
set_property PACKAGE_PIN H18 [get_ports {FMC_HPC0_LA01_P_CC}];  # "FMC-LA01_CC_P" - corrected 6/6/16 GE
set_property PACKAGE_PIN K20 [get_ports {FMC_HPC0_LA02_N}];  # "FMC-LA02_N"
set_property PACKAGE_PIN L20 [get_ports {FMC_HPC0_LA02_P}];  # "FMC-LA02_P"
set_property PACKAGE_PIN K18 [get_ports {FMC_HPC0_LA03_N}];  # "FMC-LA03_N"
set_property PACKAGE_PIN K19 [get_ports {FMC_HPC0_LA03_P}];  # "FMC-LA03_P"
set_property PACKAGE_PIN L16 [get_ports {FMC_HPC0_LA04_N}];  # "FMC-LA04_N"
set_property PACKAGE_PIN L17 [get_ports {FMC_HPC0_LA04_P}];  # "FMC-LA04_P"
set_property PACKAGE_PIN J17 [get_ports {FMC_HPC0_LA05_N}];  # "FMC-LA05_N"
set_property PACKAGE_PIN K17 [get_ports {FMC_HPC0_LA05_P}];  # "FMC-LA05_P"
set_property PACKAGE_PIN G19 [get_ports {FMC_HPC0_LA06_N}];  # "FMC-LA06_N"
set_property PACKAGE_PIN H19 [get_ports {FMC_HPC0_LA06_P}];  # "FMC-LA06_P"
set_property PACKAGE_PIN J15 [get_ports {FMC_HPC0_LA07_N}];  # "FMC-LA07_N"
set_property PACKAGE_PIN J16 [get_ports {FMC_HPC0_LA07_P}];  # "FMC-LA07_P"
set_property PACKAGE_PIN E17 [get_ports {FMC_HPC0_LA08_N}];  # "FMC-LA08_N"
set_property PACKAGE_PIN E18 [get_ports {FMC_HPC0_LA08_P}];  # "FMC-LA08_P"
set_property PACKAGE_PIN G16 [get_ports {FMC_HPC0_LA09_N}];  # "FMC-LA09_N"
set_property PACKAGE_PIN H16 [get_ports {FMC_HPC0_LA09_P}];  # "FMC-LA09_P"
set_property PACKAGE_PIN K15 [get_ports {FMC_HPC0_LA10_N}];  # "FMC-LA10_N"
set_property PACKAGE_PIN L15 [get_ports {FMC_HPC0_LA10_P}];  # "FMC-LA10_P"
set_property PACKAGE_PIN A12 [get_ports {FMC_HPC0_LA11_N}];  # "FMC-LA11_N"
set_property PACKAGE_PIN A13 [get_ports {FMC_HPC0_LA11_P}];  # "FMC-LA11_P"
set_property PACKAGE_PIN F18 [get_ports {FMC_HPC0_LA12_N}];  # "FMC-LA12_N"
set_property PACKAGE_PIN G18 [get_ports {FMC_HPC0_LA12_P}];  # "FMC-LA12_P"
set_property PACKAGE_PIN F15 [get_ports {FMC_HPC0_LA13_N}];  # "FMC-LA13_N"
set_property PACKAGE_PIN G15 [get_ports {FMC_HPC0_LA13_P}];  # "FMC-LA13_P"
set_property PACKAGE_PIN C12 [get_ports {FMC_HPC0_LA14_N}];  # "FMC-LA14_N"
set_property PACKAGE_PIN C13 [get_ports {FMC_HPC0_LA14_P}];  # "FMC-LA14_P"
set_property PACKAGE_PIN C16 [get_ports {FMC_HPC0_LA15_N}];  # "FMC-LA15_N"
set_property PACKAGE_PIN D16 [get_ports {FMC_HPC0_LA15_P}];  # "FMC-LA15_P"
set_property PACKAGE_PIN C17 [get_ports {FMC_HPC0_LA16_N}];  # "FMC-LA16_N"
set_property PACKAGE_PIN D17 [get_ports {FMC_HPC0_LA16_P}];  # "FMC-LA16_P"
set_property PACKAGE_PIN F10 [get_ports {FMC_HPC0_CLK1_M2C_N}];  # "FMC-CLK1_N"
set_property PACKAGE_PIN G10 [get_ports {FMC_HPC0_CLK1_M2C_P}];  # "FMC-CLK1_P"
set_property PACKAGE_PIN E10 [get_ports {FMC_HPC0_LA17_CC_N}];  # "FMC-LA17_CC_N"
set_property PACKAGE_PIN F11 [get_ports {FMC_HPC0_LA17_CC_P}];  # "FMC-LA17_CC_P"
set_property PACKAGE_PIN D10 [get_ports {FMC_HPC0_LA18_CC_N}];  # "FMC-LA18_CC_N"
set_property PACKAGE_PIN D11 [get_ports {FMC_HPC0_LA18_CC_P}];  # "FMC-LA18_CC_P"
set_property PACKAGE_PIN C11 [get_ports {FMC_HPC0_LA19_N}];  # "FMC-LA19_N"
set_property PACKAGE_PIN D12 [get_ports {FMC_HPC0_LA19_P}];  # "FMC-LA19_P"
set_property PACKAGE_PIN E12 [get_ports {FMC_HPC0_LA20_N}];  # "FMC-LA20_N"
set_property PACKAGE_PIN F12 [get_ports {FMC_HPC0_LA20_P}];  # "FMC-LA20_P"
set_property PACKAGE_PIN A10 [get_ports {FMC_HPC0_LA21_N}];  # "FMC-LA21_N"
set_property PACKAGE_PIN B10 [get_ports {FMC_HPC0_LA21_P}];  # "FMC-LA21_P"
set_property PACKAGE_PIN H12 [get_ports {FMC_HPC0_LA22_N}];  # "FMC-LA22_N"
set_property PACKAGE_PIN H13 [get_ports {FMC_HPC0_LA22_P}];  # "FMC-LA22_P"
set_property PACKAGE_PIN A11 [get_ports {FMC_HPC0_LA23_N}];  # "FMC-LA23_N"
set_property PACKAGE_PIN B11 [get_ports {FMC_HPC0_LA23_P}];  # "FMC-LA23_P"
set_property PACKAGE_PIN A6  [get_ports {FMC_HPC0_LA24_N}];  # "FMC-LA24_N"
set_property PACKAGE_PIN B6  [get_ports {FMC_HPC0_LA24_P}];  # "FMC-LA24_P"
set_property PACKAGE_PIN C6  [get_ports {FMC_HPC0_LA25_N}];  # "FMC-LA25_N"
set_property PACKAGE_PIN C7  [get_ports {FMC_HPC0_LA25_P}];  # "FMC-LA25_P"
set_property PACKAGE_PIN B8  [get_ports {FMC_HPC0_LA26_N}];  # "FMC-LA26_N"
set_property PACKAGE_PIN B9  [get_ports {FMC_HPC0_LA26_P}];  # "FMC-LA26_P"
set_property PACKAGE_PIN A7  [get_ports {FMC_HPC0_LA27_N}];  # "FMC-LA27_N"
set_property PACKAGE_PIN A8  [get_ports {FMC_HPC0_LA27_P}];  # "FMC-LA27_P"
set_property PACKAGE_PIN L13 [get_ports {FMC_HPC0_LA28_N}];  # "FMC-LA28_N"
set_property PACKAGE_PIN M13 [get_ports {FMC_HPC0_LA28_P}];  # "FMC-LA28_P"
set_property PACKAGE_PIN J10 [get_ports {FMC_HPC0_LA29_N}];  # "FMC-LA29_N"
set_property PACKAGE_PIN K10 [get_ports {FMC_HPC0_LA29_P}];  # "FMC-LA29_P"
set_property PACKAGE_PIN D9  [get_ports {FMC_HPC0_LA30_N}];  # "FMC-LA30_N"
set_property PACKAGE_PIN E9  [get_ports {FMC_HPC0_LA30_P}];  # "FMC-LA30_P"
set_property PACKAGE_PIN E7  [get_ports {FMC_HPC0_LA31_N}];  # "FMC-LA31_N"
set_property PACKAGE_PIN F7  [get_ports {FMC_HPC0_LA31_P}];  # "FMC-LA31_P"
set_property PACKAGE_PIN E8  [get_ports {FMC_HPC0_LA32_N}];  # "FMC-LA32_N"
set_property PACKAGE_PIN F8  [get_ports {FMC_HPC0_LA32_P}];  # "FMC-LA32_P"
set_property PACKAGE_PIN C8  [get_ports {FMC_HPC0_LA33_N}];  # "FMC-LA33_N"
set_property PACKAGE_PIN C9  [get_ports {FMC_HPC0_LA33_P}];  # "FMC-LA33_P"

#create_pblock pblock_zcu104_i; add_cells_to_pblock [get_pblocks pblock_zcu104_i] [get_cells [list {ftop/pfconfig_i/zcu104_i}]]
#resize_pblock [get_pblocks pblock_zcu104_i] -add {SLICE_X26Y88:SLICE_X49Y110}

# ----------------------------------------------------------------------------
# IOSTANDARD Constraints
#
# Note that these IOSTANDARD constraints are applied to all IOs currently
# assigned within an I/O bank.  If these IOSTANDARD constraints are 
# evaluated prior to other PACKAGE_PIN constraints being applied, then 
# the IOSTANDARD specified will likely not be applied properly to those 
# pins.  Therefore, bank wide IOSTANDARD constraints should be placed 
# within the XDC file in a location that is evaluated AFTER all 
# PACKAGE_PIN constraints within the target bank have been evaluated.
#
# Un-comment one or more of the following IOSTANDARD constraints according to
# the bank pin assignments that are required within a design.
# ----------------------------------------------------------------------------

# Note that the bank voltage for IO Bank 67 and 68 are set to 1.8V on ZCU104. 
set_property IOSTANDARD LVCMOS18 [get_ports -of_objects [get_iobanks 67]];
set_property IOSTANDARD LVCMOS18 [get_ports -of_objects [get_iobanks 68]];

# whenever we instantiate any of the ad9361 workers for FMCOMMS2/3, we really
# should set the IOSTANDARD for all of the FMCOMMS2/3 pins for the given slot

# note that the fmcomms_2_3_lpc card definition forces LVDS mode, so we do the
# same here since this constraints file is fmcomms_2_3_lpc card-specific

# ----------------------------------------------------------------------------
# IOSTANDARD constraints - platform_ad9361_config.hdl
# ----------------------------------------------------------------------------

set_property IOSTANDARD LVCMOS18 [get_ports {FMC_HPC0_LA16_N}]; # FMCOMMS2/3 AD9361 TXNRX
set_property IOSTANDARD LVCMOS18 [get_ports {FMC_HPC0_LA16_P}]; # FMCOMMS2/3 AD9361 ENABLE

# ----------------------------------------------------------------------------
# IOSTANDARD constraints - platform_ad9361_data_sub.hdl
# ----------------------------------------------------------------------------
set_property IOSTANDARD LVDS [get_ports {FMC_HPC0_LA00_P_CC}]; # FMCOMMS3 DATA_CLK_P
set_property DIFF_TERM_ADV TERM_100 [get_ports {FMC_HPC0_LA00_P_CC}];
set_property IOSTANDARD LVDS [get_ports {FMC_HPC0_LA01_P_CC}]; # FMCOMMS3 RX_FRAME_P
set_property DIFF_TERM_ADV TERM_100 [get_ports {FMC_HPC0_LA01_P_CC}];
set_property IOSTANDARD LVDS [get_ports {FMC_HPC0_LA02_P}]; # FMCOMMS3 RX_D0
set_property DIFF_TERM_ADV TERM_100 [get_ports {FMC_HPC0_LA02_P}];
set_property IOSTANDARD LVDS [get_ports {FMC_HPC0_LA03_P}]; # FMCOMMS3 RX_D1
set_property DIFF_TERM_ADV TERM_100 [get_ports {FMC_HPC0_LA03_P}];
set_property IOSTANDARD LVDS [get_ports {FMC_HPC0_LA04_P}]; # FMCOMMS3 RX_D2
set_property DIFF_TERM_ADV TERM_100 [get_ports {FMC_HPC0_LA04_P}];
set_property IOSTANDARD LVDS [get_ports {FMC_HPC0_LA05_P}]; # FMCOMMS3 RX_D3
set_property DIFF_TERM_ADV TERM_100 [get_ports {FMC_HPC0_LA05_P}];
set_property IOSTANDARD LVDS [get_ports {FMC_HPC0_LA06_P}]; # FMCOMMS3 RX_D4
set_property DIFF_TERM_ADV TERM_100 [get_ports {FMC_HPC0_LA06_P}];
set_property IOSTANDARD LVDS [get_ports {FMC_HPC0_LA07_P}]; # FMCOMMS3 RX_D5
set_property DIFF_TERM_ADV TERM_100 [get_ports {FMC_HPC0_LA07_P}];
set_property IOSTANDARD LVDS [get_ports {FMC_HPC0_LA08_P}]; # FMCOMMS3 TX_FB_CLK_P
set_property IOSTANDARD LVDS [get_ports {FMC_HPC0_LA09_P}]; # FMCOMMS3 TX_FRAME_P
set_property IOSTANDARD LVDS [get_ports {FMC_HPC0_LA11_P}]; # FMCOMMS3 TX_D0
set_property IOSTANDARD LVDS [get_ports {FMC_HPC0_LA12_P}]; # FMCOMMS3 TX_D1
set_property IOSTANDARD LVDS [get_ports {FMC_HPC0_LA13_P}]; # FMCOMMS3 TX_D2
set_property IOSTANDARD LVDS [get_ports {FMC_HPC0_LA10_P}]; # FMCOMMS3 TX_D3
set_property IOSTANDARD LVDS [get_ports {FMC_HPC0_LA14_P}]; # FMCOMMS3 TX_D4
set_property IOSTANDARD LVDS [get_ports {FMC_HPC0_LA15_P}]; # FMCOMMS3 TX_D5

# ----------------------------------------------------------------------------
# INPUT / OUTPUT DELAY constraints - data_src_qadc_ad9361_sub.hdl
# ----------------------------------------------------------------------------

# FMCOMMS3 RX_D/RX_FRAME_P
#
# ----- from Vivado GUI:
#                             _____________
# input clock              __|             |_____________
#                   _____    :      ___    :      _______
# data              _____XXXX:XXXXXX___XXXX:XXXXXX_______
#                        :<--:---->:   :<--:-----:
#                    skew_bre skew_are skew_bfe skew_afe
#
# skew_bre : Data invalid before rising edge  (I think this really means max
#                                              amount of time that
#                                              start-of-valid for "rising" data
#                                              precedes rising edge by)
# skew_are : Data invalid after rising edge   (I think this really means max
#                                              amount of time that
#                                              start-of-valid for "rising" data
#                                              follows rising edge by)
# skew_bfe : Data invalid before falling edge (I think this really means max
#                                              amount of time that
#                                              start-of-valid for "falling" data
#                                              precedes falling edge by)
# skew_afe : Data invalid after falling edge  (I think this really means max
#                                              amount of time that
#                                              start-of-valid for "falling" data
#                                              follows falling edge by)
#
# Rise Max = (period/2) + skew_afe (I don't know if GUI is wrong, this might
#                                   need to be period/2 + skew_are)
# Rise Min = (period/2) - skew_bfe (I don't know if GUI is wrong, this might
#                                   need to be period/2 - skew_are)
# Fall Max = (period/2) + skew_are (I don't know if GUI is wrong, this might
#                                   need to be period/2 + skew_afe)
# Fall Min = (period/2) - skew_bre (I don't know if GUI is wrong, this might
#                                   need to be period/2 - skew_afe)
#
# ----- from AD9361 datasheet:
# t_DDRx_min = 0.25
# t_DDRx_max = 1.25
#
# ----- assumed platform_ad9361_data_sub.hdl parameter property/no-OS init_param settings
# ----- (values chosen specifically to meet static timing):
# ------------------------------------------------------------------------------
# |                     | no-OS init_param member | value | delay(ns)          |
# | parameter property  |                         |       |                    |
# ------------------------------------------------------------------------------
# | DATA_CLK_Delay      | rx_data_clock_delay     | 4     | 1.2                |
# | Rx_Data_Delay       | rx_data_delay           | 0     | 0.0                |
# ------------------------------------------------------------------------------
#
# ----- calculations
# skew_bre = -t_DDRx_min + (DATA_CLK_Delay-Rx_Data_Delay)*0.3 = 0.95
# skew_are =  t_DDRx_max - (DATA_CLK_Delay-Rx_Data_Delay)*0.3 = 0.05
# skew_bfe = -t_DDRx_min + (DATA_CLK_Delay-Rx_Data_Delay)*0.3 = 0.95
# skew_afe =  t_DDRx_max - (DATA_CLK_Delay-Rx_Data_Delay)*0.3 = 0.05
# Rise Max = (period/2) + skew_afe = (5.712/2) + 0.05 = 2.906
# Rise Min = (period/2) - skew_bfe = (5.712/2) - 0.95 = 1.906
# Fall Max = (period/2) + skew_are = (5.712/2) + 0.05 = 2.906
# Fall Min = (period/2) - skew_bre = (5.712/2) - 0.95 = 1.906
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -min -add_delay 1.906 [get_ports {FMC_HPC0_LA02_P}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -max -add_delay 2.906 [get_ports {FMC_HPC0_LA02_P}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -min -add_delay 1.906 [get_ports {FMC_HPC0_LA02_N}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -max -add_delay 2.906 [get_ports {FMC_HPC0_LA02_N}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -clock_fall -min -add_delay 1.906 [get_ports {FMC_HPC0_LA02_P}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -clock_fall -max -add_delay 2.906 [get_ports {FMC_HPC0_LA02_P}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -clock_fall -min -add_delay 1.906 [get_ports {FMC_HPC0_LA02_N}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -clock_fall -max -add_delay 2.906 [get_ports {FMC_HPC0_LA02_N}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -min -add_delay 1.906 [get_ports {FMC_HPC0_LA03_P}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -max -add_delay 2.906 [get_ports {FMC_HPC0_LA03_P}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -min -add_delay 1.906 [get_ports {FMC_HPC0_LA03_N}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -max -add_delay 2.906 [get_ports {FMC_HPC0_LA03_N}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -clock_fall -min -add_delay 1.906 [get_ports {FMC_HPC0_LA03_P}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -clock_fall -max -add_delay 2.906 [get_ports {FMC_HPC0_LA03_P}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -clock_fall -min -add_delay 1.906 [get_ports {FMC_HPC0_LA03_N}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -clock_fall -max -add_delay 2.906 [get_ports {FMC_HPC0_LA03_N}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -min -add_delay 1.906 [get_ports {FMC_HPC0_LA04_P}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -max -add_delay 2.906 [get_ports {FMC_HPC0_LA04_P}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -min -add_delay 1.906 [get_ports {FMC_HPC0_LA04_N}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -max -add_delay 2.906 [get_ports {FMC_HPC0_LA04_N}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -clock_fall -min -add_delay 1.906 [get_ports {FMC_HPC0_LA04_P}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -clock_fall -max -add_delay 2.906 [get_ports {FMC_HPC0_LA04_P}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -clock_fall -min -add_delay 1.906 [get_ports {FMC_HPC0_LA04_N}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -clock_fall -max -add_delay 2.906 [get_ports {FMC_HPC0_LA04_N}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -min -add_delay 1.906 [get_ports {FMC_HPC0_LA05_P}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -max -add_delay 2.906 [get_ports {FMC_HPC0_LA05_P}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -min -add_delay 1.906 [get_ports {FMC_HPC0_LA05_N}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -max -add_delay 2.906 [get_ports {FMC_HPC0_LA05_N}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -clock_fall -min -add_delay 1.906 [get_ports {FMC_HPC0_LA05_P}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -clock_fall -max -add_delay 2.906 [get_ports {FMC_HPC0_LA05_P}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -clock_fall -min -add_delay 1.906 [get_ports {FMC_HPC0_LA05_N}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -clock_fall -max -add_delay 2.906 [get_ports {FMC_HPC0_LA05_N}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -min -add_delay 1.906 [get_ports {FMC_HPC0_LA06_P}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -max -add_delay 2.906 [get_ports {FMC_HPC0_LA06_P}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -min -add_delay 1.906 [get_ports {FMC_HPC0_LA06_N}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -max -add_delay 2.906 [get_ports {FMC_HPC0_LA06_N}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -clock_fall -min -add_delay 1.906 [get_ports {FMC_HPC0_LA06_P}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -clock_fall -max -add_delay 2.906 [get_ports {FMC_HPC0_LA06_P}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -clock_fall -min -add_delay 1.906 [get_ports {FMC_HPC0_LA06_N}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -clock_fall -max -add_delay 2.906 [get_ports {FMC_HPC0_LA06_N}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -min -add_delay 1.906 [get_ports {FMC_HPC0_LA07_P}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -max -add_delay 2.906 [get_ports {FMC_HPC0_LA07_P}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -min -add_delay 1.906 [get_ports {FMC_HPC0_LA07_N}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -max -add_delay 2.906 [get_ports {FMC_HPC0_LA07_N}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -clock_fall -min -add_delay 1.906 [get_ports {FMC_HPC0_LA07_P}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -clock_fall -max -add_delay 2.906 [get_ports {FMC_HPC0_LA07_P}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -clock_fall -min -add_delay 1.906 [get_ports {FMC_HPC0_LA07_N}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -clock_fall -max -add_delay 2.906 [get_ports {FMC_HPC0_LA07_N}]
# RX_FRAME_P is sampled on the DATA_CLK_P falling edge (we use DDR primitive as a sample-in-the-middle)
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -clock_fall -min -add_delay 1.906 [get_ports {FMC_HPC0_LA01_CC_P}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -clock_fall -max -add_delay 2.906 [get_ports {FMC_HPC0_LA01_CC_P}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -clock_fall -min -add_delay 1.906 [get_ports {FMC_HPC0_LA01_CC_N}]
set_input_delay -clock [get_clocks {FMC_HPC0_LA00_CC_P}] -clock_fall -max -add_delay 2.906 [get_ports {FMC_HPC0_LA01_CC_N}]


# ----------------------------------------------------------------------------
# INPUT / OUTPUT DELAY constraints - data_sink_qdac_ad9361_sub.hdl
# ----------------------------------------------------------------------------

# FMCOMMS3 TX_D/TX_FRAME_P
#
# ----- from Vivado GUI:
#                                 _____________
# forwarded clock              __|             |_____________
#                       __    ___:_____     ___:_____    ____
# data at destination   __XXXX___:_____XXXXX___:_____XXXX____
#                            :<--:---->:   :<--:-----:
#                           tsu_r  thd_r  tsu_f  thd_f
#
# tsu_r : Destination device setup time requirement for rising edge
# thd_r : Destination device hold time requirement for rising edge
# tsu_f : Destination device setup time requirement for falling edge
# thd_f : Destination device hold time requirement for falling edge
# trce_dly_max : Maximum board trace delay
# trce_dly_min : Minimum board trace delay
#
# Rise Max = trce_dly_max + tsu_r
# Rise Min = trce_dly_min - thd_r
#
# ----- from AD9361 datasheet:
# t_STx_min = 1
# t_HTx_min = 0
#
# ----- assumed platform_ad9361_data_sub.hdl parameter property/no-OS init_param settings
# ----- (values chosen specifically to meet static timing):
# ------------------------------------------------------------------------------
# |                     | no-OS init_param member | value | delay(ns)          |
# | parameter property  |                         |       |                    |
# ------------------------------------------------------------------------------
# | FB_CLK_Delay        | tx_fb_clock_delay       | 7     | 2.1                |
# | TX_Data_Delay       | tx_data_delay           | 0     | 0.0                |
# ------------------------------------------------------------------------------
#
# ----- calculations
# tsu_r = t_STx_min + (FB_CLK_Delay-TX_Data_Delay)*0.3 =  3.1 (AD9361 datasheet only specifies falling edge requirement, but rising is implied since DDR is used)
# thd_r = t_HTx_min - (FB_CLK_Delay-TX_Data_Delay)*0.3 = -2.1 (AD9361 datasheet only specifies falling edge requirement, but rising is implied since DDR is used)
# tsu_f = t_STx_min + (FB_CLK_Delay-TX_Data_Delay)*0.3 =  3.1
# thd_f = t_HTx_min - (FB_CLK_Delay-TX_Data_Delay)*0.3 = -2.1
# trce_dly_max is unknown, so value of 0 is used for calculation
# trce_dly_min is unknown, so value of 0 is used for calculation
# Rise Max = trce_dly_max + tsu_r = 0 + 3.1    = 3.1
# Rise Min = trce_dly_min - thd_r = 0 - (-2.1) = 2.1
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -clock_fall -min -add_delay 2.1 [get_ports {FMC_HPC0_LA10_P}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -clock_fall -max -add_delay 3.1 [get_ports {FMC_HPC0_LA10_P}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -clock_fall -min -add_delay 2.1 [get_ports {FMC_HPC0_LA10_N}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -clock_fall -max -add_delay 3.1 [get_ports {FMC_HPC0_LA10_N}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -min -add_delay 2.1 [get_ports {FMC_HPC0_LA10_P}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -max -add_delay 3.1 [get_ports {FMC_HPC0_LA10_P}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -min -add_delay 2.1 [get_ports {FMC_HPC0_LA10_N}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -max -add_delay 3.1 [get_ports {FMC_HPC0_LA10_N}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -clock_fall -min -add_delay 2.1 [get_ports {FMC_HPC0_LA11_P}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -clock_fall -max -add_delay 3.1 [get_ports {FMC_HPC0_LA11_P}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -clock_fall -min -add_delay 2.1 [get_ports {FMC_HPC0_LA11_N}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -clock_fall -max -add_delay 3.1 [get_ports {FMC_HPC0_LA11_N}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -min -add_delay 2.1 [get_ports {FMC_HPC0_LA11_P}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -max -add_delay 3.1 [get_ports {FMC_HPC0_LA11_P}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -min -add_delay 2.1 [get_ports {FMC_HPC0_LA11_N}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -max -add_delay 3.1 [get_ports {FMC_HPC0_LA11_N}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -clock_fall -min -add_delay 2.1 [get_ports {FMC_HPC0_LA12_P}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -clock_fall -max -add_delay 3.1 [get_ports {FMC_HPC0_LA12_P}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -clock_fall -min -add_delay 2.1 [get_ports {FMC_HPC0_LA12_N}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -clock_fall -max -add_delay 3.1 [get_ports {FMC_HPC0_LA12_N}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -min -add_delay 2.1 [get_ports {FMC_HPC0_LA12_P}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -max -add_delay 3.1 [get_ports {FMC_HPC0_LA12_P}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -min -add_delay 2.1 [get_ports {FMC_HPC0_LA12_N}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -max -add_delay 3.1 [get_ports {FMC_HPC0_LA12_N}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -clock_fall -min -add_delay 2.1 [get_ports {FMC_HPC0_LA13_P}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -clock_fall -max -add_delay 3.1 [get_ports {FMC_HPC0_LA13_P}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -clock_fall -min -add_delay 2.1 [get_ports {FMC_HPC0_LA13_N}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -clock_fall -max -add_delay 3.1 [get_ports {FMC_HPC0_LA13_N}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -min -add_delay 2.1 [get_ports {FMC_HPC0_LA13_P}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -max -add_delay 3.1 [get_ports {FMC_HPC0_LA13_P}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -min -add_delay 2.1 [get_ports {FMC_HPC0_LA13_N}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -max -add_delay 3.1 [get_ports {FMC_HPC0_LA13_N}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -clock_fall -min -add_delay 2.1 [get_ports {FMC_HPC0_LA14_P}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -clock_fall -max -add_delay 3.1 [get_ports {FMC_HPC0_LA14_P}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -clock_fall -min -add_delay 2.1 [get_ports {FMC_HPC0_LA14_N}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -clock_fall -max -add_delay 3.1 [get_ports {FMC_HPC0_LA14_N}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -min -add_delay 2.1 [get_ports {FMC_HPC0_LA14_P}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -max -add_delay 3.1 [get_ports {FMC_HPC0_LA14_P}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -min -add_delay 2.1 [get_ports {FMC_HPC0_LA14_N}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -max -add_delay 3.1 [get_ports {FMC_HPC0_LA14_N}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -clock_fall -min -add_delay 2.1 [get_ports {FMC_HPC0_LA15_P}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -clock_fall -max -add_delay 3.1 [get_ports {FMC_HPC0_LA15_P}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -clock_fall -min -add_delay 2.1 [get_ports {FMC_HPC0_LA15_N}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -clock_fall -max -add_delay 3.1 [get_ports {FMC_HPC0_LA15_N}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -min -add_delay 2.1 [get_ports {FMC_HPC0_LA15_P}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -max -add_delay 3.1 [get_ports {FMC_HPC0_LA15_P}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -min -add_delay 2.1 [get_ports {FMC_HPC0_LA15_N}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -max -add_delay 3.1 [get_ports {FMC_HPC0_LA15_N}]
# TX_FRAME_P
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -clock_fall -min -add_delay 2.1 [get_ports {FMC_HPC0_LA09_P}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -clock_fall -max -add_delay 3.1 [get_ports {FMC_HPC0_LA09_P}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -clock_fall -min -add_delay 2.1 [get_ports {FMC_HPC0_LA09_N}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -clock_fall -max -add_delay 3.1 [get_ports {FMC_HPC0_LA09_N}]

# ----------------------------------------------------------------------------
# INPUT / OUTPUT DELAY constraints - platform_ad9361_data_sub.hdl
# ----------------------------------------------------------------------------

# from AD9361 datasheet
set AD9361_ENABLE_t_SC_min 1.0;
set AD9361_ENABLE_t_HC_min 0.0;

set AD9361_ENABLE_tsu_r $AD9361_ENABLE_t_SC_min;
set AD9361_ENABLE_thd_r $AD9361_ENABLE_t_HC_min;

# assume 0 for now, can measure later if necessary
set AD9361_ENABLE_trce_dly_max 0;
set AD9361_ENABLE_trce_dly_min 0;

# see Vivado constraints wizard for these formulas
set AD9361_ENABLE_Rise_Max [expr $AD9361_ENABLE_trce_dly_max + $AD9361_ENABLE_tsu_r];
set AD9361_ENABLE_Rise_Min [expr $AD9361_ENABLE_trce_dly_min - $AD9361_ENABLE_thd_r];

set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -min -add_delay $AD9361_ENABLE_Rise_Min [get_ports {FMC_HPC0_LA16_N}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -max -add_delay $AD9361_ENABLE_Rise_Max [get_ports {FMC_HPC0_LA16_N}]

# from AD9361 datasheet
set AD9361_TXNRX_t_SC_min 1.0;
set AD9361_TXNRX_t_HC_min 0.0;

set AD9361_TXNRX_tsu_r $AD9361_TXNRX_t_SC_min;
set AD9361_TXNRX_thd_r $AD9361_TXNRX_t_HC_min;

# assume 0 for now, can measure later if necessary
set AD9361_TXNRX_trce_dly_max 0;
set AD9361_TXNRX_trce_dly_min 0;

# see Vivado constraints wizard for these formulas
set AD9361_TXNRX_Rise_Max [expr $AD9361_TXNRX_trce_dly_max + $AD9361_TXNRX_tsu_r];
set AD9361_TXNRX_Rise_Min [expr $AD9361_TXNRX_trce_dly_min - $AD9361_TXNRX_thd_r];

set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -min -add_delay $AD9361_TXNRX_Rise_Min [get_ports {FMC_HPC0_LA16_P}]
set_output_delay -clock [get_clocks {FMC_HPC0_LA08_P}] -max -add_delay $AD9361_TXNRX_Rise_Max [get_ports {FMC_HPC0_LA16_P}]

# ----------------------------------------------------------------------------
# CLOCK DOMAIN CROSSING / FALSE PATH constraints - platform_ad9361_data_sub.hdl
# ----------------------------------------------------------------------------

# disable timing check among paths between AD9361 DATA_CLK_P and control plane clock domains (which are asynchronous)
set_clock_groups -asynchronous -group [get_clocks {FMC_HPC0_LA00_CC_P}] -group [get_clocks {clk_fpga_0}]

# ----------------------------------------------------------------------------
# CLOCK DOMAIN CROSSING / FALSE PATH constraints - data_src_qadc_ad9361_sub.hdl
# ----------------------------------------------------------------------------

# because RX_FRAME_P is sampled on the DATA_CLK_P falling edge (we use DDR primitive as a sample-in-the-middle), the rising edge latched output is unconnected and therefore should not be used in timing analysis
set_false_path -from [get_ports FMC_HPC0_LA01_CC_P] -rise_to [get_pins ftop/FMC_HPC0_data_src_qadc_ad9361_sub_i/worker/supported_so_far.rx_frame_p_ddr/D]
set_clock_groups -asynchronous -group [get_clocks clk_fpga_0] -group [get_clocks adc_clkdiv2_mux]
set_clock_groups -asynchronous -group [get_clocks clk_fpga_0] -group [get_clocks adc_clkdiv4_mux]
set_clock_groups -asynchronous -group [get_clocks clk_fpga_0] -group [get_clocks adc_clkdiv4_mux]
set_clock_groups -asynchronous -group [get_clocks clk_fpga_0] -group [get_clocks FMC_HPC0_LA08_P_ADC_CLK_DIV4]
set_clock_groups -asynchronous -group [get_clocks clk_fpga_0] -group [get_clocks FMC_HPC0_LA08_P_ADC_CLK_DIV2]

# ----------------------------------------------------------------------------
# CLOCK DOMAIN CROSSING / FALSE PATH constraints - data_sink_qdac_ad9361_sub.hdl
# ----------------------------------------------------------------------------
set_clock_groups -asynchronous -group [get_clocks clk_fpga_0] -group [get_clocks -of_objects [get_pins ftop/FMC_HPC0_data_sink_qdac_ad9361_sub_i/worker/data_mode_lvds.wsi_clk_gen/clock_manager/first_divider/divider_type_buffer.routability_regional.buffer_and_divider/O]]
set_clock_groups -asynchronous -group [get_clocks clk_fpga_0] -group [get_clocks FMC_HPC0_LA08_P_DAC_CLK_DIV4]
set_clock_groups -asynchronous -group [get_clocks FMC_HPC0_LA00_CC_P] -group [get_clocks FMC_HPC0_LA08_P]
set_clock_groups -asynchronous -group [get_clocks dac_clkdiv2_mux] -group [get_clocks clk_fpga_0]
set_clock_groups -asynchronous -group [get_clocks clk_fpga_0] -group [get_clocks dacd2_clk]
set_clock_groups -asynchronous -group [get_clocks dac_clkdiv4_mux] -group [get_clocks clk_fpga_0]
set_false_path -from [get_clocks dac_clkdiv2_mux] -to [get_clocks FMC_HPC0_LA00_CC_P]
set_false_path -from [get_clocks FMC_HPC0_LA00_CC_P] -to [get_clocks dacd2_clk]
set_false_path -from [get_clocks dacd2_clk] -to [get_clocks FMC_HPC0_LA08_P]
set_false_path -from [get_clocks FMC_HPC0_LA08_P] -to [get_clocks dacd2_clk] 
set_false_path -from [get_clocks clk_fpga_0] -to [get_clocks FMC_HPC0_LA08_P]


# ----------------------------------------------------------------------------
# ZCU104 GPIO
# ----------------------------------------------------------------------------
set_property PACKAGE_PIN D5       [get_ports "GPIO_LED_0_LS"] ;# Bank  88 VCCO - VCC3V3   - IO_L11N_AD9N_88
set_property IOSTANDARD  LVCMOS33 [get_ports "GPIO_LED_0_LS"] ;# Bank  88 VCCO - VCC3V3   - IO_L11N_AD9N_88
set_property PACKAGE_PIN D6       [get_ports "GPIO_LED_1_LS"] ;# Bank  88 VCCO - VCC3V3   - IO_L11P_AD9P_88
set_property IOSTANDARD  LVCMOS33 [get_ports "GPIO_LED_1_LS"] ;# Bank  88 VCCO - VCC3V3   - IO_L11P_AD9P_88
set_property PACKAGE_PIN A5       [get_ports "GPIO_LED_2_LS"] ;# Bank  88 VCCO - VCC3V3   - IO_L10N_AD10N_88
set_property IOSTANDARD  LVCMOS33 [get_ports "GPIO_LED_2_LS"] ;# Bank  88 VCCO - VCC3V3   - IO_L10N_AD10N_88
set_property PACKAGE_PIN B5       [get_ports "GPIO_LED_3_LS"] ;# Bank  88 VCCO - VCC3V3   - IO_L10P_AD10P_88
set_property IOSTANDARD  LVCMOS33 [get_ports "GPIO_LED_3_LS"] ;# Bank  88 VCCO - VCC3V3   - IO_L10P_AD10P_88
set_property PACKAGE_PIN F4       [get_ports "GPIO_DIP_SW3"] ;# Bank  88 VCCO - VCC3V3   - IO_L9N_AD11N_88
set_property IOSTANDARD  LVCMOS33 [get_ports "GPIO_DIP_SW3"] ;# Bank  88 VCCO - VCC3V3   - IO_L9N_AD11N_88
set_property PACKAGE_PIN F5       [get_ports "GPIO_DIP_SW2"] ;# Bank  88 VCCO - VCC3V3   - IO_L9P_AD11P_88
set_property IOSTANDARD  LVCMOS33 [get_ports "GPIO_DIP_SW2"] ;# Bank  88 VCCO - VCC3V3   - IO_L9P_AD11P_88
set_property PACKAGE_PIN D4       [get_ports "GPIO_DIP_SW1"] ;# Bank  88 VCCO - VCC3V3   - IO_L8N_HDGC_88
set_property IOSTANDARD  LVCMOS33 [get_ports "GPIO_DIP_SW1"] ;# Bank  88 VCCO - VCC3V3   - IO_L8N_HDGC_88
set_property PACKAGE_PIN E4       [get_ports "GPIO_DIP_SW0"] ;# Bank  88 VCCO - VCC3V3   - IO_L8P_HDGC_88
set_property IOSTANDARD  LVCMOS33 [get_ports "GPIO_DIP_SW0"] ;# Bank  88 VCCO - VCC3V3   - IO_L8P_HDGC_88
set_property PACKAGE_PIN B4       [get_ports "GPIO_PB_SW0"] ;# Bank  88 VCCO - VCC3V3   - IO_L7N_HDGC_88
set_property IOSTANDARD  LVCMOS33 [get_ports "GPIO_PB_SW0"] ;# Bank  88 VCCO - VCC3V3   - IO_L7N_HDGC_88
set_property PACKAGE_PIN C4       [get_ports "GPIO_PB_SW1"] ;# Bank  88 VCCO - VCC3V3   - IO_L7P_HDGC_88
set_property IOSTANDARD  LVCMOS33 [get_ports "GPIO_PB_SW1"] ;# Bank  88 VCCO - VCC3V3   - IO_L7P_HDGC_88
set_property PACKAGE_PIN B3       [get_ports "GPIO_PB_SW2"] ;# Bank  88 VCCO - VCC3V3   - IO_L6N_HDGC_88
set_property IOSTANDARD  LVCMOS33 [get_ports "GPIO_PB_SW2"] ;# Bank  88 VCCO - VCC3V3   - IO_L6N_HDGC_88
set_property PACKAGE_PIN C3       [get_ports "GPIO_PB_SW3"] ;# Bank  88 VCCO - VCC3V3   - IO_L6P_HDGC_88
set_property IOSTANDARD  LVCMOS33 [get_ports "GPIO_PB_SW3"] ;# Bank  88 VCCO - VCC3V3   - IO_L6P_HDGC_88
