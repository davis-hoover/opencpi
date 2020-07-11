library ieee;
use ieee.std_logic_1164.all, ieee.numeric_std.all, ieee.math_real.all;
library misc_prims; use misc_prims.misc_prims.all;

entity subtest is
  generic(
    FILENAME                 : string;
    LFSR_BP_EN_PERIOD        : positive := 1);
  port(
    backpressure_select     : in  file_writer_backpressure_select_t;
    backpressure_select_vld : in  std_logic);
end entity subtest;
architecture rtl of subtest is
  signal clk              : std_logic := '0';
  signal rst              : std_logic := '0';
  signal data_src_odata   : data_complex_adc_t;
  signal data_src_ovld    : std_logic := '0';
  signal uut_odata        : data_complex_adc_t;
  signal uut_osamp_drop   : std_logic := '0';
  signal uut_ovld         : std_logic := '0';
  signal file_writer_irdy : std_logic := '0';
  signal end_of_test      : std_logic := '0';
begin

  clk_gen : process
  begin
    clk <= '0';
    wait for 10 ns;
    clk <= '1';
    wait for 10 ns;
  end process clk_gen;

  rst_gen : process
  begin
    rst <= '1';
    wait for 20 ns;
    wait until rising_edge(clk);
    rst <= '0';

    wait until end_of_test = '1';
    wait;

  end process rst_gen;

  data_src : entity work.data_src
    port map(
      -- CTRL
      clk                => clk,
      rst                => rst,
      stop_on_period_cnt => '1',
      stopped            => end_of_test,
      -- OUTPUT
      odata              => data_src_odata,
      ovld               => data_src_ovld);

  uut : misc_prims.misc_prims.adc_samp_drop_detector
    port map(
      -- CTRL
      clk        => clk,
      rst        => rst,
      status     => open,
      -- INPUT
      idata      => data_src_odata,
      ivld       => data_src_ovld,
      -- OUTPUT
      odata      => uut_odata,
      osamp_drop => uut_osamp_drop,
      ovld       => uut_ovld,
      ordy       => file_writer_irdy);

  file_writer : entity work.file_writer
    generic map(
      FILENAME          => FILENAME,
      LFSR_BP_EN_PERIOD => LFSR_BP_EN_PERIOD)
    port map(
      -- CTRL
      clk                     => clk,
      rst                     => rst,
      backpressure_select     => backpressure_select,
      backpressure_select_vld => backpressure_select_vld,
      -- INPUT
      idata                   => uut_odata,
      isamp_drop              => uut_osamp_drop,
      ivld                    => uut_ovld,
      irdy                    => file_writer_irdy);

end rtl;
