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
-- The DGRDMA transmit mux is used for dual ethernet operation
-- it splits its input (axis) stream, containing the ethernet packets
-- to transmit, between two ethernet interfaces (A and B).
-- it uses round-robin scheduling. alternating packets between the two interfaces.
-- dual ethernet operation is enabled by setting the 'enable' signal to '1'
-- if 'enable' is set to '0' all packets will be sent to interface A.
-- ---------------------------------------------------------------------------
library ieee; use ieee.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi; use ocpi.types.all;

entity dgrdma_tx_mux is

  generic(
    DATA_WIDTH  : natural := 64;
    KEEP_WIDTH  : natural := 8
  );

  port(
    -- clock and reset
    clk             : in std_logic;
    reset           : in std_logic;

    -- runtime signal set high to enable dual ethernet interface usage
    -- when set to '0' packets will be sent to interface A only
    enable          : in std_logic;

    -- input
    s_axis_tdata    : in std_logic_vector((DATA_WIDTH - 1) downto 0);
    s_axis_tkeep    : in std_logic_vector((KEEP_WIDTH - 1) downto 0);
    s_axis_tvalid   : in std_logic;
    s_axis_tlast    : in std_logic;
    s_axis_tuser    : in std_logic;
    s_axis_tready   : out std_logic;

    -- output A
    m_axis_tdata_a  : out std_logic_vector((DATA_WIDTH - 1) downto 0);
    m_axis_tkeep_a  : out std_logic_vector((KEEP_WIDTH - 1) downto 0);
    m_axis_tvalid_a : out std_logic;
    m_axis_tlast_a  : out std_logic;
    m_axis_tuser_a  : out std_logic;
    m_axis_tready_a : in std_logic;

    -- output B
    m_axis_tdata_b  : out std_logic_vector((DATA_WIDTH - 1) downto 0);
    m_axis_tkeep_b  : out std_logic_vector((KEEP_WIDTH - 1) downto 0);
    m_axis_tvalid_b : out std_logic;
    m_axis_tlast_b  : out std_logic;
    m_axis_tuser_b  : out std_logic;
    m_axis_tready_b : in std_logic
  );

end dgrdma_tx_mux;


architecture rtl of dgrdma_tx_mux is

signal a_selected   : boolean;
signal a_selected_r : boolean;
signal is_active_r  : boolean;

signal s_axis_tready_r : std_logic;

begin

  m_axis_tdata_a <= s_axis_tdata;
  m_axis_tkeep_a <= s_axis_tkeep;
  m_axis_tlast_a <= s_axis_tlast;
  m_axis_tuser_a <= s_axis_tuser;

  m_axis_tdata_b <= s_axis_tdata;
  m_axis_tkeep_b <= s_axis_tkeep;
  m_axis_tlast_b <= s_axis_tlast;
  m_axis_tuser_b <= s_axis_tuser;

  s_axis_tready     <= s_axis_tready_r;
  s_axis_tready_r   <= m_axis_tready_a when a_selected else m_axis_tready_b;

  m_axis_tvalid_a <= s_axis_tvalid when a_selected else '0';
  m_axis_tvalid_b <= s_axis_tvalid when not a_selected else '0';

  -- route to output A or B
  -- when dual ethernet operation is disabled always send to interface A
  -- don't change the decision whilst a packet is is_active_r
  -- if both interfaces A and B are ready, don't use the last used interface
  -- if only one interface is ready us it
  -- otherwise no change
  a_selected <= true when (enable = '0') else
              a_selected_r when is_active_r else
              true  when (m_axis_tready_a = '1') and (m_axis_tready_b = '1') and (a_selected_r = false) else
              false when (m_axis_tready_a = '1') and (m_axis_tready_b = '1') and (a_selected_r = true) else
              true  when (m_axis_tready_a = '1') else
              false when (m_axis_tready_b = '1') else
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
          if s_axis_tvalid = '1' then
            is_active_r <= true;
            a_selected_r <= a_selected;
          end if;
        end if;

        -- the end of the packet is indicated by tlast
        if s_axis_tvalid = '1' and s_axis_tready_r = '1' and s_axis_tlast = '1' then
            is_active_r <= false;
        end if;

      end if;
    end if;

end process;
end architecture;
-- ---------------------------------------------------------------------------
-- END OF FILE
-- ---------------------------------------------------------------------------