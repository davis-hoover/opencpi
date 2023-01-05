/*
 * This file is protected by Copyright. Please refer to the COPYRIGHT file
 * distributed with this source distribution.
 *
 * This file is part of OpenCPI <http://www.opencpi.org>
 *
 * OpenCPI is free software: you can redistribute it and/or modify it under the
 * terms of the GNU Lesser General Public License as published by the Free
 * Software Foundation, either version 3 of the License, or (at your option) any
 * later version.
 *
 * OpenCPI is distributed in the hope that it will be useful, but WITHOUT ANY
 * WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
 * A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
 * details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef Xfer_DATAGRAMEtherDriver2_H_
#define Xfer_DATAGRAMEtherDriver2_H_

#include <atomic>
#include <chrono>
#include <condition_variable>
#include <deque>
#include <mutex>
#include <queue>
#include <unordered_map>
#include <unordered_set>
#include <vector>

#include "OsEther.hh"
#include "OsIovec.hh"
#include "OsTimer.hh"
#include "UtilThread.hh"
#include "UtilSelfMutex.hh"
#include "XferDriver.hh"
#include "XferEndPoint.hh"
#include "XferFactory.hh"
#include "XferServices.hh"

#include "./utils.hh"

// These declaration are shared among various datagram drivers
namespace OCPI {
namespace Xfer {
namespace Ether2 {

using clock = std::chrono::steady_clock;
using deadline_t = std::chrono::time_point<clock>;

// Interface to rest of OpenCPI. DGXXX classes derived from Xfer::XXX,
// in some cases via a helper interface (TransferBase, DriverBase, DeviceBase)

class DGXferServices;
class DGXferRequest;
class DGSmemServices;
class DGXferFactory;
class DGEndPoint;

// Internal classes
struct Interface;
class Socket;
class RxThread;
class TxThread;
class FrameHeader;
class MsgHeader;
struct OutboundFrame;
struct OutboundMessage;
struct OutboundTransaction;

using OutboundFramePtr = std::unique_ptr<OutboundFrame>;
using OutboundMessagePtr = std::unique_ptr<OutboundMessage>;

// XferServices: owns a connection between our local endpoint and one remote endpoint
// Frame sequence and message transaction namespaces are scoped to this object
class DGXferServices : public ConnectionBase<DGXferFactory, DGXferServices, DGXferRequest, XferServices> {
    DGEndPoint &m_lep;
    DGEndPoint &m_rep;
    TxThread *m_sender;

    struct ReceivedTransaction {
        uint32_t total_msgs;
        uint32_t msgs_remaining;
        uint32_t flag_addr;
        uint32_t flag_value;
    };
    std::unordered_map<uint32_t, ReceivedTransaction> m_txn_record;
    duplicate_filter<uint16_t> m_frames_received;

  public:
    DGXferServices(EndPoint &source, EndPoint &target);
    ~DGXferServices();

    // Overriden virtual methods
    XferRequest* createXferRequest();

    // Internal methods

    // Send a single DG-RDMA transfer (transaction), which may be fragmented into
    // multiple frames (and/or coalesced with messages from other transactions)
    void send(OutboundTransaction txn);

    // Handle an inbound frame
    void processFrame(FrameHeader frame_hdr, uint8_t *payload, size_t payload_size);
};

// A single outbound transfer request
// For RCC->HDL transfers, this consists of data + flag
// For HDL->RCC transfers, it is flag only (to carry the buffer-release doorbell)
// This ONLY supports FlagIsMeta (i.e. transfer metadata is included in the flag,
// there is no separate metadata transfer)
class DGXferRequest : public TransferBase<DGXferServices, DGXferRequest, XferRequest> {
    void* m_src_addr;
    uint32_t m_dst_addr;
    uint32_t* m_src_flag_addr;
    uint32_t m_dst_flag_addr;
    size_t m_max_length;

    std::atomic_size_t m_pending_messages;

  public:
    DGXferRequest(DGXferServices& parent);
    virtual ~DGXferRequest();

    // overrides base-class method: add source/destination buffer
    XferRequest* copy(Offset srcoff,
                      Offset dstoff,
                      size_t nbytes,
                      XferRequest::Flags flags);

    // overrides base-class method: send transfer
    void post();

    // overrides base-class method: check transfer status
    CompletionStatus getStatus();
};

// Memory area for application buffers. All DG-RDMA addresses are offsets into
// this buffer
class DGSmemServices : public SmemServices {
    uint8_t* m_mem;
    size_t m_size;
  public:
    DGSmemServices(DGEndPoint& ep);
    ~DGSmemServices();
    void* map(Offset offset, size_t size);
};

// Endpoint. If this is the local endpoint, it owns the socket and transmit/receive threads
class DGEndPoint : public EndPoint {
    std::unordered_map<Xfer::MailBox, DGXferServices *> m_xferServices; // NB: Xfer::Mailbox == uint16_t
    std::mutex m_lock;
    Socket *m_socket;
    RxThread *m_receiver;
    SmemServices *m_smemServices;

    std::string m_ifname;
    OCPI::OS::Ether::Address m_addr;

    static bool parseRemoteEndpointInfo(const std::string& protoInfo, std::string& ifname, std::string& address);

  public:
    DGEndPoint(DGXferFactory &a_factory, const char *protoInfo, const char *eps, const char *other, bool a_local,
              size_t a_size, const OCPI::Base::PValue *params);
    ~DGEndPoint();

    Xfer::SmemServices &createSmemServices();
    virtual bool isCompatibleLocal(const char* protoInfo);

    // internals
    const uint8_t* addr() const;

    void addXfer(DGXferServices &s, Xfer::MailBox remote);
    void delXfer(MailBox remote);
    DGXferServices* getXfer(uint16_t remote);

    Socket *socket() const;
};

// Internals

// Helper class to get detail of an interface
struct Interface {
    std::string name;
    int index;
    int mtu;
    short flags;

    bool up();
    bool connected();

    Interface(std::string ifname);
};

// Socket abstraction
class Socket {
  public:
    virtual ~Socket() {}

    virtual void send(uint8_t *buffer, size_t buflen, DGEndPoint& dest_ep);
    virtual void send(struct iovec *iov, size_t iovlen, DGEndPoint& dest_ep) = 0;
    virtual size_t receive(uint8_t *buffer, size_t buflen) = 0;
    virtual void set_send_timeout(uint32_t /*timeout_ms*/) {}
    virtual void set_receive_timeout(uint32_t /*timeout_ms*/) {}
    virtual size_t mtu() const = 0;
    virtual void close() {}
};

class RawSocket : public Socket {
    int m_fd;
    Interface m_if;
    uint16_t m_ethertype;

  public:
    RawSocket(std::string& ifname, uint16_t ethertype);
    ~RawSocket();

    void send(struct iovec *iov, size_t iovlen, DGEndPoint& dest_ep);
    size_t receive(uint8_t *buffer, size_t buflen);

    void set_send_timeout(uint32_t timeout_ms);
    void set_receive_timeout(uint32_t timeout_ms);

    size_t mtu() const;
    void close();
};

// Receive thread (one per local endpoint)
class RxThread : public OCPI::Util::Thread {
    DGEndPoint &m_ep;
    std::atomic_bool m_running;

  public:
    RxThread(DGEndPoint &ep);
    void run();
    void stop();
};

// Send thread (one per remote endpoint)
class TxThread : public OCPI::Util::Thread {
    DGEndPoint& m_local_ep;
    DGEndPoint& m_remote_ep;
    std::mutex m_lock;
    std::atomic_bool m_running;

    Socket& m_socket;

    std::queue<OutboundTransaction> m_txq;
    std::condition_variable m_txq_cv;

    std::unordered_set<uint16_t> m_acks_received;
    bool m_acks_received_updated;

    std::queue<OutboundFramePtr> m_retransmit_queue;

    std::chrono::microseconds m_coalesce_wait;
    std::chrono::milliseconds m_ack_timeout;
    bool m_retransmit_enable;

    std::vector<OutboundFramePtr> m_free_frames;
    std::vector<OutboundMessagePtr> m_free_messages;

    bool get_outbound_transactions(std::vector<OutboundTransaction>& txq, deadline_t& coalesce_deadline, bool coalesce_deadline_valid);
    void send_frame(OutboundFramePtr frame, std::vector<struct iovec>& iovs);
    void fragment_transfer(std::vector<OutboundMessagePtr>& fragments, uint32_t txn_id, OutboundTransaction& txn, size_t mtu, size_t current_frame_space);

    OutboundFramePtr alloc_frame(uint16_t frame_seq, bool has_messages = true, uint16_t ack_start = 0, uint8_t ack_count = 0);
    void free_frame(OutboundFramePtr frame);
    OutboundMessagePtr alloc_message(std::atomic_size_t* txn_pending_messages);
    void free_message(OutboundMessagePtr msg);

  public:
    TxThread(Socket& socket, DGEndPoint& local_ep, DGEndPoint& remote_ep, std::chrono::microseconds coalesce_wait, std::chrono::milliseconds ack_timeout, bool retransmit_enable);
    void run();
    void stop();
    void send_transaction(OutboundTransaction txn);
    void handle_received_frame(uint16_t frame_seq, bool ack_only, uint16_t ack_start, uint8_t ack_count);
};

struct __attribute__((__packed__)) FrameHeader {
    uint16_t dst_id;
    uint16_t src_id;
    uint16_t frame_seq;
    uint16_t ack_start;
    uint8_t ack_count;
    uint8_t flags;

    static const size_t LENGTH;
    static FrameHeader from_bytes(uint8_t *buf);
};

struct __attribute__((__packed__)) MsgHeader {
    uint32_t txn_id;
    uint32_t flag_addr;
    uint32_t flag_value;
    uint16_t num_msgs_in_txn;
    uint16_t msg_seq;
    uint32_t data_addr;
    uint16_t data_len;
    uint8_t msg_type;
    uint8_t has_nextmsg;

    static const size_t LENGTH;
    static MsgHeader from_bytes(uint8_t *buf);
};

struct OutboundFrame {
    FrameHeader frame_hdr;
    std::vector<OutboundMessagePtr> messages;
    size_t space_remaining;
    deadline_t ack_deadline;
    size_t transmit_count;

    void to_iovs(std::vector<struct iovec>& iovs);
};

struct OutboundTransaction {
    uint8_t *buffer;
    uint32_t dst_addr;
    size_t size;
    uint32_t flagaddr;
    uint32_t flagvalue;

    std::atomic_size_t* pending_messages;
    OutboundTransaction(std::atomic_size_t* m) : pending_messages(m) {}
};

struct OutboundMessage {
    MsgHeader hdr;
    uint8_t* src_addr;
    std::atomic_size_t* txn_pending_messages;
};

} // namespace Ether2
} // namespace Xfer
} // namespace OCPI

#endif // !defined Xfer_DATAGRAMEtherDriver2_H_
