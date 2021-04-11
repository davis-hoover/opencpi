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
      CLK_PRIMITIVE          : string_t := to_string("altera_pll", 32);
      VENDOR                 : string_t := to_string("agnostic", 32);
      CLK_IN_FREQUENCY_MHz   : real := 100.0;
      CLK_OUT_FREQUENCY_MHz  : real := 100.0;
      REFERENCE_CLOCK_FREQUENCY : string_t := to_string("100.0 MHz", 32);
      OUTPUT_CLOCK_FREQUENCY0   : string_t := to_string("100.0 MHz", 32);
      M                      : real := 5.0;  -- M
      N                      : integer := 1; -- D
      O                      : real := 1.0;  -- O
      CLK_OUT_PHASE_DEGREES  : real := 0.0;
      PHASE_SHIFT0_PICO_SECS : string_t := to_string("0 ps", 32);
      CLK_OUT_DUTY_CYCLE     : real := 0.5);
    port(
      clk_in           : in     std_logic;
      reset            : in     std_logic;
      clk_out          : out    std_logic;
      locked           : out    std_logic);
end entity clock_generator;

architecture rtl of clock_generator is
  -- Trying to convert the the clock frequencies to strings has some issues (noticed in modelsim)
  -- where the IP doesn't set the correct output clock frequency for some reason.
  -- So avoiding trying to convert the floats to strings
  -- constant c_CLK_IN_PERIOD_PICO_SEC  : real := (1.0/CLK_OUT_FREQUENCY_MHz) * (1.0E6);
  -- Intel/Altera PLL uses strings to set parameters for the refclk and outclk frequency, and duty cycle
  -- so need to convert them to strings.
  -- constant c_CLK_IN_FREQUENCY_MHz  : string := "" & real'image(CLK_IN_FREQUENCY_MHz) & " MHz";
  -- constant c_CLK_OUT_FREQUENCY_MHz : string := "" & real'image(CLK_OUT_FREQUENCY_MHz) & " MHz";
  -- The Intel/Altera PLL's phase shift parameter units are pico seconds so need to convert degrees to picoseconds
  -- constant c_CLK_OUT_PHASE_PICO_SEC : string := "" & integer'image(integer((CLK_OUT_PHASE_DEGREES*c_CLK_OUT_PERIOD_PICO_SEC)/360.0)) & " ps";

  component pll
    generic (
      reference_clock_frequency  : string :=  "100.0 MHz";
      output_clock_frequency0    : string :=  "100.0 MHz";
      phase_shift0               : string :=  "0 ps";
      duty_cycle0                : integer :=  50);
    port(
      refclk	  : in   std_logic;
      rst	      : in   std_logic;
      outclk_0	:	out  std_logic;
      locked	  :	out  std_logic);
  end component;
  
  component agnostic_clock_generator
    generic (
      CLK_OUT_FREQUENCY_MHz      : real := 100.0);
    port(
      reset     : in     std_logic;
      clk_out   : out    std_logic;
      locked    : out    std_logic);
  end component;

begin
  
  -- For modelsim, for now only simulates for Altera
  -- This is assumes that the Altera IP were compiled for
  -- for modelsim prior to building this. Will support 
  -- Xilinx in the future.
  gen_altera: if (VENDOR = to_string("altera", 32))  generate
    -- Cyclone V uses altera_pll
    gen_altera_pll: if (CLK_PRIMITIVE = to_string("altera_pll", 32)) generate
      inst_altera_pll : component pll
        generic map(
          reference_clock_frequency =>  from_string(REFERENCE_CLOCK_FREQUENCY),
          output_clock_frequency0   =>  from_string(OUTPUT_CLOCK_FREQUENCY0),
          phase_shift0              =>  from_string(PHASE_SHIFT0_PICO_SECS),
          duty_cycle0               =>  integer(CLK_OUT_DUTY_CYCLE*100.0)) -- The Intel/Altera PLL is expecting values from 1-99
	      port map (
	        refclk => clk_in,
	        rst => reset,
	        outclk_0 => clk_out,
	        locked => locked);
    end generate gen_altera_pll;
  end generate gen_altera;  
  
  -- Vendor agnostic clock generator
  gen_vendor_agnostic: if (VENDOR = to_string("agnostic", 32))  generate
    inst_vendor_agnostic_clk_gen : agnostic_clock_generator
      generic map(
        CLK_OUT_FREQUENCY_MHz  => CLK_OUT_FREQUENCY_MHz)
      port map (
        reset => reset,
        clk_out => clk_out,
        locked => locked);
  end generate gen_vendor_agnostic;

end rtl;
