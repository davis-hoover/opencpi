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
library dgrdma;

entity eth_to_ocpi is
  generic (
    SDP_WIDTH : natural := 2;
    DATA_WIDTH : natural := 64;
    KEEP_WIDTH : natural := 8;
    ACK_TRACKER_BITFIELD_WIDTH : natural;
    ACK_TRACKER_MAX_ACK_COUNT  : natural range 1 to 255;
    TXN_RECORD_MAX_TXNS_IN_FLIGHT : natural := 64
  );
  port (
    clk          : in std_logic;
    reset        : in std_logic;
    sdp_reset    : in std_logic;

    -- Configuration
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
    rx_eth_tdata : in std_logic_vector(DATA_WIDTH - 1 downto 0);
    rx_eth_tkeep : in std_logic_vector(KEEP_WIDTH - 1 downto 0);
    rx_eth_tvalid : in std_logic;
    rx_eth_tready : out std_logic;
    rx_eth_tlast : in std_logic;
    rx_eth_tuser : in std_logic;

    tx_eth_tdata : out std_logic_vector(DATA_WIDTH - 1 downto 0);
    tx_eth_tkeep : out std_logic_vector(KEEP_WIDTH - 1 downto 0);
    tx_eth_tvalid : out std_logic;
    tx_eth_tready : in std_logic;
    tx_eth_tlast : out std_logic;
    tx_eth_tuser : out std_logic
  );
end entity eth_to_ocpi;

architecture rtl of eth_to_ocpi is
  constant CP_ETHERTYPE : std_logic_vector(15 downto 0) := X"f040";
  constant SDP_ETHERTYPE : std_logic_vector(15 downto 0) := X"f042";

  -- Ethernet interface pipelining
  signal rx_eth_tdata_r  : std_logic_vector(DATA_WIDTH - 1 downto 0);
  signal rx_eth_tkeep_r  : std_logic_vector(KEEP_WIDTH - 1 downto 0);
  signal rx_eth_tvalid_r : std_logic;
  signal rx_eth_tready_r : std_logic;
  signal rx_eth_tlast_r  : std_logic;
  signal rx_eth_tuser_r  : std_logic;
  signal rx_eth_tuser_i  : std_logic;

  signal tx_eth_tdata_i  : std_logic_vector(DATA_WIDTH - 1 downto 0);
  signal tx_eth_tkeep_i  : std_logic_vector(KEEP_WIDTH - 1 downto 0);
  signal tx_eth_tvalid_i : std_logic;
  signal tx_eth_tready_i : std_logic;
  signal tx_eth_tlast_i  : std_logic;
  signal tx_eth_tuser_i  : std_logic;
  
  signal tx_eth_tdata_r  : std_logic_vector(DATA_WIDTH - 1 downto 0);
  signal tx_eth_tkeep_r  : std_logic_vector(KEEP_WIDTH - 1 downto 0);
  signal tx_eth_tvalid_r : std_logic;
  signal tx_eth_tready_r : std_logic;
  signal tx_eth_tlast_r  : std_logic;
  signal tx_eth_tuser_r  : std_logic;

  -- Receive packets without Ethernet header
  signal rx_hdr_dest_mac : std_logic_vector(47 downto 0);
  signal rx_hdr_type : std_logic_vector(15 downto 0);

  signal rx_axis_tdata : std_logic_vector((DATA_WIDTH - 1) downto 0);
  signal rx_axis_tkeep : std_logic_vector((KEEP_WIDTH - 1) downto 0);
  signal rx_axis_tvalid : std_logic;
  signal rx_axis_tready : std_logic;
  signal rx_axis_tlast : std_logic;

  -- Transmit packets without Ethernet header
  signal tx_hdr_type : std_logic_vector(15 downto 0);

  signal tx_axis_tdata : std_logic_vector((DATA_WIDTH - 1) downto 0);
  signal tx_axis_tkeep : std_logic_vector((KEEP_WIDTH - 1) downto 0);
  signal tx_axis_tvalid : std_logic;
  signal tx_axis_tready : std_logic;
  signal tx_axis_tlast : std_logic;

  -- Received Control Plane packets
  signal cp_rx_axis_tdata  : std_logic_vector((DATA_WIDTH - 1) downto 0);
  signal cp_rx_axis_tkeep  : std_logic_vector((KEEP_WIDTH - 1) downto 0);
  signal cp_rx_axis_tvalid : std_logic;
  signal cp_rx_axis_tready : std_logic;
  signal cp_rx_axis_tlast  : std_logic;

  -- Received Data Plane packets
  signal sdp_rx_axis_tdata  : std_logic_vector((DATA_WIDTH - 1) downto 0);
  signal sdp_rx_axis_tkeep  : std_logic_vector((KEEP_WIDTH - 1) downto 0);
  signal sdp_rx_axis_tvalid : std_logic;
  signal sdp_rx_axis_tready : std_logic;
  signal sdp_rx_axis_tlast  : std_logic;

  -- Transmit Control Plane packets
  signal cp_tx_axis_tdata  : std_logic_vector((DATA_WIDTH - 1) downto 0);
  signal cp_tx_axis_tkeep  : std_logic_vector((KEEP_WIDTH - 1) downto 0);
  signal cp_tx_axis_tvalid : std_logic;
  signal cp_tx_axis_tready : std_logic;
  signal cp_tx_axis_tlast  : std_logic;

  -- Transmit Data Plane packets
  signal sdp_tx_axis_tdata  : std_logic_vector((DATA_WIDTH - 1) downto 0);
  signal sdp_tx_axis_tkeep  : std_logic_vector((KEEP_WIDTH - 1) downto 0);
  signal sdp_tx_axis_tvalid : std_logic;
  signal sdp_tx_axis_tready : std_logic;
  signal sdp_tx_axis_tlast  : std_logic;

  -- SDP->CP FLAG WRITE
  signal flag_addr : std_logic_vector(23 downto 0);
  signal flag_data : std_logic_vector(31 downto 0);
  signal flag_valid : std_logic;
  signal flag_take : std_logic;
begin

  -- Insert pipeline stage to break up long paths
  rx_pipeline_inst : entity work.dgrdma_axis_pipeline
    generic map (
      DATA_WIDTH => DATA_WIDTH,
      KEEP_WIDTH => KEEP_WIDTH,
      LENGTH => 1
    )
    port map (
      clk             => clk,
      reset           => reset,

      -- AXI input
      s_axis_tdata    => rx_eth_tdata,
      s_axis_tkeep    => rx_eth_tkeep,
      s_axis_tvalid   => rx_eth_tvalid,
      s_axis_tready   => rx_eth_tready,
      s_axis_tlast    => rx_eth_tlast,
      s_axis_tuser    => rx_eth_tuser_i,

      -- AXI output
      m_axis_tdata    => rx_eth_tdata_r,
      m_axis_tkeep    => rx_eth_tkeep_r,
      m_axis_tvalid   => rx_eth_tvalid_r,
      m_axis_tready   => rx_eth_tready_r,
      m_axis_tlast    => rx_eth_tlast_r,
      m_axis_tuser    => rx_eth_tuser_r
    );
  
  tx_pipeline_inst : entity work.dgrdma_axis_pipeline
    generic map (
      DATA_WIDTH => DATA_WIDTH,
      KEEP_WIDTH => KEEP_WIDTH,
      LENGTH => 1
    )
    port map (
      clk             => clk,
      reset           => reset,

      -- AXI input
      s_axis_tdata    => tx_eth_tdata_i,
      s_axis_tkeep    => tx_eth_tkeep_i,
      s_axis_tvalid   => tx_eth_tvalid_i,
      s_axis_tready   => tx_eth_tready_i,
      s_axis_tlast    => tx_eth_tlast_i,
      s_axis_tuser    => tx_eth_tuser_i,

      -- AXI output
      m_axis_tdata    => tx_eth_tdata_r,
      m_axis_tkeep    => tx_eth_tkeep_r,
      m_axis_tvalid   => tx_eth_tvalid_r,
      m_axis_tready   => tx_eth_tready_r,
      m_axis_tlast    => tx_eth_tlast_r,
      m_axis_tuser    => tx_eth_tuser_r
    );

  rx_eth_tuser_i  <= '0';
  tx_eth_tdata    <= tx_eth_tdata_r;
  tx_eth_tkeep    <= tx_eth_tkeep_r;
  tx_eth_tvalid   <= tx_eth_tvalid_r;
  tx_eth_tready_r <= tx_eth_tready;
  tx_eth_tlast    <= tx_eth_tlast_r;
  tx_eth_tuser    <= tx_eth_tuser_r;

  -- ETHERNET FRAME HANDLING
  eth_frame_parser_inst : entity work.eth_frame_parser
    generic map(
      DATA_WIDTH => DATA_WIDTH,
      KEEP_WIDTH => KEEP_WIDTH
    )
    port map(
      clk => clk,
      reset => reset,

      s_rx_eth_tdata => rx_eth_tdata_r,
      s_rx_eth_tkeep => rx_eth_tkeep_r,
      s_rx_eth_tvalid => rx_eth_tvalid_r,
      s_rx_eth_tready => rx_eth_tready_r,
      s_rx_eth_tlast => rx_eth_tlast_r,
      s_rx_eth_tuser => rx_eth_tuser_r,

      m_rx_axis_tdata => rx_axis_tdata,
      m_rx_axis_tkeep => rx_axis_tkeep,
      m_rx_axis_tvalid => rx_axis_tvalid,
      m_rx_axis_tready => rx_axis_tready,
      m_rx_axis_tlast => rx_axis_tlast,

      m_rx_hdr_src_mac => open,
      m_rx_hdr_dest_mac => rx_hdr_dest_mac,
      m_rx_hdr_type => rx_hdr_type
    );

  eth_frame_generator_inst : entity work.eth_frame_generator
    generic map(
      DATA_WIDTH => DATA_WIDTH,
      KEEP_WIDTH => KEEP_WIDTH
    )
    port map(
      clk => clk,
      reset => reset,

      s_tx_axis_tdata => tx_axis_tdata,
      s_tx_axis_tkeep => tx_axis_tkeep,
      s_tx_axis_tvalid => tx_axis_tvalid,
      s_tx_axis_tready => tx_axis_tready,
      s_tx_axis_tlast => tx_axis_tlast,

      s_tx_hdr_src_mac => local_mac_addr,
      s_tx_hdr_type => tx_hdr_type,

      m_tx_eth_tdata => tx_eth_tdata_i,
      m_tx_eth_tkeep => tx_eth_tkeep_i,
      m_tx_eth_tvalid => tx_eth_tvalid_i,
      m_tx_eth_tready => tx_eth_tready_i,
      m_tx_eth_tlast => tx_eth_tlast_i,
      m_tx_eth_tuser => tx_eth_tuser_i
    );

  -- ---------------------------------------------------
  -- RECEIVE PACKET ROUTING
  eth_frame_router_inst : entity work.eth_frame_router
    generic map (
      DATA_WIDTH => DATA_WIDTH,
      KEEP_WIDTH => KEEP_WIDTH
    )
    port map(
      clk   => clk,
      reset => reset,

      local_mac_addr  => local_mac_addr,
      rx_hdr_dest_mac => rx_hdr_dest_mac,
      rx_hdr_type     => rx_hdr_type,

      s_axis_tdata    => rx_axis_tdata,
      s_axis_tkeep    => rx_axis_tkeep,
      s_axis_tvalid   => rx_axis_tvalid,
      s_axis_tlast    => rx_axis_tlast,
      s_axis_tready   => rx_axis_tready,

      m_axis_tdata_cp  => cp_rx_axis_tdata,
      m_axis_tkeep_cp  => cp_rx_axis_tkeep,
      m_axis_tvalid_cp => cp_rx_axis_tvalid,
      m_axis_tlast_cp  => cp_rx_axis_tlast,
      m_axis_tready_cp => cp_rx_axis_tready,

      m_axis_tdata_sdp  => sdp_rx_axis_tdata,
      m_axis_tkeep_sdp  => sdp_rx_axis_tkeep,
      m_axis_tvalid_sdp => sdp_rx_axis_tvalid,
      m_axis_tlast_sdp  => sdp_rx_axis_tlast,
      m_axis_tready_sdp => sdp_rx_axis_tready
    );

  -- ---------------------------------------------------
  -- TRANSMIT PACKET ARBITER
  eth_frame_arbiter_inst : entity work.eth_frame_arbiter
    generic map (
      DATA_WIDTH => DATA_WIDTH,
      KEEP_WIDTH => KEEP_WIDTH
    )
    port map(
      clk   => clk,
      reset => reset,

      tx_hdr_type  => tx_hdr_type,

      s_axis_tdata_cp   => cp_tx_axis_tdata,
      s_axis_tkeep_cp   => cp_tx_axis_tkeep,
      s_axis_tvalid_cp  => cp_tx_axis_tvalid,
      s_axis_tlast_cp   => cp_tx_axis_tlast,
      s_axis_tready_cp  => cp_tx_axis_tready,

      s_axis_tdata_sdp  => sdp_tx_axis_tdata,
      s_axis_tkeep_sdp  => sdp_tx_axis_tkeep,
      s_axis_tvalid_sdp => sdp_tx_axis_tvalid,
      s_axis_tlast_sdp  => sdp_tx_axis_tlast,
      s_axis_tready_sdp => sdp_tx_axis_tready,

      m_axis_tdata      => tx_axis_tdata,
      m_axis_tkeep      => tx_axis_tkeep,
      m_axis_tvalid     => tx_axis_tvalid,
      m_axis_tlast      => tx_axis_tlast,
      m_axis_tready     => tx_axis_tready
    );

  -- CONTROL PLANE MASTER

  cp_master : entity work.axis_to_cp
    generic map(
      DATA_WIDTH => DATA_WIDTH,
      KEEP_WIDTH => KEEP_WIDTH
    )
    port map(
      clk => clk,
      reset => reset,

      eth0_mac_addr => local_mac_addr,

      -- Connections to MAC
      s_axis_tdata => rx_axis_tdata,
      s_axis_tkeep => rx_axis_tkeep,
      s_axis_tvalid => cp_rx_axis_tvalid,
      s_axis_tlast => rx_axis_tlast,
      s_axis_tready => cp_rx_axis_tready,

      m_axis_tdata => cp_tx_axis_tdata,
      m_axis_tkeep => cp_tx_axis_tkeep,
      m_axis_tvalid => cp_tx_axis_tvalid,
      m_axis_tlast => cp_tx_axis_tlast,
      m_axis_tready => cp_tx_axis_tready,

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

      -- Configuration (from platform worker properties)
      remote_mac_addr => remote_mac_addr,
      remote_dst_id => remote_dst_id,
      local_src_id => local_src_id,
      interface_mtu => interface_mtu,
      ack_wait => ack_wait,
      max_acks_outstanding => max_acks_outstanding,
      coalesce_wait => coalesce_wait,

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

      -- Connections to MAC
      s_axis_tdata => rx_axis_tdata,
      s_axis_tvalid => sdp_rx_axis_tvalid,
      s_axis_tlast => rx_axis_tlast,
      s_axis_tready => sdp_rx_axis_tready,
      s_axis_tkeep => rx_axis_tkeep,

      m_axis_tdata => sdp_tx_axis_tdata,
      m_axis_tvalid => sdp_tx_axis_tvalid,
      m_axis_tlast => sdp_tx_axis_tlast,
      m_axis_tready => sdp_tx_axis_tready,
      m_axis_tkeep => sdp_tx_axis_tkeep,

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
