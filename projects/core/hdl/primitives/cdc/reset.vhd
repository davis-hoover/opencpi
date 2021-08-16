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
---------------------------------------------------------------------------------
--
-- Asynchronous "Reset Synchronizer"
--
-- Description:
--  Level Synchronizer (Input and Output are Level signals)
--  Open-loop solution (i.e. without Feedback Acknowledgement)
--
--  Reset assertion is asynchronous, while deassertion is synchronized to the clock.
--  The width of the reset signal is at least (RSTDELAY * dest_clk) period.
--  It can take either an active low or high reset and outputs both an active low and
--  high reset.
--
-- Generics:
--  SRC_RST_VALUE : Value of source reset used to asynchronously assert
--  s_reset_hold. Default is 1.
--  0 - Active low source reset
--  1 - Active high source reset
--  RSTDELAY : Depth of shift register. The minimum allowed value is 2.
--
-- Background:
--  - "Reset Synchronizer" in
--    http://www.sunburst-design.com/papers/CummingsSNUG2002SJ_Resets.pdf.
--  - Matches the performance of Xilinx XPM: xpm_cdc_async_rst module.
--  - VHDL replacement for Blue-Spec generated Verilog module, "SyncResetA.v",
--    with the execption that it holds the output active for 1 less clock cycle.
--
---------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity reset is
  generic (
    SRC_RST_VALUE : std_logic :='1';
    RST_DELAY     : integer := 2);        -- Depth of shift register.
  port (
    src_rst   : in  std_logic;
    dst_clk   : in  std_logic;
    dst_rst   : out std_logic;  -- active high reset
    dst_rst_n : out std_logic); -- active low reset
end entity reset;

architecture rtl of reset is

  signal s_reset_hold : std_logic_vector(RST_DELAY-1 downto 0) := (others => '1');

begin

  dst_rst <= s_reset_hold(s_reset_hold'length-1);
  dst_rst_n <= not s_reset_hold(s_reset_hold'length-1);

  sync : process (dst_clk, src_rst)
  begin
    if src_rst = SRC_RST_VALUE then    --async assert of output
      s_reset_hold <= (others => '1');
    elsif rising_edge(dst_clk) then    --sync deassert of output
      s_reset_hold <= s_reset_hold(s_reset_hold'length-2 downto 0) & '0';
    end if;
  end process;

end architecture rtl;
