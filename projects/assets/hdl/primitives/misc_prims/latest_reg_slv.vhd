library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;

entity latest_reg_slv is
  generic(
    BIT_WIDTH : positive);
  port(
    clk      : in  std_logic;
    rst      : in  std_logic;
    din      : in  std_logic_vector(BIT_WIDTH-1 downto 0);
    din_vld  : in  std_logic;
    dout     : out std_logic_vector(BIT_WIDTH-1 downto 0);
    dout_vld : out std_logic);
end entity latest_reg_slv;
architecture rtl of latest_reg_slv is
  signal latest_val     : std_logic_vector(BIT_WIDTH-1 downto 0) :=
                          (others => '0');
  signal latest_val_vld : std_logic := '0';
begin

  process(clk)
  begin
    if(rising_edge(clk)) then
      if(rst = '1') then
        latest_val     <= (others => '0');
        latest_val_vld <= '0';
      elsif(din_vld = '1') then
        latest_val     <= din;
        latest_val_vld <= '1';
      end if;
    end if;
  end process;

  dout     <= latest_val;
  dout_vld <= latest_val_vld;

end rtl;
