library ieee;
use ieee.std_logic_1164.all, ieee.numeric_std.all, ieee.math_real.all;
library misc_prims; use misc_prims.misc_prims.all;

entity testbench is
end entity testbench;
architecture rtl of testbench is
begin

  subtest_0 : entity work.subtest
    generic map(
      FILENAME                 => "uut_subtest_0_data.txt",
      DATA_PIPE_LATENCY_CYCLES => 0)
    port map(
      backpressure_select      => NO_BP,
      backpressure_select_vld  => '1');

  subtest_1 : entity work.subtest
    generic map(
      FILENAME                 => "uut_subtest_1_data.txt",
      DATA_PIPE_LATENCY_CYCLES => 0)
    port map(
      backpressure_select      => LFSR_BP,
      backpressure_select_vld  => '1');

  subtest_2 : entity work.subtest
    generic map(
      FILENAME                 => "uut_subtest_2_data.txt",
      DATA_PIPE_LATENCY_CYCLES => 0,
      LFSR_BP_EN_PERIOD        => 1024)
    port map(
      backpressure_select      => LFSR_BP,
      backpressure_select_vld  => '1');

end rtl;
