library ieee;
use ieee.std_logic_1164.all, ieee.numeric_std.all, ieee.math_real.all;
library misc_prims; use misc_prims.misc_prims.all;

entity testbench is
end entity testbench;
architecture rtl of testbench is
  component subtest is
    generic(
      DATA_SRC_OUTPUT_CONTINUOUS : boolean;
      FILENAME                   : string;
      DATA_PIPE_LATENCY_CYCLES   : natural := 0);
    port(
      backpressure_select        : in  file_writer_backpressure_select_t;
      backpressure_select_vld    : in  std_logic);
  end component;
begin

  subtest_0 : subtest
    generic map(
      DATA_SRC_OUTPUT_CONTINUOUS => true,
      FILENAME                   => "uut_subtest_0_data.txt",
      DATA_PIPE_LATENCY_CYCLES   => 0)
    port map(
      backpressure_select        => NO_BP, --no backpressure expected from DAC
      backpressure_select_vld    => '1');

  subtest_1 : subtest
    generic map(
      DATA_SRC_OUTPUT_CONTINUOUS => false,
      FILENAME                   => "uut_subtest_1_data.txt",
      DATA_PIPE_LATENCY_CYCLES   => 0)
    port map(
      backpressure_select        => NO_BP, --no backpressure expected from DAC
      backpressure_select_vld    => '1');

end rtl;
