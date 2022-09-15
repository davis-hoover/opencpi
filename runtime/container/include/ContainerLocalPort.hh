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

#ifndef CONTAINER_LOCAL_PORT_H
#define CONTAINER_LOCAL_PORT_H

#include "OcpiContainerApi.hh"

#include "UtilSelfMutex.hh"
#include "BasePValue.hh"
#include "TransportRDTInterface.hh"
#include "MetadataPort.hh"
#include "BaseParentChild.hh"
#include "ContainerLauncher.hh"
#include "ContainerBasicPort.hh"

namespace OCPI {
  namespace Container {

    class Worker;
    class ExternalPort;
    class Container;

    // This class is the behavior common to both ports of local member workers,
    // as well as external ports in this process.
    // The common behavior includes:
    // Possible connection to remote ports outside the process
    // Possible connection to a multi-member crew inside or outside
    // Note that "BasicPort" is shared with BridgePort, but
    // LocalPorts actually own bridge ports (not parent/child yet).
    class BridgePort;
    class LocalPort : public BasicPort {
      friend class Container;
      friend class LocalLauncher;
      friend class Worker;
      friend class BridgePort;
      friend class Port;
      // Modes of bridge processing.
      // Input side has only: Cyclic, CyclicModulo, AsAvailable
      // Output side has more.
      enum BridgeMode {
	Cyclic,         // input: receive from output members in range
	                // output: rotate through all inputs in range
	CyclicSparse,   // output: rotate through all inputs, discard if not in set
	CyclicModulo,   // output: rotate through all inputs, skipping our crew size
	                //         module other crew size
	                // input:  ditto
	AsAvailable,    // input: receive from set as available, rotating the look
	All,            // output: send to all in the specified set
	Balanced,       // output: if least busy is in specified set, send, else discard
	Directed,       // output: take input member from API
	Hashed,         // output: compute input member based on hash of m_hashField
	Discard,        // output: discard messages
	ModeLimit
      };
      size_t                         m_scale;               // zero is no bridging at all
      LocalPort                     *m_external;            // inserted external port
      // State relating to having bridge ports (member talking to multiple other members)
      std::vector<BridgePort*>       m_bridgePorts;
      unsigned                       m_connectedBridgePorts;// count to know when all are ready
      BasicPort                     *m_localBridgePort;     // bridging to not-in-process ports
      Container                     *m_bridgeContainer;     // container we are registered with
      struct BridgeOp {
	size_t
	  m_first,  // first opposite member to deal with
	  m_last,   // last opposite member to deal with
	  m_next;   // next opposite member to deal with
	const OCPI::Base::Member *m_hashField;
	BridgeMode m_mode;
	BridgeOp();
      } *m_bridgeOp;
      std::vector<BridgeOp> m_bridgeOps;
      BridgeOp m_defaultBridgeOp; // used when there are no operations at the ports
      // These are the functions to set up the bridge op according distribution and scale
      // on both sides, per op.

      typedef void BridgeSetup(Launcher::Connection &c, const OCPI::Metadata::Port &output,
			       const OCPI::Metadata::Port &input, unsigned op, BridgeOp &bo);
      static BridgeSetup
	*bridgeModes[OCPI::Metadata::Port::DistributionLimit] [OCPI::Metadata::Port::DistributionLimit][2],
	oAllP, oCycP, oFirst2, oBalP, oHashP, oAll, oCycMod, oFirst, oBal, oHash, oDirect,
	iOneP, iFirst2, iAny, iFirst, iFirstCyc, iCycMod, ioCyc,
	bad;

      // State of the current local buffer (external or member)
      ExternalBuffer                *m_localBuffer;         // current available buffer
      OCPI::Metadata::Port::Distribution m_localDistribution;   // distribution for current opcode
      // Indexing in bridges for current local buffer
      unsigned                       m_firstBridge;         // first one for current local buf
      unsigned                       m_currentBridge;       // current bridge for local buf
      unsigned                       m_nextBridge;          // next one to use for any op
    protected:
      LocalPort(Container &container, const OCPI::Metadata::Port &mPort, bool isProvider,
		const OCPI::Base::PValue *params);
      virtual ~LocalPort();
    private:
      // Is this port actually *operating* in this process, with its buffers in this process?
      // Essentially ports are either:
      // - in this process, with buffers here
      // - local, meaning managed from in this process, but with the buffers elsewhere
      // - remote, meaning managed and owned in another process
      // "other" is the other local maybe-in-process port involved
      // "other" being NULL means the other port is remote in another process
      virtual bool isInProcess(LocalPort *other) const = 0;
      bool getLocalBuffer();
      void setupBridging(Launcher::Connection &c);
      void determineBridgeOp(Launcher::Connection &c, const OCPI::Metadata::Port &output,
			     const OCPI::Metadata::Port &input, unsigned op, BridgeOp &bo);
    protected:
      bool initialConnect(Launcher::Connection &c);
      bool finalConnect(Launcher::Connection &c);
      //      void insertExternal(Launcher::Connection &c);
      virtual bool canBeExternal() const = 0;
      void prepareOthers(size_t nOthers, size_t myCrewSize);
      void runBridge(); // flow data between this port and its bridge ports
    public:
      size_t nOthers() const { return m_bridgePorts.size(); }
    };

  }
}
#endif



