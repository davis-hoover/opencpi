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
-- This implements AD9361_Reference_Manual_UG-570.pdf Figure 69. Transmit
-- Data Path, Single Port FDD. The implementation is purely combinatorial up
-- until the DDR registers.
--
-- clock domains:
-- * dac    - AD9361 DATA_CLK
-- * dacddr - data output from DDR register whose input is in the data clock domain (sort of
--            equivalent to data clock multiplied by 2)
----------------------------------------------------------------------------------------------------

library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;
library util, dac; use dac.ad936x.all; -- note preference of dac.ad936x.DATA_BIT_WIDTH instead of dac.dac.DATA_BIT_WIDTH

entity ad936x_cmos_single_port_fdd_ddr_interleaver is
  port(
    dac_clk             : in  std_logic; -- AD9361 DATA_CLK
    dac_two_r_two_t_en  : in  std_logic; -- indicates whether 2R2T is to be used
    dac_i_t1            : in  std_logic_vector(DATA_BIT_WIDTH-1 downto 0);
    dac_q_t1            : in  std_logic_vector(DATA_BIT_WIDTH-1 downto 0);
    dac_i_t2            : in  std_logic_vector(DATA_BIT_WIDTH-1 downto 0);
    dac_q_t2            : in  std_logic_vector(DATA_BIT_WIDTH-1 downto 0);
    dac_ready_t1        : in  std_logic; -- data...{i,q}_t1 are valid and ready
    dac_ready_t2        : in  std_logic; -- data...{i,q}_t2 are valid and ready
    dac_take_t1         : out std_logic; -- facilitates backpressure for framing alignment
    dac_take_t2         : out std_logic; -- facilitates backpressure for framing alignment
    dacddr_tx_frame     : out std_logic; -- AD9361 TX_FRAME
    dacddr_tx_data      : out std_logic_vector(DATA_BIT_WIDTH/2-1 downto 0));
end entity ad936x_cmos_single_port_fdd_ddr_interleaver;

architecture rtl of ad936x_cmos_single_port_fdd_ddr_interleaver is

  type ch_sel_t    is (T1, T2);
  type hi_lo_sel_t is (LO, HI);
  signal dac_hi_lo_sel   : hi_lo_sel_t := LO;
  signal ch_toggle       : std_logic := '0';
  signal dac_ch_sel      : ch_sel_t := T1;
  signal dac_i           : std_logic_vector(DATA_BIT_WIDTH-1 downto 0) :=
                           (others => '0');
  signal dac_q           : std_logic_vector(DATA_BIT_WIDTH-1 downto 0) :=
                           (others => '0');
  signal dac_i_hi        : std_logic_vector(DATA_BIT_WIDTH/2-1 downto 0) :=
                           (others => '0');
  signal dac_q_hi        : std_logic_vector(DATA_BIT_WIDTH/2-1 downto 0) :=
                           (others => '0');
  signal dac_i_lo        : std_logic_vector(DATA_BIT_WIDTH/2-1 downto 0) :=
                           (others => '0');
  signal dac_q_lo        : std_logic_vector(DATA_BIT_WIDTH/2-1 downto 0) :=
                           (others => '0');
  signal dac_i_lo_r      : std_logic_vector(DATA_BIT_WIDTH/2-1 downto 0) :=
                           (others => '0');
  signal dac_q_lo_r      : std_logic_vector(DATA_BIT_WIDTH/2-1 downto 0) :=
                           (others => '0');
  signal dac_tx_frame    : std_logic := '0';
  signal dac_tx_data_ris : std_logic_vector(DATA_BIT_WIDTH/2-1 downto 0) :=
                           (others => '0');
  signal dac_tx_data_fal : std_logic_vector(DATA_BIT_WIDTH/2-1 downto 0) :=
                           (others => '0');

begin

  dac_hi_lo_sel_reg : process(dac_clk)
  begin
    if rising_edge(dac_clk) then
      if (dac_hi_lo_sel = HI) then
        dac_hi_lo_sel <= LO;
      else
        dac_hi_lo_sel <= HI;
      end if;
    end if;
  end process;

  ch_toggle_reg : process(dac_clk)
  begin
    if rising_edge(dac_clk) then
      if dac_hi_lo_sel = LO then
        ch_toggle <= not ch_toggle;
      end if;
    end if;
  end process;

  dac_ch_sel <= T2 when (ch_toggle = '1') and (dac_two_r_two_t_en = '1') else T1;

  -- backpressure / framing alignment
  dac_take_t1 <= '1' when (dac_ready_t1 = '1') and (dac_ch_sel = T1) and (dac_hi_lo_sel = LO) else '0';
  dac_take_t2 <= '1' when (dac_ready_t2 = '1') and (dac_ch_sel = T2) and (dac_hi_lo_sel = LO) else '0';

  dac_i <= dac_i_t2 when (dac_ch_sel = T2) else dac_i_t1;
  dac_q <= dac_q_t2 when (dac_ch_sel = T2) else dac_q_t1;

  dac_i_hi <= dac_i(DATA_BIT_WIDTH-1 downto DATA_BIT_WIDTH/2);
  dac_q_hi <= dac_q(DATA_BIT_WIDTH-1 downto DATA_BIT_WIDTH/2);
  dac_i_lo <= dac_i(DATA_BIT_WIDTH/2-1 downto 0);
  dac_q_lo <= dac_q(DATA_BIT_WIDTH/2-1 downto 0);

  -- because of hi/lo serialization, we delay lo to ensure that, by the time lo
  -- is serialized, it corresponds to the same previously serialized hi
  data_lo_delay_regs : process(dac_clk)
  begin
    if rising_edge(dac_clk) then
      if (dac_hi_lo_sel = HI) then
        dac_i_lo_r <= dac_i_lo;
        dac_q_lo_r <= dac_q_lo;
      end if;
    end if;
  end process;

  -- backpressure / framing alignment
  dac_tx_frame <= '1' when ((dac_two_r_two_t_en = '1') and (dac_ch_sel = T1)) or
                  (dac_hi_lo_sel = HI) else '0';

  dac_tx_data_ris <= dac_i_hi when (dac_hi_lo_sel = HI) else dac_i_lo_r;
  dac_tx_data_fal <= dac_q_hi when (dac_hi_lo_sel = HI) else dac_q_lo_r;

  -- an oddr primitive is used here because it improves timing slack and generally aligns the
  -- TX_FRAME with the data bus
  tx_frame_oddr : util.util.oddr
    port map(
      clk     => dac_clk,
      rst     => '0',
      din_ris => dac_tx_frame,
      din_fal => dac_tx_frame,
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
