library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all, ieee.math_real.all;
library util;
library protocol;
library misc_prims; use misc_prims.misc_prims.all;

entity data_src is
  --generic(
    --INCLUDE_ERROR_SAMP_DROP : boolean);
  port(
    -- CTRL
    clk       : in  std_logic;
    rst       : in  std_logic;
    -- OUTPUT
    oprotocol : out protocol.complex_short_with_metadata.protocol_t;
    ordy      : in  std_logic);
end entity data_src;
architecture rtl of data_src is
  signal rst_r                       : std_logic := '0';
  signal vld_rst                     : std_logic := '0';
  signal maximal_lfsr_data_src_ovld  : std_logic := '0';
  signal maximal_lfsr_data_src_odata :
        protocol.complex_short_with_metadata.op_samples_arg_iq_t := 
        protocol.complex_short_with_metadata.OP_SAMPLES_ARG_IQ_ZERO;

  signal time_time : unsigned(
                     protocol.complex_short_with_metadata.OP_TIME_BIT_WIDTH-1
                     downto 0) := (others => '0');
  signal protocol_s : protocol.complex_short_with_metadata.protocol_t :=
                      protocol.complex_short_with_metadata.PROTOCOL_ZERO;
begin

  -- trying to obey axi4streaming TVALID rules
  rst_reg : process(clk)
  begin
    if(rising_edge(clk)) then
      rst_r <= rst;
    end if;
  end process;
  vld_rst <= rst or rst_r;

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

  time_gen : util.util.counter
    generic map(
      BIT_WIDTH => protocol.complex_short_with_metadata.OP_TIME_BIT_WIDTH)
    port map(
      clk => clk,
      rst => rst,
      en  => '1',
      cnt => time_time);

  protocol_s.samples.iq     <= maximal_lfsr_data_src_odata;
  protocol_s.samples_vld    <= maximal_lfsr_data_src_ovld and (not vld_rst);
  protocol_s.time.sec       <= 
      std_logic_vector(time_time(time_time'left downto time_time'left -
      protocol.complex_short_with_metadata.OP_TIME_ARG_SEC_BIT_WIDTH+1));
  protocol_s.time.fract_sec <=
      std_logic_vector(time_time(
      protocol.complex_short_with_metadata.OP_TIME_ARG_FRACT_SEC_BIT_WIDTH-1
      downto 0));
  protocol_s.time_vld       <= ordy and (not vld_rst);
  protocol_s.sync           <= maximal_lfsr_data_src_odata.i(0);

  oprotocol <= protocol_s;

end rtl;
