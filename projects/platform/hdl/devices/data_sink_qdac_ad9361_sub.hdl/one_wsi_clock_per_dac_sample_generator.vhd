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
-- clock domain: description                | fixed-phased | frequency-locked  |
--                                          | relationship | with              |
--                                          | with         |                   |
--------------------------------------------------------------------------------
-- wci: worker control interface            |              |                   |
--------------------------------------------------------------------------------
-- dac: clock that is phase & frequency     | AD9361       | AD9361            |
--                                          | DATA_CLK     | DATA_CLK          |
--------------------------------------------------------------------------------
-- wsi:(data_sink_dac.hdl input) worker     | AD9361       |                   |
--     streaming interface clock            | DATA_CLK     |                   |
--------------------------------------------------------------------------------
library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;
library dac;

entity one_wsi_clock_per_dac_sample_generator is
  generic(
    NUM_CHANS                  : positive := 2;
    MODE                       : string; -- "CMOS", "LVDS"
     -- first divider provides data_clk divided-by-2 signal
    FIRST_DIVIDER_TYPE         : string := "REGISTER"; -- "BUFFER", "REGISTER"
    FIRST_DIVIDER_ROUTABILITY  : string := "GLOBAL"; -- "GLOBAL", "REGIONAL"
     -- second divider provides data_clk divided-by-4 signal
    SECOND_DIVIDER_TYPE        : string := "REGISTER"; -- "BUFFER", "REGISTER"
    SECOND_DIVIDER_ROUTABILITY : string := "GLOBAL"); -- "GLOBAL", "REGIONAL"

  port(
    -- to/from supported worker
    wci_use_two_r_two_t_timing : in  std_logic;
    wsi_clk                    : out std_logic; -- one clock/sample
    wsi_data_in_i              : in  dac.dac.array_data_t(0 to NUM_CHANS-1);
    wsi_data_in_q              : in  dac.dac.array_data_t(0 to NUM_CHANS-1);
    wsi_data_in_valid          : in  std_logic_vector(0 to NUM_CHANS-1);
    wsi_txen                   : in  std_logic;
    -- clock handling
    dac_clk                    : in  std_logic; -- multiple clocks/sample
    someclk                    : out std_logic;
    -- to/from data_interleaver
    someclk_data_i             : out dac.dac.array_data_t(0 to NUM_CHANS-1);
    someclk_data_q             : out dac.dac.array_data_t(0 to NUM_CHANS-1);
    someclk_data_vld           : out std_logic_vector(0 to NUM_CHANS-1);
    someclk_take               : in  std_logic_vector(0 to NUM_CHANS-1);
    dac_txen                   : out std_logic);
end entity one_wsi_clock_per_dac_sample_generator;
architecture rtl of one_wsi_clock_per_dac_sample_generator is
  signal dacd2_clk_s : std_logic := '0';
  signal someclk_s   : std_logic := '0';
begin

  clock_manager : entity work.clock_manager
    generic map(
      FIRST_DIVIDER_TYPE         => FIRST_DIVIDER_TYPE,
      FIRST_DIVIDER_ROUTABILITY  => FIRST_DIVIDER_ROUTABILITY,
      SECOND_DIVIDER_TYPE        => SECOND_DIVIDER_TYPE,
      SECOND_DIVIDER_ROUTABILITY => SECOND_DIVIDER_ROUTABILITY)
    port map(
      async_select_0_d2_1_d4 => wci_use_two_r_two_t_timing,
      data_clk               => dac_clk,
      datad2_clk             => dacd2_clk_s,
      datad4_clk             => open,
      ocps_clk               => wsi_clk);

  someclk_s <= dac_clk     when (MODE = "CMOS") else
               dacd2_clk_s when (MODE = "LVDS") else
               dac_clk;
  someclk <= someclk_s;

  process(dac_clk)
  begin
    if(rising_edge(dac_clk)) then
        dac_txen <= wsi_txen;
    end if;
  end process;

  chan_generate : for ch in 0 to NUM_CHANS-1 generate
  begin
    process(someclk_s)
    begin
      if(rising_edge(someclk_s)) then
        -- CDC between clocks that have a fixed-phase relationship, so there is no expected
        -- metastability here (relying on static timing analysis to identify setup/hold violations)
        if(someclk_take(ch) = '1') then
          someclk_data_i(ch) <= wsi_data_in_i(ch);
          someclk_data_q(ch) <= wsi_data_in_q(ch);
        end if;
        someclk_data_vld(ch) <= wsi_data_in_valid(ch);
      end if;
    end process;
  end generate chan_generate;

end rtl;
