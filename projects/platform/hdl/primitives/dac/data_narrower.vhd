library IEEE; use IEEE.std_logic_1164.all, ieee.numeric_std.all;
library protocol;
library misc_prims; use misc_prims.misc_prims.all;

-- narrows data bus
entity data_narrower is
  generic(
    -- the DATA PIPE LATENCY CYCLES is currently 0
    BITS_PACKED_INTO_LSBS    : boolean := true);
  port(
    -- INPUT
    clk           : in  std_logic;
    rst           : in  std_logic;
    iprotocol     : in  protocol.complex_short_with_metadata.protocol_t;
    imetadata     : in  metadata_dac_t;
    imetadata_vld : in  std_logic;
    irdy          : out std_logic;
    -- OUTPUT
    odata         : out data_complex_dac_t;
    odata_vld     : out std_logic;
    ometadata     : out metadata_dac_t;
    ometadata_vld : out std_logic;
    ordy          : in  std_logic);
end entity data_narrower;
architecture rtl of data_narrower is
  signal protocol_s : protocol.complex_short_with_metadata.protocol_t :=
                      protocol.complex_short_with_metadata.PROTOCOL_ZERO;
begin

  bits_packed_into_lbsbs_false : if(BITS_PACKED_INTO_LSBS = false) generate
    odata.i <= iprotocol.samples.iq.i(iprotocol.samples.iq.i'left downto
        iprotocol.samples.iq.i'left-odata.i'length+1);
    odata.q <= iprotocol.samples.iq.q(iprotocol.samples.iq.i'left downto
        iprotocol.samples.iq.i'left-odata.i'length+1);
  end generate;

  bits_packed_into_lbsbs_true : if(BITS_PACKED_INTO_LSBS) generate
    odata.i <= iprotocol.samples.iq.i(odata.i'left downto 0);
    odata.q <= iprotocol.samples.iq.q(odata.i'left downto 0);
  end generate;

  odata_vld     <= iprotocol.samples_vld;
  ometadata     <= imetadata;
  ometadata_vld <= imetadata_vld;
  irdy          <= ordy;

end rtl;
