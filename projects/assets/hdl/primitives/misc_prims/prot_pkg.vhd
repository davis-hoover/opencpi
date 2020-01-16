library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;
library misc_prims; library ocpi;

package prot is

type cswm_opcode_t is (
  SAMPLES, TIME_TIME, INTERVAL, FLUSH, SYNC, END_OF_SAMPLES);

component wsi_message_sizer is
  generic(
    SIZE_BIT_WIDTH : positive);
  port(
    clk                    : in  std_logic;
    rst                    : in  std_logic;
    give                   : in  std_logic;
    message_size_num_gives : in  unsigned(SIZE_BIT_WIDTH-1 downto 0);
    som                    : out std_logic;
    eom                    : out std_logic);
end component;

component iqstream_marshaller is
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

component cswm_marshaller is
  generic(
    WSI_DATA_WIDTH         : positive := 16; -- 16 is default of codegen, but
                                             -- MUST USE 32 FOR NOW
    OUT_PORT_MBYTEEN_WIDTH : positive);
  port(
    clk          : in  std_logic;
    rst          : in  std_logic;
    -- INPUT
    idata        : in  misc_prims.misc_prims.data_complex_t;
    imetadata    : in  misc_prims.misc_prims.metadata_t;
    ivld         : in  std_logic;
    irdy         : out std_logic;
    -- OUTPUT
    odata        : out std_logic_vector(31 downto 0);
    ovalid       : out ocpi.types.Bool_t;
    obyte_enable : out std_logic_vector(OUT_PORT_MBYTEEN_WIDTH-1 downto 0);
    ogive        : out ocpi.types.Bool_t;
    osom         : out ocpi.types.Bool_t;
    oeom         : out ocpi.types.Bool_t;
    oopcode      : out cswm_opcode_t;
    oeof         : out ocpi.types.Bool_t;
    oready       : in  ocpi.types.Bool_t);
end component;

component cswm_demarshaller is
  generic(
    WSI_DATA_WIDTH : positive := 16); -- 16 is default of codegen, but
                                      -- MUST USE 32 FOR NOW
  port(
    clk       : in  std_logic;
    rst       : in  std_logic;
    -- INPUT
    idata     : in  std_logic_vector(WSI_DATA_WIDTH-1 downto 0);
    ivalid    : in  ocpi.types.Bool_t;
    iready    : in  ocpi.types.Bool_t;
    isom      : in  ocpi.types.Bool_t;
    ieom      : in  ocpi.types.Bool_t;
    iopcode   : in  cswm_opcode_t;
    ieof      : in  ocpi.types.Bool_t;
    itake     : out ocpi.types.Bool_t;
    -- OUTPUT
    odata     : out misc_prims.misc_prims.data_complex_t;
    ometadata : out misc_prims.misc_prims.metadata_t;
    ovld      : out std_logic;
    ordy      : in  std_logic);
end component;

-- TODO / FIXME - consolidate w/ cswm_demarshaller
component cswm_marshaller_old is
  generic(
    OUT_PORT_MBYTEEN_WIDTH : positive);
  port(
    clk          : in  std_logic;
    rst          : in  std_logic;
    -- INPUT
    idata        : in  misc_prims.misc_prims.data_complex_t;
    imetadata    : in  misc_prims.misc_prims.metadata_t;
    ivld         : in  std_logic;
    irdy         : out std_logic;
    -- OUTPUT
    odata        : out std_logic_vector(31 downto 0);
    ovalid       : out ocpi.types.Bool_t;
    obyte_enable : out std_logic_vector(OUT_PORT_MBYTEEN_WIDTH-1 downto 0);
    ogive        : out ocpi.types.Bool_t;
    osom         : out ocpi.types.Bool_t;
    oeom         : out ocpi.types.Bool_t;
    oopcode      : out cswm_opcode_t;
    oeof         : out ocpi.types.Bool_t;
    oready       : in  ocpi.types.Bool_t);
end component;

end package prot;
