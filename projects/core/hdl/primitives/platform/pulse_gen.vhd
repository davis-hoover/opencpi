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

-- Generate pulse signal of width g_pulse_width i_clk cycles of period
-- g_pulse_period i_clk cycles
library ieee; use ieee.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi; use ocpi.types.all; use ocpi.util.all;

entity pulse_gen is
  generic (
    g_pulse_period : positive := 100000000;
    g_pulse_width  : positive := 16;
    g_pulse_delay  : natural := 0
  );
  port (
    i_clk          : in std_logic;
    i_reset        : in std_logic;
    o_pulse        : out std_logic
  );
end pulse_gen;

architecture rtl of pulse_gen is
  constant c_cnt_width : positive := width_for_max(g_pulse_period);
  signal   cnt         : unsigned(c_cnt_width-1 downto 0);
begin

  assert (g_pulse_delay < g_pulse_period) report "g_pulse_delay must be less than g_pulse_period" severity failure;
  
  process(i_clk)
  begin
    if rising_edge(i_clk) then
      if its(i_reset) then
        cnt <= to_unsigned(g_pulse_period - g_pulse_delay,c_cnt_width);
      elsif cnt = g_pulse_period then 
        cnt <= (others => '0');
      else
        cnt <= cnt + 1;
      end if;
    end if;
  end process;

  o_pulse <= to_bool(cnt < g_pulse_width) and not i_reset;
  
end rtl;
