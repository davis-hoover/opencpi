library ieee;
use ieee.std_logic_1164.all, ieee.numeric_std.all, ieee.math_real.all;
use std.textio.all; use ieee.std_logic_textio.all;
library util;
library protocol; use protocol.complex_short_with_metadata.all;
library misc_prims; use misc_prims.misc_prims.all;

entity ctrl_file_writer is
  generic(
    FILENAME : string);
  port(
    clk    : in  std_logic;
    rst    : in  std_logic;
    ctrl   : in  time_corrector_ctrl_t;
    status : in  time_corrector_status_t);
end entity ctrl_file_writer;
architecture rtl of ctrl_file_writer is
  signal clk_cnt         : unsigned(15 downto 0) := (others => '0');
  signal on_first_line   : std_logic := '0';
  signal ctrl_bypass     : integer := 0;
  signal status_overflow : integer := 0;
begin

  clk_counter : util.util.counter
    generic map(
      BIT_WIDTH => 16)
    port map(
      clk => clk,
      rst => rst,
      en  => '1',
      cnt => clk_cnt);

  ctrl_bypass     <= 1 when ctrl.bypass = '1' else 0;
  status_overflow <= 1 when status.overflow = '1' else 0;

  file_write : process(clk)
    file     data_file     : text open write_mode is FILENAME;
    variable data_file_row : line;
  begin
    if(rising_edge(clk)) then
      if(rst = '1') then
        on_first_line <= '1';
      elsif(on_first_line = '1') then
        write(data_file_row, string'("clk_cnt,ctrl_bypass,ctrl_time_correction,status_overflow"));
        writeline(data_file, data_file_row);
        on_first_line <= '0';
      else
        write(data_file_row, to_integer(clk_cnt));
        write(data_file_row, ',');
        write(data_file_row, ctrl_bypass);
        write(data_file_row, ',');
        write(data_file_row, to_integer(signed(ctrl.time_correction)));
        write(data_file_row, ',');
        write(data_file_row, status_overflow);
        writeline(data_file, data_file_row);
      end if;
    end if;
  end process file_write;

end rtl;
