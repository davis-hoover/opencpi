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

#ifndef OCPI_Transport_Manager_H_
#define OCPI_Transport_Manager_H_


#include "XferEvent.h"
#include "OcpiPortSet.h"
#include "OcpiRDTInterface.h"
#include "OcpiTransportConstants.h"
#include "TransportController.hh"

namespace OCPI {
namespace DataTransport {

class Transport;
class TransportManager {
  // polling or events
  bool m_useEvents;
  // This is an array of factory functions that create the right type of transfer controller
  typedef Controller &(*CreateController)(Transport &transport, PortSet &output, PortSet &input);
  CreateController m_controllers[2][2][2][2][2][OCPI::RDT::MaxRole][OCPI::RDT::MaxRole];
protected:

  // Our event handler
  DataTransfer::EventManager* m_event_manager;
public:

  TransportManager(unsigned event_ordinal, bool use_events);
  virtual ~TransportManager();
  DataTransfer::EventManager* getEventManager() { return m_event_manager;}
  bool useEvents() {return m_useEvents;}
  Controller &getController(Transport &transport, PortSet &outPortSet, PortSet &inPortSet);
};

} // namespace DataTransport
} // namespace OCPI

#endif
