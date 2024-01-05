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
library dgrdma; use dgrdma.dgrdma_util.all;

entity udp_to_ocpi is
  generic (
    SDP_WIDTH                     : natural := 2;
    ETH_DATA_WIDTH                : natural := 64;
    ETH_KEEP_WIDTH                : natural := 8;
    ACK_TRACKER_BITFIELD_WIDTH    : natural;
    ACK_TRACKER_MAX_ACK_COUNT     : natural range 1 to 255;
    TXN_RECORD_MAX_TXNS_IN_FLIGHT : natural := 64;
    MAX_FRAME_SIZE                : natural := 10240;
    UDP_CP_PORT                   : natural := 18077;
    UDP_SDP_PORT                  : natural := 18078
  );
  port (
    clk          : in std_logic;
    reset        : in std_logic;
    sdp_reset    : in std_logic;

    -- Configuration
    local_ip_addr        : in std_logic_vector(31 downto 0);
    local_subnet_mask    : in std_logic_vector(31 downto 0);
    local_gateway_ip     : in std_logic_vector(31 downto 0);
    remote_ip_addr       : in std_logic_vector(31 downto 0);
    remote_udp_port      : in std_logic_vector(15 downto 0);
    local_mac_addr       : in std_logic_vector(47 downto 0);
    remote_mac_addr      : in std_logic_vector(47 downto 0);
    remote_dst_id        : in std_logic_vector(15 downto 0);
    local_src_id         : in std_logic_vector(15 downto 0);
    interface_mtu        : in unsigned(15 downto 0);
    ack_wait             : in unsigned(31 downto 0);
    max_acks_outstanding : in unsigned(7 downto 0);
    coalesce_wait        : in unsigned(31 downto 0);

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
    cp_in        : in platform.platform_pkg.occp_out_t;
    cp_out       : out platform.platform_pkg.occp_in_t;

    -- SDP master
    sdp_in       : in sdp.sdp.s2m_t;
    sdp_in_data  : in dword_array_t(SDP_WIDTH-1 downto 0);
    sdp_out      : out sdp.sdp.m2s_t;
    sdp_out_data : out dword_array_t(SDP_WIDTH-1 downto 0);

    -- Ethernet frame interface
    rx_eth_tdata  : in std_logic_vector(ETH_DATA_WIDTH-1 downto 0);
    rx_eth_tkeep  : in std_logic_vector(ETH_KEEP_WIDTH-1 downto 0);
    rx_eth_tvalid : in std_logic;
    rx_eth_tready : out std_logic;
    rx_eth_tlast  : in std_logic;
    rx_eth_tuser  : in std_logic;

    tx_eth_tdata  : out std_logic_vector(ETH_DATA_WIDTH-1 downto 0);
    tx_eth_tkeep  : out std_logic_vector(ETH_KEEP_WIDTH-1 downto 0);
    tx_eth_tvalid : out std_logic;
    tx_eth_tready : in std_logic;
    tx_eth_tlast  : out std_logic;
    tx_eth_tuser  : out std_logic
  );
end entity udp_to_ocpi;

architecture rtl of udp_to_ocpi is

  -- The UDP Payload AXI-Stream Width
  constant UDP_DATA_WIDTH : natural := ETH_DATA_WIDTH;
  constant UDP_KEEP_WIDTH : natural := ETH_KEEP_WIDTH;

  -- The Internal AXI-Stream Width
  constant AXIS_DATA_WIDTH : natural := SDP_WIDTH*32;
  constant AXIS_KEEP_WIDTH : natural := SDP_WIDTH*4;

  -- Ethernet Receive Register Slice
  signal rx_eth_tdata_r  : std_logic_vector(ETH_DATA_WIDTH-1 downto 0);
  signal rx_eth_tkeep_r  : std_logic_vector(ETH_KEEP_WIDTH-1 downto 0);
  signal rx_eth_tvalid_r : std_logic;
  signal rx_eth_tready_r : std_logic;
  signal rx_eth_tlast_r  : std_logic;
  signal rx_eth_tuser_r  : std_logic;

  -- Ethernet Receive
  signal rx_eth_hdr_valid           : std_logic;
  signal rx_eth_hdr_ready           : std_logic;
  signal rx_eth_dest_mac            : std_logic_vector(47 downto 0);
  signal rx_eth_src_mac             : std_logic_vector(47 downto 0);
  signal rx_eth_type                : std_logic_vector(15 downto 0);
  signal rx_eth_payload_axis_tdata  : std_logic_vector(ETH_DATA_WIDTH-1 downto 0);
  signal rx_eth_payload_axis_tkeep  : std_logic_vector(ETH_KEEP_WIDTH-1 downto 0);
  signal rx_eth_payload_axis_tvalid : std_logic;
  signal rx_eth_payload_axis_tready : std_logic;
  signal rx_eth_payload_axis_tlast  : std_logic;
  signal rx_eth_payload_axis_tuser  : std_logic;

  -- Ethernet Transmit Register Slice
  signal tx_eth_tdata_r  : std_logic_vector(ETH_DATA_WIDTH-1 downto 0);
  signal tx_eth_tkeep_r  : std_logic_vector(ETH_KEEP_WIDTH-1 downto 0);
  signal tx_eth_tvalid_r : std_logic;
  signal tx_eth_tready_r : std_logic;
  signal tx_eth_tlast_r  : std_logic;
  signal tx_eth_tuser_r  : std_logic;

  -- Ethernet Transmit
  signal tx_eth_hdr_valid           : std_logic;
  signal tx_eth_hdr_ready           : std_logic;
  signal tx_eth_dest_mac            : std_logic_vector(47 downto 0);
  signal tx_eth_src_mac             : std_logic_vector(47 downto 0);
  signal tx_eth_type                : std_logic_vector(15 downto 0);
  signal tx_eth_payload_axis_tdata  : std_logic_vector(ETH_DATA_WIDTH-1 downto 0);
  signal tx_eth_payload_axis_tkeep  : std_logic_vector(ETH_KEEP_WIDTH-1 downto 0);
  signal tx_eth_payload_axis_tvalid : std_logic;
  signal tx_eth_payload_axis_tready : std_logic;
  signal tx_eth_payload_axis_tlast  : std_logic;
  signal tx_eth_payload_axis_tuser  : std_logic;

  -- UDP Receive
  signal rx_udp_hdr_valid           : std_logic;
  signal rx_udp_hdr_ready           : std_logic;
  signal rx_udp_eth_dest_mac        : std_logic_vector(47 downto 0);
  signal rx_udp_eth_src_mac         : std_logic_vector(47 downto 0);
  signal rx_udp_eth_type            : std_logic_vector(15 downto 0);
  signal rx_udp_ip_version          : std_logic_vector(3 downto 0);
  signal rx_udp_ip_ihl              : std_logic_vector(3 downto 0);
  signal rx_udp_ip_dscp             : std_logic_vector(5 downto 0);
  signal rx_udp_ip_ecn              : std_logic_vector(1 downto 0);
  signal rx_udp_ip_length           : std_logic_vector(15 downto 0);
  signal rx_udp_ip_identification   : std_logic_vector(15 downto 0);
  signal rx_udp_ip_flags            : std_logic_vector(2 downto 0);
  signal rx_udp_ip_fragment_offset  : std_logic_vector(12 downto 0);
  signal rx_udp_ip_ttl              : std_logic_vector(7 downto 0);
  signal rx_udp_ip_protocol         : std_logic_vector(7 downto 0);
  signal rx_udp_ip_header_checksum  : std_logic_vector(15 downto 0);
  signal rx_udp_ip_source_ip        : std_logic_vector(31 downto 0);
  signal rx_udp_ip_dest_ip          : std_logic_vector(31 downto 0);
  signal rx_udp_source_port         : std_logic_vector(15 downto 0);
  signal rx_udp_dest_port           : std_logic_vector(15 downto 0);
  signal rx_udp_length              : std_logic_vector(15 downto 0);
  signal rx_udp_checksum            : std_logic_vector(15 downto 0);
  signal rx_udp_payload_axis_tdata  : std_logic_vector(UDP_DATA_WIDTH-1 downto 0);
  signal rx_udp_payload_axis_tkeep  : std_logic_vector(UDP_KEEP_WIDTH-1 downto 0);
  signal rx_udp_payload_axis_tvalid : std_logic;
  signal rx_udp_payload_axis_tready : std_logic;
  signal rx_udp_payload_axis_tlast  : std_logic;
  signal rx_udp_payload_axis_tuser  : std_logic;

  -- UDP Transmit
  signal tx_udp_hdr_valid           : std_logic;
  signal tx_udp_hdr_ready           : std_logic;
  signal tx_udp_ip_dscp             : std_logic_vector(5 downto 0);
  signal tx_udp_ip_ecn              : std_logic_vector(1 downto 0);
  signal tx_udp_ip_ttl              : std_logic_vector(7 downto 0);
  signal tx_udp_ip_source_ip        : std_logic_vector(31 downto 0);
  signal tx_udp_ip_dest_ip          : std_logic_vector(31 downto 0);
  signal tx_udp_source_port         : std_logic_vector(15 downto 0);
  signal tx_udp_dest_port           : std_logic_vector(15 downto 0);
  signal tx_udp_length              : std_logic_vector(15 downto 0);
  signal tx_udp_checksum            : std_logic_vector(15 downto 0);
  signal tx_udp_payload_axis_tdata  : std_logic_vector(UDP_DATA_WIDTH-1 downto 0);
  signal tx_udp_payload_axis_tkeep  : std_logic_vector(UDP_KEEP_WIDTH-1 downto 0);
  signal tx_udp_payload_axis_tvalid : std_logic;
  signal tx_udp_payload_axis_tready : std_logic;
  signal tx_udp_payload_axis_tlast  : std_logic;
  signal tx_udp_payload_axis_tuser  : std_logic;

  -- Receive packets without Ethernet header
  signal rx_hdr_type : std_logic_vector(15 downto 0);

  signal rx_axis_tdata  : std_logic_vector(AXIS_DATA_WIDTH-1 downto 0);
  signal rx_axis_tkeep  : std_logic_vector(AXIS_KEEP_WIDTH-1 downto 0);
  signal rx_axis_tvalid : std_logic;
  signal rx_axis_tready : std_logic;
  signal rx_axis_tlast  : std_logic;

  -- Transmit packets without Ethernet header
  signal tx_hdr_type : std_logic_vector(15 downto 0);

  signal tx_axis_tdata  : std_logic_vector(AXIS_DATA_WIDTH-1 downto 0);
  signal tx_axis_tkeep  : std_logic_vector(AXIS_KEEP_WIDTH-1 downto 0);
  signal tx_axis_tvalid : std_logic;
  signal tx_axis_tready : std_logic;
  signal tx_axis_tlast  : std_logic;

  -- Received Control Plane packets
  signal cp_rx_axis_tdata  : std_logic_vector(AXIS_DATA_WIDTH-1 downto 0);
  signal cp_rx_axis_tkeep  : std_logic_vector(AXIS_KEEP_WIDTH-1 downto 0);
  signal cp_rx_axis_tvalid : std_logic;
  signal cp_rx_axis_tready : std_logic;
  signal cp_rx_axis_tlast  : std_logic;

  signal cp_rx_axis_tdata_r  : std_logic_vector(AXIS_DATA_WIDTH-1 downto 0);
  signal cp_rx_axis_tkeep_r  : std_logic_vector(AXIS_KEEP_WIDTH-1 downto 0);
  signal cp_rx_axis_tvalid_r : std_logic;
  signal cp_rx_axis_tready_r : std_logic;
  signal cp_rx_axis_tlast_r  : std_logic;

  -- Received Data Plane packets
  signal sdp_rx_axis_tdata  : std_logic_vector(AXIS_DATA_WIDTH-1 downto 0);
  signal sdp_rx_axis_tkeep  : std_logic_vector(AXIS_KEEP_WIDTH-1 downto 0);
  signal sdp_rx_axis_tvalid : std_logic;
  signal sdp_rx_axis_tready : std_logic;
  signal sdp_rx_axis_tlast  : std_logic;

  signal sdp_rx_axis_tdata_r  : std_logic_vector(AXIS_DATA_WIDTH-1 downto 0);
  signal sdp_rx_axis_tkeep_r  : std_logic_vector(AXIS_KEEP_WIDTH-1 downto 0);
  signal sdp_rx_axis_tvalid_r : std_logic;
  signal sdp_rx_axis_tready_r : std_logic;
  signal sdp_rx_axis_tlast_r  : std_logic;

  -- Transmit Control Plane packets
  signal cp_tx_axis_tdata  : std_logic_vector(AXIS_DATA_WIDTH-1 downto 0);
  signal cp_tx_axis_tkeep  : std_logic_vector(AXIS_KEEP_WIDTH-1 downto 0);
  signal cp_tx_axis_tvalid : std_logic;
  signal cp_tx_axis_tready : std_logic;
  signal cp_tx_axis_tlast  : std_logic;

  signal cp_tx_axis_tdata_r  : std_logic_vector(AXIS_DATA_WIDTH-1 downto 0);
  signal cp_tx_axis_tkeep_r  : std_logic_vector(AXIS_KEEP_WIDTH-1 downto 0);
  signal cp_tx_axis_tvalid_r : std_logic;
  signal cp_tx_axis_tready_r : std_logic;
  signal cp_tx_axis_tlast_r  : std_logic;

  -- Transmit Data Plane packets
  signal sdp_tx_axis_tdata  : std_logic_vector(AXIS_DATA_WIDTH-1 downto 0);
  signal sdp_tx_axis_tkeep  : std_logic_vector(AXIS_KEEP_WIDTH-1 downto 0);
  signal sdp_tx_axis_tvalid : std_logic;
  signal sdp_tx_axis_tready : std_logic;
  signal sdp_tx_axis_tlast  : std_logic;

  signal sdp_tx_axis_tdata_r  : std_logic_vector(AXIS_DATA_WIDTH-1 downto 0);
  signal sdp_tx_axis_tkeep_r  : std_logic_vector(AXIS_KEEP_WIDTH-1 downto 0);
  signal sdp_tx_axis_tvalid_r : std_logic;
  signal sdp_tx_axis_tready_r : std_logic;
  signal sdp_tx_axis_tlast_r  : std_logic;

  -- SDP->CP FLAG WRITE
  signal flag_addr  : std_logic_vector(23 downto 0);
  signal flag_data  : std_logic_vector(31 downto 0);
  signal flag_valid : std_logic;
  signal flag_take  : std_logic;

  -- Psuedo address replacing MAC address with ip-addr:udp-port
  signal remote_pseudo_addr : std_logic_vector(47 downto 0);

begin

-- --------------------------------------------------
-- REMOTE PSEUDO (MAC) address
remote_pseudo_addr(31 downto 0)  <= remote_ip_addr;
remote_pseudo_addr(47 downto 32) <= remote_udp_port;

-- ---------------------------------------------------
-- REGISTER RECEIVED ETHERNET FRAME
-- (register slice with registered tready used to prevent
-- long combinatorial paths from extending into the ethernet MAC)
rx_pipeline_register_inst: entity work.dgrdma_axis_pipeline
  generic map (
    DATA_WIDTH  => ETH_DATA_WIDTH,
    KEEP_WIDTH  => ETH_KEEP_WIDTH,
    LENGTH      => 1
  )
  port map (
    clk   => clk,
    reset => reset,

    -- AXI input (from ethernet MAC)
    s_axis_tdata    => rx_eth_tdata,
    s_axis_tkeep    => rx_eth_tkeep,
    s_axis_tvalid   => rx_eth_tvalid,
    s_axis_tready   => rx_eth_tready,
    s_axis_tlast    => rx_eth_tlast,
    s_axis_tuser    => rx_eth_tuser,

    -- AXI output (to ethernet parser, ethernet axis rx)
    m_axis_tdata    => rx_eth_tdata_r,
    m_axis_tkeep    => rx_eth_tkeep_r,
    m_axis_tvalid   => rx_eth_tvalid_r,
    m_axis_tready   => rx_eth_tready_r,
    m_axis_tlast    => rx_eth_tlast_r,
    m_axis_tuser    => rx_eth_tuser_r
  );

-- ---------------------------------------------------
-- REGISTER TRANSMIT ETHERNET FRAME
-- (register slice with registered tready used to prevent
-- long combinatorial paths from extending into the ethernet MAC)
tx_pipeline_register_inst:  entity work.dgrdma_axis_pipeline
  generic map (
    DATA_WIDTH  => ETH_DATA_WIDTH,
    KEEP_WIDTH  => ETH_KEEP_WIDTH,
    LENGTH      => 1
  )
  port map (
    clk   => clk,
    reset => reset,

    -- AXI input (from ethernet generator, ethernet axis tx)
    s_axis_tdata    => tx_eth_tdata_r,
    s_axis_tkeep    => tx_eth_tkeep_r,
    s_axis_tvalid   => tx_eth_tvalid_r,
    s_axis_tready   => tx_eth_tready_r,
    s_axis_tlast    => tx_eth_tlast_r,
    s_axis_tuser    => tx_eth_tuser_r,

    -- AXI output (to ethernet MAC)
    m_axis_tdata    => tx_eth_tdata,
    m_axis_tkeep    => tx_eth_tkeep,
    m_axis_tvalid   => tx_eth_tvalid,
    m_axis_tready   => tx_eth_tready,
    m_axis_tlast    => tx_eth_tlast,
    m_axis_tuser    => tx_eth_tuser
  );

-- ---------------------------------------------------
-- PARSE RECEIVED ETHERNET FRAME
-- (parse the incoming ethernet frame, extracting the
-- source MAC, destination MAC, ether-type and payload)
axis_to_eth_inst: entity work.eth_axis_rx_wrapper
  generic map(
    DATA_WIDTH  => ETH_DATA_WIDTH,
    KEEP_ENABLE => (ETH_DATA_WIDTH>8),
    KEEP_WIDTH  => ETH_KEEP_WIDTH
  )
  port map(
    clk => clk,
    rst => reset,

    -- AXI input (from registered ethernet MAC)
    s_axis_tdata  => rx_eth_tdata_r,
    s_axis_tkeep  => rx_eth_tkeep_r,
    s_axis_tvalid => rx_eth_tvalid_r,
    s_axis_tready => rx_eth_tready_r,
    s_axis_tlast  => rx_eth_tlast_r,
    s_axis_tuser  => rx_eth_tuser_r,

    -- Ethernet frame output (to UDP complete)
    m_eth_hdr_valid              => rx_eth_hdr_valid,
    m_eth_hdr_ready              => rx_eth_hdr_ready,
    m_eth_dest_mac               => rx_eth_dest_mac,
    m_eth_src_mac                => rx_eth_src_mac,
    m_eth_type                   => rx_eth_type,
    m_eth_payload_axis_tdata     => rx_eth_payload_axis_tdata,
    m_eth_payload_axis_tkeep     => rx_eth_payload_axis_tkeep,
    m_eth_payload_axis_tvalid    => rx_eth_payload_axis_tvalid,
    m_eth_payload_axis_tready    => rx_eth_payload_axis_tready,
    m_eth_payload_axis_tlast     => rx_eth_payload_axis_tlast,
    m_eth_payload_axis_tuser     => rx_eth_payload_axis_tuser,

    -- Status signals
    busy => open,
    error_header_early_termination => open
  );

-- ---------------------------------------------------
-- GENERATE TRANSMIT ETHERNET FRAME
-- (construct an outbound ethernet frame from
-- source MAC, destination MAC, ether-type and payload)
eth_to_axis_inst: entity work.eth_axis_tx_wrapper
  generic map(
    DATA_WIDTH  => ETH_DATA_WIDTH,
    KEEP_ENABLE => (ETH_DATA_WIDTH>8),
    KEEP_WIDTH  => ETH_KEEP_WIDTH
  )
  port map(
    clk => clk,
    rst => reset,

    -- Ethernet frame input (from UDP complete)
    s_eth_hdr_valid           => tx_eth_hdr_valid,
    s_eth_hdr_ready           => tx_eth_hdr_ready,
    s_eth_dest_mac            => tx_eth_dest_mac,
    s_eth_src_mac             => tx_eth_src_mac,
    s_eth_type                => tx_eth_type,
    s_eth_payload_axis_tdata  => tx_eth_payload_axis_tdata,
    s_eth_payload_axis_tkeep  => tx_eth_payload_axis_tkeep,
    s_eth_payload_axis_tvalid => tx_eth_payload_axis_tvalid,
    s_eth_payload_axis_tready => tx_eth_payload_axis_tready,
    s_eth_payload_axis_tlast  => tx_eth_payload_axis_tlast,
    s_eth_payload_axis_tuser  => tx_eth_payload_axis_tuser,

    -- AXI output (to ethernet MAC)
    m_axis_tdata  => tx_eth_tdata_r,
    m_axis_tkeep  => tx_eth_tkeep_r,
    m_axis_tvalid => tx_eth_tvalid_r,
    m_axis_tready => tx_eth_tready_r,
    m_axis_tlast  => tx_eth_tlast_r,
    m_axis_tuser  => tx_eth_tuser_r,

    -- Status signals
    busy => open
  );

-- ---------------------------------------------------
-- IP/UDP RECEIVE/TRANSMIT PACKET HANDLING
udp_inst : entity work.udp_complete_wrapper
  generic map(
    DATA_WIDTH => ETH_DATA_WIDTH,
    KEEP_WIDTH => ETH_KEEP_WIDTH,
    UDP_CHECKSUM_GEN_ENABLE => 1,
    UDP_CHECKSUM_PAYLOAD_FIFO_DEPTH => MAX_FRAME_SIZE,
    UDP_CHECKSUM_HEADER_FIFO_DEPTH => 8
  )
  port map(
    clk => clk,
    rst => reset,

    -- Inbound ethernet frame (input to this component)
    s_eth_hdr_valid           => rx_eth_hdr_valid,
    s_eth_hdr_ready           => rx_eth_hdr_ready,
    s_eth_dest_mac            => rx_eth_dest_mac,
    s_eth_src_mac             => rx_eth_src_mac,
    s_eth_type                => rx_eth_type,
    s_eth_payload_axis_tdata  => rx_eth_payload_axis_tdata,
    s_eth_payload_axis_tkeep  => rx_eth_payload_axis_tkeep,
    s_eth_payload_axis_tvalid => rx_eth_payload_axis_tvalid,
    s_eth_payload_axis_tready => rx_eth_payload_axis_tready,
    s_eth_payload_axis_tlast  => rx_eth_payload_axis_tlast,
    s_eth_payload_axis_tuser  => rx_eth_payload_axis_tuser,

    -- outbound ethernet frame (output from this component)
    m_eth_hdr_valid           => tx_eth_hdr_valid,
    m_eth_hdr_ready           => tx_eth_hdr_ready,
    m_eth_dest_mac            => tx_eth_dest_mac,
    m_eth_src_mac             => tx_eth_src_mac,
    m_eth_type                => tx_eth_type,
    m_eth_payload_axis_tdata  => tx_eth_payload_axis_tdata,
    m_eth_payload_axis_tkeep  => tx_eth_payload_axis_tkeep,
    m_eth_payload_axis_tvalid => tx_eth_payload_axis_tvalid,
    m_eth_payload_axis_tready => tx_eth_payload_axis_tready,
    m_eth_payload_axis_tlast  => tx_eth_payload_axis_tlast,
    m_eth_payload_axis_tuser  => tx_eth_payload_axis_tuser,

    -- Outbound IP frame (input to this component), not used
    s_ip_hdr_valid            => '0',
    s_ip_hdr_ready            => open,
    s_ip_dscp                 => (others => '0'),
    s_ip_ecn                  => (others => '0'),
    s_ip_length               => (others => '0'),
    s_ip_ttl                  => (others => '0'),
    s_ip_protocol             => (others => '0'),
    s_ip_source_ip            => (others => '0'),
    s_ip_dest_ip              => (others => '0'),
    s_ip_payload_axis_tdata   => (others => '0'),
    s_ip_payload_axis_tkeep   => (others => '0'),
    s_ip_payload_axis_tvalid  => '0',
    s_ip_payload_axis_tready  => open,
    s_ip_payload_axis_tlast   => '0',
    s_ip_payload_axis_tuser   => '0',

    -- Inbound IP (output from this component), not used
    m_ip_hdr_valid            => open,
    m_ip_hdr_ready            => '1',
    m_ip_eth_dest_mac         => open,
    m_ip_eth_src_mac          => open,
    m_ip_eth_type             => open,
    m_ip_version              => open,
    m_ip_ihl                  => open,
    m_ip_dscp                 => open,
    m_ip_ecn                  => open,
    m_ip_length               => open,
    m_ip_identification       => open,
    m_ip_flags                => open,
    m_ip_fragment_offset      => open,
    m_ip_ttl                  => open,
    m_ip_protocol             => open,
    m_ip_header_checksum      => open,
    m_ip_source_ip            => open,
    m_ip_dest_ip              => open,
    m_ip_payload_axis_tdata   => open,
    m_ip_payload_axis_tkeep   => open,
    m_ip_payload_axis_tvalid  => open,
    m_ip_payload_axis_tready  => '1',
    m_ip_payload_axis_tlast   => open,
    m_ip_payload_axis_tuser   => open,

    -- Outbound UDP (input to this component),
    -- UDP packets to send
    s_udp_hdr_valid           => tx_udp_hdr_valid,
    s_udp_hdr_ready           => tx_udp_hdr_ready,
    s_udp_ip_dscp             => tx_udp_ip_dscp,
    s_udp_ip_ecn              => tx_udp_ip_ecn,
    s_udp_ip_ttl              => tx_udp_ip_ttl,
    s_udp_ip_source_ip        => tx_udp_ip_source_ip,
    s_udp_ip_dest_ip          => tx_udp_ip_dest_ip,
    s_udp_source_port         => tx_udp_source_port,
    s_udp_dest_port           => tx_udp_dest_port,
    s_udp_length              => tx_udp_length,
    s_udp_checksum            => tx_udp_checksum,
    s_udp_payload_axis_tdata  => tx_udp_payload_axis_tdata,
    s_udp_payload_axis_tkeep  => tx_udp_payload_axis_tkeep,
    s_udp_payload_axis_tvalid => tx_udp_payload_axis_tvalid,
    s_udp_payload_axis_tready => tx_udp_payload_axis_tready,
    s_udp_payload_axis_tlast  => tx_udp_payload_axis_tlast,
    s_udp_payload_axis_tuser  => tx_udp_payload_axis_tuser,

    -- Inbound UDP (output from this component)
    -- received UDP packets
    m_udp_hdr_valid           => rx_udp_hdr_valid,
    m_udp_hdr_ready           => rx_udp_hdr_ready,
    m_udp_eth_dest_mac        => rx_udp_eth_dest_mac,
    m_udp_eth_src_mac         => rx_udp_eth_src_mac,
    m_udp_eth_type            => rx_udp_eth_type,
    m_udp_ip_version          => rx_udp_ip_version,
    m_udp_ip_ihl              => rx_udp_ip_ihl,
    m_udp_ip_dscp             => rx_udp_ip_dscp,
    m_udp_ip_ecn              => rx_udp_ip_ecn,
    m_udp_ip_length           => rx_udp_ip_length,
    m_udp_ip_identification   => rx_udp_ip_identification,
    m_udp_ip_flags            => rx_udp_ip_flags,
    m_udp_ip_fragment_offset  => rx_udp_ip_fragment_offset,
    m_udp_ip_ttl              => rx_udp_ip_ttl,
    m_udp_ip_protocol         => rx_udp_ip_protocol,
    m_udp_ip_header_checksum  => rx_udp_ip_header_checksum,
    m_udp_ip_source_ip        => rx_udp_ip_source_ip,
    m_udp_ip_dest_ip          => rx_udp_ip_dest_ip,
    m_udp_source_port         => rx_udp_source_port,
    m_udp_dest_port           => rx_udp_dest_port,
    m_udp_length              => rx_udp_length,
    m_udp_checksum            => rx_udp_checksum,
    m_udp_payload_axis_tdata  => rx_udp_payload_axis_tdata,
    m_udp_payload_axis_tkeep  => rx_udp_payload_axis_tkeep,
    m_udp_payload_axis_tvalid => rx_udp_payload_axis_tvalid,
    m_udp_payload_axis_tready => rx_udp_payload_axis_tready,
    m_udp_payload_axis_tlast  => rx_udp_payload_axis_tlast,
    m_udp_payload_axis_tuser  => rx_udp_payload_axis_tuser,

    -- Status
    ip_rx_busy                             => open,
    ip_tx_busy                             => open,
    udp_rx_busy                            => open,
    udp_tx_busy                            => open,
    ip_rx_error_header_early_termination   => open,
    ip_rx_error_payload_early_termination  => open,
    ip_rx_error_invalid_header             => open,
    ip_rx_error_invalid_checksum           => open,
    ip_tx_error_payload_early_termination  => open,
    ip_tx_error_arp_failed                 => open,
    udp_rx_error_header_early_termination  => open,
    udp_rx_error_payload_early_termination => open,
    udp_tx_error_payload_early_termination => open,

    -- Configuration
    local_mac       => local_mac_addr,
    local_ip        => local_ip_addr,
    gateway_ip      => local_gateway_ip,
    subnet_mask     => local_subnet_mask,
    clear_arp_cache => '0'
  );

-- ---------------------------------------------------
-- UDP FRAME PARSER
-- (parse inbound UDP header and payload. creates an
-- axi-stream containing the UDP payload with prepended header
-- comprising the source IP address and source UDP port.
-- this component filters packets based on destination MAC and
-- destination IP address)
udp_frame_parser_inst : entity work.udp_frame_parser
  generic map(
    UDP_DATA_WIDTH => UDP_DATA_WIDTH,
    UDP_KEEP_WIDTH => UDP_KEEP_WIDTH,
    DATA_WIDTH => AXIS_DATA_WIDTH,
    KEEP_WIDTH => AXIS_KEEP_WIDTH
  )
  port map(
    clk => clk,
    reset => reset,

    local_mac_addr  => local_mac_addr,
    local_ip_addr   => local_ip_addr,

    -- inbound UDP packet (from UDP complete component)
    s_udp_hdr_valid           => rx_udp_hdr_valid,
    s_udp_hdr_ready           => rx_udp_hdr_ready,
    s_udp_eth_dest_mac        => rx_udp_eth_dest_mac,
    s_udp_eth_src_mac         => rx_udp_eth_src_mac,
    s_udp_eth_type            => rx_udp_eth_type,
    s_udp_ip_version          => rx_udp_ip_version,
    s_udp_ip_ihl              => rx_udp_ip_ihl,
    s_udp_ip_dscp             => rx_udp_ip_dscp,
    s_udp_ip_ecn              => rx_udp_ip_ecn,
    s_udp_ip_length           => rx_udp_ip_length,
    s_udp_ip_identification   => rx_udp_ip_identification,
    s_udp_ip_flags            => rx_udp_ip_flags,
    s_udp_ip_fragment_offset  => rx_udp_ip_fragment_offset,
    s_udp_ip_ttl              => rx_udp_ip_ttl,
    s_udp_ip_protocol         => rx_udp_ip_protocol,
    s_udp_ip_header_checksum  => rx_udp_ip_header_checksum,
    s_udp_ip_source_ip        => rx_udp_ip_source_ip,
    s_udp_ip_dest_ip          => rx_udp_ip_dest_ip,
    s_udp_source_port         => rx_udp_source_port,
    s_udp_dest_port           => rx_udp_dest_port,
    s_udp_length              => rx_udp_length,
    s_udp_checksum            => rx_udp_checksum,
    s_udp_payload_axis_tdata  => rx_udp_payload_axis_tdata,
    s_udp_payload_axis_tkeep  => rx_udp_payload_axis_tkeep,
    s_udp_payload_axis_tvalid => rx_udp_payload_axis_tvalid,
    s_udp_payload_axis_tready => rx_udp_payload_axis_tready,
    s_udp_payload_axis_tlast  => rx_udp_payload_axis_tlast,
    s_udp_payload_axis_tuser  => rx_udp_payload_axis_tuser,

    -- inbound axi-stream containing source IP, source UDP port
    -- and UDP payload
    m_rx_axis_tdata  => rx_axis_tdata,
    m_rx_axis_tkeep  => rx_axis_tkeep,
    m_rx_axis_tvalid => rx_axis_tvalid,
    m_rx_axis_tready => rx_axis_tready,
    m_rx_axis_tlast  => rx_axis_tlast,

    -- inbound destination UDP port
    udp_dest_port => rx_hdr_type
  );

-- ---------------------------------------------------
-- UDP FRAME GENERATOR
-- (generates outbound UDP packets with separate header
-- and payload streams. the destination IP address and
-- UDP port are extracted from the axi-stream)
udp_frame_generator_inst : entity work.udp_frame_generator
  generic map(
    UDP_DATA_WIDTH => UDP_DATA_WIDTH,
    UDP_KEEP_WIDTH => UDP_KEEP_WIDTH,
    DATA_WIDTH => AXIS_DATA_WIDTH,
    KEEP_WIDTH => AXIS_KEEP_WIDTH
  )
  port map(
    clk => clk,
    reset => reset,

    -- configuration
    local_ip_addr => local_ip_addr,

    -- outbound axi-stream containing destination IP, destination UDP port
    -- and UDP payload
    s_tx_axis_tdata => tx_axis_tdata,
    s_tx_axis_tkeep => tx_axis_tkeep,
    s_tx_axis_tvalid => tx_axis_tvalid,
    s_tx_axis_tready => tx_axis_tready,
    s_tx_axis_tlast => tx_axis_tlast,

    -- outbound source UDP port
    tx_hdr_type => tx_hdr_type,

    -- outbound UDP packet (to UDP complete component)
    m_udp_hdr_valid           => tx_udp_hdr_valid,
    m_udp_hdr_ready           => tx_udp_hdr_ready,
    m_udp_ip_dscp             => tx_udp_ip_dscp,
    m_udp_ip_ecn              => tx_udp_ip_ecn,
    m_udp_ip_ttl              => tx_udp_ip_ttl,
    m_udp_ip_source_ip        => tx_udp_ip_source_ip,
    m_udp_ip_dest_ip          => tx_udp_ip_dest_ip,
    m_udp_source_port         => tx_udp_source_port,
    m_udp_dest_port           => tx_udp_dest_port,
    m_udp_length              => tx_udp_length,
    m_udp_checksum            => tx_udp_checksum,
    m_udp_payload_axis_tdata  => tx_udp_payload_axis_tdata,
    m_udp_payload_axis_tkeep  => tx_udp_payload_axis_tkeep,
    m_udp_payload_axis_tvalid => tx_udp_payload_axis_tvalid,
    m_udp_payload_axis_tready => tx_udp_payload_axis_tready,
    m_udp_payload_axis_tlast  => tx_udp_payload_axis_tlast,
    m_udp_payload_axis_tuser  => tx_udp_payload_axis_tuser
  );

-- ---------------------------------------------------
-- RECEIVE PACKET ROUTING
-- (routes the inbound packet to either the OCPI control plane
-- or data plane depending on the UDP destination port.
-- packets sent to other ports are dropped).
eth_frame_router_inst : entity work.eth_frame_router
  generic map (
    DATA_WIDTH => AXIS_DATA_WIDTH,
    KEEP_WIDTH => AXIS_KEEP_WIDTH,
    CP_TYPE    => UDP_CP_PORT,
    SDP_TYPE   => UDP_SDP_PORT
  )
  port map(
    clk   => clk,
    reset => reset,

    -- route between CP and SDP using header type (UDP Destination Port)
    local_mac_addr  => (others => '0'),
    rx_hdr_dest_mac => (others => '0'),

    -- inbound destination UDP port. used to route packet
    -- to control or data-plane
    rx_hdr_type     => rx_hdr_type,

    -- inbound packet (from UDP frame parser)
    s_axis_tdata    => rx_axis_tdata,
    s_axis_tkeep    => rx_axis_tkeep,
    s_axis_tvalid   => rx_axis_tvalid,
    s_axis_tlast    => rx_axis_tlast,
    s_axis_tready   => rx_axis_tready,

    -- inbound control-plane
    m_axis_tdata_cp  => cp_rx_axis_tdata,
    m_axis_tkeep_cp  => cp_rx_axis_tkeep,
    m_axis_tvalid_cp => cp_rx_axis_tvalid,
    m_axis_tlast_cp  => cp_rx_axis_tlast,
    m_axis_tready_cp => cp_rx_axis_tready,

    -- inbound data-plane
    m_axis_tdata_sdp  => sdp_rx_axis_tdata,
    m_axis_tkeep_sdp  => sdp_rx_axis_tkeep,
    m_axis_tvalid_sdp => sdp_rx_axis_tvalid,
    m_axis_tlast_sdp  => sdp_rx_axis_tlast,
    m_axis_tready_sdp => sdp_rx_axis_tready
  );

-- ---------------------------------------------------
-- TRANSMIT PACKET ARBITER
-- (combines packets from the control-plane and data-plane into
-- a single axi-stream.)
eth_frame_arbiter_inst : entity work.eth_frame_arbiter
  generic map (
    DATA_WIDTH => AXIS_DATA_WIDTH,
    KEEP_WIDTH => AXIS_KEEP_WIDTH,
    CP_TYPE    => UDP_CP_PORT,
    SDP_TYPE   => UDP_SDP_PORT
  )
  port map(
    clk   => clk,
    reset => reset,

    -- outbound control-plane
    s_axis_tdata_cp   => cp_tx_axis_tdata,
    s_axis_tkeep_cp   => cp_tx_axis_tkeep,
    s_axis_tvalid_cp  => cp_tx_axis_tvalid,
    s_axis_tlast_cp   => cp_tx_axis_tlast,
    s_axis_tready_cp  => cp_tx_axis_tready,

    -- outbound data-plane
    s_axis_tdata_sdp  => sdp_tx_axis_tdata,
    s_axis_tkeep_sdp  => sdp_tx_axis_tkeep,
    s_axis_tvalid_sdp => sdp_tx_axis_tvalid,
    s_axis_tlast_sdp  => sdp_tx_axis_tlast,
    s_axis_tready_sdp => sdp_tx_axis_tready,

    -- outbound packet (to UDP frame generator)
    m_axis_tdata      => tx_axis_tdata,
    m_axis_tkeep      => tx_axis_tkeep,
    m_axis_tvalid     => tx_axis_tvalid,
    m_axis_tlast      => tx_axis_tlast,
    m_axis_tready     => tx_axis_tready,

    -- sending UDP port
    tx_hdr_type  => tx_hdr_type
  );

-- ---------------------------------------------------
-- REGISTER SLICES
-- (register slices with registered tready used to prevent
-- long combinatorial paths from extending from ocpi into the IP/UDP)
cp_rx_pipeline_register_inst:  entity work.dgrdma_axis_pipeline
  generic map (
    DATA_WIDTH  => AXIS_DATA_WIDTH,
    KEEP_WIDTH  => AXIS_KEEP_WIDTH,
    LENGTH      => 1
  )
  port map (
    clk             => clk,
    reset           => reset,

    -- AXI input (from frame router)
    s_axis_tdata    => cp_rx_axis_tdata,
    s_axis_tkeep    => cp_rx_axis_tkeep,
    s_axis_tvalid   => cp_rx_axis_tvalid,
    s_axis_tready   => cp_rx_axis_tready,
    s_axis_tlast    => cp_rx_axis_tlast,
    s_axis_tuser    => '0',

    -- AXI output (to control plane master)
    m_axis_tdata    => cp_rx_axis_tdata_r,
    m_axis_tkeep    => cp_rx_axis_tkeep_r,
    m_axis_tvalid   => cp_rx_axis_tvalid_r,
    m_axis_tready   => cp_rx_axis_tready_r,
    m_axis_tlast    => cp_rx_axis_tlast_r,
    m_axis_tuser    => open
  );

sdp_rx_pipeline_register_inst:  entity work.dgrdma_axis_pipeline
  generic map (
    DATA_WIDTH  => AXIS_DATA_WIDTH,
    KEEP_WIDTH  => AXIS_KEEP_WIDTH,
    LENGTH      => 1
  )
  port map (
    clk             => clk,
    reset           => reset,

    -- AXI input (from frame router)
    s_axis_tdata    => sdp_rx_axis_tdata,
    s_axis_tkeep    => sdp_rx_axis_tkeep,
    s_axis_tvalid   => sdp_rx_axis_tvalid,
    s_axis_tready   => sdp_rx_axis_tready,
    s_axis_tlast    => sdp_rx_axis_tlast,
    s_axis_tuser    => '0',

    -- AXI output (to data plane master)
    m_axis_tdata    => sdp_rx_axis_tdata_r,
    m_axis_tkeep    => sdp_rx_axis_tkeep_r,
    m_axis_tvalid   => sdp_rx_axis_tvalid_r,
    m_axis_tready   => sdp_rx_axis_tready_r,
    m_axis_tlast    => sdp_rx_axis_tlast_r,
    m_axis_tuser    => open
  );

cp_tx_pipeline_register_inst:  entity work.dgrdma_axis_pipeline
  generic map (
    DATA_WIDTH  => AXIS_DATA_WIDTH,
    KEEP_WIDTH  => AXIS_KEEP_WIDTH,
    LENGTH      => 1
  )
  port map (
    clk             => clk,
    reset           => reset,

    -- AXI input (from control-plane master)
    s_axis_tdata    => cp_tx_axis_tdata_r,
    s_axis_tkeep    => cp_tx_axis_tkeep_r,
    s_axis_tvalid   => cp_tx_axis_tvalid_r,
    s_axis_tready   => cp_tx_axis_tready_r,
    s_axis_tlast    => cp_tx_axis_tlast_r,
    s_axis_tuser    => '0',

    -- AXI output (to frame arbiter)
    m_axis_tdata    => cp_tx_axis_tdata,
    m_axis_tkeep    => cp_tx_axis_tkeep,
    m_axis_tvalid   => cp_tx_axis_tvalid,
    m_axis_tready   => cp_tx_axis_tready,
    m_axis_tlast    => cp_tx_axis_tlast,
    m_axis_tuser    => open
  );

sdp_tx_pipeline_register_inst:  entity work.dgrdma_axis_pipeline
  generic map (
    DATA_WIDTH  => AXIS_DATA_WIDTH,
    KEEP_WIDTH  => AXIS_KEEP_WIDTH,
    LENGTH      => 1
  )
  port map (
    clk             => clk,
    reset           => reset,

    -- AXI input (from data-plane master)
    s_axis_tdata    => sdp_tx_axis_tdata_r,
    s_axis_tkeep    => sdp_tx_axis_tkeep_r,
    s_axis_tvalid   => sdp_tx_axis_tvalid_r,
    s_axis_tready   => sdp_tx_axis_tready_r,
    s_axis_tlast    => sdp_tx_axis_tlast_r,
    s_axis_tuser    => '0',

    -- AXI output (to data plane)
    m_axis_tdata    => sdp_tx_axis_tdata,
    m_axis_tkeep    => sdp_tx_axis_tkeep,
    m_axis_tvalid   => sdp_tx_axis_tvalid,
    m_axis_tready   => sdp_tx_axis_tready,
    m_axis_tlast    => sdp_tx_axis_tlast,
    m_axis_tuser    => open
  );

-- ---------------------------------------------------
-- CONTROL PLANE MASTER
cp_master : entity work.axis_to_cp
  generic map(
    DATA_WIDTH => AXIS_DATA_WIDTH,
    KEEP_WIDTH => AXIS_KEEP_WIDTH
  )
  port map(
    clk => clk,
    reset => reset,

    -- Configuration
    eth0_mac_addr => local_mac_addr,

    -- inbound control-plane
    s_axis_tdata  => cp_rx_axis_tdata_r,
    s_axis_tkeep  => cp_rx_axis_tkeep_r,
    s_axis_tvalid => cp_rx_axis_tvalid_r,
    s_axis_tlast  => cp_rx_axis_tlast_r,
    s_axis_tready => cp_rx_axis_tready_r,

    -- outbound control-plane
    m_axis_tdata  => cp_tx_axis_tdata_r,
    m_axis_tkeep  => cp_tx_axis_tkeep_r,
    m_axis_tvalid => cp_tx_axis_tvalid_r,
    m_axis_tlast  => cp_tx_axis_tlast_r,
    m_axis_tready => cp_tx_axis_tready_r,

    -- control-plane
    cp_in => cp_in,
    cp_out => cp_out,

    flag_addr => flag_addr,
    flag_data => flag_data,
    flag_valid => flag_valid,
    flag_take => flag_take,

    debug_select => (others => '0'),
    debug => open,
    test_points => open
  );

-- ---------------------------------------------------
-- DATA PLANE MASTER
sdp_master : entity work.axis_to_sdp
  generic map (
    SDP_WIDTH                  => SDP_WIDTH,
    ACK_TRACKER_BITFIELD_WIDTH => ACK_TRACKER_BITFIELD_WIDTH,
    ACK_TRACKER_MAX_ACK_COUNT  => ACK_TRACKER_MAX_ACK_COUNT,
    TXN_RECORD_MAX_TXNS_IN_FLIGHT => TXN_RECORD_MAX_TXNS_IN_FLIGHT
  )
  port map (
    clk => clk,
    reset => sdp_reset,

    -- Configuration
    remote_mac_addr      => swap_bytes(remote_pseudo_addr),
    remote_dst_id        => remote_dst_id,
    local_src_id         => local_src_id,
    interface_mtu        => interface_mtu,
    ack_wait             => ack_wait,
    max_acks_outstanding => max_acks_outstanding,
    coalesce_wait        => coalesce_wait,

    -- Ack Tracker
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

    -- inbound data-plane axi-stream
    s_axis_tdata  => sdp_rx_axis_tdata_r,
    s_axis_tvalid => sdp_rx_axis_tvalid_r,
    s_axis_tlast  => sdp_rx_axis_tlast_r,
    s_axis_tready => sdp_rx_axis_tready_r,
    s_axis_tkeep  => sdp_rx_axis_tkeep_r,

    -- outbound data-plane axi-stream
    m_axis_tdata  => sdp_tx_axis_tdata_r,
    m_axis_tvalid => sdp_tx_axis_tvalid_r,
    m_axis_tlast  => sdp_tx_axis_tlast_r,
    m_axis_tready => sdp_tx_axis_tready_r,
    m_axis_tkeep  => sdp_tx_axis_tkeep_r,

    -- data-plane
    sdp_in => sdp_in,
    sdp_in_data => sdp_in_data,
    sdp_out => sdp_out,
    sdp_out_data => sdp_out_data,

    flag_addr => flag_addr,
    flag_data => flag_data,
    flag_valid => flag_valid,
    flag_take => flag_take
  );
end rtl;
-- ---------------------------------------------------------------------------
-- END OF FILE
-- ---------------------------------------------------------------------------