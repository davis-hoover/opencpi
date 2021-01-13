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

// This file implements the singleton class used for process-global behavior on this transport subsystem

#include "TransportPortSet.hh"
#include "TransportDistribution.hh"
#include "TransportPartition.hh"
#include "TransportController.hh"
#include "TransportManager.hh"

namespace OCPI {
namespace DataTransport {

#define EVENT_START 100
#define EVENT_RANGE 20

TransportManager::
TransportManager(unsigned event_ordinal, bool async)
  : m_useEvents(async), m_event_manager(NULL) {
  unsigned
    low = EVENT_START + event_ordinal*EVENT_RANGE,
    high = low + EVENT_RANGE-1;
  if (async) {
    ocpiDebug("GPP: Using events");
    // Create an async event handler object
    m_event_manager = new DataTransfer::EventManager(low, high);
  } else {
    ocpiDebug("GPP: Not Using events");
    m_event_manager = NULL;
  }

  for(unsigned a=0;a<2;a++)
    for(unsigned b=0;b<2;b++)
      for(unsigned c=0;c<2;c++)
	for(unsigned d=0;d<2;d++)
	  for(unsigned e=0;e<2;e++)
	    for(unsigned f=0;f<OCPI::RDT::MaxRole;f++)
	      for(unsigned g=0;g<OCPI::RDT::MaxRole;g++)
		m_controllerFactories[a][b][c][d][e][f][g] = controllerNotSupported;

  //        output dd : input dd : output part : input part : "output shadow" : output role : input role
  m_controllerFactories[DataDistributionMetaData::parallel] [DataDistributionMetaData::parallel]
    [DataPartitionMetaData::INDIVISIBLE][DataPartitionMetaData::INDIVISIBLE] 
    [false] [OCPI::RDT::ActiveMessage] [OCPI::RDT::ActiveFlowControl] 
    = createController<Controller1>;

  m_controllerFactories[DataDistributionMetaData::parallel] [DataDistributionMetaData::parallel]
    [DataPartitionMetaData::INDIVISIBLE][DataPartitionMetaData::INDIVISIBLE] 
    [true] [OCPI::RDT::ActiveMessage] [OCPI::RDT::ActiveFlowControl] 
    = createController<Controller1>;

  // If the output port is AFC, the same controller is used for any input port role
  for(unsigned y=0; y<OCPI::RDT::MaxRole; y++) {
    m_controllerFactories[DataDistributionMetaData::parallel] [DataDistributionMetaData::parallel]
      [DataPartitionMetaData::INDIVISIBLE][DataPartitionMetaData::INDIVISIBLE] 
      [true] [OCPI::RDT::ActiveFlowControl] [y] 
      = createController<Controller1AFCShadow>;

    m_controllerFactories[DataDistributionMetaData::parallel] [DataDistributionMetaData::parallel]
      [DataPartitionMetaData::INDIVISIBLE][DataPartitionMetaData::INDIVISIBLE] 
      [false] [OCPI::RDT::ActiveFlowControl] [y] 
      = createController<Controller1AFC>;
  }
#if 0
  m_controllerFactories[DataDistributionMetaData::parallel] [DataDistributionMetaData::parallel]
    [DataPartitionMetaData::INDIVISIBLE][DataPartitionMetaData::INDIVISIBLE] 
    [true] [OCPI::RDT::Passive] [OCPI::RDT::ActiveOnly] 
    = createController<Controller1Passive>;

  m_controllerFactories[DataDistributionMetaData::parallel] [DataDistributionMetaData::parallel]
    [DataPartitionMetaData::INDIVISIBLE][DataPartitionMetaData::INDIVISIBLE] 
    [false] [OCPI::RDT::ActiveOnly] [OCPI::RDT::Passive] 
    = createController<Controller1Passive>;
#endif
  // Fixme.  All other DD&P patterns have not yet beed ported to the new port "roles" paradigm
  m_controllerFactories[DataDistributionMetaData::parallel][DataDistributionMetaData::sequential]
    [DataPartitionMetaData::INDIVISIBLE][DataPartitionMetaData::INDIVISIBLE] 
    [false] [OCPI::RDT::ActiveMessage] [OCPI::RDT::ActiveMessage] 
    = createController<Controller2>;

  m_controllerFactories[DataDistributionMetaData::sequential][DataDistributionMetaData::sequential]
    [DataPartitionMetaData::INDIVISIBLE][DataPartitionMetaData::INDIVISIBLE] 
    [false] [OCPI::RDT::ActiveMessage] [OCPI::RDT::ActiveMessage] 
    = createController<Controller3>;

  m_controllerFactories[DataDistributionMetaData::parallel][DataDistributionMetaData::parallel]
    [DataPartitionMetaData::INDIVISIBLE][DataPartitionMetaData::BLOCK] 
    [false] [OCPI::RDT::ActiveMessage] [OCPI::RDT::ActiveMessage] 
    = createController<Controller4>;
}

TransportManager::
~TransportManager() {
  delete m_event_manager;
}

Controller &TransportManager::
getController(PortSet &outPortSet, PortSet &inPortSet) {
  // return the factory function in the array element to create the controller
  return
      m_controllerFactories
      [outPortSet.getDataDistribution()->getMetaData()->distType]
      [inPortSet.getDataDistribution()->getMetaData()->distType]
      [outPortSet.getDataDistribution()->getDataPartition()->getData()->dataPartType]
      [inPortSet.getDataDistribution()->getDataPartition()->getData()->dataPartType]
      [outPortSet.getPort(0)->isShadow()]
      [outPortSet.getPort(0)->getMetaData()->m_descriptor.role]
    [inPortSet.getPort(0)->getMetaData()->m_descriptor.role](outPortSet, inPortSet);
}
}
}
