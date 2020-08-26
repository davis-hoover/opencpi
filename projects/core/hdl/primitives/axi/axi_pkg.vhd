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

-- This file contains axi-specific definitions, not dependeny on any particular parameterized interface.

library IEEE; use IEEE.std_logic_1164.all, ieee.numeric_std.all;
package axi_pkg is

subtype  Resp_t IS std_logic_vector(1 downto 0);
constant Resp_OKAY   : Resp_t := "00";
constant Resp_EXOKAY : Resp_t := "01";
constant Resp_SLVERR : Resp_t := "10";
constant Resp_DECERR : Resp_t := "11";

end package axi_pkg;
