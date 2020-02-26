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

library ieee; use ieee.std_logic_1164.all; use ieee.numeric_std.all; use ieee.math_real.all;

entity mmcm_100_to_100_50_and_25_top is
  port (
    clk_out_100_MHz : out STD_LOGIC;
    clk_out_50_MHz : out STD_LOGIC;
    clk_out_25_MHz : out STD_LOGIC;
    reset : in STD_LOGIC;
    locked : out STD_LOGIC;
    clk_in_100_MHz : in STD_LOGIC);
end entity mmcm_100_to_100_50_and_25_top;

architecture rtl of mmcm_100_to_100_50_and_25_top is


  component mmcm_100_to_100_50_and_25
    port(
     clk_in1           : in     std_logic;
     clk_out1          : out    std_logic;
     clk_out2          : out    std_logic;
     clk_out3          : out    std_logic;
     reset             : in     std_logic;
     locked            : out    std_logic);
  end component;

begin

 inst_mmcm_100_to_100_50_and_25 : component mmcm_100_to_100_50_and_25
	 port map (
   clk_in1 => clk_in_100_MHz,
   clk_out1 => clk_out_100_MHz,
   clk_out2 => clk_out_50_MHz,
   clk_out3 => clk_out_25_MHz,
   locked => locked,
   reset => reset);

end rtl;
