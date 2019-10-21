library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi; use ocpi.types.all; use ocpi.wci.all; -- remove this to avoid all
                                                    -- ocpi name collisions
library misc_prims;
use misc_prims.misc_prims.all;
use misc_prims.ocpi.all;
use misc_prims.cdc.all;
library cdc; use cdc.cdc.all;
architecture rtl of worker is

  constant CTRL_IN_CDC_BIT_WIDTH : positive := 
      1 + props_in.time_correction'length +
      props_in.min_num_samples_per_timestamp'length + 1;

  constant DATA_CDC_BIT_WIDTH : positive := 
      2*DATA_BIT_WIDTH+METADATA_BIT_WIDTH;

  signal cclk_is_operating_pulse     : std_logic := '0';
  signal cclk_ctrl_in_cdc_src_enq    : std_logic := '0';
  signal cclk_ctrl_in_cdc_src_in     : std_logic_vector(
      CTRL_IN_CDC_BIT_WIDTH-1 downto 0) := (others => '0');
  signal cclk_ctrl_in_cdc_src_full_n : std_logic := '0';

  signal iclk_ctrl_in_cdc_dst_out    : std_logic_vector(
      CTRL_IN_CDC_BIT_WIDTH-1 downto 0) := (others => '0');
  signal iclk_ctrl_in_cdc_empty_n    : std_logic := '0';

  signal iclk_bypass                                : std_logic := '0';
  signal iclk_time_correction                       : std_logic_vector(
      props_in.time_correction'range) := (others => '0');
  signal iclk_min_num_samples_per_timestamp         : std_logic_vector(
      props_in.min_num_samples_per_timestamp'range) := (others => '0');
  signal iclk_is_operating                          : std_logic := '0';

  signal iclk_opcode : complex_short_with_metadata_opcode_t := SAMPLES;

  signal iclk_in_adapter_odata           : data_complex_t := data_complex_zero;
  signal iclk_in_adapter_ometadata       : metadata_t := metadata_zero;
  signal iclk_in_adapter_ovld            : std_logic := '0';

  signal iclk_time_downsampler_imetadata : metadata_t := metadata_zero;
  signal iclk_time_downsampler_irdy      : std_logic := '0';
  signal iclk_time_downsampler_odata     : data_complex_t := data_complex_zero;
  signal iclk_time_downsampler_ometadata : metadata_t := metadata_zero;
  signal iclk_time_downsampler_ovld      : std_logic := '0';

  signal iclk_time_corrector_irdy        : std_logic := '0';
  signal iclk_time_corrector_odata       : data_complex_t := data_complex_zero;
  signal iclk_time_corrector_ometadata   : metadata_t := metadata_zero;
  signal iclk_time_corrector_ovld        : std_logic := '0';

  signal iclk_time_downsampler_ctrl : time_downsampler_ctrl_t;

  signal iclk_time_corrector_ctrl   : time_corrector_ctrl_t;
  signal iclk_time_corrector_status : time_corrector_status_t;

  signal iclk_data_cdc_iinfo    : info_t := info_zero;
  signal iclk_data_cdc_ienq     : std_logic := '0';
  signal iclk_data_cdc_ifull_n  : std_logic := '0';
  signal oclk_data_cdc_odeq     : std_logic := '0';
  signal oclk_data_cdc_oinfo    : info_t := info_zero;
  signal oclk_data_cdc_oempty_n : std_logic := '0';

  signal oclk_out_adapter_irdy      : std_logic := '0';
  signal oclk_out_adapter_ivld      : std_logic := '0';

  signal oclk_data   : std_logic_vector(out_out.data'range) := (others => '0');
  signal oclk_opcode : complex_short_with_metadata_opcode_t := SAMPLES;
begin

  ------------------------------------------------------------------------------
  -- CTRL -> DATA CDC
  ------------------------------------------------------------------------------

  cclk_is_operating_pulse_gen : level_to_pulse_converter
    port map(
      clk   => ctl_in.clk,
      rst   => ctl_in.reset,
      level => ctl_in.is_operating,
      pulse => cclk_is_operating_pulse);

  cclk_ctrl_in_cdc_src_enq <=
      props_in.bypass_written or
      props_in.time_correction_written or
      props_in.min_num_samples_per_timestamp_written or
      cclk_is_operating_pulse;

  cclk_ctrl_in_cdc_src_in <=
      props_in.bypass &
      std_logic_vector(props_in.time_correction) &
      std_logic_vector(props_in.min_num_samples_per_timestamp) &
      ctl_in.is_operating;

  ctrl_in_cdc : cdc.cdc.fifo
    generic map(
      WIDTH       => CTRL_IN_CDC_BIT_WIDTH,
      DEPTH       => to_integer(unsigned(CTRL_IN_CDC_DEPTH)))
    port map(
      src_CLK     => ctl_in.clk,
      src_RST     => ctl_in.reset,
      src_ENQ     => cclk_ctrl_in_cdc_src_enq,
      src_in      => cclk_ctrl_in_cdc_src_in ,
      src_FULL_N  => cclk_ctrl_in_cdc_src_full_n,
      dst_CLK     => in_in.clk,
      dst_DEQ     => iclk_ctrl_in_cdc_empty_n,
      dst_out     => iclk_ctrl_in_cdc_dst_out,
      dst_EMPTY_N => iclk_ctrl_in_cdc_empty_n);

  iclk_bypass                                <=
      iclk_ctrl_in_cdc_dst_out(3+iclk_min_num_samples_per_timestamp'length-1
                               +iclk_time_correction'length-1);
  iclk_time_correction                       <=
      iclk_ctrl_in_cdc_dst_out(2+iclk_min_num_samples_per_timestamp'length-1
                               +iclk_time_correction'length-1
                               downto
                               2+iclk_min_num_samples_per_timestamp'length-1);
  iclk_min_num_samples_per_timestamp         <=
      iclk_ctrl_in_cdc_dst_out(1+iclk_min_num_samples_per_timestamp'length-1
                                downto 1);
  iclk_is_operating                          <=
      iclk_ctrl_in_cdc_dst_out(0);

  ------------------------------------------------------------------------------
  -- CTRL <- DATA CDC
  ------------------------------------------------------------------------------

  ctrl_out_cdc : fast_pulse_to_slow_sticky
    port map(
      -- fast clock domain
      fast_clk    => in_in.clk,
      fast_rst    => in_in.reset,
      fast_pulse  => iclk_time_corrector_status.overflow,
      -- slow clock domain
      slow_clk    => ctl_in.clk,
      slow_rst    => ctl_in.reset,
      slow_clr    => props_in.clr_correction_overflow_sticky,
      slow_sticky => props_out.correction_overflow_sticky);

  ------------------------------------------------------------------------------
  -- WTI
  ------------------------------------------------------------------------------

  iclk_time_downsampler_imetadata.eof <=
      iclk_in_adapter_ometadata.eof;
  iclk_time_downsampler_imetadata.flush <=
      iclk_in_adapter_ometadata.flush;
  iclk_time_downsampler_imetadata.error_samp_drop <=
      iclk_in_adapter_ometadata.error_samp_drop;
  iclk_time_downsampler_imetadata.data_vld <=
      iclk_in_adapter_ometadata.data_vld;
  iclk_time_downsampler_imetadata.time     <= time_in.seconds &
                                              time_in.fraction;
  iclk_time_downsampler_imetadata.time_vld <= '1' when (time_in.valid = btrue)
                                              and (props_in.bypass = bfalse)
                                              else '0';
  iclk_time_downsampler_imetadata.samp_period <=
      iclk_in_adapter_ometadata.samp_period;
  iclk_time_downsampler_imetadata.samp_period_vld <=
      iclk_in_adapter_ometadata.samp_period_vld;

  time_out.clk <= in_in.clk;

  ctl_out.error <= btrue when (ctl_in.control_op = START_e) and
                   (props_in.force_error_on_invalid_time_at_start = btrue) and
                   (time_in.valid = btrue) else bfalse;

  ------------------------------------------------------------------------------
  -- DATA PATH
  ------------------------------------------------------------------------------

  iclk_opcode <=
      SAMPLES   when in_in.opcode = ComplexShortWithMetadata_samples_op_e  else
      TIME_TIME when in_in.opcode = ComplexShortWithMetadata_time_op_e     else
      INTERVAL  when in_in.opcode = ComplexShortWithMetadata_interval_op_e else
      FLUSH     when in_in.opcode = ComplexShortWithMetadata_flush_op_e    else
      SYNC      when in_in.opcode = ComplexShortWithMetadata_sync_op_e     else
      USER      when in_in.opcode = ComplexShortWithMetadata_user_op_e     else
      SAMPLES;

  in_adapter_32 : if IN_PORT_DATA_WIDTH = 32 generate

    in_adapter : misc_prims.ocpi.cswm_prot_in_adapter_dw32_clkin
      port map(
        -- INPUT
        iclk      => in_in.clk,
        irst      => in_in.reset,
        idata     => in_in.data,
        ivalid    => in_in.valid,
        iready    => in_in.ready,
        isom      => in_in.som,
        ieom      => in_in.eom,
        iopcode   => iclk_opcode,
        ieof      => in_in.eof,
        itake     => in_out.take,
        -- OUTPUT
        odata     => iclk_in_adapter_odata,
        ometadata => iclk_in_adapter_ometadata,
        ovld      => iclk_in_adapter_ovld,
        ordy      => iclk_time_downsampler_irdy);

  end generate in_adapter_32;

  iclk_time_downsampler_ctrl.bypass                    <= iclk_bypass;
  iclk_time_downsampler_ctrl.min_num_data_per_time     <=
      unsigned(iclk_min_num_samples_per_timestamp);
  iclk_time_downsampler_ctrl.min_num_data_per_time_vld <=
      iclk_is_operating;

  time_downsampler : misc_prims.misc_prims.time_downsampler
    generic map(
      DATA_PIPE_LATENCY_CYCLES => 0)
    port map(
      -- CTRL
      clk       => in_in.clk,
      rst       => in_in.reset,
      ctrl      => iclk_time_downsampler_ctrl,
      -- INPUT
      idata     => iclk_in_adapter_odata,
      imetadata => iclk_time_downsampler_imetadata,
      ivld      => iclk_in_adapter_ovld,
      irdy      => iclk_time_downsampler_irdy,
      -- OUTPUT
      odata     => iclk_time_downsampler_odata,
      ometadata => iclk_time_downsampler_ometadata,
      ovld      => iclk_time_downsampler_ovld,
      ordy      => iclk_time_corrector_irdy);

  iclk_time_corrector_ctrl.bypass              <= iclk_bypass;
  iclk_time_corrector_ctrl.time_correction     <= signed(iclk_time_correction);
  iclk_time_corrector_ctrl.time_correction_vld <= iclk_is_operating;

  time_corrector : misc_prims.misc_prims.time_corrector
    generic map(
      DATA_PIPE_LATENCY_CYCLES => 0)
    port map(
      -- CTRL
      clk       => in_in.clk,
      rst       => in_in.reset,
      ctrl      => iclk_time_corrector_ctrl,
      status    => iclk_time_corrector_status,
      -- INPUT
      idata     => iclk_time_downsampler_odata,
      imetadata => iclk_time_downsampler_ometadata,
      ivld      => iclk_time_downsampler_ovld,
      irdy      => iclk_time_corrector_irdy,
      -- OUTPUT
      odata     => iclk_time_corrector_odata,
      ometadata => iclk_time_corrector_ometadata,
      ovld      => iclk_time_corrector_ovld,
      ordy      => iclk_data_cdc_ifull_n);

  iclk_data_cdc_iinfo.data     <= iclk_time_corrector_odata;
  iclk_data_cdc_iinfo.metadata <= iclk_time_corrector_ometadata;
  iclk_data_cdc_ienq <= iclk_time_corrector_ovld and iclk_data_cdc_ifull_n;

  data_cdc : misc_prims.cdc.fifo_info
    generic map(
      DEPTH    => to_integer(unsigned(DATA_CDC_DEPTH)))
    port map(
      -- INPUT
      iclk     => in_in.clk,
      irst     => in_in.reset,
      ienq     => iclk_data_cdc_ienq,
      iinfo    => iclk_data_cdc_iinfo,
      ifull_n  => iclk_data_cdc_ifull_n,
      -- OUTPUT
      oclk     => out_in.clk,
      odeq     => oclk_data_cdc_odeq,
      oinfo    => oclk_data_cdc_oinfo,
      oempty_n => oclk_data_cdc_oempty_n);

  oclk_data_cdc_odeq <= oclk_out_adapter_irdy and oclk_data_cdc_oempty_n;
  oclk_out_adapter_ivld <= oclk_data_cdc_oempty_n and oclk_out_adapter_irdy;

  out_adapter_32 : if IN_PORT_DATA_WIDTH = 32 generate

    out_adapter : misc_prims.ocpi.cswm_prot_out_adapter_dw32_clkin
      generic map(
        OUT_PORT_MBYTEEN_WIDTH => out_out.byte_enable'length)
      port map(
        -- INPUT
        idata        => oclk_data_cdc_oinfo.data,
        imetadata    => oclk_data_cdc_oinfo.metadata,
        ivld         => oclk_out_adapter_ivld,
        irdy         => oclk_out_adapter_irdy,
        -- OUTPUT
        oclk         => out_in.clk,
        orst         => out_in.reset,
        odata        => oclk_data,
        ovalid       => out_out.valid,
        obyte_enable => out_out.byte_enable,
        ogive        => out_out.give,
        osom         => out_out.som,
        oeom         => out_out.eom,
        oopcode      => oclk_opcode,
        oeof         => out_out.eof,
        oready       => out_in.ready);

  end generate out_adapter_32;

  -- this only needed to avoid build bug for xsim:
  -- ERROR: [XSIM 43-3316] Signal SIGSEGV received.
  out_out.data <= oclk_data;

  out_out.opcode <=
      ComplexShortWithMetadata_samples_op_e  when oclk_opcode = SAMPLES   else
      ComplexShortWithMetadata_time_op_e     when oclk_opcode = TIME_TIME else
      ComplexShortWithMetadata_interval_op_e when oclk_opcode = INTERVAL  else
      ComplexShortWithMetadata_flush_op_e    when oclk_opcode = FLUSH     else
      ComplexShortWithMetadata_sync_op_e     when oclk_opcode = SYNC      else
      ComplexShortWithMetadata_user_op_e     when oclk_opcode = USER      else
      ComplexShortWithMetadata_samples_op_e;

end rtl;
