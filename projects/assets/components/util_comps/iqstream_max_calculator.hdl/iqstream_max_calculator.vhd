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
library ocpi; use ocpi.types.all; -- remove this to avoid all ocpi name collisions
architecture rtl of worker is

  -- We are locking the data type to the property types in the spec: short_t
  subtype value_t is short_t;
  -- all max values will take this value upon reset - minimum negative value
  constant RESET_VAL_c    : value_t := short_min;
  signal in_I             : value_t := (others => '0');
  signal in_Q             : value_t := (others => '0');
  signal taking_data      : bool_t;
  signal taking_eom       : bool_t; -- unusual EOM-preserving behavior of this worker
  -- registers for volatile properties
  signal max_I_r          : value_t := RESET_VAL_c;
  signal max_Q_r          : value_t := RESET_VAL_c;
  signal max_I_is_valid_r : bool_t  := bfalse;
  signal max_Q_is_valid_r : bool_t  := bfalse;
  -- convert values in the (variable width) data path to our property types
  function to_value(s: std_logic_vector) return value_t is
    variable v : std_logic_vector(value_t'range);
  begin
    if s'length >= value_t'length then
      v := s(s'left downto s'left - (value_t'length - 1));
    else
      v := s & ocpi.util.slv0(value_t'length);
    end if;
    return signed(v);
  end to_value;
begin
  --- property outputs
  props_out.max_I          <= max_I_r;
  props_out.max_Q          <= max_Q_r;
  props_out.max_I_is_valid <= max_I_is_valid_r;
  props_out.max_Q_is_valid <= max_Q_is_valid_r;
  ---------------------------------------------------------------------------------------------
  -- input: take when data is present and either output can be produced or output not connected
  ---------------------------------------------------------------------------------------------
  taking_data <= in_in.valid and (out_in.ready or out_in.reset);
  taking_eom  <= not in_in.valid and in_in.eom and in_in.ready and (out_in.ready or out_in.reset);
  in_out.take <= taking_data or taking_eom;
  -- I is first (and thus LSBs when little endian).  Q is MSBs
  in_I        <= to_value(in_in.data(in_in.data'length/2-1 downto 0));
  in_Q        <= to_value(in_in.data(in_in.data'left downto in_in.data'length/2));

  ------------------------------------------------------------------------------
  -- output: give when taking data and output is connected
  ------------------------------------------------------------------------------
  out_out.eom         <= taking_eom;
  out_out.give        <= taking_eom and not out_in.reset;
  out_out.valid       <= taking_data and not out_in.reset;
  out_out.data        <= in_in.data;
  out_out.byte_enable <= in_in.byte_enable;

  ------------------------------------------------------------------------------
  -- record max_I , max_Q properties and reset them when read
  ------------------------------------------------------------------------------
  max_calc : process(ctl_in.clk)
  begin
    if rising_edge(ctl_in.clk) then
      if ctl_in.reset = '1' then
        max_I_r          <= RESET_VAL_c;
        max_I_is_valid_r <= bfalse;
        max_Q_r          <= RESET_VAL_c;
        max_Q_is_valid_r <= bfalse;
        --debug
      elsif its(taking_data) then
        -- Do not drop a value even if reading the max
        if props_in.max_I_read = '1' or in_I > max_I_r then
          max_I_r <= in_I;
          max_I_is_valid_r <= btrue;
        end if;
        if props_in.max_Q_read = '1' or in_Q > max_Q_r then
          max_Q_r <= in_Q;
          max_Q_is_valid_r <= btrue;
        end if;
      elsif props_in.max_I_read = '1' then -- reading while not taking
        max_I_r          <= RESET_VAL_c;
        max_I_is_valid_r <= bfalse;
      elsif props_in.max_Q_read = '1' then
        max_Q_r          <= RESET_VAL_c;
        max_Q_is_valid_r <= bfalse;
      end if;
    end if;
  end process;
end rtl;
