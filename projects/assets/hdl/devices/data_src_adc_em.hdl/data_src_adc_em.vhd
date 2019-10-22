library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi; use ocpi.types.all;
library misc_prims;
library platform;
architecture rtl of worker is

  signal adc_clk    : std_logic := '0';
  signal adc_rst    : std_logic := '0';
  signal adc_opcode : misc_prims.ocpi.complex_short_with_metadata_opcode_t :=
                      misc_prims.ocpi.SAMPLES;
  signal adc_in_adapter_odata     : misc_prims.misc_prims.data_complex_t;
  signal adc_in_adapter_ometadata : misc_prims.misc_prims.metadata_t;
  signal adc_in_adapter_ovld      : std_logic := '0';


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

  adc_opcode <= misc_prims.ocpi.SAMPLES
                when in_in.opcode = ComplexShortWithMetadata_samples_op_e  else
                misc_prims.ocpi.TIME_TIME
                when in_in.opcode = ComplexShortWithMetadata_time_op_e else
                misc_prims.ocpi.INTERVAL
                when in_in.opcode = ComplexShortWithMetadata_interval_op_e else
                misc_prims.ocpi.FLUSH
                when in_in.opcode = ComplexShortWithMetadata_flush_op_e else
                misc_prims.ocpi.SYNC
                when in_in.opcode = ComplexShortWithMetadata_sync_op_e else
                misc_prims.ocpi.USER
                when in_in.opcode = ComplexShortWithMetadata_user_op_e else
                misc_prims.ocpi.SAMPLES;

  in_adapter : misc_prims.ocpi.cswm_prot_in_adapter_dw32_clkout
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
