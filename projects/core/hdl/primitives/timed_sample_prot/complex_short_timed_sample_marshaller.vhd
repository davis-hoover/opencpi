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
library timed_sample_prot; use timed_sample_prot.complex_short_timed_sample.all;

entity complex_short_timed_sample_marshaller is
  generic(
    WSI_DATA_WIDTH    : positive := 32;
    WSI_MBYTEEN_WIDTH : positive);
  port(
    clk          : in  std_logic;
    rst          : in  std_logic;
    -- INPUT
    iprotocol    : in  timed_sample_prot.complex_short_timed_sample.protocol_t;
    ieof         : in  ocpi.types.Bool_t;
    irdy         : out std_logic;
    -- OUTPUT
    odata        : out std_logic_vector(WSI_DATA_WIDTH-1 downto 0);
    ovalid       : out ocpi.types.Bool_t;
    obyte_enable : out std_logic_vector(WSI_MBYTEEN_WIDTH-1 downto 0);
    ogive        : out ocpi.types.Bool_t;
    osom         : out ocpi.types.Bool_t;
    oeom         : out ocpi.types.Bool_t;
    oopcode      : out timed_sample_prot.complex_short_timed_sample.opcode_t;
    oeof         : out ocpi.types.Bool_t;
    oready       : in  ocpi.types.Bool_t);
end entity;
architecture rtl of complex_short_timed_sample_marshaller is

  -- output states - what we are offering to give
  type state_t is (SAMPLE, TIME_95_64, TIME_63_32, TIME_31_0, SAMPLE_INTERVAL_95_64, SAMPLE_INTERVAL_63_32, SAMPLE_INTERVAL_31_0, FLUSH, DISCONTINUITY, METADATA_95_64, METADATA_63_32, METADATA_31_0, EOF, IDLE);

  signal ivld        : bool_t; -- the inputs are valid (should be an input but is not)
  signal iprotocol_r : timed_sample_prot.complex_short_timed_sample.protocol_t :=
                       timed_sample_prot.complex_short_timed_sample.PROTOCOL_ZERO;
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
  signal opcode : timed_sample_prot.complex_short_timed_sample.opcode_t :=
                  timed_sample_prot.complex_short_timed_sample.SAMPLE;
begin   
    -- FIXME bring in the overall valid signal and remove qualifications in the complex_xxx fifo
    ivld <= iprotocol.sample_vld or
            iprotocol.time_vld or
            iprotocol.sample_interval_vld or
            iprotocol.flush or
            iprotocol.discontinuity or
            iprotocol.metadata_vld or
            ieof;
    -- We can accept input if the pipeline register is empty or we are emptying it in this cycle,
    -- but not if asserting EOF
    irdy_s  <= not ifull_r or (mux_end and oready and not ieof_r);
    irdy    <= irdy_s;
    -- We offer output if the pipelne register is full
    -- And if we are sending samples, we ALSO need input valid, to know whether we need EOM
    give    <= ifull_r and to_bool(state /= SAMPLE or ivld);
    valid   <= give and to_bool(state /= DISCONTINUITY and state /= FLUSH and state /= EOF); -- assert valid if not ZLM
    pipeline: process(clk)
    begin
      if rising_edge(clk) then
        if rst = '1' then
          iprotocol_r            <= timed_sample_prot.complex_short_timed_sample.PROTOCOL_ZERO;
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

    --To-Do: Especially with a 64 bit protocol. We should be able to parameterize the widths.
    --  wsi_data_width_32 : if(WSI_DATA_WIDTH = 32) generate

    mux_start <= ifirst_r;
    -- FIXME state should not be IDLE if the pipeline register is full
    -- sets the priority of multiplexing of output messages
    -- priority is: DISCONTINUITY, TIME, INTERVAL, FLUSH, SAMPLES, EOF
    mux_end   <= to_bool(state = SAMPLE or state = EOF or state = IDLE or
                         (state = DISCONTINUITY and iprotocol_r.time_vld = '0' and iprotocol_r.sample_interval_vld = '0' and
                          iprotocol_r.flush = '0' and iprotocol_r.metadata_vld = '0' and iprotocol_r.sample_vld = '0') or
                         (state = TIME_95_64 and iprotocol_r.sample_interval_vld = '0' and iprotocol_r.flush = '0' and
                          iprotocol_r.metadata_vld = '0' and iprotocol_r.sample_vld = '0') or
                         (state = SAMPLE_INTERVAL_95_64 and iprotocol_r.flush = '0' and iprotocol_r.metadata_vld = '0' and 
                          iprotocol_r.sample_vld = '0') or
                         (state = FLUSH and iprotocol_r.sample_vld = '0' and iprotocol_r.metadata_vld = '0') or
                         (state = METADATA_95_64 and iprotocol_r.sample_vld = '0')); 

    state <= IDLE when not ifull_r else
             DISCONTINUITY when iprotocol_r.discontinuity = '1' and mux_start else
             TIME_31_0 when iprotocol_r.time_vld = '1' and (mux_start or state_r = DISCONTINUITY) else
             TIME_63_32 when state_r = TIME_31_0 else
             TIME_95_64 when state_r = TIME_63_32 else
             SAMPLE_INTERVAL_31_0 when iprotocol_r.sample_interval_vld = '1' and
                                (mux_start or state_r = DISCONTINUITY or state_r = TIME_95_64) else
             SAMPLE_INTERVAL_63_32 when state_r = SAMPLE_INTERVAL_31_0 else
             SAMPLE_INTERVAL_95_64 when state_r = SAMPLE_INTERVAL_63_32 else 
             FLUSH when iprotocol_r.flush = '1' and
                        (mux_start or state_r = DISCONTINUITY or state_r = TIME_95_64 or
                         state_r = SAMPLE_INTERVAL_95_64) else
             SAMPLE when iprotocol_r.sample_vld = '1' and
                          (mux_start or state_r = DISCONTINUITY or state_r = TIME_95_64 or
                           state_r = SAMPLE_INTERVAL_95_64 or state_r = FLUSH) else
             METADATA_31_0 when iprotocol_r.metadata_vld = '1' and (mux_start or 
                                 state_r = DISCONTINUITY or state_r = TIME_95_64 or 
                                  state_r = SAMPLE_INTERVAL_95_64 or state_r = FLUSH or state_r = SAMPLE) else
             METADATA_63_32 when state_r = METADATA_31_0 else
             METADATA_95_64 when state_r = METADATA_63_32 else
             EOF when state_r = EOF or
                      (ieof_r and (mux_start or state_r = DISCONTINUITY or state_r = TIME_95_64 or
                                  state_r = SAMPLE_INTERVAL_95_64 or state_r = FLUSH or state_r = SAMPLE or
                                   state_r = METADATA_95_64)) else
             IDLE;    

    ogen : process(state, iprotocol_r, iprotocol)
    begin
      case state is
        when SAMPLE =>
          opcode  <= timed_sample_prot.complex_short_timed_sample.SAMPLE;
          odata   <= iprotocol_r.sample.data.imaginary & iprotocol_r.sample.data.real;
          som     <= '0'; -- inserteom deals with this
          -- force EOM if next thing is higher priority, but inserteom takes care of normal eom
          eom     <= iprotocol.discontinuity or iprotocol.time_vld or iprotocol.sample_interval_vld or iprotocol.flush;
        when TIME_31_0 =>
          opcode <= timed_sample_prot.complex_short_timed_sample.TIME_TIME; -- fraction is split into two sections. This is secion 1.
          odata  <= iprotocol_r.time.fraction(7 downto 0) & X"000000"; -- This is the 1st set of 32 bits.
          som    <= '1';
          eom    <= '0';
        when TIME_63_32 =>
          opcode <= timed_sample_prot.complex_short_timed_sample.TIME_TIME; --fraction is split into two sections. This is section 2.
          odata  <= iprotocol_r.time.fraction(39 downto 8); -- This is the 2nd set of 32 bits.
          som    <= '0';
          eom    <= '0';
        when TIME_95_64 =>
          opcode <= timed_sample_prot.complex_short_timed_sample.TIME_TIME; -- seconds passes through as the higher end of the data
          odata  <= iprotocol_r.time.seconds(31 downto 0); -- seconds is ulong, so it is 32 bits. This is the third set of 32 bits.
          som    <= '0';
          eom    <= '1';
        when SAMPLE_INTERVAL_31_0 =>
          opcode <= timed_sample_prot.complex_short_timed_sample.SAMPLE_INTERVAL; -- fraction is split into two sections. This is secion 1.
          odata  <= iprotocol_r.sample_interval.fraction(7 downto 0) & X"000000"; -- this is the 1st set of 32 bits.
          som    <= '1';
          eom    <= '0';
        when SAMPLE_INTERVAL_63_32 =>
          opcode <= timed_sample_prot.complex_short_timed_sample.SAMPLE_INTERVAL; --fraction is split into two sections. This is section 2.
          odata  <= iprotocol_r.sample_interval.fraction(39 downto 8); -- This is the 2nd set of 32 bits.
          som    <= '0';
          eom    <= '0';
        when SAMPLE_INTERVAL_95_64 =>
          opcode <= timed_sample_prot.complex_short_timed_sample.SAMPLE_INTERVAL; -- seconds passes through as its own set of data
          odata  <= iprotocol_r.sample_interval.seconds(31 downto 0); -- seconds is ulong, so it is 32 bits. This is the third set of 32 bits.
          som    <= '0';
          eom    <= '1';
        when DISCONTINUITY =>
          opcode <= timed_sample_prot.complex_short_timed_sample.DISCONTINUITY;
          odata  <= (others => '0');
          som    <= '1';
          eom    <= '1';
        when FLUSH =>
          opcode <= timed_sample_prot.complex_short_timed_sample.FLUSH;
          odata  <= (others => '0');
          som    <= '1';
          eom    <= '1';
        when METADATA_31_0 =>
          opcode <= timed_sample_prot.complex_short_timed_sample.METADATA;
          odata  <= iprotocol_r.metadata.value(31 downto 0); -- the id is ulong, so it is only 32 bits. This is the first set of 32 bits.
          som    <= '1';
          eom    <= '0';
        when METADATA_63_32 =>
          opcode <= timed_sample_prot.complex_short_timed_sample.METADATA;
          odata  <= iprotocol_r.metadata.value(63 downto 32); -- the value is ulonglong, and is the second set of 32 bits.
          som    <= '0';
          eom    <= '0';
        when METADATA_95_64 =>
          opcode <= timed_sample_prot.complex_short_timed_sample.METADATA;
          odata  <= iprotocol_r.metadata.id(31 downto 0); -- the value is ulonglong, this is the third set of 32 bits.
          som    <= '0';
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

  -- end generate wsi_data_width_64;

end rtl;
