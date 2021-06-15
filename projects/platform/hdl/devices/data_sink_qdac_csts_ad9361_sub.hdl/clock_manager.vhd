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

-- this "primitive" is by-design vendor-agnostic

--------------------------------------------------------------------------------
-- clock domain: description                | fixed-phase  | frequency-locked  |
--                                          | relationship | with              |
--                                          | with         |                   |
--------------------------------------------------------------------------------
-- async: N/A                               | N/A          | N/A               |
--------------------------------------------------------------------------------
-- data_clk:                                | AD9361       | AD9361            |
--                                          | DATA_CLK     | DATA_CLK          |
--------------------------------------------------------------------------------
-- datad2_clk: data_clk divided by 2        | AD9361       |                   |
--                                          | DATA_CLK     |                   |
--------------------------------------------------------------------------------
-- datad4_clk: data_clk divided by 4        | AD9361       |                   |
--                                          | DATA_CLK     |                   |
--------------------------------------------------------------------------------
-- ocps: one clock per ADC/DAC sample       | AD9361       |                   |
--       (will be either datad2_clk         | DATA_CLK     |                   |
--       or datad4_clk based upon           |              |                   |
--       runtime selection)                 |              |                   |
--------------------------------------------------------------------------------
library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;

entity clock_manager is
  generic(
     -- first divider provides data_clk divided-by-2 signal
    FIRST_DIVIDER_TYPE         : string; -- "BUFFER", "REGISTER"
    FIRST_DIVIDER_ROUTABILITY  : string; -- "GLOBAL", "REGIONAL"
     -- second divider provides data_clk divided-by-4 signal
    SECOND_DIVIDER_TYPE        : string; -- "BUFFER", "REGISTER"
    SECOND_DIVIDER_ROUTABILITY : string); -- "GLOBAL", "REGIONAL"
  port(
    async_select_0_d2_1_d4 : in  std_logic; -- 0: divide-by-2, 1: divide-by-4
    data_clk               : in  std_logic;
    datad2_clk             : out std_logic;
    datad4_clk             : out std_logic;
    ocps_clk               : out std_logic);
end entity clock_manager;

architecture rtl of clock_manager is
  signal datad2_clk_s : std_logic := '0';
  signal datad4_clk_s : std_logic := '0';
begin

  first_divider : entity work.clock_divider
    generic map(
      DIVIDER_TYPE => FIRST_DIVIDER_TYPE,
      ROUTABILITY  => FIRST_DIVIDER_ROUTABILITY,
      DIVISOR      => "2")
    port map(
      clk_in  => data_clk,
      clk_out => datad2_clk_s);

  second_divider : entity work.clock_divider
    generic map(
      DIVIDER_TYPE => SECOND_DIVIDER_TYPE,
      ROUTABILITY  => SECOND_DIVIDER_ROUTABILITY,
      DIVISOR      => "2")
    port map(
      clk_in  => datad2_clk_s,
      clk_out => datad4_clk_s);

  clock_selector : entity work.clock_selector_with_async_select
    port map(
      async_select => async_select_0_d2_1_d4,
      clk_in0      => datad2_clk_s,
      clk_in1      => datad4_clk_s,
      clk_out      => ocps_clk);

  datad2_clk <= datad2_clk_s;
  datad4_clk <= datad4_clk_s;

end rtl;
