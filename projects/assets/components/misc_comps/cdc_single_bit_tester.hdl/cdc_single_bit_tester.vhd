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

library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all; use ieee.math_real.all;
library ocpi; use ocpi.types.all,  ocpi.util.all; -- remove this to avoid all ocpi name collisions
library misc_prims; use misc_prims.misc_prims.all;

-- TODO: Replace four_bit_lfsr with a generic lfsr and add a mode
-- for fast source to slow destination that intentionally doesn't hold input data
-- long enough show that it fails when the primitive is not properly used.
architecture rtl of worker is

  constant c_src_clk_hz : real := from_float(src_clk_hz);
  constant c_dst_clk_hz : real := from_float(dst_clk_hz);
  constant c_src_dst_ratio : real := c_src_clk_hz/c_dst_clk_hz;
  constant c_num_output_samples : natural := calc_cdc_bit_dst_fifo_depth(c_src_dst_ratio, to_integer(num_input_samples));
  constant c_fifo_depth : natural := 2**width_for_max(c_num_output_samples -1);
  constant c_hold_width : natural := natural(ceil((c_src_dst_ratio)*2.0));
  constant c_width : natural := 4;

  signal s_src_clk : std_logic;
  signal s_src_rst : std_logic := '0';
  signal s_dst_clk : std_logic;
  signal s_dst_rst : std_logic := '0';
  signal s_data_gen_en  : std_logic := '0';

  signal s_advance   : std_logic := '0';
  signal s_synced_dst_to_scr_rst : std_logic := '0';
  signal s_synced_src_to_dst_rst : std_logic := '0';
  signal s_not_synced_dst_to_scr_rst : std_logic := '0';
  signal s_one_shot_fifo_en : std_logic := '0';
  signal s_data_vld : std_logic := '0';
  signal s_done : std_logic := '0';

  signal s_bit_data_gen_out : std_logic_vector(c_width-1 downto 0) := (others => '0');
  signal s_bit_src_in : std_logic := '0';
  signal s_bit_dst_out : std_logic_vector(0 downto 0) := (others => '0');
  signal s_bit_fifo_dout : std_logic_vector(0 downto 0) := (others => '0');

  begin

  gen_clk : entity work.gen_clk
       generic map (src_clk_hz => c_src_clk_hz,
                    dst_clk_hz => c_dst_clk_hz)
       port map (
               ctl_clk => ctl_in.clk,
               ctl_rst => ctl_in.reset,
               src_clk => s_src_clk,
               src_rst => s_src_rst,
               dst_clk => s_dst_clk,
               dst_rst => s_dst_rst);

  gen_reset_sync : misc_prims.misc_prims.gen_reset_sync
      generic map (src_clk_hz => c_src_clk_hz,
                   dst_clk_hz => c_dst_clk_hz)
      port map (
              src_clk => s_src_clk,
              src_rst => s_src_rst,
              dst_clk => s_dst_clk,
              dst_rst => s_dst_rst,
              synced_dst_to_scr_rst => s_synced_dst_to_scr_rst,
              synced_src_to_dst_rst => s_synced_src_to_dst_rst);

    out_out.clk <= s_dst_clk;

    gen_src_data : misc_prims.misc_prims.four_bit_lfsr
      port map (clk  => s_src_clk,
                rst  => s_src_rst,
                en   => s_data_gen_en,
                dout => s_bit_data_gen_out);

    s_bit_src_in <= s_bit_data_gen_out(0);

    cdc_bit : cdc.cdc.single_bit
      generic map (
        IREG      => '1',
        RST_LEVEL => '0')
      port map (
	      src_clk  => s_src_clk,
        src_rst  => s_src_rst,
        src_en   => '1',
        src_in   => s_bit_src_in,
        dst_clk  => s_dst_clk,
        dst_rst  => s_dst_rst,
        dst_out  => s_bit_dst_out(0));

    s_not_synced_dst_to_scr_rst <= not s_synced_dst_to_scr_rst;

    gen_advance_counter : if (c_src_clk_hz >= c_dst_clk_hz) generate
      advance_counter : misc_prims.misc_prims.advance_counter
        generic map (hold_width => c_hold_width)
        port map (clk => s_src_clk,
                  rst => s_src_rst,
                  en => s_not_synced_dst_to_scr_rst,
                  advance => s_advance);
    end generate gen_advance_counter;

    s_data_gen_en <= s_advance when (c_src_clk_hz >= c_dst_clk_hz) else not s_src_rst;
    s_one_shot_fifo_en <= not s_dst_rst when (c_src_clk_hz > c_dst_clk_hz) else not s_synced_src_to_dst_rst;

    one_shot_fifo : misc_prims.misc_prims.one_shot_fifo
      generic map(
        data_width => 1,
        fifo_depth => c_fifo_depth,
        num_output_samples => c_num_output_samples)
      port map(
        clk => s_dst_clk,
        rst => s_dst_rst,
        din  => s_bit_dst_out,
        en => s_one_shot_fifo_en,
        rdy => out_in.ready,
        data_vld => s_data_vld,
        done => s_done,
        dout => s_bit_fifo_dout);

    out_out.data(0) <= s_bit_fifo_dout(0);
    out_out.valid <= s_data_vld;
    out_out.eof <= s_done;

end rtl;
