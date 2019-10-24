library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all, ieee.math_real.all;
library misc_prims; use misc_prims.misc_prims.all;

-- I is maximal LFSR output, Q is bit-reversed I
entity adc_maximal_lfsr_data_src is
  generic(
    DATA_BIT_WIDTH : positive); -- width of each of I/Q
  port(
    -- CTRL
    clk                : in  std_logic;
    rst                : in  std_logic;
    stop_on_period_cnt : in  std_logic;
    stopped            : out std_logic;
    -- OUTPUT
    odata              : out data_complex_adc_t;
    ovld               : out std_logic;
    ordy               : in  std_logic);
end adc_maximal_lfsr_data_src;
architecture rtl of adc_maximal_lfsr_data_src is
  constant CNT_BIT_WIDTH : positive := DATA_BIT_WIDTH+1;
  -- https://en.wikipedia.org/wiki/Linear-feedback_shift_register#Some_polynomials_for_maximal_LFSRs
  constant MAXIMAL_LFSR_12_BIT_PERIOD : positive := 4095;
  constant MAXIMAL_LFSR_16_BIT_PERIOD : positive := 65535;


  signal data_i : std_logic_vector(odata.i'range) := (others => '0');

  signal cnt                       : unsigned(CNT_BIT_WIDTH-1 downto 0) :=
                                     (others => '0');
  signal counter_en                : std_logic := '0';
  signal stopped_s                 : std_logic := '0';
  signal maximal_period_samps_sent : std_logic := '0';
begin

  stopped_s <= (stop_on_period_cnt and maximal_period_samps_sent);
  counter_en <= ordy and not (stopped_s);
  stopped <= stopped_s;

  counter : misc_prims.misc_prims.counter
    generic map(
      BIT_WIDTH => CNT_BIT_WIDTH)
    port map(
      clk      => clk,
      rst      => rst,
      en       => counter_en,
      cnt      => cnt);

  data_bit_width_12 : if(DATA_BIT_WIDTH = 12) generate

    maximal_period_samps_sent <= '1' when (cnt = MAXIMAL_LFSR_12_BIT_PERIOD) else '0';

    data_i_src : misc_prims.misc_prims.lfsr
      generic map(
        POLYNOMIAL => "111000001000",
        SEED       => "000000000001")
      port map(
        clk => clk,
        rst => rst,
        en  => ordy,
        reg => data_i);

  end generate data_bit_width_12;

  odata.i <= data_i;

  data_q_src : for idx in 0 to DATA_BIT_WIDTH-1 generate
    odata.q(odata.q'length-1-idx) <= data_i(idx);
  end generate;

  ovld <= counter_en;

end rtl;
