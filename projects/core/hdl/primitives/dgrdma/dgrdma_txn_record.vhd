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

entity dgrdma_txn_record is
  generic(
    MAX_TXNS_IN_FLIGHT : natural := 64
  );
  port(
    clk : in std_logic;
    reset : in std_logic;

    -- from frame parser
    rx_txn_valid : in std_logic;
    rx_txn_ready : out std_logic;
    rx_txn_id : in std_logic_vector(31 downto 0);
    rx_msgs_in_txn : in unsigned(15 downto 0);
    rx_flag_addr : in std_logic_vector(23 downto 0);
    rx_flag_data : in std_logic_vector(31 downto 0);

    -- to control plane
    flag_addr : out std_logic_vector(23 downto 0);
    flag_data : out std_logic_vector(31 downto 0);
    flag_valid : out std_logic;
    flag_take : in std_logic;

    -- debug outputs
    txn_id_out_of_range_count : out unsigned(15 downto 0);
    txn_error_count : out unsigned(15 downto 0)
  );
end entity;

architecture rtl of dgrdma_txn_record is
  function clog2(size : positive) return natural is
    variable size_i : natural;  -- can be zero
    variable result : natural;
  begin
    result := 0;
    size_i := size - 1;
    while size_i /= 0 loop
      size_i := size_i / 2;
      result := result + 1;
    end loop;

    return result;
  end clog2;

  -- calculate the carry out from the addition a + b (assumes a'length >= b'length)
  function check_carry(a : unsigned; b : unsigned) return std_logic is
    variable add_result : unsigned(a'length downto 0);
  begin
    add_result := ('0' & a) + ('0' & b);
    return add_result(add_result'left);
  end check_carry;

  -- RAM record structure
  -- Transaction metadata is stored in a 2-port RAM, which is used as a circular buffer.
  -- * Read/write port: addressed by update_ptr; used to update records when a message is received
  -- * Read port: addressed by next_flag_ptr; used to generate flag writes when the earliest transaction is complete
  --
  -- next_flag_ptr sets the base address of the circular buffer; it always points at the record for transaction
  -- next_flag_txn_id. Both of these fields are incremented when a flag write is sent.
  --
  -- The update state machine runs every time a message is received, and stores the transaction metadata into the
  -- appropriate address in the RAM (base + (txn_id - base_txn_id)). msgs_remaining tracks how many messages are
  -- needed to complete this transaction. When a message is received:
  --  * if there is a valid record for this transaction, msgs_remaining is decremented; if it reaches zero
  --    complete is set, allowing the flag write to be sent
  --  * otherwise, a record is written using the header metadata to populate the fields of the record
  --
  -- Record validity is tracked using the wrap_count field and the wrap_count global register. This is essentially
  -- an epoch counter. The flag write state machine considers a record valid if its wrap_count is equal to the
  -- global wrap_count, which is toggled every time the next_flag_ptr wraps around (and the update state machine
  -- needs to keep track of pointer wrapping accordingly to calculate the 'valid' state). The advantage of this over
  -- tracking validity explicity is that it simplifies the addressing logic around the RAM; a record is invalidated
  -- simply by incrementing next_flag_ptr past it (since the next time next_flag_ptr is pointing at it, the global
  -- wrap_count will have changed) and we don't need to adjust any other state. This means the flag write state
  -- machine doesn't need to write into the RAM, so we can use a distributed dual-port RAM where the second port is
  -- read-only
  type txn_entry_t is record
    wrap_count : std_logic;
    complete : std_logic;
    msgs_remaining : unsigned(15 downto 0);
    flag_addr : std_logic_vector(23 downto 0);
    flag_data : std_logic_vector(31 downto 0);
  end record txn_entry_t;

  -- Vivado can't synthesize a record array to RAM so define functions to pack/unpack into a std_logic_vector
  subtype txn_entry_packed_t is std_logic_vector(73 downto 0);
  function pack_txn_entry(rec : txn_entry_t) return txn_entry_packed_t is
  begin
    return rec.wrap_count & rec.complete & std_logic_vector(rec.msgs_remaining) & rec.flag_addr & rec.flag_data;
  end pack_txn_entry;
  function unpack_txn_entry(packed : txn_entry_packed_t) return txn_entry_t is
    variable result : txn_entry_t;
  begin
    result.flag_data := packed(31 downto 0);
    result.flag_addr := packed(55 downto 32);
    result.msgs_remaining := unsigned(packed(71 downto 56));
    result.complete := packed(72);
    result.wrap_count := packed(73);
    return result;
  end unpack_txn_entry;

  -- Initial RAM contents. Initialize entry.wrap_count to 1; wrap_count register resets to zero
  -- so this marks the entry as invalid
  constant NULL_ENTRY : txn_entry_t := (
    wrap_count => '1',
    complete => '0',
    msgs_remaining => to_unsigned(0, 16),
    others => (others => '0'));

  -- Transaction RAM. This is implemented as a dual-port LUTRAM
  -- 2 7-series LUTs are needed to implement up to a 64x1 dual-port RAM, so MAX_TXNS_IN_FLIGHT should generally be a multiple of 64
  type txn_ram_t is array (natural range <>) of txn_entry_packed_t;
  subtype txn_ptr_t is unsigned(clog2(MAX_TXNS_IN_FLIGHT)-1 downto 0);

  -- RAM Port A: flag send
  signal next_flag_ptr : txn_ptr_t;
  signal next_flag_txn_id : unsigned(31 downto 0);
  signal next_flag_txn : txn_entry_t;
  signal txn_ram : txn_ram_t(0 to MAX_TXNS_IN_FLIGHT - 1);
  signal wrap_count : std_logic;

  -- RAM Port B: update entry when message is received
  type update_state_t is (S_IDLE, S_ERROR, S_READ, S_WRITE);
  signal clearing_ram : boolean;
  signal update_state : update_state_t;
  signal update_ptr : txn_ptr_t;
  signal update_wrap_count : std_logic;
  signal update_txn : txn_entry_t;

  -- Internal signals
  signal flag_valid_r : std_logic;
  signal txn_id_out_of_range_count_r : unsigned(15 downto 0);
  signal txn_error_count_r : unsigned(15 downto 0);
begin
  flag_valid <= flag_valid_r;
  txn_id_out_of_range_count <= txn_id_out_of_range_count_r;
  txn_error_count <= txn_error_count_r;
  with update_state select rx_txn_ready <=
    '1' when S_WRITE | S_ERROR,
    '0' when others;

  txn_record_proc : process(clk)
    variable update_ram_index : unsigned(31 downto 0);
    variable entry_to_write : txn_entry_t;
  begin
    if rising_edge(clk) then
      if reset = '1' then
        wrap_count <= '0';

        next_flag_ptr <= to_unsigned(0, next_flag_ptr'length);
        next_flag_txn_id <= to_unsigned(1, next_flag_txn_id'length);
        next_flag_txn <= NULL_ENTRY;
        flag_valid_r <= '0';
        flag_addr <= (others => '0');
        flag_data <= (others => '0');

        update_ptr <= to_unsigned(0, next_flag_ptr'length);
        txn_id_out_of_range_count_r <= to_unsigned(0, txn_id_out_of_range_count_r'length);
        txn_error_count_r <= to_unsigned(0, txn_error_count_r'length);
        clearing_ram <= true;
        update_state <= S_IDLE;
      elsif clearing_ram then
          txn_ram(to_integer(update_ptr)) <= pack_txn_entry(NULL_ENTRY);
          update_ptr <= update_ptr + 1;
          if update_ptr + 1 = 0 then
            clearing_ram <= false;
          end if;
      else
        -- Flag write state machine: send flag if base transaction is valid and complete
        next_flag_txn <= unpack_txn_entry(txn_ram(to_integer(next_flag_ptr)));
        if flag_take = '1' or flag_valid_r = '0' then
          flag_addr <= next_flag_txn.flag_addr;
          flag_data <= next_flag_txn.flag_data;
          if next_flag_txn.wrap_count = wrap_count and next_flag_txn.complete = '1' then
            flag_valid_r <= '1';
            next_flag_ptr <= next_flag_ptr + 1;
            next_flag_txn_id <= next_flag_txn_id + 1;
            wrap_count <= wrap_count xor check_carry(next_flag_ptr, to_unsigned(1, next_flag_ptr'length));
          else
            flag_valid_r <= '0';
          end if;
        end if;

        -- Update state machine: read-modify-write transaction record when a message is received
        case update_state is
          when S_IDLE =>
            if rx_txn_valid = '1' then
              update_ram_index := unsigned(rx_txn_id) - unsigned(next_flag_txn_id);
              if update_ram_index < to_unsigned(MAX_TXNS_IN_FLIGHT, 32) then
                update_state <= S_READ;
                update_ptr <= next_flag_ptr + update_ram_index(next_flag_ptr'left downto 0);
                update_wrap_count <= wrap_count xor check_carry(next_flag_ptr, update_ram_index(next_flag_ptr'left downto 0));
              else
                update_state <= S_ERROR;
                report "Out-of-range transaction ID " & integer'image(to_integer(unsigned(rx_txn_id))) &
                       " (next_flag_txn_id=" & integer'image(to_integer(unsigned(next_flag_txn_id))) & ")"
                       severity warning;
                if txn_id_out_of_range_count_r /= txn_id_out_of_range_count_r'high then
                  txn_id_out_of_range_count_r <= txn_id_out_of_range_count_r + 1;
                end if;
              end if;
            end if;

          when S_ERROR =>
            update_state <= S_IDLE;

          when S_READ =>
            update_txn <= unpack_txn_entry(txn_ram(to_integer(update_ptr)));
            update_state <= S_WRITE;

          when S_WRITE =>
            update_state <= S_IDLE;
            if update_txn.wrap_count = update_wrap_count then
              -- Existing transaction: decrement remaining message and set complete flag if it reaches zero
              entry_to_write := update_txn;

              -- log unexpected message to an existing transaction
              if update_txn.msgs_remaining = 0 or update_txn.flag_addr /= rx_flag_addr or update_txn.flag_data /= rx_flag_data then
                report "Unexpected message to transaction ID " & integer'image(to_integer(unsigned(rx_txn_id))) severity warning;
                if txn_error_count_r /= txn_error_count_r'high then
                  txn_error_count_r <= txn_error_count_r + 1;
                end if;
              end if;

              if update_txn.msgs_remaining = 1 then
                entry_to_write.msgs_remaining := update_txn.msgs_remaining - 1;
                entry_to_write.complete := '1';
              else
                entry_to_write.msgs_remaining := update_txn.msgs_remaining - 1;
              end if;
            else
              -- New transaction
              entry_to_write.wrap_count := update_wrap_count;
              entry_to_write.flag_addr := rx_flag_addr;
              entry_to_write.flag_data := rx_flag_data;
              if rx_msgs_in_txn > 1 then
                entry_to_write.msgs_remaining := rx_msgs_in_txn - 1;
                entry_to_write.complete := '0';
              else
                entry_to_write.msgs_remaining := to_unsigned(0, 16);
                entry_to_write.complete := '1';
              end if;
            end if;

            txn_ram(to_integer(update_ptr)) <= pack_txn_entry(entry_to_write);
        end case;
      end if;
    end if;
  end process txn_record_proc;
end rtl;
