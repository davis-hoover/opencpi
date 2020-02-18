library ieee;
use ieee.std_logic_1164.all, ieee.numeric_std.all, ieee.math_real.all;
use std.textio.all; use ieee.std_logic_textio.all;
library misc_prims; use misc_prims.misc_prims.all;

entity file_writer is
  generic(
    FILENAME : string);
  port(
    -- CTRL
    clk                     : in  std_logic;
    rst                     : in  std_logic;
    backpressure_select     : in  file_writer_backpressure_select_t;
    backpressure_select_vld : in  std_logic;
    -- INPUT
    idata                   : in  data_complex_dac_t;
    idata_vld               : in  std_logic;
    imetadata               : in  metadata_dac_t;
    imetadata_vld           : in  std_logic;
    irdy                    : out std_logic);
end entity file_writer;
architecture rtl of file_writer is
  signal lfsr_reg : std_logic_vector(11 downto 0) :=
                    (others => '0');
  signal irdy_s   : std_logic := '0';
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

  irdy_s <= '1'         when (backpressure_select = NO_BP)   else
            lfsr_reg(0) when (backpressure_select = LFSR_BP) else
            '0';
  irdy <= irdy_s;

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
      if(rst = '0') then
        if((imetadata_vld = '1') and (imetadata.underrun_error = '1')) then
          write(data_file_row, string'("ERROR_SAMP_NOT_AVAIL"));
          writeline(data_file, data_file_row);
        end if;
        if((irdy_s = '1') and (idata_vld = '1')) then
          write(data_file_row, to_integer(unsigned(idata.i)));
          write(data_file_row, ',');
          write(data_file_row, to_integer(unsigned(idata.q)));
          writeline(data_file, data_file_row);
        end if;
      end if;
    end if;
  end process file_write;

end rtl;
