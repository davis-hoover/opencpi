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

#include "ocpi-config.h"
#ifdef OCPI_OS_linux
#include <unistd.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <sys/time.h>
#include <net/if.h>
#include <net/ethernet.h>
#include <arpa/inet.h>
#include <linux/if_packet.h>

#include "OsMisc.hh"
#include "XferDataGramEtherDriver2.hh"

namespace OCPI {
namespace Xfer {
namespace Ether2 {

static const uint16_t DGRDMA_ETHERTYPE = 0xf042;
static const uint32_t RECV_TIMEOUT_MS = 500;
static const size_t RETRANSMIT_WARN_INTERVAL = 10;

// Useful (internal) functions
static std::string hexdump(uint8_t *data, size_t length, size_t max = 16);
static uint32_t get_env_uint32(const char* name, uint32_t def);

////////////////////////////////////////////////////////////////////////////////
// DGXferFactory. These classes must be declared here (not in the header file)
// for reasons to do with the const char* template parameter
class DGDevice;

#define DRIVERNAME "datagram2-ether: "  // Name for debug messages
const char* protoname = "ether";

class DGXferFactory : public DriverBase<DGXferFactory, DGDevice, DGXferServices, protoname, XferFactory> {
  public:
    XferServices &createXferServices(EndPoint &source, EndPoint &target);
    EndPoint &createEndPoint(const char *protoInfo, const char *eps, const char *other,
                   bool local, size_t size, const OCPI::Base::PValue *params);
    const char* getProtocol();
};

class DGDevice : public DeviceBase<DGXferFactory,DGDevice> {
};

XferServices& DGXferFactory::createXferServices(EndPoint &source, EndPoint &target) {
    return *new DGXferServices(source, target);
}

EndPoint& DGXferFactory::createEndPoint(const char *protoInfo, const char *eps, const char *other,
                bool local, size_t size, const OCPI::Base::PValue *params) {
    ocpiLog(3, DRIVERNAME "createEndPoint %s %s %s %d %zu", protoInfo, eps, other, local, size);
    return *new DGEndPoint(*this, protoInfo, eps, other, local, size, params);
}

const char* DGXferFactory::getProtocol() {
    return "ocpi-ether-rdma";
}

// Register with the data transfer system
RegisterTransferDriver<DGXferFactory> ether2DatagramDriver;

////////////////////////////////////////////////////////////////////////////////
// DGXferServices methods
DGXferServices::DGXferServices(EndPoint &source, EndPoint &target) :
  ConnectionBase(*this, source, target),
  m_lep(*static_cast<DGEndPoint *>(source.local() ? &source : &target)),
  m_rep(*static_cast<DGEndPoint *>(source.local() ? &target : &source)),
  m_frames_received(256)
{
    m_sender = nullptr;

    uint32_t coalesce_wait = get_env_uint32("OCPI_COALESCE_WAIT_US", 0);
    uint32_t ack_timeout = get_env_uint32("OCPI_ACK_TIMEOUT_MS", 500);
    bool retransmit_enable = (get_env_uint32("OCPI_RETRANSMIT", 0) != 0);

    assert((source.local() && !target.local()) || (!source.local() && target.local()));
    m_lep.addXfer(*this, m_rep.mailBox());

    assert(m_lep.socket());
    m_sender = new TxThread(
        *m_lep.socket(),
        m_lep,
        m_rep,
        std::chrono::microseconds(coalesce_wait),
        std::chrono::milliseconds(ack_timeout),
        retransmit_enable);
    m_sender->start();
}

DGXferServices::~DGXferServices() {
    if (m_sender) {
        m_sender->stop();
        delete m_sender;
    }
}

XferRequest* DGXferServices::createXferRequest() {
    return new DGXferRequest(*this);
}

// Send a transaction to the remote endpoint. This just adds the transaction to
// the sender's transmit queue
void DGXferServices::send(OutboundTransaction txn) {
    m_sender->send_transaction(txn);
}

// Handle transaction received from remote endpoint. Called from receive thread
void DGXferServices::processFrame(FrameHeader frame_hdr, uint8_t* payload, size_t payload_size) {
    // Check for duplicate frame
    if (!m_frames_received.check(frame_hdr.frame_seq)) {
        return;
    }

    // Sender takes care of received ACKs and sending an ACK for this frame
    bool ack_only = (frame_hdr.flags == 0);
    m_sender->handle_received_frame(frame_hdr.frame_seq, ack_only, frame_hdr.ack_start, frame_hdr.ack_count);

    // If this is an ACK-only frame, we are done
    if (ack_only) {
        return;
    }

    // Process messages in this frame
    size_t cursor = 0;
    while (true) {
        // Adjust cursor to next 8-byte boundary
        if (cursor % 8 != 0) {
            cursor += 8 - (cursor % 8);
        }

        // Parse message header and check message length
        if (cursor + MsgHeader::LENGTH > payload_size) {
            ocpiBad(DRIVERNAME "Truncated message header (length=%zu, cursor=%zu)", payload_size, cursor);
            break;
        }

        MsgHeader hdr = MsgHeader::from_bytes(payload + cursor);

        if (cursor + MsgHeader::LENGTH + hdr.data_len > payload_size) {
            ocpiBad(DRIVERNAME "Truncated message (length=%zu, cursor=%zu, data_length=%" PRIu16 ")", payload_size, cursor, hdr.data_len);
            break;
        }

        // If there is data, write it into receive buffer
        if (hdr.data_len != 0) {
            uint8_t *dst_addr = (uint8_t*) from().sMemServices().map(hdr.data_addr, hdr.data_len);
            // ocpiInfo(DRIVERNAME "writing %u bytes to offset %u (%p)", hdr.data_len, hdr.data_addr, dst_addr);
            memcpy(dst_addr, payload + cursor + MsgHeader::LENGTH, hdr.data_len);
        }

        // Determine whether this is the last message in a transaction and update
        // transaction record
        bool end_of_transaction = false;
        if (hdr.num_msgs_in_txn < 2) {
            // ocpiInfo(DRIVERNAME "New transaction #%u (%u messages)", hdr.txn_id, hdr.num_msgs_in_txn);
            end_of_transaction = true;
        }
        else {
            // Find or create txn record
            if (m_txn_record.count(hdr.txn_id) != 0) {
                ReceivedTransaction& txn = m_txn_record[hdr.txn_id];
                // ocpiInfo(DRIVERNAME "Message for transaction #%u (%u messages left)", hdr.txn_id, txn.msgs_remaining);

                if (hdr.num_msgs_in_txn != txn.total_msgs || hdr.flag_addr != txn.flag_addr || hdr.flag_value != txn.flag_value) {
                    ocpiBad(DRIVERNAME "Message received for txn %u with different transaction metadata: total msgs %u (exp: %u), flag address %x (exp: %x), flag value %x (exp: %x)",
                        hdr.txn_id, hdr.num_msgs_in_txn, txn.total_msgs, hdr.flag_addr, txn.flag_addr, hdr.flag_value, txn.flag_value);
                }

                txn.msgs_remaining -= 1;
                if (txn.msgs_remaining == 0) {
                    end_of_transaction = true;
                    m_txn_record.erase(hdr.txn_id);
                }
            }
            else {
                // Create a new record
                // ocpiInfo("New transaction #%u (%u messages)", hdr.txn_id, hdr.num_msgs_in_txn);
                ReceivedTransaction txn;
                txn.total_msgs = hdr.num_msgs_in_txn;
                txn.msgs_remaining = hdr.num_msgs_in_txn - 1u;
                txn.flag_addr = hdr.flag_addr;
                txn.flag_value = hdr.flag_value;
                m_txn_record[hdr.txn_id] = txn;
            }
        }

        // Perform flag write if needed
        // TODO: strict transaction ordering
        if (end_of_transaction) {
            // ocpiInfo(DRIVERNAME "End of transaction %u (flag addr: 0x%x, value=0x%x)", hdr.txn_id, hdr.flag_addr, hdr.flag_value);

            if (hdr.flag_addr != 0xffffffff && hdr.flag_value != 0xffffffff) {
                uint32_t *flag = (uint32_t*) from().sMemServices().map(hdr.flag_addr, sizeof(uint32_t));

                // Store with release barrier to ensure that data write is not
                // moved after flag write - requires matching load-acquire when
                // flag is read (OcpiInputBuffer.cxx?)
                __atomic_store_n(flag, hdr.flag_value, __ATOMIC_RELEASE);
            }
        }

        if (hdr.has_nextmsg == 0) {
            break;
        }
        else {
            cursor += MsgHeader::LENGTH + hdr.data_len;
        }
    }
}

////////////////////////////////////////////////////////////////////////////////
// DGXferRequest methods
DGXferRequest::DGXferRequest(DGXferServices& parent) : TransferBase(parent, *this) {
    m_src_addr = nullptr;
    m_dst_addr = 0;
    m_src_flag_addr = nullptr;
    m_dst_flag_addr = 0;
    m_max_length = 0;
    m_pending_messages = 0;
}

DGXferRequest::~DGXferRequest() {
}

XferRequest* DGXferRequest::copy(Offset srcoff, Offset dstoff, size_t nbytes, XferRequest::Flags flags) {
    // TODO: error handling (should only call this once/twice)
    if (flags & XferRequest::FlagTransfer) {
        m_src_flag_addr = (uint32_t*) parent().from().sMemServices().map(srcoff, 4);
        m_dst_flag_addr = OCPI_UTRUNCATE(uint32_t, dstoff);
    }
    else {
        m_src_addr = (uint32_t*) parent().from().sMemServices().map(srcoff, nbytes);
        m_dst_addr = OCPI_UTRUNCATE(uint32_t, dstoff);
        m_max_length = nbytes;
    }

    return this;
}

void DGXferRequest::post() {
    OutboundTransaction txn(&m_pending_messages);
    txn.buffer = (uint8_t*) m_src_addr;
    txn.dst_addr = m_dst_addr;
    txn.flagaddr = m_dst_flag_addr;
    txn.flagvalue = *m_src_flag_addr;

    // Decode flag to determine transfer length, which could be less than buffer length
    // Length is flag[21:1]
    size_t length = (size_t) ((txn.flagvalue >> 1) & ((1u << 21) - 1));
    txn.size = std::min(length, m_max_length);

    // if (txn.size != 0) {
    //     ocpiInfo(DRIVERNAME "Post message from %p to 0x%x of length %lu [%s]",
    //         txn.buffer, txn.dst_addr, txn.size,
    //         hexdump(txn.buffer, txn.size, 8).c_str());
    // }
    // else {
    //     ocpiInfo(DRIVERNAME "Post flag-only message (addr 0x%x, value 0x%x)",
    //         txn.flagaddr, txn.flagvalue);
    // }

    // Store a non-zero value here as a placeholder so that we correctly report
    // the transfer is Pending. TxThread will fill this in with the actual number
    // of messages depending on how the transfer gets fragmented
    m_pending_messages = 1;
    parent().send(txn);
}

XferRequest::CompletionStatus DGXferRequest::getStatus() {
    return (m_pending_messages == 0) ? CompleteSuccess : Pending;
}

////////////////////////////////////////////////////////////////////////////////
// DGSmemServices methods
DGSmemServices::DGSmemServices(DGEndPoint& ep) : SmemServices(ep) {
    m_size = ep.size();
    if (ep.local()) {
        m_mem = new uint8_t[m_size];
        memset(m_mem, 0, m_size);
    }
    else {
        m_mem = nullptr;
    }
}

DGSmemServices::~DGSmemServices() {
    delete[] m_mem;
}

void* DGSmemServices::map (Offset offset, size_t size) {
    if (offset > m_size || (offset + size) > m_size) {
        throw OCPI::Util::Error(DRIVERNAME "DGSmemServices: invalid mapping at offset 0x%" DTOSDATATYPES_OFFSET_PRIx " of size 0x%zx (available size: 0x%zx)",
            offset, size, m_size);
    }

    return &m_mem[offset];
}

////////////////////////////////////////////////////////////////////////////////
// DGEndpoint methods
static std::string get_env_ifname() {
    // Get interface name from environment variable - FIXME would be good to do this another way
    const char* ifname_c = getenv("OCPI_ETHER_INTERFACE");
    if (!ifname_c) {
        throw OCPI::Util::Error(DRIVERNAME "OCPI_ETHER_INTERFACE must be specified to use datagram transport");
    }

    return std::string(ifname_c);
}

static uint32_t get_env_uint32(const char* name, uint32_t def) {
    const char* val = getenv(name);
    if (val) {
        char* endptr;
        unsigned long result = strtoul(val, &endptr, 10);
        if (endptr == val || *endptr != 0) {
            ocpiBad(DRIVERNAME "Invalid %s setting \"%s\"; using default %" PRIu32, name, val, def);
        }
        else {
            return (uint32_t) result;
        }
    }

    return def;
}

DGEndPoint::DGEndPoint(DGXferFactory &a_factory, const char* protoInfo, const char *eps,
    const char *other, bool a_local, size_t a_size, const OCPI::Base::PValue *params)
    : EndPoint(a_factory, eps, other, a_local, a_size, params)
{
    m_ifname = get_env_ifname();

    if (local()) {
        m_socket = new RawSocket(m_ifname, DGRDMA_ETHERTYPE);
        m_socket->set_receive_timeout(RECV_TIMEOUT_MS);
        m_receiver = new RxThread(*this);
        m_receiver->start();
    }
    else {
        // A remote endpoint. Parse the connection string to get MAC address and
        // check that the interface name is the same as what we were configured with
        std::string remote_ifname, remote_addr;

        if (parseRemoteEndpointInfo(protoInfo, remote_ifname, remote_addr)) {
            if (remote_ifname != m_ifname) {
                throw OCPI::Util::Error(DRIVERNAME "Tried to connect to device name \"%s\" (ifname=%s, addr=%s) but local endpoint is using interface \"%s\"", protoInfo, remote_ifname.c_str(), remote_addr.c_str(), m_ifname.c_str());
            }

            m_addr.setString(remote_addr.c_str());
        }
        else {
            throw OCPI::Util::Error(DRIVERNAME "Invalid remote device name \"%s\"", protoInfo);
        }

        m_socket = nullptr;
        m_receiver = nullptr;
    }
}

DGEndPoint::~DGEndPoint() {
    if (m_receiver) {
        m_receiver->stop();
        delete m_receiver;
    }

    delete m_socket;
}

// Extract local interface name and remote MAC address from a protoInfo string
// in the format:
//
//     Ether:<ifname>/<mac_addr>
//
// The obvious way to do this would be to use a regex, but std::regex is not
// properly supported by GCC 4.8.x (the stock compiler with CentOS 7) - sadly,
// it compiles just fine but fails with a runtime error - so just do it by hand
// (see e.g. https://gcc.gnu.org/bugzilla/show_bug.cgi?id=58576).
bool DGEndPoint::parseRemoteEndpointInfo(const std::string& protoInfo, std::string& ifname, std::string& address) {
    size_t protoSepPos = protoInfo.find(':');
    size_t addrSepPos = protoInfo.find('/', protoSepPos);
    if (protoSepPos == std::string::npos || addrSepPos == std::string::npos) {
        return false;
    }
    if (protoInfo.substr(0, protoSepPos) != "Ether") {
        return false;
    }

    ifname = protoInfo.substr(protoSepPos + 1, addrSepPos - protoSepPos - 1);
    address = protoInfo.substr(addrSepPos + 1);
    return true;
}

bool DGEndPoint::isCompatibleLocal(const char* protoInfo) {
    std::string remote_ifname, remote_addr;
    if (parseRemoteEndpointInfo(protoInfo, remote_ifname, remote_addr)) {
        if (remote_ifname == m_ifname) {
            return true;
        }
    }

    return false;
}

Xfer::SmemServices& DGEndPoint::createSmemServices() {
    return *new DGSmemServices(*this);
}

const uint8_t* DGEndPoint::addr() const {
    return m_addr.addr();
}

void DGEndPoint::addXfer(DGXferServices &s, Xfer::MailBox remote) {
    std::lock_guard<std::mutex> lock(m_lock);
    m_xferServices[remote] = &s;
    ocpiDebug(DRIVERNAME "xfer service %p added with mbox %d", &s, remote);
}

void DGEndPoint::delXfer(Xfer::MailBox remote) {
    std::lock_guard<std::mutex> lock(m_lock);
    XferServices* s = m_xferServices[remote];
    m_xferServices[remote] = nullptr;
    ocpiDebug(DRIVERNAME "xfer service %p removed with mbox %d", s, remote);
}

DGXferServices* DGEndPoint::getXfer(Xfer::MailBox remote) {
    std::lock_guard<std::mutex> lock(m_lock);
    if (m_xferServices.count(remote) != 0) {
        return m_xferServices[remote];
    }
    else {
        return nullptr;
    }
}

Socket *DGEndPoint::socket() const {
    return m_socket;
}

////////////////////////////////////////////////////////////////////////////////
// Internals

////////////////////////////////////////////////////////////////////////////////
// Interface
Interface::Interface(std::string ifname) : name(ifname) {
    int fd;
    std::string error;

    // Create request structure
    if (ifname.length() + 1 > IFNAMSIZ) {
        throw OCPI::Util::Error(DRIVERNAME "Interface name %s too long", ifname.c_str());
    }

    struct ifreq req;
    memset(&req, 0, sizeof(struct ifreq));
    strcpy(req.ifr_name, ifname.c_str());

    // Create query socket
    if ((fd = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
        OCPI::OS::setError(error, "opening socket to query interface");
        throw OCPI::Util::Error(DRIVERNAME "%s: %s", ifname.c_str(), error.c_str());
    }

    // Get index
    if (ioctl(fd, SIOCGIFINDEX, &req) < 0) {
        OCPI::OS::setError(error, "querying interface ID");
        close(fd);
        throw OCPI::Util::Error(DRIVERNAME "%s: %s", ifname.c_str(), error.c_str());
    }
    index = req.ifr_ifindex;

    // Get MTU
    if (ioctl(fd, SIOCGIFMTU, &req) < 0) {
        OCPI::OS::setError(error, "querying MTU");
        close(fd);
        throw OCPI::Util::Error(DRIVERNAME "%s: %s", ifname.c_str(), error.c_str());
    }
    mtu = req.ifr_mtu;

    // Get flags
    if (ioctl(fd, SIOCGIFFLAGS, &req) < 0) {
        OCPI::OS::setError(error, "querying flags");
        close(fd);
        throw OCPI::Util::Error(DRIVERNAME "%s: %s", ifname.c_str(), error.c_str());
    }
    flags = req.ifr_flags;

    close(fd);
}

bool Interface::up() {
    return (flags & IFF_UP) != 0;
}

bool Interface::connected() {
    return (flags & IFF_RUNNING) != 0;
}

////////////////////////////////////////////////////////////////////////////////
// RawSocket
RawSocket::RawSocket(std::string& ifname, uint16_t ethertype) : m_if(ifname), m_ethertype(ethertype) {
    ocpiInfo(DRIVERNAME "Creating raw socket on interface \"%s\"", ifname.c_str());

    // Find interface
    if (!m_if.up() || !m_if.connected()) {
        throw OCPI::Util::Error(DRIVERNAME "interface %s not ready", ifname.c_str());
    }

    // Create socket
    if ((m_fd = socket(AF_PACKET, SOCK_DGRAM, 0)) < 0) {
        std::string error;
        OCPI::OS::setError(error, "opening raw socket");
        throw OCPI::Util::Error(DRIVERNAME "%s", error.c_str());
    }

    // Bind to interface
    struct sockaddr_ll sa;
    memset(&sa, 0, sizeof(struct sockaddr_ll));
    sa.sll_family = AF_PACKET;
    sa.sll_protocol = htons(m_ethertype);
    sa.sll_ifindex = m_if.index;
    if (bind(m_fd, reinterpret_cast<sockaddr*>(&sa), sizeof(struct sockaddr_ll)) == -1) {
        ::close(m_fd);
        std::string error;
        OCPI::OS::setError(error, "binding socket to interface");
        throw OCPI::Util::Error(DRIVERNAME "%s", error.c_str());
    }

    ocpiInfo(DRIVERNAME "Opened raw socket on interface \"%s\" (%d) with MTU %d", ifname.c_str(), m_if.index, m_if.mtu);
}

void RawSocket::set_send_timeout(uint32_t timeout_ms) {
    ocpiInfo(DRIVERNAME "Set send timeout for \"%s\" to %ums", m_if.name.c_str(), timeout_ms);
    struct timeval tv;
    tv.tv_sec = timeout_ms / 1000;
    tv.tv_usec = (timeout_ms % 1000) * 1000;

    if (setsockopt(m_fd, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(struct timeval)) != 0) {
        std::string error;
        OCPI::OS::setError(error, "set send timeout to %u", timeout_ms);
    }
}

void RawSocket::set_receive_timeout(uint32_t timeout_ms) {
    ocpiInfo(DRIVERNAME "Set receive timeout for \"%s\" to %ums", m_if.name.c_str(), timeout_ms);

    struct timeval tv;
    tv.tv_sec = timeout_ms / 1000;
    tv.tv_usec = (timeout_ms % 1000) * 1000;

    if (setsockopt(m_fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(struct timeval)) != 0) {
        std::string error;
        OCPI::OS::setError(error, "set receive timeout to %u", timeout_ms);
    }
}

RawSocket::~RawSocket() {
    close();
}

void RawSocket::close() {
    ocpiInfo(DRIVERNAME "Close socket on interface \"%s\"", m_if.name.c_str());
    if (m_fd != -1) {
        ::close(m_fd);
        m_fd = -1;
    }
}

void Socket::send(uint8_t *buffer, size_t buflen, DGEndPoint& dest_ep) {
    struct iovec iov;
    iov.iov_base = buffer;
    iov.iov_len = buflen;
    send(&iov, 1, dest_ep);
}

void RawSocket::send(struct iovec *iov, size_t iovlen, DGEndPoint& dest_ep) {
    // Prepare address
    struct sockaddr_ll sa;
    memset(&sa, 0, sizeof(struct sockaddr_ll));
    sa.sll_family = AF_PACKET;
    sa.sll_protocol = htons(m_ethertype);
    sa.sll_ifindex = m_if.index;
    memcpy(sa.sll_addr, dest_ep.addr(), ETHER_ADDR_LEN);
    sa.sll_halen = ETHER_ADDR_LEN;

    // Prepare message header structure
    struct msghdr hdr;
    memset(&hdr, 0, sizeof(struct msghdr));
    hdr.msg_name = &sa;
    hdr.msg_namelen = sizeof(struct sockaddr_ll);
    hdr.msg_iov = iov;
    hdr.msg_iovlen = iovlen;

    // Send frame
    ssize_t result = sendmsg(m_fd, &hdr, 0);
    if (result < 0) {
        std::string error;
        OCPI::OS::setError(error, "sendmsg()");
        ocpiBad(DRIVERNAME "Error sending packet: %s", error.c_str());
        throw OCPI::Util::Error(DRIVERNAME "Error sending packet: %s", error.c_str());
    }
}

size_t RawSocket::receive(uint8_t *buffer, size_t buflen) {
    // Prepare structure for remote address
    struct sockaddr_ll sa;
    memset(&sa, 0, sizeof(struct sockaddr_ll));

    // Receive message
    socklen_t sa_len = sizeof(struct sockaddr_ll);
    ssize_t result = recvfrom(m_fd, buffer, buflen, 0, reinterpret_cast<sockaddr*>(&sa), &sa_len);

    if (result < 0) {
        if (errno == EAGAIN || errno == EWOULDBLOCK || errno == EINTR) { // timeout
            return 0;
        }
        else {
            std::string error;
            OCPI::OS::setError(error, "recvfrom()");
            ocpiBad(DRIVERNAME "Error receiving packet: %s", error.c_str());
            throw OCPI::Util::Error(DRIVERNAME "Error receiving packet: %s", error.c_str());
        }
    }

    // skip packets that are not addressed to us (including outbound packets which
    // are looped back)
    // TODO: supposedly we can do setsockopt(SOL_PACKET, PACKET_IGNORE_OUTGOING)
    // on more recent kernels to filter these out in the kernel
    if (sa.sll_pkttype != PACKET_HOST) {
        return 0;
    }

    if (ntohs(sa.sll_protocol) != m_ethertype) {
        ocpiWeird(DRIVERNAME "Ignoring packet with unknown Ethertype %x", ntohs(sa.sll_protocol));
        return 0;
    }

    return (size_t) result;
}

size_t RawSocket::mtu() const {
    return (size_t) m_if.mtu;
}

////////////////////////////////////////////////////////////////////////////////
// RxThread
RxThread::RxThread(DGEndPoint &ep) : m_ep(ep), m_running(true) {}

void RxThread::run() {
    uint8_t* rx_buf = new uint8_t[m_ep.socket()->mtu()];

    while(m_running) {
        size_t length = m_ep.socket()->receive(rx_buf, m_ep.socket()->mtu());

        if (length == 0) {  // timeout
            continue;
        }

        FrameHeader hdr = FrameHeader::from_bytes(rx_buf);
        DGXferServices *xs = m_ep.getXfer(hdr.dst_id);
        if (xs) {
            xs->processFrame(hdr, rx_buf + FrameHeader::LENGTH, length - FrameHeader::LENGTH);
        }
        else {
            ocpiBad(DRIVERNAME "Ignoring DG-RDMA frame with unknown destination id %u", hdr.dst_id);
        }
    }
    delete[] rx_buf;
}

void RxThread::stop() {
    m_running = false;
    join();
}

////////////////////////////////////////////////////////////////////////////////
// TxThread
TxThread::TxThread(Socket& socket, DGEndPoint& local_ep, DGEndPoint& remote_ep, std::chrono::microseconds coalesce_wait, std::chrono::milliseconds ack_timeout, bool retransmit_enable)
: m_local_ep(local_ep), m_remote_ep(remote_ep), m_socket(socket), m_coalesce_wait(coalesce_wait), m_ack_timeout(ack_timeout) {
    m_running = true;
    m_socket = socket;
    m_retransmit_enable = retransmit_enable;
    m_acks_received_updated = false;
}

// Helper function to fragment a transaction into messages
// mtu is the maximum frame size (including frame and message headers and data
// but not including the Ethernet header)
// If current_frame_space is non-zero, it is the number of bytes left in the first
// frame for a message header + data. If non-zero it must be at least
// MsgHeader::LENGTH + 4
void TxThread::fragment_transfer(std::vector<OutboundMessagePtr>& fragments, uint32_t txn_id, OutboundTransaction& txn, size_t mtu, size_t current_frame_space) {
    fragments.clear();

    size_t txn_bytes_left = txn.size;

    // Create a message object which we will copy into the fragments vector for
    // each fragment.
    // Fill in header fields that are the same for all messages in the
    // transaction
    MsgHeader hdr;
    hdr.txn_id = txn_id;
    hdr.num_msgs_in_txn = 0; // fill this in at the end, when we know it
    hdr.flag_addr = txn.flagaddr;
    hdr.flag_value = txn.flagvalue;
    hdr.msg_type = 0;
    hdr.msg_seq = 0;
    hdr.has_nextmsg = 0x1;  // cleared for last message in frame on transmit

    // These fields will be updated for each message. Set them for the first
    // message in the transaction
    uint8_t* src_addr = txn.buffer;
    hdr.data_addr = txn.dst_addr;
    hdr.msg_seq = 1;  // Not used by protocol - but useful for debugging in Wireshark

    // Handle flag-only transaction
    if (txn_bytes_left == 0) {
        // One message to send to complete transfer, but number of messages in
        // DG-RDMA header must be zero for a flag-only transfer
        *txn.pending_messages = 1;
        hdr.num_msgs_in_txn = 0;
        hdr.data_len = 0;
        OutboundMessagePtr msg = alloc_message(txn.pending_messages);
        msg->hdr = hdr;
        fragments.push_back(std::move(msg));
        return;
    }

    // Add messages until all data is accounted for
    while (txn_bytes_left > 0) {
        uint16_t data_len;

        // To avoid underflow
        if (current_frame_space > MsgHeader::LENGTH) {
            current_frame_space -= MsgHeader::LENGTH;

            if (txn_bytes_left <= current_frame_space) {
                // Round final message up to a multiple of 4 as required by FPGA
                data_len = (uint16_t) ((txn_bytes_left + 3) & ~0x3u);
                txn_bytes_left = 0;
            }
            else {
                // Round non-final messages down to a multiple of 16 as required by FPGA
                data_len = (uint16_t) (current_frame_space & (~0xfu));
                txn_bytes_left -= data_len;
            }

            if (data_len != 0) {
                hdr.data_len = data_len;

                OutboundMessagePtr msg = alloc_message(txn.pending_messages);
                msg->hdr = hdr;
                msg->src_addr = src_addr;
                fragments.push_back(std::move(msg));

                // Update pointers for next message
                src_addr += data_len;
                hdr.data_addr += data_len;
                hdr.msg_seq += (uint16_t) 1u;
            }
        }

        // Make new frame
        current_frame_space = mtu - FrameHeader::LENGTH;
    }

    size_t num_messages = fragments.size();
    *txn.pending_messages = num_messages;  // used to determine when transfer has completed
    for (OutboundMessagePtr& frag : fragments) {
        frag->hdr.num_msgs_in_txn = (uint16_t) num_messages;
    }
}

void TxThread::run() {
    // Reusable vectors to keep track of sender state. Allocated once here so that
    // heap allocations are only done once
    std::vector<OutboundTransaction> txq;   // Copy of transactions to be sent
    std::vector<OutboundMessagePtr> fragments; // Messages in the current transaction
    std::vector<OutboundFramePtr> retransmit_frames; // Unacknowledged frame to be retransmitted
    std::vector<struct iovec> iovs;         // Buffers in the current message

    // Transaction and frame sequence numbers
    uint32_t txn_id = 1;
    uint16_t frame_seq = 1;

    size_t mtu = m_socket.mtu();
    size_t new_frame_size = mtu - FrameHeader::LENGTH;

    // Keep track of a partially-filled frame. current_frame->space_in_frame
    // contains the number of bytes left in the frame, adjusted for inter-message
    // padding. If current_frame is set, deadline is valid and represents is the
    // instant at which the coalesce timer expires and the frame should be sent
    // even if not filled.
    OutboundFramePtr current_frame = nullptr;
    deadline_t deadline;

    while (true) {
        // Wait until we have work to do
        if (!get_outbound_transactions(txq, deadline, (current_frame != nullptr))) {
            break;  // Thread shutdown
        }

        // Handle received ACKs and retransmit
        // m_retransmit_queue holds unacknowledged frames in the order in which
        // they were transmitted (and therefore the order in which their ACK
        // deadline expires).

        // We need to hold the lock while looking at m_acks_received, which
        // is written to by the receive thread. We will put any frames that
        // need retransmission into retransmit_frames; this means we can send
        // them after we drop the lock to avoid holding the lock across the
        // send() system call (which could block the application thread unnecessarily)
        retransmit_frames.clear();
        {
            std::lock_guard<std::mutex> lock(m_lock);
            while (!m_retransmit_queue.empty()) {
                uint16_t front_frame_seq = m_retransmit_queue.front()->frame_hdr.frame_seq;

                if (m_acks_received.count(front_frame_seq) != 0) {
                    // This frame has been acknowledged. Free it and forget the ACK
                    // (otherwise we will run into problems when the sequence number
                    // wraps)
                    free_frame(std::move(m_retransmit_queue.front()));
                    m_retransmit_queue.pop();
                    m_acks_received.erase(front_frame_seq);
                }
                else if (clock::now() > m_retransmit_queue.front()->ack_deadline) {
                    // This frame has not been acknowledged. Retransmit or discard it.
                    OutboundFramePtr front_frame = std::move(m_retransmit_queue.front());
                    m_retransmit_queue.pop();

                    if (m_retransmit_enable) {
                        if ((front_frame->transmit_count + 1) % RETRANSMIT_WARN_INTERVAL == 0) {
                            ocpiBad(DRIVERNAME "DG-RDMA frame %" PRIu16 " was not acknowledged (sent %zu times)",
                                front_frame_seq, (front_frame->transmit_count + 1));
                        }

                        // Queue this frame for retransmission
                        retransmit_frames.push_back(std::move(front_frame));
                    }
                    else {
                        ocpiBad(DRIVERNAME "DG-RDMA frame %" PRIu16 " was not acknowledged", front_frame_seq);
                        free_frame(std::move(front_frame));
                    }
                }
                else {
                    // We have processed everything we can for now
                    break;
                }
            }
        }

        // Retransmit frames
        for (OutboundFramePtr& frame : retransmit_frames) {
            send_frame(std::move(frame), iovs);
        }

        // Pack outbound transactions into frames, sending a frame whenever we
        // have a full one
        for (OutboundTransaction& txn : txq) {
            // Calculate fragment sizes and create message headers
            size_t space_remaining = new_frame_size;
            if (current_frame != nullptr) {
                space_remaining = current_frame->space_remaining;
            }
            fragment_transfer(fragments, txn_id++, txn, mtu, space_remaining);

            // Transmit fragments
            for (OutboundMessagePtr& msg : fragments) {
                // Update space left in frame, taking into account padding of
                // next message header to an 8-byte boundary
                size_t length_including_padding = (MsgHeader::LENGTH + msg->hdr.data_len + 7) & (~7u);

                // If there is not space in frame, send it
                if (current_frame != nullptr && current_frame->space_remaining < length_including_padding) {
                    send_frame(std::move(current_frame), iovs);  // move: sets current_frame to nullptr
                }

                // Allocate a frame if needed
                if (current_frame == nullptr) {
                    current_frame = alloc_frame(frame_seq++);
                    current_frame->space_remaining = new_frame_size;
                    current_frame->transmit_count = 0;

                    // Start coalesce timer from when the first message is added to a frame
                    deadline = clock::now() + m_coalesce_wait;
                }

                current_frame->space_remaining -= length_including_padding;
                current_frame->messages.push_back(std::move(msg));
            }
        }

        // If we have a partially filled frame and have reached the deadline,
        // send it now
        if (current_frame != nullptr && clock::now() >= deadline) {
            send_frame(std::move(current_frame), iovs);  // move: sets current_frame to nullptr
        }
    }
}

// Helper function to wait on the condition varaible until something interesting
// happens:
//  1) stop() is called
//  2) one or more transactions are queued for transmission
//  3) coalesce deadline has occurred
//  4) m_acks_received_updated is true (meaning one or more ACKs have been received)
//  5) the ACK deadline of the oldest packet in the retransmit queue is reached
//
// If there is no deadline, wait indefinitely. If there are transactions
// in the transmit queue, copy them to a local queue so we don't need to hold
// the lock while we are doing blocking socket operations, allowing the
// application thread to keep making progress.
//
// Returns true if there is work to do, or false if the thread should exit
bool TxThread::get_outbound_transactions(std::vector<OutboundTransaction>& txq, deadline_t& coalesce_deadline, bool coalesce_deadline_valid) {
    txq.clear();

    // If either coalesce deadline or retransmit deadline is valid, make sure
    // we don't wait beyond it
    // (Note: it is safe to access m_retransmit_queue here since is only accessed
    // from this thread)
    bool deadline_valid;
    deadline_t deadline;
    if (coalesce_deadline_valid || !m_retransmit_queue.empty()) {
        deadline_valid = true;
        if (coalesce_deadline_valid && !m_retransmit_queue.empty()) {
            deadline = std::min(coalesce_deadline, m_retransmit_queue.front()->ack_deadline);
        }
        else if (coalesce_deadline_valid) {
            deadline = coalesce_deadline;
        }
        else {
            deadline = m_retransmit_queue.front()->ack_deadline;
        }
    }

    // Must hold the lock while we are looking at / manipulating shared data
    std::unique_lock<std::mutex> lock(m_lock);
    while (true)
    {
        // Handle thread shutdown
        if (!m_running) {
            return false;
        }

        while (!m_txq.empty()) {
            txq.push_back(std::move(m_txq.front()));
            m_txq.pop();
        }

        // Do we have anything to do?
        if (!txq.empty() || (deadline_valid && clock::now() >= deadline) || m_acks_received_updated) {
            m_acks_received_updated = false;
            return true;
        }

        // No; drop lock and wait for condition variable to be signalled. Wait
        // until the deadline passes (if there is one), otherwise indefinitely
        if (deadline_valid) {
            m_txq_cv.wait_until(lock, deadline);
        }
        else {
            m_txq_cv.wait(lock);
        }
    }
}

// Helper function to send a frame and handle related bookkeeping
void TxThread::send_frame(OutboundFramePtr frame, std::vector<struct iovec>& iovs) {
    frame->messages.back()->hdr.has_nextmsg = 0x0;
    frame->to_iovs(iovs);
    m_socket.send(iovs.data(), iovs.size(), m_remote_ep);
    frame->transmit_count++;

    // If we are NOT retransmitting, decrease reference count on transfer object
    // for all messages in this frame, allowing the data buffers to be reused
    // Also clear the src_addr pointer to catch accidental reuse of a buffer
    // we have released back to the application
    //
    // If we ARE retransmitting, this will be done when the ACK is received
    if (!m_retransmit_enable) {
        for (OutboundMessagePtr& message : frame->messages) {
            (*message->txn_pending_messages)--;
            message->src_addr = nullptr;
            message->txn_pending_messages = nullptr;
        }
    }

    // Add this frame to retransmit queue to track when it is acknowledged
    // (so that we can output a warning even if we are not retransmitting)
    frame->ack_deadline = clock::now() + m_ack_timeout;
    m_retransmit_queue.push(std::move(frame));
}

void TxThread::stop() {
    m_running = false;
    m_txq_cv.notify_one();
    join();
}

void TxThread::send_transaction(OutboundTransaction txn) {
    std::lock_guard<std::mutex> lock(m_lock);
    m_txq.push(txn);
    m_txq_cv.notify_one();
}

void TxThread::handle_received_frame(uint16_t /*frame_seq*/, bool /*ack_only*/, uint16_t ack_start, uint8_t ack_count) {
    std::lock_guard<std::mutex> lock(m_lock);

    // Process ACKs received in this frame
    for (uint8_t i = 0; i < ack_count; i++) {
        m_acks_received.insert((uint16_t) (ack_start + i));
    }

    // TOOD: record that we need to ACK this frame

    // Wake up thread
    m_acks_received_updated = true;
    m_txq_cv.notify_one();
}

OutboundFramePtr TxThread::alloc_frame(uint16_t frame_seq, bool has_messages, uint16_t ack_start, uint8_t ack_count) {
    // Get a frame from the free list, or allocate a fresh one if necessary
    // Frames are returned to the free list once they have been used.
    // This avoids unnecessary heap allocations
    OutboundFramePtr frame;
    if (!m_free_frames.empty()) {
        frame = std::move(m_free_frames.back());
        m_free_frames.pop_back();
    }
    else {
        frame = OutboundFramePtr(new OutboundFrame);
    }

    frame->frame_hdr.dst_id = m_remote_ep.mailBox();
    frame->frame_hdr.src_id = m_local_ep.mailBox();
    frame->frame_hdr.frame_seq = frame_seq;
    frame->frame_hdr.ack_start = ack_start;
    frame->frame_hdr.ack_count = ack_count;
    frame->frame_hdr.flags = (has_messages) ? 0x1 : 0x0;

    return frame;
}

void TxThread::free_frame(OutboundFramePtr frame) {
    // Free all messages in this frame, and return it to the free list to be reused
    while (!frame->messages.empty()) {
        free_message(std::move(frame->messages.back()));
        frame->messages.pop_back();
    }

    m_free_frames.push_back(std::move(frame));
}

OutboundMessagePtr TxThread::alloc_message(std::atomic_size_t* txn_pending_messages) {
    OutboundMessagePtr message;

    if (!m_free_messages.empty()) {
        message = std::move(m_free_messages.back());
        m_free_messages.pop_back();
    }
    else {
        message = OutboundMessagePtr(new OutboundMessage);
    }

    message->txn_pending_messages = txn_pending_messages;

    return message;
}

void TxThread::free_message(OutboundMessagePtr msg) {
    // If retransmit is enabled, decrease reference count on the transaction this
    // message belongs to. If retransmit is disabled, this was already done when
    // the frame was sent.
    if (m_retransmit_enable) {
        (*msg->txn_pending_messages)--;
    }

    msg->txn_pending_messages = nullptr;
    msg->src_addr = nullptr;

    m_free_messages.push_back(std::move(msg));
}


////////////////////////////////////////////////////////////////////////////////
// FrameHeader
#define UNPACK_16LE(buf) (((uint16_t)(buf)[0]) | (((uint16_t)(buf)[1]) << 8));
#define UNPACK_32LE(buf) (((uint32_t)(buf)[0]) | (((uint32_t)(buf)[1]) << 8)  | (((uint32_t)(buf)[2]) << 16)  | (((uint32_t)(buf)[3]) << 24));

const size_t FrameHeader::LENGTH = 10;
FrameHeader FrameHeader::from_bytes(uint8_t *buf) {  // static function
    FrameHeader result;
    memcpy(&result, buf, FrameHeader::LENGTH);
    return result;
}

////////////////////////////////////////////////////////////////////////////////
// MsgHeader
const size_t MsgHeader::LENGTH = 24;
MsgHeader MsgHeader::from_bytes(uint8_t *buf) {  // static function
    MsgHeader result;
    memcpy(&result, buf, MsgHeader::LENGTH);
    return result;
}

////////////////////////////////////////////////////////////////////////////////
// OutboundFrame
void OutboundFrame::to_iovs(std::vector<struct iovec>& iovs) {
    iovs.clear();
    static uint8_t pad[8];  // inter-message padding, if required (initialized to 0)

    struct iovec iov;

    // Frame header
    iov.iov_base = reinterpret_cast<uint8_t *>(&frame_hdr);
    iov.iov_len = FrameHeader::LENGTH;
    iovs.push_back(iov);

    // Add messages
    size_t cursor = 0;  // for alignment
    for (OutboundMessagePtr& msg : messages) {
        // Align messages to an 8-byte boundary
        if ((cursor % 8) != 0) {
            iov.iov_base = &pad;
            iov.iov_len = 8 - (cursor % 8);
            cursor += iov.iov_len;
            iovs.push_back(iov);
        }

        iov.iov_base = reinterpret_cast<uint8_t *>(&msg->hdr);
        iov.iov_len = MsgHeader::LENGTH;
        cursor += iov.iov_len;
        iovs.push_back(iov);

        if (msg->src_addr) {
            iov.iov_base = msg->src_addr;
            iov.iov_len = msg->hdr.data_len;
            cursor += msg->hdr.data_len;
            iovs.push_back(iov);
        }
    }
}

static std::string hexdump(uint8_t *data, size_t length, size_t max) {
    size_t n = std::min(length, max);
    auto buf = new char[n*3+4];
    int cursor = 0;

    for (size_t i = 0; i < n; i++) {
        if (cursor == 0) {
            cursor += std::sprintf(buf, "%02x", data[i]);
        }
        else {
            cursor += std::sprintf(buf + cursor, " %02x", data[i]);
        }
    }

    if (length > max) {
        strcpy(buf + cursor, "...");
    }

    std::string result(buf);
    delete[] buf;
    return result;
}

} // namespace Ether2
} // namespace Xfer
} // namespace OCPI
#endif
