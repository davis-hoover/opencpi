library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all, ieee.math_real.all;
library protocol;
library misc_prims; use misc_prims.misc_prims.all;

entity data_src is
  generic(
    --INCLUDE_ERROR_SAMP_DROP : boolean;
    TIME_TIME      : unsigned(
                     protocol.complex_short_with_metadata.OP_TIME_BIT_WIDTH-1
                     downto 0);
    TIME_TIME_VLD  : std_logic := '1');
  port(
    -- CTRL
    clk       : in  std_logic;
    rst       : in  std_logic;
    -- OUTPUT
    oprotocol : out protocol.complex_short_with_metadata.protocol_t;
    ordy      : in  std_logic);
end entity data_src;
architecture rtl of data_src is
  signal maximal_lfsr_data_src_odata :
        protocol.complex_short_with_metadata.op_samples_arg_iq_t := 
        protocol.complex_short_with_metadata.OP_SAMPLES_ARG_IQ_ZERO;
  signal maximal_lfsr_data_src_ovld  : std_logic := '0';

  signal protocol_s : protocol.complex_short_with_metadata.protocol_t :=
                      protocol.complex_short_with_metadata.PROTOCOL_ZERO;
begin

  maximal_lfsr_data_src : misc_prims.misc_prims.maximal_lfsr_data_src
    port map(
      -- CTRL
      clk                => clk,
      rst                => rst,
      stop_on_period_cnt => '0',
      stopped            => open,
      -- OUTPUT
      odata              => maximal_lfsr_data_src_odata,
      ovld               => maximal_lfsr_data_src_ovld,
      ordy               => ordy);

  protocol_s.samples.iq     <= maximal_lfsr_data_src_odata;
  protocol_s.samples_vld    <= maximal_lfsr_data_src_ovld;
  protocol_s.time.sec       <= 
      std_logic_vector(TIME_TIME(time_time'left downto time_time'left -
      protocol.complex_short_with_metadata.OP_TIME_ARG_SEC_BIT_WIDTH+1));
  protocol_s.time.fract_sec <=
      std_logic_vector(TIME_TIME(
      protocol.complex_short_with_metadata.OP_TIME_ARG_FRACT_SEC_BIT_WIDTH-1
      downto 0));
  protocol_s.time_vld       <= TIME_TIME_VLD;

  oprotocol <= protocol_s;
end rtl;
