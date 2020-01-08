-- TODO / FIXME - support WSI_DATA_WIDTH of 16
library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;
library ocpi; library misc_prims;

entity iqstream_prot_out_adapter is
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
    -- OUTPUT
    odata        : out std_logic_vector(WSI_DATA_WIDTH-1 downto 0);
    ovalid       : out ocpi.types.Bool_t;
    obyte_enable : out std_logic_vector(WSI_MBYTEEN_WIDTH-1 downto 0);
    ogive        : out ocpi.types.Bool_t;
    osom         : out ocpi.types.Bool_t;
    oeom         : out ocpi.types.Bool_t;
    oeof         : out ocpi.types.Bool_t;
    oready       : in  ocpi.types.Bool_t);
end entity;
architecture rtl of iqstream_prot_out_adapter is
  constant SAMPLES_SEQUENCE_LENGTH        : positive := 2048;
  constant SAMPLES_MESSAGE_SIZE_BIT_WIDTH : positive :=
      ocpi.util.width_for_max(SAMPLES_SEQUENCE_LENGTH);
  constant MESSAGE_SIZE_NUM_GIVES         : unsigned := to_unsigned(
                                            SAMPLES_SEQUENCE_LENGTH,
                                            SAMPLES_MESSAGE_SIZE_BIT_WIDTH);
  signal give              : std_logic := '0';
  signal message_sizer_som : std_logic := '0';
  signal message_sizer_eom : std_logic := '0';
begin

  give <= oready and ivld;

  wsi_data_width_32 : if(WSI_DATA_WIDTH = 32) generate

    message_sizer : misc_prims.ocpi.wsi_message_sizer
      generic map(
        SIZE_BIT_WIDTH => SAMPLES_MESSAGE_SIZE_BIT_WIDTH)
      port map(
        clk                    => clk,
        rst                    => rst,
        give                   => give,
        message_size_num_gives => MESSAGE_SIZE_NUM_GIVES,
        som                    => message_sizer_som,
        eom                    => message_sizer_eom);

    irdy  <= oready;
    odata <= idata.q & idata.i;

  end generate wsi_data_width_32;

  ogive        <= give;
  osom         <= message_sizer_som;
  oeom         <= message_sizer_eom;
  obyte_enable <= (others => '1');
  ovalid       <= ivld;
  oeof         <= '0';

end rtl;
