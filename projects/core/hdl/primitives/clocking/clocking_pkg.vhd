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

library ieee; use IEEE.std_logic_1164.all, ieee.numeric_std.all, ieee.math_real.all;
library ocpi; use ocpi.types.all;

package clocking is

  component clock_generator is
      generic (
        CLK_PRIMITIVE          : string_t := to_string("plle2", 32); -- Used when a vendor has multiple clock primitives or versions for a part
        CLK_IN_FREQUENCY_MHz   : real;
        CLK_OUT_FREQUENCY_MHz  : real;
        M                      : real;  -- The multiply factor for a phase-locked loop
        N                      : integer; -- The divide factor for a phase-locked loop. Xilinx calls it D and Intel calls it N
        O                      : real; -- For phase-locked loops with muitlple outputs, this is the output divide factor. Xilinx calls it O and Intel calls it C
        -- CLK_OUT_PHASE_DEGREES  : real; -- Phase shift of the output clock. Add this in when there's a generalized way to support Xilinx and Intel phase shift in optimization script
        CLK_OUT_DUTY_CYCLE     : real);
      port(
        clk_in           : in     std_logic;
        reset            : in     std_logic;
        clk_out          : out    std_logic;
        locked           : out    std_logic);
  end component clock_generator;

end package clocking;
