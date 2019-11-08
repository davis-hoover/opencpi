library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all, ieee.math_real.all;
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
    odata              : out data_complex_t;
    ovld               : out std_logic;
    ordy               : in  std_logic);
end entity data_src;
architecture rtl of data_src is
  signal s_ordy : std_logic;
begin

  data_into_dac : misc_prims.misc_prims.maximal_lfsr_data_src
    port map(
      -- CTRL
      clk                => clk,
      rst                => rst,
      stop_on_period_cnt => stop_on_period_cnt,
      stopped            => stopped,
      -- OUTPUT
      odata              => odata,
      ovld               => ovld,
      ordy               => s_ordy);

  no_lfsr: if OUTPUT_CONTINUOUS generate
    s_ordy <= ordy;
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

    s_ordy <= ordy and lfsr_reg(0);

  end generate;

end rtl;
