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

package body iqstream is

function to_slv(iq : in op_iq_t) return std_logic_vector is
begin
  return iq.data.i &
         iq.data.q;
end to_slv;

function from_slv(slv : in std_logic_vector) return op_iq_t is
  variable ret : op_iq_t;
begin
  ret.data.i := slv(ret.data.i'range);
  ret.data.q := slv(ret.data.q'range);
  return ret;
end from_slv;

function to_slv(protocol : in protocol_t) return std_logic_vector is
begin
  return to_slv(protocol.iq) &
         protocol.iq_vld;
end to_slv;

function from_slv(slv : in std_logic_vector) return protocol_t is
  variable ret : protocol_t;
begin
  ret.iq.data.i := slv(32 downto 17);
  ret.iq.data.q := slv(16 downto 1);
  ret.iq_vld    := slv(0);
  return ret;
end from_slv;

end iqstream;
