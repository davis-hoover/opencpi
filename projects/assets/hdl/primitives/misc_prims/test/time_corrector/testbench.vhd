library ieee;
use ieee.std_logic_1164.all, ieee.numeric_std.all, ieee.math_real.all;
library protocol;
library misc_prims; use misc_prims.misc_prims.all;

entity testbench is
end entity testbench;
architecture rtl of testbench is
begin

  subtest_0 : entity work.subtest
    generic map(
      FILENAME                 => "uut_subtest_0_data.txt",
      CTRL_FILENAME            => "uut_subtest_0_ctrl.txt",
      BACKPRESSURE_SELECT      => NO_BP,
      --INCLUDE_ERROR_SAMP_DROP  => false,
      BYPASS                   => '0',
      TIME_TIME                => to_unsigned(0, protocol.complex_short_with_metadata.OP_TIME_BIT_WIDTH),
      TIME_CORRECTION          => to_signed(0, protocol.complex_short_with_metadata.OP_TIME_BIT_WIDTH));

  subtest_1 : entity work.subtest
    generic map(
      FILENAME                 => "uut_subtest_1_data.txt",
      CTRL_FILENAME            => "uut_subtest_1_ctrl.txt",
      BACKPRESSURE_SELECT      => NO_BP,
      --INCLUDE_ERROR_SAMP_DROP  => false,
      BYPASS                   => '0',
      TIME_TIME                => to_unsigned(0, protocol.complex_short_with_metadata.OP_TIME_BIT_WIDTH),
      TIME_CORRECTION          => to_signed(1, protocol.complex_short_with_metadata.OP_TIME_BIT_WIDTH));

  subtest_2 : entity work.subtest
    generic map(
      FILENAME                 => "uut_subtest_2_data.txt",
      CTRL_FILENAME            => "uut_subtest_2_ctrl.txt",
      BACKPRESSURE_SELECT      => NO_BP,
      --INCLUDE_ERROR_SAMP_DROP  => false,
      BYPASS                   => '0',
      TIME_TIME                => to_unsigned(0, protocol.complex_short_with_metadata.OP_TIME_BIT_WIDTH),
      TIME_CORRECTION          => to_signed(-1, protocol.complex_short_with_metadata.OP_TIME_BIT_WIDTH));

  subtest_3 : entity work.subtest
    generic map(
      FILENAME                 => "uut_subtest_3_data.txt",
      CTRL_FILENAME            => "uut_subtest_3_ctrl.txt",
      BACKPRESSURE_SELECT      => NO_BP,
      --INCLUDE_ERROR_SAMP_DROP  => false,
      BYPASS                   => '0',
      TIME_TIME                => to_unsigned(102, protocol.complex_short_with_metadata.OP_TIME_BIT_WIDTH),
      TIME_CORRECTION          => to_signed(0, protocol.complex_short_with_metadata.OP_TIME_BIT_WIDTH));

  subtest_4 : entity work.subtest
    generic map(
      FILENAME                 => "uut_subtest_4_data.txt",
      CTRL_FILENAME            => "uut_subtest_4_ctrl.txt",
      BACKPRESSURE_SELECT      => NO_BP,
      --INCLUDE_ERROR_SAMP_DROP  => false,
      BYPASS                   => '0',
      TIME_TIME                => to_unsigned(102, protocol.complex_short_with_metadata.OP_TIME_BIT_WIDTH),
      TIME_CORRECTION          => to_signed(1, protocol.complex_short_with_metadata.OP_TIME_BIT_WIDTH));

  subtest_5 : entity work.subtest
    generic map(
      FILENAME                 => "uut_subtest_5_data.txt",
      CTRL_FILENAME            => "uut_subtest_5_ctrl.txt",
      BACKPRESSURE_SELECT      => NO_BP,
      --INCLUDE_ERROR_SAMP_DROP  => false,
      BYPASS                   => '0',
      TIME_TIME                => to_unsigned(102, protocol.complex_short_with_metadata.OP_TIME_BIT_WIDTH),
      TIME_CORRECTION          => to_signed(-1, protocol.complex_short_with_metadata.OP_TIME_BIT_WIDTH));

  -- use time/correction that would result in overflow if it were valid, but
  -- because time in is not valid, no overflow should be reported
  subtest_6 : entity work.subtest
    generic map(
      FILENAME                 => "uut_subtest_6_data.txt",
      CTRL_FILENAME            => "uut_subtest_6_ctrl.txt",
      BACKPRESSURE_SELECT      => NO_BP,
      --INCLUDE_ERROR_SAMP_DROP  => false,
      BYPASS                   => '0',
      TIME_TIME                => to_unsigned(0, protocol.complex_short_with_metadata.OP_TIME_BIT_WIDTH),
      TIME_TIME_VLD            => '0',
      TIME_CORRECTION          => to_signed(1, protocol.complex_short_with_metadata.OP_TIME_BIT_WIDTH));

end rtl;
