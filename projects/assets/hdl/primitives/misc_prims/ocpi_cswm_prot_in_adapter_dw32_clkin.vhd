library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;
library misc_prims; use misc_prims.ocpi.all; use misc_prims.misc_prims.all;
library ocpi; use ocpi.types.all;
library util; use util.all;

entity cswm_prot_in_adapter_dw32_clkin is
  port(
    -- INPUT
    iclk      : in  std_logic;
    irst      : in  std_logic;
    idata     : in  std_logic_vector(31 downto 0);
    ivalid    : in  Bool_t;
    iready    : in  Bool_t;
    isom      : in  Bool_t;
    ieom      : in  Bool_t;
    iopcode   : in  complex_short_with_metadata_opcode_t;
    ieof      : in  Bool_t;
    itake     : out Bool_t;
    -- OUTPUT
    odata     : out data_complex_t;
    ometadata : out metadata_t;
    ovld      : out std_logic;
    ordy      : in  std_logic);
end entity;
architecture rtl of cswm_prot_in_adapter_dw32_clkin is

  signal eozlm   : std_logic := '0';
  signal iinfo   : std_logic := '0';
  signal ixfer   : std_logic := '0';
  signal take    : std_logic := '0';
  signal itake_s : std_logic := '0';
  signal data_r  : std_logic_vector(31 downto 0) :=
                   (others => '0');

  signal metadata               : metadata_t;
  signal take_time_final        : std_logic := '0';
  signal take_samp_period_final : std_logic := '0';

  signal arg_31_0 : std_logic_vector(31 downto 0) := (others => '0');
  signal arg_63_0 : std_logic_vector(63 downto 0) := (others => '0');
begin

  eozlm_gen : util.util.zlm_detector
    port map(
      clk         => iclk,
      reset       => irst,
      som         => isom,
      valid       => ivalid,
      eom         => ieom,
      ready       => iready,
      take        => itake_s,
      eozlm_pulse => open,
      eozlm       => eozlm);

  iinfo <= '1' when ((iready = btrue) and ((ivalid = btrue) or (eozlm = '1')))
           else '0';

  take  <= iinfo and ordy;
  ixfer <= iinfo and itake_s;
  --ixfer <= take;

  data_reg : process(iclk)
  begin
    if(rising_edge(iclk)) then
      if(irst = '1') then
        data_r <= (others => '0');
      elsif(take = '1') then
        data_r <= idata;
      end if;
    end if;
  end process data_reg;

  take_final_regs : process(iclk)
  begin
    if(rising_edge(iclk)) then
      if(irst = '1') then
        take_time_final        <= '0';
        take_samp_period_final <= '0';
      elsif(take = '1') then
        if(iopcode = TIME_TIME) then
          take_time_final <= (not take_time_final);
        else
          take_time_final <= '0';
        end if;
        if(iopcode = INTERVAL) then
          take_samp_period_final <= (not take_samp_period_final);
        else
          take_samp_period_final <= '0';
        end if;
      end if;
    end if;
  end process take_final_regs;

  -- reference https://opencpi.github.io/OpenCPI_HDL_Development.pdf section
  -- 3.8.1 Message Payloads vs. Physical Data Width on Data Interfaces
  arg_31_0 <= idata;
  arg_63_0 <= idata & data_r;

  metadata.eof             <= '1' when (ieof = btrue) and (ixfer = '1')
                              else '0';
  metadata.flush           <= '1' when (iopcode = FLUSH) and (ixfer = '1')
                              else '0';
  metadata.error_samp_drop <= '1' when (iopcode = SYNC) and (ixfer = '1')
                              else '0';
  metadata.data_vld        <= '1' when (iopcode = SAMPLES) and (ixfer = '1')
                              else '0';
  metadata.time            <= unsigned(arg_63_0);
  metadata.time_vld        <= '1' when (take_time_final = '1') and (ixfer = '1')
                              else '0';
  metadata.samp_period     <= unsigned(arg_63_0);
  metadata.samp_period_vld <= '1' when (take_samp_period_final = '1') and
                              (ixfer = '1') else '0';

  -- necessary to prevent combinatorial loop, depending an what's connected to
  -- ovld,ordy
  pipeline : process(iclk)
  begin
    if(rising_edge(iclk)) then
      if(irst = '1') then
        odata.i  <= (others => '0');
        odata.q  <= (others => '0');
        ometadata.flush           <= '0';
        ometadata.error_samp_drop <= '0';
        ometadata.data_vld        <= '0';
        ometadata.time            <= (others => '0');
        ometadata.time_vld        <= '0';
        ometadata.samp_period     <= (others => '0');
        ometadata.samp_period_vld <= '0';
        ovld <= '0';
        --itake_s <= '0';
      else
        --itake_s <= take;
        if(ordy = '1') then
        --else
          odata.i   <= arg_31_0(15 downto 0);
          odata.q   <= arg_31_0(31 downto 16);
          ometadata <= metadata;
  
          -- this is an optimization (don't declare valid unless we have to)
          ovld <= metadata.flush or
                  metadata.error_samp_drop or
                  metadata.data_vld or
                  metadata.time_vld or
                  metadata.samp_period_vld;
         end if;
      end if;
    end if;
  end process pipeline;

  itake_s <= take;

  itake <= itake_s;
  --itake <= take;

end rtl;
