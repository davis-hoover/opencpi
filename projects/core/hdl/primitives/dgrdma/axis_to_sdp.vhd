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
library sdp; use sdp.sdp.all;
library platform; use platform.all;
library dgrdma; use dgrdma.dgrdma_util.all;

entity axis_to_sdp is
generic(
  SDP_WIDTH : natural;
  ACK_TRACKER_BITFIELD_WIDTH : natural;
  ACK_TRACKER_MAX_ACK_COUNT  : natural range 1 to 255;
  TXN_RECORD_MAX_TXNS_IN_FLIGHT : natural := 64
  );
port( clk                :  in std_logic;
      reset              :  in std_logic;

      -- configuration (properties from platform worker)
      remote_mac_addr    :  in std_logic_vector(47 downto 0);
      remote_dst_id      :  in std_logic_vector(15 downto 0);
      local_src_id       :  in std_logic_vector(15 downto 0);
      interface_mtu      :  in unsigned(15 downto 0);
      ack_wait           :  in unsigned(31 downto 0);
      max_acks_outstanding : in unsigned(7 downto 0);
      coalesce_wait      :  in unsigned(31 downto 0);

      -- ack tracker debug
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

      s_axis_tdata       :  in std_logic_vector(data_width_for_sdp(SDP_WIDTH) - 1 downto 0);
      s_axis_tkeep       :  in std_logic_vector(keep_width_for_sdp(SDP_WIDTH) - 1 downto 0);
      s_axis_tvalid      :  in std_logic;
      s_axis_tlast       :  in std_logic;
      s_axis_tready      : out std_logic;

      m_axis_tdata       : out std_logic_vector(data_width_for_sdp(SDP_WIDTH) - 1 downto 0);
      m_axis_tkeep       : out std_logic_vector(keep_width_for_sdp(SDP_WIDTH) - 1 downto 0);
      m_axis_tvalid      : out std_logic;
      m_axis_tlast       : out std_logic;
      m_axis_tready      :  in std_logic;

      sdp_in             :  in s2m_t;
      sdp_out            : out m2s_t;
      sdp_in_data        :  in dword_array_t(0 to SDP_WIDTH-1);
      sdp_out_data       : out dword_array_t(0 to SDP_WIDTH-1);

      flag_addr          : out std_logic_vector(23 downto 0);
      flag_data          : out std_logic_vector(31 downto 0);
      flag_valid         : out std_logic;
      flag_take          :  in std_logic
    );
end axis_to_sdp;

architecture rtl of axis_to_sdp is
  signal tx_ackstart : unsigned(15 downto 0);
  signal tx_ackcount : integer range 0 to ACK_TRACKER_MAX_ACK_COUNT;
  signal tx_ack_req : std_logic;
  signal tx_ack_req_urg : std_logic;
  signal tx_ack_sent : std_logic;
  signal tx_ackcount_sent : integer range 0 to ACK_TRACKER_MAX_ACK_COUNT;

  signal rx_txn_valid : std_logic;
  signal rx_txn_ready : std_logic;
  signal rx_txn_id : std_logic_vector(31 downto 0);
  signal rx_msgs_in_txn : unsigned(15 downto 0);
  signal rx_flag_addr : std_logic_vector(23 downto 0);
  signal rx_flag_data : std_logic_vector(31 downto 0);
begin
  sdp_out.clk <= clk;
  sdp_out.reset <= reset;
  sdp_out.id <= (others => '0');

  frame_generator_inst : entity work.dgrdma_frame_generator
    generic map(
      SDP_WIDTH => SDP_WIDTH,
      ACK_TRACKER_MAX_ACK_COUNT => ACK_TRACKER_MAX_ACK_COUNT
    )
    port map(
      clk => clk,
      reset => reset,

      -- config
      remote_mac_addr => remote_mac_addr,
      remote_dst_id => remote_dst_id,
      local_src_id => local_src_id,
      interface_mtu => interface_mtu,
      coalesce_wait => coalesce_wait,

      -- ack
      tx_ackstart => tx_ackstart,
      tx_ackcount => tx_ackcount,
      tx_ack_req => tx_ack_req,
      tx_ack_req_urg => tx_ack_req_urg,
      tx_ack_sent => tx_ack_sent,
      tx_ackcount_sent => tx_ackcount_sent,

      -- sdp
      sdp_init_data => sdp_in_data,
      sdp_init_count => sdp_in.sdp.header.count,
      sdp_init_op => sdp_in.sdp.header.op,
      sdp_init_xid => sdp_in.sdp.header.xid,
      sdp_init_lead => sdp_in.sdp.header.lead,
      sdp_init_trail => sdp_in.sdp.header.trail,
      sdp_init_node => sdp_in.sdp.header.node,
      sdp_init_addr => sdp_in.sdp.header.addr,
      sdp_init_extaddr => sdp_in.sdp.header.extaddr,
      sdp_init_eop => sdp_in.sdp.eop,
      sdp_init_valid => sdp_in.sdp.valid,
      sdp_init_ready => sdp_out.sdp.ready,

      m_axis_tdata => m_axis_tdata,
      m_axis_tkeep => m_axis_tkeep,
      m_axis_tvalid => m_axis_tvalid,
      m_axis_tlast => m_axis_tlast,
      m_axis_tready => m_axis_tready
    );

  frame_parser_inst : entity work.dgrdma_frame_parser
    generic map(
      SDP_WIDTH                  => SDP_WIDTH,
      ACK_TRACKER_BITFIELD_WIDTH => ACK_TRACKER_BITFIELD_WIDTH,
      ACK_TRACKER_MAX_ACK_COUNT  => ACK_TRACKER_MAX_ACK_COUNT,
      MAX_TXNS_IN_FLIGHT         => TXN_RECORD_MAX_TXNS_IN_FLIGHT
    )
    port map(
      clk => clk,
      reset => reset,

      -- config
      ack_wait => ack_wait,
      max_acks_outstanding => max_acks_outstanding,

      -- ack tracker
      tx_ackstart => tx_ackstart,
      tx_ackcount => tx_ackcount,
      tx_ack_req => tx_ack_req,
      tx_ack_req_urg => tx_ack_req_urg,
      tx_ack_sent => tx_ack_sent,
      tx_ackcount_sent => tx_ackcount_sent,

      -- ack tracker debug
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

      -- sdp
      sdp_targ_data => sdp_out_data,
      sdp_targ_count => sdp_out.sdp.header.count,
      sdp_targ_op => sdp_out.sdp.header.op,
      sdp_targ_xid => sdp_out.sdp.header.xid,
      sdp_targ_lead => sdp_out.sdp.header.lead,
      sdp_targ_trail => sdp_out.sdp.header.trail,
      sdp_targ_node => sdp_out.sdp.header.node,
      sdp_targ_addr => sdp_out.sdp.header.addr,
      sdp_targ_extaddr => sdp_out.sdp.header.extaddr,
      sdp_targ_eop => sdp_out.sdp.eop,
      sdp_targ_valid => sdp_out.sdp.valid,
      sdp_targ_ready => sdp_in.sdp.ready,

      s_axis_tdata => s_axis_tdata,
      s_axis_tkeep => s_axis_tkeep,
      s_axis_tvalid => s_axis_tvalid,
      s_axis_tlast => s_axis_tlast,
      s_axis_tready => s_axis_tready,

      flag_addr => flag_addr,
      flag_data => flag_data,
      flag_valid => flag_valid,
      flag_take => flag_take
    );
end rtl;
