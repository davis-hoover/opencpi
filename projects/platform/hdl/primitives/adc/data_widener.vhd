library IEEE; use IEEE.std_logic_1164.all, ieee.numeric_std.all;
library protocol, adc;

-- widens data bus (useful when downstream processing bit growth is anticipated)
entity data_widener is
  generic(
    -- the DATA PIPE LATENCY CYCLES is currently 0
    BITS_PACKED_INTO_MSBS : boolean := true);
  port(
    -- INPUT
    clk        : in  std_logic;
    rst        : in  std_logic;
    idata      : in  adc.adc.data_complex_t;
    isamp_drop : in  std_logic;
    ivld       : in  std_logic;
    irdy       : out std_logic;
    -- OUTPUT
    oprotocol  : out protocol.complex_short_with_metadata.protocol_t;
    ordy       : in  std_logic);
end entity data_widener;
architecture rtl of data_widener is
  signal protocol_s : protocol.complex_short_with_metadata.protocol_t :=
                      protocol.complex_short_with_metadata.PROTOCOL_ZERO;
begin

  -- the DATA PIPE LATENCY CYCLES is currently 0

  bits_packed_into_mbsbs_true : if(BITS_PACKED_INTO_MSBS) generate
    protocol_s.samples.iq.i(protocol_s.samples.iq.i'left downto
        protocol_s.samples.iq.i'left-idata.i'length+1) <= idata.i;
    protocol_s.samples.iq.i(protocol_s.samples.iq.i'left-idata.i'length downto
        0) <= (others => '0');
    protocol_s.samples.iq.q(protocol_s.samples.iq.q'left downto
        protocol_s.samples.iq.q'left-idata.q'length+1) <= idata.q;
    protocol_s.samples.iq.q(protocol_s.samples.iq.q'left-idata.q'length downto
        0) <= (others => '0');
  end generate;

  bits_packed_into_mbsbs_false : if(BITS_PACKED_INTO_MSBS = false) generate
    protocol_s.samples.iq.i(protocol_s.samples.iq.i'left downto
        idata.i'left+1) <= (others => idata.i(idata.i'left));
    protocol_s.samples.iq.i(idata.i'left downto 0) <= idata.i;
    protocol_s.samples.iq.q(protocol_s.samples.iq.q'left downto
        idata.q'left+1) <= (others => idata.q(idata.q'left));
    protocol_s.samples.iq.q(idata.q'left downto 0) <= idata.q;
  end generate;

  protocol_s.samples_vld <= ivld;
  protocol_s.sync        <= ivld and isamp_drop;

  oprotocol <= protocol_s;
  irdy      <= ordy;

end rtl;
