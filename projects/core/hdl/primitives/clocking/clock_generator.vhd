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

----------------------------------------------------------------------------------
-- Description
----------------------------------------------------------------------------------
-- This is a vendor agnostic clock generator. It simulates waiting for a period of
-- of time for a clock generator to receive "lock" before having a valid clock.
----------------------------------------------------------------------------------

library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all, ieee.math_real.all;
library ocpi; use ocpi.util.all, ocpi.types.all;
library platform;
library cdc;

entity clock_generator is
    generic (
      CLK_PRIMITIVE          : string_t := to_string("", 32);
      CLK_IN_FREQUENCY_MHz   : real := 100.0;
      CLK_OUT_FREQUENCY_MHz  : real := 100.0;
      M                      : real := 5.0;  -- M
      N                      : integer := 1; -- D
      O                      : real := 1.0;  -- O
   -- CLK_OUT_PHASE_DEGREES  : real; -- Add this in when there's a generalized way to support Xilinx and Intel phase shift in optimization script
      CLK_OUT_DUTY_CYCLE     : real := 0.5);
    port(
      clk_in           : in     std_logic;
      reset            : in     std_logic;
      clk_out          : out    std_logic;
      locked           : out    std_logic);
end entity clock_generator;

architecture rtl of clock_generator is
  constant c_num_cycles       : natural := 33;
  constant c_counter_width    : natural := width_for_max(c_num_cycles - 1);
  signal s_reset_out          : std_logic;
  signal s_clk_out            : std_logic;
  signal s_counter            : unsigned(c_counter_width-1 downto 0);
  signal s_enable             : std_logic;
  signal s_locked             : std_logic;
  signal s_reset_in_synced    : std_logic;
begin

  inst_sim_clk : platform.platform_pkg.sim_clk
  generic map(frequency => CLK_OUT_FREQUENCY_MHz*1.0E6,
             offset  => 0)
  port map(
    clk   => s_clk_out,
    reset => s_reset_out);

  s_enable <= '1' when  (s_reset_in_synced = '0' and s_counter < c_num_cycles) else '0';
  s_locked <= '1' when (s_counter = c_num_cycles) else '0';
  clk_out <=  s_clk_out when (s_locked ='1') else '0';
  locked <= s_locked;

  sync_reset_in : cdc.cdc.reset
    port map   (
      src_rst   => reset,
      dst_clk   => s_clk_out,
      dst_rst   => s_reset_in_synced);

  process(s_clk_out)
  begin
    if rising_edge(s_clk_out) then
      if (s_reset_out = '1') then
        s_counter <= (others=>'0');
      elsif (s_enable = '1') then
        s_counter <= s_counter + 1;
      end if;
    end if;
  end process;

end rtl;
