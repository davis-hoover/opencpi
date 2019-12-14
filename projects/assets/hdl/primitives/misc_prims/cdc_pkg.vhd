library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;
library misc_prims; use misc_prims.misc_prims.all;

package cdc is

component fifo_info is
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
end component;

end package cdc;
