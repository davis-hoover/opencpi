library ieee;
use ieee.std_logic_1164.all, ieee.numeric_std.all, ieee.math_real.all;
library protocol;
library misc_prims; use misc_prims.misc_prims.all;

entity subtest is
  generic(
    FILENAME                 : string;
    CTRL_FILENAME            : string;
    BACKPRESSURE_SELECT      : file_writer_backpressure_select_t;
    --INCLUDE_ERROR_SAMP_DROP  : boolean;
    BYPASS                   : std_logic;
    TIME_TIME                : unsigned(
        protocol.complex_short_with_metadata.OP_TIME_BIT_WIDTH-1 downto 0);
    TIME_TIME_VLD            : std_logic := '1';
    TIME_CORRECTION          : signed(
        protocol.complex_short_with_metadata.OP_TIME_BIT_WIDTH-1 downto 0));
end entity subtest;
architecture rtl of subtest is
  signal clk                : std_logic := '0';
  signal rst                : std_logic := '0';
  signal data_src_oprotocol :
      protocol.complex_short_with_metadata.protocol_t := 
      protocol.complex_short_with_metadata.PROTOCOL_ZERO;
  signal uut_irdy           : std_logic := '0';
  signal uut_ctrl           : time_corrector_ctrl_t;
  signal uut_status         : time_corrector_status_t;
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
    generic map(
      --INCLUDE_ERROR_SAMP_DROP => INCLUDE_ERROR_SAMP_DROP,
      TIME_TIME               => TIME_TIME,
      TIME_TIME_VLD           => TIME_TIME_VLD)
    port map(
      -- CTRL
      clk       => clk,
      rst       => rst,
      -- OUTPUT
      oprotocol => data_src_oprotocol,
      ordy      => uut_irdy);

  uut_ctrl.bypass          <= BYPASS;
  uut_ctrl.time_correction <= TIME_CORRECTION;

  uut : misc_prims.misc_prims.time_corrector
    port map(
      -- CTRL
      clk       => clk,
      rst       => rst,
      ctrl      => uut_ctrl,
      status    => uut_status,
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

  ctrl_file_writer : entity work.ctrl_file_writer
    generic map(
      FILENAME => CTRL_FILENAME)
    port map(
      -- CTRL
      clk    => clk,
      rst    => rst,
      ctrl   => uut_ctrl,
      status => uut_status);

end rtl;
