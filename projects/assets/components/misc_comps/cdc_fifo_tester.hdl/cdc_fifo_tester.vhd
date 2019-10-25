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

  component mmcm_100_to_50_and_25
    port(
      clk_in1           : in     std_logic;
      clk_out1          : out    std_logic;
      clk_out2          : out    std_logic;
      reset             : in     std_logic;
      locked            : out    std_logic);
  end component;


  constant c_sim_src_clk_hz : real := from_float(sim_src_clk_hz);
  constant c_sim_dst_clk_hz : real := from_float(sim_dst_clk_hz);
  constant c_hw_src_dst_clk_ratio : real := from_float(hw_src_dst_clk_ratio);
  constant c_src_dst_ratio : real := src_dst_ratio(c_sim_src_clk_hz, c_sim_dst_clk_hz, simulation, c_hw_src_dst_clk_ratio);
  constant c_cdc_fifo_depth : natural := 2**width_for_max(calc_cdc_fifo_depth(c_src_dst_ratio)-1);
  constant c_lfsr_width : natural := 4;

  signal s_src_clk : std_logic;
  signal s_src_rst : std_logic := '0';
  signal s_dst_clk : std_logic;
  signal s_dst_rst : std_logic := '0';

  signal s_fifo_not_full : std_logic := '0';
  signal s_fifo_not_empty : std_logic := '0';
  signal s_fifo_enq : std_logic := '0';
  signal s_fifo_deq : std_logic := '0';
  signal s_dst_counter : unsigned(width_for_max(to_integer(num_input_samples) -1) downto 0) := (others => '0');
  signal s_fifo_data_gen_out : std_logic_vector(c_lfsr_width-1 downto 0) := (others => '0');
  signal s_fifo_dst_out : std_logic_vector(c_lfsr_width-1 downto 0) := (others => '0');
  signal s_clk_out1 : std_logic;
  signal s_clk_out2 : std_logic;
  signal s_locked : std_logic;
  signal s_not_locked : std_logic;

  begin
    s_src_clk <= ctl_in.clk;
    s_not_locked <= not s_locked;
    inst_mmcm_100_to_50_and_25 : component mmcm_100_to_50_and_25
     port map (
      clk_in1 => ctl_in.clk,
      clk_out1 => s_dst_clk,
      clk_out2 => open,
      reset => ctl_in.reset,
      locked => s_locked);

      reset_sync_s_not_locked_to_dst : cdc.cdc.reset
        port map   (
          src_rst   => s_not_locked,
          dst_clk   => s_dst_clk,
          dst_rst   => s_dst_rst);

      reset_sync_s_not_locked_to_src : cdc.cdc.reset
        port map   (
          src_rst   => s_not_locked,
          dst_clk   => s_src_clk,
          dst_rst   => s_src_rst);

  -- gen_clk : misc_prims.misc_prims.gen_clk
  --     generic map (sim_src_clk_hz => c_sim_src_clk_hz,
  --                  sim_dst_clk_hz => c_sim_dst_clk_hz,
  --                  simulation => simulation,
  --                  hw_src_dst_clk_ratio => c_hw_src_dst_clk_ratio)
  --     port map (
  --             ctl_clk => ctl_in.clk,
  --             ctl_rst => ctl_in.reset,
  --             src_clk => s_src_clk,
  --             src_rst => s_src_rst,
  --             dst_clk => s_dst_clk,
  --             dst_rst => s_dst_rst);

    out_out.clk <= s_dst_clk;

    gen_src_data : misc_prims.misc_prims.four_bit_lfsr
      port map (clk  => s_src_clk,
                rst  => s_src_rst,
                en   => s_fifo_enq,
                dout => s_fifo_data_gen_out);

    s_fifo_enq <= s_fifo_not_full;
    cdc_fifo : cdc.cdc.fifo
        generic map (
          WIDTH       => c_lfsr_width,
          DEPTH       => c_cdc_fifo_depth)
        port map (
          src_CLK     => s_src_clk,
          src_RST     => s_src_rst,
          src_ENQ     => s_fifo_enq,
          src_in      => s_fifo_data_gen_out,
          src_FULL_N  => s_fifo_not_full,
          dst_CLK     => s_dst_clk,
          dst_DEQ     => s_fifo_deq,
          dst_out     => s_fifo_dst_out,
          dst_EMPTY_N => s_fifo_not_empty);

      s_fifo_deq <= s_fifo_not_empty and out_in.ready when (s_dst_counter < num_input_samples) else '0';

      process(s_dst_clk)
      begin
        if rising_edge(s_dst_clk) then
          if (s_dst_rst = '1') then
            s_dst_counter <= (others=>'0');
          elsif (s_fifo_deq = '1') then
            s_dst_counter <= s_dst_counter + 1;
          end if;
        end if;
      end process;

      out_out.data(c_lfsr_width-1 downto 0) <= s_fifo_dst_out;
      out_out.valid <= s_fifo_deq when (s_dst_counter < num_input_samples) else '0';
      out_out.eof <= '1' when (s_dst_counter = num_input_samples) else '0';



end rtl;
