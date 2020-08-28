-- This file is protected by Copyright. Please refer to the COPYRIGHT file
-- distributed with this source distribution.
--
-- This file is part of OpenCPI <http://www.opencpi.org>
--
-- OpenCPI is free software: you can redistribute it and/or modify it under the
-- terms of the GNU Lesser General Public License as published by the Free
-- Software Foundation, either version 3 of the License, or (at your option) any
-- later version.
--
-- OpenCPI is distributed in the hope that it will be useful, but WITHOUT ANY
-- WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
-- A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
-- details.
--
-- You should have received a copy of the GNU Lesser General Public License
-- along with this program. If not, see <http://www.gnu.org/licenses/>.
library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;
library dac; use dac.ad936x.all;

-- clock domains:
-- static_* - clock domain independent (constant value)
-- wci_*    - worker control interface
-- wsi_*    - worker streaming interface (one clock/sample, samples coming in from data_sink_dac.hdl)
-- dac_*    - AD9361 DATA_CLK
entity control_interfacer is
  generic(
    LVDS_P                     : boolean;
    HALF_DUPLEX_P              : boolean;
    SINGLE_PORT_P              : boolean;
    DATA_RATE_CONFIG_P         : dac.ad936x.data_rate_config_t;
    DATA_BUS_BITS_ARE_REVERSED : boolean);
  port(
    -- wci
    wci_clk                      : in  std_logic;
    wci_reset                    : in  std_logic;
    wci_is_operating             : in  std_logic;
    -- dev_cfg_data
    wci_config_is_two_r          : in  std_logic;
    wci_ch0_handler_is_present   : out std_logic;
    wci_ch1_handler_is_present   : out std_logic;
    wci_data_bus_index_direction : out std_logic;
    wci_data_clk_is_inverted     : out std_logic;
    wci_islvds                   : out std_logic;
    wci_isdualport               : out std_logic;
    wci_isfullduplex             : out std_logic;
    wci_isddr                    : out std_logic;
    wci_present                  : out std_logic;
    -- dev_cfg_data_tx
    wci_config_is_two_t          : in  std_logic;
    wci_force_two_r_two_t_timing : in  std_logic;
    -- dev_data_ch0
    static_ch0_in_present        : in  std_logic;
    -- dev_data_ch1
    static_ch1_in_present        : in  std_logic;
    -- data_sink_qdac_ad9361_sub
    wci_use_two_r_two_t_timing   : out std_logic);
end entity control_interfacer;
architecture rtl of control_interfacer is
  signal static_dual_port   : std_logic := '0';
  signal static_data_rate   : std_logic := '0';
  signal static_full_duplex : std_logic := '0';
begin

  -- From ADI's UG-570:
  -- "For a system with a 2R1T or a 1R2T configuration, the clock
  -- frequencies, bus transfer rates and sample periods, and data
  -- capture timing are the same as if configured for a 2R2T system.
  -- However, in the path with only a single channel used, the
  -- disabled channel’s I-Q pair in each data group is unused."
  wci_use_two_r_two_t_timing <= wci_config_is_two_r or
                                wci_config_is_two_t or
                                wci_force_two_r_two_t_timing;

  -- these signals are used to (eventually) tell higher level proxy(ies)
  -- about the data port configuration that was enforced when this worker was
  -- compiled, so that said proxy(ies) can set the AD9361 registers accordingly
  static_dual_port             <= '0' when SINGLE_PORT_P else '1';
  static_full_duplex           <= '0' when HALF_DUPLEX_P else '1';
  static_data_rate             <= '1' when (DATA_RATE_CONFIG_P = DDR) else '0';
  wci_ch0_handler_is_present   <= static_ch0_in_present;
  wci_ch1_handler_is_present   <= static_ch1_in_present;
  wci_data_bus_index_direction <= '1' when DATA_BUS_BITS_ARE_REVERSED else '0';
  wci_data_clk_is_inverted     <= '0';
  wci_islvds                   <= '1' when LVDS_P else '0';
  wci_isdualport               <= '1' when LVDS_P else static_dual_port;
  wci_isfullduplex             <= '1' when LVDS_P else static_full_duplex;
  wci_isddr                    <= '1' when LVDS_P else static_data_rate;
  wci_present                  <= '1';

end rtl;
