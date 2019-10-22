library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all, ieee.math_real.all;
library misc_prims; use misc_prims.misc_prims.all;

entity data_src is
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
    ometadata          : out metadata_t;
    ovld               : out std_logic;
    ordy               : in  std_logic);
end entity data_src;
architecture rtl of data_src is
  signal adc_emulator_odata : data_complex_adc_t;
  signal adc_emulator_ovld  : std_logic := '0';
begin

  adc_emulator : misc_prims.misc_prims.adc_maximal_lfsr_data_src
    generic map(
      DATA_BIT_WIDTH => DATA_BIT_WIDTH)
    port map(
      -- CTRL
      clk                => clk,
      rst                => rst,
      stop_on_period_cnt => stop_on_period_cnt,
      stopped            => stopped,
      -- OUTPUT
      odata              => adc_emulator_odata,
      ovld               => adc_emulator_ovld,
      ordy               => '1'); -- emulates forward pressure from ADC

  adc_samp_drop_detector : misc_prims.misc_prims.adc_samp_drop_detector
    port map(
      -- CTRL
      clk       => clk,
      rst       => rst,
      status    => open,
      -- INPUT
      idata     => adc_emulator_odata,
      ivld      => adc_emulator_ovld,
      -- OUTPUT
      odata     => odata,
      ometadata => ometadata,
      ovld      => ovld,
      ordy      => ordy);

end rtl;
