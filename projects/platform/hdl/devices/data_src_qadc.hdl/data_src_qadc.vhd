library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library cdc, util, adc, ocpi; use ocpi.wci.all;
library protocol; use protocol.complex_short_with_metadata.all;
architecture rtl of worker is

  constant BITS_PACKED_INTO_MSBS : boolean := not
      to_boolean(ADC_INPUT_IS_LSB_OF_OUT_PORT);

  signal adc_opcode : opcode_t := SAMPLES;
  signal adc_data   : std_logic_vector(
                      to_integer(unsigned(OUT_PORT_DATA_WIDTH))-1 downto 0) :=
                      (others => '0');

  signal adc_status : adc.adc.samp_drop_detector_status_t;

  signal adc_rst   : std_logic := '0';
  signal adc_idata : adc.adc.data_complex_t;

  signal adc_pending_initial_ready   : std_logic := '0';
  signal adc_pending_initial_ready_r : std_logic := '0';

  signal adc_overrun_generator_ivld       : std_logic := '0';
  signal adc_overrun_generator_odata      : adc.adc.data_complex_t;
  signal adc_overrun_generator_osamp_drop : std_logic := '0';
  signal adc_overrun_generator_ovld       : std_logic := '0';

  signal adc_data_widener_irdy      : std_logic := '0';
  signal adc_data_widener_oprotocol : protocol_t := PROTOCOL_ZERO;
  signal adc_data_widener_oeof      : std_logic := '0';

  signal dev_ready                 : bool_t;

  signal ctl_suppress_sync_opcode  : bool_t;
  signal adc_suppress_sync_opcode  : bool_t;

begin
  ------------------------------------------------------------------------------
  -- CTRL
  ------------------------------------------------------------------------------

  ctl_out.done <= to_bool(dev_ready or (ctl_in.control_op = no_op_e));
  adc_rst <= out_in.reset;
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

  props_out.samp_count_before_first_samp_drop <= to_ulong(adc_status.samp_count_before_first_samp_drop);
  props_out.num_dropped_samps <= to_ulong(adc_status.num_dropped_samps);

  -- this worker is not initialized until dev_in.clk is ticking and the out port
  -- has successfully come into reset
  adc_rst_detector_reg : util.util.reset_detector
    port map(
      clk                     => dev_in.clk,
      rst                     => out_in.reset,
      clr                     => '0',
      rst_detected            => dev_ready,
      rst_then_unrst_detected => open);

  ------------------------------------------------------------------------------
  -- out port
  ------------------------------------------------------------------------------

  adc_idata.i <= dev_in.data_i(dev_in.data_i'left downto
                               dev_in.data_i'left-
                               to_integer(unsigned(ADC_WIDTH_BITS))+1);
  adc_idata.q <= dev_in.data_q(dev_in.data_q'left downto
                               dev_in.data_q'left-
                               to_integer(unsigned(ADC_WIDTH_BITS))+1);

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
    
    ctl_suppress_sync_opcode <= props_in.suppress_sync_opcode and 
                                ctl_in.is_operating;
                                
    suppress_sync_opcode_cdc : cdc.cdc.single_bit
    generic map(
      N    =>  2,
      IREG => '1')
    port map(
      src_clk  => ctl_in.clk,
      src_rst  => ctl_in.reset,
      src_en   => '1',
      src_in   => ctl_suppress_sync_opcode,
      dst_clk  => dev_in.clk,
      dst_rst  => adc_rst,
      dst_out  => adc_suppress_sync_opcode);

    overrun_generator :
        adc.adc.samp_drop_detector
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

    data_widener : adc.adc.data_widener
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
        ordy       => out_in.ready);

    out_marshaller : protocol.complex_short_with_metadata.out_port_cswm_samples_and_sync
      generic map(
        WSI_DATA_WIDTH => to_integer(OUT_PORT_DATA_WIDTH),
        WSI_MBYTEEN_WIDTH => out_out.byte_enable'length)
      port map(
        clk               => dev_in.clk,
        rst               => adc_rst,
        -- INPUT
        iprotocol         => adc_data_widener_oprotocol,
        iready            => out_in.ready,
        isuppress_sync_op => adc_suppress_sync_opcode,
        -- OUTPUT
        odata             => adc_data,
        ovalid            => out_out.valid,
        obyte_enable      => out_out.byte_enable,
        ogive             => out_out.give,
        osom              => out_out.som,
        oeom              => out_out.eom,
        oopcode           => adc_opcode);

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
