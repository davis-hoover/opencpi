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

-- TODO/FIXME:  use precise bursts to eliminate buffering when they are there
--              implement both endians

library ieee, ocpi, util;
use ieee.std_logic_1164.all, ieee.numeric_std.all, std.textio.all; 
use ocpi.types.all, ocpi.wci.all, util.util.all;

architecture rtl of worker is
  -- for file I/O and using util.cwd module
  constant pathLength      : natural := props_in.fileName'right;
  signal cwd               : string_t(0 to props_out.cwd'right);
  file   data_file         : char_file_t;
  signal messageLength_r   : ulong_t := (others => '0');
  -- registers driving ctl_out
  signal finished_r        : boolean := false;
  -- registers driving props_out
  signal messagesWritten_r : ulonglong_t := (others => '0');
  signal bytesWritten_r    : ulonglong_t := (others => '0');
  -- register for operating state
  signal operating_r       : boolean; -- have we seen start?
  signal ctl_start         : std_logic;
  signal ctl_release       : std_logic;
  -- control ops synchronized to the wsi clock domain
  signal wsi_start         : std_logic;
  signal wsi_release       : std_logic;
  -- pull a byte out of a dword and convert to char type. FIXME: endian!
  function char(dw : ulong_t; pos : natural) return character is begin
    return to_character(char_t(dw(pos*8+7 downto pos*8)));
  end char;
begin
  -- worker outputs
  ctl_out.finished          <= to_bool(finished_r);
  props_out.cwd             <= cwd;
  props_out.bytesWritten    <= bytesWritten_r; 
  props_out.messagesWritten <= messagesWritten_r;
  in_out.take               <= in_in.ready;

  -- get access to the CWD for pathname resolution (and as a readable property)
  cwd_i : component util.util.cwd
    generic map(length     => cwd'right)
    port    map(cwd        => cwd);

  -- provide start to the data clock domain
  ctl_start <= '1' when not its(ctl_in.reset) and ctl_in.control_op = START_E else '0';
  control_op_is_start_inst : component cdc.cdc.pulse
  generic map(N => 2)
  port map   (src_clk      => ctl_in.clk,
              src_rst      => ctl_in.reset,
              src_in       => ctl_start,
              src_rdy      => open, -- no chance that this will ever not be ready
              dst_clk      => in_in.clk,
              dst_rst      => in_in.reset,
              dst_out      => wsi_start);

  -- provide release to the data clock domain
  ctl_release <= '1' when not its(ctl_in.reset) and ctl_in.control_op = RELEASE_E else '0';
  control_op_is_release_inst : component cdc.cdc.pulse
  generic map(N => 2)
  port map   (src_clk      => ctl_in.clk,
              src_rst      => ctl_in.reset,
              src_in       => ctl_release,
              src_rdy      => open, -- no chance that this will ever not be ready
              dst_clk      => in_in.clk,
              dst_rst      => in_in.reset,
              dst_out      => wsi_release);

  process(in_in.clk)
    variable c              : character;
    variable msg_buffer     : string(1 to 16*1024);
    variable new_msg_length : natural;
  begin
    if rising_edge(in_in.clk) then
      if its(in_in.reset) then
        messageLength_r   <= (others => '0');
        finished_r        <= false;
        messagesWritten_r <= (others => '0');
        bytesWritten_r    <= (others => '0');
        operating_r       <= false;
      elsif its(wsi_release) then -- note this might happen after EOF and finished
        operating_r <= false;
        if not finished_r then
          close_file(data_file, props_in.fileName);
        end if;
      elsif its(wsi_start) and not operating_r then
        assert(not finished_r) severity failure;
        open_file(data_file, cwd, props_in.fileName, write_mode);
        operating_r <= true;
      elsif operating_r and not finished_r then
        -- operating_r <= true; -- make it sticky
        if its(in_in.eof) then
          finished_r <= true;
          close_file(data_file, props_in.fileName);
          report "Output file closed";
        elsif its(in_in.ready) then
          new_msg_length := to_integer(messageLength_r);
          if its(in_in.valid) and in_in.byte_enable /= "0000" then
            -- There is data: either write it directly or put it in the buffer
            for i in 0 to 3 loop
              if in_in.byte_enable(i) = '1' then -- FIXME: endian!
                c := char(ulong_t(in_in.data), i);
                if its(props_in.messagesInFile) then 
                  if new_msg_length >= msg_buffer'length then
                    report "The messagesInFile property is true so messages are being buffered";
                    report "A message is too large for the message buffer";
                    report "new_msg_length is " & integer'image(new_msg_length) severity failure;
                  else
                    msg_buffer(new_msg_length+1) := c;
                  end if;
                else
                  write(data_file, c);
                end if;
                new_msg_length := new_msg_length + 1;
              end if;
            end loop;    
          end if;
          if its(in_in.eom) then
            if its(props_in.messagesInFile) then
              for i in 0 to 3 loop
                write(data_file, char(to_ulong(new_msg_length),i));
              end loop;
              for i in 0 to 3 loop
                write(data_file, char(ulong_t(resize(unsigned(std_logic_vector(in_in.opcode)),
                                                     ulong_t'length)), i));
              end loop;
              for i in 0 to new_msg_length-1 loop
                write(data_file, msg_buffer(i+1));
              end loop;
            end if;
            messagesWritten_r <= messagesWritten_r + 1; -- we count non-EOF ZLMs
            bytesWritten_r <= bytesWritten_r + new_msg_length;
            messageLength_r <= (others => '0');
          else
            messageLength_r <= to_ulong(new_msg_length);
          end if; -- eom
        end if; --if in_in.ready
      end if; -- if operating and not finished
    end if; -- if rising_edge(in_in.clk)
  end process;
end rtl;
