library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi; use ocpi.types.all;
library protocol;
library misc_prims;
architecture rtl of worker is
  signal in_opcode :
      protocol.complex_short_with_metadata.opcode_t :=
      protocol.complex_short_with_metadata.SAMPLES;
  signal in_demarshaller_oprotocol :
      protocol.complex_short_with_metadata.protocol_t :=
      protocol.complex_short_with_metadata.PROTOCOL_ZERO;
  signal oprotocol : protocol.iqstream.protocol_t :=
                     protocol.iqstream.PROTOCOL_ZERO;
  signal out_marshaller_irdy  : std_logic := '0';
  signal out_marshaller_odata : std_logic_vector(out_out.data'range) :=
                                (others => '0');
begin

  in_opcode <=
    protocol.complex_short_with_metadata.SAMPLES        when
    in_in.opcode = ComplexShortWithMetadata_samples_op_e        else
    protocol.complex_short_with_metadata.TIME_TIME      when
    in_in.opcode = ComplexShortWithMetadata_time_op_e           else
    protocol.complex_short_with_metadata.INTERVAL       when
    in_in.opcode = ComplexShortWithMetadata_interval_op_e       else
    protocol.complex_short_with_metadata.FLUSH          when
    in_in.opcode = ComplexShortWithMetadata_flush_op_e          else
    protocol.complex_short_with_metadata.SYNC           when
    in_in.opcode = ComplexShortWithMetadata_sync_op_e           else
    protocol.complex_short_with_metadata.END_OF_SAMPLES when
    in_in.opcode = ComplexShortWithMetadata_end_of_samples_op_e else
    protocol.complex_short_with_metadata.SAMPLES;

  in_demarshaller : protocol.complex_short_with_metadata.complex_short_with_metadata_demarshaller
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
      ordy         => out_marshaller_irdy);

  oprotocol.iq.data.i <= in_demarshaller_oprotocol.samples.iq.i;
  oprotocol.iq.data.q <= in_demarshaller_oprotocol.samples.iq.q;
  oprotocol.iq_vld    <= in_demarshaller_oprotocol.samples_vld;

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

end rtl;
