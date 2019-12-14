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

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

-- Implementation of standard lsfr with polynomial x^4 +x^3 + 1
-- Shifts from lsb to msb
entity four_bit_lfsr is
    generic (
        SEED : std_logic_vector := "1000");
    port (
        clk     : in std_logic;
        rst     : in std_logic;
        en      : in std_logic;
        dout    : out std_logic_vector);

end entity four_bit_lfsr;

architecture rtl of four_bit_lfsr is

    signal s_lfsr_data : std_logic_vector(3 downto 0);

begin

  dout <= s_lfsr_data;
  process (clk)
  begin
    if rising_edge(clk) then
      if (rst = '1') then
        s_lfsr_data <= SEED;
      elsif (en = '1') then
        s_lfsr_data <= s_lfsr_data(2 downto 0) & (s_lfsr_data(3) xor s_lfsr_data(2));
      end if;
    end if;
  end process;

end rtl;
