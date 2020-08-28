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
library util;

entity oddr_slv is
  generic(
    BIT_WIDTH : positive);
  port(
    clk       : in  std_logic;
    rst       : in  std_logic; -- synchronous w/ the rising clock edge
    din_ris   : in  std_logic_vector(BIT_WIDTH-1 downto 0);
    din_fal   : in  std_logic_vector(BIT_WIDTH-1 downto 0);
    ddr_out   : out std_logic_vector(BIT_WIDTH-1 downto 0));
end entity oddr_slv;

architecture rtl of oddr_slv is

  signal ddr_out_s : std_logic := '0';

begin

  reg_loop : for idx in BIT_WIDTH-1 downto 0 generate
  begin
    reg : util.util.oddr
      port map(
        clk     => clk,
        rst     => '0',
        din_ris => din_ris(idx),
        din_fal => din_fal(idx),
        ddr_out => ddr_out(idx));
  end generate;

end rtl;
