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
library ocpi; use ocpi.types.all;-- remove this to avoid all ocpi name collisions
library util; use util.util.all;


architecture rtl of worker is
  signal s_clk_out : std_logic;
  signal s_locked  : std_logic;
  signal s_not_locked : std_logic;
  signal s_not_locked_synced_data  : std_logic;
  signal doit : bool_t;
  signal out_in_rst_detected : std_logic;
  signal s_data_out : std_logic;
  signal s_ctr : unsigned(4 downto 0);
begin

    clock_gen : clocking.clocking.clock_generator
    generic map (
      CLK_PRIMITIVE          => Clock_Primitive,
      CLK_IN_FREQUENCY_MHz   => from_float(CLK_IN_FREQUENCY_MHz),
      CLK_OUT_FREQUENCY_MHz  => from_float(CLK_OUT_FREQUENCY_MHz),
      M                      => from_float(M),
      N                      => to_integer(unsigned(N)),
      O                      => from_float(O),
      CLK_OUT_DUTY_CYCLE     => from_float(CLKOUT_DUTY_CYCLE))
    port map(
      clk_in           =>    ctl_in.clk,
      reset            =>    ctl_in.reset,
      clk_out          =>    s_clk_out,
      locked           =>    s_locked);

    s_not_locked <= not s_locked;

    sync_not_locked_data : cdc.cdc.reset
      port map   (
        src_rst   => s_not_locked,
        dst_clk   => s_clk_out,
        dst_rst   => s_not_locked_synced_data);

    -- this worker is not initialized until s_clk_out is ticking and the out port
    -- has successfully come into reset
    rst_detector_reg_out_in_reset : util.util.reset_detector
      port map(
        clk                     => s_clk_out,
        rst                     => out_in.reset,
        clr                     => '0',
        rst_detected            => out_in_rst_detected,
        rst_then_unrst_detected => open);


    ctl_out.done <= out_in_rst_detected;
    out_out.eof <= '1' when (s_ctr = 20) else '0';
    doit <= out_in.ready and not s_not_locked_synced_data;
  -- WSI output interface outputs
    -- out_out.give <= doit;
    out_out.data <= x"0000_BEEF";
    -- out_out.som <= in_in.som;
    -- out_out.eom <= in_in.eom;
    out_out.valid <= doit when (s_ctr < 20) else '0';
    -- out_out.byte_enable <= in_in.byte_enable; -- only necessary due to BSV protocol sharing
    -- out_out.opcode <= in_in.opcode;
    out_out.clk <= s_clk_out;


    process(s_clk_out)
    begin
      if(rising_edge(s_clk_out)) then
        if(out_in.reset = '1') then
          s_ctr <= (others=>'0');
        elsif (doit = '1' and s_ctr < 20) then
          s_ctr <= s_ctr + 1;
        end if;
      end if;
    end process;



end rtl;
