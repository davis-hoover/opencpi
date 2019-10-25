library IEEE; use IEEE.std_logic_1164.all, ieee.numeric_std.all;
library misc_prims; use misc_prims.misc_prims.all;

-- narrows data bus
entity data_narrower is
  generic(
    BITS_PACKED_INTO_LSBS    : boolean := true);
  port(
    -- INPUT
    clk       : in  std_logic;
    rst       : in  std_logic;
    idata     : in  data_complex_t;
    imetadata : in  metadata_dac_t;
    ivld      : in  std_logic;
    irdy      : out std_logic;
    -- OUTPUT
    odata     : out data_complex_dac_t;
    ometadata : out metadata_dac_t;
    ovld      : out std_logic;
    ordy      : in  std_logic);
end entity data_narrower;
architecture rtl of data_narrower is
begin

  bits_packed_into_lbsbs_false : if(BITS_PACKED_INTO_LSBS = false) generate
    odata.i <= idata.i(idata.i'left downto idata.i'left-odata.i'length+1);
    odata.q <= idata.q(idata.i'left downto idata.i'left-odata.i'length+1);
  end generate;

  bits_packed_into_lbsbs_true : if(BITS_PACKED_INTO_LSBS) generate
    odata.i <= idata.i(odata.i'left downto 0);
    odata.q <= idata.q(odata.i'left downto 0);
  end generate;

  ometadata <= imetadata;
  ovld <= ivld;
  irdy <= ordy;

end rtl;
