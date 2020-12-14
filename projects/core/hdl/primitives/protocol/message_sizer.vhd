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
library ocpi;
library util;

-- sizes messages by counting gives
-- TODO / FIXME - include mechanism for assessment of port buffer size
entity message_sizer is
  generic(
    SIZE_BIT_WIDTH : positive);
  port(
    clk                    : in  std_logic;
    rst                    : in  std_logic;
    give                   : in  ocpi.types.Bool_t;
    message_size_num_gives : in  unsigned(SIZE_BIT_WIDTH-1 downto 0);
    som                    : out ocpi.types.Bool_t;
    eom                    : out ocpi.types.Bool_t);
end entity message_sizer;
architecture rtl of message_sizer is
  signal eom_s            : std_logic := '0';
  signal give_counter_rst : std_logic := '0';
  signal give_counter_cnt : unsigned(SIZE_BIT_WIDTH-1 downto 0) := (others => '0');
begin

  eom_s <= '1' when (give_counter_cnt = message_size_num_gives-1 and give = '1') else '0';
  give_counter_rst <= rst or eom_s;

  give_counter : util.util.counter
    generic map(
      BIT_WIDTH => SIZE_BIT_WIDTH)
    port map(
      clk => clk,
      rst => give_counter_rst,
      en  => give,
      cnt => give_counter_cnt);

  som <= ocpi.types.btrue when (give_counter_cnt = 0 and give = '1') else ocpi.types.bfalse;
  eom <= eom_s;

end rtl;
