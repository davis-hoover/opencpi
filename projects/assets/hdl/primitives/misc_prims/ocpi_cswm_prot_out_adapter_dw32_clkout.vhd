-- TODO / FIXME - this implementation will be affect by protocol changes (which are expected - see #124)
-- TODO / FIXME - USER opcode is not supported!
library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;
library misc_prims; use misc_prims.ocpi.all;
library misc_prims; use misc_prims.misc_prims.all;
library ocpi; use ocpi.types.all;

-- for use w/ port clockdirection='output'
entity cswm_prot_out_adapter_dw32_clkout is
  generic(
    OUT_PORT_MBYTEEN_WIDTH : positive);
  port(
    -- INPUT
    iclk         : in  std_logic;
    irst         : in  std_logic;
    idata        : in  data_complex_t;
    imetadata    : in  metadata_t;
    ivld         : in  std_logic;
    irdy         : out std_logic;
    -- OUTPUT
    oclk         : out std_logic;
    odata        : out std_logic_vector(31 downto 0);
    ovalid       : out Bool_t;
    obyte_enable : out std_logic_vector(OUT_PORT_MBYTEEN_WIDTH-1 downto 0);
    ogive        : out Bool_t;
    osom         : out Bool_t;
    oeom         : out Bool_t;
    oopcode      : out complex_short_with_metadata_opcode_t;
    oeof         : out Bool_t;
    oready       : in  Bool_t);
end entity;
architecture rtl of cswm_prot_out_adapter_dw32_clkout is
begin

  oclk <= iclk;

  adapter : cswm_prot_out_adapter_dw32_clkin
    generic map(
      OUT_PORT_MBYTEEN_WIDTH => OUT_PORT_MBYTEEN_WIDTH)
    port map(
      -- INPUT
      idata        => idata,
      imetadata    => imetadata,
      ivld         => ivld,
      irdy         => irdy,
      -- OUTPUT
      oclk         => iclk,
      orst         => irst,
      odata        => odata,
      ovalid       => ovalid,
      obyte_enable => obyte_enable,
      ogive        => ogive,
      osom         => osom,
      oeom         => oeom,
      oopcode      => oopcode,
      oeof         => oeof,
      oready       => oready);

end rtl;
