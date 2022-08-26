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
library ocpi; use ocpi.all; use ocpi.types.all;
package body wci is

-- convert byte enables to byte offsets

function decode_access(input : in_t) return access_t is
  variable cmd : ocpi.ocp.MCmd_t;
begin
  if input.MReset_n = '0' then
    cmd := ocpi.ocp.MCmd_IDLE;
  else         
    cmd := input.MCmd;
  end if;
  case cmd is
    when ocpi.ocp.MCmd_WRITE => if input.MAddrSpace(0) = '1' then return write_e; else return Error_e; end if;
    when ocpi.ocp.MCmd_READ  => if input.MAddrSpace(0) = '1' then return Read_e; else return Control_e; end if;
    when others => return None_e;
  end case;
end decode_access;

--function "=" (l,r: Property_Io_t) return boolean is begin
--  return Property_io_t'pos(l) = Property_io_t'pos(r);
--end "=";
-- return property access specific to this offset and size and address width
-- the basic decode is redundant across properties, but should be optimized anyawy
--function decode_property (input : in_t; low, high : unsigned) return property_access_t is
--  variable io : property_io_t := config_access(input);
--  variable moffset : unsigned (low'left downto 0)
--    := unsigned(input.MAddr(low'left downto 2) & be2offset(input));
--begin
--  if io /= None_e and moffset >= low and moffset <= high then
--    return property_access_t'(io, moffset - low);
--  end if;
--  return property_access_t'(None_e, property_offset_t'(others => '0'));
--end decode_property;

--function get_value(input : in_t; boffset : unsigned; width : natural) return std_logic_vector is
--  variable bitoffset : natural := to_integer(boffset & "000");
--  variable bitwidth  : natural := width;
--begin
--  if bitwidth > 32 then bitwidth := 32; end if;
--  return input.MData(bitoffset + bitwidth - 1 downto bitoffset);
--end get_value;     

function to_control_op(bits : std_logic_vector(2 downto 0)) return control_op_t is
begin
--this fine in VHDL, but not in XST
--return control_op_t'val(to_integer(unsigned(bits)));
  case to_integer(unsigned(bits)) is
    when control_op_t'pos(initialize_e)   => return initialize_e;
    when control_op_t'pos(start_e)        => return start_e;
    when control_op_t'pos(stop_e)         => return stop_e;
    when control_op_t'pos(release_e)      => return release_e;
    when control_op_t'pos(before_query_e) => return before_query_e;
    when control_op_t'pos(after_config_e) => return after_config_e;
    when control_op_t'pos(test_e)         => return test_e;
    when others                           => return no_op_e;
  end case;
--return start_e; --to_unsigned(2,3); --unsigned(bits);
--  case unsigned(bits) is
--    when initialize_e   => return initialize_e;
--    when start_e        => return start_e;
--    when stop_e         => return stop_e;
--    when release_e      => return release_e;
--    when before_query_e => return before_query_e;
--    when after_config_e => return after_config_e;
--    when test_e         => return test_e;
--    when others         => return no_op_e;
--  end case;
end to_control_op;

---- How wide should the data path be from the decoder to the property
--function data_top (property : property_t;
--                   byte_offset : byte_offset_t)-- v5 xst can't do it := to_unsigned(0,byte_offset_t'length))
--  return bit_offset_t is
--begin
--  if property.data_width >= 32 then
--    return 31;
--  elsif property.nitems > 1 then
--    return property.data_width - 1;
--  else
--    return (property.data_width - 1) + (to_integer(byte_offset) * 8);
--  end if;
--end data_top;

function resize(bits : std_logic_vector; n : natural) return std_logic_vector is begin
  return std_logic_vector(resize(unsigned(bits),n));
end resize;

  -- convert state enum value to state number
  -- because at least isim is broken and does not implement the "pos" function
  function get_state_pos(input: state_t) return natural is
  begin
    case input is
      when exists_e => return 0;
      when initialized_e => return 1;
      when operating_e => return 2;
      when suspended_e => return 3;
      when finished_e => return 4;
      when unusable_e => return 5;
    end case;
  end get_state_pos;
  -- convert control op enum value to a number
  -- because at least isim is broken and does not implement the "pos" function
  function get_op_pos(input: control_op_t) return natural is
  begin
    case input is
      when initialize_e   => return 0;
      when start_e        => return 1;
      when stop_e         => return 2;
      when release_e      => return 3;
      when before_query_e => return 4;
      when after_config_e => return 5;
      when test_e         => return 6;
      when no_op_e        => return 7;
    end case;
  end get_op_pos;

end package body wci;

