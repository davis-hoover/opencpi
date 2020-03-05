library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library misc_prims; use misc_prims.misc_prims.all;
library cdc;
library util;
library protocol; use protocol.complex_short_with_metadata.all;
architecture rtl of worker is

  constant BITS_PACKED_INTO_MSBS : boolean := not
      to_boolean(ADC_INPUT_IS_LSB_OF_OUT_PORT);

  signal adc_opcode : opcode_t := SAMPLES;
  signal adc_data   : std_logic_vector(
                      to_integer(unsigned(OUT_PORT_DATA_WIDTH))-1 downto 0) :=
                      (others => '0');

  signal adc_status : adc_samp_drop_detector_status_t;

  signal adc_rst   : std_logic := '0';
  signal adc_idata : data_complex_adc_t;

  signal adc_pending_initial_ready   : std_logic := '0';
  signal adc_pending_initial_ready_r : std_logic := '0';

  signal adc_overrun_generator_ivld       : std_logic := '0';
  signal adc_overrun_generator_odata      : data_complex_adc_t;
  signal adc_overrun_generator_osamp_drop : std_logic := '0';
  signal adc_overrun_generator_ovld       : std_logic := '0';

  signal adc_data_widener_irdy      : std_logic := '0';
  signal adc_data_widener_oprotocol : protocol_t := PROTOCOL_ZERO;

  signal adc_out_marshaller_irdy : std_logic := '0';

begin
  ------------------------------------------------------------------------------
  -- CTRL <- DATA CDC
  ------------------------------------------------------------------------------

  -- ADCs usally won't provide a reset along w/ their clock
  adc_rst_gen : cdc.cdc.reset
    port map(
      src_rst => ctl_in.reset,
      dst_clk => dev_in.clk,
      dst_rst => adc_rst);

  ctrl_out_cdc : cdc.cdc.fast_pulse_to_slow_sticky
    port map(
      -- fast clock domain
      fast_clk    => dev_in.clk,
      fast_rst    => adc_rst,
      fast_pulse  => adc_status.error_samp_drop,
      -- slow clock domain
      slow_clk    => ctl_in.clk,
      slow_rst    => ctl_in.reset,
      slow_clr    => props_in.clr_overrun_sticky_error,
      slow_sticky => props_out.overrun_sticky_error);

  ------------------------------------------------------------------------------
  -- out port
  ------------------------------------------------------------------------------

  adc_idata.i <= dev_in.data_i(to_integer(unsigned(ADC_WIDTH_BITS))-1 downto 0);
  adc_idata.q <= dev_in.data_q(to_integer(unsigned(ADC_WIDTH_BITS))-1 downto 0);

  out_port_data_width_32 : if(OUT_PORT_DATA_WIDTH = 32) generate

    -- this can't be simply dev_in.valid, otherwise sync message would be sent
    -- before first sample message in the event ADC is streaming before the
    -- output port first becomes ready to accept data (sync means
    -- *discontinuity*, and exclaiming discontinuity when there is only "after"
    -- data, not "before"-and-"after" data, would not be correct)
    adc_overrun_generator_ivld <= dev_in.valid and
                                  (not adc_pending_initial_ready);

    adc_pending_initial_ready <= '1' when (adc_data_widener_irdy = '0') and
        (adc_pending_initial_ready_r = '1') else '0';

    adc_pending_initial_ready_reg : process(dev_in.clk)
    begin
      if(rising_edge(dev_in.clk)) then
        if(adc_rst = '1') then
          adc_pending_initial_ready_r <= '1';
        else
          adc_pending_initial_ready_r <= adc_pending_initial_ready;
        end if;
      end if;
    end process;

    overrun_generator :
        misc_prims.misc_prims.adc_samp_drop_detector
      port map(
        -- CTRL
        clk        => dev_in.clk,
        rst        => adc_rst,
        status     => adc_status,
        -- INPUT
        idata      => adc_idata,
        ivld       => adc_overrun_generator_ivld,
        -- OUTPUT
        odata      => adc_overrun_generator_odata,
        osamp_drop => adc_overrun_generator_osamp_drop,
        ovld       => adc_overrun_generator_ovld,
        ordy       => adc_data_widener_irdy);

    data_widener : misc_prims.misc_prims.data_widener
      generic map(
        BITS_PACKED_INTO_MSBS => BITS_PACKED_INTO_MSBS)
      port map(
        -- CTRL INTERFACE
        clk        => dev_in.clk,
        rst        => adc_rst,
        -- INPUT INTERFACE
        idata      => adc_overrun_generator_odata,
        isamp_drop => adc_overrun_generator_osamp_drop,
        ivld       => adc_overrun_generator_ovld,
        irdy       => adc_data_widener_irdy,
        -- OUTPUT INTERFACE
        oprotocol  => adc_data_widener_oprotocol,
        ordy       => adc_out_marshaller_irdy);

    out_marshaller : complex_short_with_metadata_marshaller_old
      generic map(
        OUT_PORT_MBYTEEN_WIDTH => out_out.byte_enable'length)
      port map(
        clk          => dev_in.clk,
        rst          => adc_rst,
        -- INPUT
        iprotocol    => adc_data_widener_oprotocol,
        irdy         => adc_out_marshaller_irdy,
        -- OUTPUT
        odata        => adc_data,
        ovalid       => out_out.valid,
        obyte_enable => out_out.byte_enable,
        ogive        => out_out.give,
        osom         => out_out.som,
        oeom         => out_out.eom,
        oopcode      => adc_opcode,
        oeof         => out_out.eof,
        oready       => out_in.ready);

    out_clk_gen : util.util.in2out
      port map(
        in_port  => dev_in.clk,
        out_port => out_out.clk);

  end generate;

  ------------------------------------------------------------------------------
  -- dev port
  ------------------------------------------------------------------------------

  -- subdevices may support multiple instances of this worker, and some may need
  -- to know how many instances of this worker are present
  dev_out.present <= '1';

  -- this only needed to avoid build bug for xsim:
  -- ERROR: [XSIM 43-3316] Signal SIGSEGV received.
  out_out.data <= adc_data;

  out_out.opcode <=
      ComplexShortWithMetadata_samples_op_e  when adc_opcode = SAMPLES   else
      ComplexShortWithMetadata_time_op_e     when adc_opcode = TIME_TIME else
      ComplexShortWithMetadata_interval_op_e when adc_opcode = INTERVAL  else
      ComplexShortWithMetadata_flush_op_e    when adc_opcode = FLUSH     else
      ComplexShortWithMetadata_sync_op_e     when adc_opcode = SYNC      else
      ComplexShortWithMetadata_samples_op_e;

end rtl;
