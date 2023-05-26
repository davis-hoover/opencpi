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

library ieee; use ieee.std_logic_1164.all, ieee.numeric_std.all;

entity fs_div_4_generator is
  port(
    freq_is_positive : in  std_logic;
    aclk             : in  std_logic;
    aresetn          : in  std_logic;
    m_axis_tdata     : out std_logic_vector(32-1 downto 0);
    m_axis_tvalid    : out std_logic;
    m_axis_tready    : in  std_logic);
end entity;
architecture rtl of fs_div_4_generator is
  signal state : std_logic_vector(2-1 downto 0) := (others => '0');
  signal out_i : std_logic_vector(16-1 downto 0) := (others => '0');
  signal out_q : std_logic_vector(16-1 downto 0) := (others => '0');
begin

  fsm : process(aclk)
  begin
    if rising_edge(aclk) then
      if aresetn = '0' then
        state <= "00";
        m_axis_tvalid <= '0';
      else
        m_axis_tvalid <= '1';
        if m_axis_tready = '1' then
          if freq_is_positive = '1' then
            if state = "00" then
              state <= "01";
            elsif state = "01" then
              state <= "10";
            elsif state = "10" then
              state <= "11";
            else -- state = "11"
              state <= "00";
            end if;
          else
            if state = "00" then
              state <= "11";
            elsif state = "01" then
              state <= "00";
            elsif state = "10" then
              state <= "01";
            else -- state = "11"
              state <= "10";
            end if;
          end if;
        end if;
      end if;
    end if;
  end process;

  out_generator : process(state)
  begin
    if state = "00" then
      out_i <= "0111111111111111";
      out_q <= "0000000000000000";
    elsif state = "01" then
      out_i <= "0000000000000000";
      out_q <= "0111111111111111";
    elsif state = "10" then
      out_i <= "1000000000000001";
      out_q <= "0000000000000000";
    else -- state = "11"
      out_i <= "0000000000000000";
      out_q <= "1000000000000001";
    end if;
  end process;
 
  m_axis_tdata <= out_q & out_i;

end rtl;
