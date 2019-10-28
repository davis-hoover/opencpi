library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all, ieee.math_real.all;

entity level_to_pulse_converter is
  port(
    clk   : in  std_logic;
    rst   : in  std_logic;
    level : in  std_logic;
    pulse : out std_logic);
end level_to_pulse_converter;
architecture rtl of level_to_pulse_converter is
  signal level_r : std_logic := '0';
begin

  process(clk)
  begin
    if(rising_edge(clk)) then
      if(rst = '1') then
        level_r <= '0';
      else
        level_r <= level;
      end if;
    end if;
  end process;

  pulse <= level xor level_r;

end rtl;
