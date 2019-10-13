library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library misc_prims; use misc_prims.misc_prims.all; use misc_prims.ocpi.all;
architecture rtl of worker is
  signal adc_opcode : complex_short_with_metadata_opcode_t := SAMPLES;
  signal adc_data   : std_logic_vector(
                      to_integer(unsigned(OUT_PORT_DATA_WIDTH))-1 downto 0) :=
                      (others => '0');
begin

  prim : data_src_adc
    generic map(
      OUT_PORT_DATA_WIDTH          => OUT_PORT_DATA_WIDTH,
      OUT_PORT_MBYTEEN_WIDTH       => out_out.byte_enable'length,
      ADC_WIDTH_BITS               => ADC_WIDTH_BITS,
      ADC_INPUT_IS_LSB_OF_OUT_PORT => ADC_INPUT_IS_LSB_OF_OUT_PORT)
    port map(
      -- CTRL
      ctrl_clk                      => ctl_in.clk,
      ctrl_reset                    => ctl_in.reset,
      ctrl_overrun_sticky_error     => props_out.overrun_sticky_error,
      ctrl_clr_overrun_sticky_error => props_in.clr_overrun_sticky_error,
      -- DEV SIGNAL INPUT
      adc_dev_clk                   => dev_in.clk,
      adc_dev_data_i                => dev_in.data_i,
      adc_dev_data_q                => dev_in.data_q,
      adc_dev_valid                 => dev_in.valid,
      adc_dev_present               => dev_out.present,
      -- OUTPUT
      adc_out_clk                   => out_out.clk,
      adc_out_data                  => adc_data,
      adc_out_valid                 => out_out.valid,
      adc_out_byte_enable           => out_out.byte_enable,
      adc_out_give                  => out_out.give,
      adc_out_som                   => out_out.som,
      adc_out_eom                   => out_out.eom,
      adc_out_opcode                => adc_opcode,
      adc_out_eof                   => out_out.eof,
      adc_out_ready                 => out_in.ready);

  -- this only needed to avoid build bug for xsim:
  -- ERROR: [XSIM 43-3316] Signal SIGSEGV received.
  out_out.data <= adc_data;

  out_out.opcode <=
      ComplexShortWithMetadata_samples_op_e  when adc_opcode = SAMPLES   else
      ComplexShortWithMetadata_time_op_e     when adc_opcode = TIME_TIME else
      ComplexShortWithMetadata_interval_op_e when adc_opcode = INTERVAL  else
      ComplexShortWithMetadata_flush_op_e    when adc_opcode = FLUSH     else
      ComplexShortWithMetadata_sync_op_e     when adc_opcode = SYNC      else
      ComplexShortWithMetadata_user_op_e     when adc_opcode = USER      else
      ComplexShortWithMetadata_samples_op_e;

end rtl;
