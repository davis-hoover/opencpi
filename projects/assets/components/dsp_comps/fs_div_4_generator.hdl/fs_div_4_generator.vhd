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
library protocol;
architecture structural of worker is
  signal ctl_in_resetn : std_logic := '0';
  signal generator_to_converter_tdata
      : std_logic_vector(out_out.data'length-1 downto 0) := (others => '0');
  signal generator_to_converter_tvalid : std_logic := '0';
  signal generator_to_converter_tready : std_logic := '0';
  signal converter_to_marshaller_protocol
    : protocol.iqstream.protocol_t := protocol.iqstream.PROTOCOL_ZERO;
  signal converter_to_marshaller_rdy : std_logic := '0';
  attribute mark_debug : string;
  attribute mark_debug of generator_to_converter_tdata : signal is "true";
  attribute mark_debug of generator_to_converter_tvalid : signal is "true";
  attribute mark_debug of generator_to_converter_tready : signal is "true";
  attribute mark_debug of converter_to_marshaller_protocol : signal is "true";
  attribute mark_debug of converter_to_marshaller_rdy : signal is "true";
begin

  ctl_in_resetn <= not ctl_in.reset;

  generator : dsp_prims.dsp_prims.fs_div_4_generator
    port map(
      aclk             => ctl_in.clk,
      aresetn          => ctl_in_resetn,
      freq_is_positive => std_logic(props_in.freq_is_positive),
      m_axis_tdata     => generator_to_converter_tdata,
      m_axis_tvalid    => generator_to_converter_tvalid,
      m_axis_tready    => generator_to_converter_tready);

  converter : protocol.iqstream.axis_to_iqstream_converter
    port map(
      s_axis_tdata  => generator_to_converter_tdata,
      s_axis_tvalid => generator_to_converter_tvalid,
      s_axis_tready => generator_to_converter_tready,
      oprotocol     => converter_to_marshaller_protocol,
      ordy          => converter_to_marshaller_rdy);

  marshaller : protocol.iqstream.iqstream_marshaller
    generic map(
      WSI_DATA_WIDTH    => out_out.data'length,
      WSI_MBYTEEN_WIDTH => out_out.byte_enable'length)
    port map(
      clk          => ctl_in.clk,
      rst          => ctl_in.reset,
      iprotocol    => converter_to_marshaller_protocol,
      ieof         => '0',
      irdy         => converter_to_marshaller_rdy,
      odata        => out_out.data,
      ovalid       => out_out.valid,
      obyte_enable => out_out.byte_enable,
      ogive        => out_out.give,
      osom         => out_out.som,
      oeom         => out_out.eom,
      oeof         => out_out.eof,
      oready       => out_in.ready);

end structural;
