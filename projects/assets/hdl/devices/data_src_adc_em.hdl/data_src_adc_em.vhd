library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi; use ocpi.types.all;
library misc_prims; library platform; library util;
library protocol; use protocol.complex_short_with_metadata.all;
architecture rtl of worker is
  signal adc_clk    : std_logic := '0';
  signal adc_rst    : std_logic := '0';
  signal adc_opcode : opcode_t := SAMPLES;
  signal adc_in_demarshaller_oprotocol : protocol_t := PROTOCOL_ZERO;
begin
  ------------------------------------------------------------------------------
  -- emulate ADC clock
  ------------------------------------------------------------------------------

  adc_clk_gen : platform.platform_pkg.sim_clk
    generic map(
      frequency => 30720000.0)
    port map(
      clk   => adc_clk,
      reset => adc_rst);

  ------------------------------------------------------------------------------
  -- in port
  ------------------------------------------------------------------------------

  adc_opcode <=
    SAMPLES   when in_in.opcode = ComplexShortWithMetadata_samples_op_e  else
    TIME_TIME when in_in.opcode = ComplexShortWithMetadata_time_op_e     else
    INTERVAL  when in_in.opcode = ComplexShortWithMetadata_interval_op_e else
    FLUSH     when in_in.opcode = ComplexShortWithMetadata_flush_op_e    else
    SYNC      when in_in.opcode = ComplexShortWithMetadata_sync_op_e     else
    SAMPLES;

  in_demarshaller : complex_short_with_metadata_demarshaller
    generic map(
      WSI_DATA_WIDTH => 32)
    port map(
      clk       => adc_clk,
      rst       => adc_rst,
      -- INPUT
      idata     => in_in.data,
      ivalid    => in_in.valid,
      iready    => in_in.ready,
      isom      => in_in.som,
      ieom      => in_in.eom,
      iopcode   => adc_opcode,
      ieof      => in_in.eof,
      itake     => in_out.take,
      -- OUTPUT
      oprotocol => adc_in_demarshaller_oprotocol,
      ordy      => '1');

  in_clk_gen : util.util.in2out
    port map(
      in_port  => adc_clk,
      out_port => in_out.clk);

  ------------------------------------------------------------------------------
  -- dev port
  ------------------------------------------------------------------------------

  dev_out_clk_gen : util.util.in2out
    port map(
      in_port  => adc_clk,
      out_port => dev_out.clk);

  dev_out.data_i <= adc_in_demarshaller_oprotocol.samples.iq.i;
  dev_out.data_q <= adc_in_demarshaller_oprotocol.samples.iq.q;
  dev_out.valid  <= adc_in_demarshaller_oprotocol.samples_vld;
 
end rtl;
