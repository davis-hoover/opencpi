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

-- The purpose of this worker is to test the time server
library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi; use ocpi.types.all; -- remove this to avoid all ocpi name collisions
architecture rtl of worker is
  signal frac_rollover_detected : bool_t;
  signal finished               : bool_t;
  signal last_sec               : ulong_t;
  signal last_frac              : ulong_t;
begin
  process(ctl_in.clk)
  begin
    if rising_edge(ctl_in.clk) then
      if its(ctl_in.reset) then
        props_out.timestamp_sec  <= (others => (others => '0'));
        props_out.timestamp_frac <= (others => (others => '0'));
        finished <= bfalse;
      elsif its(ctl_in.is_operating) then 
        if its(not finished) then
          last_sec  <= time_in.seconds;
          last_frac <= time_in.fraction;
          props_out.timestamp_sec(0)  <= time_in.seconds;
          props_out.timestamp_frac(0) <= time_in.fraction;
          props_out.timestamp_frac(1) <= last_sec;
          props_out.timestamp_frac(1) <= last_frac;
          if props_in.mode = valid_e and its(time_in.valid) then
            finished <= btrue;
          elsif props_in.mode = rollover_e and its(frac_rollover_detected) then
            finished <= btrue;
          end if;
        end if;
      end if;
    end if;
  end process;

  frac_rollover_detected <= to_bool(time_in.fraction(31) = '0') and to_bool(last_frac(31) = '1');
  ctl_out.finished <= finished;
end rtl;
