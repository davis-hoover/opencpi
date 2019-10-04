library ieee;
use ieee.std_logic_1164.all, ieee.numeric_std.all, ieee.math_real.all;
library misc_prims; use misc_prims.misc_prims.all;

entity testbench is
end entity testbench;
architecture rtl of testbench is
begin

  subtest_0 : entity work.subtest
    generic map(
      DATA_SRC_OUTPUT_CONTINUOUS => true,
      FILENAME                   => "uut_subtest_0_data.txt",
      DATA_PIPE_LATENCY_CYCLES   => 0,
      BITS_PACKED_INTO_LSBS      => false)
    port map(
      backpressure_select        => NO_BP, --no backpressure expected from DAC
      backpressure_select_vld    => '1');

  subtest_1 : entity work.subtest
    generic map(
      DATA_SRC_OUTPUT_CONTINUOUS => false,
      FILENAME                   => "uut_subtest_1_data.txt",
      DATA_PIPE_LATENCY_CYCLES   => 0,
      BITS_PACKED_INTO_LSBS      => false)
    port map(
      backpressure_select        => NO_BP, --no backpressure expected from DAC
      backpressure_select_vld    => '1');

  subtest_2 : entity work.subtest
    generic map(
      DATA_SRC_OUTPUT_CONTINUOUS => true,
      FILENAME                 => "uut_subtest_2_data.txt",
      DATA_PIPE_LATENCY_CYCLES => 0,
      BITS_PACKED_INTO_LSBS    => true)
    port map(
      backpressure_select      => NO_BP, --no backpressure expected from DAC
      backpressure_select_vld  => '1');

  subtest_3 : entity work.subtest
    generic map(
      DATA_SRC_OUTPUT_CONTINUOUS => false,
      FILENAME                 => "uut_subtest_3_data.txt",
      DATA_PIPE_LATENCY_CYCLES => 0,
      BITS_PACKED_INTO_LSBS    => true)
    port map(
      backpressure_select      => NO_BP, --no backpressure expected from DAC
      backpressure_select_vld  => '1');

end rtl;
