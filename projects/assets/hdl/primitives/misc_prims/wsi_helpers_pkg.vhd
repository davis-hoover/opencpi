library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;
library misc_prims; library ocpi;

package wsi_helpers is

component iqstream_prot_out_adapter is
  generic(
    WSI_DATA_WIDTH    : positive := 16; -- 16 is default of codegen, but
                                        -- MUST USE 32 FOR NOW
    WSI_MBYTEEN_WIDTH : positive);
  port(
    -- CTRL
    clk          : in  std_logic;
    rst          : in  std_logic;
    -- INPUT
    idata        : in  misc_prims.misc_prims.data_complex_t;
    ivld         : in  std_logic;
    irdy         : out std_logic;
    -- OUTPUT (WSI)
    odata        : out std_logic_vector(WSI_DATA_WIDTH-1 downto 0);
    ovalid       : out ocpi.types.Bool_t;
    obyte_enable : out std_logic_vector(WSI_MBYTEEN_WIDTH-1 downto 0);
    ogive        : out ocpi.types.Bool_t;
    osom         : out ocpi.types.Bool_t;
    oeom         : out ocpi.types.Bool_t;
    oeof         : out ocpi.types.Bool_t;
    oready       : in  ocpi.types.Bool_t);
end component;

end package wsi_helpers;
