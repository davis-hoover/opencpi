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

-- clock domains:
-- wci: worker control interface
-- wsi: worker streaming interface (will be same as either dacd2 or dacd4 clock
--      domain, depending on wci_use_two_r_two_timing_t)
-- dac: clock that is phase & frequency locked with the AD9361 DATA_CLK
-- dacd2: AD9361 DATA_CLK divided by 2
-- dacd4: AD9361 DATA_CLK divided by 4
library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;
library cdc, dac;

entity one_wsi_clock_per_dac_sample_generator is
  generic(
    NUM_CHANS : positive := 2);
  port(
    -- to/from supported worker
    wci_use_two_r_two_t_timing : in  std_logic;
    wsi_clk                    : out std_logic;
    wsi_data_in_i              : in  dac.dac.array_data_t(0 to NUM_CHANS-1);
    wsi_data_in_q              : in  dac.dac.array_data_t(0 to NUM_CHANS-1);
    wsi_data_in_valid          : in  std_logic_vector(0 to NUM_CHANS-1);
    -- clock handling
    dac_clk                    : in  std_logic;
    dacd2_clk                  : out std_logic;
    dacd4_clk                  : out std_logic;
    -- to/from data_interleaver
    dac_data_i                 : out dac.dac.array_data_t(0 to NUM_CHANS-1);
    dac_data_q                 : out dac.dac.array_data_t(0 to NUM_CHANS-1);
    dac_data_vld               : out std_logic_vector(0 to NUM_CHANS-1);
    dac_take                   : in  std_logic_vector(0 to NUM_CHANS-1));
end entity one_wsi_clock_per_dac_sample_generator;
architecture rtl of one_wsi_clock_per_dac_sample_generator is

  signal wsi_clk_s            : std_logic := '0';
  signal wsi_data_in          : dac.dac.array_qdata_t(0 to NUM_CHANS-1) :=
                                (others => (others => '0'));
  signal dac_fifo_dst_out     : dac.dac.array_qdata_t(0 to NUM_CHANS-1) :=
                                (others => (others => '0'));
  signal dac_fifo_dst_deq     : std_logic_vector(0 to NUM_CHANS-1)
                                := (others => '0');
  signal dac_fifo_dst_empty_n : std_logic_vector(0 to NUM_CHANS-1)
                                := (others => '0');

begin

  -- NOTES: The combination of clock_manager and fifo allows:
  -- 1. wsi_clk to be one clock per sample per channel.
  -- 2. fifo's src_FULL_N to be ignored since the fifo will never overrun
  -- (because fifo's dst_CLK is guaranteed to have >= 2x the frequency of src_CLK, due to the BUFR_DIVIDE values within clock_manager_xilinx_7_series, src_FULL_N can never go high)

  clock_manager : entity work.clock_manager_xilinx_7_series
    port map(
      dac_clk                => dac_clk,
      async_select_0_d2_1_d4 => wci_use_two_r_two_t_timing,
      dacd2_clk              => dacd2_clk,
      dacd4_clk              => dacd4_clk,
      wsi_clk                => wsi_clk_s);

  wsi_clk <= wsi_clk_s;
  chan_generate : for ch in 0 to NUM_CHANS-1 generate
  begin

    wsi_data_in(ch) <= wsi_data_in_i(ch) & wsi_data_in_q(ch);

    foo : cdc.cdc.fifo
      generic map(
        WIDTH       => 2*dac.dac.DATA_BIT_WIDTH,
        DEPTH       => 16) -- recommended minimum
      port map(
        src_CLK     => wsi_clk_s,
        src_RST     => '0',
        src_ENQ     => wsi_data_in_valid(ch),
        src_in      => wsi_data_in(ch),
        src_FULL_N  => open, -- see NOTES
        dst_CLK     => dac_clk,
        dst_DEQ     => dac_fifo_dst_deq(ch),
        dst_out     => dac_fifo_dst_out(ch),
        dst_EMPTY_N => dac_fifo_dst_empty_n(ch));

    dac_fifo_dst_deq(ch) <= dac_fifo_dst_empty_n(ch) and dac_take(ch);

    dac_data_i(ch)   <= dac_fifo_dst_out(ch)(2*dac.dac.DATA_BIT_WIDTH
                                             - 1 downto dac.dac.DATA_BIT_WIDTH);
    dac_data_q(ch)   <= dac_fifo_dst_out(ch)(dac.dac.DATA_BIT_WIDTH-1 downto 0);
    dac_data_vld(ch) <= dac_fifo_dst_empty_n(ch);

  end generate;

end rtl;
