-- This file is protected by Copyright. Please refer to the COPYRIGHT file
-- distributed with this source distribution.
--
-- This file is part of OpenCPI <http://www.opencpi.org>
--
-- OpenCPI is free software: you can redistribute it and/or modify it under the -- terms of the GNU Lesser General Public License as published by the Free
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
library sync, dac; use dac.ad936x.all; -- note preference of dac.ad936x.DATA_BIT_WIDTH instead of dac.dac.DATA_BIT_WIDTH

-- clock domains:
-- ctrl    - control clock domain
-- ocps    - one DAC clock/sample clock domain
-- data    - AD9361 DATA_CLK domain
-- dataddr - AD9361 DATA_CLK w/ DDR data (as if clock was DATA_CLK x2)
entity ad936x_ocps_lvds_interleaver is
  port(
    -- command/control
    ctrl_clk                    : in  std_logic;
    ctrl_rst                    : in  std_logic;
    ctrl_use_two_r_two_t_timing : in  std_logic;
    -- data ingress (one DAC clock per sample)
    ocps_clk                    : out std_logic; -- one clock/sample
    ocps_data_i_t1              : in  std_logic_vector(DATA_BIT_WIDTH-1 downto 0);
    ocps_data_q_t1              : in  std_logic_vector(DATA_BIT_WIDTH-1 downto 0);
    ocps_data_i_t2              : in  std_logic_vector(DATA_BIT_WIDTH-1 downto 0);
    ocps_data_q_t2              : in  std_logic_vector(DATA_BIT_WIDTH-1 downto 0);
    ocps_ready_t1               : in  std_logic;
    ocps_ready_t2               : in  std_logic;
    ocps_txen                   : in  std_logic;
    -- data egress (to/from AD9361 pins)
    dac_clk                     : in  std_logic; -- AD9361 DATA_CLK
    dac_txen                    : out std_logic; -- AD9361 transmitter on/off
    dacddr_tx_frame             : out std_logic; -- AD9361 TX_FRAME
    dacddr_tx_data              : out std_logic_vector(DATA_BIT_WIDTH/2-1 downto 0)); -- AD9361 P0 or P1
end entity ad936x_ocps_lvds_interleaver;
architecture rtl of ad936x_ocps_lvds_interleaver is

  signal dacd2_clk            : std_logic := '0'; 
  signal dacd2_two_r_two_t_en : std_logic := '0'; 
  signal dacd2_ready_t1       : std_logic := '0';
  signal dacd2_ready_t2       : std_logic := '0';
  signal dacd2_take_t1        : std_logic := '0';
  signal dacd2_take_t2        : std_logic := '0';
  signal dacd2_i_t1           : std_logic_vector(DATA_BIT_WIDTH-1 downto 0) := (others => '0');
  signal dacd2_q_t1           : std_logic_vector(DATA_BIT_WIDTH-1 downto 0) := (others => '0');
  signal dacd2_i_t2           : std_logic_vector(DATA_BIT_WIDTH-1 downto 0) := (others => '0');
  signal dacd2_q_t2           : std_logic_vector(DATA_BIT_WIDTH-1 downto 0) := (others => '0');

begin

  --------------------------------------------------------------------------------------------------
  -- clock management (produces one-clock-per-sample clock domain based on AD936x config)
  --------------------------------------------------------------------------------------------------

  ad936x_clock_per_sample_generator : dac.ad936x.ad936x_clock_per_sample_generator
    port map(
      async_select_0_d2_1_d4 => ctrl_use_two_r_two_t_timing,
      dac_clk                => dac_clk,
      dacd2_clk              => dacd2_clk,
      dacd4_clk              => open,
      ocps_clk               => ocps_clk);

  --------------------------------------------------------------------------------------------------
  -- data_txen alignment w/ data bus (and CDC)
  --------------------------------------------------------------------------------------------------

  data_txen_pipeline_cdc : process(dac_clk)
  begin
    if rising_edge(dac_clk) then
      -- CDC between clocks that have a fixed-phase relationship, so there is no expected
      -- metastability here (relying on static timing analysis to identify setup/hold violations)
      if (dacd2_take_t1 = '1') then
        dac_txen <= ocps_txen;
      end if;
    end if;
  end process;

  --------------------------------------------------------------------------------------------------
  -- data bus CDC from one-clock-per-DAC-sample clock domain to DATA_CLK/2 clock domain
  --------------------------------------------------------------------------------------------------

  ocps_to_dacd2_cdc : process(dacd2_clk)
  begin
    if rising_edge(dacd2_clk) then
      -- CDC between clocks that have a fixed-phase relationship, so there is no expected
      -- metastability here (relying on static timing analysis to identify setup/hold violations)
      if (dacd2_take_t1 = '1') then
        dacd2_i_t1 <= ocps_data_i_t1;
        dacd2_q_t1 <= ocps_data_q_t1;
      end if;
      if (dacd2_take_t2 = '1') then
        dacd2_i_t2 <= ocps_data_i_t2;
        dacd2_q_t2 <= ocps_data_q_t2;
      end if;
      dacd2_ready_t1 <= ocps_ready_t1;
      dacd2_ready_t2 <= ocps_ready_t2;
    end if;
  end process;

  --------------------------------------------------------------------------------------------------
  -- data interleaving required for AD936x physical bus
  --------------------------------------------------------------------------------------------------

  cdc : sync.sync.sync_bit
    generic map(
      N         => 2,
      IREG      => '1',
      RST_LEVEL => '0')
    port map(
      src_clk  => ctrl_clk,
      src_rst  => ctrl_rst,
      src_en   => '1',
      src_in   => ctrl_use_two_r_two_t_timing,
      dest_clk => dacd2_clk,
      dest_rst => '0',
      dest_out => dacd2_two_r_two_t_en);

  interleaver : dac.ad936x.ad936x_lvds_interleaver
    port map(
      dac_clk              => dac_clk,
      dacd2_clk            => dacd2_clk,
      dacd2_two_r_two_t_en => dacd2_two_r_two_t_en,
      dacd2_i_t1           => dacd2_i_t1,
      dacd2_q_t1           => dacd2_q_t1,
      dacd2_i_t2           => dacd2_i_t2,
      dacd2_q_t2           => dacd2_q_t2,
      dacd2_ready_t1       => dacd2_ready_t1,
      dacd2_ready_t2       => dacd2_ready_t2,
      dacd2_take_t1        => dacd2_take_t1,
      dacd2_take_t2        => dacd2_take_t2,
      dacddr_tx_frame      => dacddr_tx_frame,
      dacddr_tx_data       => dacddr_tx_data);

end rtl;
