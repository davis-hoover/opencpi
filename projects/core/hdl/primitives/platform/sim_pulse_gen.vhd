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

-- Generate PPS signal of width g_pps_width
-- PPS is only produced after g_pps_delay
library ieee; use ieee.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi; use ocpi.types.all; use ocpi.util.all;

entity sim_pulse_gen is
  generic (
    g_clk_period   : time     := 10 ns;
    g_pulse_period : time     := 1000 ms;
    g_pulse_width  : positive := 16       -- num of g_clk_periods pulse is high 
  );
  port (
    i_reset        : in std_logic;
    o_pulse        : out std_logic
  );
end sim_pulse_gen;

architecture rtl of sim_pulse_gen is
  constant c_high_time : time := g_pulse_width * g_clk_period;
  constant c_low_time  : time := g_pulse_period - c_high_time;
begin

  process
  begin
    wait until i_reset = '0';
    loop
      o_pulse <= '1';
      wait until i_reset = '1' for c_high_time;
      o_pulse <= '0';
      wait until i_reset = '1' for c_low_time;
    end loop;
  end process;

end rtl;
