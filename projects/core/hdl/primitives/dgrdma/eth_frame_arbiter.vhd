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
-- The ethernet frame arbiter receives outbound ethernet packets from both
-- the Control Plane (CP) and Data Plane (SDP). these are forwarded to the
-- output interface. If packets are present on both CP and SDP simultaneously
-- the CP is given priority
-- ---------------------------------------------------------------------------
library ieee; use ieee.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi; use ocpi.types.all;

entity eth_frame_arbiter is

  generic(
    DATA_WIDTH  : natural := 64;
    KEEP_WIDTH  : natural := 8
  );

  port(
    -- clock and reset
    clk             : in std_logic;
    reset           : in std_logic;

    -- the transmit ethertye
    tx_hdr_type        : out std_logic_vector(15 downto 0);

    -- input CP
    s_axis_tdata_cp    : in std_logic_vector((DATA_WIDTH - 1) downto 0);
    s_axis_tkeep_cp    : in std_logic_vector((KEEP_WIDTH - 1) downto 0);
    s_axis_tvalid_cp   : in std_logic;
    s_axis_tlast_cp    : in std_logic;
    s_axis_tready_cp   : out std_logic;

    -- input SDP
    s_axis_tdata_sdp    : in std_logic_vector((DATA_WIDTH - 1) downto 0);
    s_axis_tkeep_sdp    : in std_logic_vector((KEEP_WIDTH - 1) downto 0);
    s_axis_tvalid_sdp   : in std_logic;
    s_axis_tlast_sdp    : in std_logic;
    s_axis_tready_sdp   : out std_logic;

    -- output
    m_axis_tdata  : out std_logic_vector((DATA_WIDTH - 1) downto 0);
    m_axis_tkeep  : out std_logic_vector((KEEP_WIDTH - 1) downto 0);
    m_axis_tvalid : out std_logic;
    m_axis_tlast  : out std_logic;
    m_axis_tready : in std_logic
  );

end eth_frame_arbiter;

architecture rtl of eth_frame_arbiter is

constant CP_ETHERTYPE  : std_logic_vector(15 downto 0) := X"f040";
constant SDP_ETHERTYPE : std_logic_vector(15 downto 0) := X"f042";

signal tx_is_cp    : boolean;
signal tx_is_cp_r  : boolean;
signal tx_active_r : boolean;

begin

  -- route the selected packet to the output
  tx_hdr_type   <= CP_ETHERTYPE     when tx_is_cp else SDP_ETHERTYPE;
  m_axis_tdata  <= s_axis_tdata_cp  when tx_is_cp else s_axis_tdata_sdp;
  m_axis_tkeep  <= s_axis_tkeep_cp  when tx_is_cp else s_axis_tkeep_sdp;
  m_axis_tvalid <= s_axis_tvalid_cp when tx_is_cp else s_axis_tvalid_sdp;
  m_axis_tlast  <= s_axis_tlast_cp  when tx_is_cp else s_axis_tlast_sdp;

  -- pass on the ready signal to the selected interface
  s_axis_tready_cp  <= m_axis_tready when tx_is_cp else '0';
  s_axis_tready_sdp <= m_axis_tready when not tx_is_cp else '0';

  -- arbiter decision, control plane response has priority
  tx_is_cp <= tx_is_cp_r when tx_active_r else
              true  when s_axis_tvalid_cp = '1' else
              false when s_axis_tvalid_sdp = '1' else
              true;

  -- latch the arbiter decision until the end of the packet
  process(clk)
  begin

    if rising_edge(clk) then
      if reset = '1' then
        tx_active_r <= false;
        tx_is_cp_r  <= false;
      else

         -- hold the decision at the start of a new packet
        if not tx_active_r then
          if s_axis_tvalid_cp = '1' or s_axis_tvalid_sdp = '1' then
            tx_active_r <= true;
            tx_is_cp_r  <= tx_is_cp;
          end if;
        end if;

        -- the end of the packet is indicated by tlast on the selectd interface
        if tx_is_cp then
          if m_axis_tready = '1' and s_axis_tvalid_cp = '1' and s_axis_tlast_cp = '1' then
            tx_active_r <= false;
          end if;
        else
          if m_axis_tready = '1' and s_axis_tvalid_sdp = '1' and s_axis_tlast_sdp = '1' then
             tx_active_r <= false;
           end if;
        end if;
      end if;
    end if;
  end process;

end architecture;
-- ---------------------------------------------------------------------------
-- END OF FILE
-- ---------------------------------------------------------------------------