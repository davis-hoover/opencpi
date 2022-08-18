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

library ieee; use ieee.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi; use ocpi.types.all;
library sdp; use sdp.sdp.all;
library dgrdma; use dgrdma.dgrdma_util.all;

entity dgrdma_frame_parser is
  generic(
    SDP_WIDTH : natural;
    MAX_RX_MTU : natural := 16384;
    MAX_TXNS_IN_FLIGHT : natural := 32;
    ACK_TRACKER_BITFIELD_WIDTH : natural;
    ACK_TRACKER_MAX_ACK_COUNT  : natural range 1 to 255
  );
  port(
    clk : in std_logic;
    reset : in std_logic;

    -- configuration (via platform worker properties)
    ack_wait : in unsigned(31 downto 0);
    max_acks_outstanding : in unsigned(7 downto 0);

    -- ack request
    tx_ackstart : out unsigned(15 downto 0);
    tx_ackcount : out integer range 0 to ACK_TRACKER_MAX_ACK_COUNT;
    tx_ack_req : out std_logic;
    tx_ack_req_urg : out std_logic;
    tx_ack_sent : in std_logic;
    tx_ackcount_sent : in integer range 0 to ACK_TRACKER_MAX_ACK_COUNT;

    -- Ack Tracker Debug
    ack_tracker_rej_ack             : out std_logic;
    ack_tracker_bitfield            : out std_logic_vector(31 downto 0);
    ack_tracker_base_seqno          : out std_logic_vector(15 downto 0);
    ack_tracker_rej_seqno           : out std_logic_vector(15 downto 0);
    ack_tracker_total_acks_sent     : out std_logic_vector(31 downto 0);
    ack_tracker_tx_acks_sent        : out std_logic_vector(31 downto 0);
    ack_tracker_pkts_enqueued       : out std_logic_vector(31 downto 0);
    ack_tracker_reject_out_of_range : out std_logic_vector(31 downto 0);
    ack_tracker_reject_already_set  : out std_logic_vector(31 downto 0);
    ack_tracker_accepted_by_peek    : out std_logic_vector(31 downto 0);
    ack_tracker_high_watermark      : out std_logic_vector(15 downto 0);
    frame_parser_reject             : out std_logic_vector(31 downto 0);

    -- connection to SDP target
    sdp_targ_count : out count_t;
    sdp_targ_op : out op_t;
    sdp_targ_xid : out xid_t;
    sdp_targ_lead : out unsigned(end_bytes_width-1 downto 0);
    sdp_targ_trail : out unsigned(end_bytes_width-1 downto 0);
    sdp_targ_node : out id_t;
    sdp_targ_addr : out addr_t;
    sdp_targ_extaddr : out extaddr_t;
    sdp_targ_eop : out bool_t;
    sdp_targ_valid : out bool_t;
    sdp_targ_ready : in bool_t;

    sdp_targ_data : out dword_array_t(0 to SDP_WIDTH-1);

    -- DGRDMA frame (64-bit bus). Ethernet header has been stripped off, first 6
    -- bytes of first beat contain the source MAC address (currently ignored).
    -- We assume the bus is in 'little-endian' byte order - i.e., the earliest byte to arrive
    -- from the MAC is s_axis_tdata(7 downto 0) and the latest is (63 downto 56)
    s_axis_tdata : in std_logic_vector(data_width_for_sdp(SDP_WIDTH) - 1 downto 0);
    s_axis_tkeep : in std_logic_vector(keep_width_for_sdp(SDP_WIDTH) - 1 downto 0);
    s_axis_tvalid : in std_logic;
    s_axis_tready : out std_logic;
    s_axis_tlast : in std_logic;

    -- to control plane
    flag_addr : out std_logic_vector(23 downto 0);
    flag_data : out std_logic_vector(31 downto 0);
    flag_valid : out std_logic;
    flag_take : in std_logic
  );
end dgrdma_frame_parser;

architecture rtl of dgrdma_frame_parser is
  type rx_state_t is (
    RX_IDLE,
    RX_FRAME_HDR,
    RX_WAIT_ACK_TRACKER,
    RX_MSG_HDR,
    RX_PARSE_MSG_HDR,
    RX_SHORT_MSG,
    RX_MSG_PAYLOAD,
    RX_MSG_PAYLOAD_LAST_ALIGN,
    RX_MSG_PAYLOAD_LAST,
    RX_FLAG,
    RX_INTER_MSG_PADDING,
    RX_WAIT_TLAST,
    RX_GEN_ACK,
    RX_ERROR_WAIT_TLAST
  );

  constant DATA_WIDTH : natural := data_width_for_sdp(SDP_WIDTH);

  signal rx_state : rx_state_t;
  function max_header_beats return natural is
  begin
    case SDP_WIDTH is
      when 1 => return 6;
      when 2 => return 3;
      when 4 => return 2;
      when others => report "Unsupported SDP width!" severity error;
    end case;
  end max_header_beats;
  signal header_beat : natural range 0 to max_header_beats - 1;

  -- only relevant for SDP_WIDTH = 1
  signal frame_beat_lsb : std_logic;

  -- only relevant for SDP_WIDTH = 4
  signal msg_hdr_alignment : natural range 0 to 1;
  signal msg_start_alignment : natural range 0 to 1;
  signal msg_end_alignment : natural range 0 to 1;
  signal prev_tdata : std_logic_vector(DATA_WIDTH - 1 downto 0);

  signal tlast_hold : boolean;  -- remember if we have seen a TLAST while we are dealing with flag write

  -- pipelined data and ready/valid signals
  signal sdp_targ_data_align : std_logic_vector(DATA_WIDTH - 1 downto 0);
  signal sdp_targ_valid_r : std_logic;
  signal payload_ready : std_logic;
  signal s_axis_tready_r : std_logic;

  -- frame header
  signal rx_frame_hdr_reg : std_logic_vector(127 downto 0);
  signal rx_src_id : std_logic_vector(15 downto 0);
  signal rx_dst_id : std_logic_vector(15 downto 0);
  signal rx_frameseq : unsigned(15 downto 0);
  signal rx_ackstart : unsigned(15 downto 0);
  signal rx_ackcount : unsigned(7 downto 0);
  signal rx_hasmsg : boolean;

  -- message header
  signal rx_msg_hdr_reg : std_logic_vector(191 downto 0);
  signal rx_txn_id : std_logic_vector(31 downto 0);
  signal rx_msgs_in_txn : unsigned(15 downto 0);
  signal rx_flag_addr : std_logic_vector(23 downto 0);
  signal rx_flag_data : std_logic_vector(31 downto 0);
  signal rx_msg_seq : unsigned(15 downto 0);
  signal rx_data_addr : unsigned(31 downto 0);
  signal rx_data_len : unsigned(15 downto 0);
  signal rx_type : std_logic_vector(7 downto 0);
  signal rx_nextmsg : boolean;

  -- count 64-bit data beats
  subtype data_beat_ctr_t is natural range 0 to (MAX_RX_MTU / (SDP_WIDTH * 4)) - 1;
  signal msg_data_beats : data_beat_ctr_t;
  signal rx_data_beats : data_beat_ctr_t;

  -- ack tracker
  signal ack_tracker_rx_valid         : std_logic;
  signal ack_tracker_rx_peek          : std_logic;
  signal ack_tracker_rx_reject        : std_logic;
  signal ack_tracker_rx_reject_valid  : std_logic;
  signal ack_tracker_rx_reject_ready  : std_logic;
  signal ack_tracker_tx_ackcount      : integer range 0 to ACK_TRACKER_MAX_ACK_COUNT;
  signal ack_tracker_tx_ack_req       : std_logic;
  signal ack_tracker_debug_bitfield   : std_logic_vector(31 downto 0);
  signal ack_tracker_debug_base_seqno : std_logic_vector(15 downto 0);

  signal ack_tracker_rej_ack_r        : std_logic;

  -- ack tx handling
  signal ack_wait_ctr : natural;

  -- to/from txn_record
  signal rx_txn_valid : std_logic;
  signal rx_txn_ready : std_logic;

  -- debug
  signal rx_state_i : natural;
  signal debug_reject_count : unsigned(31 downto 0);
begin

  rx_state_i          <= rx_state_t'pos(rx_state);
  frame_parser_reject <= std_logic_vector(debug_reject_count);

  -- Generate SDP header. trail and count are set by the receive state machine
  -- as they need to be calculated from rx_data_addr and rx_data_len which are
  -- available on the last beat of the header.
  -- Note that the SDP header must remain stable for the entire transfer.
  sdp_targ_op      <= write_e;          -- DG-RDMA only supports writes
  sdp_targ_xid     <= (others => '0');  -- transaction ID not used for writes
  sdp_targ_extaddr <= (others => '0');
  sdp_targ_node    <= rx_data_addr(29 downto 26);
  sdp_targ_addr    <= rx_data_addr(sdp_targ_addr'left + 2 downto 2); -- word address
  sdp_targ_lead    <= rx_data_addr(1 downto 0);

  -- Unpack pipelined data into SDP words and drive valid/ready signals
  sdp_targ_data    <= unpack_sdp_data(sdp_targ_data_align);
  sdp_targ_valid   <= sdp_targ_valid_r;
  payload_ready <= sdp_targ_ready or not(sdp_targ_valid_r);

  s_axis_tready <= s_axis_tready_r;
  with rx_state select s_axis_tready_r <=
    '0'            when RX_IDLE | RX_WAIT_ACK_TRACKER | RX_PARSE_MSG_HDR | RX_SHORT_MSG | RX_MSG_PAYLOAD_LAST_ALIGN | RX_MSG_PAYLOAD_LAST | RX_FLAG | RX_GEN_ACK,
    payload_ready  when RX_MSG_PAYLOAD,
    '1'            when RX_FRAME_HDR | RX_MSG_HDR | RX_INTER_MSG_PADDING | RX_WAIT_TLAST | RX_ERROR_WAIT_TLAST;

  -- set SDP EOP on last beat of transfer
  sdp_targ_eop     <= '1' when rx_state = RX_MSG_PAYLOAD_LAST else '0';

  -- Decode frame header (first 48 bits are reserved to align rest of frame on a 64-bit boundary)
  rx_dst_id   <=          rx_frame_hdr_reg( 63 downto  48);
  rx_src_id   <=          rx_frame_hdr_reg( 79 downto  64);
  rx_frameseq <= unsigned(rx_frame_hdr_reg( 95 downto  80));
  rx_ackstart <= unsigned(rx_frame_hdr_reg(111 downto  96));
  rx_ackcount <= unsigned(rx_frame_hdr_reg(119 downto 112));
  rx_hasmsg   <=         (rx_frame_hdr_reg(120) = '1');

  -- Decode message header
  rx_txn_id      <=          rx_msg_hdr_reg( 31 downto   0);
  rx_flag_addr   <=          rx_msg_hdr_reg( 57 downto  34); -- CP address is 24-bit word address, address in packet is 32-bit byte address
                                                             -- TODO: should it be treated as an error if rx_flag_addr(31 downto 26) /= 0?
  rx_flag_data   <=          rx_msg_hdr_reg( 95 downto  64);
  rx_msgs_in_txn <= unsigned(rx_msg_hdr_reg(111 downto  96));
  rx_msg_seq     <= unsigned(rx_msg_hdr_reg(127 downto 112));
  rx_data_addr   <= unsigned(rx_msg_hdr_reg(159 downto 128));
  rx_data_len    <= unsigned(rx_msg_hdr_reg(175 downto 160));
  rx_type        <=          rx_msg_hdr_reg(183 downto 176);
  rx_nextmsg     <=         (rx_msg_hdr_reg(184) = '1');

  -- RECEIVE STATE MACHINE

  rx_proc : process(clk)

    variable short_message : boolean;
    variable last_msg_header_beat : boolean;

    -- reset frame state and SDP outputs
    procedure reset_state is
    begin
      tlast_hold <= false;

      rx_frame_hdr_reg <= (others => '0');
      rx_msg_hdr_reg <= (others => '0');

      msg_data_beats <= 0;
      rx_data_beats <= 0;

      ack_tracker_rx_valid        <= '0';
      ack_tracker_rx_peek         <= '0';
      ack_tracker_rx_reject_ready <= '0';

      sdp_targ_valid_r <= '0';
      sdp_targ_trail <= (others => '0');
      sdp_targ_count <= (others => '0');
      sdp_targ_data_align <= (others => '0');

      header_beat <= 0;
      frame_beat_lsb <= '0';
      msg_hdr_alignment <= 0;
      msg_start_alignment <= 0;
      msg_end_alignment <= 0;
    end procedure reset_state;

    -- calculate SDP header count and trail, and expected number of 64-bit data beats in message
    procedure calculate_sdp_counts(start_addr : unsigned(rx_data_addr'range); len : unsigned(rx_data_len'range)) is
      variable end_addr : unsigned(start_addr'range);
      variable word_count : unsigned(sdp_targ_count'range);
      variable end_packet_alignment : natural range 0 to 3;  -- only used when SDP_WIDTH = 4
    begin
      -- end_addr is one past last byte
      end_addr := start_addr + len;
      -- number of DWORDs in transfer, adjusted if end address is not aligned to a DWORD boundary
      if end_addr(1 downto 0) = "00" then
        sdp_targ_trail <= unsigned'("00");
        word_count := resize(end_addr(start_addr'left downto 2) - start_addr(start_addr'left downto 2), word_count'length);
      else
        sdp_targ_trail <= unsigned'("00") - end_addr(1 downto 0);
        word_count := resize(end_addr(start_addr'left downto 2) - start_addr(start_addr'left downto 2), word_count'length) + 1;
      end if;

      -- NOTE: len is required to be > 0, which means word_count is also > 0, so these results is always non-negative
      -- number of DWORDS in the transfer minus one
      sdp_targ_count <= word_count - 1;
      short_message := false;  -- default
      -- number of data beats in transfer minus one
      if SDP_WIDTH /= 4 then
        msg_data_beats <= to_integer((word_count - 1) / SDP_WIDTH);
      else
        -- 128-bit bus
        -- Set alignment of message start and end, and next message header
        if msg_hdr_alignment = 0 then
          msg_start_alignment <= 1;
          end_packet_alignment := to_integer(word_count + 1) mod 4;
        else
          msg_start_alignment <= 0;
          end_packet_alignment := to_integer(word_count + 3) mod 4;
        end if;
        case end_packet_alignment is
          when 0 | 1 =>
            msg_data_beats <= to_integer((word_count - 1) / SDP_WIDTH);
            msg_end_alignment <= 0;
            msg_hdr_alignment <= 1;
          when 2 | 3 =>
            if msg_hdr_alignment = 1 then  -- therefore msg_start_alignment = 0 after this cycle
              msg_data_beats <= to_integer((word_count - 1) / SDP_WIDTH);
            else  -- msg_start_alignment = 1 after this cycle
              if to_integer(word_count) < SDP_WIDTH then  -- short message (complete payload in last beat of header)
                msg_data_beats <= 0;
                short_message := true;
              else  -- normal message; calculate data beats given that first 2 DWORDS are in last beat of header
                msg_data_beats <= to_integer((word_count - 1) / SDP_WIDTH) - 1;
              end if;
            end if;
            msg_end_alignment <= 1;
            msg_hdr_alignment <= 0;
        end case;
      end if;
    end procedure calculate_sdp_counts;

  begin
    if rising_edge(clk) then
      if reset = '1' then
        reset_state;
        rx_state <= RX_IDLE;

        ack_tracker_rej_ack_r  <= '0';
        ack_tracker_bitfield   <= (others => '0');
        ack_tracker_base_seqno <= (others => '0');
        ack_tracker_rej_seqno  <= (others => '0');
        debug_reject_count     <= (others => '0');
      else
        -- Defaults for single-cycle strobes
        ack_tracker_rx_valid        <= '0';
        ack_tracker_rx_peek         <= '0';
        ack_tracker_rx_reject_ready <= '0';

        -- Save previous TDATA word (required for handling message alignment for SDP_WIDTH > 4)
        if s_axis_tvalid = '1' and s_axis_tready_r = '1' then
          prev_tdata <= s_axis_tdata;
          frame_beat_lsb <= not frame_beat_lsb;
        end if;

        -- Main receive state machine
        case rx_state is
          when RX_IDLE =>
            -- Reset all state variables and outputs and prepare to accept AXIS packet
            reset_state;
            rx_state <= RX_FRAME_HDR;
            ack_tracker_rx_reject_ready <= '1';

          when RX_FRAME_HDR =>
            if s_axis_tvalid = '1' then
              if s_axis_tlast = '1' then  -- ignore truncated frame
                -- Going to RX_IDLE here shouldn't mess up the ack tracking
                -- for any SDP width:
                -- Width  Rationale
                -- -----  ---------
                -- 1      cycle n  : rx_frameseq parsed and ack_tracker_rx_peek set high
                --        cycle n+1: truncated frame so next cycle in RX_IDLE.
                --        cycle n+2: in state RX_IDLE; ack_tracker responds to peek.
                --                   Not ready to continue.  We don't know if this was an
                --                   ack-only msg because tlast was asserted on the beat
                --                   where that would be parsed. so debug output shouldn't
                --                   be messed up either.
                -- 2/4    rx_frameseq is parsed in final cycle of this state
                --        so no opportuntiy to truncate after
                --        ack_tracker_rx_peek is asserted.  Instead go straight
                --        to RX_WAIT_ACK_TRACKER.
                -- Equally, this is purely an error case as ethernet payloads should be
                -- at least 48 bits.
                rx_state <= RX_IDLE;
              else
                -- save new word into frame header register
                rx_frame_hdr_reg((header_beat * s_axis_tdata'length) + s_axis_tdata'left downto header_beat * s_axis_tdata'length) <= s_axis_tdata;

                if (SDP_WIDTH = 1 and header_beat = 3) or (SDP_WIDTH = 2 and header_beat = 1) or (SDP_WIDTH = 4 and header_beat = 0) then
                  header_beat <= 0;
                  ack_tracker_rx_peek <= '1';
                  rx_state <= RX_WAIT_ACK_TRACKER;
                else
                  header_beat <= header_beat + 1;
                end if;
              end if;
            end if;

          when RX_WAIT_ACK_TRACKER =>
            -- Wait until the ack tracker responds.  If rx_frameseq is parsed
            -- on cycle n, the response arrives at cycle n+2.  Even if the sdp
            -- width is 1, we will arrive in this state in time to receive it.
            -- Abort if packet is rejected and set debug state for the first
            -- ack-only packet that is rejected.
            -- Continue if the packet is accepted.
            if ack_tracker_rx_reject_valid = '1' then
              ack_tracker_rx_reject_ready <= '1';
              if ack_tracker_rx_reject = '1' then
                rx_state <= RX_ERROR_WAIT_TLAST;
                if (not rx_hasmsg) and (ack_tracker_rej_ack_r = '0') then
                  -- Freeze the debug output on the first ack-only rejection
                  ack_tracker_rej_ack_r  <= '1';
                  ack_tracker_bitfield <= ack_tracker_debug_bitfield;
                  ack_tracker_base_seqno <= ack_tracker_debug_base_seqno;
                  ack_tracker_rej_seqno  <= std_logic_vector(rx_frameseq);
                end if;
              else
                if rx_hasmsg then
                  rx_state <= RX_MSG_HDR;
                else
                  -- ACK-only frame: updated received-ACK status
                  -- We won't send an ACK just for this frame, but it will be included with an ACK of real frames
                  rx_state <= RX_GEN_ACK;
                end if;
              end if;
            end if;

          when RX_MSG_HDR =>
            if s_axis_tvalid = '1' then
              last_msg_header_beat := false;

              if SDP_WIDTH /= 4 then
                rx_msg_hdr_reg((header_beat * s_axis_tdata'length) + s_axis_tdata'left downto header_beat * s_axis_tdata'length) <= s_axis_tdata;

                if (SDP_WIDTH = 1 and header_beat = 5) or (SDP_WIDTH = 2 and header_beat = 2) then
                  header_beat <= 0;
                  last_msg_header_beat := true;
                else
                  header_beat <= header_beat + 1;
                end if;

              else
                -- SDP_WIDTH = 4
                -- handle message alignment
                if msg_hdr_alignment = 0 then
                  case header_beat is
                    when 0 =>
                      rx_msg_hdr_reg(127 downto 0) <= s_axis_tdata;
                      header_beat <= 1;
                    when 1 =>
                      rx_msg_hdr_reg(191 downto 128) <= s_axis_tdata(63 downto 0);
                      header_beat <= 0;
                      last_msg_header_beat := true;
                  end case;
                else
                  -- First two words of header are previous AXI beat that has been partially processed
                  -- Rest of header is in this beat
                  rx_msg_hdr_reg <= s_axis_tdata & prev_tdata(127 downto 64);
                  last_msg_header_beat := true;
                end if;
              end if;

              -- If we have got the whole header, go ahead and parse it.
              if last_msg_header_beat then
                rx_state <= RX_PARSE_MSG_HDR;
                if s_axis_tlast = '1' then
                  -- A frame can end after the message header if all the payload is included in the last header beat
                  -- or it is a flag-only message with no payload: remember state of TLAST so that we return to IDLE
                  -- after completing processing.
                  tlast_hold <= true;
                end if;
              elsif s_axis_tlast = '1' then
                -- Truncated frame - immediately go to IDLE.
                rx_state <= RX_IDLE;
              end if;
            end if;

          when RX_PARSE_MSG_HDR =>
            if rx_msgs_in_txn = to_unsigned(0, rx_msgs_in_txn'length) then
              -- flag-only message
              rx_state <= RX_FLAG;
              if SDP_WIDTH = 4 then  -- no payload - next header has opposite alignment
                msg_hdr_alignment <= (msg_hdr_alignment + 1) mod 2;
              end if;
            else
              -- This is a real message
              -- Set address- and length-dependent fields in SDP header, which
              -- must remain stable for the entire transfer. This also sets
              -- msg_data_beats
              calculate_sdp_counts(rx_data_addr, rx_data_len);
              rx_data_beats <= 0;

              if short_message then
                -- If calculate_sdp_counts set short_message (only possible for SDP_WIDTH=4 and when this
                -- message data is misaligned), the entire message payload is included in the same beat as
                -- the end of the header
                rx_state <= RX_SHORT_MSG;
              elsif tlast_hold then
                -- Truncated frame - immediate go to IDLE
                rx_state <= RX_IDLE;
              elsif rx_data_len = 0 or rx_data_len > 16384 then
                -- Message length must be > 0 and <= 16kByte
                rx_state <= RX_ERROR_WAIT_TLAST;
              else
                rx_state <= RX_MSG_PAYLOAD;
              end if;
            end if;

          when RX_SHORT_MSG =>
            rx_state <= RX_MSG_PAYLOAD_LAST;
            sdp_targ_valid_r <= '1';
            sdp_targ_data_align((DATA_WIDTH / 2 ) - 1 downto 0) <= prev_tdata(DATA_WIDTH - 1 downto DATA_WIDTH / 2);
            sdp_targ_data_align(DATA_WIDTH - 1 downto DATA_WIDTH / 2) <= (others => '0');

          when RX_MSG_PAYLOAD =>
            if payload_ready = '1' then
              if SDP_WIDTH /= 4 or msg_start_alignment = 0 then
                sdp_targ_data_align <= s_axis_tdata;
              else
                -- SDP_WIDTH = 4 and message data starts in between data beats - so AXI data and SDP data are offset by 2 DWORDS
                sdp_targ_data_align((DATA_WIDTH / 2 ) - 1 downto 0) <= prev_tdata(DATA_WIDTH - 1 downto DATA_WIDTH / 2);
                sdp_targ_data_align(DATA_WIDTH - 1 downto DATA_WIDTH / 2) <= s_axis_tdata((DATA_WIDTH / 2 ) - 1 downto 0);
              end if;

              sdp_targ_valid_r <= s_axis_tvalid;
            end if;

            if s_axis_tvalid = '1' and payload_ready = '1' then
              if rx_data_beats = msg_data_beats then
                -- end of message
                if msg_start_alignment = 0 or msg_end_alignment = 0 then
                  rx_state <= RX_MSG_PAYLOAD_LAST;
                else
                  -- for SDP_WIDTH = 4: message data is misaligned and we need an extra cycle to get saved MSBs
                  rx_state <= RX_MSG_PAYLOAD_LAST_ALIGN;
                end if;

                -- Remember if TLAST is asserted on this cycle
                tlast_hold <= (s_axis_tlast = '1');
              else
                rx_data_beats <= rx_data_beats + 1;
                if s_axis_tlast = '1' then
                  -- This is a bad situation of a truncated frame when we have already sent some payload
                  -- sdp_targ_eop is set above to let the target know we are ending the transfer early
                  -- Go straight to RX_IDLE without acknowledging this frame, which should eventually either retry this
                  -- packet or cause a runtime error
                  -- TODO: might want to keep a count of these events to report to platform worker
                  rx_state <= RX_IDLE;
                end if;
              end if;
            end if;

          when RX_MSG_PAYLOAD_LAST_ALIGN =>
            if sdp_targ_ready = '1' then
              sdp_targ_data_align((DATA_WIDTH / 2 ) - 1 downto 0) <= prev_tdata(DATA_WIDTH - 1 downto DATA_WIDTH / 2);
              sdp_targ_data_align(DATA_WIDTH - 1 downto DATA_WIDTH / 2) <= (others => '0');
              rx_state <= RX_MSG_PAYLOAD_LAST;
            end if;

          when RX_MSG_PAYLOAD_LAST =>
            if sdp_targ_ready = '1' then
              sdp_targ_valid_r <= '0';
              rx_state <= RX_FLAG;
            end if;

          when RX_FLAG =>
            -- NOTE: rx_txn_valid is asserted while we are in this state
            if rx_txn_ready = '1' then
              if tlast_hold then
                rx_state <= RX_GEN_ACK;
                -- TODO: technically this is an error if rx_nextmsg is set - do we want to do something about it?
              else
                -- If we expect another message, handle it - otherwise we need to consume padding bytes at end of Ethernet frame
                if rx_nextmsg then
                  if SDP_WIDTH = 1 and frame_beat_lsb = '1' then
                    rx_state <= RX_INTER_MSG_PADDING;
                  else
                    rx_state <= RX_MSG_HDR;
                  end if;
                else
                  rx_state <= RX_WAIT_TLAST;
                end if;
              end if;
            end if;

          when RX_INTER_MSG_PADDING =>
            if s_axis_tvalid = '1' then
              rx_state <= RX_MSG_HDR;
            end if;

          when RX_WAIT_TLAST =>
            -- consume extra bytes at end of Ethernet frame
            if s_axis_tvalid = '1' and s_axis_tlast = '1' then
              rx_state <= RX_GEN_ACK;
            end if;

          when RX_GEN_ACK =>
            -- At this point the data in the dgrdma frame has been sent to the
            -- sdp bus without error, so we enqueue the sequence number into
            -- the ack tracker by strobing its valid line.
            ack_tracker_rx_valid <= '1';
            rx_state             <= RX_IDLE;

          when RX_ERROR_WAIT_TLAST =>
            -- parse error - wait for TLAST
            if s_axis_tvalid = '1' and s_axis_tlast = '1' then
              rx_state <= RX_IDLE;
              debug_reject_count <= debug_reject_count + 1;
            end if;
        end case;
      end if;
    end if;
  end process rx_proc;

  -- ACK GENERATION

  tx_ack_req  <= ack_tracker_tx_ack_req;
  tx_ackcount <= ack_tracker_tx_ackcount;

  ack_proc : process(clk)
  begin
    if rising_edge(clk) then
      if reset = '1' then
        tx_ack_req_urg <= '0';
        ack_wait_ctr   <= 0;
      else
        -- Update ACK request urgent flag
        -- If we have just sent an ACK, reset counter and clear urgent request
        -- If we have too many outstanding ACKs, or an ACK has been outstanding for too long, set flag
        if tx_ack_sent = '1' or ack_tracker_tx_ack_req = '0' then
          tx_ack_req_urg <= '0';
          ack_wait_ctr <= 0;
        else
          if max_acks_outstanding /= X"00" and ack_tracker_tx_ackcount >= max_acks_outstanding then
            tx_ack_req_urg <= '1';
          end if;

          if to_integer(ack_wait) /= 0 and ack_wait_ctr >= to_integer(ack_wait) then
            tx_ack_req_urg <= '1';
          else
            ack_wait_ctr <= ack_wait_ctr + 1;
          end if;
        end if;
      end if;
    end if;
  end process ack_proc;

  -- TRANSACTION HANDLING
  rx_txn_valid <= '1' when rx_state = RX_FLAG else '0';
  txn_record_inst : entity work.dgrdma_txn_record
    generic map(
      MAX_TXNS_IN_FLIGHT => MAX_TXNS_IN_FLIGHT
    )
    port map(
      clk => clk,
      reset => reset,

      rx_txn_valid => rx_txn_valid,
      rx_txn_ready => rx_txn_ready,
      rx_txn_id => rx_txn_id,
      rx_msgs_in_txn => rx_msgs_in_txn,
      rx_flag_addr => rx_flag_addr,
      rx_flag_data => rx_flag_data,

      flag_addr => flag_addr,
      flag_data => flag_data,
      flag_valid => flag_valid,
      flag_take => flag_take,

      -- TODO connect debug output signals
      txn_id_out_of_range_count => open,
      txn_error_count => open
    );

  -- Ack tracker
  ack_tracker_rej_ack <= ack_tracker_rej_ack_r;

  ack_tracker_inst : entity work.dgrdma_ack_tracker
    generic map(
      BITFIELD_WIDTH => ACK_TRACKER_BITFIELD_WIDTH,
      MAX_ACK_COUNT => ACK_TRACKER_MAX_ACK_COUNT
    )
    port map (
      clk => clk,
      reset => reset,

      rx_frameseq => rx_frameseq,

      rx_valid        => ack_tracker_rx_valid,
      rx_peek         => ack_tracker_rx_peek,
      rx_reject       => ack_tracker_rx_reject,
      rx_reject_valid => ack_tracker_rx_reject_valid,
      rx_reject_ready => ack_tracker_rx_reject_ready,

      tx_ackcount_sent => tx_ackcount_sent,
      tx_ack_sent      => tx_ack_sent,

      tx_ackstart => tx_ackstart,
      tx_ackcount => ack_tracker_tx_ackcount,
      tx_ack_req  => ack_tracker_tx_ack_req,

      debug_bitfield     => ack_tracker_debug_bitfield,
      debug_base_seqno   => ack_tracker_debug_base_seqno,

      count_ack_tracker_total_acks_sent     => ack_tracker_total_acks_sent,
      count_ack_tracker_tx_acks_sent        => ack_tracker_tx_acks_sent,
      count_ack_tracker_pkts_enqueued       => ack_tracker_pkts_enqueued,
      count_ack_tracker_reject_out_of_range => ack_tracker_reject_out_of_range,
      count_ack_tracker_reject_already_set  => ack_tracker_reject_already_set,
      count_ack_tracker_accepted_by_peek    => ack_tracker_accepted_by_peek,
      debug_high_watermark                  => ack_tracker_high_watermark
    );

end architecture;
