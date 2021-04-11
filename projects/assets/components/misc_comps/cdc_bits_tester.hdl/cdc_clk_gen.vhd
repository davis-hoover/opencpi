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

-- TODO Parameterize this some more and make more generic
library ieee; use ieee.std_logic_1164.all; use ieee.numeric_std.all; use ieee.math_real.all; use ieee.std_logic_misc.all;
library ocpi; use ocpi.types.all,  ocpi.util.all;
library cdc;
library clocking;

entity cdc_clk_gen is
    generic (ctl_clk_hz : real := 100000000.0;
             src_clk_hz : real := 100000000.0;
             dst_clk_hz : real := 100000000.0);
    port (
      	ctl_clk      : in std_logic;
      	ctl_rst      : in std_logic;
        src_clk      : out std_logic;
        src_rst      : out std_logic;
        dst_clk      : out std_logic;
        dst_rst      : out std_logic);
end entity cdc_clk_gen;

architecture rtl of cdc_clk_gen is
  signal s_src_clk            : std_logic := '0';
  signal s_src_rst            : std_logic;
  signal s_dst_clk            : std_logic := '0';
  signal s_dst_rst            : std_logic;
  signal s_src_clk_locked     : std_logic;
  signal s_src_clk_not_locked : std_logic;
  signal s_dst_clk_locked     : std_logic;
  signal s_dst_clk_not_locked : std_logic;
  signal s_sync_dst_not_locked_to_src : std_logic;
  signal s_sync_src_not_locked_to_dst : std_logic;
  signal s_not_locked_src_rst : std_logic;
  signal s_not_locked_dst_rst : std_logic;
begin

  src_clk <= s_src_clk;
  src_rst <= s_src_rst;
  dst_clk <= s_dst_clk;
  dst_rst <= s_dst_rst;


  gen_equal_clk_freq : if (src_clk_hz = dst_clk_hz) generate
    s_src_clk <= ctl_clk;
    s_src_rst <= ctl_rst;
    s_dst_clk <= ctl_clk;
    s_dst_rst <= ctl_rst;
  end generate gen_equal_clk_freq;

  gen_diff_clk_freq : if (src_clk_hz /= dst_clk_hz) generate

    s_src_clk_not_locked <= not s_src_clk_locked;
    s_dst_clk_not_locked <= not s_dst_clk_locked;

    reset_sync_1 : cdc.cdc.reset
      port map   (
        src_rst   => s_dst_clk_not_locked,
        dst_clk   => s_src_clk,
        dst_rst   => s_sync_dst_not_locked_to_src);

    reset_sync_2 : cdc.cdc.reset
      port map   (
        src_rst   => s_src_clk_not_locked,
        dst_clk   => s_dst_clk,
        dst_rst   => s_sync_src_not_locked_to_dst);

    s_not_locked_src_rst <= s_src_clk_not_locked or s_sync_dst_not_locked_to_src;
    reset_sync_s_not_locked_to_src : cdc.cdc.reset
      port map   (
        src_rst   => s_not_locked_src_rst,
        dst_clk   => s_src_clk,
        dst_rst   => s_src_rst);

    s_not_locked_dst_rst <= s_dst_clk_not_locked or s_sync_src_not_locked_to_dst;
    reset_sync_s_not_locked_to_dst : cdc.cdc.reset
      port map   (
        src_rst   => s_not_locked_dst_rst,
        dst_clk   => s_dst_clk,
        dst_rst   => s_dst_rst);


    gen_1_to_2_clk : if (src_clk_hz = 50000000.0) generate

    inst_100_to_50 : clocking.clocking.clock_generator
      generic map (
        CLK_PRIMITIVE          => to_string("mmcme2", 32),
        VENDOR                 => to_string("xilinx", 32),
        CLK_IN_FREQUENCY_MHz   => ctl_clk_hz/(1.0E6),
        CLK_OUT_FREQUENCY_MHz  => src_clk_hz/(1.0E6),
        M                      => 12.0,
        N                      => 1,
        O                      => 24.0,
        CLK_OUT_PHASE_DEGREES  => 0.0,
        CLK_OUT_DUTY_CYCLE     => 0.5)
      port map(
        clk_in => ctl_clk,
        reset  => ctl_rst,
        clk_out => s_src_clk,
        locked => s_src_clk_locked);

    inst_100_to_100 : clocking.clocking.clock_generator
      generic map (
        CLK_PRIMITIVE          => to_string("mmcme2", 32),
        VENDOR                 => to_string("xilinx", 32),
        CLK_IN_FREQUENCY_MHz   => ctl_clk_hz/(1.0E6),
        CLK_OUT_FREQUENCY_MHz  => dst_clk_hz/(1.0E6),
        M                      => 12.0,
        N                      => 1,
        O                      => 12.0,
        CLK_OUT_PHASE_DEGREES  => 0.0,
        CLK_OUT_DUTY_CYCLE     => 0.5)
      port map(
        clk_in => ctl_clk,
        reset  => ctl_rst,
        clk_out => s_dst_clk,
        locked => s_dst_clk_locked);

    end generate gen_1_to_2_clk;

    gen_1_to_4_clk : if (src_clk_hz = 25000000.0) generate

    inst_100_to_25 : clocking.clocking.clock_generator
      generic map (
        CLK_PRIMITIVE          => to_string("mmcme2", 32),
        VENDOR                 => to_string("xilinx", 32),
        CLK_IN_FREQUENCY_MHz   => ctl_clk_hz/(1.0E6),
        CLK_OUT_FREQUENCY_MHz  => src_clk_hz/(1.0E6),
        M                      => 12.0,
        N                      => 1,
        O                      => 48.0,
        CLK_OUT_PHASE_DEGREES  => 0.0,
        CLK_OUT_DUTY_CYCLE     => 0.5)
      port map(
        clk_in => ctl_clk,
        reset  => ctl_rst,
        clk_out => s_src_clk,
        locked => s_src_clk_locked);

    inst_100_to_100 : clocking.clocking.clock_generator
      generic map (
        CLK_PRIMITIVE          => to_string("mmcme2", 32),
        VENDOR                 => to_string("xilinx", 32),
        CLK_IN_FREQUENCY_MHz   => ctl_clk_hz/(1.0E6),
        CLK_OUT_FREQUENCY_MHz  => dst_clk_hz/(1.0E6),
        M                      => 12.0,
        N                      => 1,
        O                      => 12.0,
        CLK_OUT_PHASE_DEGREES  => 0.0,
        CLK_OUT_DUTY_CYCLE     => 0.5)
      port map(
        clk_in => ctl_clk,
        reset  => ctl_rst,
        clk_out => s_dst_clk,
        locked => s_dst_clk_locked);

    end generate gen_1_to_4_clk;

    gen_2_to_1_clk : if (dst_clk_hz = 50000000.0) generate

    inst_100_to_100 : clocking.clocking.clock_generator
      generic map (
        CLK_PRIMITIVE          => to_string("mmcme2", 32),
        VENDOR                 => to_string("xilinx", 32),
        CLK_IN_FREQUENCY_MHz   => ctl_clk_hz/(1.0E6),
        CLK_OUT_FREQUENCY_MHz  => src_clk_hz/(1.0E6),
        M                      => 12.0,
        N                      => 1,
        O                      => 12.0,
        CLK_OUT_PHASE_DEGREES  => 0.0,
        CLK_OUT_DUTY_CYCLE     => 0.5)
      port map(
        clk_in => ctl_clk,
        reset  => ctl_rst,
        clk_out => s_src_clk,
        locked => s_src_clk_locked);

    inst_100_to_50 : clocking.clocking.clock_generator
      generic map (
        CLK_PRIMITIVE          => to_string("mmcme2", 32),
        VENDOR                 => to_string("xilinx", 32),
        CLK_IN_FREQUENCY_MHz   => ctl_clk_hz/(1.0E6),
        CLK_OUT_FREQUENCY_MHz  => dst_clk_hz/(1.0E6),
        M                      => 12.0,
        N                      => 1,
        O                      => 24.0,
        CLK_OUT_PHASE_DEGREES  => 0.0,
        CLK_OUT_DUTY_CYCLE     => 0.5)
      port map(
        clk_in => ctl_clk,
        reset  => ctl_rst,
        clk_out => s_dst_clk,
        locked => s_dst_clk_locked);

    end generate gen_2_to_1_clk;

    gen_4_to_1_clk : if (dst_clk_hz = 25000000.0) generate

    inst_100_to_100 : clocking.clocking.clock_generator
      generic map (
        CLK_PRIMITIVE          => to_string("mmcme2", 32),
        VENDOR                 => to_string("xilinx", 32),
        CLK_IN_FREQUENCY_MHz   => ctl_clk_hz/(1.0E6),
        CLK_OUT_FREQUENCY_MHz  => src_clk_hz/(1.0E6),
        M                      => 12.0,
        N                      => 1,
        O                      => 12.0,
        CLK_OUT_PHASE_DEGREES  => 0.0,
        CLK_OUT_DUTY_CYCLE     => 0.5)
      port map(
        clk_in => ctl_clk,
        reset  => ctl_rst,
        clk_out => s_src_clk,
        locked => s_src_clk_locked);

     inst_100_to_25 : clocking.clocking.clock_generator
       generic map (
         CLK_PRIMITIVE          => to_string("mmcme2", 32),
         VENDOR                 => to_string("xilinx", 32),
         CLK_IN_FREQUENCY_MHz   => ctl_clk_hz/(1.0E6),
         CLK_OUT_FREQUENCY_MHz  => dst_clk_hz/(1.0E6),
         M                      => 12.0,
         N                      => 1,
         O                      => 48.0,
         CLK_OUT_PHASE_DEGREES  => 0.0,
         CLK_OUT_DUTY_CYCLE     => 0.5)
       port map(
         clk_in => ctl_clk,
         reset  => ctl_rst,
         clk_out => s_dst_clk,
         locked => s_dst_clk_locked);

    end generate gen_4_to_1_clk;

  end generate gen_diff_clk_freq;

end rtl;
