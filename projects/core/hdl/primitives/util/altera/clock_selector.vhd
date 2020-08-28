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
library altera_mf;

entity clock_selector is
  port(
    async_select : in  std_logic;
    clk_in0      : in  std_logic;
    clk_in1      : in  std_logic;
    clk_out      : out std_logic);
end entity clock_selector;

architecture rtl of clock_selector is
  constant NUM_CLKS : positive := 2;
  signal inclk_s : std_logic_vector(NUM_CLKS-1 downto 0) := (others => '0');
  signal async_select_s : std_logic_vector(NUM_CLKS-1 downto 0) := (others => '0');
begin

  async_select_s(0) <= async_select;
  inclk_s <= clk_in1 & clk_in0;

  selector : altera_mf.altera_mf_components.altclkctrl
    generic map(
      clock_type       => "AUTO",
      number_of_clocks => NUM_CLKS)
    port map(
      clkselect => async_select_s,
      inclk     => inclk_s,
      outclk    => clk_out);     

end rtl;
