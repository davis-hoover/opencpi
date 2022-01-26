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

// This file declares the singleton class used for process-global behavior on this transport subsystem

#ifndef OCPI_Transport_Manager_H_
#define OCPI_Transport_Manager_H_

#include "XferEvent.hh"
#include "TransportRDTInterface.hh"

namespace OCPI {
namespace Transport {

class PortSet;
class Controller;

class TransportManager {
  bool m_useEvents;  // polling or events
  // This is an array of factory functions that create the right type of transfer controller
  // based on input and output port set characteristics
  // It is initialized with runtime code rather than statically
  Controller &
  (*m_controllerFactories[2][2][2][2][2][MaxRole][MaxRole])
  (PortSet &output, PortSet &input);
  
  // Our event handler, this is out of commission
  OCPI::Xfer::EventManager* m_event_manager; // FIXME:  move this down to the xfermanager layer
public:
  TransportManager(unsigned event_ordinal, bool use_events);
  virtual ~TransportManager();
  OCPI::Xfer::EventManager* getEventManager() { return m_event_manager;}
  bool useEvents() {return m_useEvents;}
  Controller &getController(PortSet &outPortSet, PortSet &inPortSet);
};

} // namespace DataTransport
} // namespace OCPI

#endif
