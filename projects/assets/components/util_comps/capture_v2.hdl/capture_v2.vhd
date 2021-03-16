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
-- Capture_v2
-------------------------------------------------------------------------------
--
-- Description:
--
-- The capture_v2 worker provides the ability to store an input port's
-- data. Two modes are supported:
-- * 'leading' - capture all messages from input port until the buffer is full.
-- This has the affect of capturing messages from the start of an application.
-- * 'trailing' - capture all messages from input port and allow the buffer's
-- content to be overwritten while application is in operation. This has the affect
-- of capturing all messages (a buffers worth) near the end of an application.
--
-- This worker provides an optional output port, so that, it may be
-- placed between two workers. The input messages are directly passed to
-- the output port with a latency of the input port clock cycles.
--
-- The capture_v2 worker takes input port messages and stores their data in a
-- buffer via the data property as 4 byte words. Metadata associated with each
-- message is stored as a record in a metadata buffer via the metadata property.
-- It captures four 4 byte words of metadata. The first metadata word is the
-- opcode of the message and message size (bytes); opcode 8 MSB and message
-- size 24 LSB. The second word is the fraction time stamp for the EOM. The
-- third word is the fraction time stamp for the SOM. And the fourth word is
-- the seconds timestamp for the SOM. So that the metadata can be read on a
-- little-endian processor, the ordering of the metadata is as follows:
-- 1) opcode (8-bit) & message size (24-bit)
-- 2) eom fraction (32-bit)
-- 3) som fraction (32-bit)
-- 4) som seconds (32-bit)
--
-- When the number of bytes sent for a message is not a multiple of 4, only the
-- last (number of bytes modulus 4) least significant bytes of the last word
-- in the data buffer represent received data. The (number of bytes modulus 4)
-- most significant bytes will always be zero in the last word in the data
-- buffer.
-- For example, given that last captured data buffer word is 0x0000005a:
-- - if number of bytes is 5, the last data received was 0x5a.
-- - if number of bytes is 6, the last data received was 0x005a.
--
-- The capture_v2 worker counts the number of metadata records (metadataCount)
-- have been captured and how many data words have been captured (dataCount), 
-- and the total number of bytes that were passed through the worker 
-- during an app run (totalBytes). It allows for the option to wrap around and 
-- continue to capture data and metadata once the buffers are full or to stop 
-- capturing data and metadata when the data and metadata buffers are full 
-- via the stoponFull property.
--
-- When stopOnFull is true (leading), data and metadata will be captured as long as
-- the metadata buffer is not full. The data buffer will loop if it is not full
-- and the metadata buffer is not full. The metadata buffer will loop independently
-- until it is not full. When stopOnFull is false (trailing), the data and
-- metadata buffers loop independently. There will be a wrap around when the data
-- and metadata buffers are full and data and metadata will continue to be captured.
--
-- The worker also has properties that keep track of whether or not the
-- metadata and data buffers are full; metaFull and dataFull.
--
-- When using capture_v2.hdl, the totalBytes, metadataCount,  dataCount, metaFull, and
-- dataFull properties should be checked at the end of an app run because they won't 
-- be stable until then. The worker doesn't use cdc crossing circuits for them because 
-- it takes advantage that they will have a stable value by the time the control plane 
-- reads those values at the end of an app run.
--
-- Something to note is that the BRAM2 module that is used to store the data
-- and metadata initializes the BRAM to an initial value of 0xAAAAAAAA
-- (2863311530 in base 10) in simulation. This means at the start of an application,
-- in simulation, the data and metadata properties will have an initial value of
-- 0xAAAAAAAA.

-------------------------------------------------------------------------------
-- TODO - Add a "trigger" capability that will allow the capture of data based on
-- on a condition, i.e, "start capturing when a second zlm has occurred or
-- start capturing when an opcode of 5 has been seen"
-------------------------------------------------------------------------------

library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi; use ocpi.util.all; use ocpi.types.all; -- remove this to avoid all ocpi name collisions
library util; use util.util.all;

architecture rtl of worker is

-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- Signals for capture logic
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
signal s_metadata_count   : ulong_t := (others => '0');
signal s_data_count       : ulong_t := (others => '0');
signal s_metadata_Full    : bool_t  := bfalse;
signal s_data_full        : bool_t := bfalse;
signal s_finished         : std_logic := '0';   -- Used to determine when the worker is finished
signal s_finished_to_ctl  : std_logic := '0';   -- Used to drive ctl_out.finished
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- Signals for combinatorial logic
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
signal s_is_read_r         : std_logic := '0'; -- Register to aid in incrementing the BRAM read side addresses
signal s_out_not_connected : std_logic := '0';
signal s_take              : std_logic := '0';
signal s_give              : std_logic := '0';
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- Data BRAM constants and signals
-- Writing to the BRAM B side and then reading from the BRAM A side
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
constant c_data_memory_depth  : natural := to_integer(numDataWords);
constant c_data_addr_width    : natural := width_for_max(c_data_memory_depth - 1);
constant c_data_bram_dsize    : natural := 32; -- Size in bytes of the data for data bram
signal s_data_bramW_in        : std_logic_vector(c_data_bram_dsize-1 downto 0) := (others => '0');
signal s_data_bramR_addr      : unsigned(c_data_addr_width-1 downto 0) := (others => '0');
signal s_data_bramW_write     : std_logic := '0';
signal s_data_bramR_out       : std_logic_vector(c_data_bram_dsize-1 downto 0) := (others => '0');
signal s_data_bramW_addr      : std_logic_vector(c_data_addr_width-1 downto 0) := (others => '0');
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- Metadata BRAM constants and signals
-- Writing to the BRAM B side and then reading from the BRAM A side
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
constant c_metadata_memory_depth  : natural := to_integer(numRecords);
constant c_metadata_addr_width    : natural := width_for_max(c_metadata_memory_depth - 1);
constant c_metadata_bram_dsize    : natural := 128; -- Size in bytes of the data for metadata bram
signal s_metadata_bramW_in        : std_logic_vector(c_metadata_bram_dsize-1 downto 0) := (others => '0');
signal s_metadata_bramR_out       : std_logic_vector(c_metadata_bram_dsize-1 downto 0) := (others => '0');
alias opcode_and_messageSize      : std_logic_vector(31 downto 0) is s_metadata_bramR_out(127 downto 96);
alias eom_fraction                : std_logic_vector(31 downto 0) is s_metadata_bramR_out(95 downto 64);
alias som_fraction                : std_logic_vector(31 downto 0) is s_metadata_bramR_out(63 downto 32);
alias som_seconds                 : std_logic_vector(31 downto 0) is s_metadata_bramR_out(31 downto 0);
signal s_metadata_bramW_write     : std_logic := '0';
signal s_metadata_bramR_addr      : unsigned(c_metadata_addr_width-1 downto 0) := (others => '0');
signal s_metadata_bramW_addr      : std_logic_vector(c_metadata_addr_width-1 downto 0) := (others => '0');
signal s_metadata_out             : std_logic_vector(31 downto 0) := (others => '0'); -- Used to store metadata words from s_metadata_bramR_out after doing some decoding
constant c_counter_size           : natural := width_for_max(3); -- Size for s_metadata_bramR_ctr. Using 3 as input because number of metadata words-1 (4-1)
signal s_metadata_bramR_ctr       : unsigned(c_counter_size-1 downto 0) := (others => '0'); -- Used for the metadata decoding
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- Mandatory input port logic
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
signal s_ready_for_in_port_data  : std_logic := '0';
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- Mandatory output port logic
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
signal s_data_ready_for_out_port : std_logic := '0';
signal s_out_meta_is_reserved    : std_logic := '0';
signal s_out_som                 : std_logic := '0';
signal s_out_eom                 : std_logic := '0';
signal s_out_valid               : std_logic := '0';

signal s_total_bytes             : ulonglong_t := (others => '0'); -- Total number of bytes sent for entire app run

begin

-- Mandatory input port logic
-- (note that s_ready_for_in_port_data MUST have the same clock latency as the latency
-- between in port's data and any associated output port's data)
in_out.take <= s_take;

s_take <= in_in.ready and s_ready_for_in_port_data; -- this applies backpressure

-- Mandatory output port logic
-- (note that s_data_ready_for_out_port MUST be clock-aligned with out_out.data)
-- (note that reserved messages will be DROPPED ON THE FLOOR)
out_out.give <= s_give;
s_give <= out_in.ready and (not s_out_meta_is_reserved) and s_data_ready_for_out_port;

s_out_meta_is_reserved <= (not s_out_som) and (not s_out_valid) and (not s_out_eom);
out_out.som <= s_out_som;
out_out.eom <= s_out_eom;
out_out.valid <= s_out_valid;

s_out_som <= in_in.som;
s_out_eom <= in_in.eom;
s_out_valid <= in_in.valid;


s_ready_for_in_port_data <= out_in.ready or s_out_not_connected;
s_data_ready_for_out_port <= in_in.ready;

-- When an optional output port is not connected, out_in.reset will always be '1'
s_out_not_connected <= out_in.reset;

out_out.data <= in_in.data;
out_out.byte_enable <= in_in.byte_enable;
out_out.opcode   <= in_in.opcode;

props_out.metadataCount <= s_metadata_count;
props_out.dataCount <= s_data_count;
props_out.totalBytes <= s_total_bytes;
props_out.metaFull <= s_metadata_Full;
props_out.dataFull <= s_data_full;
props_out.raw.done  <= '1';
props_out.raw.error <= '0';

finished_to_ctl: component cdc.cdc.single_bit
  generic map(IREG      => '1',
              RST_LEVEL => '0')
  port map   (src_clk      => in_in.clk,
              src_rst      => in_in.reset,
              src_en       => '1',
              src_in       => s_finished,
              dst_clk      => ctl_in.clk,
              dst_rst      => ctl_in.reset,
              dst_out      => s_finished_to_ctl);

ctl_out.finished  <= s_finished_to_ctl;

capture_inst : entity work.capture_implementation
  generic map (
        numRecords  => to_integer(numRecords),
        numDataWords  => to_integer(numDataWords),
        data_width => c_data_bram_dsize,
        metadata_width  => c_metadata_bram_dsize,
        data_addr_width => c_data_addr_width,
        metadata_addr_width  => c_metadata_addr_width)
  port map (
        stopOnFull            => props_in.stopOnFull,
        stopZLMOpcode         => props_in.stopZLMOpcode,
        stopOnZLM             => props_in.stopOnZLM,
        stopOnEOF             => props_in.stopOnEOF,
        iport_in              => in_in,
        iport_take            => s_take,
        oport_give            => s_give,
        oport_not_connected   => s_out_not_connected,
        itime_in              => time_in,
        captured_data         => s_data_bramW_in,
        captured_metadata     => s_metadata_bramW_in,
        data_bram_write       => s_data_bramW_write,
        metadata_bram_write   => s_metadata_bramW_write,
        data_bram_write_addr  => s_data_bramW_addr,
        metadata_bram_write_addr   => s_metadata_bramW_addr,
        data_count            => s_data_count,
        metadata_count        => s_metadata_count,
        total_bytes           => s_total_bytes,
        data_full             => s_data_full,
        metadata_full         => s_metadata_Full,
        finished              => s_finished);



dataBram : component util.util.BRAM2
generic map(PIPELINED  => 0,
            ADDR_WIDTH => c_data_addr_width,
            DATA_WIDTH => c_data_bram_dsize,
            MEMSIZE    => c_data_memory_depth)
  port map   (CLKA       => ctl_in.clk,
              ENA        => '1',
              WEA        => '0',
              ADDRA      => std_logic_vector(s_data_bramR_addr),
              DIA        => x"00000000",
              DOA        => s_data_bramR_out,
              CLKB       => in_in.clk,
              ENB        => '1',
              WEB        => s_data_bramW_write,
              ADDRB      => s_data_bramW_addr,
              DIB        => s_data_bramW_in,
              DOB        => open);

  metadataBram : component util.util.BRAM2
  generic map(PIPELINED  => 0,
              ADDR_WIDTH => c_metadata_addr_width,
              DATA_WIDTH => c_metadata_bram_dsize,
              MEMSIZE    => c_metadata_memory_depth)
    port map   (CLKA       => ctl_in.clk,
                ENA        => '1',
                WEA        => '0',
                ADDRA      => std_logic_vector(s_metadata_bramR_addr),
                DIA        => x"00000000000000000000000000000000",
                DOA        => s_metadata_bramR_out,
                CLKB       => in_in.clk,
                ENB        => '1',
                WEB        => s_metadata_bramW_write,
                ADDRB      => s_metadata_bramW_addr,
                DIB        => s_metadata_bramW_in,
                DOB        => open);

-- Decode to get each metadata word
s_metadata_out <= opcode_and_messageSize when (s_metadata_bramR_ctr = 0) else
                  eom_fraction when (s_metadata_bramR_ctr = 1) else
                  som_fraction when (s_metadata_bramR_ctr = 2) else
                  som_seconds  when (s_metadata_bramR_ctr = 3) else
                 (others=>'0');

-- Since metadata is the first raw property, assign raw.data to metadata until
-- finished reading out metadata and then assign raw.data to the data.
-- Divide the raw.address by 4 because raw.address increments in steps of 4.
-- Mulitplying numRecords by 4 because there are 4 metadata words.
props_out.raw.data <= s_metadata_out when (to_integer(props_in.raw.address)/4 < 4*numRecords) else s_data_bramR_out;


delay_reg : process (ctl_in.clk)
begin
    if rising_edge(ctl_in.clk) then
      if ctl_in.reset = '1' then
        s_is_read_r <= '0';
      else
        s_is_read_r <= props_in.raw.is_read;
      end if;
    end if;
end process delay_reg;

-- Running counter to keep track of data BRAM reading side address
-- Increments counter when props_in.raw.address/4 >= 4*numRecords because
-- the metadata property is stored in the addresses prior to that
data_bramR_addr_counter : process (ctl_in.clk)
begin
  if rising_edge(ctl_in.clk) then
    if ctl_in.reset = '1' then
      s_data_bramR_addr  <= (others => '0');
    elsif ((to_integer(props_in.raw.address)/4 >= 4*numRecords) and props_in.raw.is_read = '1' and s_is_read_r = '0') then
      if (s_data_bramR_addr = numDataWords-1) then
        s_data_bramR_addr <= (others => '0');
      else
        s_data_bramR_addr <= s_data_bramR_addr + 1;
      end if;
    end if;
  end if;
end process data_bramR_addr_counter;


-- Counter used to decode metadata and to advance s_metadata_bramR_addr
-- Increments counter when props_in.raw.address/4 < 4*numRecords because
-- the metadata property is the first raw property
metadata_bramR_counter : process (ctl_in.clk)
begin
  if rising_edge(ctl_in.clk) then
    if ctl_in.reset = '1' then
      s_metadata_bramR_ctr <= (others => '0');
    -- Using s_is_read_r = '1' because the metadata signal logic relies on s_metadata_bramR_ctr
    -- and metadata signal is driven combinatorially. is_read is on high for 2 clock cycles and since metadata signal is driven combinatorially, s_metadata_bramR_ctr
    -- has to stay the same value until is_read goes low so that the metadata signal's value doesn't change until after is_read goes low.
    elsif ((to_integer(props_in.raw.address)/4 < 4*numRecords) and props_in.raw.is_read = '1' and s_is_read_r = '1') then
          s_metadata_bramR_ctr <= s_metadata_bramR_ctr + 1;
    end if;
  end if;
end process metadata_bramR_counter;

-- Running counter to keep track of metadata BRAM reading side address
-- Increments counter when props_in.raw.address/4 < 4*numRecords because
-- the metadata property is the first raw property
metadata_bramR_addr_counter : process (ctl_in.clk)
begin
  if rising_edge(ctl_in.clk) then
    if ctl_in.reset = '1' then
      s_metadata_bramR_addr  <= (others => '0');
    -- Increment s_metadata_bramR_addr only when ready to read in metadata
    elsif ((to_integer(props_in.raw.address)/4 < 4*numRecords) and props_in.raw.is_read = '1' and s_is_read_r = '0') then
    -- Reset s_metadata_bramR_addr to 0 when on the last metadata word
        if (s_metadata_bramR_addr = numRecords-1 and s_metadata_bramR_ctr = 3) then
          s_metadata_bramR_addr <= (others => '0');
        elsif (s_metadata_bramR_ctr = 3) then
          s_metadata_bramR_addr <= s_metadata_bramR_addr + 1;
        end if;
    end if;
  end if;
end process metadata_bramR_addr_counter;



end rtl;
