library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi, cdc; use ocpi.types.all; -- remove this to avoid all ocpi name collisions
library util;
library protocol; use protocol.complex_short_with_metadata.all;
library misc_prims; use misc_prims.misc_prims.all;
architecture rtl of worker is

  signal dac_rst                                : std_logic;
  signal opcode_samples, opcode_eos             : std_logic := '0';

  signal dac_metadata_status                    : dac_underrun_detector_status_t;
  signal dac_opcode                             : opcode_t := SAMPLES;
  signal dac_in_demarshaller_oprotocol          : protocol_t := PROTOCOL_ZERO;
  signal dac_in_demarshaller_oeof               : std_logic := '0';

  signal dac_underrun_detector_imetadata        : metadata_dac_t;
  signal dac_underrun_detector_irdy             : std_logic := '0';
  signal dac_underrun_detector_oprotocol        :
      protocol.complex_short_with_metadata.protocol_t;
  signal dac_underrun_detector_ometadata        : metadata_dac_t;
  signal dac_underrun_detector_ometadata_vld    : std_logic := '0';

  signal dac_data_narrower_irdy                 : std_logic := '0';
  signal dac_data_narrower_ordy                 : std_logic := '0';
  signal dac_data_narrower_odata                : data_complex_dac_t;
  signal dac_data_narrower_ometadata            : metadata_dac_t;
  signal dac_data_narrower_ometadata_vld        : std_logic := '0';

  signal dac_clk_unused_opcode_detected         : std_logic;
  signal ctrl_clr_underrun_sticky_error         : bool_t;
  signal ctrl_clr_unused_opcode_detected_sticky : bool_t;

  signal tx_on_off_s, tx_on_off_r               : std_logic;
  signal start_samples, end_samples             : std_logic;
  signal event_pending, event_present           : std_logic;

begin
  dev_out.present <= '1';
  in_clk_gen : util.util.in2out
    port map(
      in_port  => dev_in.clk,
      out_port => in_out.clk);
  
  -- DACs usally won't provide a reset along w/ their clock
  dac_rst_gen : cdc.cdc.reset
    port map(
      src_rst => ctl_in.reset,
      dst_clk => dev_in.clk,
      dst_rst => dac_rst);

  dac_opcode <=
      SAMPLES   when in_in.opcode = ComplexShortWithMetadata_samples_op_e  else
      TIME_TIME when in_in.opcode = ComplexShortWithMetadata_time_op_e     else
      INTERVAL  when in_in.opcode = ComplexShortWithMetadata_interval_op_e else
      FLUSH     when in_in.opcode = ComplexShortWithMetadata_flush_op_e    else
      SYNC      when in_in.opcode = ComplexShortWithMetadata_sync_op_e     else
      SAMPLES;
  
  out_port_data_width_32 : if(IN_PORT_DATA_WIDTH = 32) generate

    in_demarshaller : complex_short_with_metadata_demarshaller
      generic map(
        WSI_DATA_WIDTH => to_integer(IN_PORT_DATA_WIDTH))
      port map(
        clk       => dev_in.clk,
        rst       => dac_rst,
        -- INPUT
        idata     => in_in.data,
        ivalid    => in_in.valid,
        iready    => in_in.ready,
        isom      => in_in.som,
        ieom      => in_in.eom,
        iopcode   => dac_opcode,
        ieof      => in_in.eof,
        itake     => in_out.take,
        -- OUTPUT
        oprotocol => dac_in_demarshaller_oprotocol,
        oeof      => dac_in_demarshaller_oeof,
        ordy      => dac_underrun_detector_irdy);

    dac_clk_unused_opcode_detected <=
        not(dac_in_demarshaller_oprotocol.end_of_samples or
        dac_in_demarshaller_oprotocol.samples_vld);
    
    --On/Off signal used to qualify underrun
    start_samples <= dac_in_demarshaller_oprotocol.samples_vld and
                     not tx_on_off_r;
    end_samples   <= dac_in_demarshaller_oprotocol.end_of_samples or
                     dac_in_demarshaller_oeof;
    tx_on_off_s   <= start_samples or (tx_on_off_r and not end_samples);

    process(dev_in.clk)
    begin
      if rising_edge(dev_in.clk) then
        if its(dac_rst) then
          tx_on_off_r <= '0';
        else
          tx_on_off_r <= tx_on_off_s;
        end if;
      end if;
    end process;

    dac_underrun_detector_imetadata.underrun_error <= '0';
    dac_underrun_detector_imetadata.ctrl_tx_on_off <= tx_on_off_s;

    --On/Off port logic
    event_present <= start_samples or end_samples;
    
    --Note that OWD includes Clock='in' for on_off port which means that the
    --on_off port operates in the same clock domain as the in port (dev_in.clk)
    process(dev_in.clk)
    begin
      if rising_edge(dev_in.clk) then
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
    
    ctl_out.finished <= dac_in_demarshaller_oeof;
    
    dac_underrun_detector : misc_prims.misc_prims.dac_underrun_detector
      port map(
        -- CTRL
        clk           => dev_in.clk,
        rst           => dac_rst,
        status        => dac_metadata_status,
        -- INPUT
        iprotocol     => dac_in_demarshaller_oprotocol,
        imetadata     => dac_underrun_detector_imetadata,
        imetadata_vld => tx_on_off_s,
        irdy          => dac_underrun_detector_irdy,
        -- OUTPUT
        oprotocol     => dac_underrun_detector_oprotocol,
        ometadata     => dac_underrun_detector_ometadata,
        ometadata_vld => dac_underrun_detector_ometadata_vld,
        ordy          => dac_data_narrower_irdy);

    data_narrower : misc_prims.misc_prims.data_narrower
      generic map(
        BITS_PACKED_INTO_LSBS => to_boolean(DAC_OUTPUT_IS_LSB_OF_IN_PORT))
      port map(
        -- CTRL INTERFACE
        clk           => dev_in.clk,
        rst           => dac_rst,
        -- INPUT INTERFACE
        iprotocol     => dac_underrun_detector_oprotocol,
        imetadata     => dac_underrun_detector_ometadata,
        imetadata_vld => dac_underrun_detector_ometadata_vld,
        irdy          => dac_data_narrower_irdy,
        -- OUTPUT INTERFACE
        odata         => dac_data_narrower_odata,
        ometadata     => dac_data_narrower_ometadata,
        ometadata_vld => dac_data_narrower_ometadata_vld,
        ordy          => dac_data_narrower_ordy);

    dac_data_narrower_ordy <= not dac_rst;
    dev_out.valid <= dac_data_narrower_ometadata_vld;
  
    dev_out.data_i <= std_logic_vector(resize(unsigned(dac_data_narrower_odata.i),16));
    dev_out.data_q <= std_logic_vector(resize(unsigned(dac_data_narrower_odata.q),16));
    
  end generate;
      
  ctrl_clr_underrun_sticky_error <= props_in.clr_underrun_sticky_error_written and
                                    props_in.clr_underrun_sticky_error;

  underrun : component cdc.cdc.fast_pulse_to_slow_sticky
    port map(
      fast_clk    => dev_in.clk,
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
      fast_clk    => dev_in.clk,
      fast_rst    => dac_rst,
      fast_pulse  => dac_clk_unused_opcode_detected,
      slow_clk    => ctl_in.clk,
      slow_rst    => ctl_in.reset,
      slow_sticky => props_out.unused_opcode_detected_sticky,
      slow_clr    => ctrl_clr_unused_opcode_detected_sticky);
  
end rtl;
