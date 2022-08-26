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

-- Clock generator for Zedboard + Avnet FMC Network card
-- Inputs: differential 125MHz clock (from LVDS clock generator, FMC_CLK0)
-- Outputs: 125MHz, 125MHz + 90 degrees, 225MHz
-- Note that external clock generator enable must be driven high to turn it on
library ieee; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library unisim; use unisim.vcomponents.all;
library cdc; use cdc.cdc.all;

entity clock_gen is
  generic(
    RESET_STAGES : natural := 4;
    RESET_STAGES2: natural := 7
  );
  port(
    clkin_125mhz_p : in std_logic;
    clkin_125mhz_n : in std_logic;
    reset_in : in std_logic;

    clk : out std_logic;
    reset : out std_logic;

    clk_mac : out std_logic;
    clk_mac_90 : out std_logic;
    reset_mac : out std_logic
  );
end clock_gen;

architecture rtl of clock_gen is
  signal clkin_125mhz_bufg : std_logic;
  signal mmcm_clkfb : std_logic;
  signal mmcm_locked : std_logic;

  signal clk_125mhz : std_logic;
  signal clk_125mhz_90 : std_logic;
  signal clk_125mhz_int : std_logic;
  signal clk_125mhz_90_int : std_logic;
  signal clk_225mhz : std_logic;
  signal clk_225mhz_int : std_logic;

  signal reset_125mhz : std_logic;
  signal reset_225mhz : std_logic;

begin
  clk <= clk_125mhz;
  clk_mac <= clk_125mhz;
  clk_mac_90 <= clk_125mhz_90;
  reset <= reset_125mhz;
  reset_mac <= reset_125mhz;

  sync_reset125_inst : cdc.cdc.reset
    generic map(
      SRC_RST_VALUE => '0',
      RST_DELAY => RESET_STAGES
    )
    port map(
      dst_clk => clk_125mhz,
      src_rst => mmcm_locked,
      dst_rst => reset_125mhz
    ); 

  sync_reset225_inst : cdc.cdc.reset
    generic map(
      SRC_RST_VALUE => '0',
      RST_DELAY => RESET_STAGES2
    )
    port map(
      dst_clk => clk_225mhz,
      src_rst => mmcm_locked,
      dst_rst => reset_225mhz
    ); 

  ibufgds_inst : IBUFGDS
    port map(
      I => clkin_125mhz_p,
      IB => clkin_125mhz_n,
      O => clkin_125mhz_bufg
    );

  mmcm_inst : MMCME2_BASE
    generic map(
      BANDWIDTH => "OPTIMIZED",
      CLKOUT0_DIVIDE_F => 9.0,
      CLKOUT0_DUTY_CYCLE => 0.5,
      CLKOUT0_PHASE => 0.0,
      CLKOUT1_DIVIDE => 9,
      CLKOUT1_DUTY_CYCLE => 0.5,
      CLKOUT1_PHASE => 90.0,
      CLKOUT2_DIVIDE => 5,
      CLKOUT2_DUTY_CYCLE => 0.5,
      CLKOUT2_PHASE => 0.0,
      CLKOUT3_DIVIDE => 1,
      CLKOUT3_DUTY_CYCLE => 0.5,
      CLKOUT3_PHASE => 0.0,
      CLKOUT4_DIVIDE => 1,
      CLKOUT4_DUTY_CYCLE => 0.5,
      CLKOUT4_PHASE => 0.0,
      CLKOUT5_DIVIDE => 1,
      CLKOUT5_DUTY_CYCLE => 0.5,
      CLKOUT5_PHASE => 0.0,
      CLKOUT6_DIVIDE => 1,
      CLKOUT6_DUTY_CYCLE => 0.5,
      CLKOUT6_PHASE => 0.0,
      CLKFBOUT_MULT_F => 9.0,
      CLKFBOUT_PHASE => 0.0,
      DIVCLK_DIVIDE => 1,
      REF_JITTER1 => 0.010,
      CLKIN1_PERIOD => 5.0,
      STARTUP_WAIT => false,
      CLKOUT4_CASCADE => false
    )
    port map(
      CLKIN1 => clkin_125mhz_bufg,
      CLKFBIN => mmcm_clkfb,
      RST => reset_in,
      PWRDWN => '0',
      CLKOUT0 => clk_125mhz_int,
      CLKOUT0B => open,
      CLKOUT1 => clk_125mhz_90_int,
      CLKOUT1B => open,
      CLKOUT2 => clk_225mhz_int,
      CLKOUT2B => open,
      CLKOUT3 => open,
      CLKOUT3B => open,
      CLKOUT4 => open,
      CLKOUT5 => open,
      CLKOUT6 => open,
      CLKFBOUT => mmcm_clkfb,
      CLKFBOUTB => open,
      LOCKED => mmcm_locked
    );

  clk_125_bufg : BUFG
    port map(
      I => clk_125mhz_int,
      O => clk_125mhz
    );

  clk_125_90_bufg : BUFG
    port map(
      I => clk_125mhz_90_int,
      O => clk_125mhz_90
    );

  clk_225_bufg : BUFG
    port map(
      I => clk_225mhz_int,
      O => clk_225mhz
    );
end rtl;
