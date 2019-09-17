library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;

entity clk_src is
  generic(
    CLK_PERIOD : time);
  port(
    clk : out std_logic);
end entity clk_src;
architecture rtl of clk_src is
  signal clk_s : std_logic := '0';
begin

  process
  begin
    clk_s <= '1';
    wait for CLK_PERIOD/2;
    clk_s <= '0';
    wait for CLK_PERIOD/2;
  end process;

  clk <= clk_s;

end rtl;
