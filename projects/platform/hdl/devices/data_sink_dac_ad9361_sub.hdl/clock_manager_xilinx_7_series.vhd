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
library unisim;

entity clock_manager_xilinx_7_series is
  port(
    dac_clk                : in  std_logic;
    async_select_0_d2_1_d4 : in  std_logic;
    dacd2_clk              : out std_logic;
    dacd4_clk              : out std_logic;
    wsi_clk                : out std_logic);
end entity clock_manager_xilinx_7_series;

architecture rtl of clock_manager_xilinx_7_series is

  signal dacd2_clk_s : std_logic := '0';
  signal dacd4_clk_s : std_logic := '0';

begin

  dacd2_clk_gen : unisim.vcomponents.BUFR
    generic map(
      BUFR_DIVIDE => "2")
    port map(
      O   => dacd2_clk_s,
      CE  => '1',
      CLR => '0',
      I   => dac_clk);

  dacd4_clk_gen : unisim.vcomponents.BUFR
    generic map(
      BUFR_DIVIDE => "2")
    port map(
      O   => dacd4_clk_s,
      CE  => '1',
      CLR => '0',
      I   => dacd2_clk_s);

  -- With BUFGMUX "glitches or short pulses can appear on the output" when
  -- setup/hold is not met for the select.
  -- BUFGMUX_CTRL does not have this shortcoming, implying that select is
  -- allowed to be asynchronous.
  -- For more info see Xilinx UG472.
  bugfmux : unisim.vcomponents.BUFGMUX_CTRL
    port map(
      O  => wsi_clk,
      I0 => dacd2_clk_s,
      I1 => dacd4_clk_s,
      S  => async_select_0_d2_1_d4);

  dacd2_clk <= dacd2_clk_s;
  dacd4_clk <= dacd4_clk_s;

end rtl;
