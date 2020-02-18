library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;
library misc_prims; use misc_prims.misc_prims.all;
library cdc; use cdc.all;

entity fifo_info is
  generic(
    DEPTH : natural := 2);
  port(
    -- INPUT
    iclk     : in  std_logic;
    irst     : in  std_logic;
    ienq     : in  std_logic;
    iinfo    : in  info_t;
    ifull_n  : out std_logic;
    -- OUTPUT
    oclk     : in  std_logic;
    odeq     : in  std_logic;
    oinfo    : out info_t;
    oempty_n : out std_logic);
end entity;
architecture rtl of fifo_info is
  signal src_in  : std_logic_vector(INFO_BIT_WIDTH-1 downto 0) :=
                   (others => '0');
  signal dst_out : std_logic_vector(INFO_BIT_WIDTH-1 downto 0) :=
                   (others => '0');
begin

  src_in <= to_slv(iinfo);

  fifo : cdc.cdc.fifo
    generic map(
      WIDTH       => INFO_BIT_WIDTH,
      DEPTH       => DEPTH)
    port map(
      src_CLK     => iclk,
      src_RST     => irst,
      src_ENQ     => ienq,
      src_in      => src_in,
      src_FULL_N  => ifull_n,
      dst_CLK     => oclk,
      dst_DEQ     => odeq,
      dst_out     => dst_out,
      dst_EMPTY_N => oempty_n);

  oinfo <= from_slv(dst_out);

end rtl;
