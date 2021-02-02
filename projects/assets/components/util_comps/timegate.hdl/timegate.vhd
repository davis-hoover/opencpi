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

library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi; use ocpi.types.all, ocpi.wci.all, ocpi.util.all;
library cdc; use cdc.cdc.all;
architecture rtl of worker is
  constant time_width_c        : natural := ulonglong_t'length;
  constant nchunks_c           : natural := max(in_in.data'length, time_width_c)/in_in.data'length;
  -- The time gate state machine
  type state_t is (open_e,         -- gate is open, samples are flowing
                   time_coming_e,  -- time is coming in chunks, not yet complete
                   time_waiting_e, -- time has arrived and we are waiting
                   error_e);       -- things are broken, protocol is erroneous, we're stuck
  signal state_r               : state_t;
  -- The fifo from input port (and clock) to output port (and clock)
  signal fifo_in, fifo_out     : std_logic_vector(in_in.data'length + 3 - 1 downto 0);
  signal fifo_in_encoded_bits  : std_logic_vector(1 downto 0);
  signal fifo_enq, fifo_deq    : bool_t;
  signal fifo_empty_n          : bool_t;
  signal fifo_full_n           : bool_t;
  signal fifo_out_data         : std_logic_vector(in_in.data'range); -- LSBs
  signal fifo_out_encoded_bits : std_logic_vector(1 downto 0); -- MSBs
  signal fifo_out_is_time      : bool_t;
  signal fifo_out_is_eof       : bool_t;
  signal fifo_out_is_samples   : bool_t;
  signal fifo_out_is_eom       : bool_t;
  signal fifo_out_is_flush     : bool_t;
  -- Timekeepping - mostly reading time in chunks if data port is narrower than time
  signal time_to_transmit_r    : ulonglong_t; -- the corrected time when transmit should be enabled
  signal time_now              : ulonglong_t;
  signal time_chunk_idx_r      : unsigned(width_for_max(nchunks_c-1)-1 downto 0);
  signal time_chunks           : unsigned(ulonglong_t'length - in_in.data'length-1 downto 0);
  function set_array_length(nchunks, in_data_length, time_width : natural) return natural
  is begin
    if in_data_length < time_width then
      return nchunks-2;
    else
      return 0;
    end if;
  end function;
  type chunks_t is array (0 to set_array_length(nchunks_c, in_in.data'length, time_width_c)) of unsigned(in_in.data'range);
  signal time_chunks_r         : chunks_t;
  -- convenience
  signal good_opcode           : bool_t;
  -- output port signals
  signal som                   : bool_t;
  signal eom                   : bool_t;
  signal valid                 : bool_t;
  signal give                  : bool_t;
  -- status signals
  signal error_r               : bool_t;
  signal time_late_r           : bool_t;    -- timestamp arrived after its time
  signal clr_late_time_sticky  : bool_t;
  signal time_delta            : ulonglong_t;

begin
  -- TODO: Implement ignore_time_stamps
  
  props_out.actual_time_to_requested_time_delta <= time_delta;
  good_opcode <= to_bool(in_in.opcode = ComplexShortWithMetadata_samples_op_e or
                         in_in.opcode = ComplexShortWithMetadata_time_op_e or 
                         in_in.opcode = ComplexShortWithMetadata_flush_op_e);
  time_now    <= time_in.seconds & time_in.fraction;
  -- input port outputs, using input port input clock
  in_out.take   <= fifo_full_n or not good_opcode;
  -- Fifo uses MSB to capture time, samples, and flush opcode. Other opcodes are not put in fifo
  fifo_in_encoded_bits <= "00" when (its(in_in.eof)) else
                          "01" when (in_in.opcode = ComplexShortWithMetadata_samples_op_e) else
                          "10" when (in_in.opcode = ComplexShortWithMetadata_time_op_e) else
                          "11" when (in_in.opcode = ComplexShortWithMetadata_flush_op_e) else 
                          "01";

  fifo_in               <= fifo_in_encoded_bits & in_in.eom & in_in.data;
  fifo_out_data         <= fifo_out(in_in.data'range);
  fifo_out_encoded_bits <= fifo_out(fifo_out'left downto fifo_out'left-1);
  fifo_out_is_eom       <= to_bool(fifo_out(fifo_out'left-2));
  fifo_out_is_eof       <= to_bool(fifo_out_encoded_bits = "00");
  fifo_out_is_samples   <= to_bool(fifo_out_encoded_bits = "01");
  fifo_out_is_time      <= to_bool(fifo_out_encoded_bits = "10");
  fifo_out_is_flush     <= to_bool(fifo_out_encoded_bits = "11");
  fifo_enq              <= fifo_full_n and ((in_in.ready and good_opcode) or in_in.eof);
  fifo_deq              <= to_bool(fifo_empty_n and not its(fifo_out_is_eof) and out_in.ready and
                                  (state_r = open_e or fifo_out_is_time));

  -- output port outputs, just putting out data when appropriate
  som <= fifo_out_is_flush and fifo_empty_n;
  eom <= ((fifo_out_is_eom and fifo_out_is_samples) or fifo_out_is_flush) and fifo_empty_n; -- Propogate eom if samples message. This is done so that
                                                                                            -- the eom prior to flush happens at the correct time. Also
                                                                                            -- drive eom if flush occurs 
  valid <= to_bool(state_r = open_e and fifo_empty_n and not its(fifo_out_is_time) and
                   not its(fifo_out_is_eof) and not its(fifo_out_is_flush));
  give <= (som or eom or valid) and out_in.ready;
  
  out_out.data   <= fifo_out_data;
  out_out.som    <= som;
  out_out.eom    <= eom;
  out_out.eof    <= fifo_out_is_eof and fifo_empty_n;
  out_out.valid  <= valid;
  out_out.give   <= give;
  out_out.opcode <= ComplexShortWithMetadata_flush_op_e when (its(fifo_out_is_flush))  else
                    ComplexShortWithMetadata_samples_op_e;
  
  ctl_out.attention <= error_r;
  ctl_out.error <= to_bool((ctl_in.control_op = START_e) and
                   its(props_in.force_error_on_invalid_time_at_start) and
                   its(time_in.valid));

  fifo : cdc.cdc.fifo
    generic map(
      WIDTH       => in_in.data'length + 3, -- MSB is encoded bits
      DEPTH       => to_integer(CDC_FIFO_DEPTH))
    port map(
      src_CLK     => in_in.clk,
      src_RST     => in_in.reset,
      src_ENQ     => fifo_enq,
      src_in      => fifo_in,
      src_FULL_N  => fifo_full_n,
      dst_CLK     => out_in.clk,
      dst_DEQ     => fifo_deq,
      dst_out     => fifo_out,
      dst_EMPTY_N => fifo_empty_n);

  
  -- Handles making time_late sticky and clearing the sticky bit if 
  -- props_in.clr_late_time_sticky is true
  clr_late_time_sticky  <= props_in.clr_late_time_sticky_written and 
                           props_in.clr_late_time_sticky and 
                           ctl_in.is_operating;
  time_late : component cdc.cdc.fast_pulse_to_slow_sticky
  port map(
    fast_clk    => out_in.clk,
    fast_rst    => out_in.reset,
    fast_pulse  => time_late_r,
    slow_clk    => ctl_in.clk,
    slow_rst    => ctl_in.reset,
    slow_sticky => props_out.late_time_sticky,
    slow_clr    => clr_late_time_sticky);
  
  -- Handles setting time_late_r
  time_late_reg : process (out_in.clk)
  begin
      if rising_edge(out_in.clk) then
        if its(out_in.reset) then
          time_late_r <= bfalse;
        else
          if its(time_late_r) then
            time_late_r <= bfalse;
          end if;
          if state_r = time_waiting_e and time_now >= time_to_transmit_r then
            if time_now > time_to_transmit_r then
              time_late_r <= btrue;
            end if;
          end if;
        end if;
      end if;
  end process time_late_reg;

  notchunked: -- simpler version when time is not chunked
  if in_in.data'length >= time_width_c generate
    g0 : process(out_in.clk)
    begin
      if rising_edge(out_in.clk) then 
        if its(out_in.reset) then
          error_r     <= bfalse;
          state_r     <= open_e; -- gate is initially open
          time_delta  <= (others => '0');
        elsif its(fifo_empty_n) then
          if its(fifo_out_is_time) then
            time_to_transmit_r <= unsigned(fifo_out_data(time_width_c-1 downto 0))
                                  - props_in.time_correction;
            state_r <= time_waiting_e;
          elsif state_r = time_coming_e then -- data opcode
            state_r <= error_e; 
          elsif state_r = time_waiting_e and time_now >= time_to_transmit_r then
            state_r <= open_e;
            time_delta <= time_now - time_to_transmit_r;
          elsif state_r = error_e then -- non-time opcode when waiting for time chunks
            error_r <= btrue;
          end if;
        end if;
      end if;
    end process; -- end of process
  end generate;

  chunked: -- more complicated when time arrives in chunks
  if in_in.data'length < time_width_c generate
    g1: for i in 0 to nchunks_c - 2 generate
      time_chunks((i+1) * in_in.data'length-1 downto i*in_in.data'length) <= time_chunks_r(i);
    end generate;
    -- Clocked process in the output port's clock domain
    -- The state machine between getting time, waiting for time, and passing samples
    input_chunked : process(out_in.clk)
    begin
      if rising_edge(out_in.clk) then 
        if its(out_in.reset) then
          error_r     <= bfalse;
          state_r     <= open_e; -- gate is initially open
          time_delta  <= (others => '0');
        elsif its(fifo_empty_n)  then
          if its(fifo_out_is_time) then -- time opcode
            if state_r = open_e or state_r = time_waiting_e then
              time_chunks_r(0) <= unsigned(fifo_out_data);
              state_r <= time_coming_e;
              time_chunk_idx_r <= to_unsigned(1, time_chunk_idx_r'length);
            elsif state_r = time_coming_e then -- never will happen if width >= time_width
              if time_chunk_idx_r = to_unsigned(nchunks_c - 1, time_chunk_idx_r'length) then
                time_to_transmit_r <= (unsigned(fifo_out_data) & time_chunks) - props_in.time_correction;
                state_r <= time_waiting_e;
              else
                time_chunks_r(to_integer(time_chunk_idx_r)) <= unsigned(fifo_out_data);
                time_chunk_idx_r <= time_chunk_idx_r + 1;
              end if;
            end if;
          elsif state_r = time_coming_e then -- data opcode
            state_r <= error_e; 
          elsif state_r = time_waiting_e and time_now >= time_to_transmit_r then
            state_r <= open_e;
            time_delta <= time_now - time_to_transmit_r;
          elsif state_r = error_e then -- non-time opcode when waiting for time chunks
            error_r <= btrue;
          end if;
        end if;    -- end of fifo not empty
      end if;
    end process; -- end of process
  end generate;
end rtl;
