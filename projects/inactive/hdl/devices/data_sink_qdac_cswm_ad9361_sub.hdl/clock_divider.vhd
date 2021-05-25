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
library unisim;

entity clock_divider is
  generic(
    DIVIDER_TYPE : string  := "BUFFER"; -- "BUFFER", "REGISTER"
    ROUTABILITY  : string  := "GLOBAL"; -- "GLOBAL", "REGIONAL"
    DIVISOR      : string  := "2");
  port(
    clk_in  : in  std_logic;
    clk_out : out std_logic);
end entity clock_divider;

architecture rtl of clock_divider is
  signal reg_out : std_logic := '0';
begin

  divider_type_buffer : if(DIVIDER_TYPE = "BUFFER") generate
    routability_regional : if(ROUTABILITY = "REGIONAL") generate
      buffer_and_divider : unisim.vcomponents.BUFR
        generic map(
          BUFR_DIVIDE => DIVISOR)
        port map(
          O   => clk_out,
          CE  => '1',
          CLR => '0',
          I   => clk_in);
    end generate routability_regional;
  end generate divider_type_buffer;

  -- use of a register to generate a divide-by-two-clock is a perfectly valid
  -- design practice according to Xilinx - see
  -- https://www.xilinx.com/support/documentation/sw_manuals/xilinx2017_1/ug903-vivado-using-constraints.pdf#G5.365789
  -- (particularly "Figure 3-5: Generated Clock Example One")
  divider_type_register : if(DIVIDER_TYPE = "REGISTER") generate
    routability_global : if(ROUTABILITY = "GLOBAL") generate
      divisor_2 : if(DIVISOR = "2") generate
        process(clk_in)
        begin
          if(rising_edge(clk_in)) then
            reg_out <= not reg_out;
          end if;
        end process;
        clk_out <= reg_out;
      end generate divisor_2;
    end generate routability_global;
  end generate divider_type_register;

end rtl;
