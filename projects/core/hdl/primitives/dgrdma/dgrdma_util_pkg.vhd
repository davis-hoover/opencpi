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
library ocpi; use ocpi.types.all;
use std.textio.all;

package dgrdma_util is
  function swap_bytes(s : std_logic_vector) return std_logic_vector;

  function data_width_for_sdp(sdp_width : natural) return natural;
  function keep_width_for_sdp(sdp_width : natural) return natural;
  function pack_sdp_data(sdp_words : dword_array_t) return std_logic_vector;
  function unpack_sdp_data(sdp_data : std_logic_vector) return dword_array_t;
  function minimum(left, right: integer) return integer;
end dgrdma_util;

package body dgrdma_util is
  function swap_bytes(s : std_logic_vector) return std_logic_vector is
    variable n : natural;
    variable result : std_logic_vector(s'length - 1 downto 0);
  begin
    n := s'length / 8;
    for i in 0 to n - 1 loop
      result((i+1)*8-1 downto i*8) := s(s'low + (n-i)*8-1 downto s'low + (n-i-1)*8);
    end loop;
    return result;
  end swap_bytes;

  function data_width_for_sdp(sdp_width : natural) return natural is
    begin
      return sdp_width * 32;
    end function data_width_for_sdp;

    function keep_width_for_sdp(sdp_width : natural) return natural is
    begin
      return sdp_width * 4;
    end function keep_width_for_sdp;

    function pack_sdp_data(sdp_words : dword_array_t) return std_logic_vector is
      variable result : std_logic_vector((32*sdp_words'length)-1 downto 0);
    begin
      for i in 0 to sdp_words'length - 1 loop
        result(i*32+31 downto i*32) := std_logic_vector'(sdp_words(i));
      end loop;
      return result;
    end pack_sdp_data;

    function unpack_sdp_data(sdp_data : std_logic_vector) return dword_array_t is
      variable result : dword_array_t(0 to (sdp_data'length/32)-1);
    begin
      for i in 0 to (sdp_data'length/32)-1 loop
        result(i) := dword_t'(sdp_data(i*32+31 downto i*32));
      end loop;
      return result;
    end unpack_sdp_data;

    function minimum(left, right: integer) return integer is
    begin
      if left < right then
        return left;
      else
        return right;
      end if;
    end;
end dgrdma_util;
