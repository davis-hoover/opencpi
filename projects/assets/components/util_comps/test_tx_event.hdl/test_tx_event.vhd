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

library IEEE; use IEEE.std_logic_1164.all, ieee.numeric_std.all;
library ocpi; use ocpi.types.all;
architecture rtl of worker is
  signal opcode_bit     : bool_t;
  signal ctr            : ulong_t;
  signal assert_eof     : bool_t;
begin
  event_out_out.give   <= event_out_in.ready and to_bool(ctr = props_in.max_count_value-1);
  event_out_out.opcode <= tx_event_txOn_op_e when its(opcode_bit) else tx_event_txOff_op_e;
  event_out_out.eof    <= assert_eof;
  props_out.opcode_bit <= opcode_bit;

  work : process(ctl_in.clk)
  begin
    if rising_edge(ctl_in.clk) then
      if its(ctl_in.reset) then
        ctr        <= (others => '0');
        assert_eof <= bfalse;
        opcode_bit <= bfalse;
      elsif its(event_out_in.ready) then
        if its(props_in.assert_eof) then
          assert_eof <= btrue;
        elsif ctr = props_in.max_count_value-1 then
          ctr <= (others => '0');
          opcode_bit <= not opcode_bit;
        else
          ctr <= ctr +1;
        end if;
      end if;
    end if;
  end process;
end architecture;
