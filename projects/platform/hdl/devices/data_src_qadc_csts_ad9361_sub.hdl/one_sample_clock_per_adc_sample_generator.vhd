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
-- adc: clock that is phase & frequency     | AD9361       | AD9361            |
--                                          | DATA_CLK     | DATA_CLK          |
--------------------------------------------------------------------------------
-- sample:(data_src_adc.hdl input) worker   | AD9361       |                   |
--        sample clock                      | DATA_CLK     |                   |
--------------------------------------------------------------------------------
library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;
library adc_csts;

entity one_sample_clock_per_adc_sample_generator is
  generic(
    NUM_CHANS                  : positive := 2;
     -- first divider provides data_clk divided-by-2 signal
    FIRST_DIVIDER_TYPE         : string := "REGISTER"; -- "BUFFER", "REGISTER"
    FIRST_DIVIDER_ROUTABILITY  : string := "GLOBAL"; -- "GLOBAL", "REGIONAL"
     -- second divider provides data_clk divided-by-4 signal
    SECOND_DIVIDER_TYPE        : string := "REGISTER"; -- "BUFFER", "REGISTER"
    SECOND_DIVIDER_ROUTABILITY : string := "GLOBAL"); -- "GLOBAL", "REGIONAL"

  port(
    -- to/from data_interleaver
    someclk_data_i                : in  adc_csts.adc_csts.array_data_t(0 to NUM_CHANS-1);
    someclk_data_q                : in  adc_csts.adc_csts.array_data_t(0 to NUM_CHANS-1);
    someclk_data_vld              : in  std_logic_vector(0 to NUM_CHANS-1);
    -- clock handling
    adc_clk                       : in  std_logic; -- multiple clocks/sample
    -- to/from supported worker
    worker_present                : in  std_logic_vector(0 to NUM_CHANS-1);
    wci_use_two_r_two_t_timing    : in  std_logic;
    sample_clk                    : out std_logic; -- one clock/sample
    sample_data_out_i             : out adc_csts.adc_csts.array_data_t(0 to NUM_CHANS-1);
    sample_data_out_q             : out adc_csts.adc_csts.array_data_t(0 to NUM_CHANS-1);
    sample_data_out_valid         : out std_logic_vector(0 to NUM_CHANS-1));
  
end entity one_sample_clock_per_adc_sample_generator;

architecture rtl of one_sample_clock_per_adc_sample_generator is
  signal sample_clk_s       : std_logic;
begin

  clock_manager : entity work.clock_manager
    generic map(
      FIRST_DIVIDER_TYPE         => FIRST_DIVIDER_TYPE,
      FIRST_DIVIDER_ROUTABILITY  => FIRST_DIVIDER_ROUTABILITY,
      SECOND_DIVIDER_TYPE        => SECOND_DIVIDER_TYPE,
      SECOND_DIVIDER_ROUTABILITY => SECOND_DIVIDER_ROUTABILITY)
    port map(
      async_select_0_d2_1_d4 => wci_use_two_r_two_t_timing,
      data_clk               => adc_clk,
      datad2_clk             => open,
      datad4_clk             => open,
      ocps_clk               => sample_clk_s);

  sample_clk <= sample_clk_s;

  chan_generate : for ch in 0 to NUM_CHANS-1 generate
  begin

    sample_data_out_valid(ch) <= '1' when (ch = 0 or (ch = 1 and wci_use_two_r_two_t_timing = '1' and worker_present(1) = '1')) else '0';

    process(sample_clk_s)
    begin
      if(rising_edge(sample_clk_s)) then
        -- CDC between clocks that have a fixed-phase relationship, so there is no expected
        -- metastability here (relying on static timing analysis to identify setup/hold violations)
          sample_data_out_i(ch) <= someclk_data_i(ch);
          sample_data_out_q(ch) <= someclk_data_q(ch);
      end if;
    end process;
  end generate chan_generate;

end rtl;
