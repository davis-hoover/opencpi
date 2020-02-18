library ieee;
use ieee.std_logic_1164.all, ieee.numeric_std.all, ieee.math_real.all;
use std.textio.all; use ieee.std_logic_textio.all;
library util;
library protocol; use protocol.complex_short_with_metadata.all;
library misc_prims; use misc_prims.misc_prims.all;

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
    iprotocol               : in  protocol_t;
    irdy                    : out std_logic);
end entity file_writer;
architecture rtl of file_writer is
  signal irdy_s        : std_logic := '0';
  signal lfsr_reg      : std_logic_vector(11 downto 0) := (others => '0');
  signal clk_cnt       : unsigned(15 downto 0) := (others => '0');
  signal on_first_line : std_logic := '0';
begin

  clk_counter : util.util.counter
    generic map(
      BIT_WIDTH => 16)
    port map(
      clk      => clk,
      rst      => rst,
      en       => '1',
      cnt      => clk_cnt);

  lfsr : misc_prims.misc_prims.lfsr
    generic map(
      POLYNOMIAL => "111000001000",
      SEED       => "000000000001")
    port map(
      clk => clk,
      rst => rst,
      en  => '1',
      reg => lfsr_reg);

  irdy_s <= '1'         when (backpressure_select = NO_BP) else
            lfsr_reg(0) when (backpressure_select = LFSR_BP) else
            '0';
  irdy <= irdy_s;

  file_write : process(clk)
    file     data_file     : text open write_mode is FILENAME;
    variable data_file_row : line;
  begin
    if(rising_edge(clk)) then
      if(rst = '1') then
        on_first_line <= '1';
      elsif(on_first_line = '1') then
        write(data_file_row, string'("clk_cnt,op_samples_iq_i,op_samples_iq_q,op_time_fract_sec,op_time_sec,op_interval_delta_time,op_flush,op_sync,op_end_of_samples,eof"));
        writeline(data_file, data_file_row);
        on_first_line <= '0';
      elsif(irdy_s = '1') then
        write(data_file_row, to_integer(clk_cnt));
        write(data_file_row, ',');
        -- op: samples, arg: iq
        if(iprotocol.samples_vld = '1') then
          write(data_file_row, to_integer(signed(iprotocol.samples.iq.i)));
          write(data_file_row, ',');
          write(data_file_row, to_integer(signed(iprotocol.samples.iq.q)));
        end if;
        write(data_file_row, ',');
        -- op: time, arg: fract_sec
        if(iprotocol.time_vld = '1') then
          write(data_file_row, to_integer(unsigned(iprotocol.time.fract_sec)));
        end if;
        write(data_file_row, ',');
        -- op: time, arg: fract_sec
        if(iprotocol.time_vld = '1') then
          write(data_file_row, to_integer(unsigned(iprotocol.time.sec)));
        end if;
        write(data_file_row, ',');
        -- op: interval, arg: delta_time
        if(iprotocol.interval_vld = '1') then
          write(data_file_row, to_integer(unsigned(iprotocol.interval.delta_time)));
        end if;
        write(data_file_row, ',');
        -- op: flush
        if(iprotocol.flush= '1') then
          write(data_file_row, string'("flush"));
        end if;
        write(data_file_row, ',');
        -- op: sync
        if(iprotocol.sync = '1') then
          write(data_file_row, string'("sync"));
        end if;
        write(data_file_row, ',');
        -- op: end_of_samples
        if(iprotocol.end_of_samples = '1') then
          write(data_file_row, string'("end_of_samples"));
        end if;
        write(data_file_row, ',');
        -- eof
        if(iprotocol.eof = '1') then
          write(data_file_row, string'("eof"));
        end if;
        writeline(data_file, data_file_row);
      end if;
    end if;
  end process file_write;

end rtl;
