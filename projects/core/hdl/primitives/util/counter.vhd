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

entity counter is
  generic(
    BIT_WIDTH : positive);
  port(
    clk      : in  std_logic;
    rst      : in  std_logic;
    en       : in  std_logic;
    cnt      : out unsigned(BIT_WIDTH-1 downto 0));
end entity counter;
architecture rtl of counter is
  signal cnt_s : unsigned(BIT_WIDTH-1 downto 0) := (others => '0');
begin

  process(clk)
  begin
    if(rising_edge(clk)) then
      if(rst = '1') then
        cnt_s <= (others => '0');
      elsif(en = '1') then
        cnt_s <= cnt_s + 1;
      end if;
    end if;
  end process;

  cnt <= cnt_s;

end rtl;
