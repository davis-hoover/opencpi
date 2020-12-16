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

#include <algorithm>
#include "farmhash.h"
#include "OcpiOsAssert.h"
#include "OcpiUtilCDR.h"
#include "Container.h"
#include "ContainerPort.h"

namespace OCPI {
  namespace Container {
    namespace OA = OCPI::API;
    namespace OU = OCPI::Util;
    namespace OD = OCPI::DataTransport;
    namespace OR = OCPI::RDT;

    LocalPort::
    LocalPort(Container &a_container, const OCPI::Util::Port &mPort, bool a_isProvider,
	      const OU::PValue *params)
      :  BasicPort(a_container, mPort, a_isProvider, params),
	 m_scale(0), m_external(NULL), m_connectedBridgePorts(0), m_localBridgePort(NULL),
	 m_bridgeContainer(NULL), m_localBuffer(NULL),
	 m_localDistribution(OU::Port::DistributionLimit), m_firstBridge(0), m_currentBridge(0),
	 m_nextBridge(0) {
    }

    LocalPort::
    ~LocalPort() {
      // FIXME: we need to ensure base containers are destroyed last
      if (m_bridgeContainer)
	m_bridgeContainer->unregisterBridgedPort(*this);
      for (unsigned n = 0; n < m_bridgePorts.size(); n++)
	if (m_bridgePorts[n]) // maybe connections did not complete
	  delete m_bridgePorts[n];
      if (m_localBridgePort != this)
	delete m_localBridgePort;
    }

    // This is called soon after construction, but not in the constructor.
    void LocalPort::
    prepareOthers(size_t a_nOthers, size_t mine) {
      m_scale = mine;
      if (a_nOthers) { // nOthers == 0 means no bridging, but to expect one connection
	ocpiDebug("Preparing port for connection to ports scaled crew");
	m_bridgePorts.resize(a_nOthers, NULL);
      }
    }

    // Compute the range of input members that this output member should send to
    // Return true if range is empty
    static bool
    partialRange(size_t outScale, size_t outIndex, size_t inScale, size_t &first,
		 size_t &last) {
      size_t
	minper = inScale / outScale,
	nbumped = inScale % outScale;
      first = outIndex * minper + std::min(nbumped, outIndex);
      last = first + minper - 1 + (outIndex < nbumped ? 1 : 0);
      ocpiDebug("partialRange(%zu, %zu, %zu --> %zu to %zu)",
		outScale, outIndex, inScale, first, last);
      assert(last < inScale);
      return first >= inScale;
    }
    // Compute the sending member which will send to this input member
    static void
    partialSender(size_t outScale, size_t inScale, size_t inIndex, size_t &sender) {
      sender = inIndex * outScale / inScale;
    }

    // Send each message to all in our partial range or discard if range is empty
    void LocalPort::
    oAllP(Launcher::Connection &c, const OU::Port &/*output*/, const OU::Port &/*input*/,
	  unsigned /*op*/, LocalPort::BridgeOp &bo) {
      bo.m_mode = partialRange(c.m_out.m_scale, c.m_out.m_index, c.m_in.m_scale,
			       bo.m_first, bo.m_last) ? Discard : All;
      bo.m_next = bo.m_first;
    }
    // Send cyclically to all, but discard if not in our range
    void LocalPort::
    oCycP(Launcher::Connection &c, const OU::Port &/*output*/, const OU::Port &/*input*/,
	  unsigned /*op*/, LocalPort::BridgeOp &bo) {
      bo.m_mode = partialRange(c.m_out.m_scale, c.m_out.m_index, c.m_in.m_scale,
			       bo.m_first, bo.m_last) ? Discard : CyclicSparse;
    }
    // Send balanced to all, but discard if not in our range
    void LocalPort::
    oBalP(Launcher::Connection &c, const OU::Port &/*output*/, const OU::Port &/*input*/,
	  unsigned /*op*/, LocalPort::BridgeOp &bo) {
      bo.m_mode = partialRange(c.m_out.m_scale, c.m_out.m_index, c.m_in.m_scale,
			       bo.m_first, bo.m_last) ? Discard : Balanced;
    }
    // Send balanced to all
    void LocalPort::
    oBal(Launcher::Connection &/*c*/, const OU::Port &/*output*/, const OU::Port &/*input*/,
	 unsigned /*op*/, LocalPort::BridgeOp &bo) {
      bo.m_mode = Balanced;
    }
    // Send cyclically to all, but discard if not in our range
    void LocalPort::
    oHashP(Launcher::Connection &c, const OU::Port &/*output*/, const OU::Port &input,
	  unsigned op, LocalPort::BridgeOp &bo) {
      bo.m_mode = partialRange(c.m_out.m_scale, c.m_out.m_index, c.m_in.m_scale,
			       bo.m_first, bo.m_last) ? Discard : Hashed;
      bo.m_hashField = input.m_opScaling[op]->m_hashField;
    }
    // Send cyclically to all
    void LocalPort::
    oHash(Launcher::Connection &/*c*/, const OU::Port &/*output*/, const OU::Port &input,
	  unsigned op, LocalPort::BridgeOp &bo) {
      bo.m_mode = Hashed;
      bo.m_hashField = input.m_opScaling[op]->m_hashField;
    }
    // Send from first to first
    void LocalPort::
    oFirst2(Launcher::Connection &c, const OU::Port &/*output*/, const OU::Port &/*input*/,
	   unsigned /*op*/, LocalPort::BridgeOp &bo) {
      if (c.m_out.m_index == 0) {
	bo.m_first = bo.m_last = 0;
	bo.m_mode = All;
      } else
	bo.m_mode = Discard;
    }
    // Send from first to first
    void LocalPort::
    oFirst(Launcher::Connection &/*c*/, const OU::Port &/*output*/, const OU::Port &/*input*/,
	   unsigned /*op*/, LocalPort::BridgeOp &bo) {
      bo.m_first = bo.m_last = 0;
      bo.m_mode = All;
    }
    // Send to all.
    void LocalPort::
    oAll(Launcher::Connection &/*c*/, const OU::Port &/*output*/, const OU::Port &/*input*/,
	 unsigned /*op*/, LocalPort::BridgeOp &bo) {
      bo.m_mode = All;
    }
    // Send as directed
    void LocalPort::
    oDirect(Launcher::Connection &/*c*/, const OU::Port &/*output*/, const OU::Port &/*input*/,
	    unsigned /*op*/, LocalPort::BridgeOp &bo) {
      bo.m_mode = Directed;
    }
    // Send/Receive to/from all cyclically
    void LocalPort::
    ioCyc(Launcher::Connection &/*c*/, const OU::Port &/*output*/, const OU::Port &/*input*/,
	  unsigned /*op*/, LocalPort::BridgeOp &bo) {
      bo.m_mode = Cyclic;
    }
    // Receive from all cyclically, modulo the other side
    void LocalPort::
    iCycMod(Launcher::Connection &c, const OU::Port &/*output*/, const OU::Port &/*input*/,
	     unsigned /*op*/, LocalPort::BridgeOp &bo) {
      bo.m_mode = CyclicModulo;
      bo.m_next = c.m_in.m_index % c.m_out.m_scale;
    }
    // Receive from all cyclically, modulo the other side
    void LocalPort::
    oCycMod(Launcher::Connection &c, const OU::Port &/*output*/, const OU::Port &/*input*/,
	     unsigned /*op*/, LocalPort::BridgeOp &bo) {
      bo.m_mode = CyclicModulo;
      bo.m_next = c.m_out.m_index % c.m_in.m_scale;
    }
    // Receive first to first
    void LocalPort::
    iFirst2(Launcher::Connection &c, const OU::Port &/*output*/, const OU::Port &/*input*/,
	    unsigned /*op*/, LocalPort::BridgeOp &bo) {
      if (c.m_in.m_index == 0) {
	bo.m_first = bo.m_last = 0;
	bo.m_mode = AsAvailable;
      } else
	bo.m_mode = Discard;
    }
    // Receive from one, defined by our range
    void LocalPort::
    iFirstCyc(Launcher::Connection &c, const OU::Port &/*output*/, const OU::Port &/*input*/,
	      unsigned /*op*/, LocalPort::BridgeOp &bo) {
      bo.m_mode = c.m_in.m_index == 0 ? Cyclic : Discard;
    }
    void LocalPort::
    iFirst(Launcher::Connection &/*c*/, const OU::Port &/*output*/, const OU::Port &/*input*/,
	      unsigned /*op*/, LocalPort::BridgeOp &bo) {
      bo.m_first = bo.m_last = 0;
      bo.m_mode = AsAvailable;
    }
    // Receive from any
    void LocalPort::
    iAny(Launcher::Connection &/*c*/, const OU::Port &/*output*/, const OU::Port &/*input*/,
	unsigned /*op*/, LocalPort::BridgeOp &bo) {
      bo.m_mode = AsAvailable;
    }
    // Receive from one, defined by our range
    void LocalPort::
    iOneP(Launcher::Connection &c, const OU::Port &/*output*/, const OU::Port &/*input*/,
	  unsigned /*op*/, LocalPort::BridgeOp &bo) {
      partialSender(c.m_out.m_scale, c.m_in.m_scale, c.m_in.m_index, bo.m_first);
      bo.m_last = bo.m_first;
      bo.m_mode = AsAvailable;
    }
    // Receive from one, defined by our range
    void LocalPort::
    bad(Launcher::Connection &/*c*/, const OU::Port &/*output*/, const OU::Port &/*input*/,
	unsigned /*op*/, LocalPort::BridgeOp &/*bo*/) {
      assert("Incompatible distributions between input and output"==0);
    }
    // Each pair is output to input.
    // The first function sets up the output bridge, the second sets up the input bridge.
    LocalPort::BridgeSetup
    *LocalPort::bridgeModes[OU::Port::DistributionLimit][OU::Port::DistributionLimit][2] = {
      //     input->  All            Cyclic             First               Balanced        Directed   Random          Hashed
      // output \|/
      /* All */      {{oAllP,iOneP}, {oCycP,iOneP},     {oFirst2,iFirst2},  {oBalP,iAny},   {bad,bad}, {oCycP,iOneP},  {oHashP,iAny}},
      /* Cyclic */   {{oAll,ioCyc},  {oCycMod,iCycMod}, {oFirst,iFirstCyc}, {oBal,iAny},    {bad,bad}, {oCycP,iOneP},  {oHash,iAny}},
      /* First */    {{oAll,iFirst}, {ioCyc,iFirst},    {oFirst,iFirst},    {oBal,iAny},    {bad,bad}, {ioCyc,iFirst}, {oHash,iAny}},
      /* Balanced */ {{bad,bad},     {bad,bad},         {bad,bad},          {bad,bad},      {bad,bad}, {bad,bad},      {bad,bad}},
      /* Directed */ {{oAll,iAny},   {oDirect,iAny},    {oFirst,iFirst},    {oDirect,iAny}, {bad,bad}, {oDirect,iAny}, {oHash,iAny}},
      /* Random */   {{oAll,iAny},   {oCycP,iAny},      {oFirst,iAny},      {oCycP,iOneP},  {bad,bad}, {oCycP,iOneP},  {oHash,iAny}},
      /* Hashed */   {{bad,bad},     {bad,bad},         {bad,bad},          {bad,bad},      {bad,bad}, {bad,bad},      {bad,bad}},
    };

    LocalPort::BridgeOp::BridgeOp() : m_first(0), m_last(0), m_next(0), m_hashField(NULL), m_mode(Cyclic) {}

    // Figure out the three parameters for bridge port processing for the given op
    // at this port: the mode, the starting bridge port, and the ending bridge port.
    void LocalPort::
    determineBridgeOp(Launcher::Connection &c, const OU::Port &output, const OU::Port &input,
		      unsigned op, BridgeOp &bo) {
      bo.m_last = m_bridgePorts.size() - 1;
      bridgeModes[output.getDistribution(op)][input.getDistribution(op)][isProvider() ? 1 : 0]
	(c, output, input, op, bo);
    }
    void LocalPort::
    setupBridging(Launcher::Connection &c) {
      const Launcher::Port &other = isProvider() ? c.m_out : c.m_in;
      assert(other.m_port || other.m_metaPort);
      const OU::Port
	&otherMeta = other.m_port ? other.m_port->m_metaPort : *other.m_metaPort,
	&input = isProvider() ? m_metaPort : otherMeta,
	&output = isProvider() ? otherMeta : m_metaPort;
      size_t nOps = std::max(input.nOperations(), output.nOperations());
      m_bridgeOps.resize(nOps);
      m_defaultBridgeOp.m_last = m_bridgePorts.size() - 1;
      for (unsigned n = 0; n < nOps; n++)
	determineBridgeOp(c, output, input, n, m_bridgeOps[n]);
      if (isInProcess(NULL)) {
	becomeShim(NULL);    // skinny set of buffers and flags between codec and worker
	m_localBridgePort = this;
      } else {
	// Communication with this local port will be via a newly created bridge port
	// The codec will talk to this bridge port (thus a bridge port on BOTH sides)
	// The "connection" between the bridge port and "this" local port will be
	// via the preferred method of this port's container.
	const Transports
	  &base = Container::baseContainer().transports(),
	  &mine = container().transports();
	Transport bridged;
	determineTransport(isProvider() ? mine : base, isProvider() ? base : mine,
			   NULL, NULL, NULL, bridged);
	applyConnection(bridged, c.m_bufferSize);
	m_localBridgePort = new BridgePort(Container::baseContainer(), metaPort(), !isProvider(), NULL);
	ocpiDebug("BRIDGE in setupBridging: %p in container %p", m_localBridgePort, &Container::baseContainer());
	m_localBridgePort->applyConnection(bridged, c.m_bufferSize); // native transport
	m_localBridgePort->connectLocal(*this, NULL);
      }
    }

    // Return true if there is something to return to the other side, even if this side is
    // "done".
    bool LocalPort::
    initialConnect(Launcher::Connection &c) {
      OU::SelfAutoMutex guard(this);
      bool more = false;
      Launcher::Port &otherSide = isProvider() ? c.m_out : c.m_in;
      if (m_bridgePorts.size() && m_connectedBridgePorts == 0)
	setupBridging(c); // this will applyConnection as necessary
      else
	applyConnection(c.m_transport, c.m_bufferSize);
      LocalPort *other = otherSide.m_port;
      if (m_bridgePorts.size()) {
	size_t otherOrdinal = (isProvider() ? c.m_out : c.m_in).m_index;
	assert(!m_bridgePorts[otherOrdinal]);
	BridgePort &bp =
	  *(m_bridgePorts[otherOrdinal] =
	    new BridgePort(Container::baseContainer(), metaPort(), isProvider(),
			   (isProvider() ? c.m_in : c.m_out).m_params));
	// we can't imply recurse here without creating a dummy connection.
	bp.applyConnection(c.m_transport, c.m_bufferSize);
	if (!other)
	  more = bp.startRemote(c);
	else if (other->m_bridgePorts.size()) {
	  // bridge ports on both sides locally.  whoever is last does it with forwarding
	  BridgePort *otherBridge =
	    other->m_bridgePorts[(isProvider() ? c.m_in : c.m_out).m_index];
	  if (otherBridge)
	    bp.connectInProcess(c, *otherBridge);
	  else
	    other->initialConnect(c);
	} else if (other->isInProcess(this))
	  bp.connectInProcess(c, *other);
	else
	  bp.connectLocal(*other, &c);
	if (++m_connectedBridgePorts == m_bridgePorts.size()) {
	  // Save the bridge container so we know it in our destructor when we can't call
	  // containers' virtual methods
	  m_bridgeContainer =
	    &(container().needThread() ? container() : Container::baseContainer());
	  m_bridgeContainer->registerBridgedPort(*this);
	  portIsConnected();
	}
      } else if (!other) // if other side is remote
	more = startRemote(c); // could return false on output port
      else if (other->m_bridgePorts.size())
	other->initialConnect(c); // do it all from the other side in this case.
      else if (&container() == &other->container() && container().connectInside(*this, *other)) {
	portIsConnected();
	other->portIsConnected();
	c.m_in.m_done = c.m_out.m_done = true;
      } else if (isInProcess(other) && other->isInProcess(this))
	connectInProcess(c, *other);
      else {
	other->applyConnection(c.m_transport, c.m_bufferSize);
	connectLocal(*other, &c); // both workers are in this process
      }
      return more;
    }

    // Try to complete the connection on this worker member port.
    // We expect to be called again if we return true
    bool LocalPort::
    finalConnect(Launcher::Connection &c) {
      OU::SelfAutoMutex guard(this);
      if (m_bridgePorts.empty())
	// We'll only be called in the remote case here.
	return finishRemote(c);
      else {
	size_t otherMember = (isProvider() ? c.m_out : c.m_in).m_index;
	ocpiAssert(m_bridgePorts[otherMember]);
	return m_bridgePorts[otherMember]->finishRemote(c);
      }
    }

    // Make sure a local buffer is available and return true of there is one ready to go.
    // Also, for each new local buffer, initialize m_bridgeOp (and m_currentBuffer)
    // If m_localBuffer is set but m_bridgeOp is NOT set, it means we can't yet do anything,
    // since we don't have the opcode yet (input only - output has opcode from local buffer).
    // Thus for a local input, we don't return true unless there is a local buffer AND
    // there is an acceptable incoming message to receive.
    inline bool LocalPort::
    getLocalBuffer() {
      BasicPort &lbp = *m_localBridgePort;
      if (m_localBuffer) {
	if (m_bridgeOp)
	  return true; // we're processing a local buffer with a known opcode
      } else if (!((m_localBuffer =
		    isProvider() ?
		    lbp.getEmptyBuffer() : lbp.getFullBuffer())))
	return false;  // there is no local buffer to work with
      uint8_t op;
      if (isProvider()) {
	// Find a bridge with a message and opcode
	unsigned bpn = m_nextBridge;
	do {
	  ocpiDebug("getLocalBuffer input: port %p (%s) buf %p trying bpn %u %p ",
		    this, name().c_str(), m_localBuffer, bpn, m_bridgePorts[bpn]);
	  //	  assert("Peeking for opcode for bridge ports disabled"==0);
	  if (m_bridgePorts[bpn]->peekOpCode(op)) {
	    assert(m_bridgeOps.empty() || op < m_bridgeOps.size());
	    BridgeOp &bo = m_bridgeOps.empty() ? m_defaultBridgeOp : m_bridgeOps[op];
	    ocpiDebug("getLocalBuffer: op %u nops %zu mode %u, first %zu last %zu next %zu",
		      op, m_metaPort.nOperations(), bo.m_mode, bo.m_first, bo.m_last, bo.m_next);
	    // Accept the bridge message if we can process it now
	    if (bo.m_mode == AsAvailable || bpn == bo.m_next) {
	      assert(bpn >= bo.m_first && bpn <= bo.m_last);
	      m_bridgeOp = &bo;
	      bo.m_next = bpn; // if AsAvailable, set this
	      return true;
	    }
	  }
	  if (++bpn >= m_bridgePorts.size())
	    bpn = 0;
	} while (bpn != m_nextBridge);
	m_bridgeOp = NULL;
	return false;
      }
      ocpiDebug("getLocalBuffer output: port %p (%s) buf %p ", this, name().c_str(), m_localBuffer);
      // Sending a local buffer.  Bridge op tells us which bridge(s) to use.
      op = m_localBuffer->opCode();
      assert(m_bridgeOps.empty() || op < m_bridgeOps.size());
      m_bridgeOp = m_bridgeOps.empty() ? &m_defaultBridgeOp : &m_bridgeOps[op];
      return true;
    }

    static inline void
    send2Bridge(ExternalBuffer &local, ExternalBuffer &bridge) {
      assert(bridge.length() >= local.length());
      memcpy(bridge.data(), local.data(), local.length());
      bridge.send(local.length(), local.opCode(), local.end());
    }

    // The callback to do bridge port processing on a local port.
    void LocalPort::
    runBridge() {
      OU::SelfAutoMutex guard(this);
      // Wait for all bridge connections to be made to this local port.
      if (m_connectedBridgePorts != m_bridgePorts.size())
	return;
      // Keep going while there are local buffers we can process
      // If this returns true, we have both m_currentBuffer and m_bridgeOp
      while (getLocalBuffer()) {
	BridgeOp &bo = *m_bridgeOp;
	if (isProvider()) {
	  // getLocalBuffer already found a bridge port so it is ready to go.
	  // it had to find a bridge port since it had to know what message opcode is current
	  BridgePort &bp = *m_bridgePorts[bo.m_next];
	  ExternalBuffer *b = bp.getFullBuffer();
	  assert(b);
	  ocpiDebug("bridging for %p got local input %p from local side len %zu %zu",
		    this, m_localBuffer, m_localBuffer->length(), b->length());
	  assert(m_localBuffer->length() >= b->length());
	  assert(m_localBuffer->data());
	  memcpy(m_localBuffer->data(), b->data(), b->length());
	  m_localBuffer->send(b->length(), b->opCode(), b->end());
	  bp.releaseBuffer(*b);
	  m_localBuffer = NULL;
	  // Cycle nextBridge globally among all bridge ports.
	  if (++m_nextBridge == m_bridgePorts.size())
	    m_nextBridge = 0;
	  // Cycle the bridgeOp in its own set.
	  if (bo.m_mode == CyclicModulo)
	    bo.m_next = (bo.m_next + m_scale) % m_bridgePorts.size();
	  else
	    bo.m_next = bo.m_next == bo.m_last ? bo.m_first : bo.m_next + 1;
	} else {
	  ocpiDebug("bridging for %p got local output %p mode %u next %zu last %zu", this,
		    m_localBuffer, bo.m_mode, bo.m_next, bo.m_last);
	  size_t next = bo.m_next;
	  ExternalBuffer *lb = m_localBuffer; // save for later release
	  // Phase 1: figure out which bridge port and whether to discard the message.
	  switch (bo.m_mode) {
	  case CyclicSparse:
	    if (next < bo.m_first || next > bo.m_last)
	      m_localBuffer = NULL;
	    break;
	  case Balanced:
	    // For now, left be cyclic
	    break;
	  case Directed:
	    next = m_localBuffer->direct();
	    assert(next < m_bridgePorts.size());
	    break;
	  case Hashed:
	    {
	      size_t length;
	      const uint8_t *data = bo.m_hashField->getField(m_localBuffer->data(), length);
	      assert(data);
	      next = OU::Hash((const char*)data, length) % m_bridgePorts.size();
	      if (next < bo.m_first || next > bo.m_last)
		m_localBuffer = NULL;
	    }
	    break;
	  case Discard:
	    m_localBuffer = NULL;
	    break;
	  default:;
	  }
	  if (m_localBuffer) { // have a full output from local port
	    // Phase 2: see if the identified bridge port has a buffer after all and ship it.
	    BridgePort *bp = m_bridgePorts[next];
	    ExternalBuffer *b = bp->getEmptyBuffer();
	    if (!b)
	      return;
	    send2Bridge(*m_localBuffer, *b);
	    // Phase 3: do post processing, to compute bo.m_next, etc. "all" is special case
	    switch (bo.m_mode) { // break to process buffer if b != NULL
	    case Cyclic:
	      bo.m_next = next == bo.m_last ? bo.m_first : ++next;
	      break;
	    case CyclicSparse:
	      if ((bo.m_next = ++next) >= m_bridgePorts.size())
		bo.m_next = 0;
	      break;
	    case CyclicModulo:
	      bo.m_next += m_scale;
	      bo.m_next %= m_bridgePorts.size();
	      break;
	    case All:
	      // A special case where we loop and replicate the output
	      while (bo.m_next != bo.m_last) {
		bo.m_next++;
		bp = m_bridgePorts[bo.m_next];
		if (!(b = bp->getEmptyBuffer()))
		  return;
		send2Bridge(*m_localBuffer, *b);
	      }
	      break;
	    case Balanced: // do cyclic for now.
	      bo.m_next = next == bo.m_last ? bo.m_first : ++next;
	      break;
	    case Directed:
	    case Hashed:
	    default:;
	    }
	    m_localBuffer = NULL;
	  }
	  lb->release();
	} // end of output processing
      } // end of loop through local buffers
    }  // end of method
  } // end of namespace Container
} // end of namespace OCPI
