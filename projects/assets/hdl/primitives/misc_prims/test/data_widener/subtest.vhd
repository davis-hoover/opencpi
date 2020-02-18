library ieee;
use ieee.std_logic_1164.all, ieee.numeric_std.all, ieee.math_real.all;
library misc_prims; use misc_prims.misc_prims.all;
library protocol;

entity subtest is
  generic(
    FILENAME                 : string;
    BITS_PACKED_INTO_MSBS    : boolean := true);
  port(
    backpressure_select     : in  file_writer_backpressure_select_t;
    backpressure_select_vld : in  std_logic);
end entity subtest;
architecture rtl of subtest is
  signal clk                 : std_logic := '0';
  signal rst                 : std_logic := '0';
  signal data_src_odata      : data_complex_adc_t;
  signal data_src_osamp_drop : std_logic := '0';
  signal data_src_ovld       : std_logic := '0';
  signal uut_irdy            : std_logic := '0';
  signal file_writer_irdy    : std_logic := '0';
  signal end_of_test         : std_logic := '0';
  signal uut_oprotocol : protocol.complex_short_with_metadata.protocol_t :=
                         protocol.complex_short_with_metadata.PROTOCOL_ZERO;
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
      osamp_drop         => data_src_osamp_drop,
      ovld               => data_src_ovld,
      ordy               => uut_irdy);

  uut : misc_prims.misc_prims.data_widener
    generic map(
      BITS_PACKED_INTO_MSBS    => BITS_PACKED_INTO_MSBS)
    port map(
      -- CTRL
      clk        => clk,
      rst        => rst,
      -- INPUT
      idata      => data_src_odata,
      isamp_drop => data_src_osamp_drop,
      ivld       => data_src_ovld,
      irdy       => uut_irdy,
      -- OUTPUT
      oprotocol  => uut_oprotocol,
      ordy       => file_writer_irdy);

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
      irdy                    => file_writer_irdy);

end rtl;
