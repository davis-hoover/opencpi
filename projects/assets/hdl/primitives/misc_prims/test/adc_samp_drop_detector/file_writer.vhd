library ieee;
use ieee.std_logic_1164.all, ieee.numeric_std.all, ieee.math_real.all;
use std.textio.all; use ieee.std_logic_textio.all;
library misc_prims; use misc_prims.misc_prims.all;
library util;

entity file_writer is
  generic(
    FILENAME          : string;
    LFSR_BP_EN_PERIOD : positive := 1);
  port(
    -- CTRL
    clk                     : in  std_logic;
    rst                     : in  std_logic;
    backpressure_select     : in  file_writer_backpressure_select_t;
    backpressure_select_vld : in  std_logic;
    -- INPUT
    idata                   : in  data_complex_adc_t;
    isamp_drop              : in  std_logic;
    ivld                    : in  std_logic;
    irdy                    : out std_logic);
end entity file_writer;
architecture rtl of file_writer is
  signal lfsr_reg                           : std_logic_vector(11 downto 0) :=
                                              (others => '0');

  signal counter_rst : std_logic := '0';
  signal counter_cnt : unsigned(15 downto 0) := (others => '0');
begin

  counter_rst <= '1' when (rst = '1') or
                 (counter_cnt = to_unsigned(LFSR_BP_EN_PERIOD, 16))
                 else '0';
  counter : util.util.counter
    generic map(
      BIT_WIDTH => 16)
    port map(
      clk      => clk,
      rst      => counter_rst,
      en       => '1',
      cnt      => counter_cnt);

  lfsr : misc_prims.misc_prims.lfsr
    generic map(
      POLYNOMIAL => "111000001000",
      SEED       => "000000000001")
    port map(
      clk => clk,
      rst => rst,
      en  => counter_rst,
      reg => lfsr_reg);

  irdy <= '1'         when (backpressure_select = NO_BP) else
          lfsr_reg(0) when (backpressure_select = LFSR_BP) else
          '0';

  file_write : process(clk)
    file     data_file     : text open write_mode is FILENAME;
    variable data_file_row : line;
  begin
    if(rising_edge(clk)) then
      --if(on_first_line = '1') then
      --  write(data_file_row, 'i');
      --  write(data_file_row, ',');
      --  write(data_file_row, 'q');
      --  writeline(data_file, data_file_row);
      --  on_first_line <= '0';
      --end if;
      if((rst = '0') and (ivld = '1')) then
        if(isamp_drop = '1') then
          write(data_file_row, string'("ERROR_SAMP_DROP"));
          writeline(data_file, data_file_row);
        end if;
        if(ivld = '1') then
          write(data_file_row, to_integer(signed(idata.i)));
          write(data_file_row, ',');
          write(data_file_row, to_integer(signed(idata.q)));
          writeline(data_file, data_file_row);
        end if;
      end if;
    end if;
  end process file_write;

end rtl;
