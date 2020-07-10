library ieee;
use ieee.std_logic_1164.all, ieee.numeric_std.all, ieee.math_real.all;
library protocol;
library misc_prims; use misc_prims.misc_prims.all;

entity subtest is
  generic(
    FILENAME              : string;
    BACKPRESSURE_SELECT   : file_writer_backpressure_select_t;
    BYPASS                : std_logic;
    MIN_NUM_DATA_PER_TIME : unsigned(TIME_DOWNSAMPLER_DATA_CNT_BIT_WIDTH-1
                            downto 0));
end entity subtest;
architecture rtl of subtest is
  signal clk                : std_logic := '0';
  signal rst                : std_logic := '0';
  signal data_src_oprotocol :
      protocol.complex_short_with_metadata.protocol_t := 
      protocol.complex_short_with_metadata.PROTOCOL_ZERO;
  signal uut_irdy           : std_logic := '0';
  signal uut_ctrl           : time_downsampler_ctrl_t;
  signal uut_oprotocol      :
      protocol.complex_short_with_metadata.protocol_t := 
      protocol.complex_short_with_metadata.PROTOCOL_ZERO;
  signal file_writer_irdy   : std_logic := '0';
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
    wait;
  end process rst_gen;

  data_src : entity work.data_src
    port map(
      -- CTRL
      clk       => clk,
      rst       => rst,
      -- OUTPUT
      oprotocol => data_src_oprotocol,
      ordy      => uut_irdy);

  uut_ctrl.bypass                <= BYPASS;
  uut_ctrl.min_num_data_per_time <= MIN_NUM_DATA_PER_TIME;

  uut : misc_prims.misc_prims.time_downsampler
    port map(
      -- CTRL
      clk       => clk,
      rst       => rst,
      ctrl      => uut_ctrl,
      -- INPUT
      iprotocol => data_src_oprotocol,
      irdy      => uut_irdy,
      -- OUTPUT
      oprotocol => uut_oprotocol,
      ordy      => file_writer_irdy);

  file_writer : entity work.file_writer
    generic map(
      FILENAME => FILENAME)
    port map(
      -- CTRL
      clk                     => clk,
      rst                     => rst,
      backpressure_select     => BACKPRESSURE_SELECT,
      backpressure_select_vld => '1',
      -- INPUT
      iprotocol               => uut_oprotocol,
      irdy                    => file_writer_irdy);

end rtl;
