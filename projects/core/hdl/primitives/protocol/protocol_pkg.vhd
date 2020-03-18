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
library ieee; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
package protocol is

-- TODO / FIXME - include mechanism for assessment of port buffer size
component message_sizer is
  generic(
    SIZE_BIT_WIDTH : positive);
  port(
    clk                    : in  std_logic;
    rst                    : in  std_logic;
    give                   : in  std_logic;
    message_size_num_gives : in  unsigned(SIZE_BIT_WIDTH-1 downto 0);
    som                    : out std_logic;
    eom                    : out std_logic);
end component;

end package protocol;
