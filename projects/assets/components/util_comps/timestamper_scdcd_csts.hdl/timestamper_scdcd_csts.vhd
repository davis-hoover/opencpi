-- This file is protected by Copyright. Please refer to the COPYRIGHT file
-- distributed with this source distribution.
--
-- This file is part of OpenCPI <http://www.opencpi.org>
--
-- OpenCPI is free software: you can redistribute it and/or modify it under the
-- terms of the GNU Lesser General Public License as published by the Free
-- Software Foundation, either version 3 of the License, or (at your option) any
-- later version.
--
-- OpenCPI is distributed in the hope that it will be useful, but WITHOUT ANY
-- WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
-- A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
-- details.
--
-- You should have received a copy of the GNU Lesser General Public License
-- along with this program. If not, see <http://www.gnu.org/licenses/>.
library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi; use ocpi.types.all; use ocpi.wci.all; -- remove this to avoid all
                                                    -- ocpi name collisions

library misc_prims;
use work.timestamper_scdcd_csts_pkg.all;

library timed_sample_prot; use timed_sample_prot.complex_short_timed_sample.all;
architecture rtl of worker is

  constant CTRL_IN_CDC_BIT_WIDTH : positive := 
      1 + props_in.time_correction_seconds'length + props_in.time_correction_fraction'length +
      props_in.samples_per_timestamp'length + 1;

  signal cclk_is_operating_pulse     : std_logic := '0';
  signal cclk_ctrl_in_cdc_src_enq    : std_logic := '0';
  signal cclk_ctrl_in_cdc_src_in     : std_logic_vector(
      CTRL_IN_CDC_BIT_WIDTH-1 downto 0) := (others => '0');
  signal cclk_ctrl_in_cdc_src_full_n : std_logic := '0';

  signal cclk_ctrl_in_insert_interval_fraction : bool_t;
  signal cclk_ctrl_in_insert_interval_seconds  : bool_t;
  signal iclk_ctrl_in_cdc_dst_out    : std_logic_vector(
      CTRL_IN_CDC_BIT_WIDTH-1 downto 0) := (others => '0');
  signal iclk_ctrl_in_cdc_empty_n    : std_logic := '0';

  signal iclk_interval_written_fraction       : std_logic := '0';
  signal iclk_interval_written_seconds        : std_logic := '0';
  signal iclk_bypass                                : std_logic := '0';
  signal iclk_time_correction                       : std_logic_vector(props_in.time_correction_seconds'length + props_in.time_correction_fraction'length - 1 downto 0) := (others => '0');
  signal iclk_samples_per_timestamp         : std_logic_vector(
      props_in.samples_per_timestamp'range) := (others => '0');
  signal iclk_is_operating                          : std_logic;

  signal iclk_opcode : timed_sample_prot.complex_short_timed_sample.opcode_t := SAMPLE;

  signal iclk_in_demarshaller_oprotocol : protocol_t := PROTOCOL_ZERO;
  signal iclk_in_demarshaller_oeof      : std_logic := '0';

  signal iclk_time_downsampler_irdy      : std_logic := '0';
  signal iclk_time_downsampler_oprotocol : protocol_t := PROTOCOL_ZERO;
  signal iclk_time_downsampler_oeof      : std_logic := '0';

  signal iclk_time_corrector_irdy        : std_logic := '0';
  signal iclk_time_corrector_ordy        : std_logic := '0';
  signal iclk_time_corrector_oprotocol   : protocol_t := PROTOCOL_ZERO;
  signal iclk_time_corrector_oeof        : std_logic := '0';
  signal iclk_time_downsampler_iprotocol : protocol_t := PROTOCOL_ZERO;

  signal iclk_time_downsampler_ctrl : time_downsampler_ctrl_t;

  signal iclk_time_corrector_ctrl   : time_corrector_ctrl_t;
  signal iclk_time_corrector_status : time_corrector_status_t;

  signal iclk_data_cdc_ienq      : std_logic := '0';
  signal iclk_data_cdc_ifull_n   : std_logic := '0';
  signal oclk_data_cdc_odeq      : std_logic := '0';
  signal oclk_data_cdc_oprotocol : protocol_t := PROTOCOL_ZERO;
  signal oclk_data_cdc_oeof      : std_logic := '0';
  signal oclk_data_cdc_oempty_n  : std_logic := '0';
  signal oclk_in_marshaller_oprotocol : protocol_t;

  signal oclk_out_adapter_irdy   : std_logic := '0';

  signal oclk_data   : std_logic_vector(out_out.data'range) := (others => '0');
  signal oclk_opcode : timed_sample_prot.complex_short_timed_sample.opcode_t := SAMPLE;
  signal oclk_eof    : std_logic := '0';
  signal samples_per_timestamp : unsigned(props_in.samples_per_timestamp'range);
  signal samples_per_message : unsigned(props_in.samples_per_timestamp'range);

  signal arg_40_0 : std_logic_vector(39 downto 0) := (others => '0');

begin
  -- respect system-provided output buffer size and use
  samples_per_message <= resize(props_in.ocpi_buffer_size_out srl 2, samples_per_message'length);
  samples_per_timestamp <= samples_per_message
                           when props_in.samples_per_timestamp < samples_per_message else
                           props_in.samples_per_timestamp;

  ------------------------------------------------------------------------------
  -- CTRL -> DATA CDC
  ------------------------------------------------------------------------------

  cclk_is_operating_pulse_gen : misc_prims.misc_prims.level_to_pulse_converter
    port map(
      clk   => ctl_in.clk,
      rst   => ctl_in.reset,
      level => ctl_in.is_operating,
      pulse => cclk_is_operating_pulse);

  cclk_ctrl_in_cdc_src_enq <=
      props_in.bypass_written or
      props_in.time_correction_seconds_written or
      props_in.time_correction_fraction_written or
      props_in.samples_per_timestamp_written or
      cclk_is_operating_pulse;

  cclk_ctrl_in_cdc_src_in <=
      props_in.bypass &
      std_logic_vector(props_in.time_correction_fraction) &
      std_logic_vector(props_in.time_correction_seconds) &
      std_logic_vector(samples_per_timestamp) &
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
      iclk_ctrl_in_cdc_dst_out(3+iclk_samples_per_timestamp'length-1
                               +iclk_time_correction'length-1);
  iclk_time_correction                       <=
      iclk_ctrl_in_cdc_dst_out(2+iclk_samples_per_timestamp'length-1
                               +iclk_time_correction'length-1
                               downto
                               2+iclk_samples_per_timestamp'length-1);
  iclk_samples_per_timestamp         <=
      iclk_ctrl_in_cdc_dst_out(1+iclk_samples_per_timestamp'length-1
                                downto 1);
  iclk_is_operating                          <=
      iclk_ctrl_in_cdc_dst_out(0);

  ------------------------------------------------------------------------------
  -- CTRL <- DATA CDC
  ------------------------------------------------------------------------------

  ctrl_out_cdc : cdc.cdc.fast_pulse_to_slow_sticky
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


  -- This defaults to zero, so that should be written first.
  -- The interval is only inserted on demand.
  cclk_ctrl_in_insert_interval_fraction <=
    to_bool(props_in.sampling_interval_fraction_written and props_in.sampling_interval_fraction /= 0);
  cclk_ctrl_in_insert_interval_seconds <=
    to_bool(props_in.sampling_interval_seconds_written and props_in.sampling_interval_seconds /= 0);

  interval_cdc_fraction : cdc.cdc.pulse
    port map(
      src_clk     => ctl_in.clk,
      src_rst     => ctl_in.reset,
      src_in      => cclk_ctrl_in_insert_interval_fraction,
      src_rdy     => open,  -- we know that these pulses will be far apart
      dst_clk     => in_in.clk,
      dst_rst     => in_in.reset,
      dst_out     => iclk_interval_written_fraction);

  interval_cdc_seconds : cdc.cdc.pulse
    port map(
      src_clk     => ctl_in.clk,
      src_rst     => ctl_in.reset,
      src_in      => cclk_ctrl_in_insert_interval_seconds,
      src_rdy     => open,  -- we know that these pulses will be far apart
      dst_clk     => in_in.clk,
      dst_rst     => in_in.reset,
      dst_out     => iclk_interval_written_seconds);
  ------------------------------------------------------------------------------
  -- WTI
  ------------------------------------------------------------------------------

  iclk_time_downsampler_iprotocol <= iclk_in_demarshaller_oprotocol;

  ctl_out.error <= btrue when (ctl_in.control_op = START_e) and
                   (props_in.force_error_on_invalid_time_at_start = btrue) and
                   (time_in.valid = btrue) else bfalse;

  ------------------------------------------------------------------------------
  -- DATA PATH
  ------------------------------------------------------------------------------

  iclk_opcode <=
      SAMPLE             when in_in.opcode = complex_short_timed_sample_sample_op_e  else
      TIME_TIME          when in_in.opcode = complex_short_timed_sample_time_op_e     else
      SAMPLE_INTERVAL    when in_in.opcode = complex_short_timed_sample_sample_interval_op_e else
      FLUSH              when in_in.opcode = complex_short_timed_sample_flush_op_e    else
      DISCONTINUITY      when in_in.opcode = complex_short_timed_sample_discontinuity_op_e     else
      METADATA           when in_in.opcode = complex_short_timed_sample_metadata_op_e  else
      SAMPLE;

  in_demarshaller : complex_short_timed_sample_demarshaller
    generic map(
      WSI_DATA_WIDTH => to_integer(IN_PORT_DATA_WIDTH))
    port map(
      clk       => in_in.clk,
      rst       => in_in.reset,
      -- INPUT
      idata     => in_in.data,
      ivalid    => in_in.valid,
      iready    => in_in.ready,
      isom      => in_in.som,
      ieom      => in_in.eom,
      iopcode   => iclk_opcode,
      ieof      => in_in.eof,
      itake     => in_out.take,
      -- OUTPUT
      oprotocol => iclk_in_demarshaller_oprotocol,
      oeof      => iclk_in_demarshaller_oeof,
      ordy      => iclk_time_downsampler_irdy);




  arg_40_0(39 downto 8) <= std_logic_vector(time_in.fraction);
  iclk_time_downsampler_ctrl.bypass                <= iclk_bypass; -- forces pure bypass

  iclk_time_downsampler_ctrl.time.seconds          <= std_logic_vector(time_in.seconds);
  iclk_time_downsampler_ctrl.time.fraction         <= arg_40_0;
  iclk_time_downsampler_ctrl.time_vld              <= time_in.valid;
  iclk_time_downsampler_ctrl.samples_per_timestamp <= unsigned(iclk_samples_per_timestamp);

  iclk_time_downsampler_ctrl.insert_interval_fraction       <= iclk_interval_written_fraction; -- rising edge cause insertion
  iclk_time_downsampler_ctrl.insert_interval_seconds        <= iclk_interval_written_seconds;
  -- cdc not needed  since it will only be sampled after a _written pulse *is* cdc'd;
  iclk_time_downsampler_ctrl.interval.seconds  <= std_logic_vector(props_in.sampling_interval_seconds); -- cdc not needed
  iclk_time_downsampler_ctrl.interval.fraction <= std_logic_vector(props_in.sampling_interval_fraction(63 downto 24)); 
  time_downsampler : entity work.time_downsampler
    port map(
      -- CTRL
      clk       => in_in.clk,
      rst       => in_in.reset,
      ctrl      => iclk_time_downsampler_ctrl,
      -- INPUT
      iprotocol => iclk_time_downsampler_iprotocol,
      ieof      => iclk_in_demarshaller_oeof,
      irdy      => iclk_time_downsampler_irdy,
      -- OUTPUT
      oprotocol => iclk_time_downsampler_oprotocol,
      oeof      => iclk_time_downsampler_oeof,
      ordy      => iclk_time_corrector_irdy);

  iclk_time_corrector_ctrl.bypass          <= iclk_bypass;
  iclk_time_corrector_ctrl.time_correction <= signed(iclk_time_correction(95 downto 24));
  iclk_time_corrector_ordy                 <= iclk_data_cdc_ifull_n and iclk_is_operating;

  time_corrector : entity work.time_corrector
    port map(
      -- CTRL
      clk       => in_in.clk,
      rst       => in_in.reset,
      ctrl      => iclk_time_corrector_ctrl,
      status    => iclk_time_corrector_status,
      -- INPUT
      iprotocol => iclk_time_downsampler_oprotocol,
      ieof      => iclk_time_downsampler_oeof,
      irdy      => iclk_time_corrector_irdy,
      -- OUTPUT
      oprotocol => iclk_time_corrector_oprotocol,
      oeof      => iclk_time_corrector_oeof,
      ordy      => iclk_time_corrector_ordy);

  iclk_data_cdc_ienq <= (
    iclk_time_corrector_oprotocol.sample_vld             or
    iclk_time_corrector_oprotocol.time_vld               or
    iclk_time_corrector_oprotocol.sample_interval_vld    or
    iclk_time_corrector_oprotocol.flush                  or
    iclk_time_corrector_oprotocol.discontinuity          or
    iclk_time_corrector_oprotocol.metadata_vld           or
    iclk_time_corrector_oeof
    ) and iclk_data_cdc_ifull_n;

  data_cdc : entity work.fifo_complex_short_timed_sample
    generic map(
      DEPTH    => to_integer(unsigned(DATA_CDC_DEPTH)))
    port map(
      -- INPUT
      iclk      => in_in.clk,
      irst      => in_in.reset,
      ienq      => iclk_data_cdc_ienq,
      iprotocol => iclk_time_corrector_oprotocol,
      ieof      => iclk_time_corrector_oeof,
      ifull_n   => iclk_data_cdc_ifull_n,
      -- OUTPUT
      oclk      => out_in.clk,
      odeq      => oclk_data_cdc_odeq,
      oprotocol => oclk_data_cdc_oprotocol,
      oeof      => oclk_data_cdc_oeof,
      oempty_n  => oclk_data_cdc_oempty_n);

  oclk_data_cdc_odeq <= oclk_out_adapter_irdy and oclk_data_cdc_oempty_n;


  oclk_in_marshaller_oprotocol.sample                 <= oclk_data_cdc_oprotocol.sample;
  oclk_in_marshaller_oprotocol.sample_vld             <= oclk_data_cdc_oprotocol.sample_vld and oclk_data_cdc_oempty_n;
  oclk_in_marshaller_oprotocol.time                   <= oclk_data_cdc_oprotocol.time;
  oclk_in_marshaller_oprotocol.time_vld               <= oclk_data_cdc_oprotocol.time_vld and oclk_data_cdc_oempty_n;
  oclk_in_marshaller_oprotocol.sample_interval        <= oclk_data_cdc_oprotocol.sample_interval;
  oclk_in_marshaller_oprotocol.sample_interval_vld    <= oclk_data_cdc_oprotocol.sample_interval_vld and oclk_data_cdc_oempty_n;
  oclk_in_marshaller_oprotocol.flush                  <= oclk_data_cdc_oprotocol.flush and oclk_data_cdc_oempty_n;
  oclk_in_marshaller_oprotocol.discontinuity          <= oclk_data_cdc_oprotocol.discontinuity and oclk_data_cdc_oempty_n;
  oclk_in_marshaller_oprotocol.metadata               <= oclk_data_cdc_oprotocol.metadata;
  oclk_in_marshaller_oprotocol.metadata_vld           <= oclk_data_cdc_oprotocol.metadata_vld and oclk_data_cdc_oempty_n;

  oclk_eof <= oclk_data_cdc_oempty_n and oclk_data_cdc_oeof;

  out_marshaller : complex_short_timed_sample_marshaller
    generic map(
      WSI_DATA_WIDTH    => to_integer(OUT_PORT_DATA_WIDTH),
      WSI_MBYTEEN_WIDTH => out_out.byte_enable'length)
    port map(
      clk          => out_in.clk,
      rst          => out_in.reset,
      -- INPUT
      iprotocol    => oclk_in_marshaller_oprotocol,
      ieof         => oclk_eof,
      irdy         => oclk_out_adapter_irdy,
      -- OUTPUT
      odata        => oclk_data,
      ovalid       => out_out.valid,
      obyte_enable => out_out.byte_enable,
      ogive        => out_out.give,
      osom         => out_out.som,
      oeom         => out_out.eom,
      oopcode      => oclk_opcode,
      oeof         => out_out.eof,
      oready       => out_in.ready);

  -- this only needed to avoid build bug for xsim:
  -- ERROR: [XSIM 43-3316] Signal SIGSEGV received.
  out_out.data <= oclk_data;

  out_out.opcode <=
      complex_short_timed_sample_sample_op_e            when oclk_opcode = SAMPLE          else
      complex_short_timed_sample_time_op_e              when oclk_opcode = TIME_TIME       else
      complex_short_timed_sample_sample_interval_op_e   when oclk_opcode = SAMPLE_INTERVAL else
      complex_short_timed_sample_flush_op_e             when oclk_opcode = FLUSH           else
      complex_short_timed_sample_discontinuity_op_e     when oclk_opcode = DISCONTINUITY   else
      complex_short_timed_sample_METADATA_op_e          when oclk_opcode = METADATA        else
      complex_short_timed_sample_sample_op_e;

end rtl;
