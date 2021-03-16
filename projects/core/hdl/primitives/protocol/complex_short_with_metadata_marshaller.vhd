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
library ocpi; use ocpi.types.all;
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

  -- output states - what we are offering to give
  type state_t is (SAMPLES, TIME_63_32, TIME_31_0, INTERVAL_63_32, INTERVAL_31_0, FLUSH, SYNC, EOF, IDLE);

  signal ivld        : bool_t; -- the inputs are valid (should be an input but is not)
  signal iprotocol_r : protocol.complex_short_with_metadata.protocol_t :=
                       protocol.complex_short_with_metadata.PROTOCOL_ZERO;
  signal ieof_r      : bool_t; -- the EOF indication associated with the pipeline register
  signal irdy_s      : bool_t; -- are we ready to load the pipeline?
  signal ifull_r     : bool_t; -- is the pipeline register occupied?
  signal ifirst_r    : bool_t; -- are we doing the first thing indicated by what is in the pipeline reg?
  signal mux_start   : bool_t; -- a copy of ifirst_r;
  signal mux_end     : bool_t; -- we are offering the last thing indicated in the pipeline reg
  signal state       : state_t; -- what is being offered to the output port
  signal state_r     : state_t; -- what was last offered

  signal valid        : bool_t;
  signal give         : bool_t;
  signal som          : bool_t;
  signal eom          : bool_t;
  signal opcode : protocol.complex_short_with_metadata.opcode_t :=
                  protocol.complex_short_with_metadata.SAMPLES;
begin

  wsi_data_width_32 : if(WSI_DATA_WIDTH = 32) generate

    -- FIXME bring in the overall valid signal and remove qualifications in the complex_xxx fifo
    ivld <= iprotocol.samples_vld or
            iprotocol.time_vld or
            iprotocol.interval_vld or
            iprotocol.flush or
            iprotocol.sync or
            iprotocol.end_of_samples or
            ieof;
    -- We can accept input if the pipeline register is empty or we are emptying it in this cycle,
    -- but not if asserting EOF
    irdy_s  <= not ifull_r or (mux_end and oready and not ieof_r);
    irdy    <= irdy_s;
    -- We offer output if the pipelne register is full
    -- And if we are sending samples, we ALSO need input valid, to know whether we need EOM
    give    <= ifull_r and to_bool(state /= SAMPLES or ivld);
    valid   <= give and to_bool(state /= SYNC and state /= FLUSH and state /= EOF); -- assert valid if not ZLM
    pipeline: process(clk)
    begin
      if rising_edge(clk) then
        if rst = '1' then
          iprotocol_r            <= protocol.complex_short_with_metadata.PROTOCOL_ZERO;
          ieof_r                 <= '0';
          ifull_r                <= '0';
          ifirst_r               <= '0';
          state_r                <= IDLE;
        else
          if ifull_r and state = IDLE then
            report "No outputs when pipeline register is full" severity failure;
          end if;
          -- input side: load the pipeline if there is input and we can accept it
          if ivld = '1' and irdy_s = '1' then
            iprotocol_r <= iprotocol;
            ieof_r      <= ieof;
            ifull_r     <= '1';
            ifirst_r    <= '1';
          elsif give and oready then
            -- we're not loading but we are transferring
            ifirst_r    <= '0';
            if mux_end = '1' and not its(ieof_r) then
              ifull_r   <= '0';
            end if;
          end if;
          -- we are transferring so advance the state
          if give and oready then
            state_r <= state;
          end if;
        end if;
      end if;
    end process pipeline;

    mux_start <= ifirst_r;
    -- FIXME state should not be IDLE if the pipeline register is full
    -- sets the priority of multiplexing of output messages
    -- priority is: SYNC, TIME, INTERVAL, FLUSH, SAMPLES, EOF
    mux_end   <= to_bool(state = SAMPLES or state = EOF or state = IDLE or
                         (state = SYNC and iprotocol_r.time_vld = '0' and iprotocol_r.interval_vld = '0' and
                          iprotocol_r.flush = '0' and iprotocol_r.samples_vld = '0') or
                         (state = TIME_63_32 and iprotocol_r.interval_vld = '0' and iprotocol_r.flush = '0' and
                          iprotocol_r.samples_vld = '0') or
                         (state = INTERVAL_63_32 and iprotocol_r.flush = '0' and iprotocol_r.samples_vld = '0') or
                         (state = FLUSH and iprotocol_r.samples_vld = '0'));

    state <= IDLE when not ifull_r else
             SYNC when iprotocol_r.sync = '1' and mux_start else
             TIME_31_0 when iprotocol_r.time_vld = '1' and (mux_start or state_r = SYNC) else
             TIME_63_32 when state_r = TIME_31_0 else
             INTERVAL_31_0 when iprotocol_r.interval_vld = '1' and
                                (mux_start or state_r = SYNC or state_r = TIME_63_32) else
             INTERVAL_63_32 when state_r = INTERVAL_31_0 else
             FLUSH when iprotocol_r.flush = '1' and
                        (mux_start or state_r = SYNC or state_r = TIME_63_32 or
                         state_r = INTERVAL_63_32) else
             SAMPLES when iprotocol_r.samples_vld = '1' and
                          (mux_start or state_r = SYNC or state_r = TIME_63_32 or
                           state_r = INTERVAL_63_32 or state_r = FLUSH) else
             EOF when state_r = EOF or
                      (ieof_r and (mux_start or state_r = SYNC or state_r = TIME_63_32 or
                                  state_r = INTERVAL_63_32 or
                                   state_r = FLUSH or state_r = SAMPLES)) else
             IDLE;

    ogen : process(state, iprotocol_r, iprotocol)
    begin
      case state is
        when SAMPLES =>
          opcode  <= protocol.complex_short_with_metadata.SAMPLES;
          odata   <= iprotocol_r.samples.iq.q & iprotocol_r.samples.iq.i;
          som     <= '0'; -- inserteom deals with this
          -- force EOM if next thing is higher priority, but inserteom takes care of normal eom
          eom     <= iprotocol.sync or iprotocol.time_vld or iprotocol.interval_vld or iprotocol.flush;
        when TIME_63_32 =>
          opcode <= protocol.complex_short_with_metadata.TIME_TIME;
          odata  <= iprotocol_r.time.sec;
          som    <= '0';
          eom    <= '1';
        when TIME_31_0 =>
          opcode <= protocol.complex_short_with_metadata.TIME_TIME;
          odata  <= iprotocol_r.time.fract_sec;
          som    <= '1';
          eom    <= '0';
        when INTERVAL_63_32 =>
          opcode <= protocol.complex_short_with_metadata.INTERVAL;
          odata  <= iprotocol_r.interval.delta_time(63 downto 32);
          som    <= '0';
          eom    <= '1';
        when INTERVAL_31_0 =>
          opcode <= protocol.complex_short_with_metadata.INTERVAL;
          odata  <= iprotocol_r.interval.delta_time(31 downto 0);
          som    <= '1';
          eom    <= '0';
        when SYNC =>
          opcode <= protocol.complex_short_with_metadata.SYNC;
          odata  <= (others => '0');
          som    <= '1';
          eom    <= '1';
        when FLUSH =>
          opcode <= protocol.complex_short_with_metadata.FLUSH;
          odata  <= (others => '0');
          som    <= '1';
          eom    <= '1';
        when others => -- IDLE or EOF
          odata  <= (others => '0');
          som    <= '0';
          eom    <= '0';
      end case;
    end process ogen;

    oopcode      <= opcode;
    ovalid       <= valid;
    ogive        <= give;
    osom         <= som;
    oeom         <= eom;
    obyte_enable <= (others => '1');
    oeof         <= to_bool(state = EOF);

  end generate wsi_data_width_32;

end rtl;
