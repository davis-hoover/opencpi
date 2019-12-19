library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;
library misc_prims; use misc_prims.misc_prims.all;
library ocpi; use ocpi.types.all;

-- sizes messages by counting gives
entity wsi_message_sizer is
  generic(
    SIZE_BIT_WIDTH : positive);
  port(
    clk                    : in  std_logic;
    rst                    : in  std_logic;
    give                   : in  Bool_t;
    message_size_num_gives : in  unsigned(SIZE_BIT_WIDTH-1 downto 0);
    som                    : out Bool_t;
    eom                    : out Bool_t);
end entity wsi_message_sizer;
architecture rtl of wsi_message_sizer is
  signal eom_s            : std_logic := '0';
  signal give_counter_rst : std_logic := '0';
  signal give_counter_cnt : unsigned(SIZE_BIT_WIDTH-1 downto 0) := (others => '0');
begin

  eom_s <= '1' when (give_counter_cnt = message_size_num_gives-1) else '0';
  give_counter_rst <= rst or eom_s;

  give_counter : counter
    generic map(
      BIT_WIDTH => SIZE_BIT_WIDTH)
    port map(
      clk => clk,
      rst => give_counter_rst,
      en  => give,
      cnt => give_counter_cnt);

  som <= btrue when (give_counter_cnt = 0) else bfalse;
  eom <= eom_s;

end rtl;
