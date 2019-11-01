library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi, cdc; use ocpi.types.all; -- remove this to avoid all ocpi name collisions
library misc_prims; use misc_prims.misc_prims.all;
architecture rtl of worker is

  signal dac_clk, dac_rst                       : std_logic;
  signal opcode_samples, opcode_eos             : std_logic := '0';

  signal dac_metadata_status                    : dac_underrun_detector_status_t;

  signal dac_underrun_detector_idata            : data_complex_t;
  signal dac_underrun_detector_imetadata        : metadata_dac_t;
  signal dac_underrun_detector_ivld             : std_logic := '0';
  signal dac_underrun_detector_irdy             : std_logic := '0';
  signal dac_underrun_detector_odata            : data_complex_t;
  signal dac_underrun_detector_ometadata        : metadata_dac_t;
  signal dac_underrun_detector_ovld             : std_logic := '0';

  signal dac_data_narrower_irdy                 : std_logic := '0';
  signal dac_data_narrower_ordy                 : std_logic := '0';
  signal dac_data_narrower_odata                : data_complex_dac_t;
  signal dac_data_narrower_ometadata            : metadata_dac_t;
  signal dac_data_narrower_ovld                 : std_logic := '0';

  signal dac_clk_unused_opcode_detected         : std_logic;
  signal ctrl_clr_underrun_sticky_error         : bool_t;
  signal ctrl_clr_unused_opcode_detected_sticky : bool_t;

  signal tx_on_off_s, tx_on_off_r               : std_logic;
  signal start_samples, end_samples             : std_logic;
  signal event_pending, event_present           : std_logic;

begin
  dev_out.present <= '1';
  dac_clk <= dev_in.clk;
  in_out.clk <= dac_clk;
  
  -- DACs usally won't provide a reset along w/ their clock
  dac_rst_gen : cdc.cdc.reset
    port map(
      src_rst => ctl_in.reset,
      dst_clk => dac_clk,
      dst_rst => dac_rst);
  
  out_port_data_width_32 : if(IN_PORT_DATA_WIDTH = 32) generate

    dac_underrun_detector_idata.i <= in_in.data(15 downto  0);
    dac_underrun_detector_idata.q <= in_in.data(31 downto 16);
    

    opcode_eos <= to_bool(in_in.opcode = ComplexShortWithMetadata_end_of_samples_op_e);
    opcode_samples <= to_bool(in_in.opcode = ComplexShortWithMetadata_samples_op_e);
    dac_clk_unused_opcode_detected <= in_in.ready and
                                      not(opcode_eos or opcode_samples);
    
    --On/Off signal used to qualify underrun
    start_samples <= in_in.ready and opcode_samples and not tx_on_off_r;
    end_samples   <= (in_in.ready and opcode_eos) or in_in.eof;
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
        if its(dac_rst) or its(on_off_in.reset) then
          event_pending <= '0';
        elsif its(not on_off_in.ready) then
          event_pending <= event_present;
        else
          event_pending <= '0';
        end if;
      end if;
    end process;

    on_off_out.give <= on_off_in.ready and (event_present or event_pending);
    
    dac_underrun_detector_ivld <= in_in.valid;
    in_out.take                <= in_in.ready and dac_underrun_detector_irdy;
    ctl_out.finished           <= in_in.eof;
    
    dac_underrun_detector : misc_prims.misc_prims.dac_underrun_detector
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
        ovld      => dac_data_narrower_ovld,
        ordy      => dac_data_narrower_ordy);

    dac_data_narrower_ordy <= not dac_rst;
    dev_out.valid <= dac_data_narrower_ovld;
  
    dev_out.data_i <= std_logic_vector(resize(unsigned(dac_data_narrower_odata.i),16));
    dev_out.data_q <= std_logic_vector(resize(unsigned(dac_data_narrower_odata.i),16));
    
  end generate;
      
  ctrl_clr_underrun_sticky_error <= props_in.clr_underrun_sticky_error_written and
                                    props_in.clr_underrun_sticky_error;

  underrun : component cdc.cdc.fast_pulse_to_slow_sticky
    port map(
      fast_clk    => dac_clk,
      fast_rst    => dac_rst,
      fast_pulse  => dac_metadata_status.underrun_error,
      slow_clk    => ctl_in.clk,
      slow_rst    => ctl_in.reset,
      slow_sticky => props_out.underrun_sticky_error,
      slow_clr    => ctrl_clr_underrun_sticky_error);

  ctrl_clr_unused_opcode_detected_sticky <= props_in.clr_unused_opcode_detected_sticky_written and
                                            props_in.clr_unused_opcode_detected_sticky;

  unused_opcode : component cdc.cdc.fast_pulse_to_slow_sticky
    port map(
      fast_clk    => dac_clk,
      fast_rst    => dac_rst,
      fast_pulse  => dac_clk_unused_opcode_detected,
      slow_clk    => ctl_in.clk,
      slow_rst    => ctl_in.reset,
      slow_sticky => props_out.unused_opcode_detected_sticky,
      slow_clr    => ctrl_clr_unused_opcode_detected_sticky);
  
end rtl;
