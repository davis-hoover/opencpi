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

library ieee; use ieee.std_logic_1164.all; use ieee.numeric_std.all; use ieee.math_real.all; use ieee.std_logic_misc.all;
library ocpi; use ocpi.types.all,  ocpi.util.all;
library ocpi_core_bsv; use ocpi_core_bsv.all;

entity one_shot_fifo is
    generic (data_width : natural := 1;
             fifo_depth : natural := 2;
             num_output_samples : natural := 1);
    port (
        clk      : in std_logic;
        rst      : in std_logic;
        din      : in std_logic_vector;
        en       : in std_logic;
        rdy      : in std_logic;
        data_vld : out std_logic;
        done     : out std_logic;
        dout     : out std_logic_vector);

end entity one_shot_fifo;

architecture rtl of one_shot_fifo is

  signal s_enq       : std_logic := '0';
  signal s_deq       : std_logic := '0';
  signal s_counter   : unsigned(width_for_max(num_output_samples-1) downto 0) := (others => '0');
  signal s_not_rst   : std_logic;
  signal s_not_full  : std_logic := '0';
  signal s_not_empty : std_logic := '0';
  signal s_done      : std_logic := '0';
  signal s_dout      : std_logic_vector(data_width-1 downto 0);


begin

  s_enq <= s_not_full and en and not s_done;
  s_deq <= s_not_empty and rdy when (s_counter < num_output_samples) else '0';
  s_not_rst <= not rst;

  SizedFIFO : bsv_pkg.SizedFIFO
  generic map(p1Width      => data_width,
              p2depth      => fifo_depth,
              p3cntr_width => width_for_max(fifo_depth-1))
  port map   (CLK     => clk,
              RST     => s_not_rst,
              ENQ     => s_enq,
              D_IN    => din,
              FULL_N  => s_not_full,
              DEQ     => s_deq,
              D_OUT   => s_dout,
              EMPTY_N => s_not_empty,
              CLR     => '0');

  process(clk)
  begin
    if rising_edge(clk) then
      if (rst = '1') then
        s_counter <= (others=>'0');
      elsif (s_deq = '1') then
        s_counter <= s_counter + 1;
      end if;
    end if;
  end process;
  dout <= s_dout;
  s_done <= '1' when (s_counter = num_output_samples) else '0';
  done <= s_done;
  data_vld <= s_deq when (s_counter < num_output_samples) else '0';
end rtl;
