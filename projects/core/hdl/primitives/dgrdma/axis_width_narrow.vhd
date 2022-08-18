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

entity axis_width_narrow is
  generic(
    NBYTES : natural := 8
  );
  port(
    clk : in std_logic;
    reset : in std_logic;

    s_axis_tdata : in std_logic_vector((NBYTES * 8) - 1 downto 0);
    s_axis_tkeep : in std_logic_vector(NBYTES - 1 downto 0);
    s_axis_tvalid : in std_logic;
    s_axis_tready : out std_logic;
    s_axis_tlast : in std_logic;

    m_axis_tdata : out std_logic_vector(7 downto 0);
    m_axis_tvalid : out std_logic;
    m_axis_tready : in std_logic;
    m_axis_tlast : out std_logic
  );
end axis_width_narrow;

architecture rtl of axis_width_narrow is
  constant TKEEP_NO_BYTES_REMAINING : std_logic_vector(NBYTES - 1 downto 0) := (
    others => '0'
  );
  constant TKEEP_ONE_BYTE_REMAINING : std_logic_vector(NBYTES - 1 downto 0) := (
    0 => '1',
    others => '0'
  );

  signal shift_in : boolean;
  signal shift_out : boolean;

  signal latched_tdata : std_logic_vector((NBYTES * 8) - 1 downto 0);
  signal latched_tlast : std_logic;
  signal latched_tkeep : std_logic_vector(NBYTES - 1 downto 0);
begin

  m_axis_tdata <= latched_tdata(7 downto 0);
  m_axis_tvalid <= latched_tkeep(0);
  m_axis_tlast <= latched_tlast when latched_tkeep = TKEEP_ONE_BYTE_REMAINING else '0';
  shift_out <= latched_tkeep(0) = '1' and m_axis_tready = '1';
  shift_in <= latched_tkeep = TKEEP_NO_BYTES_REMAINING or (latched_tkeep = TKEEP_ONE_BYTE_REMAINING and shift_out);

  s_axis_tready <= '1' when shift_in else '0';

  process(clk)
  begin
    if rising_edge(clk) then
      if reset = '1' then
        latched_tdata <= (others => '0');
        latched_tkeep <= (others => '0');
        latched_tlast <= '0';
      else
        if shift_in and s_axis_tvalid = '1' then
          latched_tdata <= s_axis_tdata;
          latched_tkeep <= s_axis_tkeep;
          latched_tlast <= s_axis_tlast;

        elsif shift_out then
          latched_tdata <= X"00" & latched_tdata(latched_tdata'left downto 8);
          latched_tkeep <= "0" & latched_tkeep(latched_tkeep'left downto 1);
        end if;
      end if;
    end if;
  end process;

end architecture;
