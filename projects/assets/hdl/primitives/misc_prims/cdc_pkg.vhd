library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;
library protocol;

package cdc is

component fifo_complex_short_with_metadata is
  generic(
    DEPTH : natural := 2);
  port(
    -- INPUT
    iclk      : in  std_logic;
    irst      : in  std_logic;
    ienq      : in  std_logic;
    iprotocol : in  protocol.complex_short_with_metadata.protocol_t;
    ifull_n   : out std_logic;
    -- OUTPUT
    oclk      : in  std_logic;
    odeq      : in  std_logic;
    oprotocol : out protocol.complex_short_with_metadata.protocol_t;
    oempty_n  : out std_logic);
end component;

end package cdc;
