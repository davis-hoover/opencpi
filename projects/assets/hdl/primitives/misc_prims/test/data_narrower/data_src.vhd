library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all, ieee.math_real.all;
library ocpi;
library util;
library protocol;
library misc_prims; use misc_prims.misc_prims.all;

entity data_src is
  generic(
    OUTPUT_CONTINUOUS : boolean); --false will generate bubbles in output
  port(
    -- CTRL
    clk                : in  std_logic;
    rst                : in  std_logic;
    stop_on_period_cnt : in  std_logic;
    stopped            : out std_logic;
    -- OUTPUT
    oprotocol          : out protocol.complex_short_with_metadata.protocol_t;
    ometadata          : out metadata_dac_t;
    ometadata_vld      : out std_logic;
    ordy               : in  std_logic);
end entity data_src;
architecture rtl of data_src is  
  constant MAX_COUNT_VALUE   : positive := 32767;
  constant COUNTER_BIT_WIDTH : positive :=
      protocol.complex_short_with_metadata.OP_SAMPLES_ARG_IQ_I_BIT_WIDTH;
  signal dac_underrun_detector_iprotocol :
      protocol.complex_short_with_metadata.protocol_t :=
      protocol.complex_short_with_metadata.PROTOCOL_ZERO;
  signal cnt : unsigned(COUNTER_BIT_WIDTH-1 downto 0) :=
               (others => '0');
  signal counter_en                             : std_logic;
  signal cnt_stopped                            : std_logic;
  signal dac_underrun_detector_irdy      : std_logic;
  signal dac_underrun_detector_imetadata : metadata_dac_t;
begin

  counter : util.util.counter
    generic map(
      BIT_WIDTH => COUNTER_BIT_WIDTH)
    port map(
      clk => clk,
      rst => rst,
      en  => counter_en,
      cnt => cnt);

  cnt_stopped <= '1' when (cnt = MAX_COUNT_VALUE) else '0';
  
  stopped <= cnt_stopped;
  
  no_lfsr: if OUTPUT_CONTINUOUS generate
    counter_en <= dac_underrun_detector_irdy and not cnt_stopped;
  end generate;

  yes_lfsr: if not OUTPUT_CONTINUOUS generate
    signal lfsr_reg : std_logic_vector(11 downto 0) := (others => '0');    
  begin
    
    lfsr : misc_prims.misc_prims.lfsr
      generic map(
        POLYNOMIAL => "111000001000",
        SEED       => "000000000001")
      port map(
        clk => clk,
        rst => rst,
        en  => '1',
        reg => lfsr_reg);

    counter_en <= dac_underrun_detector_irdy and lfsr_reg(0) and not cnt_stopped;

  end generate;

  dac_underrun_detector_imetadata.underrun_error <= '0';
  dac_underrun_detector_imetadata.ctrl_tx_on_off <= not cnt_stopped;

  dac_underrun_detector_iprotocol.samples.iq.i <= std_logic_vector(cnt);
  dac_underrun_detector_iprotocol.samples.iq.q <= std_logic_vector(cnt);
  dac_underrun_detector_iprotocol.samples_vld  <= counter_en;
  
  dac_underrun_detector : misc_prims.misc_prims.dac_underrun_detector
    port map(
      -- CTRL
      clk           => clk,
      rst           => rst,
      status        => open,
      -- INPUT
      iprotocol     => dac_underrun_detector_iprotocol,
      imetadata     => dac_underrun_detector_imetadata,
      imetadata_vld => counter_en,
      irdy          => dac_underrun_detector_irdy,
      -- OUTPUT
      oprotocol     => oprotocol,
      ometadata     => ometadata,
      ometadata_vld => ometadata_vld,
      ordy          => ordy);

end rtl;
