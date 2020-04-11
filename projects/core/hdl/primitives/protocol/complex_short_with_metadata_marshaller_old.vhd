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

-- see README

library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;
library ocpi;
library protocol; use protocol.complex_short_with_metadata.all;

entity complex_short_with_metadata_marshaller_old is
  generic(
    OUT_PORT_MBYTEEN_WIDTH : positive);
  port(
    clk          : in  std_logic;
    rst          : in  std_logic;
    -- INPUT
    iprotocol    : in  protocol.complex_short_with_metadata.protocol_t;
    ieof         : in  ocpi.types.Bool_t;
    irdy         : out std_logic;
    -- OUTPUT
    odata        : out std_logic_vector(31 downto 0);
    ovalid       : out ocpi.types.Bool_t;
    obyte_enable : out std_logic_vector(OUT_PORT_MBYTEEN_WIDTH-1 downto 0);
    ogive        : out ocpi.types.Bool_t;
    osom         : out ocpi.types.Bool_t;
    oeom         : out ocpi.types.Bool_t;
    oopcode      : out protocol.complex_short_with_metadata.opcode_t;
    oeof         : out ocpi.types.Bool_t;
    oready       : in  ocpi.types.Bool_t);
end entity;
architecture rtl of complex_short_with_metadata_marshaller_old is

  constant SAMPLES_MESSAGE_SIZE_BIT_WIDTH : positive := 16;
  type state_t is (SAMPLES, TIME_63_32, TIME_31_0, INTERVAL_63_32,
                   INTERVAL_31_0, FLUSH, SYNC, EOF, IDLE);

  signal iprotocol_r  : protocol.complex_short_with_metadata.protocol_t :=
                        protocol.complex_short_with_metadata.PROTOCOL_ZERO;
  signal iprotocol_r2 : protocol.complex_short_with_metadata.protocol_t :=
                        protocol.complex_short_with_metadata.PROTOCOL_ZERO;
  signal ieof_r       : std_logic := '0';
  signal ieof_r2      : std_logic := '0';
  -- needed to avoid bug in opt stage for Vivado zynq 7 series build:
  -- ERROR: [DRC MDRV-1] Multiple Driver Nets:
  signal iprotocol_r2_samples_vld : std_logic := '0';
  signal iprotocol_r2_sync        : std_logic := '0';

  signal ivld    : std_logic := '0';
  signal ivld_r  : std_logic := '0';
  signal ivld_r2 : std_logic := '0';

  signal irdy_s : std_logic := '0';

  signal state        : state_t := IDLE;
  signal state_r      : state_t := IDLE;

  signal samples_eom  : std_logic := '0';
  signal give         : std_logic := '0';
  signal som          : std_logic := '0';
  signal eom          : std_logic := '0';
  signal eof_s        : std_logic := '0';

  signal message_sizer_rst      : std_logic := '0';
  signal message_sizer_give     : std_logic := '0';
  signal message_sizer_som      : std_logic := '0';
  signal message_sizer_eom      : std_logic := '0';
  signal force_end_of_samples   : std_logic := '0';
  signal force_end_of_samples_r : std_logic := '0';

  signal opcode : protocol.complex_short_with_metadata.opcode_t :=
                  protocol.complex_short_with_metadata.SAMPLES;
  signal pending_samples_eom : std_logic := '0';

begin

  ivld <= iprotocol.samples_vld or
          iprotocol.time_vld or
          iprotocol.interval_vld or
          iprotocol.flush or
          iprotocol.sync or
          iprotocol.end_of_samples or
          ieof;

  pipeline : process(clk)
  begin
    if(rising_edge(clk)) then
      if(rst = '1') then
        iprotocol_r  <= protocol.complex_short_with_metadata.PROTOCOL_ZERO;
        iprotocol_r2 <= protocol.complex_short_with_metadata.PROTOCOL_ZERO;
        ivld_r       <= '0';
        irdy         <= '0';
        ieof_r       <= '0';
        ieof_r2      <= '0';
        -- needed to avoid bug in opt stage for Vivado zynq 7 series build:
        -- ERROR: [DRC MDRV-1] Multiple Driver Nets:
        iprotocol_r2_samples_vld  <= '0';
        iprotocol_r2_sync         <= '0';
      else
        iprotocol_r  <= iprotocol;
        iprotocol_r2 <= iprotocol_r;
        ivld_r       <= ivld;
        irdy         <= irdy_s;
        ieof_r       <= ieof;
        ieof_r2      <= ieof_r;
        -- needed to avoid bug in opt stage for Vivado zynq 7 series build:
        -- ERROR: [DRC MDRV-1] Multiple Driver Nets:
        iprotocol_r2_samples_vld <= iprotocol_r.samples_vld;
        iprotocol_r2_sync        <= iprotocol_r.sync;
      end if;
    end if;
  end process pipeline;

  iprotocol_r2_gen : process(clk)
  begin
    if(rising_edge(clk)) then
      if(rst = '1') then
        iprotocol_r2 <= protocol.complex_short_with_metadata.PROTOCOL_ZERO;
      elsif(ivld_r = '1') then
        iprotocol_r2 <= iprotocol_r;
      end if;
    end if;
  end process iprotocol_r2_gen;

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
      elsif((give = '1') and
          (opcode = protocol.complex_short_with_metadata.SAMPLES)) then
        if(eom = '1') then
          pending_samples_eom <= '0';
        elsif(som = '1') then
          pending_samples_eom <= '1';
        end if;
      end if;
    end if;
  end process pending_samples_eom_gen;

  -- sets the priority of multiplexing of output messages
  imetadata_demux : process(ivld_r, ivld_r2, oready, iprotocol_r, iprotocol_r2, state_r)
  begin
    if(oready = '1') then
      if(state_r = TIME_31_0) and (ivld_r2 = '1') then
        irdy_s <= (not iprotocol_r2_sync) and
                  (not iprotocol_r2_samples_vld) and
                  (not iprotocol_r2.interval_vld) and
                  (not iprotocol_r2.flush) and
                  (not ieof_r2);
        state <= TIME_63_32;
        force_end_of_samples <= '0';
      elsif(state_r = INTERVAL_31_0) and (ivld_r2 = '1') then
        irdy_s <= (not iprotocol_r2_sync) and
                  (not iprotocol_r2_samples_vld) and
                  (not iprotocol_r2.time_vld) and
                  (not iprotocol_r2.flush) and
                  (not ieof_r2);
        state <= INTERVAL_63_32;
        force_end_of_samples <= '0';
      elsif((iprotocol_r.sync = '1') or (force_end_of_samples_r = '1'))
          and (ivld_r = '1') then
        irdy_s <= (not iprotocol_r.samples_vld) and
                  (not iprotocol_r.time_vld) and
                  (not iprotocol_r.interval_vld) and
                  (not iprotocol_r.flush) and
                  (not ieof_r);
        if(pending_samples_eom = '1') then
          state <= SAMPLES;
          force_end_of_samples <= '1';
        else
          state <= SYNC;
          force_end_of_samples <= '0';
        end if;
      elsif(iprotocol_r.time_vld = '1') and (ivld_r = '1') then
        irdy_s <= '0';
        state <= TIME_31_0;
        force_end_of_samples <= '0';
      elsif(iprotocol_r.samples_vld = '1') and (ivld_r = '1') then
        irdy_s <= (not iprotocol_r.sync) and
                  (not iprotocol_r.time_vld) and
                  (not iprotocol_r.interval_vld) and
                  (not iprotocol_r.flush) and
                  (not ieof_r);
        state <= SAMPLES;
        force_end_of_samples <= '0';
      elsif(iprotocol_r.interval_vld = '1') and (ivld_r = '1') then
        irdy_s <= '0';
        state <= INTERVAL_31_0;
        force_end_of_samples <= '0';
      elsif(iprotocol_r.flush = '1') and (ivld_r = '1') then
        irdy_s <= (not ieof_r);
        state <= FLUSH;
        force_end_of_samples <= '0';
      elsif(ieof_r = '1') and (ivld_r = '1') then
        irdy_s <= '0';
        state <= EOF;
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

  ogen : process(state, iprotocol_r, message_sizer_som, message_sizer_eom,
                 force_end_of_samples, oready, iprotocol_r, iprotocol_r2)
  begin
    case state is
      when SAMPLES =>
        opcode  <= protocol.complex_short_with_metadata.SAMPLES;
        odata   <= iprotocol_r.samples.iq.q & iprotocol_r.samples.iq.i;
        som     <= message_sizer_som;

        -- handles forced EOM due to data_vld=1 error_samp_drop=1
        ovalid  <= not force_end_of_samples;

        eom     <= message_sizer_eom or force_end_of_samples;
        give    <= oready;
        eof_s   <= '0';
      when TIME_63_32 =>
        opcode <= protocol.complex_short_with_metadata.TIME_TIME;
        odata  <= iprotocol_r2.time.sec;
        som    <= '0';
        ovalid <= '1';
        eom    <= '1';
        give   <= oready;
        eof_s  <= '0';
      when TIME_31_0 =>
        opcode <= protocol.complex_short_with_metadata.TIME_TIME;
        odata  <= iprotocol_r.time.fract_sec;
        som    <= '1';
        ovalid <= '1';
        eom    <= '0';
        give   <= oready;
        eof_s  <= '0';
      when INTERVAL_63_32 =>
        opcode <= protocol.complex_short_with_metadata.INTERVAL;
        odata  <= iprotocol_r2.interval.delta_time(63 downto 32);
        som    <= '0';
        ovalid <= '1';
        eom    <= '1';
        give   <= oready;
        eof_s  <= '0';
      when INTERVAL_31_0 =>
        opcode <= protocol.complex_short_with_metadata.INTERVAL;
        odata  <= iprotocol_r.interval.delta_time(31 downto 0);
        som    <= '1';
        ovalid <= '1';
        eom    <= '0';
        give   <= oready;
        eof_s  <= '0';
      when SYNC =>
        opcode <= protocol.complex_short_with_metadata.SYNC;
        som    <= '1';
        ovalid <= '0';
        eom    <= '1';
        give   <= oready;
        eof_s  <= '0';
      when FLUSH =>
        opcode <= protocol.complex_short_with_metadata.FLUSH;
        som    <= '1';
        ovalid <= '0';
        eom    <= '1';
        give   <= oready;
        eof_s  <= '0';
      when EOF =>
        som    <= '0';
        ovalid <= '0';
        eom    <= '0';
        give   <= '0';
        eof_s  <= '1';
      when others =>
        som    <= '0';
        ovalid <= '0';
        eom    <= '0';
        give   <= '0';
        eof_s  <= '0';
    end case;
  end process ogen;

  oopcode <= opcode;

  message_sizer_rst <= rst or force_end_of_samples;
  message_sizer_give <= '1' when ((give = '1') and
      (opcode = protocol.complex_short_with_metadata.SAMPLES)) else '0';

  message_sizer : protocol.protocol.message_sizer
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
  oeof         <= eof_s;
  obyte_enable <= (others => '1');

end rtl;
