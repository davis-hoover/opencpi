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
library ocpi; use ocpi.types.all; -- remove this to avoid all ocpi name collisions
library util, protocol;
architecture rtl of worker is
  signal in_opcode :
      protocol.iqstream.opcode_t :=
      protocol.iqstream.IQ;
  signal in_demarshaller_oprotocol :
      protocol.iqstream.protocol_t :=
      protocol.iqstream.PROTOCOL_ZERO;
  signal in_demarshaller_oeof : std_logic := '0';
  signal oprotocol : protocol.complex_short_with_metadata.protocol_t :=
                     protocol.complex_short_with_metadata.PROTOCOL_ZERO;
  signal out_marshaller_irdy  : std_logic := '0';
  signal out_marshaller_odata : std_logic_vector(out_out.data'range) :=
                                (others => '0');
  signal in_rst_detected  : std_logic := '0';
  signal out_rst_detected : std_logic := '0';
begin

  in_demarshaller : protocol.iqstream.iqstream_demarshaller
    generic map(
      WSI_DATA_WIDTH => in_in.data'length)
    port map(
      clk          => out_in.clk,
      rst          => out_in.reset,
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

  oprotocol.samples.iq.i <= in_demarshaller_oprotocol.iq.data.i;
  oprotocol.samples.iq.q <= in_demarshaller_oprotocol.iq.data.q;
  oprotocol.samples_vld  <= in_demarshaller_oprotocol.iq_vld;

  out_marshaller : protocol.complex_short_with_metadata.complex_short_with_metadata_marshaller
    generic map(
      WSI_DATA_WIDTH    => out_out.data'length,
      WSI_MBYTEEN_WIDTH => out_out.byte_enable'length)
    port map(
      -- CTRL
      clk          => out_in.clk,
      rst          => out_in.reset,
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
      clk                     => out_in.clk,
      rst                     => in_in.reset,
      clr                     => '0',
      rst_detected            => in_rst_detected,
      rst_then_unrst_detected => open);
  out_rst_detector : util.util.reset_detector
    port map(
      clk                     => out_in.clk,
      rst                     => out_in.reset,
      clr                     => '0',
      rst_detected            => out_rst_detected,
      rst_then_unrst_detected => open);
  ctl_out.done <= in_rst_detected and out_rst_detected;

end rtl;

