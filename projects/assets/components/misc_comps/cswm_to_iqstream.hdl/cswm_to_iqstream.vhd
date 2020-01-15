library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi; use ocpi.types.all;
library misc_prims;
architecture rtl of worker is
  signal opcode : misc_prims.ocpi.complex_short_with_metadata_opcode_t :=
                  misc_prims.ocpi.SAMPLES;
  signal in_adapter_odata     : misc_prims.misc_prims.data_complex_t :=
                                misc_prims.misc_prims.data_complex_zero;
  signal in_adapter_ometadata : misc_prims.misc_prims.metadata_t :=
                                misc_prims.misc_prims.metadata_zero;
  signal in_adapter_ovld      : std_logic := '0';
  signal out_adapter_irdy     : std_logic := '0';
  signal out_adapter_odata    : std_logic_vector(out_out.data'range) :=
                                (others => '0');
  signal data_vld             : std_logic := '0';
begin

  opcode <=
    misc_prims.ocpi.SAMPLES         when
    in_in.opcode = ComplexShortWithMetadata_samples_op_e        else
    misc_prims.ocpi.TIME_TIME       when
    in_in.opcode = ComplexShortWithMetadata_time_op_e           else
    misc_prims.ocpi.INTERVAL        when
    in_in.opcode = ComplexShortWithMetadata_interval_op_e       else
    misc_prims.ocpi.FLUSH           when
    in_in.opcode = ComplexShortWithMetadata_flush_op_e          else
    misc_prims.ocpi.SYNC            when
    in_in.opcode = ComplexShortWithMetadata_sync_op_e           else
    misc_prims.ocpi.END_OF_SAMPLES when
    in_in.opcode = ComplexShortWithMetadata_end_of_samples_op_e else
    misc_prims.ocpi.SAMPLES;

  in_adapter : misc_prims.ocpi.cswm_prot_in_adapter_dw32_clkin
    port map(
      -- INPUT
      iclk         => in_in.clk,
      irst         => in_in.reset,
      idata        => in_in.data,
      ivalid       => in_in.valid,
      iready       => in_in.ready,
      isom         => in_in.som,
      ieom         => in_in.eom,
      iopcode      => opcode,
      ieof         => in_in.eof,
      itake        => in_out.take,
      -- OUTPUT
      odata        => in_adapter_odata,
      ometadata    => in_adapter_ometadata,
      ovld         => in_adapter_ovld,
      ordy         => out_adapter_irdy);

  data_vld <= in_adapter_ovld and in_adapter_ometadata.data_vld;

  out_adapter : misc_prims.wsi_helpers.iqstream_prot_out_adapter
    generic map(
      WSI_DATA_WIDTH    => out_out.data'length,
      WSI_MBYTEEN_WIDTH => out_out.byte_enable'length)
    port map(
      -- CTRL
      clk          => in_in.clk,
      rst          => in_in.reset,
      -- INPUT
      idata        => in_adapter_odata,
      ivld         => data_vld,
      irdy         => out_adapter_irdy,
      -- OUTPUT
      odata        => out_adapter_odata,
      ovalid       => out_out.valid,
      obyte_enable => out_out.byte_enable,
      ogive        => out_out.give,
      osom         => out_out.som,
      oeom         => out_out.eom,
      oeof         => out_out.eof,
      oready       => out_in.ready);

  -- this only needed to avoid build bug for xsim:
  -- ERROR: [XSIM 43-3316] Signal SIGSEGV received.
  out_out.data <= out_adapter_odata;

end rtl;
