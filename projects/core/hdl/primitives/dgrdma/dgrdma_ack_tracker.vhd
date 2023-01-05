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
use ieee.math_real.ceil;
use ieee.math_real.log2;
use work.dgrdma_util.minimum;

entity dgrdma_ack_tracker is
  generic(
    BITFIELD_WIDTH : natural := 8;
    MAX_ACK_COUNT  : natural range 1 to 255 := 8;
    -- Should be 1 except in testing
    INIT_BASE_SEQNO : unsigned(15 downto 0) := to_unsigned(1, 16)
  );
  port(
    clk   : in std_logic;
    reset : in std_logic;

    -- Incoming packet data
    rx_frameseq : in unsigned(15 downto 0);

    -- Request and response valid strobes
    -- rx_valid and rx_peek should never be high simultaneously
    rx_valid        : in std_logic;  -- valid strobe for rx_frameseq to enqueue
    rx_peek         : in std_logic;  -- valid strobe for rx_frameseq to ask if will reject
    rx_reject       : out std_logic;  -- response strobe on the next cycle as the rx_peek request
    rx_reject_valid : out std_logic;  -- Valid signal for rx_reject
    rx_reject_ready : in std_logic; -- rx_reject has been consumed by caller

    -- Transmitted acks
    tx_ackcount_sent : in integer range 0 to MAX_ACK_COUNT;
    tx_ack_sent      : in std_logic;  -- valid pulse for tx_ackcount_sent

    -- Requests for acks to be transmitted
    tx_ackstart : out unsigned(15 downto 0);
    tx_ackcount : out integer range 0 to MAX_ACK_COUNT;
    tx_ack_req  : out std_logic;

    -- Debug outputs
    debug_bitfield                        : out std_logic_vector(31 downto 0);
    debug_base_seqno                      : out std_logic_vector(15 downto 0);
    count_ack_tracker_total_acks_sent     : out std_logic_vector(31 downto 0);
    count_ack_tracker_tx_acks_sent        : out std_logic_vector(31 downto 0);
    count_ack_tracker_pkts_enqueued       : out std_logic_vector(31 downto 0);
    count_ack_tracker_reject_out_of_range : out std_logic_vector(31 downto 0);
    count_ack_tracker_reject_already_set  : out std_logic_vector(31 downto 0);
    count_ack_tracker_accepted_by_peek    : out std_logic_vector(31 downto 0);
    debug_high_watermark                  : out std_logic_vector(15 downto 0)
  );
end dgrdma_ack_tracker;

architecture rtl of dgrdma_ack_tracker is

  constant MAX_SEQNO : unsigned(15 downto 0) := to_unsigned(65535, 16);
  constant MAX_BITFIELD_INDEX : integer := BITFIELD_WIDTH - 1;
  -- The number of bits which are required to select items in the bitfield
  constant BITFIELD_SELECT_WIDTH : integer := integer(ceil(log2(real(BITFIELD_WIDTH))));

  -- Tracking state --
  -- The sequence number at the left most bit of the bitfield
  signal base_seqno      : unsigned(15 downto 0);
  -- Note that the bitfield uses `to` rather than `downto`
  subtype bitfield_t is std_logic_vector(0 to MAX_BITFIELD_INDEX);
  signal seqno_bitfield  : bitfield_t;

  -- The number of consecutive set bits at the start of the bitfield.  Limited
  -- to a generic parameter to control:
  --  1) The combinational path associated with counting set bits
  --  2) The combinational path associated with shifting the bitfield when acks
  --     are sent.
  subtype seqno_count_t is integer range 0 to MAX_ACK_COUNT;
  signal seqno_count         : seqno_count_t;

  -- Internal debug signals
  signal count_ack_tracker_total_acks_sent_r     : unsigned(31 downto 0);
  signal count_ack_tracker_tx_acks_sent_r        : unsigned(31 downto 0);
  signal count_ack_tracker_pkts_enqueued_r       : unsigned(31 downto 0);
  signal count_ack_tracker_reject_out_of_range_r : unsigned(31 downto 0);
  signal count_ack_tracker_reject_already_set_r  : unsigned(31 downto 0);
  signal count_ack_tracker_accepted_by_peek_r    : unsigned(31 downto 0);
  signal debug_high_watermark_r                  : unsigned(15 downto 0);

  -- Ensure that the generics make sense.  Do this here to ensure the
  -- assert is checked at elaboration.
  -- This assert works in simulation but when using `opcidev build` a
  -- different error is thrown.
  function verify_generics return boolean is
  begin
    assert
      MAX_ACK_COUNT <= BITFIELD_WIDTH
      report "MAX_ACK_COUNT (" & integer'image(MAX_ACK_COUNT) & ") must be less than or equal to BITFIELD_WIDTH (" & integer'image(BITFIELD_WIDTH) & ")"
      severity failure;
    return true;
  end function;
  constant dummy : boolean := verify_generics;

begin
  -- Count the number of consecutive set bits at the start of the bitfield
  count_sm : process ( seqno_bitfield )
  begin
    seqno_count <= MAX_ACK_COUNT;

    for i in 0 to MAX_ACK_COUNT - 1 loop
        if seqno_bitfield(i) = '0' then
          seqno_count <= i;
          exit;
        end if;
    end loop;

  end process count_sm;

  tx_ackstart <= base_seqno;
  tx_ackcount <= seqno_count;
  tx_ack_req  <= '1' when seqno_count > 0 else '0';

  -- If the bitfield width is larger than the 32 bits assigned to the debug output
  -- the first 32 bits should be used.  If it's smaller, than the remainder is padded
  -- with zeros.
  debug_bitfield_narrow: if BITFIELD_WIDTH >= 32 generate
    debug_bitfield <= seqno_bitfield(0 to 31);
  end generate debug_bitfield_narrow;
  debug_bitfield_wide: if BITFIELD_WIDTH < 32 generate
    debug_bitfield <= seqno_bitfield & (31 - BITFIELD_WIDTH downto 0 => '0');
  end generate debug_bitfield_wide;
  debug_base_seqno   <= std_logic_vector(base_seqno);

  count_ack_tracker_total_acks_sent     <= std_logic_vector(count_ack_tracker_total_acks_sent_r);
  count_ack_tracker_tx_acks_sent        <= std_logic_vector(count_ack_tracker_tx_acks_sent_r);
  count_ack_tracker_pkts_enqueued       <= std_logic_vector(count_ack_tracker_pkts_enqueued_r);
  count_ack_tracker_reject_out_of_range <= std_logic_vector(count_ack_tracker_reject_out_of_range_r);
  count_ack_tracker_reject_already_set  <= std_logic_vector(count_ack_tracker_reject_already_set_r);
  count_ack_tracker_accepted_by_peek    <= std_logic_vector(count_ack_tracker_accepted_by_peek_r);
  debug_high_watermark                  <= std_logic_vector(debug_high_watermark_r);

  tracking_sm : process( clk )
    -- Index into the bitfield for incoming packets
    variable idx : unsigned(BITFIELD_SELECT_WIDTH - 1 downto 0);
    -- Working copy of the bitfield. Updated to handle newly-arrived packet
    -- then transmitted ACKs
    variable temp_seqno_bitfield : bitfield_t;

    -- Test if the seqno is in range.  The difference between the peeked
    -- sequence number and the base sequence number is the index into the
    -- bitfield.  This holds even when: the seqno is below the base; when
    -- the discontinuity between the largest and smallest sequence number is
    -- in the range of the bitfield; or a combination of the two.  This is
    -- because of wrapping subtraction.  When this index is greater than the
    -- bitfield length, the seqno is out of range (it could be above OR below
    -- the bitfield though, again, because of wrapping subtract).
    pure function seqno_in_range(seqno: unsigned(15 downto 0);
                                 base: unsigned(15 downto 0)
                                ) return boolean is
    begin
      return seqno - base <= MAX_BITFIELD_INDEX;
    end function seqno_in_range;

    -- Create an index type because GHDL (correctly) complains if we try to
    -- use this kind of constraint directly as a function return type.
    -- See: https://github.com/ghdl/ghdl/issues/1646
    subtype idx_t is unsigned(BITFIELD_SELECT_WIDTH - 1 downto 0);
    -- Find the index into the bitfield of a sequence number (which is assumed
    -- to be in range)
    pure function find_idx(seqno: unsigned(15 downto 0);
                           base: unsigned(15 downto 0)
                          ) return idx_t is
    begin
      -- The following subtraction works even when the discontinuity between
      -- the largest and smallest sequence number is in the range of the
      -- bitfield because of wrapping subtraction.
      -- We use the `"-"` syntax for subtract so we can select the correct
      -- number of bits from the result.
      return "-"(seqno, base)(BITFIELD_SELECT_WIDTH - 1 downto 0);
    end function find_idx;

    -- Note the restriction on the @by argument to limit the amount by which
    -- we can shift.
    pure function shift_bitfield(temp_seqno_bitfield : bitfield_t;
                                 by                  : seqno_count_t)
                                 return                bitfield_t is
    begin
      return std_logic_vector(unsigned(temp_seqno_bitfield) sll by);
    end function shift_bitfield;

  begin
    if rising_edge(clk) then
      if reset = '1' then

        -- We require that sequence numbers start at zero (modulo the slight
        -- reordering this ack tracker is designed to handle).  Allowing an
        -- arbitrary initial sequence number significantly  increases
        -- implementation complexity for little gain.  We do allow the inital
        -- base sequence number to be set here because it helps with debugging.
        base_seqno <= INIT_BASE_SEQNO;
        seqno_bitfield  <= (others => '0');  -- Initialise bitfield with 0s
        rx_reject       <= '0';
        rx_reject_valid <= '0';

        count_ack_tracker_total_acks_sent_r     <= to_unsigned(0, count_ack_tracker_total_acks_sent_r'length);
        count_ack_tracker_tx_acks_sent_r        <= to_unsigned(0, count_ack_tracker_tx_acks_sent_r'length);
        count_ack_tracker_pkts_enqueued_r       <= to_unsigned(0, count_ack_tracker_pkts_enqueued_r'length);
        count_ack_tracker_reject_out_of_range_r <= to_unsigned(0, count_ack_tracker_reject_out_of_range_r'length);
        count_ack_tracker_reject_already_set_r  <= to_unsigned(0, count_ack_tracker_reject_already_set_r'length);
        count_ack_tracker_accepted_by_peek_r    <= to_unsigned(0, count_ack_tracker_accepted_by_peek_r'length);
        debug_high_watermark_r                  <= to_unsigned(0, debug_high_watermark_r'length);

      else  -- not reset

        -- On any given clock cycle, four things might happen from the outside world:
        --    1) A new packet is received/peeked
        --    2) Acks are transmitted
        --    3) Both (1) and (2)
        --    4) Nothing
        -- We want to deal with (1) and (2) in that order to avoid a long timing path from ACK
        -- transmission to the accept/reject decision. The tradeoff is that we reject a packet which
        -- arrives on the same cycle that an ACK is sent when the bitfield is full.
        -- It is tempting to try to treat (1), (2) and (3) separately, but when we handle (3)
        -- we just find ourselves re-implementing (1) and (2).

        temp_seqno_bitfield := seqno_bitfield;
        idx := find_idx(seqno => rx_frameseq, base => base_seqno);

        if rx_valid = '1' then
          -- Enqueue the packet.  Do not check if it's within the bitfield
          -- range because the caller should have checked this already using
          -- rx_peek.

          -- Find the index into the bitfield and set the bit
          temp_seqno_bitfield(to_integer(idx)) := '1';

          count_ack_tracker_pkts_enqueued_r <= count_ack_tracker_pkts_enqueued_r + 1;
          if idx > debug_high_watermark_r then
            -- idx should be narrower than debug_high_watermark_r for any
            -- reasonable size of bitfield
            debug_high_watermark_r <= (15 - BITFIELD_SELECT_WIDTH downto 0 => '0') & idx;
          end if;
        end if;  -- New packet enqueued

        if rx_peek = '1' then
          rx_reject_valid    <= '1';
          if seqno_in_range(seqno => rx_frameseq, base => base_seqno) then
            -- Find the index into the bitfield and test if the bit is already set
            if seqno_bitfield(to_integer(idx)) = '1' then
              rx_reject                            <= '1';
              count_ack_tracker_reject_already_set_r <= count_ack_tracker_reject_already_set_r + 1;
            else
              -- Implicitely accept packet
              count_ack_tracker_accepted_by_peek_r <= count_ack_tracker_accepted_by_peek_r + 1;
            end if;
          else  -- sequence number not in range so reject
            rx_reject                             <= '1';
            count_ack_tracker_reject_out_of_range_r <= count_ack_tracker_reject_out_of_range_r + 1;
          end if;
        end if;  -- New packet received

        if rx_reject_ready = '1' then
          -- Reset the peek state if the response has been consumed by the caller
          rx_reject_valid <= '0';
          rx_reject       <= '0';
        end if;

        if tx_ack_sent = '1' then
          temp_seqno_bitfield := shift_bitfield(temp_seqno_bitfield, tx_ackcount_sent);
          -- This correctly wraps round to zero when necessary
          base_seqno <= base_seqno + tx_ackcount_sent;

          count_ack_tracker_total_acks_sent_r <= count_ack_tracker_total_acks_sent_r + tx_ackcount_sent;
          count_ack_tracker_tx_acks_sent_r    <= count_ack_tracker_tx_acks_sent_r + 1;
        end if;  -- Acks transmitted

        -- Update registered state
        seqno_bitfield <= temp_seqno_bitfield;

      end if;  -- reset
    end if;  -- clk
  end process ; -- tracking_sm

end rtl ; -- rtl
