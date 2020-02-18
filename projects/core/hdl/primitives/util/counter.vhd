library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;

entity counter is
  generic(
    BIT_WIDTH : positive);
  port(
    clk      : in  std_logic;
    rst      : in  std_logic;
    en       : in  std_logic;
    cnt      : out unsigned(BIT_WIDTH-1 downto 0));
end entity counter;
architecture rtl of counter is
  signal cnt_s : unsigned(BIT_WIDTH-1 downto 0) := (others => '0');
begin

  process(clk)
  begin
    if(rising_edge(clk)) then
      if(rst = '1') then
        cnt_s <= (others => '0');
      elsif(en = '1') then
        cnt_s <= cnt_s + 1;
      end if;
    end if;
  end process;

  cnt <= cnt_s;

end rtl;
