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

#ifndef OCPI_Transport_PortSet_H_
#define OCPI_Transport_PortSet_H_

#include "OcpiTransportConstants.h"
#include "TransportDistribution.hh"
#include "OcpiPort.h"
#include "BaseParentChild.hh"
#include "OcpiTimeEmit.h"

namespace OCPI {
namespace DataTransport {

// Forward references
class Circuit;
class Port;
class Buffer;
class Controller;

class PortSet : public OCPI::Util::Child<Circuit,PortSet>, public OCPI::Util::Parent<Port>,
		public OCPI::Util::Parent<PortMetaData>, public OCPI::Time::Emit {
  unsigned           m_portCount; // count of children, not m_ports.size() since it can be sparse
  OCPI::Util::VList  m_portMd;
  OCPI::Util::VList  m_ports;     // children in ordinal vector
  bool               m_isOutput;
  Controller        *m_transferController; // not a ref since it is set after construction
  DataDistribution  &m_dataDistribution;
  uint32_t           m_bufferCount;
  uint32_t           m_bufferLength;

public:
  PortSet(Circuit &c, bool isOutput, DataDistribution &dd, unsigned bufferCount,
	  unsigned bufferSize,
	  unsigned portCount = 0,                   // if zero we are creating it empty
	  DataTransfer::EndPoint *outputEp = NULL,  // non-NULL when we are creating ports
	  DataTransfer::EndPoint **inputEp = NULL,  // non-NULL when are are creating ports, port port
	  const OCPI::RDT::Descriptors *inputDesc = NULL);
  ~PortSet();

  inline PortMetaData *getPortInfo(uint32_t idx) {
    return static_cast<PortMetaData*>(m_portMd[idx]);
  }
  Circuit *getCircuit() { return &parent(); } // need to change callers and return a ref
  DataDistribution *getDataDistribution() { return &m_dataDistribution; }
  Port *getPortFromIndex(unsigned idx);
  Port *getPort(unsigned idx) { return getPortFromIndex(idx); }
  inline Port *getPortFromOrdinal(PortOrdinal id) {
    if (id >= m_ports.size())
      ocpiAbort("id => m_ports.size()"); // always assert when asserts are disabled
    return static_cast<Port*>(m_ports[id]);
  }

  Controller *getTxController() { return m_transferController;}
  void setTxController(Controller *t) { m_transferController = t; }
  unsigned getPortCount() { return m_portCount;}
  unsigned getSize() { return m_portMd.size();}
  unsigned &getBufferCount() { return m_bufferCount;}
  unsigned &getBufferLength() { return m_bufferLength;}
  bool isOutput() { return m_isOutput; }

  void addPortMetaData(PortMetaData *pmd);
  // Informs the shadow port that it can queue a pull data transfer from the real port.
  Buffer *pullData(Buffer *buffer);
private:
  void addPort(Port *port);
};
class PortSetMetaData : public PortSet {};

} // DataTransport
} // OCPI

#endif
