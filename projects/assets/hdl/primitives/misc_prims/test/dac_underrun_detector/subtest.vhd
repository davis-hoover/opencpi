library ieee;
use ieee.std_logic_1164.all, ieee.numeric_std.all, ieee.math_real.all;
library misc_prims; use misc_prims.misc_prims.all;

entity subtest is
  generic(
    DATA_SRC_OUTPUT_CONTINUOUS : boolean;
    FILENAME                   : string;
    DATA_PIPE_LATENCY_CYCLES   : natural := 0);
  port(
    backpressure_select     : in  file_writer_backpressure_select_t;
    backpressure_select_vld : in  std_logic);
end entity subtest;
architecture rtl of subtest is
  signal clk              : std_logic := '0';
  signal rst              : std_logic := '0';
  signal data_src_odata   : data_complex_t;
  signal data_src_ovld    : std_logic := '0';
  signal uut_irdy         : std_logic := '0';
  signal uut_imetadata    : metadata_dac_t;
  signal uut_odata        : data_complex_t;
  signal uut_ometadata    : metadata_dac_t;
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
    generic map(
      OUTPUT_CONTINUOUS => DATA_SRC_OUTPUT_CONTINUOUS)
    port map(
      -- CTRL
      clk                => clk,
      rst                => rst,
      stop_on_period_cnt => '1',
      stopped            => end_of_test,
      -- OUTPUT
      odata              => data_src_odata,
      ovld               => data_src_ovld,
      ordy               => uut_irdy);

  uut_imetadata.underrun_error <= '0';
  uut_imetadata.data_vld <= '0';
  uut_imetadata.ctrl_tx_on_off <= not end_of_test;
    
  uut : misc_prims.misc_prims.dac_underrun_detector
    generic map(
      DATA_PIPE_LATENCY_CYCLES => DATA_PIPE_LATENCY_CYCLES)
    port map(
      -- CTRL
      clk       => clk,
      rst       => rst,
      status    => open,
      -- INPUT
      idata     => data_src_odata,
      imetadata => uut_imetadata,
      ivld      => data_src_ovld,
      irdy      => uut_irdy,
      -- OUTPUT
      odata     => uut_odata,
      ometadata => uut_ometadata,
      ovld      => uut_ovld,
      ordy      => file_writer_irdy);

  file_writer : entity work.file_writer
    generic map(
      FILENAME => FILENAME)
    port map(
      -- CTRL
      clk                     => clk,
      rst                     => rst,
      backpressure_select     => backpressure_select,
      backpressure_select_vld => backpressure_select_vld,
      -- INPUT
      idata                   => uut_odata,
      imetadata               => uut_ometadata,
      ivld                    => uut_ovld,
      irdy                    => file_writer_irdy);

end rtl;
