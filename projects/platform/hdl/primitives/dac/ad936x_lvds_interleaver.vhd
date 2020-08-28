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

----------------------------------------------------------------------------------------------------
-- This implements AD9361_Reference_Manual_UG-570.pdf Figure 80. Transmit
-- Data Path, LVDS. The implementation employs ample pipelining and register
-- duplication in order to meet the demanding timing requirements of Zynq
-- 7-Series FPGAs.
--
-- clock domains:
-- * dac    - AD9361 DATA_CLK
-- * dacd2  - AD9361 DATA_CLK divided by two (fixed phase relationship w/ DATA_CLK)
-- * dacddr - data output from DDR register whose input is in the data clock domain (sort of
--            equivalent to data clock multiplied by 2)
----------------------------------------------------------------------------------------------------
library ieee; use ieee.std_logic_1164.all; use ieee.numeric_std.all;
library util, dac; use dac.ad936x.all; -- note preference of dac.ad936x.DATA_BIT_WIDTH instead of dac.dac.DATA_BIT_WIDTH
entity ad936x_lvds_interleaver is
  port(
    dac_clk              : in  std_logic; -- AD9361 DATA_CLK
    dacd2_clk            : in  std_logic;
    dacd2_two_r_two_t_en : in  std_logic; -- indicates whether 2R2T is to be used
    dacd2_i_t1           : in  std_logic_vector(DATA_BIT_WIDTH-1 downto 0);
    dacd2_q_t1           : in  std_logic_vector(DATA_BIT_WIDTH-1 downto 0);
    dacd2_i_t2           : in  std_logic_vector(DATA_BIT_WIDTH-1 downto 0);
    dacd2_q_t2           : in  std_logic_vector(DATA_BIT_WIDTH-1 downto 0);
    dacd2_ready_t1       : in  std_logic; -- data...{i,q}_t1 are valid and ready
    dacd2_ready_t2       : in  std_logic; -- data...{i,q}_t2 are valid and ready
    dacd2_take_t1        : out std_logic; -- facilitates backpressure for framing alignment
    dacd2_take_t2        : out std_logic; -- facilitates backpressure for framing alignment
    dacddr_tx_frame      : out std_logic; -- AD9361 TX_FRAME
    dacddr_tx_data       : out std_logic_vector(DATA_BIT_WIDTH/2-1 downto 0)); -- AD9361 P0 or P1
end entity ad936x_lvds_interleaver;
architecture rtl of ad936x_lvds_interleaver is

  type ch_sel_t is (T1, T2);
  type ch_sel_array_t is array(DATA_BIT_WIDTH-1 downto 0) of ch_sel_t;

  -- manually duplicate these register to aid in timing
  signal dacd2_ch_sel   : ch_sel_array_t := (others => T1);
  signal dacd2_ch_sel_r : ch_sel_array_t := (others => T1);

  signal dacd2_i_t1_r : std_logic_vector(DATA_BIT_WIDTH-1 downto 0) := (others => '0');
  signal dacd2_q_t1_r : std_logic_vector(DATA_BIT_WIDTH-1 downto 0) := (others => '0');
  signal dacd2_i_t2_r : std_logic_vector(DATA_BIT_WIDTH-1 downto 0) := (others => '0');
  signal dacd2_q_t2_r : std_logic_vector(DATA_BIT_WIDTH-1 downto 0) := (others => '0');

  signal dacd2_i_r    : std_logic_vector(DATA_BIT_WIDTH-1 downto 0) := (others => '0');
  signal dacd2_q_r    : std_logic_vector(DATA_BIT_WIDTH-1 downto 0) := (others => '0');

  signal dacd2_i_hi_r : std_logic_vector(DATA_BIT_WIDTH/2-1 downto 0) := (others => '0');
  signal dacd2_q_hi_r : std_logic_vector(DATA_BIT_WIDTH/2-1 downto 0) := (others => '0');
  signal dacd2_i_lo_r : std_logic_vector(DATA_BIT_WIDTH/2-1 downto 0) := (others => '0');
  signal dacd2_q_lo_r : std_logic_vector(DATA_BIT_WIDTH/2-1 downto 0) := (others => '0');
  signal dac_tx_data_ris : std_logic_vector(DATA_BIT_WIDTH/2-1 downto 0) := (others => '0');
  signal dac_tx_data_fal : std_logic_vector(DATA_BIT_WIDTH/2-1 downto 0) := (others => '0');
  signal dacd2_tx_frame_ddr_ris : std_logic := '0';
  signal dacd2_tx_frame_ddr_fal : std_logic := '0';

  attribute equivalent_register_removal : string;
  attribute equivalent_register_removal of dacd2_ch_sel : signal is "no";
  attribute equivalent_register_removal of dacd2_ch_sel_r : signal is "no";

begin

  -- backpressure / framing alignment
  dacd2_take_t1 <= '1' when (dacd2_ready_t1 = '1') and (dacd2_ch_sel(0) = T1) else '0';
  dacd2_take_t2 <= '1' when (dacd2_ready_t2 = '1') and (dacd2_ch_sel(0) = T2) else '0';

  -- needed loop because we're manually duplicating dacd2_ch_sel reg
  -- to aid in timing
  reg_duplication_loop : for idx in (DATA_BIT_WIDTH-1) downto 0 generate
    regs : process(dacd2_clk)
    begin
      if rising_edge(dacd2_clk) then
        if (dacd2_ch_sel(idx) = T2) or (dacd2_two_r_two_t_en = '1') then
          dacd2_ch_sel(idx) <= T1;
        else
          dacd2_ch_sel(idx) <= T2;
        end if;
        dacd2_ch_sel_r(idx) <= dacd2_ch_sel(idx);
        if (dacd2_ready_t1 = '1') and (dacd2_ch_sel(idx) = T1) then
          dacd2_i_t1_r(idx) <= dacd2_i_t1(idx);
          dacd2_q_t1_r(idx) <= dacd2_q_t1(idx);
        end if;
        if (dacd2_ready_t2 = '1') and (dacd2_ch_sel(idx) = T2) then
          dacd2_i_t2_r(idx) <= dacd2_i_t2(idx);
          dacd2_q_t2_r(idx) <= dacd2_q_t2(idx);
        end if;
      end if;
    end process;

    -- channel serialization mux (chan 0 one dacd2_clk, chan 1 next dacd2_clk)
    dacd2_i_r(idx) <= dacd2_i_t1_r(idx) when (dacd2_ch_sel_r(idx) = T1) else
                      dacd2_i_t2_r(idx);
    dacd2_q_r(idx) <= dacd2_q_t1_r(idx) when (dacd2_ch_sel_r(idx) = T1) else
                      dacd2_q_t2_r(idx);
  end generate reg_duplication_loop;

  dacd2_i_hi_r <= dacd2_i_r(DATA_BIT_WIDTH-1 downto DATA_BIT_WIDTH/2);
  dacd2_q_hi_r <= dacd2_q_r(DATA_BIT_WIDTH-1 downto DATA_BIT_WIDTH/2);
  dacd2_i_lo_r <= dacd2_i_r(DATA_BIT_WIDTH/2-1 downto 0);
  dacd2_q_lo_r <= dacd2_q_r(DATA_BIT_WIDTH/2-1 downto 0);

  -- 12-bit word-> 6-bit word serialization registers (high 6 bits one
  -- DATA_CLK_P, low 6 bits next DATA_CLK_P)
  word_serial_regs : process(dac_clk)
  begin
    if rising_edge(dac_clk) then
      if (dacd2_clk = '1') then
        -- CDC between clocks that have a fixed-phase relationship, so there is no expected
        -- metastability here (relying on static timing analysis to identify setup/hold violations)
        dac_tx_data_ris <= dacd2_i_hi_r;
        dac_tx_data_fal <= dacd2_q_hi_r;
      else
        -- CDC between clocks that have a fixed-phase relationship, so there is no expected
        -- metastability here (relying on static timing analysis to identify setup/hold violations)
        dac_tx_data_ris <= dacd2_i_lo_r;
        dac_tx_data_fal <= dacd2_q_lo_r;
      end if;
    end if;
  end process;

  -- backpressure / framing alignment
  tx_frame_toggle_reg : process(dacd2_clk)
  begin
    if rising_edge(dacd2_clk) then
      if (dacd2_two_r_two_t_en = '1') then
        -- chose dacd2_ch_sel idx 0 but we could have done any idx
        if (dacd2_ch_sel(0) = T1) then
          dacd2_tx_frame_ddr_ris <= '1';
        else
          dacd2_tx_frame_ddr_ris <= '0';
        end if;
        if (dacd2_ch_sel(0) = T1) then
          dacd2_tx_frame_ddr_fal <= '1';
        else
          dacd2_tx_frame_ddr_fal <= '0';
        end if;
      else
        dacd2_tx_frame_ddr_ris <= '1';
        dacd2_tx_frame_ddr_fal <= '0';
      end if;
    end if;
  end process;

  -- an oddr primitive is used here because it improves timing slack and generally aligns the
  -- TX_FRAME with the data bus
  tx_frame_oddr : util.util.oddr
      port map(
        clk     => dac_clk,
        rst     => '0',
        din_ris => dacd2_tx_frame_ddr_ris,
        din_fal => dacd2_tx_frame_ddr_fal,
        ddr_out => dacddr_tx_frame);

  tx_data_oddr : util.util.oddr_slv
    generic map(
      BIT_WIDTH => DATA_BIT_WIDTH/2)
    port map(
      clk     => dac_clk,
      rst     => '0',
      din_ris => dac_tx_data_ris,
      din_fal => dac_tx_data_fal,
      ddr_out => dacddr_tx_data);

end rtl;
