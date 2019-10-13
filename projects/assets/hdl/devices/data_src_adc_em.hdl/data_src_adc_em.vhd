library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi; use ocpi.types.all;
library misc_prims; use misc_prims.misc_prims.all; use misc_prims.ocpi.all;
library platform; use platform.platform_pkg.all;
architecture rtl of worker is

  signal adc_clk                  : std_logic := '0';
  signal adc_rst                  : std_logic := '0';
  signal adc_opcode               : complex_short_with_metadata_opcode_t :=
                                    SAMPLES;
  signal adc_in_adapter_odata     : data_complex_t;
  signal adc_in_adapter_ometadata : metadata_t;
  signal adc_in_adapter_ovld      : std_logic := '0';


begin
  ------------------------------------------------------------------------------
  -- emulate ADC clock
  ------------------------------------------------------------------------------

  adc_clk_gen : sim_clk
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
      USER      when in_in.opcode = ComplexShortWithMetadata_user_op_e     else
      SAMPLES;

  in_adapter : cswm_prot_in_adapter_dw32_clkout
    port map(
      -- INPUT
      iclk      => in_out.clk,
      idata     => in_in.data,
      ivalid    => in_in.valid,
      iready    => in_in.ready,
      isom      => in_in.som,
      ieom      => in_in.eom,
      iopcode   => adc_opcode,
      ieof      => in_in.eof,
      itake     => in_out.take,
      -- OUTPUT
      oclk      => adc_clk,
      orst      => adc_rst,
      odata     => adc_in_adapter_odata,
      ometadata => adc_in_adapter_ometadata,
      ovld      => adc_in_adapter_ovld,
      ordy      => '1');

  ------------------------------------------------------------------------------
  -- dev port
  ------------------------------------------------------------------------------

  dev_out.clk    <= adc_clk;
  dev_out.data_i <= adc_in_adapter_odata.i;
  dev_out.data_q <= adc_in_adapter_odata.q;
  dev_out.valid  <= adc_in_adapter_ovld and adc_in_adapter_ometadata.data_vld;
 
end rtl;
