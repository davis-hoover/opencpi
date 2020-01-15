library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;
library misc_prims; use misc_prims.misc_prims.all; use misc_prims.ocpi.all;
library ocpi; use ocpi.types.all;

entity cswm_prot_in_adapter_dw32_clkout is
  port(
    -- INPUT
    iclk      : out std_logic;
    idata     : in  std_logic_vector(31 downto 0);
    ivalid    : in  Bool_t;
    iready    : in  Bool_t;
    isom      : in  Bool_t;
    ieom      : in  Bool_t;
    iopcode   : in  complex_short_with_metadata_opcode_t;
    ieof      : in  Bool_t;
    itake     : out Bool_t;
    -- OUTPUT
    oclk      : in  std_logic;
    orst      : in  std_logic;
    odata     : out data_complex_t;
    ometadata : out metadata_t;
    ovld      : out std_logic;
    ordy      : in  std_logic);
end entity;
architecture rtl of cswm_prot_in_adapter_dw32_clkout is
begin

  iclk <= oclk;

  adapter : cswm_prot_in_adapter_dw32_clkin
    port map(
      -- INPUT
      iclk      => oclk,
      irst      => orst,
      idata     => idata,
      ivalid    => ivalid,
      iready    => iready,
      isom      => isom,
      ieom      => ieom,
      iopcode   => iopcode,
      ieof      => ieof,
      itake     => itake,
      -- OUTPUT
      odata     => odata,
      ometadata => ometadata,
      ovld      => ovld,
      ordy      => ordy);
  
end rtl;
