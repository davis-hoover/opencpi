library IEEE; use IEEE.std_logic_1164.all, ieee.numeric_std.all;
library timed_sample_prot, adc_csts;

-- widens data bus (useful when downstream processing bit growth is anticipated)
entity data_widener is
  generic(
    -- the DATA PIPE LATENCY CYCLES is currently 0
    BITS_PACKED_INTO_MSBS : boolean := true);
  port(
    -- INPUT
    clk        : in  std_logic;
    rst        : in  std_logic;
    idata      : in  adc_csts.adc_csts.data_complex_t;
    isamp_drop : in  std_logic;
    ivld       : in  std_logic;
    irdy       : out std_logic;
    -- OUTPUT
    oprotocol  : out timed_sample_prot.complex_short_timed_sample.protocol_t;
    ordy       : in  std_logic);
end entity data_widener;
architecture rtl of data_widener is
  signal protocol_s : timed_sample_prot.complex_short_timed_sample.protocol_t :=
                      timed_sample_prot.complex_short_timed_sample.PROTOCOL_ZERO;
begin

  -- the DATA PIPE LATENCY CYCLES is currently 0

  bits_packed_into_mbsbs_true : if(BITS_PACKED_INTO_MSBS) generate
    protocol_s.sample.data.real(protocol_s.sample.data.real'left downto
        protocol_s.sample.data.real'left-idata.real'length+1) <= idata.real;
    protocol_s.sample.data.real(protocol_s.sample.data.real'left-idata.real'length downto
        0) <= (others => '0');
    protocol_s.sample.data.imaginary(protocol_s.sample.data.imaginary'left downto
        protocol_s.sample.data.imaginary'left-idata.imaginary'length+1) <= idata.imaginary;
    protocol_s.sample.data.imaginary(protocol_s.sample.data.imaginary'left-idata.imaginary'length downto
        0) <= (others => '0');
  end generate;

  bits_packed_into_mbsbs_false : if(BITS_PACKED_INTO_MSBS = false) generate
    protocol_s.sample.data.real(protocol_s.sample.data.real'left downto
        idata.real'left+1) <= (others => idata.real(idata.real'left));
    protocol_s.sample.data.real(idata.real'left downto 0) <= idata.real;
    protocol_s.sample.data.imaginary(protocol_s.sample.data.imaginary'left downto
        idata.imaginary'left+1) <= (others => idata.imaginary(idata.imaginary'left));
    protocol_s.sample.data.imaginary(idata.imaginary'left downto 0) <= idata.imaginary;
  end generate;

  protocol_s.sample_vld    <= ivld;
  protocol_s.discontinuity <= isamp_drop;

  oprotocol <= protocol_s;
  irdy      <= ordy;

end rtl;
