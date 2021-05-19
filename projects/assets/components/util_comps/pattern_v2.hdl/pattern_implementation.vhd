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
library ocpi; use ocpi.util.all; use ocpi.types.all; -- remove this to avoid all ocpi name collisions
library util; use util.util.all;
library work;
use work.pattern_v2_worker_defs.all;

entity pattern_implementation is
  generic(
    numDataWords : natural := 15;
    numMessagesMax : natural := 5;
    data_width : natural := 32;
    messages_width  : natural := 40;
    data_addr_width : natural := 4;
    messages_addr_width : natural := 5);
  port(
    dataRepeat                : in   bool_t;
    messagesToSend_in         : in   uLong_t;
    oport_in                  : in   worker_out_in_t;
    wsi_start_op              : in  std_logic;
    data_valid                : in   std_logic;
    messages_bram_bytes       : in   std_logic_vector(31 downto 0);
    messages_bram_opcode      : in   std_logic_vector(7 downto 0);
    som                       : out  std_logic;
    eom                       : out  std_logic;
    valid                     : out  std_logic;
    ready                     : out  std_logic;
    opcode_out                : out  std_logic_vector(7 downto 0);
    byte_enable               : out  std_logic_vector(3 downto 0);
    eof                       : out  std_logic;
    messages_bram_read_addr   : out  unsigned(messages_addr_width-1 downto 0);
    data_addr                 : out  unsigned(data_addr_width-1 downto 0);
    dataSent                  : out  ulong_t;
    messagesToSend_out        : out  ulong_t;
    messagesSent              : out  ulong_t;
    finished                  : out  std_logic);
end entity;

architecture rtl of pattern_implementation is
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- Signals for pattern logic
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
signal s_byte_enable          : std_logic_vector(3 downto 0) := (others => '0');
signal s_opcode               : std_logic_vector(7 downto 0) := (others => '0');
signal s_bytes_left           : ulong_t := (others => '0'); -- Keep track of how many bytes that are left to send for current message
signal s_messagesToSend       : ulong_t := (others => '0');
signal s_dataSent             : ulong_t := (others => '0');
signal s_messagesSent         : ulong_t := (others => '0');
signal s_finished_r           : std_logic := '0';   -- Used to to stop sending messages
signal s_keep_repeating_r     : std_logic := '0';   -- If messagesToSend > numMessagesMax and dataRepeat is true, it is used to to keep 
                                                    -- repeating until messagesToSend = 0
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- Signals for combinatorial logic
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
signal s_som_r               : std_logic := '0'; -- Used to drive s_out_som
signal s_som_next_r          : std_logic := '0'; -- Used for logic for starting a message
signal s_eom_r               : std_logic := '0'; -- Used to drive s_out_eom
signal s_ready_r             : std_logic := '0'; -- Used to determine if ready to send message data
signal s_valid_r             : std_logic := '0'; -- Used for combinatorial logic for out_valid
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- Data BRAM constants and signals
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
signal s_data_addr               : unsigned(data_addr_width-1 downto 0) := (others => '0');
signal s_messages_bram_read_addr : unsigned(messages_addr_width-1 downto 0) := (others => '0');
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- Mandatory output port logic
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
signal s_out_eof                 : std_logic := '0';

-- Signal for when the working is operating
signal operating         : std_logic;
-- Register for the operating state
signal operating_r       : std_logic;

-- Takes in the argument bytes_left and outputs the appropriate byte_enable
function read_bytes (bytes_left : ulong_t) return std_logic_vector is
    variable v_result : std_logic_vector(3 downto 0) := (others => '0');
    begin
        if bytes_left >= 4 then
           v_result := "1111";
        elsif bytes_left = 3 then
           v_result := "0111";
        elsif bytes_left = 2 then
           v_result := "0011";
        elsif bytes_left = 1 then
           v_result := "0001";
        elsif bytes_left = 0 then
           v_result := (others => '0');
        end if;
        return v_result;
 end function read_bytes;

begin

  -- Output signals
  som                       <= s_som_r;
  eom                       <= s_eom_r;
  valid                     <= s_valid_r;
  ready                     <= s_ready_r;
  opcode_out                <= s_opcode;
  byte_enable               <= s_byte_enable;
  eof                       <= s_out_eof;
  messages_bram_read_addr   <= s_messages_bram_read_addr;
  data_addr                 <= s_data_addr;
  dataSent                  <= s_dataSent;
  messagesToSend_out        <= s_messagesToSend;
  messagesSent              <= s_messagesSent;
  finished                  <= s_finished_r;
  
  operating <= operating_r or oport_in.ready;

  -- This process handles the logic for the byte enable, opcode, som, eom, valid, and give for the
  -- current message. It handles decrementing the messagesToSend counter, incrementing the
  -- messages_bramR_addr and the messages s_messagesSent counter. It also handles when
  -- the worker should stop sending messages
  message_logic : process(oport_in.clk)
  begin
    if rising_edge(oport_in.clk) then
      if oport_in.reset = '1' then
        s_bytes_left  <= (others => '0');
        s_byte_enable  <= (others => '0');
        s_opcode <= (others => '0');
        s_ready_r <= '0';
        s_eom_r <=  '0';
        s_som_r <= '0';
        s_som_next_r <= '0';
        s_valid_r <= '0';
        s_messagesToSend <= (others => '0');
        s_finished_r <= '0';
        s_messagesSent <= (others => '0');
        s_out_eof <= '0';
        s_messages_bram_read_addr <= (others => '0');
        s_keep_repeating_r <= '0';
      -- Grab the value of messagesToSend once it gets its initial value
      elsif (wsi_start_op = '1') then
        s_messagesToSend <= messagesToSend_in;
        if (messagesToSend_in > numMessagesMax and dataRepeat = '1') then
          s_keep_repeating_r <= '1';
        -- Report an error if messagesToSend is greater than numMessagesMax
        elsif (messagesToSend_in > numMessagesMax and dataRepeat = '0') then
          report "messagesToSend is greater than numMessagesMax. messagesToSend must be less than or equal to numMessagesMax" severity failure;
        end if;
      elsif (operating = '1' and s_out_eof = '0' and oport_in.ready = '1') then
          operating_r <= '1'; -- make it sticky
          s_som_r <= s_som_next_r;
          if s_eom_r = '1' then
              s_ready_r <= '0';
          end if;
          -- No more messages to send. Send an eof
          if s_messagesToSend = 0 then
              s_byte_enable <= (others=>'0');
              s_opcode <= (others=>'0');
              s_som_r <= '0';
              s_eom_r <= '0';
              s_ready_r <= '1';
              s_valid_r <= '0';
              s_out_eof <= '1';
          -- Starting a message
          elsif (s_bytes_left = 0 and s_som_next_r = '0') then
              s_eom_r<= '0';
              s_som_next_r <= '1';
              s_bytes_left <= to_ulong(messages_bram_bytes);
              s_opcode <= messages_bram_opcode;
              s_byte_enable <= read_bytes(to_ulong(messages_bram_bytes));
              -- Wrap around to beggining of messages buffer if keep repeating is true
              if (s_keep_repeating_r = '1' and s_messages_bram_read_addr =  numMessagesMax-1) then
                s_messages_bram_read_addr <= (others=>'0');
              elsif (s_messages_bram_read_addr <  numMessagesMax-1) then
                s_messages_bram_read_addr <= s_messages_bram_read_addr + 1;
              end if;
          -- Handle sending a message that is a ZLM
          elsif (s_bytes_left = 0 and s_som_next_r = '1') then
              s_som_next_r <= '0';
              s_byte_enable <= (others=>'0');
              s_eom_r <= '1';
              s_ready_r <= '1';
              s_valid_r <= '0';
              s_messagesToSend <= s_messagesToSend - 1;
              s_messagesSent <=  s_messagesSent + 1;
          -- Keep track of how many bytes are left for the current message and set byte enable
          elsif (s_bytes_left > 4) then
              s_som_next_r <= '0';
              s_bytes_left <= s_bytes_left - 4;
              s_byte_enable <= (others => '1');
              s_ready_r <= '1';
              s_valid_r <= '1';
          -- At the end of the message
          elsif (s_bytes_left <= 4) then
              s_som_next_r <= '0';
              s_bytes_left <= (others=>'0');
              s_ready_r <= '1';
              s_valid_r <= '1';
              s_eom_r <= '1';
              s_messagesToSend <= s_messagesToSend - 1;
              s_byte_enable <= read_bytes(s_bytes_left);
              s_messagesSent <=  s_messagesSent + 1;
          end if;
      -- Set set finished high and s_ready_r low after EOF is sent
      elsif (s_out_eof = '1') then
          s_finished_r <= '1';
          s_ready_r <= '0';
      end if;
    end if;
  end process;

  -- The process handles incrementing the data address and s_dataSent counter
  data_logic : process(oport_in.clk)
  begin
      if rising_edge(oport_in.clk) then
        if oport_in.reset = '1' then
          s_data_addr <= (others => '0');
          s_dataSent <= (others => '0');
        elsif (data_valid = '1') then
          s_dataSent <= s_dataSent + 1;
          if (dataRepeat = '1' and s_eom_r = '1') then
              s_data_addr <= (others => '0');
          elsif (s_data_addr < numDataWords-1) then
              s_data_addr <= s_data_addr + 1;
          end if;
        end if;
      end if;
  end process;
end rtl;
