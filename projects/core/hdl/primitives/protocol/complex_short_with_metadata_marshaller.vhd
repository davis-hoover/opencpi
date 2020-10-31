-- This file is protected by Copyright. Please refer to the COPYRIGHT file
-- distributed with this source distribution.
--
-- This file is part of OpenCPI <http://www.opencpi.org>
--
-- OpenCPI is free software: you can redistribute it and/or modify it under the
-- terms of the GNU Lesser General Public License as published by the Free
-- Software Foundation, either version 3 of the License, or (at your option) any
-- later version.
--
-- OpenCPI is distributed in the hope that it will be useful, but WITHOUT ANY
-- WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
-- A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
-- details.
--
-- You should have received a copy of the GNU Lesser General Public License
-- along with this program. If not, see <http://www.gnu.org/licenses/>.
library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;
library ocpi;
library util;
library protocol; use protocol.complex_short_with_metadata.all;

entity complex_short_with_metadata_marshaller is
  generic(
    WSI_DATA_WIDTH    : positive := 16; -- 16 is default of codegen, but
                                        -- MUST USE 32 FOR NOW
    WSI_MBYTEEN_WIDTH : positive);
  port(
    clk          : in  std_logic;
    rst          : in  std_logic;
    -- INPUT
    iprotocol    : in  protocol.complex_short_with_metadata.protocol_t;
    ieof         : in  ocpi.types.Bool_t;
    irdy         : out std_logic;
    -- OUTPUT
    odata        : out std_logic_vector(WSI_DATA_WIDTH-1 downto 0);
    ovalid       : out ocpi.types.Bool_t;
    obyte_enable : out std_logic_vector(WSI_MBYTEEN_WIDTH-1 downto 0);
    ogive        : out ocpi.types.Bool_t;
    osom         : out ocpi.types.Bool_t;
    oeom         : out ocpi.types.Bool_t;
    oopcode      : out protocol.complex_short_with_metadata.opcode_t;
    oeof         : out ocpi.types.Bool_t;
    oready       : in  ocpi.types.Bool_t);
end entity;
architecture rtl of complex_short_with_metadata_marshaller is

  constant SAMPLES_MESSAGE_SIZE_BIT_WIDTH : positive := 16;
  type state_t is (SAMPLES, SAMPLES_EOM_ONLY, TIME_63_32, TIME_31_0, INTERVAL_63_32,
                   INTERVAL_31_0, FLUSH, SYNC, EOF, IDLE);

  signal ivld        : std_logic := '0';
  signal iprotocol_r : protocol.complex_short_with_metadata.protocol_t :=
                       protocol.complex_short_with_metadata.PROTOCOL_ZERO;
  signal ieof_r      : std_logic := '0';

  signal in_xfer           : std_logic := '0';
  signal in_xfer_r         : std_logic := '0';
  signal irdy_s            : std_logic := '0';
  signal mux_start         : std_logic := '0';
  signal mux_end           : std_logic := '0';

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

  signal opcode : protocol.complex_short_with_metadata.opcode_t :=
                  protocol.complex_short_with_metadata.SAMPLES;
  signal pending_samples_eom_gen_set : std_logic := '0';
  signal pending_samples_eom_gen_clr : std_logic := '0';
  signal pending_samples_eom_r       : std_logic := '0';

begin

  wsi_data_width_32 : if(WSI_DATA_WIDTH = 32) generate

    ivld <= iprotocol.samples_vld or
            iprotocol.time_vld or
            iprotocol.interval_vld or
            iprotocol.flush or
            iprotocol.sync or
            iprotocol.end_of_samples or
            ieof;
    in_xfer <= irdy_s and ivld;

    in_xfer_reg : process(clk)
    begin
      if(rising_edge(clk)) then
        if(rst = '1') then
          in_xfer_r <= '0';
        else
          in_xfer_r <= in_xfer;
        end if;
      end if;
    end process in_xfer_reg;

    in_in_pipeline : process(clk)
    begin
      if(rising_edge(clk)) then
        if(rst = '1') then
          iprotocol_r <= protocol.complex_short_with_metadata.PROTOCOL_ZERO;
          ieof_r      <= '0';
        elsif(in_xfer = '1') then
          iprotocol_r <= iprotocol;
          ieof_r      <= ieof;
        end if;
      end if;
    end process in_in_pipeline;

    in_out_pipeline : process(clk)
    begin
      if(rising_edge(clk)) then
        if(rst = '1') then
          irdy_s <= '0';
        else
          if((state = IDLE) and (mux_end = '1')) then
            --irdy_s <= (not ivld) and oready;
            irdy_s <= oready;
          else
            irdy_s <= '0';
          end if;
        end if;
      end if;
    end process in_out_pipeline;

    irdy <= irdy_s;

    regs : process(clk)
    begin
      if(rising_edge(clk)) then
        if(rst = '1') then
          state_r                <= IDLE;
          force_end_of_samples_r <= '0';
        elsif(oready = '1') then
          state_r                <= state;
          force_end_of_samples_r <= force_end_of_samples;
        end if;
      end if;
    end process regs;

    pending_samples_eom_gen_set <= '1' when (give = '1') and (som = '1') and
        (opcode = protocol.complex_short_with_metadata.SAMPLES) else '0';
    pending_samples_eom_gen_clr <= '1' when (give = '1') and (eom = '1') and
        (opcode = protocol.complex_short_with_metadata.SAMPLES) else '0';

    pending_samples_eom_gen : util.util.set_clr
      port map(clk => clk,
               rst => rst,
               set => pending_samples_eom_gen_set,
               clr => pending_samples_eom_gen_clr,
               q   => open,
               q_r => pending_samples_eom_r);

    mux_start <= in_xfer_r;
    mux_end   <= '1' when (state_r = IDLE) and (in_xfer= '0') and
                 (in_xfer_r = '0') else '0';

    -- sets the priority of multiplexing of output messages
    -- EOF, SYNC, TIME, INTERVAL, FLUSH, SAMPLES
    mux : process(oready, iprotocol_r, mux_start, state_r, pending_samples_eom_r)
    begin
      if(oready = '1') then
        if((ieof_r = '1') and (
            (mux_start = '1') or
            (state_r = SAMPLES_EOM_ONLY))) then
          if(pending_samples_eom_r = '1') then
            state <= SAMPLES_EOM_ONLY;
          else
            state <= EOF;
          end if;
          force_end_of_samples <= pending_samples_eom_r;
        elsif((iprotocol_r.sync = '1') and (
            (mux_start = '1') or
            (state_r = SAMPLES_EOM_ONLY) or
            (state_r = EOF))) then
          if(pending_samples_eom_r = '1') then
            state <= SAMPLES_EOM_ONLY;
          else
            state <= SYNC;
          end if;
          force_end_of_samples <= pending_samples_eom_r;
        elsif((iprotocol_r.time_vld = '1') and (
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
        elsif((iprotocol_r.interval_vld = '1') and (
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
        elsif((iprotocol_r.flush = '1') and (
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
        elsif((iprotocol_r.samples_vld = '1') and (
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

    ogen : process(state, iprotocol_r, samples_som, samples_eom, oready)
    begin
      case state is
        when SAMPLES =>
          opcode  <= protocol.complex_short_with_metadata.SAMPLES;
          odata   <= iprotocol_r.samples.iq.q & iprotocol_r.samples.iq.i;
          som     <= samples_som;
          ovalid  <= '1';
          eom     <= message_sizer_eom;
          oeof    <= '0';
          give    <= oready;
        when SAMPLES_EOM_ONLY =>
          opcode  <= protocol.complex_short_with_metadata.SAMPLES;
          odata   <= (others => '0');
          som     <= '0';
          ovalid  <= '0';
          eom     <= '1';
          oeof    <= '0';
          give    <= oready;
        when TIME_63_32 =>
          opcode <= protocol.complex_short_with_metadata.TIME_TIME;
          odata  <= iprotocol_r.time.sec;
          som    <= '0';
          ovalid <= '1';
          eom    <= '1';
          oeof   <= '0';
          give   <= oready;
        when TIME_31_0 =>
          opcode <= protocol.complex_short_with_metadata.TIME_TIME;
          odata  <= iprotocol_r.time.fract_sec;
          som    <= '1';
          ovalid <= '1';
          eom    <= '0';
          oeof   <= '0';
          give   <= oready;
        when INTERVAL_63_32 =>
          opcode <= protocol.complex_short_with_metadata.INTERVAL;
          odata  <= iprotocol_r.interval.delta_time(63 downto 32);
          som    <= '0';
          ovalid <= '1';
          eom    <= '1';
          oeof   <= '0';
          give   <= oready;
        when INTERVAL_31_0 =>
          opcode <= protocol.complex_short_with_metadata.INTERVAL;
          odata  <= iprotocol_r.interval.delta_time(31 downto 0);
          som    <= '1';
          ovalid <= '1';
          eom    <= '0';
          oeof   <= '0';
          give   <= oready;
        when SYNC =>
          opcode <= protocol.complex_short_with_metadata.SYNC;
          odata   <= (others => '0');
          som    <= '1';
          ovalid <= '0';
          eom    <= '1';
          oeof   <= '0';
          give   <= oready;
        when FLUSH =>
          opcode <= protocol.complex_short_with_metadata.FLUSH;
          odata   <= (others => '0');
          som    <= '1';
          ovalid <= '0';
          eom    <= '1';
          oeof   <= '0';
          give   <= oready;
        when EOF =>
          odata   <= (others => '0');
          som    <= '0';
          ovalid <= '0';
          eom    <= '0';
          oeof   <= '1';
          give   <= oready;
        when IDLE =>
          odata  <= (others => '0');
          som    <= '0';
          ovalid <= '0';
          eom    <= message_sizer_eom;
          oeof   <= '0';
          give   <= oready and message_sizer_eom;
        when others =>
          odata   <= (others => '0');
          som    <= '0';
          ovalid <= '0';
          eom    <= '0';
          oeof   <= '0';
          give   <= '0';
      end case;
    end process ogen;

    oopcode <= opcode;

    message_sizer_rst <= rst or force_end_of_samples;
    message_sizer_give <= '1' when ((give = '1') and (opcode = SAMPLES)) else '0';

    -- TODO / FIXME - include mechanism for assessment of port buffer size
    message_sizer : protocol.protocol.message_sizer
      generic map(
        SIZE_BIT_WIDTH => SAMPLES_MESSAGE_SIZE_BIT_WIDTH)
      port map(
        clk                    => clk,
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
