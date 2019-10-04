library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi; use ocpi.types.all; -- remove this to avoid all ocpi name collisions
library misc_prims; use misc_prims.misc_prims.all;
library misc_prims; use misc_prims.ocpi.all;
architecture rtl of worker is
  signal dac_in_opcode                          : complex_short_with_metadata_opcode_t := SAMPLES;
  signal on_off_out_opcode                      : bool_t;
  signal ctrl_clr_underrun_sticky_error         : bool_t;
  signal ctrl_clr_unused_opcode_detected_sticky : bool_t;
begin
  ctrl_clr_underrun_sticky_error <= props_in.clr_underrun_sticky_error_written and
                                    props_in.clr_underrun_sticky_error;
  ctrl_clr_unused_opcode_detected_sticky <= props_in.clr_unused_opcode_detected_sticky_written and
                                            props_in.clr_unused_opcode_detected_sticky;
  
  prim : misc_prims.ocpi.ocpi_data_sink_dac
    generic map(
      DAC_WIDTH_BITS                         => DAC_WIDTH_BITS,
      DATA_PIPE_LATENCY_CYCLES               => DATA_PIPE_LATENCY_CYCLES,
      IN_PORT_DATA_WIDTH                     => IN_PORT_DATA_WIDTH,
      DAC_OUTPUT_IS_LSB_OF_IN_PORT           => DAC_OUTPUT_IS_LSB_OF_IN_PORT,
      IN_PORT_MBYTEEN_WIDTH                  => in_in.byte_enable'length)
    port map(
      -- CTRL
      ctrl_clk                               => ctl_in.clk,
      ctrl_rst                               => ctl_in.reset,
      ctrl_underrun_sticky_error             => props_out.underrun_sticky_error,
      ctrl_clr_underrun_sticky_error         => ctrl_clr_underrun_sticky_error,
      ctrl_unused_opcode_detected_sticky     => props_out.unused_opcode_detected_sticky,
      ctrl_clr_unused_opcode_detected_sticky => ctrl_clr_unused_opcode_detected_sticky,
      ctrl_finished                          => ctl_out.finished,
      -- INPUT
      dac_in_clk                             => in_out.clk,
      dac_in_take                            => in_out.take,
      dac_in_data                            => in_in.data,
      dac_in_opcode                          => dac_in_opcode,
      dac_in_ready                           => in_in.ready,
      dac_in_valid                           => in_in.valid,
      dac_in_eof                             => in_in.eof,
      -- ON/OFF OUTPUT
      on_off_out_reset                       => on_off_in.reset,
      on_off_out_ready                       => on_off_in.ready,
      on_off_out_opcode                      => on_off_out_opcode,
      on_off_out_give                        => on_off_out.give,
      -- DEV SIGNAL OUTPUT
      dac_dev_clk                            => dev_in.clk,
      dac_dev_data_i                         => dev_out.data_i,
      dac_dev_data_q                         => dev_out.data_q,
      dac_dev_valid                          => dev_out.valid,
      dac_dev_take                           => dev_in.take);

  opcode_gen : process(in_in.opcode)
  begin
    case in_in.opcode is
      when ComplexShortWithMetadata_time_op_e =>
        dac_in_opcode <= TIME;
      when ComplexShortWithMetadata_interval_op_e =>
        dac_in_opcode <= INTERVAL;
      when ComplexShortWithMetadata_flush_op_e =>
        dac_in_opcode <= FLUSH;
      when ComplexShortWithMetadata_sync_op_e =>
        dac_in_opcode <= SYNC;
      when ComplexShortWithMetadata_end_of_samples_op_e =>
        dac_in_opcode <= END_OF_SAMPLES;
      when ComplexShortWithMetadata_user_op_e =>
        dac_in_opcode <= USER;
      when others =>
        dac_in_opcode <= SAMPLES;
    end case;
  end process opcode_gen;
  
end rtl;
