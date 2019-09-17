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
      BACKPRESSURE_SELECT      => NO_BP,
      INCLUDE_ERROR_SAMP_DROP  => false,
      TIME_TIME                => to_unsigned(0, METADATA_TIME_BIT_WIDTH),
      TIME_CORRECTION          => to_signed(0, METADATA_TIME_BIT_WIDTH),
      DATA_PIPE_LATENCY_CYCLES => 0);

  subtest_1 : entity work.subtest
    generic map(
      FILENAME                 => "uut_subtest_1_data.txt",
      BACKPRESSURE_SELECT      => NO_BP,
      INCLUDE_ERROR_SAMP_DROP  => false,
      TIME_TIME                => to_unsigned(0, METADATA_TIME_BIT_WIDTH),
      TIME_CORRECTION          => to_signed(1, METADATA_TIME_BIT_WIDTH),
      DATA_PIPE_LATENCY_CYCLES => 0);

  subtest_2 : entity work.subtest
    generic map(
      FILENAME                 => "uut_subtest_2_data.txt",
      BACKPRESSURE_SELECT      => NO_BP,
      INCLUDE_ERROR_SAMP_DROP  => false,
      TIME_TIME                => to_unsigned(0, METADATA_TIME_BIT_WIDTH),
      TIME_CORRECTION          => to_signed(-1, METADATA_TIME_BIT_WIDTH),
      DATA_PIPE_LATENCY_CYCLES => 0);

  subtest_3 : entity work.subtest
    generic map(
      FILENAME                 => "uut_subtest_3_data.txt",
      BACKPRESSURE_SELECT      => NO_BP,
      INCLUDE_ERROR_SAMP_DROP  => false,
      TIME_TIME                => to_unsigned(102, METADATA_TIME_BIT_WIDTH),
      TIME_CORRECTION          => to_signed(0, METADATA_TIME_BIT_WIDTH),
      DATA_PIPE_LATENCY_CYCLES => 0);

  subtest_4 : entity work.subtest
    generic map(
      FILENAME                 => "uut_subtest_4_data.txt",
      BACKPRESSURE_SELECT      => NO_BP,
      INCLUDE_ERROR_SAMP_DROP  => false,
      TIME_TIME                => to_unsigned(102, METADATA_TIME_BIT_WIDTH),
      TIME_CORRECTION          => to_signed(1, METADATA_TIME_BIT_WIDTH),
      DATA_PIPE_LATENCY_CYCLES => 0);

  subtest_5 : entity work.subtest
    generic map(
      FILENAME                 => "uut_subtest_5_data.txt",
      BACKPRESSURE_SELECT      => NO_BP,
      INCLUDE_ERROR_SAMP_DROP  => false,
      TIME_TIME                => to_unsigned(102, METADATA_TIME_BIT_WIDTH),
      TIME_CORRECTION          => to_signed(-1, METADATA_TIME_BIT_WIDTH),
      DATA_PIPE_LATENCY_CYCLES => 0);

end rtl;
