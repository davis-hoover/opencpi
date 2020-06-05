-- THIS FILE WAS ORIGINALLY GENERATED ON Tue Jan 21 17:09:33 2020 EST
-- BASED ON THE FILE: test_clock_generator.xml
-- YOU *ARE* EXPECTED TO EDIT IT
-- This file initially contains the architecture skeleton for worker: test_clock_generator

library IEEE; use IEEE.std_logic_1164.all, ieee.numeric_std.all;
library ocpi; use ocpi.types.all;-- remove this to avoid all ocpi name collisions
library util; use util.util.all;

-- This worker serves as an example of using clocking primitives.

architecture rtl of worker is
  signal s_clk_out : std_logic;
  signal s_locked  : std_logic;
  signal s_not_locked : std_logic;
  signal s_not_locked_synced_data  : std_logic;
  signal doit : bool_t;
  signal out_in_rst_detected : std_logic;
  signal in_in_rst_detected : std_logic;
begin

    clock_gen : clocking.clocking.clock_generator
    generic map (
      CLK_PRIMITIVE          => Clock_Primitive,
      CLK_IN_FREQUENCY_MHz   => from_float(CLK_IN_FREQUENCY_MHz),
      CLK_OUT_FREQUENCY_MHz  => from_float(CLK_OUT_FREQUENCY_MHz),
      M                      => from_float(M),
      N                      => to_integer(unsigned(N)),
      O                      => from_float(O),
      CLK_OUT_DUTY_CYCLE     => from_float(CLKOUT_DUTY_CYCLE))
    port map(
      clk_in           =>    ctl_in.clk,
      reset            =>    ctl_in.reset,
      clk_out          =>    s_clk_out,
      locked           =>    s_locked);

    s_not_locked <= not s_locked;

    sync_not_locked_data : cdc.cdc.reset
      port map   (
        src_rst   => s_not_locked,
        dst_clk   => s_clk_out,
        dst_rst   => s_not_locked_synced_data);

    -- this worker is not initialized until s_clk_out is ticking and the out port
    -- has successfully come into reset
    rst_detector_reg_out_in_reset : util.util.reset_detector
      port map(
        clk                     => s_clk_out,
        rst                     => out_in.reset,
        clr                     => '0',
        rst_detected            => out_in_rst_detected,
        rst_then_unrst_detected => open);

    -- this worker is not initialized until s_clk_out is ticking and the in port
    -- has successfully come into reset
    rst_detector_reg_in_in_reset : util.util.reset_detector
      port map(
        clk                     => s_clk_out,
        rst                     => in_in.reset,
        clr                     => '0',
        rst_detected            => in_in_rst_detected,
        rst_then_unrst_detected => open);

    ctl_out.done <= out_in_rst_detected and in_in_rst_detected;
    doit <= in_in.ready and out_in.ready and not s_not_locked_synced_data;
  -- WSI input interface outputs
    in_out.take         <= doit;
  -- WSI output interface outputs
    out_out.give <= doit;
    out_out.data <= in_in.data;
    out_out.som <= in_in.som;
    out_out.eom <= in_in.eom;
    out_out.valid <= in_in.valid;
    out_out.byte_enable <= in_in.byte_enable; -- only necessary due to BSV protocol sharing
    out_out.opcode <= in_in.opcode;
    in2out_in_clk: util.util.in2out port map(in_port => s_clk_out, out_port => in_out.clk);
    in2out_out_clk: util.util.in2out port map(in_port => s_clk_out, out_port => out_out.clk);

end rtl;