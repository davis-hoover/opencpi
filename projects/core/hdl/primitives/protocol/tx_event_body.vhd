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

package body tx_event is

function to_slv(protocol : in protocol_t) return std_logic_vector is
begin
  return protocol.txOff &
         protocol.txOn;
end to_slv;

function from_slv(slv : in std_logic_vector) return protocol_t is
  variable ret : protocol_t;
begin
  ret.txOff := slv(1);
  ret.txOn  := slv(0);
  return ret;
end from_slv;

end tx_event;
