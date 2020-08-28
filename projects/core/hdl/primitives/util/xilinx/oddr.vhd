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

library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;
library unisim;

entity oddr is
  port(
    clk     : in  std_logic;
    rst     : in  std_logic; -- synchronous w/ the rising clock edge
    din_ris : in  std_logic;
    din_fal : in  std_logic;
    ddr_out : out std_logic);
end entity oddr;

architecture rtl of oddr is
begin

  prim : unisim.vcomponents.ODDR
    generic map (
      DDR_CLK_EDGE => "SAME_EDGE",
      INIT         => '0',
      SRTYPE       => "SYNC")
    port map (
      Q  => ddr_out,
      C  => clk,
      CE => '1',
      D1 => din_ris,
      D2 => din_fal,
      R  => rst,
      S  => '0');

end rtl;
