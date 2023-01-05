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

entity axis_width_widen is
  generic(
    NBYTES: natural := 8
  );
  port(
    clk : in std_logic;
    reset : in std_logic;

    s_axis_tdata : in std_logic_vector(7 downto 0);
    s_axis_tvalid : in std_logic;
    s_axis_tready : out std_logic;
    s_axis_tlast : in std_logic;

    m_axis_tdata : out std_logic_vector((NBYTES * 8) - 1 downto 0);
    m_axis_tkeep : out std_logic_vector(NBYTES - 1 downto 0);
    m_axis_tvalid : out std_logic;
    m_axis_tready : in std_logic;
    m_axis_tlast : out std_logic
  );
end axis_width_widen;

architecture rtl of axis_width_widen is
  signal count : natural range 0 to NBYTES - 1;
  signal m_axis_tvalid_r : std_logic;
  signal ready_in : std_logic;
begin

  m_axis_tvalid <= m_axis_tvalid_r;
  s_axis_tready <= ready_in;
  ready_in <= (not m_axis_tvalid_r) or m_axis_tready;

  process(clk)
  begin
    if rising_edge(clk) then
      if reset = '1' then
        count <= 0;
        m_axis_tdata <= (others => '0');
        m_axis_tkeep <= (others => '0');
        m_axis_tlast <= '0';
        m_axis_tvalid_r <= '0';
      else
        if m_axis_tready = '1' and m_axis_tvalid_r = '1' then
          m_axis_tkeep <= (others => '0');
          m_axis_tvalid_r <= '0';
        end if;

        if ready_in = '1' then
          if s_axis_tvalid = '1' then
            m_axis_tdata(count*8+7 downto count*8) <= s_axis_tdata;
            m_axis_tkeep(count) <= '1';

            m_axis_tlast <= s_axis_tlast;

            if s_axis_tlast = '1' or count = NBYTES - 1 then
              count <= 0;
              m_axis_tvalid_r <= '1';
            else
              count <= count + 1;
            end if;
          end if;
        end if;
      end if;
    end if;
  end process;
end architecture;
