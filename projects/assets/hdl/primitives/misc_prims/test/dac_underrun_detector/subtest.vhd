library ieee;
use ieee.std_logic_1164.all, ieee.numeric_std.all, ieee.math_real.all;
library protocol;
library misc_prims; use misc_prims.misc_prims.all;

entity subtest is
  generic(
    DATA_SRC_OUTPUT_CONTINUOUS : boolean;
    FILENAME                   : string);
  port(
    backpressure_select     : in  file_writer_backpressure_select_t;
    backpressure_select_vld : in  std_logic);
end entity subtest;
architecture rtl of subtest is
  signal clk                    : std_logic := '0';
  signal rst                    : std_logic := '0';
  signal data_src_oprotocol     :
      protocol.complex_short_with_metadata.protocol_t := 
      protocol.complex_short_with_metadata.PROTOCOL_ZERO;
  signal data_src_ometadata     : metadata_dac_t;
  signal data_src_ometadata_vld : std_logic := '0';
  signal uut_irdy               : std_logic := '0';
  signal uut_oprotocol          :
      protocol.complex_short_with_metadata.protocol_t := 
      protocol.complex_short_with_metadata.PROTOCOL_ZERO;
  signal uut_ometadata          : metadata_dac_t;
  signal uut_ometadata_vld      : std_logic := '0';
  signal file_writer_irdy       : std_logic := '0';
  signal end_of_test            : std_logic := '0';
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
      oprotocol          => data_src_oprotocol,
      ometadata          => data_src_ometadata,
      ometadata_vld      => data_src_ometadata_vld,
      ordy               => uut_irdy);
    
  uut : misc_prims.misc_prims.dac_underrun_detector
    port map(
      -- CTRL
      clk           => clk,
      rst           => rst,
      status        => open,
      -- INPUT
      iprotocol     => data_src_oprotocol,
      imetadata     => data_src_ometadata,
      imetadata_vld => data_src_ometadata_vld,
      irdy          => uut_irdy,
      -- OUTPUT
      oprotocol     => uut_oprotocol,
      ometadata     => uut_ometadata,
      ometadata_vld => uut_ometadata_vld,
      ordy          => file_writer_irdy);

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
      iprotocol               => uut_oprotocol,
      imetadata               => uut_ometadata,
      imetadata_vld           => uut_ometadata_vld,
      irdy                    => file_writer_irdy);

end rtl;
