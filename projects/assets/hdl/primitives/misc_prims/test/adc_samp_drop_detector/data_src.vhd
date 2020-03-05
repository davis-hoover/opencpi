library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all, ieee.math_real.all;
library misc_prims; use misc_prims.misc_prims.all;

entity data_src is
  port(
    -- CTRL
    clk                : in  std_logic;
    rst                : in  std_logic;
    stop_on_period_cnt : in  std_logic;
    stopped            : out std_logic;
    -- OUTPUT
    odata              : out data_complex_adc_t;
    ovld               : out std_logic);
end entity data_src;
architecture rtl of data_src is
begin

  adc_emulator : misc_prims.misc_prims.adc_maximal_lfsr_data_src
    port map(
      -- CTRL
      clk                => clk,
      rst                => rst,
      stop_on_period_cnt => stop_on_period_cnt,
      stopped            => stopped,
      -- OUTPUT
      odata              => odata,
      ovld               => ovld,
      ordy               => '1'); -- emulates forward pressure from ADC

end rtl;
