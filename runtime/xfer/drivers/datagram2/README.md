# datagram2 transfer driver

This directory contains a clean re-implementation of the datagram transfer driver
which provides support for DG-RDMA platforms. It has been tested with the
`zed_ether` reference platform.

The driver can be enabled by including the following line in `system.xml` (under
the `<transfer>` tag):

```xml
    <datagram2-ether load='1'/>
```

It is configured using environment variables:

* `OCPI_ETHER_INTERFACE`: name of local interface to use for DG-RDMA
* `OCPI_COALESCE_WAIT_US`: how long to wait (in microseconds) for more data
    before sending a partially-filled frame [default: 0us]
* `OCPI_ACK_TIMEOUT_MS`: how long to wait (in milliseconds) before retransmitting
    a frame which has not been acknowledged by the remote. If retransmit is
    disabled, an error will be logged to console instead. [default: 500ms]
* `OCPI_RETRANSMIT`: enable retransmit of frames that are not acknowledged by the
    remote. This allows an application to tolerate some packet loss, but may make it
    more difficult to diagnose system problems (as dropped packets will result in
    silent degradation of performance rather than an error message followed by
    a hang).

    When retransmit is enabled, the driver retains ownership of worker output
    buffers until they have been ACKed by the remote; when retransmit is off,
    buffers are released as soon as they are sent. Therefore the application
    may need to be configured with more buffers to achieve the same level of
    performance if retransmit is enabled. [default: 0]

`OCPI_ETHER_INTERFACE` must be specified; the other environment variables have
defaults and are optional.

## Design notes

We start one thread per local endpoint for receive (`RxThread` instance) and one
thread per local-remote connection (`TxThread` instance). Each local-remote connection
is represented by a `DGXferServices` instance, which owns the `TxThread`; the
`RxThread` and the raw socket are owned by the local `DGEndpoint`.

### Receive thread to application communication

When a buffer is received from the remote, it is written into the application's
input buffer space. When a DG-RDMA transaction is complete, a completion doorbell
is written to the application's flag address. The application polls this flag
address to determine when a buffer is available to consume.

A store-release memory barrier is used for the doorbell write, which is paired
with a load-acquire in `TransportInputPort.cc`. This pair of barriers ensures that
_if_ the application reads a valid doorbell from the flag address, it can _then_
read data from the buffer area which will reflect all preceding writes from the
receive thread.

These barriers are no-ops on x86/x86_64 (which does not permit store-store or
load-load reordering), and in this case just serve to document the handoff
process. However, on architectures with weaker memory ordering guarantees (e.g.
ARM/ARM64), these barriers are required for correct operation.

### Application thread to transmit thread communication

The application sends a buffer using `XferRequest::post()`. This creates a
transaction and places it into the transmit queue, then sets a condition variable
to wake up the transmit thread. The transaction contains a C++ atomic variable
which acts as a reference count. It is initially set to the number of message
fragments required to send the transfer, and is decremented whenever a message
is sent (if retransmit is disabled) or acknowledge (if retransmit is enabled).

When the reference count reaches 0, the buffer is returned to the application.

### Receive thread to transmit thread communication

When a frame is received, `TxThread::handle_received_frame` is called from the
receive thread. This locks the mutex and records ACKs contained in the frame into
a private `std::unordered_set` member variable; these are then picked up by the
transmit thread.

### Transmit thread

Good performance of the transmit thread is critical to achieve good system throughput.
The following principles guide the design of the transmit thread:

* avoid thrashing the heap by allocating and freeing memory for each transmission
* but conversely avoid imposing artificial limits on message size / throughput
    by allocating fixed-size buffers to hold messages in flight, as is done by
    the existing datagram driver
* since the application and receive threads need to take the mutex to send messages
    to the transmit thread, avoid holding the mutex for longer than necessary; in
    particular, do not hold it across the `send()` system call, as this would
    unnecessarily block the application thread when it could make progress
    (particularly true when there are many buffers configured, or many RCC workers)

To satisfy the first two guidelines, we use `std::vector`s which are allocated once
on the stack of the transmit thread to hold per-transaction data and per-frame
data which does not need to be preserved across iterations of the main thread
(list of messages in the transaction; list of IOVs in the frame). These vectors
are cleared on each iteration of the loop but this does not free their backing
storage, which is reused on the next iteration.

Therefore, during application startup these vectors will grow to the right size
(which depends on how the system is configured: e.g. higher MTUs require more
IOVs, larger application buffers require more fragments) which may require several
heap allocations and copies; but for the majority of the lifetime of the application
these buffers will remain fixed - so the amortized cost of heap allocations is
negligible.

For data which has a longer lifetime (`OutboundFrame`s and `OutboundMessage`s
which must remain valid until an ACK is received), a similar approach is used
with an extra layer of indirection. These structures are heap-allocated and
wrapped in `std::unique_ptr`. When a structure reaches the end of its lifetime, rather
than letting the `std::unique_ptr` go out of scope and freeing the underlying
storage, it is pushed on to a free list (private member of the `TxThread`).

When we need a new structure, we first try and pop one off the free list, resorting
to a heap allocation only if necessary. This means we will get a flurry of
allocations early in the application's lifecycle, but once we have allocated
enough buffering to deal with the round-trip delay between sending a frame and
receiving an ACK, there should be few if any further allocations.

Allocation/freeing of these heap-allocated structures is handled by
`TxThread::alloc_frame()/TxThread::free_frame()` and
`TxThread::alloc_message()/TxThread::free_message()`.

To satisfy the final guideline (avoid holding the mutex longer than necessary)
we copy data out of shared data structures in private members of the `TxThread`
class into local structures on the transmit thread's stack. For example in
`TxThread::get_outbound_transactions()` we move transactions to be sent from
`m_txq` (shared member variable) into `txq` (stack variable in `TxThread::run()`).
This means we can drop the lock and allow the application to continue filling the
shared transmit queue while we deal with transactions in the local copy.

### Socket
The `OCPI::OS::Ether::Socket` class is not used; instead we have a minimal
`RawSocket` implementation which just wraps a Linux raw socket. This has a few
advantages over using the `OCPI::OS::Ether::Socket`:

* we use `SOCK_DGRAM` sockets rather than `SOCK_RAW` which means the network stack
    inserts the Ethernet header, making it very straightforward to add a UDP
    implementation in the future
* eliminates a lot of complexity in `OCPI::OS::Ether::Socket` which would
    otherwise need to be worked around (for example, adding and removing padding
    to ensure proper alignment of data following the Ethernet header
* allows us to directly query the MTU of the interface and use it without
    explicit configuration by the user
* `OCPI::OS::Ether::Socket` has a hard limit of 10 IOVs (buffers) per frame,
    which is not enough to deal with DG-RDMA frames containing several messages

## Known issues

* Does not generate ACKs for received packets
* Does not support UDP
* Supports multiple remotes in principle, but in practice this is difficult to
    configure. Uses same approach as existing datagram driver (dispatching based
    on source ID field in incoming DG-RDMA frame header); the source ID is supposed
    to be the mailbox ID of the remote endpoint, but there is currently no way to
    communicate this to the FPGA - the source ID used by the FPGA is configured in
    `system.xml` (or defaults to 1, which is correct for the case of a single remote).
    Using the source MAC address instead to dispatch incoming frames would be
    better
* Does not support operation with multiple local interfaces
