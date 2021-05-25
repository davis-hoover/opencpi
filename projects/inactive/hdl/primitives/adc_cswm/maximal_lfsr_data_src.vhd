library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all, ieee.math_real.all;
library util, ocpi;
library adc_cswm; use adc_cswm.adc_cswm.all;

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
  -- https://en.wikipedia.org/wiki/Linear-feedback_shift_register#Some_polynomials_for_maximal_LFSRs
  constant MAXIMAL_LFSR_12_BIT_PERIOD : positive := 4095;
  constant MAXIMAL_LFSR_16_BIT_PERIOD : positive := 65535;
  constant CNT_BIT_WIDTH : integer := ocpi.util.width_for_max(MAXIMAL_LFSR_12_BIT_PERIOD);

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

  data_bit_width_12 : if(DATA_BIT_WIDTH = 12) generate

  counter : util.util.counter
    generic map(
      BIT_WIDTH => CNT_BIT_WIDTH)
    port map(
      clk => clk,
      rst => rst,
      en  => counter_en,
      cnt => cnt);

    maximal_period_samps_sent_gen : process(clk)
    begin
      if(rising_edge(clk)) then
        if(rst = '1') then
          maximal_period_samps_sent <= '0';
        elsif(ordy = '1') then
          if((cnt = MAXIMAL_LFSR_12_BIT_PERIOD) or
              (maximal_period_samps_sent = '1')) then
            maximal_period_samps_sent <= '1';
          else
            maximal_period_samps_sent <= '0';
          end if;
        end if;
      end if;
    end process maximal_period_samps_sent_gen;

    data_i_src : util.util.lfsr
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

  ovld <= counter_en and (not vld_rst);

end rtl;
