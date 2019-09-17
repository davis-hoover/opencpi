library ieee;
use ieee.std_logic_1164.all, ieee.numeric_std.all, ieee.math_real.all;
library misc_prims; use misc_prims.misc_prims.all;

entity subtest is
  generic(
    FILENAME                 : string;
    BACKPRESSURE_SELECT      : file_writer_backpressure_select_t;
    INCLUDE_ERROR_SAMP_DROP  : boolean;
    TIME_TIME                : unsigned(METADATA_TIME_BIT_WIDTH-1 downto 0);
    TIME_CORRECTION          : signed(METADATA_TIME_BIT_WIDTH-1 downto 0);
    DATA_PIPE_LATENCY_CYCLES : natural := 0);
end entity subtest;
architecture rtl of subtest is
  signal clk                : std_logic := '0';
  signal rst                : std_logic := '0';
  signal data_src_odata     : data_complex_t;
  signal data_src_ometadata : metadata_t;
  signal data_src_ovld      : std_logic := '0';
  signal uut_irdy           : std_logic := '0';
  signal uut_ctrl           : time_corrector_ctrl_t;
  signal uut_odata          : data_complex_t;
  signal uut_ometadata      : metadata_t;
  signal uut_ovld           : std_logic := '0';
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
      DATA_BIT_WIDTH          => DATA_BIT_WIDTH,
      INCLUDE_ERROR_SAMP_DROP => INCLUDE_ERROR_SAMP_DROP,
      TIME_TIME               => TIME_TIME)
    port map(
      -- CTRL
      clk       => clk,
      rst       => rst,
      -- OUTPUT
      odata     => data_src_odata,
      ometadata => data_src_ometadata,
      ovld      => data_src_ovld,
      ordy      => uut_irdy);

  uut_ctrl.time_correction <= TIME_CORRECTION;
  uut_ctrl.time_correction_vld <= '1';

  uut : misc_prims.misc_prims.time_corrector
    generic map(
      DATA_PIPE_LATENCY_CYCLES => DATA_PIPE_LATENCY_CYCLES)
    port map(
      -- CTRL
      clk       => clk,
      rst       => rst,
      ctrl      => uut_ctrl,
      status    => open,
      -- INPUT
      idata     => data_src_odata,
      imetadata => data_src_ometadata,
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
      backpressure_select     => BACKPRESSURE_SELECT,
      backpressure_select_vld => '1',
      -- INPUT
      idata                   => uut_odata,
      imetadata               => uut_ometadata,
      ivld                    => uut_ovld,
      irdy                    => file_writer_irdy);

end rtl;
