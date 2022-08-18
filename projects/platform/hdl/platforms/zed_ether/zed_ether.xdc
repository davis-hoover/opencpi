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
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

############################################################################
# Clock constraints                                                        #
############################################################################
# 125MHz LVDS oscillator (on FMC card) - Bank 34
# NOTE: this is connected to a High-Range I/O bank, which supports LVDS_25 (not
# LVDS). We require DIFF_TERM to terminate the LVDS pair internally since there
# is no external termination resistor. Therefore we must use a VADJ of 2.5V to
# set the bank voltage appropriately, and consequently all other I/Os on banks
# 34 and 35 which are connected to VADJ are LVCMOS25
#
#                 !!! J17 (VADJ select) must be set to 2V5 !!!

set_property -dict {LOC L18 IOSTANDARD LVDS_25 DIFF_TERM TRUE} [get_ports clk_125mhz_p]
set_property -dict {LOC L19 IOSTANDARD LVDS_25 DIFF_TERM TRUE} [get_ports clk_125mhz_n]
create_clock -period 8.000 -name clk_125mhz [get_ports clk_125mhz_p]

# Oscillator enable
set_property -dict {LOC L17 IOSTANDARD LVCMOS25} [get_ports clk_125mhz_en]

# ----------------------------------------------------------------------------
# User LEDs - Bank 33
# ----------------------------------------------------------------------------
set_property -dict { PACKAGE_PIN T22 IOSTANDARD LVCMOS33 SLEW SLOW DRIVE 12 } [get_ports {led[0]}];  # "LD0"
set_property -dict { PACKAGE_PIN T21 IOSTANDARD LVCMOS33 SLEW SLOW DRIVE 12 } [get_ports {led[1]}];  # "LD1"
set_property -dict { PACKAGE_PIN U22 IOSTANDARD LVCMOS33 SLEW SLOW DRIVE 12 } [get_ports {led[2]}];  # "LD2"
set_property -dict { PACKAGE_PIN U21 IOSTANDARD LVCMOS33 SLEW SLOW DRIVE 12 } [get_ports {led[3]}];  # "LD3"
set_property -dict { PACKAGE_PIN V22 IOSTANDARD LVCMOS33 SLEW SLOW DRIVE 12 } [get_ports {led[4]}];  # "LD4"
set_property -dict { PACKAGE_PIN W22 IOSTANDARD LVCMOS33 SLEW SLOW DRIVE 12 } [get_ports {led[5]}];  # "LD5"
set_property -dict { PACKAGE_PIN U19 IOSTANDARD LVCMOS33 SLEW SLOW DRIVE 12 } [get_ports {led[6]}];  # "LD6"
set_property -dict { PACKAGE_PIN U14 IOSTANDARD LVCMOS33 SLEW SLOW DRIVE 12 } [get_ports {led[7]}];  # "LD7"

set_false_path -to [get_ports {led[*]}]
set_output_delay 0 [get_ports {led[*]}]

# ----------------------------------------------------------------------------
# Push buttons - Bank 34
# ----------------------------------------------------------------------------
set_property -dict {LOC T18  IOSTANDARD LVCMOS25} [get_ports btnu]
set_property -dict {LOC N15  IOSTANDARD LVCMOS25} [get_ports btnl]
set_property -dict {LOC R16  IOSTANDARD LVCMOS25} [get_ports btnd]
set_property -dict {LOC R18  IOSTANDARD LVCMOS25} [get_ports btnr]
set_property -dict {LOC P16  IOSTANDARD LVCMOS25} [get_ports btnc]

set_false_path -from [get_ports {btnu btnl btnd btnr btnc}]
set_input_delay 0 [get_ports {btnu btnl btnd btnr btnc}]

# ----------------------------------------------------------------------------
# Toggle switches - Bank 35
# ----------------------------------------------------------------------------
set_property -dict {LOC F22  IOSTANDARD LVCMOS25} [get_ports {sw[0]}]
set_property -dict {LOC G22  IOSTANDARD LVCMOS25} [get_ports {sw[1]}]
set_property -dict {LOC H22  IOSTANDARD LVCMOS25} [get_ports {sw[2]}]
set_property -dict {LOC F21  IOSTANDARD LVCMOS25} [get_ports {sw[3]}]

set_false_path -from [get_ports {sw[*]}]
set_input_delay 0 [get_ports {sw[*]}]

# ----------------------------------------------------------------------------
# Ethernet PHY Port 1 (on FMC card) - Bank 34
# ----------------------------------------------------------------------------
set_property -dict {LOC M19  IOSTANDARD LVCMOS25} [get_ports phy_rx_clk_1] ;# from U37.C1 RXCLK
set_property -dict {LOC P17  IOSTANDARD LVCMOS25} [get_ports {phy_rxd_1[0]}] ;# from U37.B2 RXD0
set_property -dict {LOC P18  IOSTANDARD LVCMOS25} [get_ports {phy_rxd_1[1]}] ;# from U37.D3 RXD1
set_property -dict {LOC N22  IOSTANDARD LVCMOS25} [get_ports {phy_rxd_1[2]}] ;# from U37.C3 RXD2
set_property -dict {LOC P22  IOSTANDARD LVCMOS25} [get_ports {phy_rxd_1[3]}] ;# from U37.B3 RXD3
set_property -dict {LOC M20  IOSTANDARD LVCMOS25} [get_ports phy_rx_ctl_1] ;# from U37.B1 RXCTL_RXDV
set_property -dict {LOC M22  IOSTANDARD LVCMOS25 SLEW FAST DRIVE 16} [get_ports phy_tx_clk_1] ;# from U37.E2 TXC_GTXCLK
set_property -dict {LOC M21  IOSTANDARD LVCMOS25 SLEW FAST DRIVE 16} [get_ports {phy_txd_1[0]}] ;# from U37.F1 TXD0
set_property -dict {LOC J21  IOSTANDARD LVCMOS25 SLEW FAST DRIVE 16} [get_ports {phy_txd_1[1]}] ;# from U37.G2 TXD1
set_property -dict {LOC J22  IOSTANDARD LVCMOS25 SLEW FAST DRIVE 16} [get_ports {phy_txd_1[2]}] ;# from U37.G3 TXD2
set_property -dict {LOC T16  IOSTANDARD LVCMOS25 SLEW FAST DRIVE 16} [get_ports {phy_txd_1[3]}] ;# from U37.H1 TXD3
set_property -dict {LOC T17  IOSTANDARD LVCMOS25 SLEW FAST DRIVE 16} [get_ports phy_tx_ctl_1] ;# from U37.E1 TXCTL_TXEN
set_property -dict {LOC K18  IOSTANDARD LVCMOS25 SLEW SLOW DRIVE 12} [get_ports phy_reset_n_1] ;# from U37.K3 RESET_B

create_clock -period 8.000 -name phy_rx_clk_1 [get_ports phy_rx_clk_1]
set_false_path -to [get_ports {phy_reset_n_1}]
set_output_delay 0 [get_ports {phy_reset_n_1}]

# ----------------------------------------------------------------------------
# Ethernet PHY Port 2 (on FMC card) - Bank 34
# ----------------------------------------------------------------------------
set_property -dict {LOC N19  IOSTANDARD LVCMOS25} [get_ports phy_rx_clk_2]
set_property -dict {LOC L21  IOSTANDARD LVCMOS25} [get_ports {phy_rxd_2[0]}]
set_property -dict {LOC R20  IOSTANDARD LVCMOS25} [get_ports {phy_rxd_2[1]}]
set_property -dict {LOC T19  IOSTANDARD LVCMOS25} [get_ports {phy_rxd_2[2]}]
set_property -dict {LOC R21  IOSTANDARD LVCMOS25} [get_ports {phy_rxd_2[3]}]
set_property -dict {LOC N20  IOSTANDARD LVCMOS25} [get_ports phy_rx_ctl_2]
set_property -dict {LOC N18  IOSTANDARD LVCMOS25 SLEW FAST DRIVE 16} [get_ports phy_tx_clk_2]
set_property -dict {LOC P21  IOSTANDARD LVCMOS25 SLEW FAST DRIVE 16} [get_ports {phy_txd_2[0]}]
set_property -dict {LOC N17  IOSTANDARD LVCMOS25 SLEW FAST DRIVE 16} [get_ports {phy_txd_2[1]}]
set_property -dict {LOC J20  IOSTANDARD LVCMOS25 SLEW FAST DRIVE 16} [get_ports {phy_txd_2[2]}]
set_property -dict {LOC K21  IOSTANDARD LVCMOS25 SLEW FAST DRIVE 16} [get_ports {phy_txd_2[3]}]
set_property -dict {LOC J16  IOSTANDARD LVCMOS25 SLEW FAST DRIVE 16} [get_ports phy_tx_ctl_2]
set_property -dict {LOC J17  IOSTANDARD LVCMOS25 SLEW SLOW DRIVE 12} [get_ports phy_reset_n_2]

create_clock -period 8.000 -name phy_rx_clk_2 [get_ports phy_rx_clk_2]
set_false_path -to [get_ports {phy_reset_n_2}]
set_output_delay 0 [get_ports {phy_reset_n_2}]

# ----------------------------------------------------------------------------
# MAC address EEPROM for Port 1 (on FMC card) - Bank 35
# ----------------------------------------------------------------------------
set_property -dict {LOC A21  IOSTANDARD LVCMOS25} [get_ports mac_eeprom_scl]
set_property -dict {LOC A22  IOSTANDARD LVCMOS25} [get_ports mac_eeprom_sda]
