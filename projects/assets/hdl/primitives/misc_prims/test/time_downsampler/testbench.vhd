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
      BYPASS                   => '0',
      MIN_NUM_DATA_PER_TIME    => to_unsigned(4,
                                  TIME_DOWNSAMPLER_DATA_CNT_BIT_WIDTH));

  subtest_1 : entity work.subtest
    generic map(
      FILENAME                 => "uut_subtest_1_data.txt",
      BACKPRESSURE_SELECT      => NO_BP,
      BYPASS                   => '0',
      MIN_NUM_DATA_PER_TIME    => to_unsigned(8,
                                  TIME_DOWNSAMPLER_DATA_CNT_BIT_WIDTH));

  subtest_2 : entity work.subtest
    generic map(
      FILENAME                 => "uut_subtest_2_data.txt",
      BACKPRESSURE_SELECT      => LFSR_BP,
      BYPASS                   => '0',
      MIN_NUM_DATA_PER_TIME    => to_unsigned(4,
                                  TIME_DOWNSAMPLER_DATA_CNT_BIT_WIDTH));

  subtest_3 : entity work.subtest
    generic map(
      FILENAME                 => "uut_subtest_3_data.txt",
      BACKPRESSURE_SELECT      => LFSR_BP,
      BYPASS                   => '0',
      MIN_NUM_DATA_PER_TIME    => to_unsigned(8,
                                  TIME_DOWNSAMPLER_DATA_CNT_BIT_WIDTH));

  subtest_4 : entity work.subtest
    generic map(
      FILENAME                 => "uut_subtest_4_data.txt",
      BACKPRESSURE_SELECT      => NO_BP,
      BYPASS                   => '1',
      MIN_NUM_DATA_PER_TIME    => to_unsigned(4,
                                  TIME_DOWNSAMPLER_DATA_CNT_BIT_WIDTH));

  subtest_5 : entity work.subtest
    generic map(
      FILENAME                 => "uut_subtest_5_data.txt",
      BACKPRESSURE_SELECT      => NO_BP,
      BYPASS                   => '1',
      MIN_NUM_DATA_PER_TIME    => to_unsigned(8,
                                  TIME_DOWNSAMPLER_DATA_CNT_BIT_WIDTH));

  subtest_6 : entity work.subtest
    generic map(
      FILENAME                 => "uut_subtest_6_data.txt",
      BACKPRESSURE_SELECT      => LFSR_BP,
      BYPASS                   => '1',
      MIN_NUM_DATA_PER_TIME    => to_unsigned(4,
                                  TIME_DOWNSAMPLER_DATA_CNT_BIT_WIDTH));

  subtest_7 : entity work.subtest
    generic map(
      FILENAME                 => "uut_subtest_7_data.txt",
      BACKPRESSURE_SELECT      => LFSR_BP,
      BYPASS                   => '1',
      MIN_NUM_DATA_PER_TIME    => to_unsigned(8,
                                  TIME_DOWNSAMPLER_DATA_CNT_BIT_WIDTH));

end rtl;
