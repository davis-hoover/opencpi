library ieee;
use ieee.std_logic_1164.all, ieee.numeric_std.all, ieee.math_real.all;
library misc_prims; use misc_prims.misc_prims.all;

entity subtest is
  generic(
    CCLK_PERIOD              : time;
    DCLK_PERIOD              : time;
    FILENAME                 : string;
    ALLOW_LFSR_BACKPRESSURE  : boolean;
    DATA_PIPE_LATENCY_CYCLES : natural := 0);
end entity subtest;
architecture rtl of subtest is
  signal cclk_clk  : std_logic := '0';
  signal cclk_rst  : std_logic := '0';
  signal cclk_ctrl : adc_samp_drop_generator_scdcd_ctrl_t;

  signal dclk_clk                     : std_logic := '0';
  signal dclk_rst                     : std_logic := '0';
  signal dclk_data_src_odata          : data_complex_adc_t;
  signal dclk_data_src_ovld           : std_logic := '0';
  signal dclk_uut_odata               : data_complex_adc_t;
  signal dclk_uut_ometadata           : metadata_t;
  signal dclk_uut_ovld                : std_logic := '0';
  signal dclk_file_writer_irdy        : std_logic := '0';
  signal dclk_end_of_test             : std_logic := '0';
  signal dclk_backpressure_select     : file_writer_backpressure_select_t;
  signal dclk_backpressure_select_vld : std_logic := '0';
begin

  cclk_clk_gen : process
  begin
    cclk_clk <= '1';
    wait for CCLK_PERIOD/2;
    cclk_clk <= '0';
    wait for CCLK_PERIOD/2;
  end process cclk_clk_gen;

  dclk_clk_gen : process
  begin
    dclk_clk <= '1';
    wait for DCLK_PERIOD/2;
    dclk_clk <= '0';
    wait for DCLK_PERIOD/2;
  end process dclk_clk_gen;

  cclk_stimulus : process
  begin
    cclk_rst <= '1';
    wait for 40 ns;
    wait until rising_edge(cclk_clk);
    cclk_rst <= '0';
    cclk_ctrl.clr_error_samp_drop_sticky <= '0';
    wait for 2500*DCLK_PERIOD;
    wait until rising_edge(cclk_clk);
    cclk_ctrl.clr_error_samp_drop_sticky <= '1';
    wait until rising_edge(cclk_clk);
    cclk_ctrl.clr_error_samp_drop_sticky <= '0';
    wait;
  end process cclk_stimulus;

  allow_lfsr_backpressure_true : if(ALLOW_LFSR_BACKPRESSURE) generate
    dclk_stimulus : process
    begin
      dclk_rst <= '1';
      dclk_backpressure_select <= LFSR_BP;
      dclk_backpressure_select_vld <= '1';
      wait for 40 ns;
      dclk_rst <= '0';
      wait until rising_edge(dclk_clk);
      wait for 2500*DCLK_PERIOD;
      wait until rising_edge(dclk_clk);
      dclk_backpressure_select <= NO_BP;
      wait;
    end process dclk_stimulus;
  end generate;
  allow_lfsr_backpressure_false : if(ALLOW_LFSR_BACKPRESSURE = false) generate
    dclk_stimulus : process
    begin
      dclk_rst <= '1';
      dclk_backpressure_select <= NO_BP;
      dclk_backpressure_select_vld <= '1';
      wait for 40 ns;
      dclk_rst <= '0';
      wait until rising_edge(dclk_clk);
      wait for 2500*DCLK_PERIOD;
      wait until rising_edge(dclk_clk);
      dclk_backpressure_select <= NO_BP;
      wait;
    end process dclk_stimulus;
  end generate;

  data_src : entity work.data_src
    generic map(
      DATA_BIT_WIDTH => DATA_ADC_BIT_WIDTH)
    port map(
      -- CTRL
      clk                => dclk_clk,
      rst                => dclk_rst,
      stop_on_period_cnt => '1',
      stopped            => dclk_end_of_test,
      -- OUTPUT
      odata              => dclk_data_src_odata,
      ovld               => dclk_data_src_ovld);

  uut : misc_prims.misc_prims.adc_samp_drop_generator_scdcd
    generic map(
      DATA_PIPE_LATENCY_CYCLES => DATA_PIPE_LATENCY_CYCLES)
    port map(
      -- CTRL
      cclk_clk       => cclk_clk,
      cclk_rst       => cclk_rst,
      cclk_ctrl      => cclk_ctrl,
      cclk_status    => open,
      -- INPUT
      dclk_clk       => dclk_clk,
      dclk_rst       => dclk_rst,
      dclk_idata     => dclk_data_src_odata,
      dclk_ivld      => dclk_data_src_ovld,
      -- OUTPUT
      dclk_odata     => dclk_uut_odata,
      dclk_ometadata => dclk_uut_ometadata,
      dclk_ovld      => dclk_uut_ovld,
      dclk_ordy      => dclk_file_writer_irdy);

  file_writer : entity work.file_writer
    generic map(
      FILENAME => FILENAME)
    port map(
      -- CTRL
      clk                     => dclk_clk,
      rst                     => dclk_rst,
      backpressure_select     => dclk_backpressure_select,
      backpressure_select_vld => dclk_backpressure_select_vld,
      -- INPUT
      idata                   => dclk_uut_odata,
      imetadata               => dclk_uut_ometadata,
      ivld                    => dclk_uut_ovld,
      irdy                    => dclk_file_writer_irdy);

end rtl;
