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

-- THIS FILE WAS ORIGINALLY GENERATED ON Tue Jun 23 17:57:52 2015 EDT
-- BASED ON THE FILE: time_server.xml
-- YOU *ARE* EXPECTED TO EDIT IT
-- This file initially contains the architecture skeleton for worker: time_server

--
-- This module is normalized the interface when the BSV was converted to VHDL
--
library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi, cdc, platform; use ocpi.types.all; -- remove this to avoid all ocpi name collisions

architecture rtl of dgrdma_config_dev_worker is
begin

  dev_out(0).RESET <= ctl_in.reset or not props_in.enable_d;

  dev_out(0).REMOTE_MAC_ADDR         <= from_ulonglong(props_in.remote_mac_addr_d);
  dev_out(0).REMOTE_DST_ID           <= from_ushort(props_in.remote_dst_id_d);
  dev_out(0).LOCAL_SRC_ID            <= from_ushort(props_in.local_src_id_d);
  dev_out(0).INTERFACE_MTU           <= from_ushort(props_in.interface_mtu_d);
  dev_out(0).ACK_WAIT                <= from_ulong(props_in.ack_wait_d);
  dev_out(0).MAX_ACKS_OUTSTANDING    <= from_uchar(props_in.max_acks_outstanding_d);
  dev_out(0).COALESCE_WAIT           <= from_ulong(props_in.coalesce_wait_d);
  dev_out(0).DUAL_ETHERNET           <= '0' when props_in.dual_ethernet_d = 0 else '1';

  props_out.ack_tracker_rej_ack_d    <= to_uchar(0) when dev_in(0).ACK_TRACKER_REJ_ACK = '0' else to_uchar(1);
  props_out.ack_tracker_bitfield_d   <= to_ulong(to_integer(unsigned(dev_in(0).ACK_TRACKER_BITFIELD)));
  props_out.ack_tracker_base_seqno_d <= to_ushort(to_integer(unsigned(dev_in(0).ACK_TRACKER_BASE_SEQNO)));
  props_out.ack_tracker_rej_seqno_d  <= to_ushort(to_integer(unsigned(dev_in(0).ACK_TRACKER_REJ_SEQNO)));

  props_out.ack_tracker_total_acks_sent_d     <= to_ulong(to_integer(unsigned(dev_in(0).ACK_TRACKER_TOTAL_ACKS_SENT)));
  props_out.ack_tracker_tx_acks_sent_d        <= to_ulong(to_integer(unsigned(dev_in(0).ACK_TRACKER_TX_ACKS_SENT)));
  props_out.ack_tracker_pkts_enqueued_d       <= to_ulong(to_integer(unsigned(dev_in(0).ACK_TRACKER_PKTS_ENQUEUED)));
  props_out.ack_tracker_reject_out_of_range_d <= to_ulong(to_integer(unsigned(dev_in(0).ACK_TRACKER_REJECT_OUT_OF_RANGE)));
  props_out.ack_tracker_reject_already_set_d  <= to_ulong(to_integer(unsigned(dev_in(0).ACK_TRACKER_REJECT_ALREADY_SET)));
  props_out.ack_tracker_accepted_by_peek_d    <= to_ulong(to_integer(unsigned(dev_in(0).ACK_TRACKER_ACCEPTED_BY_PEEK)));

  props_out.ack_tracker_high_watermark_d <= to_ushort(to_integer(unsigned(dev_in(0).ACK_TRACKER_HIGH_WATERMARK)));

  props_out.frame_parser_reject_d <= to_ulong(to_integer(unsigned(dev_in(0).FRAME_PARSER_REJECT)));

end rtl;
