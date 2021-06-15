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
library ocpi; use ocpi.types.all;
library util, protocol, timed_sample_prot;
architecture rtl of worker is
  signal in_opcode :
      timed_sample_prot.complex_short_timed_sample.opcode_t :=
      timed_sample_prot.complex_short_timed_sample.SAMPLE;
  signal in_demarshaller_oprotocol :
      timed_sample_prot.complex_short_timed_sample.protocol_t :=
      timed_sample_prot.complex_short_timed_sample.PROTOCOL_ZERO;
  signal in_demarshaller_oeof : std_logic := '0';
  signal oprotocol : protocol.iqstream.protocol_t :=
                     protocol.iqstream.PROTOCOL_ZERO;
  signal out_marshaller_irdy  : std_logic := '0';
  signal out_marshaller_odata : std_logic_vector(out_out.data'range) :=
                                (others => '0');
  signal in_rst_detected  : std_logic := '0';
  signal out_rst_detected : std_logic := '0';
begin

  in_opcode <=
    timed_sample_prot.complex_short_timed_sample.SAMPLE        when
    in_in.opcode = complex_short_timed_sample_sample_op_e        else
    timed_sample_prot.complex_short_timed_sample.TIME_TIME      when
    in_in.opcode = complex_short_timed_sample_time_op_e           else
    timed_sample_prot.complex_short_timed_sample.SAMPLE_INTERVAL       when
    in_in.opcode = complex_short_timed_sample_sample_interval_op_e       else
    timed_sample_prot.complex_short_timed_sample.FLUSH          when
    in_in.opcode = complex_short_timed_sample_flush_op_e          else
    timed_sample_prot.complex_short_timed_sample.DISCONTINUITY           when
    in_in.opcode = complex_short_timed_sample_discontinuity_op_e           else
    timed_sample_prot.complex_short_timed_sample.METADATA when
    in_in.opcode = complex_short_timed_sample_metadata_op_e else
    timed_sample_prot.complex_short_timed_sample.SAMPLE;

  in_demarshaller : timed_sample_prot.complex_short_timed_sample.complex_short_timed_sample_demarshaller
    generic map(
      WSI_DATA_WIDTH => in_in.data'length)
    port map(
      clk          => in_in.clk,
      rst          => in_in.reset,
      -- INPUT
      idata        => in_in.data,
      ivalid       => in_in.valid,
      iready       => in_in.ready,
      isom         => in_in.som,
      ieom         => in_in.eom,
      iopcode      => in_opcode,
      ieof         => in_in.eof,
      itake        => in_out.take,
      -- OUTPUT
      oprotocol    => in_demarshaller_oprotocol,
      oeof         => in_demarshaller_oeof,
      ordy         => out_marshaller_irdy);

  oprotocol.iq.data.i <= in_demarshaller_oprotocol.sample.data.real;
  oprotocol.iq.data.q <= in_demarshaller_oprotocol.sample.data.imaginary;
  oprotocol.iq_vld    <= in_demarshaller_oprotocol.sample_vld;

  out_marshaller : protocol.iqstream.iqstream_marshaller
    generic map(
      WSI_DATA_WIDTH    => out_out.data'length,
      WSI_MBYTEEN_WIDTH => out_out.byte_enable'length)
    port map(
      -- CTRL
      clk          => in_in.clk,
      rst          => in_in.reset,
      -- INPUT
      iprotocol    => oprotocol,
      ieof         => in_demarshaller_oeof,
      irdy         => out_marshaller_irdy,
      -- OUTPUT
      odata        => out_marshaller_odata,
      ovalid       => out_out.valid,
      obyte_enable => out_out.byte_enable,
      ogive        => out_out.give,
      osom         => out_out.som,
      oeom         => out_out.eom,
      oeof         => out_out.eof,
      oready       => out_in.ready);

  -- this only needed to avoid build bug for xsim:
  -- ERROR: [XSIM 43-3316] Signal SIGSEGV received.
  out_out.data <= out_marshaller_odata;

  -- this worker is not initialized until out_in.clk is ticking and both the in
  -- and out ports have successfully come into reset
  in_rst_detector : util.util.reset_detector
    port map(
      clk                     => in_in.clk,
      rst                     => in_in.reset,
      clr                     => '0',
      rst_detected            => in_rst_detected,
      rst_then_unrst_detected => open);
  out_rst_detector : util.util.reset_detector
    port map(
      clk                     => in_in.clk,
      rst                     => out_in.reset,
      clr                     => '0',
      rst_detected            => out_rst_detected,
      rst_then_unrst_detected => open);
  ctl_out.done <= in_rst_detected and out_rst_detected;

end rtl;
