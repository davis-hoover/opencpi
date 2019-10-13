library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;
library misc_prims; use misc_prims.misc_prims.all; use misc_prims.ocpi.all;
library ocpi; use ocpi.types.all;
library cdc; use cdc.cdc.all;

entity data_src_adc is
  generic(
    OUT_PORT_DATA_WIDTH          : ulong_t;
    OUT_PORT_MBYTEEN_WIDTH       : natural;
    ADC_WIDTH_BITS               : ushort_t;
    ADC_INPUT_IS_LSB_OF_OUT_PORT : Bool_t);
  port(
    -- CTRL
    ctrl_clk                      : in std_logic;
    ctrl_reset                    : in std_logic;
    ctrl_overrun_sticky_error     : out Bool_t;
    ctrl_clr_overrun_sticky_error : in  Bool_t;
    -- DEV SIGNAL INPUT
    adc_dev_clk                   : in  std_logic;
    adc_dev_data_i                : in  std_logic_vector(15 downto 0);
    adc_dev_data_q                : in  std_logic_vector(15 downto 0);
    adc_dev_valid                 : in  std_logic;
    adc_dev_present               : out std_logic;
    -- OUTPUT
    adc_out_clk                   : out std_logic;
    adc_out_data                  : out std_logic_vector(
                                    to_integer(unsigned(OUT_PORT_DATA_WIDTH))-1
                                    downto 0);
    adc_out_valid                 : out Bool_t;
    adc_out_byte_enable           : out std_logic_vector(
                                    OUT_PORT_MBYTEEN_WIDTH-1 downto 0);
    adc_out_give                  : out Bool_t;
    adc_out_som                   : out Bool_t;
    adc_out_eom                   : out Bool_t;
    adc_out_opcode                : out complex_short_with_metadata_opcode_t;
    adc_out_eof                   : out Bool_t;
    adc_out_ready                 : in  Bool_t);
end entity data_src_adc;
architecture rtl of data_src_adc is

  constant BITS_PACKED_INTO_MSBS : boolean := not
      to_boolean(ADC_INPUT_IS_LSB_OF_OUT_PORT);

  signal adc_status : adc_samp_drop_detector_status_t;

  signal adc_rst   : std_logic := '0';
  signal adc_idata : data_complex_adc_t;

  signal adc_overrun_generator_odata     : data_complex_adc_t;
  signal adc_overrun_generator_ometadata : metadata_t;
  signal adc_overrun_generator_ovld      : std_logic := '0';

  signal adc_data_widener_irdy      : std_logic := '0';
  signal adc_data_widener_odata     : data_complex_t;
  signal adc_data_widener_ometadata : metadata_t;
  signal adc_data_widener_ovld      : std_logic := '0';

  signal adc_out_adapter_irdy  : std_logic := '0';

begin
  ------------------------------------------------------------------------------
  -- CTRL <- DATA CDC
  ------------------------------------------------------------------------------

  -- ADCs usally won't provide a reset along w/ their clock
  adc_rst_gen : cdc.cdc.reset
    port map(
      src_rst => ctrl_reset,
      dst_clk => adc_dev_clk,
      dst_rst => adc_rst);

  ctrl_out_cdc : fast_pulse_to_slow_sticky
    port map(
      -- fast clock domain
      fast_clk    => adc_dev_clk,
      fast_rst    => adc_rst,
      fast_pulse  => adc_status.error_samp_drop,
      -- slow clock domain
      slow_clk    => ctrl_clk,
      slow_rst    => ctrl_reset,
      slow_clr    => ctrl_clr_overrun_sticky_error,
      slow_sticky => ctrl_overrun_sticky_error);

  ------------------------------------------------------------------------------
  -- out port
  ------------------------------------------------------------------------------

  adc_idata.i <= adc_dev_data_i(to_integer(unsigned(ADC_WIDTH_BITS))-1 downto
                 0);
  adc_idata.q <= adc_dev_data_q(to_integer(unsigned(ADC_WIDTH_BITS))-1 downto
                 0);

  out_port_data_width_32 : if(OUT_PORT_DATA_WIDTH = 32) generate

    overrun_generator :
        misc_prims.misc_prims.adc_samp_drop_detector
      generic map(
        DATA_PIPE_LATENCY_CYCLES => 0)
      port map(
        -- CTRL INTERFACE
        clk       => adc_dev_clk,
        rst       => adc_rst,
        status    => adc_status,
        -- INPUT INTERFACE
        idata     => adc_idata,
        ivld      => adc_dev_valid,
        -- OUTPUT INTERFACE
        odata     => adc_overrun_generator_odata,
        ometadata => adc_overrun_generator_ometadata,
        ovld      => adc_overrun_generator_ovld,
        ordy      => adc_data_widener_irdy);

    data_widener : misc_prims.misc_prims.data_widener
      generic map(
        DATA_PIPE_LATENCY_CYCLES => 0,
        BITS_PACKED_INTO_MSBS    => BITS_PACKED_INTO_MSBS)
      port map(
        -- CTRL INTERFACE
        clk       => adc_dev_clk,
        rst       => adc_rst,
        -- INPUT INTERFACE
        idata     => adc_overrun_generator_odata,
        imetadata => adc_overrun_generator_ometadata,
        ivld      => adc_overrun_generator_ovld,
        irdy      => adc_data_widener_irdy,
        -- OUTPUT INTERFACE
        odata     => adc_data_widener_odata,
        ometadata => adc_data_widener_ometadata,
        ovld      => adc_data_widener_ovld,
        ordy      => adc_out_adapter_irdy);

    out_adapter : misc_prims.ocpi.cswm_prot_out_adapter_dw32_clkout
      generic map(
        OUT_PORT_MBYTEEN_WIDTH => OUT_PORT_MBYTEEN_WIDTH)
      port map(
        -- INPUT
        iclk         => adc_dev_clk,
        irst         => adc_rst,
        idata        => adc_data_widener_odata,
        imetadata    => adc_data_widener_ometadata,
        ivld         => adc_data_widener_ovld,
        irdy         => adc_out_adapter_irdy,
        -- OUTPUT
        oclk         => adc_out_clk,
        odata        => adc_out_data,
        ovalid       => adc_out_valid,
        obyte_enable => adc_out_byte_enable,
        ogive        => adc_out_give,
        osom         => adc_out_som,
        oeom         => adc_out_eom,
        oopcode      => adc_out_opcode,
        oeof         => adc_out_eof,
        oready       => adc_out_ready);

  end generate;

  ------------------------------------------------------------------------------
  -- dev port
  ------------------------------------------------------------------------------

  -- subdevices may support multiple instances of this worker, and some may need
  -- to know how many instances of this worker are present
  adc_dev_present<= '1';
end rtl;
