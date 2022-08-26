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
-- A single instance of the dual_rgmii_to_ocpi component is instanced
-- by the Platform Worker.  it instances the ethernet interface(s)
-- and the eth_to_ocpi component which is responsible for converting
-- ethernet packets to and from Control Plane (CP) and Data plane (SDP)
-- buses
-- ---------------------------------------------------------------------------
library ieee; use ieee.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi; use ocpi.types.all;
library platform, sdp;

entity dual_rgmii_to_ocpi is
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
    phy_reset_n_1       : out std_logic;
    phy_int_n_1         : in std_logic;
    phy_rx_clk_1        : in std_logic;
    phy_rxd_1           : in std_logic_vector(3 downto 0);
    phy_rx_ctl_1        : in std_logic;
    phy_tx_clk_1        : out std_logic;
    phy_txd_1           : out std_logic_vector(3 downto 0);
    phy_tx_ctl_1        : out std_logic;

    -- RGMII interface 2
    phy_reset_n_2       : out std_logic;
    phy_int_n_2         : in std_logic;
    phy_rx_clk_2        : in std_logic;
    phy_rxd_2           : in std_logic_vector(3 downto 0);
    phy_rx_ctl_2        : in std_logic;
    phy_tx_clk_2        : out std_logic;
    phy_txd_2           : out std_logic_vector(3 downto 0);
    phy_tx_ctl_2        : out std_logic
  );
end entity dual_rgmii_to_ocpi;

architecture rtl of dual_rgmii_to_ocpi is

  constant DATA_WIDTH : integer := SDP_WIDTH * 32;
  constant KEEP_WIDTH : integer := SDP_WIDTH * 4;

  -- Receive Ethernet packets from MAC 1
  signal rx_eth_tdata_1 : std_logic_vector(DATA_WIDTH - 1 downto 0);
  signal rx_eth_tkeep_1 : std_logic_vector(KEEP_WIDTH - 1 downto 0);
  signal rx_eth_tvalid_1 : std_logic;
  signal rx_eth_tlast_1 : std_logic;
  signal rx_eth_tready_1 : std_logic;
  signal rx_eth_tuser_1 : std_logic;

  -- Transmit ethernet packets to MAC 1
  signal tx_eth_tdata_1 : std_logic_vector(DATA_WIDTH - 1 downto 0);
  signal tx_eth_tkeep_1 : std_logic_vector(KEEP_WIDTH - 1 downto 0);
  signal tx_eth_tvalid_1 : std_logic;
  signal tx_eth_tlast_1 : std_logic;
  signal tx_eth_tready_1 : std_logic;
  signal tx_eth_tuser_1 : std_logic;

  -- Receive Ethernet packets from MAC 2
  signal rx_eth_tdata_2 : std_logic_vector(DATA_WIDTH - 1 downto 0);
  signal rx_eth_tkeep_2 : std_logic_vector(KEEP_WIDTH - 1 downto 0);
  signal rx_eth_tvalid_2 : std_logic;
  signal rx_eth_tlast_2 : std_logic;
  signal rx_eth_tready_2 : std_logic;
  signal rx_eth_tuser_2 : std_logic;

  -- Transmit ethernet packets to MAC 2
  signal tx_eth_tdata_2 : std_logic_vector(DATA_WIDTH - 1 downto 0);
  signal tx_eth_tkeep_2 : std_logic_vector(KEEP_WIDTH - 1 downto 0);
  signal tx_eth_tvalid_2 : std_logic;
  signal tx_eth_tlast_2 : std_logic;
  signal tx_eth_tready_2 : std_logic;
  signal tx_eth_tuser_2 : std_logic;

begin
  -- MAC INSTANCE 1
  mac_inst_1 : entity work.rgmii_mac_wrapper
    generic map(
      DATA_WIDTH => DATA_WIDTH,
      KEEP_WIDTH => KEEP_WIDTH,
      MAX_FRAME_SIZE => MAX_FRAME_SIZE
    )
    port map(
      clk           => clk,
      clk_125mhz    => clk_mac,
      clk_125mhz_90 => clk_mac_90,
      reset         => reset,
      reset_125mhz  => reset_mac,

      phy_rx_clk    => phy_rx_clk_1,
      phy_rxd       => phy_rxd_1,
      phy_rx_ctl    => phy_rx_ctl_1,
      phy_tx_clk    => phy_tx_clk_1,
      phy_txd       => phy_txd_1,
      phy_tx_ctl    => phy_tx_ctl_1,
      phy_reset_n   => phy_reset_n_1,
      phy_int_n     => phy_int_n_1,

      rx_eth_tdata  => rx_eth_tdata_1,
      rx_eth_tkeep  => rx_eth_tkeep_1,
      rx_eth_tvalid => rx_eth_tvalid_1,
      rx_eth_tlast  => rx_eth_tlast_1,
      rx_eth_tready => rx_eth_tready_1,
      rx_eth_tuser  => rx_eth_tuser_1,

      tx_eth_tdata  => tx_eth_tdata_1,
      tx_eth_tkeep  => tx_eth_tkeep_1,
      tx_eth_tvalid => tx_eth_tvalid_1,
      tx_eth_tlast  => tx_eth_tlast_1,
      tx_eth_tready => tx_eth_tready_1,
      tx_eth_tuser  => tx_eth_tuser_1,

      ifg_delay     => ifg_delay,
      eth_speed     => eth_speed_1
    );

  -- MAC INSTANCE 2
  mac_inst_2 : entity work.rgmii_mac_wrapper
  generic map(
    DATA_WIDTH => DATA_WIDTH,
    KEEP_WIDTH => KEEP_WIDTH,
    MAX_FRAME_SIZE => MAX_FRAME_SIZE
  )
  port map(
    clk           => clk,
    clk_125mhz    => clk_mac,
    clk_125mhz_90 => clk_mac_90,
    reset         => reset,
    reset_125mhz  => reset_mac,

    phy_rx_clk    => phy_rx_clk_2,
    phy_rxd       => phy_rxd_2,
    phy_rx_ctl    => phy_rx_ctl_2,
    phy_tx_clk    => phy_tx_clk_2,
    phy_txd       => phy_txd_2,
    phy_tx_ctl    => phy_tx_ctl_2,
    phy_reset_n   => phy_reset_n_2,
    phy_int_n     => phy_int_n_2,

    rx_eth_tdata  => rx_eth_tdata_2,
    rx_eth_tkeep  => rx_eth_tkeep_2,
    rx_eth_tvalid => rx_eth_tvalid_2,
    rx_eth_tlast  => rx_eth_tlast_2,
    rx_eth_tready => rx_eth_tready_2,
    rx_eth_tuser  => rx_eth_tuser_2,

    tx_eth_tdata  => tx_eth_tdata_2,
    tx_eth_tkeep  => tx_eth_tkeep_2,
    tx_eth_tvalid => tx_eth_tvalid_2,
    tx_eth_tlast  => tx_eth_tlast_2,
    tx_eth_tready => tx_eth_tready_2,
    tx_eth_tuser  => tx_eth_tuser_2,

    ifg_delay     => ifg_delay,
    eth_speed     => eth_speed_2
  );

  -- CONVERT ETHERNET TO CP AND SDP OPENCPI MASTERS
  eth_to_ocpi_inst : entity work.dual_eth_to_ocpi
    generic map (
      SDP_WIDTH  => SDP_WIDTH,
      DATA_WIDTH => DATA_WIDTH,
      KEEP_WIDTH => KEEP_WIDTH,
      ACK_TRACKER_BITFIELD_WIDTH => ACK_TRACKER_BITFIELD_WIDTH,
      ACK_TRACKER_MAX_ACK_COUNT  => ACK_TRACKER_MAX_ACK_COUNT,
      TXN_RECORD_MAX_TXNS_IN_FLIGHT => TXN_RECORD_MAX_TXNS_IN_FLIGHT
    )
    port map (
      clk       => clk,
      reset     => reset,
      sdp_reset => sdp_reset,

      -- Configuration
      local_mac_addr       => local_mac_addr,
      remote_mac_addr      => remote_mac_addr,
      remote_dst_id        => remote_dst_id,
      local_src_id         => local_src_id,
      interface_mtu        => interface_mtu,
      ack_wait             => ack_wait,
      max_acks_outstanding => max_acks_outstanding,
      coalesce_wait        => coalesce_wait,
      dual_ethernet        => dual_ethernet,

      -- Ack Tracker Debug
      ack_tracker_rej_ack => ack_tracker_rej_ack,
      ack_tracker_bitfield => ack_tracker_bitfield,
      ack_tracker_base_seqno => ack_tracker_base_seqno,
      ack_tracker_rej_seqno => ack_tracker_rej_seqno,
      ack_tracker_total_acks_sent => ack_tracker_total_acks_sent,
      ack_tracker_tx_acks_sent => ack_tracker_tx_acks_sent,
      ack_tracker_pkts_enqueued => ack_tracker_pkts_enqueued,
      ack_tracker_reject_out_of_range => ack_tracker_reject_out_of_range,
      ack_tracker_reject_already_set => ack_tracker_reject_already_set,
      ack_tracker_accepted_by_peek => ack_tracker_accepted_by_peek,
      ack_tracker_high_watermark => ack_tracker_high_watermark,
      frame_parser_reject => frame_parser_reject,

      -- Control plane master
      cp_in  => cp_in,
      cp_out => cp_out,

      -- SDP master
      sdp_in       => sdp_in,
      sdp_in_data  => sdp_in_data,
      sdp_out      => sdp_out,
      sdp_out_data => sdp_out_data,

      -- Ethernet frame interface A
      rx_eth_tdata_a  => rx_eth_tdata_1,
      rx_eth_tkeep_a  => rx_eth_tkeep_1,
      rx_eth_tvalid_a => rx_eth_tvalid_1,
      rx_eth_tready_a => rx_eth_tready_1,
      rx_eth_tlast_a  => rx_eth_tlast_1,
      rx_eth_tuser_a  => rx_eth_tuser_1,

      tx_eth_tdata_a  => tx_eth_tdata_1,
      tx_eth_tkeep_a  => tx_eth_tkeep_1,
      tx_eth_tvalid_a => tx_eth_tvalid_1,
      tx_eth_tready_a => tx_eth_tready_1,
      tx_eth_tlast_a  => tx_eth_tlast_1,
      tx_eth_tuser_a  => tx_eth_tuser_1,

      -- Ethernet frame interface B
      rx_eth_tdata_b  => rx_eth_tdata_2,
      rx_eth_tkeep_b  => rx_eth_tkeep_2,
      rx_eth_tvalid_b => rx_eth_tvalid_2,
      rx_eth_tready_b => rx_eth_tready_2,
      rx_eth_tlast_b  => rx_eth_tlast_2,
      rx_eth_tuser_b  => rx_eth_tuser_2,

      tx_eth_tdata_b  => tx_eth_tdata_2,
      tx_eth_tkeep_b  => tx_eth_tkeep_2,
      tx_eth_tvalid_b => tx_eth_tvalid_2,
      tx_eth_tready_b => tx_eth_tready_2,
      tx_eth_tlast_b  => tx_eth_tlast_2,
      tx_eth_tuser_b  => tx_eth_tuser_2
    );

end architecture;
-- ---------------------------------------------------------------------------
-- END OF FILE
-- ---------------------------------------------------------------------------