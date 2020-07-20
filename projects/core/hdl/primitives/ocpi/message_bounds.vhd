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

-- per-property decoder - purely combinatorial
-- result is write_enable, offset-in-array, and aligned data output
library ieee; use ieee.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi; use ocpi.all; use ocpi.types.all; use ocpi.util.all;

entity message_bounds is
  generic(width     : natural);
  port(Clk          : in std_logic;
       RST          : in bool_t;
       -- input side interface
       som_in       : in  bool_t;
       valid_in     : in  bool_t;
       eom_in       : in  bool_t;
       take_in      : out bool_t; -- input side is taking the input from the input port
       -- core facing signals
       core_out     : in  bool_t; -- output side has a valid value
       core_ready   : in  bool_t;
       core_enable  : out bool_t;
       -- output side interface
       ready_out    : in  bool_t; -- output side may produce
       som_out      : out bool_t;
       eom_out      : out bool_t;
       valid_out    : out bool_t;
       give_out     : out bool_t);
end entity message_bounds;

library ocpi_core_bsv; use ocpi_core_bsv.all;
architecture rtl of message_bounds is
  signal in_count_r  : unsigned(width-1 downto 0);
  signal out_count_r : unsigned(width-1 downto 0);
  -- input side of counter fifo
  signal fifo_in     : unsigned(width-1 downto 0);
  signal fifo_enq    : bool_t;                     -- load input counter into fifo
  -- output side of counter fifo
  signal fifo_deq    : bool_t;
  signal fifo_count  : unsigned(width-1 downto 0);
  signal fifo_eom    : bool_t;                     -- fifo has valid count
  signal fifo_ready  : bool_t;
  signal my_take     : bool_t;
  signal my_core_enable : bool_t;
  signal my_reset_n     : bool_t;
  signal zero_count : bool_t;
  signal fifo_out   : std_logic_vector(width-1 downto 0);
--  for myfifo : FIFO2 use entity bsv.FIFO2;
begin
  fifo_count <= unsigned(fifo_out);
  zero_count <= to_bool(fifo_ready and fifo_count = 0);
  -- som is first data or when empty message
  som_out <= to_bool(out_count_r = 1 and (core_out or (its(fifo_eom) and zero_count)));
  -- eom is last data or when empty message
  fifo_deq <= to_bool(its(fifo_eom) and ready_out and
                      ((core_out and out_count_r = fifo_count) or zero_count));
  eom_out <= fifo_deq;
  -- data is always sent since we can't hold it back
  valid_out <= core_out;
  give_out <= core_out or fifo_deq;
  fifo_enq <= eom_in and my_take; -- this should only happen if our mbu_is_ready
  fifo_in  <= in_count_r + 1 when valid_in and my_take else in_count_r;              

  -- decide when the core can have its input enabled to take data
  my_core_enable <= ready_out and valid_in and core_ready and (not eom_in or fifo_ready);
  core_enable <= my_core_enable;
  -- decide when we can take from the input port
  my_take <= my_core_enable or (not valid_in and (som_in or (fifo_ready and eom_in)));
  take_in <= my_take;
  my_reset_n <= not RST; -- for old vhdl
  
  myfifo : bsv_pkg.FIFO2
    generic map(width           => width)
    port    map(clk             => clk,
                rst             => my_reset_n,
                d_in            => std_logic_vector(fifo_in),
                enq             => fifo_enq,
                full_n          => fifo_ready,
                d_out           => fifo_out,
                deq             => fifo_deq,
                empty_n         => fifo_eom,
                clr             => '0');
  process(clk) is
  begin
    -- som_out and eom_out are combinatorial.
    if rising_edge(clk) then
      if its(rst) then
        in_count_r <= to_unsigned(0, width);
        out_count_r <= to_unsigned(1, width);
      else
        if its(my_take) then
          if its(eom_in) then
            in_count_r <= to_unsigned(0, width);
          elsif its(valid_in) then
            in_count_r <= in_count_r + 1;
          end if;
        end if;
        if its(fifo_deq) then
          out_count_r <= to_unsigned(1, width);
        elsif its(core_out) then
          out_count_r <= out_count_r + 1;
        end if;
      end if;
    end if;
  end process;
end rtl;
