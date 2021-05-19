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

-- TODO / FIXME - this is a primitive-with-shadowing candidate
library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;
library unisim; -- BUFGMUX_CTRL

entity clock_selector_with_async_select is
  port(
    async_select : in  std_logic;
    clk_in0      : in  std_logic;
    clk_in1      : in  std_logic;
    clk_out      : out std_logic);
end entity clock_selector_with_async_select;

architecture rtl of clock_selector_with_async_select is
begin

  -- With BUFGMUX "glitches or short pulses can appear on the output" when setup/hold is not met for
  -- the select.
  -- BUFGMUX_CTRL, however, does not have this shortcoming, implying that select is allowed to be
  -- asynchronous.
  -- For more info see Xilinx UG472.
  bufgmux : unisim.vcomponents.BUFGMUX_CTRL
    port map(
      O  => clk_out,
      I0 => clk_in0,
      I1 => clk_in1,
      S  => async_select);

end rtl;
