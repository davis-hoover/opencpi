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
-- The ethernet frame router receives inbound ethernet packets and routes
-- these to either the Control Plane (CP) or Data Plane (SDP) based on
-- the ether-type indicated in the ethernet frame header.
-- only packets with a broadcast destination address or those with
-- a destination address matching our local address will be forwarded
-- packets with unknown ether-types will be discard.
-- ---------------------------------------------------------------------------
library ieee; use ieee.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi; use ocpi.types.all;

entity eth_frame_router is

  generic(
    DATA_WIDTH  : natural := 64;
    KEEP_WIDTH  : natural := 8
  );

  port(
    -- clock and reset
    clk             : in std_logic;
    reset           : in std_logic;

    -- Local MAC Address
    local_mac_addr : in std_logic_vector(47 downto 0);

    -- Received Packet addressing
    rx_hdr_dest_mac : std_logic_vector(47 downto 0);
    rx_hdr_type     : std_logic_vector(15 downto 0);

    -- (input)
    s_axis_tdata    : in std_logic_vector((DATA_WIDTH - 1) downto 0);
    s_axis_tkeep    : in std_logic_vector((KEEP_WIDTH - 1) downto 0);
    s_axis_tvalid   : in std_logic;
    s_axis_tlast    : in std_logic;
    s_axis_tready   : out std_logic;

    -- (output) CP
    m_axis_tdata_cp  : out std_logic_vector((DATA_WIDTH - 1) downto 0);
    m_axis_tkeep_cp  : out std_logic_vector((KEEP_WIDTH - 1) downto 0);
    m_axis_tvalid_cp : out std_logic;
    m_axis_tlast_cp  : out std_logic;
    m_axis_tready_cp : in std_logic;

    -- (output) SDP
    m_axis_tdata_sdp  : out std_logic_vector((DATA_WIDTH - 1) downto 0);
    m_axis_tkeep_sdp  : out std_logic_vector((KEEP_WIDTH - 1) downto 0);
    m_axis_tvalid_sdp : out std_logic;
    m_axis_tlast_sdp  : out std_logic;
    m_axis_tready_sdp : in std_logic
  );

end eth_frame_router;

architecture rtl of eth_frame_router is

constant CP_ETHERTYPE  : std_logic_vector(15 downto 0) := X"f040";
constant SDP_ETHERTYPE : std_logic_vector(15 downto 0) := X"f042";

signal rx_max_addr_match : boolean;
signal rx_is_cp  : boolean;
signal rx_is_sdp : boolean;

begin

  -- route input to both CP and SDP interfaces
  -- (but control the respective valid and ready signals)
  m_axis_tdata_cp <= s_axis_tdata;
  m_axis_tkeep_cp <= s_axis_tkeep;
  m_axis_tlast_cp <= s_axis_tlast;

  m_axis_tdata_sdp <= s_axis_tdata;
  m_axis_tkeep_sdp <= s_axis_tkeep;
  m_axis_tlast_sdp <= s_axis_tlast;

  -- check the ethernet frame destination MAC address is
  -- either our address or a broadcast
  rx_max_addr_match <= (rx_hdr_dest_mac = local_mac_addr) or (rx_hdr_dest_mac = X"ffffffffffff");

  -- check if this a CP packet
  rx_is_cp <= rx_max_addr_match and (rx_hdr_type = CP_ETHERTYPE);

  -- check if this is an SDP packet
  rx_is_sdp <= rx_max_addr_match and (rx_hdr_type = SDP_ETHERTYPE);

  -- route to CP
  m_axis_tvalid_cp <= s_axis_tvalid when rx_is_cp else '0';

  -- route to SDP
  m_axis_tvalid_sdp <= s_axis_tvalid when rx_is_sdp else '0';

  -- pass the ready signal from the appropriate interface
  -- if we are not handling this frame set ready high to consume it
  -- without routing
  s_axis_tready <= m_axis_tready_cp  when rx_is_cp else
                   m_axis_tready_sdp when rx_is_sdp else
                  '1';

end architecture;
-- ---------------------------------------------------------------------------
-- END OF FILE
-- ---------------------------------------------------------------------------