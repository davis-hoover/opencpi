library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;
library ocpi;
library misc_prims; use misc_prims.prot.all;

entity cswm_marshaller_old is
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
end entity;
architecture rtl of cswm_marshaller_old is

  constant SAMPLES_MESSAGE_SIZE_BIT_WIDTH : positive := 16;
  type state_t is (SAMPLES, TIME_63_32, TIME_31_0, INTERVAL_63_32,
                   INTERVAL_31_0, FLUSH, SYNC, IDLE);

  signal idata_r : misc_prims.misc_prims.data_complex_t;

  signal ivld_r  : std_logic := '0';
  signal ivld_r2 : std_logic := '0';

  signal irdy_s : std_logic := '0';

  signal metadata_zeros : std_logic_vector(
         misc_prims.misc_prims.METADATA_BIT_WIDTH-1 downto 0) :=
         (others => '0');
  signal imetadata_r  : misc_prims.misc_prims.metadata_t;
  signal imetadata_r2 : misc_prims.misc_prims.metadata_t;

  signal state        : state_t := IDLE;
  signal state_r      : state_t := IDLE;

  signal samples_eom  : std_logic := '0';
  signal give         : std_logic := '0';
  signal som          : std_logic := '0';
  signal eom          : std_logic := '0';

  signal message_sizer_rst      : std_logic := '0';
  signal message_sizer_give     : std_logic := '0';
  signal message_sizer_som      : std_logic := '0';
  signal message_sizer_eom      : std_logic := '0';
  signal force_end_of_samples   : std_logic := '0';
  signal force_end_of_samples_r : std_logic := '0';

  signal opcode : cswm_opcode_t := SAMPLES;
  signal pending_samples_eom : std_logic := '0';

begin

  pipeline : process(clk)
  begin
    if(rising_edge(clk)) then
      if(rst = '1') then
        idata_r.i   <= (others => '0');
        idata_r.q   <= (others => '0');
        imetadata_r <= misc_prims.misc_prims.from_slv(metadata_zeros);
        ivld_r      <= '0';
        irdy        <= '0';
      else
        idata_r     <= idata;
        imetadata_r <= imetadata;
        ivld_r      <= ivld;
        irdy        <= irdy_s;
      end if;
    end if;
  end process pipeline;

  metadata_reg : process(clk)
  begin
    if(rising_edge(clk)) then
      if(rst = '1') then
        imetadata_r2 <= misc_prims.misc_prims.from_slv(metadata_zeros);
      elsif(ivld_r = '1') then
        imetadata_r2 <= imetadata_r;
      end if;
    end if;
  end process metadata_reg;

  regs : process(clk)
  begin
    if(rising_edge(clk)) then
      if(rst = '1') then
        ivld_r2                <= '0';
        state_r                <= IDLE;
        force_end_of_samples_r <= '0';
      elsif(oready = '1') then
        ivld_r2                <= ivld_r;
        state_r                <= state;
        force_end_of_samples_r <= force_end_of_samples;
      end if;
    end if;
  end process regs;

  pending_samples_eom_gen : process(clk)
  begin
    if(rising_edge(clk)) then
      if(rst = '1') then
        pending_samples_eom <= '0';
      elsif((give = '1') and (opcode = SAMPLES)) then
        if(eom = '1') then
          pending_samples_eom <= '0';
        elsif(som = '1') then
          pending_samples_eom <= '1';
        end if;
      end if;
    end if;
  end process pending_samples_eom_gen;

  -- sets the priority of multiplexing of output messages
  imetadata_demux : process(ivld_r, ivld_r2, oready, imetadata_r, state_r)
  begin
    if(oready = '1') then
      if(state_r = TIME_31_0) and (ivld_r2 = '1') then
        irdy_s <= (not imetadata_r2.error_samp_drop) and
                  (not imetadata_r2.data_vld) and
                  (not imetadata_r2.samp_period_vld) and
                  (not imetadata_r2.flush);
        state <= TIME_63_32;
        force_end_of_samples <= '0';
      elsif(state_r = INTERVAL_31_0) and (ivld_r2 = '1') then
        irdy_s <= (not imetadata_r2.error_samp_drop) and
                  (not imetadata_r2.data_vld) and
                  (not imetadata_r2.time_vld) and
                  (not imetadata_r2.flush);
        state <= INTERVAL_63_32;
        force_end_of_samples <= '0';
      elsif((imetadata_r.error_samp_drop = '1') or (force_end_of_samples_r = '1'))
          and (ivld_r = '1') then
        irdy_s <= (not imetadata_r.data_vld) and
                  (not imetadata_r.time_vld) and
                  (not imetadata_r.samp_period_vld) and
                  (not imetadata_r.flush);
        if(pending_samples_eom = '1') then
          state <= SAMPLES;
          force_end_of_samples <= '1';
        else
          state <= SYNC;
          force_end_of_samples <= '0';
        end if;
      elsif(imetadata_r.time_vld = '1') and (ivld_r = '1') then
        irdy_s <= '0';
        state <= TIME_31_0;
        force_end_of_samples <= '0';
      elsif(imetadata_r.data_vld = '1') and (ivld_r = '1') then
        irdy_s <= (not imetadata_r.error_samp_drop) and
                  (not imetadata_r.time_vld) and
                  (not imetadata_r.samp_period_vld) and
                  (not imetadata_r.flush);
        state <= SAMPLES;
        force_end_of_samples <= '0';
      elsif(imetadata_r.samp_period_vld = '1') and (ivld_r = '1') then
        irdy_s <= '0';
        state <= INTERVAL_31_0;
        force_end_of_samples <= '0';
      elsif(imetadata_r.flush = '1') and (ivld_r = '1') then
        irdy_s <= '1';
        state <= FLUSH;
        force_end_of_samples <= '0';
      else
        irdy_s <= '1';
        state <= IDLE;
        force_end_of_samples <= '0';
      end if;
    else
      irdy_s <= '0';
      state <= IDLE;
      force_end_of_samples <= '0';
    end if;
  end process imetadata_demux;

  ogen : process(state, idata_r, message_sizer_som, message_sizer_eom,
                 force_end_of_samples, oready, imetadata_r2, imetadata_r)
  begin
    case state is
      when SAMPLES =>
        opcode    <= SAMPLES;
        odata   <= idata_r.q & idata_r.i;
        som     <= message_sizer_som;

        -- handles forced EOM due to data_vld=1 error_samp_drop=1
        ovalid  <= not force_end_of_samples;

        eom     <= message_sizer_eom or force_end_of_samples;
        give    <= oready;
      when TIME_63_32 =>
        opcode    <= TIME_TIME;
        odata <= std_logic_vector(imetadata_r2.time(63 downto 32));
        som    <= '0';
        ovalid <= '1';
        eom    <= '1';
        give   <= oready;
      when TIME_31_0 =>
        opcode    <= TIME_TIME;
        odata <= std_logic_vector(imetadata_r.time(31 downto 0));
        som    <= '1';
        ovalid <= '1';
        eom    <= '0';
        give   <= oready;
      when INTERVAL_63_32 =>
        opcode    <= INTERVAL;
        odata <= std_logic_vector(imetadata_r2.samp_period(63 downto 32));
        som    <= '0';
        ovalid <= '1';
        eom    <= '1';
        give   <= oready;
      when INTERVAL_31_0 =>
        opcode    <= INTERVAL;
        odata <= std_logic_vector(imetadata_r.samp_period(31 downto 0));
        som    <= '1';
        ovalid <= '1';
        eom    <= '0';
        give   <= oready;
      when SYNC =>
        opcode    <= SYNC;
        som    <= '1';
        ovalid <= '0';
        eom    <= '1';
        give   <= oready;
      when FLUSH =>
        opcode    <= FLUSH;
        som    <= '1';
        ovalid <= '0';
        eom    <= '1';
        give   <= oready;
      when others =>
        som    <= '0';
        ovalid <= '0';
        eom    <= '0';
        give   <= '0';
    end case;
  end process ogen;

  oopcode <= opcode;

  message_sizer_rst <= rst or force_end_of_samples;
  message_sizer_give <= '1' when ((give = '1') and (opcode = SAMPLES)) else '0';

  message_sizer : misc_prims.prot.wsi_message_sizer
    generic map(
      SIZE_BIT_WIDTH => SAMPLES_MESSAGE_SIZE_BIT_WIDTH)
    port map(
      clk                    => clk,
      rst                    => message_sizer_rst,
      give                   => message_sizer_give,
      message_size_num_gives => to_unsigned(4092, 16),
      som                    => message_sizer_som,
      eom                    => message_sizer_eom);

  ogive        <= give;
  osom         <= som;
  oeom         <= eom;
  oeof         <= '0';
  obyte_enable <= (others => '1');

end rtl;
