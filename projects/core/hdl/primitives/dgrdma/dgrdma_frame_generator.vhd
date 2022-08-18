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

entity dgrdma_frame_generator is
  generic(
    SDP_WIDTH : natural;
    MAX_MESSAGE_DWORDS : natural := 4096;
    ACK_TRACKER_MAX_ACK_COUNT  : natural range 1 to 255 := 8
  );
  port(
    clk : in std_logic;
    reset : in std_logic;

    -- configuration (via platform worker properties)
    remote_mac_addr : in std_logic_vector(47 downto 0);
    remote_dst_id : in std_logic_vector(15 downto 0);
    local_src_id : in std_logic_vector(15 downto 0);
    interface_mtu : in unsigned(15 downto 0);
    coalesce_wait :  in unsigned(31 DOWNTO 0);

    -- ack request
    tx_ackstart : in unsigned(15 downto 0);
    tx_ackcount : integer range 0 to ACK_TRACKER_MAX_ACK_COUNT;
    tx_ack_req : in std_logic;
    tx_ack_req_urg : in std_logic;
    tx_ack_sent : out std_logic;
    tx_ackcount_sent : out integer range 0 to ACK_TRACKER_MAX_ACK_COUNT;

    -- connection from SDP initiator
    sdp_init_count : in count_t;
    sdp_init_op : in op_t;
    sdp_init_xid : in xid_t;
    sdp_init_lead : in unsigned(end_bytes_width-1 downto 0);
    sdp_init_trail : in unsigned(end_bytes_width-1 downto 0);
    sdp_init_node : in id_t;
    sdp_init_addr : in addr_t;
    sdp_init_extaddr : in extaddr_t;
    sdp_init_eop : in bool_t;
    sdp_init_valid : in bool_t;
    sdp_init_ready : out bool_t;

    sdp_init_data : in dword_array_t(0 to SDP_WIDTH - 1);

    -- DGRDMA frame
    m_axis_tdata : out std_logic_vector(data_width_for_sdp(SDP_WIDTH) - 1 downto 0);
    m_axis_tkeep : out std_logic_vector(keep_width_for_sdp(SDP_WIDTH) - 1 downto 0);
    m_axis_tvalid : out std_logic;
    m_axis_tready : in std_logic;
    m_axis_tlast : out std_logic
  );
end dgrdma_frame_generator;

architecture rtl of dgrdma_frame_generator is

  -- FRAGMENTATION STATE MACHINE
  constant FRAME_HEADER_BYTES : natural := 24;  -- (14 bytes Ethernet frame header + 10 bytes DG-RDMA frame header)
  constant MESSAGE_HEADER_BYTES : natural := 24;
  type frag_state_t is (
    FRAG_IDLE,
    FRAG_WAIT_START,
    FRAG_CALC1_FIRSTMSG,
    FRAG_CALC1,
    FRAG_CALC2,
    FRAG_META1,
    FRAG_META2,
    FRAG_PAYLOAD,
    FRAG_WAIT_DIVIDE,
    FRAG_WAIT_SDP,
    FRAG_WAIT_TX
  );

  signal frag_state : frag_state_t;
  signal remaining_frame_capacity_bytes : unsigned(15 downto 0);
  signal txn_len_dwords : unsigned(12 downto 0);
  signal need_metadata : boolean;
  signal coalesce_wait_count : unsigned (31 downto 0);

  -- debug signals (variables in process)
  signal txn_len_dwords_d : unsigned(12 downto 0);
  signal txn_len_bytes_d : unsigned(15 downto 0);
  signal msg_len_dwords_d : unsigned(12 downto 0);
  signal msg_len_beats_d : unsigned(12 downto 0);

  signal dividend : unsigned(12 downto 0);
  signal divisor : unsigned(12 downto 0);
  signal div_q : unsigned(12 downto 0);
  signal div_rem : unsigned(12 downto 0);
  signal div_start : std_logic;
  signal div_complete : std_logic;
  signal div_required : std_logic;

  -- MESSAGE BUFFER
  subtype msgbuf_row_t is std_logic_vector(data_width_for_sdp(SDP_WIDTH) - 1 downto 0);
  subtype msgbuf_ptr_t is natural range 0 to (MAX_MESSAGE_DWORDS / SDP_WIDTH) - 1;
  type msgbuf_t is array (natural range <>) of msgbuf_row_t;

  signal msgbuf : msgbuf_t(0 to (MAX_MESSAGE_DWORDS / SDP_WIDTH) - 1);
  signal msgbuf_rptr : msgbuf_ptr_t;
  signal msgbuf_wptr : msgbuf_ptr_t;
  signal msgbuf_empty : std_logic;
  signal msgbuf_full : std_logic;
  signal msgbuf_write : std_logic;
  signal msgbuf_read : std_logic;
  signal msgbuf_write_data : dword_array_t(0 to SDP_WIDTH - 1);
  signal msgbuf_read_data : dword_array_t(0 to SDP_WIDTH - 1);

  -- NEXT MESSAGE HEADER
  type msg_hdr_t is record
  last_in_frame : std_logic;
    txn_id : unsigned(31 downto 0);
    msgs_in_txn : unsigned(12 downto 0);
    seq : unsigned(15 downto 0);
    addr : unsigned(31 downto 0);
    len_dwords : unsigned(12 downto 0);
    flag_addr : std_logic_vector(31 downto 0);
    flag_data : std_logic_vector(31 downto 0);
  end record msg_hdr_t;

  signal nextmsg : msg_hdr_t;
  signal nextmsg_valid : std_logic;
  signal nextmsg_ready : std_logic;

  -- TRANSMIT STATE MACHINE
  type tx_state_t is (
    TX_IDLE,
    TX_WAIT_START,
    TX_FRAME_HDR,
    TX_WAIT_MSG,
    TX_MSG_HDR,
    TX_SHORT_MSG,
    TX_MSG_PAYLOAD,
    TX_MSG_PAD,
    TX_WAIT_LAST
  );

  signal tx_state : tx_state_t;
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

  signal msg_hdr_alignment : natural range 0 to 1;
  signal msg_start_alignment : natural range 0 to 1;
  signal msg_end_alignment : natural range 0 to 1;
  signal prev_msgbuf_read_data : dword_array_t(0 to SDP_WIDTH - 1);

  signal m_axis_tdata_words : dword_array_t(0 to SDP_WIDTH - 1);
  signal last_tdata_words   : dword_array_t(0 to SDP_WIDTH - 1);

  signal tx_frame_hdr_reg : std_logic_vector(127 downto 0);
  signal tx_msg_hdr_reg : std_logic_vector(191 downto 0);

  signal tx_hasmsg : boolean;
  signal msg_last_in_frame : std_logic;
  signal msg_len_dwords : unsigned(12 downto 0);
  signal msg_pad_dwords : unsigned(1 downto 0);

  signal tx_frameseq : unsigned(15 downto 0);

  signal m_axis_tvalid_r : std_logic;
  signal msgbuf_read_valid : std_logic;
begin

  -- FRAGMENTATION STATE MACHINE
  with frag_state select sdp_init_ready <=
    not msgbuf_full when FRAG_PAYLOAD,
    '1'             when FRAG_META1 | FRAG_META2,
    '0'             when others;

  with frag_state select msgbuf_write <=
    sdp_init_valid when FRAG_PAYLOAD,
    '0'            when others;

  msgbuf_write_data <= sdp_init_data;

  ---------------------------------------------------------------------------
  frag_proc : process(clk)
    variable txn_len_bytes : unsigned(15 downto 0);
    variable msg_len_dwords : unsigned(12 downto 0);
    variable msg_len_beats : unsigned(12 downto 0);
    variable remaining_capacity : unsigned(15 downto 0);

    procedure reset_state is
    begin
      nextmsg_valid <= '0';

      nextmsg.last_in_frame <= '0';
      nextmsg.msgs_in_txn <= (others => '0');
      nextmsg.addr <= (others => '0');
      nextmsg.len_dwords <= (others => '0');
      nextmsg.flag_addr <= (others => '0');
      nextmsg.flag_data <= (others => '0');

      txn_len_dwords <= (others => '0');

      div_required <= '0';
      need_metadata <= false;

      coalesce_wait_count <= (others => '0');
    end procedure reset_state;

    function round_down(value : unsigned; precision : natural) return unsigned is
    begin
      return resize((value / precision) * precision, value'length);
    end round_down;

    function round_up(value : unsigned; precision : natural) return unsigned is
    begin
      return resize(((value + precision - 1) / precision) * precision, value'length);
    end round_up;

  begin
    if rising_edge(clk) then
      if reset = '1' then
        frag_state <= FRAG_IDLE;
        nextmsg.txn_id <= to_unsigned(1, nextmsg.txn_id'length);
        reset_state;
      else
        -- defaults for single-cycle strobe outputs
        div_start <= '0';

        case frag_state is
          when FRAG_IDLE =>
            reset_state;
            frag_state <= FRAG_WAIT_START;
            remaining_frame_capacity_bytes <= interface_mtu - FRAME_HEADER_BYTES;

          when FRAG_WAIT_START =>
            if sdp_init_valid and (sdp_init_op = write_e or sdp_init_op = write_with_metadata_e) then
              -- addr is a 24-bit word address (corresponding to 26-bit byte address)
              -- extaddr is 10-bits wide to allows us to extend this to a 36-bit byte address
              -- DG-RDMA has a 32-bit byte addresses, so we'll ignore the top 4 bits of extaddr
              nextmsg.addr <= sdp_init_extaddr(5 downto 0) & sdp_init_addr & "00";
              nextmsg.seq <= to_unsigned(1, nextmsg.seq'length);
              txn_len_dwords <= ("0" & sdp_init_count) + 1;
              frag_state <= FRAG_CALC1_FIRSTMSG;
              remaining_frame_capacity_bytes <= remaining_frame_capacity_bytes - MESSAGE_HEADER_BYTES;
              coalesce_wait_count <= (others => '0');

              if sdp_init_op = write_e then
                need_metadata <= false;
                nextmsg.flag_addr <= X"ffffffff";
                nextmsg.flag_data <= X"ffffffff";
              else
                need_metadata <= true;
              end if;
            end if;

          when FRAG_CALC1_FIRSTMSG =>
            txn_len_bytes := resize(txn_len_dwords * 4, txn_len_bytes'length);
            frag_state <= FRAG_CALC2;

            -- Can this transfer be sent as a single message in the current frame?
            if round_up(txn_len_bytes,8) <= remaining_frame_capacity_bytes then
              -- next message (if any) must start on an 8-byte boundary per DG-RDMA spec
              remaining_frame_capacity_bytes <= remaining_frame_capacity_bytes - round_up(txn_len_bytes, 8);

              msg_len_dwords := txn_len_dwords;
              nextmsg.msgs_in_txn <= to_unsigned(1, nextmsg.msgs_in_txn'length);
              nextmsg.len_dwords <= txn_len_dwords;
            else
              -- No; we will fill the current frame
              remaining_frame_capacity_bytes <= to_unsigned(0, remaining_frame_capacity_bytes'length);

              -- Always fragment on an SDP_WIDTH boundary for simplicity
              msg_len_dwords := resize(round_down(remaining_frame_capacity_bytes / 4, SDP_WIDTH), msg_len_dwords'length);
              nextmsg.len_dwords <= msg_len_dwords;

              -- Start divider to calculate total number of messages in transaction
              dividend <= txn_len_dwords - msg_len_dwords;
              -- Always fragment on an SDP_WIDTH boundary for simplicity
              divisor <= resize(round_down((interface_mtu - (FRAME_HEADER_BYTES + MESSAGE_HEADER_BYTES)) / 4, SDP_WIDTH), divisor'length);
              div_start <= '1';
              div_required <= '1';
            end if;

            -- Update number of words left in the transaction
            txn_len_dwords <= txn_len_dwords - msg_len_dwords;

          when FRAG_CALC1 =>
            txn_len_bytes := resize(txn_len_dwords * 4, txn_len_bytes'length);
            frag_state <= FRAG_CALC2;

            nextmsg.seq <= nextmsg.seq + 1;

            -- Can this transfer be sent as a single message in the current frame?
            if txn_len_bytes <= remaining_frame_capacity_bytes then
              -- next message (if any) must start on an 8-byte boundary per DG-RDMA spec
              remaining_frame_capacity_bytes <= remaining_frame_capacity_bytes - round_up(txn_len_bytes, 8);

              msg_len_dwords := txn_len_dwords;
              nextmsg.len_dwords <= txn_len_dwords;
            else
              -- No; we will fill the current frame
              remaining_frame_capacity_bytes <= to_unsigned(0, remaining_frame_capacity_bytes'length);

              -- Always fragment on an SDP_WIDTH boundary for simplicity
              msg_len_dwords := resize(round_down(remaining_frame_capacity_bytes / 4, SDP_WIDTH), msg_len_dwords'length);
              nextmsg.len_dwords <= msg_len_dwords;
            end if;

            -- Update number of words left in the transaction
            txn_len_dwords <= txn_len_dwords - msg_len_dwords;

          when FRAG_CALC2 =>
            msg_len_beats := resize(round_up(msg_len_dwords, SDP_WIDTH) / SDP_WIDTH, msg_len_beats'length);

            -- check if there is space left for another message in the frame
            -- last_in_frame might be overridden if coalesce_wait times out (in FRAG_WAIT_SDP state below)
            if remaining_frame_capacity_bytes < (MESSAGE_HEADER_BYTES + (4*SDP_WIDTH)) then
              nextmsg.last_in_frame <= '1';
            else
              nextmsg.last_in_frame <= '0';
            end if;

            if need_metadata then
              frag_state <= FRAG_META1;
              need_metadata <= false;
            else
              frag_state <= FRAG_PAYLOAD;
            end if;

          when FRAG_META1 =>
            if sdp_init_valid = '1' then
              nextmsg.flag_addr <= sdp_init_data(0);
              if SDP_WIDTH = 1 then
                frag_state <= FRAG_META2;
              else
                frag_state <= FRAG_PAYLOAD;
                nextmsg.flag_data <= sdp_init_data(1);
              end if;
            end if;

          when FRAG_META2 =>
            -- only for SDP_WIDTH=1
            if sdp_init_valid = '1' then
              nextmsg.flag_data <= sdp_init_data(0);
              frag_state <= FRAG_PAYLOAD;
            end if;

          -- In this state we write SDP data straight into the message buffer
          when FRAG_PAYLOAD =>
            if msgbuf_full = '0' and sdp_init_valid = '1' then
              if msg_len_beats = 1 then
                -- Last beat of message
                if div_required = '1' then
                  frag_state <= FRAG_WAIT_DIVIDE;
                else
                  frag_state <= FRAG_WAIT_SDP;
                end if;
              end if;
              msg_len_beats := msg_len_beats - 1;
            end if;

          when FRAG_WAIT_DIVIDE =>
            div_required <= '0';
            if div_complete = '1' then
              frag_state <= FRAG_WAIT_SDP;
              -- Adjust divider output to calculate total messages in transaction
              -- Note that we have already subtracted the length of the first (current) message
              -- and if div_rem /= 0 we will need a partial-frame message at the end
              if div_rem = 0 then
                nextmsg.msgs_in_txn <= div_q + 1;
              else
                nextmsg.msgs_in_txn <= div_q + 2;
              end if;
            end if;

          when FRAG_WAIT_SDP =>
            coalesce_wait_count <= coalesce_wait_count + 1;
            if nextmsg.last_in_frame = '1' then
              -- no more room in frame - send immediately
              -- this covers the case where the transfer was fragmented and there is another message ready to be sent immediately
              nextmsg_valid <= '1';
              frag_state <= FRAG_WAIT_TX;
            elsif coalesce_wait_count = coalesce_wait or tx_ack_req_urg = '1' then
              -- timeout or we need to send an ACK - send buffered message (resulting in partially-filled frame) and go idle
              nextmsg.last_in_frame <= '1';
              nextmsg_valid <= '1';
              frag_state <= FRAG_WAIT_TX;
            elsif sdp_init_valid = '1' then
              -- another transfer is ready - send buffered message then start processing incoming transfer
              nextmsg_valid <= '1';
              frag_state <= FRAG_WAIT_TX;
            end if;

          when FRAG_WAIT_TX =>
            coalesce_wait_count <= (others => '0');
            if nextmsg_ready = '1' then
              nextmsg_valid <= '0';

              if txn_len_dwords = 0 then
                -- End of transaction
                if nextmsg.last_in_frame = '1' then
                  frag_state <= FRAG_IDLE;
                else
                  frag_state <= FRAG_WAIT_START;
                end if;

                nextmsg.txn_id <= nextmsg.txn_id + 1;
              else
                -- Prepare next message (there is more data remaining in the transaction)
                -- This can only happen if we have filled a frame so last_in_frame is set, so reset frame capacity
                frag_state <= FRAG_CALC1;
                remaining_frame_capacity_bytes <= interface_mtu - (FRAME_HEADER_BYTES + MESSAGE_HEADER_BYTES);
                nextmsg.addr <= nextmsg.addr + (msg_len_dwords * 4);
              end if;
            end if;
        end case;

        -- copy variables to signals for debugging
        txn_len_dwords_d <= txn_len_dwords;
        txn_len_bytes_d <= txn_len_bytes;
        msg_len_dwords_d <= msg_len_dwords;
        msg_len_beats_d <= msg_len_beats;
      end if;
    end if;
  end process frag_proc;

  divide_inst : entity work.divide
    generic map(
      OPERAND_WIDTH => 13
    )
    port map(
      clk => clk,
      reset => reset,

      start => div_start,
      dividend => dividend,
      divisor => divisor,

      quotient => div_q,
      remainder => div_rem,
      result_valid => div_complete
    );

  -- -------------------------------------------------------------------------
  -- MESSAGE BUFFER
  msgbuf_fifo : process(clk)
    variable read : boolean;
    variable write : boolean;
    variable read_addr : msgbuf_ptr_t;

    function inc_ptr(ptr : msgbuf_ptr_t) return msgbuf_ptr_t is
      begin
        if ptr = msgbuf_ptr_t'high then
          return 0;
        else
          return ptr + 1;
        end if;
      end inc_ptr;

  begin
    if rising_edge(clk) then
      if reset = '1' then
        msgbuf_rptr <= 0;
        msgbuf_wptr <= 0;
        msgbuf_empty <= '1';
        msgbuf_full <= '0';
      else
        -- Read/write strobes
        read := (msgbuf_read = '1' and msgbuf_empty = '0');
        write := (msgbuf_write = '1' and msgbuf_full = '0');

        -- Handle input and output data
        if write then
          msgbuf(msgbuf_wptr) <= pack_sdp_data(msgbuf_write_data);
        end if;

        if read then
          read_addr := inc_ptr(msgbuf_rptr);
        else
          read_addr := msgbuf_rptr;
        end if;

        -- Update pointers and flags
        if read and write then
          msgbuf_rptr <= inc_ptr(msgbuf_rptr);
          msgbuf_wptr <= inc_ptr(msgbuf_wptr);
        elsif read then
          msgbuf_rptr <= inc_ptr(msgbuf_rptr);
          msgbuf_full <= '0';
          if inc_ptr(msgbuf_rptr) = msgbuf_wptr then
            msgbuf_empty <= '1';
          end if;
        elsif write then
          msgbuf_wptr <= inc_ptr(msgbuf_wptr);
          msgbuf_empty <= '0';
          if inc_ptr(msgbuf_wptr) = msgbuf_rptr then
            msgbuf_full <= '1';
          end if;
        end if;

        msgbuf_read_data <= unpack_sdp_data(msgbuf(read_addr));

      end if;
    end if;
  end process msgbuf_fifo;

  -- -------------------------------------------------------------------------
  -- TX STATE MACHINE
  m_axis_tlast <= '1' when (tx_state = TX_WAIT_LAST) else '0';
  m_axis_tvalid <= m_axis_tvalid_r;
  m_axis_tdata <= pack_sdp_data(m_axis_tdata_words);

  -- Determine when to read the message data buffer
  msgbuf_read_proc : process(tx_state, m_axis_tready, header_beat, msg_hdr_alignment, msg_start_alignment, msg_end_alignment, msg_len_dwords)
  begin
    -- Default: don't read
    msgbuf_read <= '0';

    -- Final header beat with msg_hdr_alignment = 0 (and therefore msg_start_alignment = 1):
    -- we have consumed LSBs of data from message buffer
    -- next beat will consist of MSBs plus LSBs from next row in buffer, so read it here
    if tx_state = TX_MSG_HDR then
      if m_axis_tready = '1' and SDP_WIDTH = 4 and msg_hdr_alignment = 0 and header_beat = 1 then
        msgbuf_read <= '1';
      end if;

    -- Payload: usually we read whenever we consume a beat (whenever AXI TREADY is high)
    -- The exception is the last beat on a 128-bit bus when msg_start_alignment = 1 (so we
    -- are realigning message data) and msg_end_alignment = 0 (so the last beat contains one or two
    -- DWORDS) - in this case we are just taking the previous beat's MSBs from prev_msg_read_data,
    -- so must not consume another word from the buffer
    elsif tx_state = TX_MSG_PAYLOAD then
      if m_axis_tready = '1' then
        if SDP_WIDTH /= 4 then
          msgbuf_read <= '1';
        else
          if not(msg_start_alignment = 1 and msg_end_alignment = 0 and msg_len_dwords <= 2) then
            msgbuf_read <= '1';
          end if;
        end if;
      end if;
    end if;
  end process msgbuf_read_proc;

  -- -------------------------------------------------------------------------
  -- Tx state machine
  tx_proc : process(clk)

    variable last_msg_header_beat : boolean;
    variable end_packet_alignment : natural range 0 to SDP_WIDTH - 1;  -- index into AXI beat of last word in the message

    -- reset frame state
    procedure reset_state is
    begin
      nextmsg_ready <= '0';

      tx_ack_sent <= '0';
      tx_ackcount_sent <= 0;
      m_axis_tdata_words <= (others => (others => '0'));
      m_axis_tkeep <= (others => '0');
      m_axis_tvalid_r <= '0';
      tx_hasmsg <= false;
      msg_last_in_frame <= '0';
      msg_len_dwords <= (others => '0');
      last_tdata_words <= (others => (others => '0'));

      tx_frame_hdr_reg <= (others => '0');
      tx_msg_hdr_reg <= (others => '0');

      header_beat <= 0;
      msg_hdr_alignment <= 0;
      msg_start_alignment <= 0;
      msg_end_alignment <= 0;
    end procedure reset_state;

    procedure set_frame_hdr_reg(hasmsg : boolean) is
    begin
      tx_frame_hdr_reg <= (others => '0'); -- default

      tx_frame_hdr_reg( 47 downto   0) <= swap_bytes(remote_mac_addr);
      tx_frame_hdr_reg( 63 downto  48) <= remote_dst_id;
      tx_frame_hdr_reg( 79 downto  64) <= local_src_id;
      tx_frame_hdr_reg( 95 downto  80) <= std_logic_vector(tx_frameseq);
      tx_frame_hdr_reg(111 downto  96) <= std_logic_vector(tx_ackstart);
      tx_frame_hdr_reg(119 downto 112) <= std_logic_vector(to_unsigned(tx_ackcount, 8));
      if hasmsg then
        tx_frame_hdr_reg(120) <= '1';
      end if;

      tx_ackcount_sent <= tx_ackcount;
      tx_ack_sent <= '1';
      tx_frameseq <= tx_frameseq + 1;
      tx_hasmsg <= hasmsg;
    end procedure;

    procedure set_msg_hdr_reg is
    begin
      tx_msg_hdr_reg <= (others => '0'); -- default

      tx_msg_hdr_reg( 31 downto   0) <= std_logic_vector(nextmsg.txn_id);
      tx_msg_hdr_reg( 63 downto  32) <= nextmsg.flag_addr;
      tx_msg_hdr_reg( 95 downto  64) <= nextmsg.flag_data;
      tx_msg_hdr_reg(111 downto  96) <= "000" & std_logic_vector(nextmsg.msgs_in_txn);
      tx_msg_hdr_reg(127 downto 112) <= std_logic_vector(nextmsg.seq);
      tx_msg_hdr_reg(159 downto 128) <= std_logic_vector(nextmsg.addr);
      tx_msg_hdr_reg(175 downto 160) <= "0" & std_logic_vector(nextmsg.len_dwords) & "00";  -- in bytes

      if nextmsg.last_in_frame = '0' then
        tx_msg_hdr_reg(184) <= '1';
      end if;
    end procedure;

  begin
    if rising_edge(clk) then
      if reset = '1' then
        reset_state;
        tx_frameseq <= to_unsigned(1, 16);
        tx_state <= TX_IDLE;
      else
        -- defaults for single-cycle strobe outputs
        tx_ack_sent <= '0';
        nextmsg_ready <= '0';

        -- Save previous read data to handle message alignment for SDP_WIDTH > 4
        if msgbuf_read = '1' and msgbuf_empty = '0' then
          prev_msgbuf_read_data <= msgbuf_read_data;
        end if;

        case tx_state is
          when TX_IDLE =>
            -- Reset all state variables and outputs and prepare to accept SDP data
            reset_state;
            tx_state <= TX_WAIT_START;
            m_axis_tvalid_r <= '0';

          -- s_axis_tready is asserted while we are in this state
          -- send a frame if an SDP transfer is starting, or an ACK needs to be sent urgently

          when TX_WAIT_START =>
            if nextmsg_valid = '1' or tx_ack_req_urg = '1' then
              tx_state <= TX_FRAME_HDR;

              set_frame_hdr_reg(nextmsg_valid = '1');
              set_msg_hdr_reg;
            end if;

          when TX_FRAME_HDR =>
            -- TVALID is low on entrance to this state
            m_axis_tvalid_r <= '1';
            m_axis_tkeep <=  (others => '1');

            if m_axis_tready = '1' or m_axis_tvalid_r = '0' then
              -- header alignment is always zero for the first message in a frame
              msg_hdr_alignment <= 0;

              for i in 0 to SDP_WIDTH - 1 loop
                m_axis_tdata_words(i) <= unpack_sdp_data(tx_frame_hdr_reg)(header_beat*SDP_WIDTH+i);
              end loop;

              if (SDP_WIDTH = 1 and header_beat = 3) or (SDP_WIDTH = 2 and header_beat = 1) or (SDP_WIDTH = 4 and header_beat = 0) then
                header_beat <= 0;
                if tx_hasmsg then
                  tx_state <= TX_MSG_HDR;
                else
                  tx_state <= TX_WAIT_LAST;
                end if;
              else
                header_beat <= header_beat + 1;
              end if;
            end if;

          when TX_SHORT_MSG =>
            if m_axis_tready = '1' then
              m_axis_tvalid_r <= '0';
              tx_state <= TX_WAIT_MSG;
            end if;

          when TX_WAIT_MSG =>
            if m_axis_tready = '1' then
              m_axis_tvalid_r <= '0';
            end if;
            if nextmsg_valid = '1' then
              tx_state <= TX_MSG_HDR;
              set_msg_hdr_reg;
            end if;

          when TX_MSG_HDR =>
            m_axis_tvalid_r <= '1';

            if m_axis_tready = '1' or m_axis_tvalid_r = '0' then
              last_msg_header_beat := false;

              if SDP_WIDTH /= 4 then
                for i in 0 to SDP_WIDTH - 1 loop
                  m_axis_tdata_words(i) <= unpack_sdp_data(tx_msg_hdr_reg)(header_beat*SDP_WIDTH+i);
                end loop;

                if (SDP_WIDTH = 1 and header_beat = 5) or (SDP_WIDTH = 2 and header_beat = 2) then
                  header_beat <= 0;
                  last_msg_header_beat := true;
                else
                  header_beat <= header_beat + 1;
                end if;
              else
                -- 128-bit bus
                -- Set alignment of message start and end, and next message header
                if header_beat = 0 then
                  header_beat <= 1;
                else
                  header_beat <= 0;
                  last_msg_header_beat := true;
                end if;

                if msg_hdr_alignment = 0 then
                  case header_beat is
                    when 0 =>
                      for i in 0 to 3 loop
                        m_axis_tdata_words(i) <= unpack_sdp_data(tx_msg_hdr_reg)(i);
                      end loop;
                      header_beat <= 1;
                    when 1 =>
                      for i in 0 to 1 loop
                        m_axis_tdata_words(i) <= unpack_sdp_data(tx_msg_hdr_reg)(4+i);
                      end loop;
                      for i in 0 to 1 loop
                        m_axis_tdata_words(2 + i) <= msgbuf_read_data(i);
                      end loop;
                      -- don't send trailing word for a 1-DWORD message
                      --if nextmsg.len_dwords = 1 then
                      --  m_axis_tkeep(m_axis_tkeep'high downto m_axis_tkeep'high - 3) <= "0000";
                      --end if;

                  end case;
                else  -- msg_hdr_alignment = 1
                  case header_beat is
                    when 0 =>
                      for i in 0 to 1 loop
                        -- first 2 words are last words of previous message
                        m_axis_tdata_words(2 + i) <= unpack_sdp_data(tx_msg_hdr_reg)(i);
                      end loop;
                    when 1 =>
                      for i in 0 to 3 loop
                        m_axis_tdata_words(i) <= unpack_sdp_data(tx_msg_hdr_reg)(2 + i);
                      end loop;
                  end case;
                end if;
              end if;

              if last_msg_header_beat then
                nextmsg_ready <= '1';
                msg_last_in_frame <= nextmsg.last_in_frame;
                header_beat <= 0;

                if (SDP_WIDTH = 1) and  (nextmsg.len_dwords mod 2 /= 0) then
                  msg_pad_dwords <= to_unsigned(1, msg_pad_dwords'length);
                else
                  msg_pad_dwords <= to_unsigned(0, msg_pad_dwords'length);
                end if;

                if SDP_WIDTH /= 4 then
                  tx_state <= TX_MSG_PAYLOAD;
                  msg_len_dwords <= nextmsg.len_dwords;
                else  -- SDP_WIDTH = 4
                  if msg_hdr_alignment = 0 then
                    msg_start_alignment <= 1;
                    end_packet_alignment := to_integer(nextmsg.len_dwords + 1) mod 4;

                    if nextmsg.len_dwords <= 2 then
                      -- If the entire message fits into the same beat as the last cycle of the header, we are done
                      if nextmsg.last_in_frame = '1' then
                        tx_state <= TX_WAIT_LAST;
                      else
                        tx_state <= TX_SHORT_MSG;
                      end if;

                      msg_len_dwords <= to_unsigned(0, msg_len_dwords'length);
                    else
                      -- Otherwise take up to 2 words from prev_sdp_targ_data and up to 2 words from sdp_targ_data
                      tx_state <= TX_MSG_PAYLOAD;
                      msg_len_dwords <= nextmsg.len_dwords - 2;
                    end if;
                  else
                    -- message data is aligned with SDP data - continue as in SDP_WIDTH < 4 case
                    msg_start_alignment <= 0;
                    end_packet_alignment := to_integer(nextmsg.len_dwords + 3) mod 4;
                    tx_state <= TX_MSG_PAYLOAD;
                    msg_len_dwords <= nextmsg.len_dwords;
                  end if;

                  case end_packet_alignment is
                    when 0 | 1 =>
                      msg_end_alignment <= 0;
                      msg_hdr_alignment <= 1;
                    when 2 | 3 =>
                      msg_end_alignment <= 1;
                      msg_hdr_alignment <= 0;
                  end case;
                end if;
              end if;
            end if;

          -- m_axis_tvalid is always high in this state
          when TX_MSG_PAYLOAD =>
            if m_axis_tready = '1' then
              if SDP_WIDTH /= 4 then
                -- Place data on to AXI output
                m_axis_tdata_words <= msgbuf_read_data;
                last_tdata_words <= msgbuf_read_data;
              else
                -- Place data on to AXI output, realigning if necessary
                if msg_start_alignment = 0 then
                  m_axis_tdata_words <= msgbuf_read_data;
                  last_tdata_words <= msgbuf_read_data;
                else
                  m_axis_tdata_words(0 to SDP_WIDTH / 2 - 1) <= prev_msgbuf_read_data(SDP_WIDTH / 2 to SDP_WIDTH - 1);
                  m_axis_tdata_words(SDP_WIDTH / 2 to SDP_WIDTH - 1) <= msgbuf_read_data(0 to SDP_WIDTH / 2 - 1);
                  last_tdata_words(0 to SDP_WIDTH / 2 - 1) <= prev_msgbuf_read_data(SDP_WIDTH / 2 to SDP_WIDTH - 1);
                  last_tdata_words(SDP_WIDTH / 2 to SDP_WIDTH - 1) <= msgbuf_read_data(0 to SDP_WIDTH / 2 - 1);
                end if;
              end if;

              -- Set TKEEP correctly for last beat in transfer
              -- Update remaining message length for other beats
              if msg_len_dwords <= SDP_WIDTH then

                if msg_last_in_frame = '1' then
                  for i in 0 to SDP_WIDTH - 1 loop
                    if msg_len_dwords > i then
                      m_axis_tkeep(i*4+3 downto i*4) <= X"f";
                    else
                      m_axis_tkeep(i*4+3 downto i*4) <= X"0";
                      m_axis_tdata_words(i) <= (others => '0');
                    end if;
                  end loop;
                end if;

                if msg_last_in_frame = '1' then
                  tx_state <= TX_WAIT_LAST;
                else
                  if (SDP_WIDTH = 1) and (msg_pad_dwords /= 0) then
                    tx_state <= TX_MSG_PAD;
                  elsif (SDP_WIDTH = 4) and (msg_end_alignment = 0) then
                     tx_state <= TX_WAIT_MSG;
                     m_axis_tvalid_r <= '0';
                  else
                    tx_state <= TX_WAIT_MSG;
                  end if;
                end if;

                msg_len_dwords <= to_unsigned(0, msg_len_dwords'length);
              else
                m_axis_tkeep <= (others => '1');
                msg_len_dwords <= msg_len_dwords - SDP_WIDTH;
              end if;
            end if;

          -- insert padding for alignment of message header
          -- (SDP_WIDTH=1 only)
          when TX_MSG_PAD =>
            if m_axis_tready = '1' then
              tx_state <= TX_WAIT_MSG;
            end if;

          -- wait for last beat of frame to be accepted
          -- TVALID must be asserted on entry to this state
          -- TLAST is asserted while in this state
          when TX_WAIT_LAST =>
            if m_axis_tready = '1' then
              m_axis_tvalid_r <= '0';

              tx_state <= TX_IDLE;
            end if;

        end case;
      end if;
    end if;
  end process tx_proc;

end architecture;
