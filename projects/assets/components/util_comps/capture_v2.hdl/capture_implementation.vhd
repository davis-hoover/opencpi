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
use work.capture_v2_worker_defs.all;

entity capture_implementation is
  generic(
    numRecords : natural := 256;
    numDataWords : natural := 1024;
    data_width : natural := 32;
    metadata_width  : natural := 128;
    data_addr_width : natural := 10;
    metadata_addr_width : natural := 8);
  port(
    stopOnFull                : in  bool_t;
    stopZLMOpcode             : in  uChar_t;
    stopOnZLM                 : in  bool_t;
    stopOnEOF                 : in  bool_t;
    iport_in                  : in  worker_in_in_t;
    iport_take                : in  std_logic;
    oport_give                : in  std_logic;
    oport_not_connected       : in  std_logic;
    itime_in                  : in  worker_time_in_t;
    captured_data             : out std_logic_vector(data_width-1 downto 0);
    captured_metadata         : out std_logic_vector(metadata_width-1 downto 0);
    data_bram_write           : out std_logic;
    metadata_bram_write       : out std_logic;
    data_bram_write_addr      : out std_logic_vector(data_addr_width-1 downto 0);
    metadata_bram_write_addr  : out std_logic_vector(metadata_addr_width-1 downto 0);
    data_count                : out ulong_t;
    metadata_count            : out ulong_t;
    total_bytes               : out ulonglong_t;
    data_full                 : out bool_t;
    metadata_full             : out bool_t;
    finished                  : out std_logic);
end entity;

architecture rtl of capture_implementation is
  constant num_count_bytes_max_value   : unsigned  := x"FFFF_FFFF_FFFF_FFFF"; -- (2^64)-1
  ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  -- Signals for capture logic
  -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  signal s_metadataCount    : ulong_t := (others => '0');
  signal s_data_count       : ulong_t := (others => '0');
  signal s_metadata_Full    : bool_t := bfalse;
  signal s_data_full        : bool_t := bfalse;
  signal s_bytes            : integer := 0; -- Number of bytes decoded from byte enable
  signal s_total_bytes      : ulonglong_t := (others => '0'); -- Total number of bytes sent for entire app run
  signal s_valid_bytes      : std_logic_vector(31 downto 0) := (others => '0'); -- Valid bytes determined from byte enable
  signal s_messageSize      : unsigned(23 downto 0) := (others => '0'); -- Total number of bytes sent during a message
  signal s_som_seconds      : std_logic_vector(31 downto 0) := (others => '0'); -- Seconds time stamp captured for som
  signal s_som_fraction     : std_logic_vector(31 downto 0) := (others => '0'); -- Fraction time stamp captured for som
  signal s_in_seconds_r     : std_logic_vector(31 downto 0) := (others => '0'); -- Latched value of seconds time stamp captured for som
  signal s_in_fraction_r    : std_logic_vector(31 downto 0) := (others => '0'); -- Latched value of fraction time stamp captured for som
  signal s_finished         : std_logic := '0';   -- Used to determine when the worker is finished
  -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  -- Signals for combinatorial logic
  -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  signal s_data_disable      : std_logic := '0'; -- When stopOnFull is true, used to disable writing to data BRAM when data is full
  signal s_metadata_disable  : std_logic := '0'; -- When stopOnFull is true, used to disable writing to metadata BRAM and data BRAM when metadata is full
  signal s_eom               : std_logic := '0'; -- Used for counting eoms
  signal s_som               : std_logic := '0'; -- Used for counting soms
  signal s_zlm               : std_logic := '0'; -- Used for zlms
  signal s_is_read_r         : std_logic := '0'; -- Register to aid in incrementing the BRAM read side addresses
  signal s_capture_valid     : std_logic := '0'; -- Used to determine if data being captured is valid
  -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  -- Signals for captured data and metadata
  -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  signal s_data              : std_logic_vector(data_width-1 downto 0) := (others => '0');
  signal s_metadata          : std_logic_vector(metadata_width-1 downto 0) := (others => '0');
  -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  -- Signals for BRAM write
  -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  signal s_data_bram_write            : std_logic := '0';
  signal s_data_bram_write_addr       : unsigned(data_addr_width-1 downto 0) := (others => '0');
  signal s_metadata_bram_write        : std_logic := '0';
  signal s_metadata_bram_write_addr   : unsigned(metadata_addr_width-1 downto 0) := (others => '0');

begin

  s_capture_valid <= iport_in.valid and iport_in.ready and iport_take;
  
  s_eom <= iport_in.eom and iport_in.ready and iport_take;
  s_som <= iport_in.som and iport_in.ready and iport_take;
  s_zlm <= iport_in.ready and iport_in.som and iport_in.eom and not iport_in.valid;

  -- If a single cycle single word message or ZLM occurs,
  -- use the non-latched seconds/fraction timestamp,
  -- otherwise use the latched version of the timestamp
  s_som_seconds  <= std_logic_vector(itime_in.seconds)  when (its(s_som and s_eom)) else
                    s_in_seconds_r;
  s_som_fraction <= std_logic_vector(itime_in.fraction) when (its(s_som and s_eom)) else
                    s_in_fraction_r;

  -- What each byte_enable value means in number of bytes
  s_bytes <=  4 when (iport_in.byte_enable(3) = '1' and iport_in.valid = '1') else
              3 when (iport_in.byte_enable(2) = '1' and iport_in.valid = '1') else
              2 when (iport_in.byte_enable(1) = '1' and iport_in.valid = '1') else
              1 when (iport_in.byte_enable(0) = '1' and iport_in.valid = '1') else
              0;

  s_valid_bytes(31 downto 24) <= (others => iport_in.byte_enable(3));
  s_valid_bytes(23 downto 16) <= (others => iport_in.byte_enable(2));
  s_valid_bytes(15 downto  8) <= (others => iport_in.byte_enable(1));
  s_valid_bytes(7 downto  0)  <= (others => iport_in.byte_enable(0));

  -- Data to place into data BRAM
  s_data <= std_logic_vector(iport_in.data and s_valid_bytes);

  -- Metadata to place into metadata BRAM
  s_metadata <= iport_in.opcode &
                std_logic_vector(s_messageSize+s_bytes) &
                std_logic_vector(itime_in.fraction) & s_som_fraction & s_som_seconds;

  -- Write to data BRAM when data is valid, when metadata and
  -- data not full (when stopOnFull = true).
  s_data_bram_write <= s_capture_valid and (not s_data_disable) and (not s_metadata_disable) and (not s_finished);

  -- Write to metadata BRAM when there is an eom. And if stopOnFull is true write when metadata not full.
  s_metadata_bram_write <= s_eom and (not s_metadata_disable) and (not s_finished);
    
  -- Output signals
  captured_data <= s_data;
  captured_metadata <= s_metadata;
  data_bram_write <= s_data_bram_write;
  metadata_bram_write <= s_metadata_bram_write;
  data_bram_write_addr  <= std_logic_vector(s_data_bram_write_addr);
  metadata_bram_write_addr  <= std_logic_vector(s_metadata_bram_write_addr);
  data_count <= s_data_count;
  metadata_count <= s_metadataCount;
  data_full <= s_data_full;
  metadata_full <= s_metadata_Full;
  finished <= s_finished;
  total_bytes <= s_total_bytes;

  -- Latch the timestamp
  timestamp_reg : process(iport_in.clk)
  begin
    if rising_edge(iport_in.clk) then
      if iport_in.reset = '1' then
        s_in_seconds_r <= (others => '0');
        s_in_fraction_r <= (others => '0');
      elsif (s_som = '1') then
        s_in_seconds_r <= std_logic_vector(itime_in.seconds);
        s_in_fraction_r <= std_logic_vector(itime_in.fraction);
      end if;
    end if;
  end process timestamp_reg;

  -- Counts the total number of bytes for a message
  messageSize_counter : process (iport_in.clk)
  begin
    if rising_edge(iport_in.clk) then
      if (iport_in.reset = '1' or s_eom = '1') then
        s_messageSize <= (others =>'0');
      elsif (s_capture_valid = '1' and s_finished = '0') then
          s_messageSize <= s_messageSize + s_bytes;
      end if;
    end if;
  end process messageSize_counter;

  -- Counts the total number of bytes for an entire app run
  total_bytes_counter : process (iport_in.clk)
  begin
    if rising_edge(iport_in.clk) then
      if (iport_in.reset = '1') then
          s_total_bytes <= (others =>'0');
      elsif (s_capture_valid = '1' and s_total_bytes < num_count_bytes_max_value) then
          s_total_bytes <= s_total_bytes + s_bytes;
      end if;
    end if;
  end process total_bytes_counter;

  -- Take data while buffer is in wrapping mode (stopOnFull=false) or
  -- single capture (stopOnFull=true) and data and metadata counts
  -- have not reached their respective maximum.
  data_capture : process (iport_in.clk)
  begin
      if rising_edge(iport_in.clk) then
        if iport_in.reset = '1' then
          s_data_count <= (others => '0');
          s_data_bram_write_addr <= (others => '0');
          s_data_disable <= '0';
        elsif (s_capture_valid = '1' and s_finished = '0') then
            if ((stopOnFull = btrue and (not (s_data_count = numDataWords) and not (s_metadataCount = numRecords))) or stopOnFull = bfalse) then
              s_data_count <= s_data_count + 1;
            end if;
            -- Configured for a single buffer capture
            if (stopOnFull = btrue and not (s_data_count = numDataWords) and not (s_metadataCount = numRecords)) then
              -- Disable writing to data BRAM when data is full
              if (s_data_count = numDataWords-1) then
                s_data_disable <= '1';
              end if;
              s_data_bram_write_addr <= s_data_bram_write_addr + 1;
            else -- Configured for wrap-around buffer capture
              if (s_data_bram_write_addr = numDataWords -1) then
                s_data_bram_write_addr <= (others => '0');
              else
                s_data_bram_write_addr <= s_data_bram_write_addr + 1;
              end if;
            end if;
        end if;
      end if;
  end process data_capture;

  -- Store metadata after each message or if stopOnFull is true store metadata until data full or metadata full
  metadata_capture : process (iport_in.clk)
  begin
    if rising_edge(iport_in.clk) then
      if iport_in.reset = '1' then
        s_metadataCount <= (others => '0');
        s_metadata_bram_write_addr <= (others => '0');
        s_metadata_disable <= '0';
      elsif (s_eom = '1' and s_finished = '0') then
          if ((stopOnFull = btrue and not (s_metadataCount = numRecords)) or stopOnFull = bfalse) then
            s_metadataCount <= s_metadataCount + 1;
          end if;
          -- Configured for a single buffer capture
          if (stopOnFull = btrue and not (s_metadataCount = numRecords)) then
            -- Disable writing to metadata and data BRAMs when metadata is full
            if (s_metadataCount = numRecords-1) then
              s_metadata_disable <= '1';
            end if;
            s_metadata_bram_write_addr <= s_metadata_bram_write_addr + 1;
          else -- Configured for wrap-around buffer capture
            if (s_metadata_bram_write_addr = numRecords-1)  then
              s_metadata_bram_write_addr <= (others => '0');
            else
              s_metadata_bram_write_addr <= s_metadata_bram_write_addr + 1;
            end if;
          end if;
      end if;
    end if;
  end process metadata_capture;

  -- Sticky-bit full flags for data and metadata buffers
  buffer_full : process (iport_in.clk)
  begin
    if rising_edge(iport_in.clk) then
      if iport_in.reset = '1' then
        s_data_full <= bfalse;
        s_metadata_Full <= bfalse;
      else
        if (s_data_count = numDataWords) then
          s_data_full <= btrue;
        end if;
        if (s_metadataCount = numRecords) then
          s_metadata_Full <= btrue;
        end if;
      end if;
    end if;
  end process buffer_full;
  
  -- Determines when the worker is finished.
  -- For stopOnEOF, if there is a EOF and stopOnEOF is true then set finished to true.
  -- For stopOnZLM, if there is a ZLM and has been GIVEN (if output connected),
  -- the input opcode is equal to stopZLMOpcode, and stopOnZLM is true then set finished to true.
  finish : process (iport_in.clk)
    begin
        if rising_edge(iport_in.clk) then
          if (iport_in.reset = '1') then
            s_finished <= '0';
          elsif ((iport_in.eof = '1' and stopOnEOF = btrue) or
                ((oport_give = '1' or oport_not_connected = '1') and
                (s_zlm = '1' and to_uchar(iport_in.opcode) = stopZLMOpcode and stopOnZLM = btrue))) then
            s_finished <= '1';
          end if;
        end if;
  end process finish;

end rtl;
