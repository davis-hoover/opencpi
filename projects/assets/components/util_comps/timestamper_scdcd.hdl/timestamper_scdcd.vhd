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
use misc_prims.misc_prims.all;
library cdc; use cdc.cdc.all;
library protocol; use protocol.complex_short_with_metadata.all;
architecture rtl of worker is

  constant CTRL_IN_CDC_BIT_WIDTH : positive := 
      1 + props_in.time_correction'length +
      props_in.min_num_samples_per_timestamp'length + 1;

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

  signal iclk_opcode : protocol.complex_short_with_metadata.opcode_t := SAMPLES;

  signal iclk_in_demarshaller_oprotocol : protocol_t := PROTOCOL_ZERO;
  signal iclk_in_demarshaller_oeof      : std_logic := '0';

  signal iclk_time_downsampler_irdy      : std_logic := '0';
  signal iclk_time_downsampler_oprotocol : protocol_t := PROTOCOL_ZERO;
  signal iclk_time_downsampler_oeof      : std_logic := '0';

  signal iclk_time_corrector_irdy        : std_logic := '0';
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

  signal oclk_out_adapter_irdy   : std_logic := '0';

  signal oclk_data   : std_logic_vector(out_out.data'range) := (others => '0');
  signal oclk_opcode : protocol.complex_short_with_metadata.opcode_t := SAMPLES;
  signal oclk_eof    : std_logic := '0';
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

  iclk_time_downsampler_iprotocol.samples <= 
      iclk_in_demarshaller_oprotocol.samples;
  iclk_time_downsampler_iprotocol.samples_vld <=
      iclk_in_demarshaller_oprotocol.samples_vld;
  iclk_time_downsampler_iprotocol.time.sec <=
      std_logic_vector(time_in.seconds);
  iclk_time_downsampler_iprotocol.time.fract_sec <=
      std_logic_vector(time_in.fraction);
  iclk_time_downsampler_iprotocol.time_vld <= '1' when (time_in.valid = btrue)
                                              and (props_in.bypass = bfalse)
                                              else '0';
  iclk_time_downsampler_iprotocol.interval <=
      iclk_in_demarshaller_oprotocol.interval;
  iclk_time_downsampler_iprotocol.interval_vld <=
      iclk_in_demarshaller_oprotocol.interval_vld;
  iclk_time_downsampler_iprotocol.flush <=
      iclk_in_demarshaller_oprotocol.flush;
  iclk_time_downsampler_iprotocol.sync <=
      iclk_in_demarshaller_oprotocol.sync;
  iclk_time_downsampler_iprotocol.end_of_samples <=
      iclk_in_demarshaller_oprotocol.end_of_samples;

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
      SAMPLES;

  in_demarshaller : complex_short_with_metadata_demarshaller
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

  iclk_time_downsampler_ctrl.bypass                <= iclk_bypass;
  iclk_time_downsampler_ctrl.min_num_data_per_time <=
      unsigned(iclk_min_num_samples_per_timestamp);

  time_downsampler : misc_prims.misc_prims.time_downsampler
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
  iclk_time_corrector_ctrl.time_correction <= signed(iclk_time_correction);

  time_corrector : misc_prims.misc_prims.time_corrector
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
      ordy      => iclk_data_cdc_ifull_n);

  iclk_data_cdc_ienq <= (
    iclk_time_corrector_oprotocol.samples_vld    or
    iclk_time_corrector_oprotocol.time_vld       or
    iclk_time_corrector_oprotocol.interval_vld   or
    iclk_time_corrector_oprotocol.flush          or
    iclk_time_corrector_oprotocol.sync           or
    iclk_time_corrector_oprotocol.end_of_samples or
    iclk_time_corrector_oeof
    ) and iclk_data_cdc_ifull_n;

  data_cdc : entity work.fifo_complex_short_with_metadata
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

  oclk_eof <= oclk_data_cdc_oempty_n and oclk_data_cdc_oeof;

  out_marshaller : complex_short_with_metadata_marshaller
    generic map(
      WSI_DATA_WIDTH    => to_integer(OUT_PORT_DATA_WIDTH),
      WSI_MBYTEEN_WIDTH => out_out.byte_enable'length)
    port map(
      clk          => out_in.clk,
      rst          => out_in.reset,
      -- INPUT
      iprotocol    => oclk_data_cdc_oprotocol,
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
      ComplexShortWithMetadata_samples_op_e  when oclk_opcode = SAMPLES   else
      ComplexShortWithMetadata_time_op_e     when oclk_opcode = TIME_TIME else
      ComplexShortWithMetadata_interval_op_e when oclk_opcode = INTERVAL  else
      ComplexShortWithMetadata_flush_op_e    when oclk_opcode = FLUSH     else
      ComplexShortWithMetadata_sync_op_e     when oclk_opcode = SYNC      else
      ComplexShortWithMetadata_samples_op_e;

end rtl;
