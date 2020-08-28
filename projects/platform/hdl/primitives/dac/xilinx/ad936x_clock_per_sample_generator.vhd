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

--------------------------------------------------------------------------------
-- clock domain: description                | fixed-phase  | frequency-locked  |
--                                          | relationship | with              |
--                                          | with         |                   |
--------------------------------------------------------------------------------
-- async: N/A                               | N/A          | N/A               |
--------------------------------------------------------------------------------
-- dac_clk:                                 | AD9361       | AD9361            |
--                                          | DATA_CLK     | DATA_CLK          |
--------------------------------------------------------------------------------
-- dacd2_clk: dac_clk divided by 2          | AD9361       |                   |
--                                          | DATA_CLK     |                   |
--------------------------------------------------------------------------------
-- dacd4_clk: dac_clk divided by 4          | AD9361       |                   |
--                                          | DATA_CLK     |                   |
--------------------------------------------------------------------------------
-- ocps: one clock per ADC/DAC sample       | AD9361       |                   |
--       (will be either dacd2_clk          | DATA_CLK     |                   |
--       or dacd4_clk based upon            |              |                   |
--       runtime selection)                 |              |                   |
--------------------------------------------------------------------------------

library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;
library util, unisim;

entity ad936x_clock_per_sample_generator is
  port(
    async_select_0_d2_1_d4 : in  std_logic; -- 0: divide-by-2, 1: divide-by-4
    dac_clk                : in  std_logic;
    dacd2_clk              : out std_logic;
    dacd4_clk              : out std_logic;
    ocps_clk               : out std_logic);
end entity ad936x_clock_per_sample_generator;

architecture rtl of ad936x_clock_per_sample_generator is

  signal dacd2_clk_s : std_logic := '0';
  signal dacd4_clk_s : std_logic := '0';

begin

  -- BUFR required for Zynq 7-Series performance
  first_divider : unisim.vcomponents.BUFR
    generic map(
      BUFR_DIVIDE => "2")
    port map(
      O   => dacd2_clk_s,
      CE  => '1',
      CLR => '0',
      I   => dac_clk);

  second_divider : process(dacd2_clk_s)
  begin
    if rising_edge(dacd2_clk_s) then
      dacd4_clk_s <= not dacd4_clk_s;
    end if;
  end process second_divider;

  clock_selector : util.util.clock_selector
    port map(
      async_select => async_select_0_d2_1_d4,
      clk_in0      => dacd2_clk_s,
      clk_in1      => dacd4_clk_s,
      clk_out      => ocps_clk);

  dacd2_clk <= dacd2_clk_s;
  dacd4_clk <= dacd4_clk_s;

end rtl;
