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
library ieee; use ieee.std_logic_1164.all; use ieee.numeric_std.all;

package body complex_short_with_metadata is

function to_slv(samples : in op_samples_t) return std_logic_vector is
begin
  return samples.iq.i &
         samples.iq.q;
end to_slv;

function from_slv(slv : in std_logic_vector) return op_samples_t is
  variable ret : op_samples_t;
begin
  ret.iq.i := slv(ret.iq.i'range);
  ret.iq.q := slv(ret.iq.q'range);
  return ret;
end from_slv;

function to_slv(time : in op_time_t) return std_logic_vector is
begin
  return time.fract_sec &
         time.sec;
end to_slv;

function from_slv(slv : in std_logic_vector) return op_time_t is
  variable ret : op_time_t;
begin
  ret.fract_sec := slv(ret.fract_sec'range);
  ret.sec       := slv(ret.sec'range);
  return ret;
end from_slv;

function to_slv(interval : in op_interval_t) return std_logic_vector is
begin
  return interval.delta_time;
end to_slv;

function from_slv(slv : in std_logic_vector) return op_interval_t is
  variable ret : op_interval_t;
begin
  ret.delta_time := slv;
  return ret;
end from_slv;

function to_slv(protocol : in protocol_t) return std_logic_vector is
begin
  return to_slv(protocol.samples) &
         protocol.samples_vld &
         to_slv(protocol.time) &
         protocol.time_vld &
         to_slv(protocol.interval) &
         protocol.interval_vld &
         protocol.flush &
         protocol.sync &
         protocol.end_of_samples;
end to_slv;

function from_slv(slv : in std_logic_vector) return protocol_t is
  variable ret : protocol_t;
begin
  ret.samples.iq.i        := slv(165 downto 150);
  ret.samples.iq.q        := slv(149 downto 134);
  ret.samples_vld         := slv(133);
  ret.time.fract_sec      := slv(132 downto 101);
  ret.time.sec            := slv(100 downto 69);
  ret.time_vld            := slv(68);
  ret.interval.delta_time := slv(67 downto 4);
  ret.interval_vld        := slv(3);
  ret.flush               := slv(2);
  ret.sync                := slv(1);
  ret.end_of_samples      := slv(0);
  return ret;
end from_slv;

end complex_short_with_metadata;
