library IEEE; use IEEE.std_logic_1164.all, ieee.numeric_std.all;
library misc_prims; use misc_prims.misc_prims.all;

-- widens data bus (useful when downstream processing bit growth is anticipated)
entity data_widener is
  generic(
    DATA_PIPE_LATENCY_CYCLES : natural := 0;
    BITS_PACKED_INTO_MSBS    : boolean := true);
  port(
    -- INPUT
    clk       : in  std_logic;
    rst       : in  std_logic;
    idata     : in  data_complex_adc_t;
    imetadata : in  metadata_t;
    ivld      : in  std_logic;
    irdy      : out std_logic;
    -- OUTPUT
    odata     : out data_complex_t;
    ometadata : out metadata_t;
    ovld      : out std_logic;
    ordy      : in  std_logic);
end entity data_widener;
architecture rtl of data_widener is
begin

  data_pipe_latency_cycles_0 : if(DATA_PIPE_LATENCY_CYCLES = 0) generate

    bits_packed_into_mbsbs_true : if(BITS_PACKED_INTO_MSBS) generate
      odata.i(odata.i'left downto odata.i'left-idata.i'length+1) <= idata.i;
      odata.i(odata.i'left-idata.i'length downto 0) <= (others => '0');
      odata.q(odata.q'left downto odata.q'left-idata.q'length+1) <= idata.q;
      odata.q(odata.q'left-idata.q'length downto 0) <= (others => '0');
    end generate;

    bits_packed_into_mbsbs_false : if(BITS_PACKED_INTO_MSBS = false) generate
      odata.i(odata.i'left downto idata.i'left+1) <=
          (others => idata.i(idata.i'left));
      odata.i(idata.i'left downto 0) <= idata.i;
      odata.q(odata.q'left downto idata.q'left+1) <=
          (others => idata.q(idata.q'left));
      odata.q(idata.q'left downto 0) <= idata.q;
    end generate;

    ometadata <= imetadata;
    irdy <= ordy;
    ovld <= ivld;

  end generate;

end rtl;
