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

library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all, ieee.math_real.all;
library ocpi; use ocpi.types.all;

entity clock_generator is
    generic (
      CLK_PRIMITIVE          : string_t := to_string("plle2", 32);
      CLK_IN_FREQUENCY_MHz   : real := 100.0;
      CLK_OUT_FREQUENCY_MHz  : real := 100.0;
      M                      : real := 5.0;  -- M
      N                      : integer := 1; -- D
      O                      : real := 1.0;  -- O
   -- CLK_OUT_PHASE_DEGREES  : real; -- Add this in when there's a generalized way to support Xilinx and Intel phase shift in optimization script
      CLK_OUT_DUTY_CYCLE     : real := 0.5);
    port(
      clk_in           : in     std_logic;
      reset            : in     std_logic;
      clk_out          : out    std_logic;
      locked           : out    std_logic);
end entity clock_generator;

architecture rtl of clock_generator is
  constant c_CLKIN1_PERIOD_NANO_SEC  : real := (1.0/CLK_IN_FREQUENCY_MHz) * (1.0E3);

  component mmcme2
    generic (
      DIVCLK_DIVIDE        : integer := 1; -- D
      CLKFBOUT_MULT_F      : real := 5.0;  -- M
      CLKOUT0_DIVIDE_F     : real := 1.0;  -- O
      CLKOUT0_PHASE        : real := 0.0;
      CLKOUT0_DUTY_CYCLE   : real := 0.5;
      CLKIN1_PERIOD        : real := 0.0);
    port(
      clk_in1           : in     std_logic;
      clk_out1          : out    std_logic;
      reset             : in     std_logic;
      locked            : out    std_logic);
  end component;

  component plle2
    generic (
      DIVCLK_DIVIDE        : integer := 1;  -- D
      CLKFBOUT_MULT        : integer := 5;  -- M
      CLKOUT0_DIVIDE       : integer := 1;  -- O
      CLKOUT0_PHASE        : real := 0.0;
      CLKOUT0_DUTY_CYCLE   : real := 0.5;
      CLKIN1_PERIOD        : real := 0.0);
    port(
      clk_in1           : in     std_logic;
      clk_out1          : out    std_logic;
      reset             : in     std_logic;
      locked            : out    std_logic);
  end component;

begin
  -- Zynq 7000 uses mmcme2 and plle2 primitives
  -- Zynq UltraScale uses mmcme3 and plle3 primitives
  -- Zynq Ultrascale+ uses mmcme4 and plle4 primitives
  gen_pll: if CLK_PRIMITIVE = to_string("plle2", 32) generate
    inst_pll : component plle2
      generic map(
       DIVCLK_DIVIDE        =>  N,
       CLKFBOUT_MULT        =>  integer(M),
       CLKOUT0_DIVIDE       =>  integer(O),
       --CLKOUT0_PHASE        =>  CLK_OUT_PHASE_DEGREES,
       CLKOUT0_DUTY_CYCLE   =>  CLK_OUT_DUTY_CYCLE,
       CLKIN1_PERIOD        =>  c_CLKIN1_PERIOD_NANO_SEC)
   	 port map (
   	  clk_in1 => clk_in,
   	  clk_out1 => clk_out,
   	  reset => reset,
   	  locked => locked);
  end generate gen_pll;

  gen_mmcm: if CLK_PRIMITIVE = to_string("mmcme2", 32) generate
   inst_mmcm : component mmcme2
     generic map(
      DIVCLK_DIVIDE        =>  N,
      CLKFBOUT_MULT_F      =>  M,
      CLKOUT0_DIVIDE_F     =>  O,
      --CLKOUT0_PHASE        =>  CLK_OUT_PHASE_DEGREES,
      CLKOUT0_DUTY_CYCLE   =>  CLK_OUT_DUTY_CYCLE,
      CLKIN1_PERIOD        =>  c_CLKIN1_PERIOD_NANO_SEC)
  	 port map (
  	  clk_in1 => clk_in,
  	  clk_out1 => clk_out,
  	  reset => reset,
  	  locked => locked);
  end generate gen_mmcm;
end rtl;
