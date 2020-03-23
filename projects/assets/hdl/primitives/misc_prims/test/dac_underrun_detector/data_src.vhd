library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all, ieee.math_real.all;
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
  signal protocol_s : protocol.complex_short_with_metadata.protocol_t :=
                      protocol.complex_short_with_metadata.PROTOCOL_ZERO;
  signal stopped_s  : std_logic := '0';
  signal ordy_s     : std_logic := '0';
begin

  data_into_dac : misc_prims.misc_prims.maximal_lfsr_data_src
    port map(
      -- CTRL
      clk                => clk,
      rst                => rst,
      stop_on_period_cnt => stop_on_period_cnt,
      stopped            => stopped_s,
      -- OUTPUT
      odata              => protocol_s.samples.iq,
      ovld               => protocol_s.samples_vld,
      ordy               => ordy_s);

  no_lfsr: if OUTPUT_CONTINUOUS generate
    ordy_s <= ordy;
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

    ordy_s <= ordy and lfsr_reg(0);

  end generate;

  stopped <= stopped_s;
  oprotocol <= protocol_s;
  ometadata.underrun_error <= '0';
  ometadata.ctrl_tx_on_off <= not stopped_s;
  ometadata_vld <= not stopped_s;

end rtl;
