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

#include "TransportPort.hh"
#include "TransportCircuit.hh"
#include "TransportPortMetaData.hh"
#include "TransportController.hh"
#include "TransportPortSet.hh"

namespace XF = OCPI::Xfer;
namespace OCPI {
namespace Transport {

PortSet::
PortSet(Circuit &c, bool isOutput, DataDistribution &dd, unsigned bufferCount,
	unsigned bufferSize,
	unsigned portCount,             // if zero we are creating it empty (with no ports yet)
	XF::EndPoint *outputEp,        // non-NULL when we are creating ports
	XF::EndPoint **inputEp,        // non-NULL when are are creating ports, port port
	const Descriptors *inputDesc) // when we are creating ports, per port
  : OCPI::Util::Child<Circuit,PortSet>(c, *this ),
    OCPI::Time::Emit(&c, "PortSet"),
    m_portCount(portCount), m_isOutput(isOutput), m_transferController(NULL),
  m_dataDistribution(dd), m_bufferCount(bufferCount), m_bufferLength(bufferSize) {

  m_ports.noShuffle();
  for (unsigned n = 0; n < m_portCount; n++) {
    auto *pmd = new PortMetaData(n+1, *outputEp, *inputEp[n], inputDesc[n], this);
    pmd->m_portSetMd = this;
    m_portMd.push_back(pmd);
    addPort(new Port(pmd, this));
  }
  // addPortMetaData(new PortMetaData(n+1, *outputEp, *inputEp[n], inputDesc[n], this));

  for (unsigned n = 0; n < m_portMd.size(); n++) {
    PortMetaData *pmd = static_cast<PortMetaData *>(m_portMd[n]);
    if (!static_cast<Port *>(getPortFromOrdinal(pmd->id)))
      addPort(new Port(pmd, this));
  }
}

PortSet::
~PortSet() {
  delete &m_dataDistribution;
  for (unsigned n = 0; n < m_portCount; n++)
    delete getPortFromIndex(n);
  m_ports.destroyList();
  if (!m_isOutput &&  m_transferController)
    delete m_transferController;
}

void PortSet::
addPortMetaData(PortMetaData *pmd) {
  pmd->m_portSetMd = this;
  m_portMd.push_back(pmd);
  addPort(new Port(pmd, this));
  m_portCount++;
}

void PortSet::
addPort(Port *port) {
  m_ports.insertToPosition(port, port->getPortId());
}

Port *PortSet::
getPortFromIndex(unsigned idx) {
  for (unsigned f = 0, n = 0; n < m_ports.size(); n++)
    if (m_ports[n]) {
      if (f == idx)
        return static_cast<Port *>(m_ports[n]);
      f++;
    }
  return NULL;
}

Buffer *PortSet::
pullData(Buffer */*buffer*/) {
  Port *p = getPortFromIndex(0);
  ocpiAssert(p->getMetaData()->m_shadowPortDescriptor.role == ActiveFlowControl);

  // We got notified because the output port indicated that it has data available on this
  // buffer, so Q the transfer
  Buffer *b = p->getNextEmptyOutputBuffer();
  b->send();
  return b;
}

}
}
