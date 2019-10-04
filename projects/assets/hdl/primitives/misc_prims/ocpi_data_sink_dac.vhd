library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;
library misc_prims; use misc_prims.misc_prims.all; use misc_prims.ocpi.all;
library ocpi; use ocpi.types.all;
library cdc;

entity ocpi_data_sink_dac is
  generic(
    DAC_WIDTH_BITS                         : UChar_t;
    DATA_PIPE_LATENCY_CYCLES               : ULong_t;
    IN_PORT_DATA_WIDTH                     : ULong_t;
    DAC_OUTPUT_IS_LSB_OF_IN_PORT           : Bool_t;
    IN_PORT_MBYTEEN_WIDTH                  : positive);
  port(
    -- CTRL
    ctrl_clk                               : in  std_logic;
    ctrl_rst                               : in  bool_t;
    ctrl_underrun_sticky_error             : out bool_t;
    ctrl_clr_underrun_sticky_error         : in bool_t;
    ctrl_unused_opcode_detected_sticky     : out bool_t;
    ctrl_clr_unused_opcode_detected_sticky : in bool_t;
    ctrl_finished                          : out bool_t;
    -- INPUT
    dac_in_clk                             : out std_logic;
    dac_in_take                            : out bool_t;
    dac_in_data                            : in  std_logic_vector(to_integer(unsigned(
                                                                  IN_PORT_DATA_WIDTH))-1 downto 0);
    dac_in_opcode                          : in  complex_short_with_metadata_opcode_t;
    dac_in_ready                           : in  bool_t;
    dac_in_valid                           : in  bool_t;
    dac_in_eof                             : in  bool_t;
    -- ON/OFF OUTPUT
    on_off_out_reset                       : in  bool_t;
    on_off_out_ready                       : in  bool_t;
    on_off_out_opcode                      : out bool_t;
    on_off_out_give                        : out bool_t;
    -- DEV SIGNAL OUTPUT (Matches dac-16-signals bundle)
    dac_dev_clk                            : in  std_logic;
    dac_dev_data_i                         : out std_logic_vector(15 downto 0);
    dac_dev_data_q                         : out std_logic_vector(15 downto 0);
    dac_dev_valid                          : out std_logic;
    dac_dev_take                           : in  std_logic;
    dac_dev_present                        : out std_logic);
end entity ocpi_data_sink_dac;

architecture rtl of ocpi_data_sink_dac is
  signal dac_clk                         : std_logic;
  signal dac_rst                         : std_logic;
  signal opcode_samples, opcode_eos      : std_logic := '0';

  signal dac_metadata_status             : dac_underrun_detector_status_t;

  signal dac_underrun_detector_idata     : data_complex_t;
  signal dac_underrun_detector_imetadata : metadata_dac_t;
  signal dac_underrun_detector_ivld      : std_logic := '0';
  signal dac_underrun_detector_irdy      : std_logic := '0';
  signal dac_underrun_detector_odata     : data_complex_t;
  signal dac_underrun_detector_ometadata : metadata_dac_t;
  signal dac_underrun_detector_ovld      : std_logic := '0';

  signal dac_data_narrower_irdy          : std_logic := '0';
  signal dac_data_narrower_odata         : data_complex_dac_t;
  signal dac_data_narrower_ometadata     : metadata_dac_t;
  signal dac_data_narrower_ovld          : std_logic := '0';

  signal dac_clk_unused_opcode_detected  : std_logic;

  signal tx_on_off_s, tx_on_off_r        : std_logic;
  signal start_samples, end_samples      : std_logic;
  signal event_pending, event_present    : std_logic;
  
begin
  dac_clk <= dac_dev_clk;
  dac_in_clk <= dac_clk;
  
  -- DACs usally won't provide a reset along w/ their clock
  dac_rst_gen : cdc.cdc.reset
    port map(
      src_rst => ctrl_rst,
      dst_clk => dac_clk,
      dst_rst => dac_rst);
  
  out_port_data_width_32 : if(IN_PORT_DATA_WIDTH = 32) generate

    dac_underrun_detector_idata.i <= dac_in_data(15 downto  0);
    dac_underrun_detector_idata.q <= dac_in_data(31 downto 16);
    
    data_pipe_latency_cycles_0 : if(DATA_PIPE_LATENCY_CYCLES = 0) generate

      opcode_eos                     <= to_bool(dac_in_opcode=END_OF_SAMPLES);
      opcode_samples                 <= to_bool(dac_in_opcode=SAMPLES);
      dac_clk_unused_opcode_detected <= dac_in_ready and
                                        not(opcode_eos or opcode_samples);
  
      --On/Off signal used to qualify underrun
      start_samples <= dac_in_ready and opcode_samples and not tx_on_off_r;
      end_samples   <= (dac_in_ready and opcode_eos) or dac_in_eof;
      tx_on_off_s   <= start_samples or (tx_on_off_r and not end_samples);

      process(dac_clk)
      begin
        if rising_edge(dac_clk) then
          if its(dac_rst) then
            tx_on_off_r <= '0';
          else
            tx_on_off_r <= tx_on_off_s;
          end if;
        end if;
      end process;

      dac_underrun_detector_imetadata.ctrl_tx_on_off <= tx_on_off_s;

      --On/Off port logic
      event_present <= start_samples or end_samples;
      
      process(dac_clk)
      begin
        if rising_edge(dac_clk) then
          --reset is used as a way to know whether port is connected
          if its(dac_rst) or its(on_off_out_reset) then
            event_pending <= '0';
          elsif its(not on_off_out_ready) then
            event_pending <= event_present;
          else
            event_pending <= '0';
          end if;
        end if;
      end process;

      on_off_out_give <= on_off_out_ready and (event_present or event_pending);
      
      dac_underrun_detector_ivld <= dac_in_valid;
      dac_in_take                <= dac_in_ready and dac_underrun_detector_irdy;
      ctrl_finished              <= dac_in_eof;
      
      dac_underrun_detector : misc_prims.misc_prims.dac_underrun_detector
        generic map(
          DATA_PIPE_LATENCY_CYCLES => 0)
        port map(
          -- CTRL
          clk       => dac_clk,
          rst       => dac_rst,
          status    => dac_metadata_status,
          -- INPUT
          idata     => dac_underrun_detector_idata,
          imetadata => dac_underrun_detector_imetadata,
          ivld      => dac_underrun_detector_ivld,
          irdy      => dac_underrun_detector_irdy,
          -- OUTPUT
          odata     => dac_underrun_detector_odata,
          ometadata => dac_underrun_detector_ometadata,
          ovld      => dac_underrun_detector_ovld,
          ordy      => dac_data_narrower_irdy);

      data_narrower : misc_prims.misc_prims.data_narrower
        generic map(
          DATA_PIPE_LATENCY_CYCLES => 0,
          BITS_PACKED_INTO_LSBS    => to_boolean(DAC_OUTPUT_IS_LSB_OF_IN_PORT))
        port map(
          -- CTRL INTERFACE
          clk       => dac_clk,
          rst       => dac_rst,
          -- INPUT INTERFACE
          idata     => dac_underrun_detector_odata,
          imetadata => dac_underrun_detector_ometadata,
          ivld      => dac_underrun_detector_ovld,
          irdy      => dac_data_narrower_irdy,
          -- OUTPUT INTERFACE
          odata     => dac_data_narrower_odata,
          ometadata => dac_data_narrower_ometadata,
          ovld      => dac_dev_valid,
          ordy      => dac_dev_take);

      BITS_PACKED_INTO_LSBS_true : if(DAC_OUTPUT_IS_LSB_OF_IN_PORT = btrue) generate
        dac_dev_data_i <= std_logic_vector(resize(unsigned(dac_data_narrower_odata.i),16));
        dac_dev_data_q <= std_logic_vector(resize(unsigned(dac_data_narrower_odata.i),16));
      end generate;

      BITS_PACKED_INTO_LSBS_false : if(DAC_OUTPUT_IS_LSB_OF_IN_PORT = bfalse) generate
        dac_dev_data_i <= std_logic_vector(
          shift_left(unsigned(dac_data_narrower_odata.i), 16-to_integer(DAC_WIDTH_BITS)));
        dac_dev_data_q <= std_logic_vector(
          shift_left(unsigned(dac_data_narrower_odata.q), 16-to_integer(DAC_WIDTH_BITS)));
      end generate;
      
    end generate;
    
  end generate;
      
  underrun : component cdc.cdc.fast_pulse_to_slow_sticky
    port map(
      fast_clk    => dac_clk,
      fast_rst    => dac_rst,
      fast_pulse  => dac_metadata_status.underrun_error,
      slow_clk    => ctrl_clk,
      slow_rst    => ctrl_rst,
      slow_sticky => ctrl_underrun_sticky_error,
      slow_clr    => ctrl_clr_underrun_sticky_error);

  unused_opcode : component cdc.cdc.fast_pulse_to_slow_sticky
    port map(
      fast_clk    => dac_clk,
      fast_rst    => dac_rst,
      fast_pulse  => dac_clk_unused_opcode_detected,
      slow_clk    => ctrl_clk,
      slow_rst    => ctrl_rst,
      slow_sticky => ctrl_unused_opcode_detected_sticky,
      slow_clr    => ctrl_clr_unused_opcode_detected_sticky);

  dac_dev_present <= '1';
end rtl;
