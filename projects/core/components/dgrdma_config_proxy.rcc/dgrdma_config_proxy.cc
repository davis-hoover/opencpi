/*
 * THIS FILE WAS ORIGINALLY GENERATED ON Mon Nov  8 13:27:14 2021 UTC
 * BASED ON THE FILE: platform-proxy.xml
 * YOU *ARE* EXPECTED TO EDIT IT
 *
 * This file contains the implementation skeleton for the simpleproxy worker in C++
 */

#include "dgrdma_config_proxy-worker.hh"

using namespace OCPI::RCC; // for easy access to RCC data types and constants
using namespace Dgrdma_config_proxyWorkerTypes;

class Dgrdma_config_proxyWorker : public Dgrdma_config_proxyWorkerBase {

  RCCResult start() {
    slave.set_enable_d(true);
    return RCC_OK;
  }

  RCCResult stop() {
    slave.set_enable_d(false);
    return RCC_OK;
  }

  RCCResult release() {
    return RCC_OK;
  }

  RCCResult remote_mac_addr_read() {
    properties().remote_mac_addr = slave.get_remote_mac_addr_d();
    return RCC_OK;
  }

  RCCResult remote_mac_addr_written() {
    slave.set_remote_mac_addr_d(properties().remote_mac_addr);
    return RCC_OK;
  }

  RCCResult remote_dst_id_read() {
    properties().remote_dst_id = slave.get_remote_dst_id_d();
    return RCC_OK;
  }

  RCCResult remote_dst_id_written() {
    slave.set_remote_dst_id_d(properties().remote_dst_id);
    return RCC_OK;
  }

  RCCResult local_src_id_read() {
    properties().local_src_id = slave.get_local_src_id_d();
    return RCC_OK;
  }

  RCCResult local_src_id_written() {
    slave.set_local_src_id_d(properties().local_src_id);
    return RCC_OK;
  }

  RCCResult interface_mtu_read() {
    properties().local_src_id = slave.get_local_src_id_d();
    return RCC_OK;
  }

  RCCResult interface_mtu_written() {
    slave.set_interface_mtu_d(properties().interface_mtu);
    return RCC_OK;
  }

  RCCResult ack_wait_read() {
    properties().ack_wait = slave.get_ack_wait_d();
    return RCC_OK;
  }

  RCCResult ack_wait_written() {
    slave.set_ack_wait_d(properties().ack_wait);
    return RCC_OK;
  }

  RCCResult max_acks_outstanding_read() {
    properties().max_acks_outstanding = slave.get_max_acks_outstanding_d();
    return RCC_OK;
  }
  RCCResult max_acks_outstanding_written() {
    slave.set_max_acks_outstanding_d(properties().max_acks_outstanding);
    return RCC_OK;
  }

  RCCResult coalesce_wait_read() {
    properties().coalesce_wait = slave.get_coalesce_wait_d();
    return RCC_OK;
  }
  RCCResult coalesce_wait_written() {
    slave.set_coalesce_wait_d(properties().coalesce_wait);
    return RCC_OK;
  }

  RCCResult dual_ethernet_read() {
    properties().dual_ethernet = slave.get_dual_ethernet_d();
    return RCC_OK;
  }

  RCCResult dual_ethernet_written() {
    slave.set_dual_ethernet_d(properties().dual_ethernet);
    return RCC_OK;
  }

  RCCResult ack_tracker_rej_ack_read() {
    properties().ack_tracker_rej_ack = slave.get_ack_tracker_rej_ack_d();
    return RCC_OK;
  }

  RCCResult ack_tracker_rej_ack_written() {
    //slave.set_ack_tracker_rej_ack_d(properties().ack_tracker_rej_ack);
    return RCC_OK;
  }

  RCCResult ack_tracker_bitfield_read() {
    properties().ack_tracker_bitfield = slave.get_ack_tracker_bitfield_d();
    return RCC_OK;
  }

  RCCResult ack_tracker_bitfield_written() {
    //slave.set_ack_tracker_bitfield_d(properties().ack_tracker_bitfield);
    return RCC_OK;
  }

  RCCResult ack_tracker_base_seqno_read() {
    properties().ack_tracker_base_seqno = slave.get_ack_tracker_base_seqno_d();
    return RCC_OK;
  }

  RCCResult ack_tracker_base_seqno_written() {
    //slave.set_ack_tracker_base_seqno_d(properties().ack_tracker_base_seqno);
    return RCC_OK;
  }

  RCCResult ack_tracker_rej_seqno_read() {
    properties().ack_tracker_rej_seqno = slave.get_ack_tracker_rej_seqno_d();
    return RCC_OK;
  }

  RCCResult ack_tracker_rej_seqno_written() {
    //slave.set_ack_tracker_rej_seqno_d(properties().ack_tracker_rej_seqno);
    return RCC_OK;
  }

  RCCResult ack_tracker_total_acks_sent_read() {
    properties().ack_tracker_total_acks_sent = slave.get_ack_tracker_total_acks_sent_d();
    return RCC_OK;
  }

  RCCResult ack_tracker_total_acks_sent_written() {
    //slave.set_ack_tracker_total_acks_sent_d(properties().ack_tracker_total_acks_sent);
    return RCC_OK;
  }

  RCCResult ack_tracker_tx_acks_sent_read() {
    properties().ack_tracker_tx_acks_sent = slave.get_ack_tracker_tx_acks_sent_d();
    return RCC_OK;
  }

  RCCResult ack_tracker_tx_acks_sent_written() {
    //slave.set_ack_tracker_tx_acks_sent_d(properties().ack_tracker_tx_acks_sent);
    return RCC_OK;
  }

  RCCResult ack_tracker_pkts_enqueued_read() {
    properties().ack_tracker_pkts_enqueued = slave.get_ack_tracker_pkts_enqueued_d();
    return RCC_OK;
  }

  RCCResult ack_tracker_pkts_enqueued_written() {
    //slave.set_ack_tracker_pkts_enqueued_d(properties().ack_tracker_pkts_enqueued);
    return RCC_OK;
  }

  RCCResult ack_tracker_reject_out_of_range_read() {
    properties().ack_tracker_reject_out_of_range = slave.get_ack_tracker_reject_out_of_range_d();
    return RCC_OK;
  }

  RCCResult ack_tracker_reject_out_of_range_written() {
    //slave.set_ack_tracker_reject_out_of_range_d(properties().ack_tracker_reject_out_of_range);
    return RCC_OK;
  }

  RCCResult ack_tracker_reject_already_set_read() {
    properties().ack_tracker_reject_already_set = slave.get_ack_tracker_reject_already_set_d();
    return RCC_OK;
  }

  RCCResult ack_tracker_reject_already_set_written() {
    //slave.set_ack_tracker_reject_already_set_d(properties().ack_tracker_reject_already_set);
    return RCC_OK;
  }

  RCCResult ack_tracker_accepted_by_peek_read() {
    properties().ack_tracker_accepted_by_peek = slave.get_ack_tracker_accepted_by_peek_d();
    return RCC_OK;
  }

  RCCResult ack_tracker_accepted_by_peek_written() {
    //slave.ack_tracker_accepted_by_peek_d(properties().ack_tracker_accepted_by_peek);
    return RCC_OK;
  }

  RCCResult ack_tracker_high_watermark_read() {
    properties().ack_tracker_high_watermark = slave.get_ack_tracker_high_watermark_d();
    return RCC_OK;
  }

  RCCResult ack_tracker_high_watermark_written() {
    //slave.set_ack_tracker_high_watermark_d(properties().ack_tracker_high_watermark);
    return RCC_OK;
  }

  RCCResult frame_parser_reject_read() {
    properties().frame_parser_reject = slave.get_frame_parser_reject_d();
    return RCC_OK;
  }

  RCCResult frame_parser_reject_written() {
    //slave.set_frame_parser_reject_d(properties().frame_parser_reject);
    return RCC_OK;
  }

  RCCResult run(bool /*timedout*/) {
    return RCC_DONE; // change this as needed for this worker to do something useful
    // return RCC_ADVANCE; when all inputs/outputs should be advanced each time "run" is called.
    // return RCC_ADVANCE_DONE; when all inputs/outputs should be advanced, and there is nothing more to do.
    // return RCC_DONE; when there is nothing more to do, and inputs/outputs do not need to be advanced.
  }
};

DGRDMA_CONFIG_PROXY_START_INFO
// Insert any static info assignments here (memSize, memSizes, portInfo)
// e.g.: info.memSize = sizeof(MyMemoryStruct);
// YOU MUST LEAVE THE *START_INFO and *END_INFO macros here and uncommented in any case
DGRDMA_CONFIG_PROXY_END_INFO
