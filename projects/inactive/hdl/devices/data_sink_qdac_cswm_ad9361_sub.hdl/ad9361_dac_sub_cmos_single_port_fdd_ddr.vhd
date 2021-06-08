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

library IEEE; use IEEE.std_logic_1164.all, ieee.numeric_std.all;
library cdc; use cdc.cdc.all;
entity ad9361_dac_sub_cmos_single_port_fdd_ddr is
  generic(data_bus_bits_are_reversed : in boolean);
  port (-- wci (control plane) clock domain
        wci_clk                      : in  std_logic;
        wci_reset                    : in  std_logic;
        wci_use_two_r_two_t_timing   : in  std_logic;
        -- dac clock domain (AD9361 DATA_CLK domain)
        dac_clk                      : in  std_logic; -- AD9361 DATA_CLK
        dac_data_i_ch0               : in  std_logic_vector(11 downto 0);
        dac_data_i_ch1               : in  std_logic_vector(11 downto 0);
        dac_data_q_ch0               : in  std_logic_vector(11 downto 0);
        dac_data_q_ch1               : in  std_logic_vector(11 downto 0);
        dac_dev_data_ch0_in_in_ready : in  std_logic;
        dac_dev_data_ch1_in_in_ready : in  std_logic;
        dac_tx_frame                 : out std_logic; -- AD9361 TX_FRAME
        dac_dev_data_ch0_in_out_take : out std_logic;
        dac_dev_data_ch1_in_out_take : out std_logic;
        -- dac clock x2 domain (e.g. dac clock w/ DDR data)
        dacm2_dev_data               : out std_logic_vector(23 downto 0)); -- to AD9361 P0 or P1
end entity ad9361_dac_sub_cmos_single_port_fdd_ddr;
architecture rtl of ad9361_dac_sub_cmos_single_port_fdd_ddr is
  signal dac_reset : std_logic;
  -- dac clock domain (AD9361 DATA_CLK domain)
  signal dac_use_two_r_two_t_timing_rr : std_logic := '0';
  signal dac_ch0_ready_rr     : std_logic := '0';
  signal dac_ch1_ready_rr     : std_logic := '0';
  signal dac_tx_data_ddr_ris  : std_logic_vector(5 downto 0) := (others => '0');
  signal dac_tx_data_ddr_fal  : std_logic_vector(5 downto 0) := (others => '0');
  -- dac clock x2 domain (e.g. dac clock w/ DDR data)
  signal dacm2_tx_data : std_logic_vector(5 downto 0) := (others => '0');
begin
  
  dac_reset_gen : cdc.cdc.reset
    port map(
      src_rst => wci_reset,
      dst_clk => dac_clk,
      dst_rst => dac_reset); 

  -- sync (WCI clock domain) -> (DAC clock domain),
  -- note that we don't care if WCI clock is much faster and bits are
  -- dropped - wci_use_two_r_two_t_timing is a configuration bit which is
  -- expected to change very rarely in relation to either clock
  second_chan_enable_sync : cdc.cdc.single_bit
    generic map(IREG      => '1',
                RST_LEVEL => '0')
    port map   (src_clk      => wci_clk,
                src_rst      => wci_reset,
                src_en       => '1',
                src_in       => wci_use_two_r_two_t_timing,
                dst_clk      => dac_clk,
                dst_rst      => dac_reset,
                dst_out      => dac_use_two_r_two_t_timing_rr);  -- delayed by one WCI clock, two DAC clocks

  -- delay ready enough to ensure that there is always at least
  -- 1 sample in the CDC FIFO (prevents possibility of CDC FIFO underrun upon
  -- startup)
  ready_delay_regs : process(dac_clk)
    variable dac_ch0_ready_r : std_logic := '0';
    variable dac_ch1_ready_r : std_logic := '0';
  begin
    if rising_edge(dac_clk) then
      dac_ch0_ready_rr <= dac_ch0_ready_r;
      dac_ch1_ready_rr <= dac_ch1_ready_r;
      dac_ch0_ready_r  := dac_dev_data_ch0_in_in_ready;
      dac_ch1_ready_r  := dac_dev_data_ch1_in_in_ready;
    end if;
  end process;

  -- AD9361 T1/T2 channels correspond to dev signal channels 0/1 (we are taking
  -- ADI-specific terminology and exposing it generically)
  tx_data : entity work.ad936x_tx_data_cmos_single_port_fdd_ddr
    port map(
      data_clk        => dac_clk,
      two_r_two_t_en  => dac_use_two_r_two_t_timing_rr,
      data_i_t1       => dac_data_i_ch0,
      data_q_t1       => dac_data_q_ch0,
      data_i_t2       => dac_data_i_ch1,
      data_q_t2       => dac_data_q_ch1,
      ready_t1        => dac_ch0_ready_rr,
      ready_t2        => dac_ch1_ready_rr,
      take_t1         => dac_dev_data_ch0_in_out_take,
      take_t2         => dac_dev_data_ch1_in_out_take,
      tx_frame        => dac_tx_frame,
      tx_data         => dacm2_tx_data);

  dacm2_dev_data(dacm2_dev_data'left downto dacm2_tx_data'length) <= (others => '0');

  data_bus_bits_not_reversed : if data_bus_bits_are_reversed = false generate
    data_order_loop : for idx in dacm2_tx_data'left downto 0 generate
      dacm2_dev_data(idx) <= dacm2_tx_data(idx);
    end generate;
  end generate;

  data_bus_bits_reversed : if data_bus_bits_are_reversed generate
    data_order_loop : for idx in dacm2_tx_data'left downto 0 generate
      dacm2_dev_data(idx) <= dacm2_tx_data(dacm2_tx_data'left-idx);
    end generate;
  end generate;

end rtl;
