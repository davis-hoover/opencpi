library ieee;
use ieee.std_logic_1164.all, ieee.numeric_std.all, ieee.math_real.all;
library misc_prims; use misc_prims.misc_prims.all;

entity testbench is
end entity testbench;
architecture rtl of testbench is
begin

  subtest_0 : entity work.subtest
    generic map(
      CCLK_PERIOD              => 20 ns, -- 50 MHz
      DCLK_PERIOD              => 17 ns, -- chosen to be close to E310
                                         -- max-per-ADC channel 30.72 MHz
      FILENAME                 => "uut_subtest_0_data.txt",
      ALLOW_LFSR_BACKPRESSURE  => false,
      DATA_PIPE_LATENCY_CYCLES => 0);

  subtest_1 : entity work.subtest
    generic map(
      CCLK_PERIOD              => 20 ns, -- 50 MHz
      DCLK_PERIOD              => 480 ns, -- chosen to be close to E310
                                          -- min-per-ADC channel 2.08333.. MHz
      FILENAME                 => "uut_subtest_1_data.txt",
      ALLOW_LFSR_BACKPRESSURE  => false,
      DATA_PIPE_LATENCY_CYCLES => 0);

  subtest_2 : entity work.subtest
    generic map(
      CCLK_PERIOD              => 20 ns, -- 50 MHz
      DCLK_PERIOD              => 17 ns, -- chosen to be close to E310
                                         -- max-per-ADC channel 30.72 MHz
      FILENAME                 => "uut_subtest_2_data.txt",
      ALLOW_LFSR_BACKPRESSURE  => true,
      DATA_PIPE_LATENCY_CYCLES => 0);

  subtest_3 : entity work.subtest
    generic map(
      CCLK_PERIOD              => 20 ns, -- 50 MHz
      DCLK_PERIOD              => 480 ns, -- chosen to be close to E310
                                          -- min-per-ADC channel 2.08333.. MHz
      FILENAME                 => "uut_subtest_3_data.txt",
      ALLOW_LFSR_BACKPRESSURE  => true,
      DATA_PIPE_LATENCY_CYCLES => 0);

end rtl;
