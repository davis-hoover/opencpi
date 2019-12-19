library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all, ieee.math_real.all;
library misc_prims; use misc_prims.misc_prims.all;

-- I is maximal LFSR output, Q is bit-reversed I
entity maximal_lfsr_data_src is
  port(
    -- CTRL
    clk                : in  std_logic;
    rst                : in  std_logic;
    stop_on_period_cnt : in  std_logic;
    stopped            : out std_logic;
    -- OUTPUT
    odata              : out data_complex_t;
    ovld               : out std_logic;
    ordy               : in  std_logic);
end maximal_lfsr_data_src;
architecture rtl of maximal_lfsr_data_src is
  constant CNT_BIT_WIDTH : integer := integer(ceil(real(DATA_BIT_WIDTH)))+1;
  -- https://en.wikipedia.org/wiki/Linear-feedback_shift_register#Some_polynomials_for_maximal_LFSRs
  constant MAXIMAL_LFSR_16_BIT_PERIOD : positive := 65535;

  signal rst_r   : std_logic := '0';
  signal vld_rst : std_logic := '0';
  signal data_i  : std_logic_vector(odata.i'range) := (others => '0');

  signal cnt                       : unsigned(CNT_BIT_WIDTH-1 downto 0) :=
                                     (others => '0');
  signal counter_en                : std_logic := '0';
  signal stopped_s                 : std_logic := '0';
  signal maximal_period_samps_sent : std_logic := '0';
begin

  -- trying to obey axi4streaming TVALID rules
  rst_reg : process(clk)
  begin
    if(rising_edge(clk)) then
      rst_r <= rst;
    end if;
  end process;
  vld_rst <= rst or rst_r;

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

  maximal_period_samps_sent <= '1' when (cnt = MAXIMAL_LFSR_16_BIT_PERIOD) else '0';

  data_i_src : misc_prims.misc_prims.lfsr
    generic map(
      POLYNOMIAL => "1101000000001000",
      SEED       => "0000000000000001")
    port map(
      clk => clk,
      rst => vld_rst,
      en  => ordy,
      reg => data_i);

  odata.i <= data_i;

  data_q_src : for idx in 0 to DATA_BIT_WIDTH-1 generate
    odata.q(odata.q'length-1-idx) <= data_i(idx);
  end generate;

  ovld <= counter_en and (not vld_rst);

end rtl;
