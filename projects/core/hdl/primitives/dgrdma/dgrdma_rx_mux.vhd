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

-- ---------------------------------------------------------------------------
-- The DGRDMA receive mux is used for dual ethernet operation
-- it combines the received ethernet packets from network interfaces A and B
-- if packets are available on both interfaces a round-robin scheme is used
-- if the enable signal is set to '0' dual ethernet operation is disabled
-- and packets will always be taken from interface A only
-- ---------------------------------------------------------------------------
library ieee; use ieee.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi; use ocpi.types.all;

entity dgrdma_rx_mux is

  generic(
    DATA_WIDTH  : natural := 64;
    KEEP_WIDTH  : natural := 8
  );

  port(
    -- clocks and reset
    clk             : in std_logic;
    reset           : in std_logic;

    -- runtime signal set high to enable dual ethernet interface usage
    -- when set to '0' packets will be taken from interface A only
    enable          : in std_logic;

    -- input A
    s_axis_tdata_a  : in std_logic_vector((DATA_WIDTH - 1) downto 0);
    s_axis_tkeep_a  : in std_logic_vector((KEEP_WIDTH - 1) downto 0);
    s_axis_tvalid_a : in std_logic;
    s_axis_tlast_a  : in std_logic;
    s_axis_tuser_a  : in std_logic;
    s_axis_tready_a : out std_logic;

    -- input B
    s_axis_tdata_b  : in std_logic_vector((DATA_WIDTH - 1) downto 0);
    s_axis_tkeep_b  : in std_logic_vector((KEEP_WIDTH - 1) downto 0);
    s_axis_tvalid_b : in std_logic;
    s_axis_tlast_b  : in std_logic;
    s_axis_tuser_b  : in std_logic;
    s_axis_tready_b : out std_logic;

    -- output interface
    m_axis_tdata  : out std_logic_vector((DATA_WIDTH - 1) downto 0);
    m_axis_tkeep  : out std_logic_vector((KEEP_WIDTH - 1) downto 0);
    m_axis_tvalid : out std_logic;
    m_axis_tlast  : out std_logic;
    m_axis_tuser  : out std_logic;
    m_axis_tready : in std_logic
  );

end dgrdma_rx_mux;


architecture rtl of dgrdma_rx_mux is

signal a_selected   : boolean;
signal a_selected_r : boolean;
signal is_active_r  : boolean;

begin

  -- set the ready signals dependent on the selected interface
  s_axis_tready_a <= m_axis_tready when a_selected else '0';
  s_axis_tready_b <= m_axis_tready when not a_selected else '0';

  -- mux the selected interface oto the output signals
  m_axis_tdata  <= s_axis_tdata_a  when a_selected else s_axis_tdata_b;
  m_axis_tkeep  <= s_axis_tkeep_a  when a_selected else s_axis_tkeep_b;
  m_axis_tvalid <= s_axis_tvalid_a when a_selected else s_axis_tvalid_b;
  m_axis_tlast  <= s_axis_tlast_a  when a_selected else s_axis_tlast_b;
  m_axis_tuser  <= s_axis_tuser_a  when a_selected else s_axis_tuser_b;

  -- take the next packet from input A or B
  -- when dual ethernet operation is disabled take packet from interface A
  -- don't change the decision whilst a packet is is_active_r
  -- if both interfaces A and B have packets, don't use the last used interface
  -- if only one interface packet then us it
  -- otherwise no change
  a_selected <= true when (enable = '0') else
              a_selected_r when is_active_r else
              true   when (s_axis_tvalid_a = '1') and (s_axis_tvalid_b = '1') and (a_selected_r = false) else
              false  when (s_axis_tvalid_a = '1') and (s_axis_tvalid_b = '1') and (a_selected_r = true) else
              true   when (s_axis_tvalid_a = '1') else
              false  when (s_axis_tvalid_b = '1') else
              a_selected_r;

process(clk)
  begin

    if rising_edge(clk) then
      if reset = '1' then
        is_active_r <= false;
        a_selected_r <= false;
      else

        -- hold the decision at the start of a new packet
        if not is_active_r then
          if s_axis_tvalid_a = '1' or s_axis_tvalid_b = '1' then
            is_active_r <= true;
            a_selected_r <= a_selected;
          end if;
        end if;

        -- the end of the packet is indicated by tlast on the selectd interface
        if a_selected then
          if m_axis_tready = '1' and s_axis_tvalid_a = '1' and s_axis_tlast_a = '1' then
            is_active_r <= false;
          end if;
        else
          if m_axis_tready = '1' and s_axis_tvalid_b = '1' and s_axis_tlast_b = '1' then
            is_active_r <= false;
          end if;
        end if;

      end if;
    end if;
end process;

end architecture;
-- ---------------------------------------------------------------------------
-- END OF FILE
-- ---------------------------------------------------------------------------