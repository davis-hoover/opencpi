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


-------------------------------------------------------------------------------
-- Pattern_v2
-------------------------------------------------------------------------------
--
-- Description:
--
-- The pattern v2 component provides the ability to output a pattern of messages
-- by allowing the user to create a record of messages each having a configurable
-- number of bytes and associated 8 bit opcode. Through a set of properties, the
-- component may send messages (data and opcode) up to the amount dictated by
-- the build-time parameters. The messages property defines the record of messages
-- to send, as well as, defines the number of data bytes and an opcode for each
-- message.
--
-- For example:
-- When messages = {4, 255}, one message will be sent having 4
-- bytes of data and an opcode of 255. When messages = {8, 251}, {6, 250}, two
-- messages will be sent, the first having 8 bytes of data and an opcode of 251,
-- and the second message having 6 bytes of data and an opcode of 250.
--
-- Data to be sent with a message is defined by the data property and is referred
-- to as the data buffer. The number of data words in the data buffer is the
-- number of data bytes for the messages. The component offers an additional
-- feature when there are multiple messages via the dataRepeat property which
-- indicates whether the a message starts at the beginning of the data buffer,
-- or continues from its current index within the buffer.
--
-- For example:
-- Given messages = {4, 251},{8, 252},{12, 253},{16, 254},{20, 255}
--
-- If dataRepeat = true, then numDataWords is 5. To calculate the numDataWords
-- when dataRepeat is true, divide the largest message size (in bytes) by 4.
-- Dividing by four required because the data is output as a 4 byte data
-- word. Since the largest message size in the given messages assignment is 20,
-- 20/4 = 5. 
-- 
-- When numDataWords = 5, then a valid data assignment would be
-- data = {0, 1, 2, 3, 4}, and the data within each
-- message would look like: msg1 = {0}, msg2 = {0, 1}, msg3 = {0, 1, 2},
-- msg4 = {0, 1, 2, 3}, msg5 = {0, 1, 2, 3, 4}
-- 
-- If dataRepeat = false, then numDataWords is 15. To calculate the numDataWords
-- when dataRepeat is false, divide the sum of all the message sizes (in bytes) 
-- by 4. Dividing by four is required because the data is output as a 4 byte 
-- data word. Since the sum of all message sizes in the given messages assignment 
-- is (4+8+12+16+20)/4 = 15. 
-- 
-- When numDataWords = 15, then a valid data assignment 
-- would be data = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14},
-- and the data within each message would look like:
-- msg1 = {0}, msg2 = {1, 2}, msg3 = {3, 4, 5}, msg4 = {6, 7, 8, 9},
-- msg5 = {10, 11, 12, 13, 14}
-- 
-- There is also a messagesToSend property that sets the number of messages to send 
-- and decrements as the messages are sent. When dataRepeat is true, 
-- messagesToSend > numMessagesMax, and at the end of the messages buffer, the messages 
-- buffer wraps around and starts at the beginning of the messages buffer. When dataRepeat 
-- is false, this value must be less than or equal to numMessagesMax. The worker will 
-- check for this and report an error if messagesToSend is greater than numMessagesMax. 
-- The error checking for the HDL worker only happens in simulation. 
--
-- When using pattern_v2.hdl, the messagesToSend, messagesSent, and dataSent properties should 
-- be checked at the end of an app run because they won't be stable until then. The worker doesn't 
-- use cdc crossing circuits for them because it takes advantage that they will have a stable value 
-- by the time the control plane reads those values at the end of an app run.

-------------------------------------------------------------------------------

library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi; use ocpi.util.all; use ocpi.types.all; use ocpi.wci.all;
library util; use util.util.all;

architecture rtl of worker is

-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- Signals for pattern logic
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
signal s_byte_enable                          : std_logic_vector(3 downto 0) := (others => '0');
signal s_opcode                               : std_logic_vector(7 downto 0) := (others => '0');
signal s_bytes_left                           : ulong_t := (others => '0'); -- Keep track of how many bytes that are left to send for current message
signal s_messagesToSend                       : ulong_t := (others => '0');
signal s_dataSent                             : ulong_t := (others => '0');
signal s_messagesSent                         : ulong_t := (others => '0');
signal s_start                                : std_logic := '0';
signal s_start_r                              : std_logic := '0';   -- reg for the start operation
signal s_wsi_start_op                         : std_logic := '0';   -- Used to to start sending messages
signal s_finished                             : std_logic := '0';   -- Used to to stop sending messages
signal s_finished_to_ctl                      : std_logic := '0';   -- Used to to stop sending messages
signal s_src_rdy                              : std_logic;
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- Signals for combinatorial logic
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
signal s_som                 : std_logic := '0'; -- Used to drive s_out_som
signal s_eom                 : std_logic := '0'; -- Used to drive s_out_eom
signal s_ready               : std_logic := '0'; -- Used to determine if ready to send message data
signal s_valid               : std_logic := '0'; -- Used for combinatorial logic for out_valid
signal s_give                : std_logic := '0'; -- Used for combinatorial logic for out_valid
signal s_data_valid          : std_logic := '0';
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- Data BRAM constants and signals
-- Writing to the BRAM B side and then reading from the BRAM A side
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
constant c_data_memory_depth  : natural := to_integer(numDataWords);
constant c_data_addr_width    : natural := width_for_max(c_data_memory_depth - 1);
constant c_data_bram_dsize    : natural := 32; -- Size in bytes of the data for data bram
signal s_data_bramW_in        : std_logic_vector(c_data_bram_dsize-1 downto 0) := (others => '0');
signal s_data_bramW_write     : std_logic := '0';
signal s_data_bramR_out       : std_logic_vector(c_data_bram_dsize-1 downto 0) := (others => '0');
signal s_data_addr            : unsigned(c_data_addr_width-1 downto 0) := (others => '0');
signal s_data_bramR_addr      : unsigned(c_data_addr_width-1 downto 0) := (others => '0');
signal s_data_bramW_addr      : unsigned(c_data_addr_width-1 downto 0) := (others => '0');
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- Messages BRAM constants and signals
-- Writing to the BRAM B side and then reading from the BRAM A side
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
constant c_messages_memory_depth  : natural := to_integer(numMessagesMax);
constant c_messages_addr_width    : natural := width_for_max(c_messages_memory_depth - 1);
constant c_messages_bram_dsize    : natural := 40; -- Size in bytes of the data for messages bram
constant c_counter_size           : natural := width_for_max(1); -- Size in bytes for messages_bramR_ctr
signal s_messages_bramW_in        : std_logic_vector(c_messages_bram_dsize-1 downto 0) := (others => '0');
signal s_messages_bramR_out       : std_logic_vector(c_messages_bram_dsize-1 downto 0) := (others => '0');
alias messages_bram_bytes         : std_logic_vector(31 downto 0) is s_messages_bramR_out(39 downto 8);
alias messages_bram_opcode        : std_logic_vector(7 downto 0) is s_messages_bramR_out(7 downto 0);
signal s_messages_bramW_write     : std_logic := '0';
signal s_messages_bramR_addr      : unsigned(c_messages_addr_width-1 downto 0) := (others => '0');
signal s_messages_bramW_addr      : unsigned(c_messages_addr_width-1 downto 0) := (others => '0');
signal s_messages_bramW_ctr       : unsigned(c_counter_size-1 downto 0) := (others => '0'); -- Used for the messages_bramW_addr_counter process
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- Counter to control Data and Messages BRAM write signals
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
constant c_bramW_ctr_size           : natural := width_for_max(to_integer(numMessagesMax + numDataWords));
signal s_bramW_ctr                  : unsigned(c_bramW_ctr_size-1 downto 0) := (others => '0');
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- Mandatory output port logic
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
signal s_data_ready_for_out_port : std_logic := '0';
signal s_out_meta_is_reserved    : std_logic := '0';
signal s_out_som                 : std_logic := '0';
signal s_out_eom                 : std_logic := '0';
signal s_out_valid               : std_logic := '0';
signal s_out_eof                 : std_logic := '0';

begin
  
  -- Register for the start operation 
  start_reg : process (ctl_in.clk)
    begin
      if rising_edge(ctl_in.clk) then
        if ctl_in.reset = '1' then
          s_start_r  <= '0';
        else
          -- The start op may not be on long enough to be captured
          -- and synchronized so register it
          if ctl_in.control_op = START_e then
            s_start_r <= '1';
          end if;
          -- Set the register to 0 once the src_rdy signal goes high
          if s_src_rdy and s_start_r then
            s_start_r <= '0';
          end if;
        end if;
      end if;
    end process start_reg;
  
  s_start <= s_start_r when (s_src_rdy = '1') else '0';

  control_op_is_start_inst : component cdc.cdc.pulse
    generic map(N => 2)
    port map   (src_clk      => ctl_in.clk,
                src_rst      => ctl_in.reset,
                src_in       => s_start,
                src_rdy      => s_src_rdy,
                dst_clk      => out_in.clk,
                dst_rst      => out_in.reset,
                dst_out      => s_wsi_start_op);

  props_out.messagesToSend <= props_in.messagesToSend when ctl_in.state = INITIALIZED_e else
                              s_messagesToSend;

  props_out.messagesSent <= s_messagesSent;
  props_out.dataSent <= s_dataSent;

  -- Mandatory output port logic, (note that
  -- s_data_ready_for_out_port MUST be clock-aligned with out_out.data)
  -- (note that reserved messages will be DROPPED ON THE FLOOR)
  out_out.give <= s_give;

  s_give <= out_in.ready and (not s_out_meta_is_reserved) and s_data_ready_for_out_port;


  s_out_meta_is_reserved <= (not s_out_som) and (not s_out_valid) and (not s_out_eom);
  out_out.som   <= s_out_som;
  out_out.eom   <= s_out_eom;
  out_out.valid <= s_out_valid;
  out_out.eof <= s_out_eof;

  s_out_som <= s_som;

  s_out_eom <= s_eom;

  s_out_valid <= out_in.ready and s_data_ready_for_out_port and s_valid;

  s_data_ready_for_out_port <= s_ready;

  out_out.data <= s_data_bramR_out;
  out_out.byte_enable <= s_byte_enable;
  out_out.opcode <= s_opcode;


  finished_to_ctl: component cdc.cdc.single_bit
    generic map(IREG      => '1',
                RST_LEVEL => '0')
    port map   (src_clk      => out_in.clk,
                src_rst      => out_in.reset,
                src_en       => '1',
                src_in       => s_finished,
                dst_clk      => ctl_in.clk,
                dst_rst      => ctl_in.reset,
                dst_out      => s_finished_to_ctl);

  ctl_out.finished <= s_finished_to_ctl;

  pattern_inst : entity work.pattern_implementation
  generic map(
    numDataWords =>to_integer(numDataWords),
    numMessagesMax =>to_integer(numMessagesMax),
    data_width => c_data_bram_dsize,
    messages_width  => c_messages_bram_dsize,
    data_addr_width => c_data_addr_width,
    messages_addr_width => c_messages_addr_width)
  port map(
    dataRepeat                =>   props_in.dataRepeat,
    messagesToSend_in         =>   props_in.messagesToSend,
    oport_in                  =>   out_in,
    wsi_start_op              =>  s_wsi_start_op,
    data_valid                =>  s_data_valid,
    messages_bram_bytes       =>  messages_bram_bytes,
    messages_bram_opcode      =>  messages_bram_opcode,
    som                       =>  s_som,
    eom                       =>  s_eom,
    valid                     =>  s_valid,
    ready                     =>  s_ready,
    opcode_out                =>  s_opcode,
    byte_enable               =>  s_byte_enable,
    eof                       =>  s_out_eof,
    messages_bram_read_addr   =>  s_messages_bramR_addr,
    data_addr                 =>  s_data_addr,
    dataSent                  =>  s_dataSent,
    messagesToSend_out        =>  s_messagesToSend,
    messagesSent              =>  s_messagesSent,
    finished                  =>  s_finished);

  -- Data is ready to send
  s_data_valid <= out_in.ready and s_out_valid and not (s_finished);

  props_out.raw.done  <= '1';
  props_out.raw.error <= '0';

  s_data_bramW_in <= std_logic_vector(props_in.raw.data);

  -- Write to data BRAM when data
  s_data_bramW_write <= '1' when (to_integer(props_in.raw.address)/4 >= 2*numMessagesMax and props_in.raw.is_write ='1') else '0';

  -- Write to messages BRAM when
  s_messages_bramW_write <= '1' when (to_integer(props_in.raw.address)/4 < 2*numMessagesMax and props_in.raw.is_write ='1') else '0';

  s_data_bramR_addr <= (others => '0') when (s_data_valid = '1' and props_in.dataRepeat = '1' and s_eom = '1') else
                       s_data_addr + 1  when(s_data_valid = '1' and s_data_addr < numDataWords-1)   else
                       s_data_addr;


  dataBram : component util.util.BRAM2
  generic map(PIPELINED  => 0,
              ADDR_WIDTH => c_data_addr_width,
              DATA_WIDTH => c_data_bram_dsize,
              MEMSIZE    => c_data_memory_depth)
    port map   (CLKA       => out_in.clk,
                ENA        => '1',
                WEA        => '0',
                ADDRA      => std_logic_vector(s_data_bramR_addr),
                DIA        => x"00000000",
                DOA        => s_data_bramR_out,
                CLKB       => ctl_in.clk,
                ENB        => '1',
                WEB        => s_data_bramW_write,
                ADDRB      => std_logic_vector(s_data_bramW_addr),
                DIB        => s_data_bramW_in,
                DOB        => open);

    messagesBram : component util.util.BRAM2
    generic map(PIPELINED  => 0,
                ADDR_WIDTH => c_messages_addr_width,
                DATA_WIDTH => c_messages_bram_dsize,
                MEMSIZE    => c_messages_memory_depth)
      port map   (CLKA       => out_in.clk,
                  ENA        => '1',
                  WEA        => '0',
                  ADDRA      => std_logic_vector(s_messages_bramR_addr),
                  DIA        => x"0000000000",
                  DOA        => s_messages_bramR_out,
                  CLKB       => ctl_in.clk,
                  ENB        => '1',
                  WEB        => s_messages_bramW_write,
                  ADDRB      => std_logic_vector(s_messages_bramW_addr),
                  DIB        => s_messages_bramW_in,
                  DOB        => open);

  -- Running counter to keep track of data BRAM write side address
  data_bramW_addr_counter : process (ctl_in.clk)
  begin
    if rising_edge(ctl_in.clk) then
      if ctl_in.reset = '1' then
        s_data_bramW_addr  <= (others => '0');
      -- Increment s_data_bramW_addr only when ready to write to data BRAM
      elsif ((to_integer(props_in.raw.address)/4 >= 2*numMessagesMax) and props_in.raw.is_write = '1') then
        if (s_data_bramW_addr = numDataWords-1) then
          s_data_bramW_addr <= (others => '0');
        else
          s_data_bramW_addr <= s_data_bramW_addr + 1;
        end if;
      end if;
    end if;
  end process data_bramW_addr_counter;


  -- Counter used to decode messages and to advance s_messages_bramW_addr
  messages_bramW_counter : process (ctl_in.clk)
  begin
    if rising_edge(ctl_in.clk) then
      if ctl_in.reset = '1' then
        s_messages_bramW_ctr <= (others => '0');
      -- Increment s_messages_bramW_ctr only when ready to write to messages BRAM
      elsif ((to_integer(props_in.raw.address)/4 < 2*numMessagesMax) and props_in.raw.is_write = '1') then
            s_messages_bramW_ctr <= s_messages_bramW_ctr + 1;
      end if;
    end if;
  end process messages_bramW_counter;

  -- Running counter to keep track of messages BRAM writing side address
  messages_bramW_addr_counter : process (ctl_in.clk)
  begin
    if rising_edge(ctl_in.clk) then
      if ctl_in.reset = '1' then
        s_messages_bramW_addr  <= (others => '0');
      -- Increment s_messages_bramW_addr only when ready to write to messages BRAM
      elsif ((to_integer(props_in.raw.address)/4 < 2*numMessagesMax) and props_in.raw.is_write = '1') then
      -- Reset s_messages_bramW_addr to 0 when on the second messages field
          if (s_messages_bramW_addr = numMessagesMax-1 and s_messages_bramW_ctr = 1) then
            s_messages_bramW_addr <= (others => '0');
          elsif (s_messages_bramW_ctr = 1) then
            s_messages_bramW_addr <= s_messages_bramW_addr + 1;
          end if;
      end if;
    end if;
  end process messages_bramW_addr_counter;

  -- Encode messages fields
  messages_encoder : process (ctl_in.clk)
  begin
    if rising_edge(ctl_in.clk) then
      if ctl_in.reset = '1' then
        s_messages_bramW_in  <= (others => '0');
      elsif ((to_integer(props_in.raw.address)/4 < 2*numMessagesMax)) then
        if (s_messages_bramW_ctr = 0) then
          -- message bytes
          s_messages_bramW_in(39 downto 8) <= props_in.raw.data;
        elsif (s_messages_bramW_ctr = 1) then
          -- message opcode
          s_messages_bramW_in(7 downto 0) <= std_logic_vector(resize(unsigned(props_in.raw.data), s_opcode'length));
        end if;
      end if;
    end if;
  end process messages_encoder;

end rtl;
