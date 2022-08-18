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

-- radix-2 restoring divide algorithm (unsigned)
entity divide is
  generic(
    OPERAND_WIDTH : natural := 16
  );
  port(
    clk : in std_logic;
    reset : in std_logic;

    start : in std_logic;
    dividend : in unsigned(OPERAND_WIDTH - 1 downto 0);
    divisor : in unsigned(OPERAND_WIDTH - 1 downto 0);

    result_valid : out std_logic;
    quotient : out unsigned(OPERAND_WIDTH -1 downto 0);
    remainder : out unsigned(OPERAND_WIDTH -1 downto 0)
  );
end entity;

architecture rtl of divide is
  subtype op_t is unsigned(OPERAND_WIDTH -1 downto 0);

  signal div_r : op_t;
  signal rem_r : op_t;

  signal count : natural range 0 to OPERAND_WIDTH;
begin

  quotient <= div_r;
  remainder <= rem_r;

  process(clk)

    procedure div_step(rem_i, div_i : in op_t) is
      variable rem_v : op_t;
    begin
      rem_v := rem_i(op_t'high - 1 downto 0) & div_i(op_t'high);
      if rem_v < divisor then
        rem_r <= rem_v;
        div_r <= div_i(op_t'high - 1 downto 0) & '0';
      else
        rem_r <= rem_v - divisor;
        div_r <= div_i(op_t'high - 1 downto 0) & '1';
      end if;
    end div_step;

  begin
    if rising_edge(clk) then
      if reset = '1' then
        div_r <= (others => '0');
        rem_r <= (others => '0');
        count <= 0;
        result_valid <= '0';
      else
        if count = 0 then
          if start = '1' then
            result_valid <= '0';
            div_step((others => '0'), dividend);
            count <= 1;
          end if;
        elsif count < OPERAND_WIDTH then
          div_step(rem_r, div_r);
          count <= count + 1;
        else
          count <= 0;
          result_valid <= '1';
        end if;
      end if;
    end if;
  end process;
end architecture;
