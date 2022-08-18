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
library ocpi; use ocpi.types.all;
library platform, sdp;

package dgrdma is

  component rgmii_to_ocpi is
    generic (
      SDP_WIDTH : natural := 1;      -- default to 32-bit data bus
      ACK_TRACKER_BITFIELD_WIDTH : natural;
      ACK_TRACKER_MAX_ACK_COUNT  : natural range 1 to 255;
      TXN_RECORD_MAX_TXNS_IN_FLIGHT : natural := 64;
      MAX_FRAME_SIZE : natural := 10240
    );
    port (
      clk                   : in std_logic;
      reset                 : in std_logic;
      clk_mac               : in std_logic;
      clk_mac_90            : in std_logic;
      reset_mac             : in std_logic;
      sdp_reset             : in std_logic;

      -- Configuration
      local_mac_addr        : in std_logic_vector(47 downto 0);
      remote_mac_addr       : in std_logic_vector(47 downto 0);
      remote_dst_id         : in std_logic_vector(15 downto 0);
      local_src_id          : in std_logic_vector(15 downto 0);
      interface_mtu         : in unsigned(15 downto 0);
      ack_wait              : in unsigned(31 downto 0);
      max_acks_outstanding  : in unsigned(7 downto 0);
      coalesce_wait         : in unsigned(31 downto 0);
      ifg_delay             : in unsigned(7 downto 0);
      eth_speed             : out std_logic_vector(1 downto 0);

      -- Ack Tracker
      ack_tracker_rej_ack             : out std_logic;
      ack_tracker_bitfield            : out std_logic_vector(31 downto 0);
      ack_tracker_base_seqno          : out std_logic_vector(15 downto 0);
      ack_tracker_rej_seqno           : out std_logic_vector(15 downto 0);
      ack_tracker_total_acks_sent     : out std_logic_vector(31 downto 0);
      ack_tracker_tx_acks_sent        : out std_logic_vector(31 downto 0);
      ack_tracker_pkts_enqueued       : out std_logic_vector(31 downto 0);
      ack_tracker_reject_out_of_range : out std_logic_vector(31 downto 0);
      ack_tracker_reject_already_set  : out std_logic_vector(31 downto 0);
      ack_tracker_accepted_by_peek    : out std_logic_vector(31 downto 0);
      ack_tracker_high_watermark      : out std_logic_vector(15 downto 0);
      frame_parser_reject             : out std_logic_vector(31 downto 0);

      -- Control plane master
      cp_in                 : in platform.platform_pkg.occp_out_t;
      cp_out                : out platform.platform_pkg.occp_in_t;

      -- SDP master
      sdp_in                : in sdp.sdp.s2m_t;
      sdp_in_data           : in dword_array_t(SDP_WIDTH-1 downto 0);
      sdp_out               : out sdp.sdp.m2s_t;
      sdp_out_data          : out dword_array_t(SDP_WIDTH-1 downto 0);

      -- RGMII interface
      phy_reset_n           : out std_logic;
      phy_int_n             : in std_logic;
      phy_rx_clk            : in std_logic;
      phy_rxd               : in std_logic_vector(3 downto 0);
      phy_rx_ctl            : in std_logic;
      phy_tx_clk            : out std_logic;
      phy_txd               : out std_logic_vector(3 downto 0);
      phy_tx_ctl            : out std_logic
    );
  end component rgmii_to_ocpi;

  component dual_rgmii_to_ocpi is
    generic (
      SDP_WIDTH : natural := 1;      -- default to 32-bit data bus
      ACK_TRACKER_BITFIELD_WIDTH : natural;
      ACK_TRACKER_MAX_ACK_COUNT  : natural range 1 to 255;
      TXN_RECORD_MAX_TXNS_IN_FLIGHT : natural := 64;
      MAX_FRAME_SIZE : natural := 10240
    );
    port (
      clk                   : in std_logic;
      reset                 : in std_logic;
      clk_mac               : in std_logic;
      clk_mac_90            : in std_logic;
      reset_mac             : in std_logic;
      sdp_reset             : in std_logic;

      -- Configuration
      local_mac_addr        : in std_logic_vector(47 downto 0);
      remote_mac_addr       : in std_logic_vector(47 downto 0);
      remote_dst_id         : in std_logic_vector(15 downto 0);
      local_src_id          : in std_logic_vector(15 downto 0);
      interface_mtu         : in unsigned(15 downto 0);
      ack_wait              : in unsigned(31 downto 0);
      max_acks_outstanding  : in unsigned(7 downto 0);
      coalesce_wait         : in unsigned(31 downto 0);
      dual_ethernet         : in std_logic;
      ifg_delay             : in unsigned(7 downto 0);
      eth_speed_1           : out std_logic_vector(1 downto 0);
      eth_speed_2           : out std_logic_vector(1 downto 0);

      -- Ack Tracker Debug
      ack_tracker_rej_ack             : out std_logic;
      ack_tracker_bitfield            : out std_logic_vector(31 downto 0);
      ack_tracker_base_seqno          : out std_logic_vector(15 downto 0);
      ack_tracker_rej_seqno           : out std_logic_vector(15 downto 0);
      ack_tracker_total_acks_sent     : out std_logic_vector(31 downto 0);
      ack_tracker_tx_acks_sent        : out std_logic_vector(31 downto 0);
      ack_tracker_pkts_enqueued       : out std_logic_vector(31 downto 0);
      ack_tracker_reject_out_of_range : out std_logic_vector(31 downto 0);
      ack_tracker_reject_already_set  : out std_logic_vector(31 downto 0);
      ack_tracker_accepted_by_peek    : out std_logic_vector(31 downto 0);
      ack_tracker_high_watermark      : out std_logic_vector(15 downto 0);
      frame_parser_reject             : out std_logic_vector(31 downto 0);

      -- Control plane master
      cp_in                 : in platform.platform_pkg.occp_out_t;
      cp_out                : out platform.platform_pkg.occp_in_t;

      -- SDP master
      sdp_in                : in sdp.sdp.s2m_t;
      sdp_in_data           : in dword_array_t(SDP_WIDTH-1 downto 0);
      sdp_out               : out sdp.sdp.m2s_t;
      sdp_out_data          : out dword_array_t(SDP_WIDTH-1 downto 0);

      -- RGMII interface 1
      phy_reset_n_1         : out std_logic;
      phy_int_n_1           : in std_logic;
      phy_rx_clk_1          : in std_logic;
      phy_rxd_1             : in std_logic_vector(3 downto 0);
      phy_rx_ctl_1          : in std_logic;
      phy_tx_clk_1          : out std_logic;
      phy_txd_1             : out std_logic_vector(3 downto 0);
      phy_tx_ctl_1          : out std_logic;

      -- RGMII interface 2
      phy_reset_n_2         : out std_logic;
      phy_int_n_2           : in std_logic;
      phy_rx_clk_2          : in std_logic;
      phy_rxd_2             : in std_logic_vector(3 downto 0);
      phy_rx_ctl_2          : in std_logic;
      phy_tx_clk_2          : out std_logic;
      phy_txd_2             : out std_logic_vector(3 downto 0);
      phy_tx_ctl_2          : out std_logic
    );
  end component dual_rgmii_to_ocpi;

  component xgmii_to_ocpi is
    generic (
      SDP_WIDTH                     : natural := 4;  -- default to 128-bit data bus
      ACK_TRACKER_BITFIELD_WIDTH    : natural;
      ACK_TRACKER_MAX_ACK_COUNT     : natural range 1 to 255;
      TXN_RECORD_MAX_TXNS_IN_FLIGHT : natural := 64;
      MAX_FRAME_SIZE                : natural := 10240
    );
    port (
      clk                   : in std_logic;
      reset                 : in std_logic;
      sdp_reset             : in std_logic;

      -- Configuration
      local_mac_addr        : in std_logic_vector(47 downto 0);
      remote_mac_addr       : in std_logic_vector(47 downto 0);
      remote_dst_id         : in std_logic_vector(15 downto 0);
      local_src_id          : in std_logic_vector(15 downto 0);
      interface_mtu         : in unsigned(15 downto 0);
      ack_wait              : in unsigned(31 downto 0);
      max_acks_outstanding  : in unsigned(7 downto 0);
      coalesce_wait         : in unsigned(31 downto 0);
      ifg_delay             : in unsigned(7 downto 0);

      -- Ack Tracker Debug
      ack_tracker_rej_ack             : out std_logic;
      ack_tracker_bitfield            : out std_logic_vector(31 downto 0);
      ack_tracker_base_seqno          : out std_logic_vector(15 downto 0);
      ack_tracker_rej_seqno           : out std_logic_vector(15 downto 0);
      ack_tracker_total_acks_sent     : out std_logic_vector(31 downto 0);
      ack_tracker_tx_acks_sent        : out std_logic_vector(31 downto 0);
      ack_tracker_pkts_enqueued       : out std_logic_vector(31 downto 0);
      ack_tracker_reject_out_of_range : out std_logic_vector(31 downto 0);
      ack_tracker_reject_already_set  : out std_logic_vector(31 downto 0);
      ack_tracker_accepted_by_peek    : out std_logic_vector(31 downto 0);
      ack_tracker_high_watermark      : out std_logic_vector(15 downto 0);
      frame_parser_reject             : out std_logic_vector(31 downto 0);

      -- Control plane master
      cp_in                 : in platform.platform_pkg.occp_out_t;
      cp_out                : out platform.platform_pkg.occp_in_t;

      -- SDP master
      sdp_in                : in sdp.sdp.s2m_t;
      sdp_in_data           : in dword_array_t(sdp_width-1 downto 0);
      sdp_out               : out sdp.sdp.m2s_t;
      sdp_out_data          : out dword_array_t(sdp_width-1 downto 0);

      -- XGMII interface
      xgmii_rx_clk          : in  std_logic;
      xgmii_rx_reset        : in  std_logic;
      xgmii_rxd             : in  std_logic_vector(63 downto 0);
      xgmii_rxc             : in  std_logic_vector(7 downto 0);
      xgmii_tx_clk          : in  std_logic;
      xgmii_tx_reset        : in  std_logic;
      xgmii_txd             : out std_logic_vector(63 downto 0);
      xgmii_txc             : out std_logic_vector(7 downto 0)
    );
  end component xgmii_to_ocpi;

  component dual_xgmii_to_ocpi is
    generic (
      SDP_WIDTH                     : natural := 4;  -- default to 128-bit data bus
      ACK_TRACKER_BITFIELD_WIDTH    : natural;
      ACK_TRACKER_MAX_ACK_COUNT     : natural range 1 to 255;
      TXN_RECORD_MAX_TXNS_IN_FLIGHT : natural := 64;
      MAX_FRAME_SIZE                : natural := 10240
    );
    port (
      clk                   : in std_logic;
      reset                 : in std_logic;
      sdp_reset             : in std_logic;

      -- Configuration
      local_mac_addr        : in std_logic_vector(47 downto 0);
      remote_mac_addr       : in std_logic_vector(47 downto 0);
      remote_dst_id         : in std_logic_vector(15 downto 0);
      local_src_id          : in std_logic_vector(15 downto 0);
      interface_mtu         : in unsigned(15 downto 0);
      ack_wait              : in unsigned(31 downto 0);
      max_acks_outstanding  : in unsigned(7 downto 0);
      coalesce_wait         : in unsigned(31 downto 0);
      dual_ethernet         : in std_logic;
      ifg_delay             : in unsigned(7 downto 0);

      -- Ack Tracker Debug
      ack_tracker_rej_ack             : out std_logic;
      ack_tracker_bitfield            : out std_logic_vector(31 downto 0);
      ack_tracker_base_seqno          : out std_logic_vector(15 downto 0);
      ack_tracker_rej_seqno           : out std_logic_vector(15 downto 0);
      ack_tracker_total_acks_sent     : out std_logic_vector(31 downto 0);
      ack_tracker_tx_acks_sent        : out std_logic_vector(31 downto 0);
      ack_tracker_pkts_enqueued       : out std_logic_vector(31 downto 0);
      ack_tracker_reject_out_of_range : out std_logic_vector(31 downto 0);
      ack_tracker_reject_already_set  : out std_logic_vector(31 downto 0);
      ack_tracker_accepted_by_peek    : out std_logic_vector(31 downto 0);
      ack_tracker_high_watermark      : out std_logic_vector(15 downto 0);
      frame_parser_reject             : out std_logic_vector(31 downto 0);

      -- Control plane master
      cp_in                 : in platform.platform_pkg.occp_out_t;
      cp_out                : out platform.platform_pkg.occp_in_t;

      -- SDP master
      sdp_in                : in sdp.sdp.s2m_t;
      sdp_in_data           : in dword_array_t(SDP_WIDTH-1 downto 0);
      sdp_out               : out sdp.sdp.m2s_t;
      sdp_out_data          : out dword_array_t(SDP_WIDTH-1 downto 0);

      -- XGMII interface 1
      xgmii_rx_clk_1        : in  std_logic;
      xgmii_rx_reset_1      : in  std_logic;
      xgmii_rxd_1           : in  std_logic_vector(63 downto 0);
      xgmii_rxc_1           : in  std_logic_vector(7 downto 0);
      xgmii_tx_clk_1        : in  std_logic;
      xgmii_tx_reset_1      : in  std_logic;
      xgmii_txd_1           : out std_logic_vector(63 downto 0);
      xgmii_txc_1           : out std_logic_vector(7 downto 0);

      -- XGMII interface 2
      xgmii_rx_clk_2        : in  std_logic;
      xgmii_rx_reset_2      : in  std_logic;
      xgmii_rxd_2           : in  std_logic_vector(63 downto 0);
      xgmii_rxc_2           : in  std_logic_vector(7 downto 0);
      xgmii_tx_clk_2        : in  std_logic;
      xgmii_tx_reset_2      : in  std_logic;
      xgmii_txd_2           : out std_logic_vector(63 downto 0);
      xgmii_txc_2           : out std_logic_vector(7 downto 0)
    );
  end component dual_xgmii_to_ocpi;

end package dgrdma;
