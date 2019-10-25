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

-- TODO: Replace four_bit_lfsr with a generic lfsr
architecture rtl of worker is

  constant c_sim_src_clk_hz : real := from_float(sim_src_clk_hz);
  constant c_sim_dst_clk_hz : real := from_float(sim_dst_clk_hz);
  constant c_hw_src_dst_clk_ratio : real := from_float(hw_src_dst_clk_ratio);
  constant c_src_dst_ratio : real := src_dst_ratio(c_sim_src_clk_hz, c_sim_dst_clk_hz, simulation, c_hw_src_dst_clk_ratio);
  constant c_num_output_samples : natural := calc_cdc_bit_dst_fifo_depth(c_src_dst_ratio, to_integer(num_input_samples));
  constant c_fifo_depth : natural := 2**width_for_max(c_num_output_samples -1);
  constant c_hold_width : natural := natural(ceil((c_src_dst_ratio)*2.0));
  constant c_lfsr_width : natural := 4;
  constant c_bits_data_gen_seed : std_logic_vector(15 downto 0) := x"8421";

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


  signal s_bits_fifo_dout : std_logic_vector(c_lfsr_width-1 downto 0) := (others => '0');
  signal s_bits_src_in : std_logic_vector(c_lfsr_width-1 downto 0) := (others => '0');
  signal s_bits_dst_out : std_logic_vector(c_lfsr_width-1 downto 0) := (others => '0');
  signal s_bits_data_gen_out : std_logic_vector(15 downto 0) := (others => '0');

  begin

   gen_clk : misc_prims.misc_prims.gen_clk
      generic map (sim_src_clk_hz => c_sim_src_clk_hz,
                   sim_dst_clk_hz => c_sim_dst_clk_hz,
                   simulation => simulation,
                   hw_src_dst_clk_ratio => c_hw_src_dst_clk_ratio)
      port map (
              ctl_clk => ctl_in.clk,
              ctl_rst => ctl_in.reset,
              src_clk => s_src_clk,
              src_rst => s_src_rst,
              dst_clk => s_dst_clk,
              dst_rst => s_dst_rst);

   gen_reset_sync : misc_prims.misc_prims.gen_reset_sync
      generic map (sim_src_clk_hz => c_sim_src_clk_hz,
                   sim_dst_clk_hz => c_sim_dst_clk_hz,
                   simulation => simulation,
                   hw_src_dst_clk_ratio => c_hw_src_dst_clk_ratio)
      port map (
              src_clk => s_src_clk,
              src_rst => s_src_rst,
              dst_clk => s_dst_clk,
              dst_rst => s_dst_rst,
              synced_dst_to_scr_rst => s_synced_dst_to_scr_rst,
              synced_src_to_dst_rst => s_synced_src_to_dst_rst);

    out_out.clk <= s_dst_clk;

    input_gen : for i in 0 to c_lfsr_width-1 generate
      gen_src_data : misc_prims.misc_prims.four_bit_lfsr
        generic map (SEED => c_bits_data_gen_seed((i*4)+3 downto i*4))
        port map (clk => s_src_clk,
                  rst => s_src_rst,
                  en => s_data_gen_en,
                  dout => s_bits_data_gen_out((i*4)+4-1 downto i*4));

      s_bits_src_in(i) <= s_bits_data_gen_out((i*c_lfsr_width));

    end generate input_gen;

    cdc_bits : cdc.cdc.bits
      generic map (
        N         => 2,
        IREG      => '1',
        RST_LEVEL => '0',
        WIDTH     => c_lfsr_width)
      port map   (
        src_clk => s_src_clk,
        src_rst => s_src_rst,
        src_in  => s_bits_src_in,
        dst_clk => s_dst_clk,
        dst_rst => s_dst_rst,
        dst_out => s_bits_dst_out);

    s_not_synced_dst_to_scr_rst <= not s_synced_dst_to_scr_rst;

    gen_advance_counter : if (c_src_dst_ratio >= 1.0) generate
      advance_counter : misc_prims.misc_prims.advance_counter
       generic map (hold_width => c_hold_width)
       port map (clk => s_src_clk,
                 rst => s_src_rst,
                 en => s_not_synced_dst_to_scr_rst,
                 advance => s_advance);
     end generate gen_advance_counter;

    s_data_gen_en <= s_advance  when (c_src_dst_ratio >= 1.0) else not s_src_rst;


    s_one_shot_fifo_en <= not s_dst_rst when (c_src_dst_ratio > 1.0) else not s_synced_src_to_dst_rst;

    one_shot_fifo : misc_prims.misc_prims.one_shot_fifo
      generic map(
        data_width => c_lfsr_width,
        fifo_depth => c_fifo_depth,
        num_output_samples => c_num_output_samples)
      port map(
        clk => s_dst_clk,
        rst => s_dst_rst,
        din  => s_bits_dst_out,
        en => s_one_shot_fifo_en,
        rdy => out_in.ready,
        data_vld => s_data_vld,
        done => s_done,
        dout => s_bits_fifo_dout);

    out_out.data(c_lfsr_width-1 downto 0) <= s_bits_fifo_dout;
    out_out.valid <= s_data_vld;
    out_out.eof <= s_done;


end rtl;
