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
library util, unisim;

entity lvds_clock_buffer is
  port(
    data_clk_p : in  std_logic;
    data_clk_n : in  std_logic;
    oclk       : out std_logic);
end entity lvds_clock_buffer;

architecture rtl of lvds_clock_buffer is

  signal data_clk_s   : std_logic := '0';
  signal data_clk_n_s : std_logic := '0';

begin

  data_clk : util.util.BUFFER_IN_1
    generic map(
      DIFFERENTIAL => true)
    port map(
      I    => data_clk_p,
      IBAR => data_clk_n,
      O    => data_clk_s);

  -- inverter is necessary for (LVDS) DAC timing to be met (additional clock
  -- propagation delay is helpful)
  -- TODO/FIXME - investigate increasing FB_CLK_Delay to remedy this problem instead of using an inverter
  data_clk_n_s <= not data_clk_s;

  -- BUFR required for (LVDS) timing to be met (BUFG would not meet timing)
  data_clk_buf_i : unisim.vcomponents.BUFR
    generic map(
      BUFR_DIVIDE => "BYPASS")
    port map(
      O   => oclk,
      CE  => '1',
      CLR => '0',
      I   => data_clk_n_s);

end rtl;
