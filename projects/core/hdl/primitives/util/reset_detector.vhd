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

-- * detects whether a synchronous reset, followed by a synchronous unreset, has
--   occurred
-- * rst_then_unrst_detected output is set the same clock cycle that rst input
--   is cleared
-- * once set, rst_then_unrst_detected output is not cleared until clr is set
library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;
library util;

entity reset_detector is
  port(
    clk                     : in  std_logic;
    rst                     : in  std_logic;
    clr                     : in  std_logic;  -- clears all rst_*
    rst_detected            : out std_logic;  -- synchronous reset detected
    rst_then_unrst_detected : out std_logic); -- synchronous reset, followed by
                                              -- a synchronous unreset, detected
end entity reset_detector;
architecture rtl of reset_detector is
  signal rising_pulse  : std_logic := '0';
  signal falling_pulse : std_logic := '0';
  signal rst_sticky    : std_logic := '0';
  signal tmp           : std_logic := '0';
begin

  edge_detector_i : util.util.edge_detector
    port map(
      clk           => clk,
      reset         => '0',
      din           => rst,
      rising_pulse  => open,
      falling_pulse => falling_pulse);

  rst_sticky_reg : util.util.set_clr 
    port map(
      clk => clk,
      rst => '0',
      set => rst,
      clr => clr,
      q   => open,
      q_r => rst_sticky);

  tmp <= rst_sticky and falling_pulse;
  detected_gen : util.util.set_clr 
    port map(
      clk => clk,
      rst => '0',
      set => tmp,
      clr => clr,
      q   => rst_then_unrst_detected,
      q_r => open);

  rst_detected <= rst_sticky;

end rtl;
