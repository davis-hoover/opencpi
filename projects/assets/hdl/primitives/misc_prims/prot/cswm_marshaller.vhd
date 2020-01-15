library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;
library ocpi; library misc_prims;

-- for use w/ port clockdirection='input'
entity cswm_marshaller is
  generic(
    WSI_DATA_WIDTH         : positive := 16; -- 16 is default of codegen, but
                                             -- MUST USE 32 FOR NOW
    OUT_PORT_MBYTEEN_WIDTH : positive);
  port(
    -- INPUT
    idata        : in  misc_prims.misc_prims.data_complex_t;
    imetadata    : in  misc_prims.misc_prims.metadata_t;
    ivld         : in  std_logic;
    irdy         : out std_logic;
    -- OUTPUT
    oclk         : in  std_logic;
    orst         : in  std_logic;
    odata        : out std_logic_vector(WSI_DATA_WIDTH-1 downto 0);
    ovalid       : out ocpi.types.Bool_t;
    obyte_enable : out std_logic_vector(OUT_PORT_MBYTEEN_WIDTH-1 downto 0);
    ogive        : out ocpi.types.Bool_t;
    osom         : out ocpi.types.Bool_t;
    oeom         : out ocpi.types.Bool_t;
    oopcode      : out cswm_opcode_t;
    oeof         : out ocpi.types.Bool_t;
    oready       : in  ocpi.types.Bool_t);
end entity;
architecture rtl of cswm_marshaller is

  constant SAMPLES_MESSAGE_SIZE_BIT_WIDTH : positive := 16;
  type state_t is (SAMPLES, SAMPLES_EOM_ONLY, TIME_63_32, TIME_31_0, INTERVAL_63_32,
                   INTERVAL_31_0, FLUSH, SYNC, EOF, IDLE);

  signal idata_r : misc_prims.misc_prims.data_complex_t :=
                   misc_prims.misc_prims.data_complex_zero;

  signal in_xfer           : std_logic := '0';
  signal in_xfer_r         : std_logic := '0';
  signal irdy_s            : std_logic := '0';
  signal mux_start         : std_logic := '0';
  signal mux_end           : std_logic := '0';

  signal metadata_zeros : std_logic_vector(METADATA_BIT_WIDTH-1 downto 0) :=
                          (others => '0');
  signal imetadata_r  : misc_prims.misc_prims.metadata_t :=
                       misc_prims.misc_prims.metadata_zero;

  signal state        : state_t := IDLE;
  signal state_r      : state_t := IDLE;

  signal samples_som  : std_logic := '0';
  signal samples_eom  : std_logic := '0';
  signal give         : std_logic := '0';
  signal som          : std_logic := '0';
  signal eom          : std_logic := '0';

  signal message_sizer_rst      : std_logic := '0';
  signal message_sizer_give     : std_logic := '0';
  signal message_sizer_eom      : std_logic := '0';
  signal force_end_of_samples   : std_logic := '0';
  signal force_end_of_samples_r : std_logic := '0';

  signal opcode : cswm_opcode_t := SAMPLES;
  signal pending_samples_eom_gen_set : std_logic := '0';
  signal pending_samples_eom_gen_clr : std_logic := '0';
  signal pending_samples_eom_r       : std_logic := '0';

begin

  wsi_data_width_32 : if(WSI_DATA_WIDTH = 32) generate

    in_xfer <= irdy_s and ivld;

    in_xfer_reg : process(oclk)
    begin
      if(rising_edge(oclk)) then
        if(orst = '1') then
          in_xfer_r <= '0';
        else
          in_xfer_r <= in_xfer;
        end if;
      end if;
    end process in_xfer_reg;

    in_in_pipeline : process(oclk)
    begin
      if(rising_edge(oclk)) then
        if(orst = '1') then
          idata_r.i   <= (others => '0');
          idata_r.q   <= (others => '0');
          imetadata_r <= from_slv(metadata_zeros);
        elsif(in_xfer = '1') then
          idata_r     <= idata;
          imetadata_r <= imetadata;
        end if;
      end if;
    end process in_in_pipeline;

    in_out_pipeline : process(oclk)
    begin
      if(rising_edge(oclk)) then
        if(orst = '1') then
          irdy_s <= '0';
        else
          if((state = IDLE) and (mux_end = '1')) then
            irdy_s <= (not ivld) and oready;
          else
            irdy_s <= '0';
          end if;
        end if;
      end if;
    end process in_out_pipeline;

    irdy <= irdy_s;

    regs : process(oclk)
    begin
      if(rising_edge(oclk)) then
        if(orst = '1') then
          state_r                <= IDLE;
          force_end_of_samples_r <= '0';
        elsif(oready = '1') then
          state_r                <= state;
          force_end_of_samples_r <= force_end_of_samples;
        end if;
      end if;
    end process regs;

    pending_samples_eom_gen_set <= '1' when (give = '1') and (som = '1') and
                                   (opcode = SAMPLES) else '0';
    pending_samples_eom_gen_clr <= '1' when (give = '1') and (eom = '1') and
                                   (opcode = SAMPLES) else '0';

    pending_samples_eom_gen : set_clr
      port map(clk => oclk,
               rst => orst,
               set => pending_samples_eom_gen_set,
               clr => pending_samples_eom_gen_clr,
               q   => open,
               q_r => pending_samples_eom_r);

    mux_start <= in_xfer_r;
    mux_end   <= '1' when (state_r = IDLE) and (in_xfer= '0') and
                 (in_xfer_r = '0') else '0';

    -- sets the priority of multiplexing of output messages
    -- EOF, SYNC, TIME, INTERVAL, FLUSH, SAMPLES
    mux : process(oready, imetadata_r, mux_start, state_r, pending_samples_eom_r)
    begin
      if(oready = '1') then
        if((imetadata_r.eof = '1') and (
            (mux_start = '1') or
            (state_r = SAMPLES_EOM_ONLY))) then
          if(pending_samples_eom_r = '1') then
            state <= SAMPLES_EOM_ONLY;
          else
            state <= EOF;
          end if;
          force_end_of_samples <= pending_samples_eom_r;
        elsif((imetadata_r.error_samp_drop = '1') and (
            (mux_start = '1') or
            (state_r = SAMPLES_EOM_ONLY) or
            (state_r = EOF))) then
          if(pending_samples_eom_r = '1') then
            state <= SAMPLES_EOM_ONLY;
          else
            state <= SYNC;
          end if;
          force_end_of_samples <= pending_samples_eom_r;
        elsif((imetadata_r.time_vld = '1') and (
            (mux_start = '1') or
            (state_r = SAMPLES_EOM_ONLY) or
            (state_r = EOF) or
            (state_r = SYNC))) then
          if(pending_samples_eom_r = '1') then
            state <= SAMPLES_EOM_ONLY;
          else
            state <= TIME_31_0;
          end if;
          force_end_of_samples <= pending_samples_eom_r;
        elsif(state_r = TIME_31_0) then
          state                <= TIME_63_32;
          force_end_of_samples <= '0';
        elsif((imetadata_r.samp_period_vld = '1') and (
            (mux_start = '1') or
            (state_r = SAMPLES_EOM_ONLY) or
            (state_r = EOF) or
            (state_r = SYNC) or
            (state_r = TIME_63_32))) then
          if(pending_samples_eom_r = '1') then
            state <= SAMPLES_EOM_ONLY;
          else
            state <= INTERVAL_31_0;
          end if;
          force_end_of_samples <= pending_samples_eom_r;
        elsif(state_r = INTERVAL_31_0) then
          state                <= INTERVAL_63_32;
          force_end_of_samples <= '0';
        elsif((imetadata_r.flush = '1') and (
            (mux_start = '1') or
            (state_r = SAMPLES_EOM_ONLY) or
            (state_r = EOF) or
            (state_r = SYNC) or
            (state_r = TIME_63_32) or
            (state_r = INTERVAL_63_32))) then
          if(pending_samples_eom_r = '1') then
            state <= SAMPLES_EOM_ONLY;
          else
            state <= FLUSH;
          end if;
          force_end_of_samples <= pending_samples_eom_r;
        elsif((imetadata_r.data_vld = '1') and (
            (mux_start = '1') or
            (state_r = SAMPLES_EOM_ONLY) or
            (state_r = EOF) or
            (state_r = SYNC) or
            (state_r = TIME_63_32) or
            (state_r = INTERVAL_63_32) or
            (state_r = FLUSH))) then
          state                <= SAMPLES;
          force_end_of_samples <= '0';
        else
          state                <= IDLE;
          force_end_of_samples <= '0';
        end if;
      end if;
    end process mux;

    ogen : process(state, idata_r, samples_som, samples_eom, imetadata_r, oready)
    begin
      case state is
        when SAMPLES =>
          opcode  <= SAMPLES;
          odata   <= idata_r.q & idata_r.i;
          som     <= samples_som;
          ovalid  <= '1';
          eom     <= message_sizer_eom;
          oeof    <= '0';
          give    <= oready;
        when SAMPLES_EOM_ONLY =>
          opcode  <= SAMPLES;
          som     <= '0';
          ovalid  <= '0';
          eom     <= '1';
          oeof    <= '0';
          give    <= oready;
        when TIME_63_32 =>
          opcode    <= TIME_TIME;
          odata <= std_logic_vector(imetadata_r.time(63 downto 32));
          som    <= '0';
          ovalid <= '1';
          eom    <= '1';
          oeof   <= '0';
          give   <= oready;
        when TIME_31_0 =>
          opcode    <= TIME_TIME;
          odata <= std_logic_vector(imetadata_r.time(31 downto 0));
          som    <= '1';
          ovalid <= '1';
          eom    <= '0';
          oeof   <= '0';
          give   <= oready;
        when INTERVAL_63_32 =>
          opcode    <= INTERVAL;
          odata <= std_logic_vector(imetadata_r.samp_period(63 downto 32));
          som    <= '0';
          ovalid <= '1';
          eom    <= '1';
          oeof   <= '0';
          give   <= oready;
        when INTERVAL_31_0 =>
          opcode    <= INTERVAL;
          odata <= std_logic_vector(imetadata_r.samp_period(31 downto 0));
          som    <= '1';
          ovalid <= '1';
          eom    <= '0';
          oeof   <= '0';
          give   <= oready;
        when SYNC =>
          opcode    <= SYNC;
          som    <= '1';
          ovalid <= '0';
          eom    <= '1';
          oeof   <= '0';
          give   <= oready;
        when FLUSH =>
          opcode <= FLUSH;
          som    <= '1';
          ovalid <= '0';
          eom    <= '1';
          oeof   <= '0';
          give   <= oready;
        when EOF =>
          som    <= '0';
          ovalid <= '0';
          eom    <= '0';
          oeof   <= '1';
          give   <= oready;
        when others =>
          som    <= '0';
          ovalid <= '0';
          eom    <= '0';
          oeof   <= '0';
          give   <= '0';
      end case;
    end process ogen;

    oopcode <= opcode;

    message_sizer_rst <= orst or force_end_of_samples;
    message_sizer_give <= '1' when ((give = '1') and (opcode = SAMPLES)) else '0';

    message_sizer : wsi_message_sizer
      generic map(
        SIZE_BIT_WIDTH => SAMPLES_MESSAGE_SIZE_BIT_WIDTH)
      port map(
        clk                    => oclk,
        rst                    => message_sizer_rst,
        give                   => message_sizer_give,
        message_size_num_gives => to_unsigned(4092, 16),
        som                    => samples_som,
        eom                    => message_sizer_eom);

    ogive        <= give;
    osom         <= som;
    oeom         <= eom;
    obyte_enable <= (others => '1');

  end generate wsi_data_width_32;

end rtl;
