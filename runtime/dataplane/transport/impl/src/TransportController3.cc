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

#include "OcpiList.h"
#include "OcpiOsAssert.h"
#include "OcpiTimeEmitCategories.h"
#include "OcpiCircuit.h"
#include "OcpiPortSet.h"
#include "OcpiBuffer.h"
#include "OcpiOutputBuffer.h"
#include "OcpiInputBuffer.h"
#include "OcpiIntDataDistribution.h"
#include "TransportController.hh"

///
////  Transfer controller for pattern 3
///

namespace DDT = DtOsDataTypes;
namespace DT = DataTransfer;
namespace OCPI {
namespace DataTransport {

void Controller3::
addTransferPreState(DT::XferRequest* pt, Port &s_port, unsigned s_tid, Port &t_port, unsigned t_tid) {
  ocpiDebug("*** In TransferTemplateGeneratorPattern3::addTransferPreState()");

  // We need to update all of the shadow buffers for all "real" output ports
  // to let them know that the input buffer for this input port has been allocated
  struct PortMetaData::InputPortBufferControlMap *input_offsets = 
    &t_port.getMetaData()->m_bufferData[t_tid].inputOffsets;

  unsigned our_smb_id = s_port.getMailbox();
  PortSet *sps = static_cast<PortSet*>(s_port.getPortSet());
  for (PortOrdinal n = 0; n < sps->getPortCount(); n++) {

    Port* shadow_port = static_cast<Port*>(sps->getPortFromIndex(n));
    unsigned idx = shadow_port->getMailbox();

    // We need to ignore self transfers
    if (idx == our_smb_id)
      continue;

    // A shadow for a output may not exist if they are co-located
    if (input_offsets->myShadowsRemoteStateOffsets[idx] != 0) {
      ocpiDebug("TransferTemplateGeneratorPattern3::addTransferPreState mapping shadow offset to 0x%llx", 
             (long long)input_offsets->myShadowsRemoteStateOffsets[idx]);
      DT::XferRequest* ptransfer =
	s_port.getTemplate(s_port.getEndPoint(), shadow_port->getEndPoint()).
	createXferRequest();
      pt->group(ptransfer);
      try {
        // Create the transfer that copys the local shadow buffer state to the remote
        // shadow buffers state
        ptransfer->copy (input_offsets->myShadowsRemoteStateOffsets[our_smb_id],
			 input_offsets->myShadowsRemoteStateOffsets[idx],
			 sizeof(BufferState),
			 DT::XferRequest::FlagTransfer);
      } catch ( ... ) {
        FORMAT_TRANSFER_EC_RETHROW(&s_port, shadow_port);
      }
    }
  }

  // Now we need to pass the output control baton onto the next output port
  unsigned next_output = (s_port.getPortId() + 1) % sps->getPortCount();
  Port &next_sp = *static_cast<Port*>(sps->getPortFromIndex(next_output));

  struct PortMetaData::OutputPortBufferControlMap *output_offsets = 
    &s_port.getMetaData()->m_bufferData[s_tid].outputOffsets;

  struct PortMetaData::OutputPortBufferControlMap *next_output_offsets = 
    &next_sp.getMetaData()->m_bufferData[s_tid].outputOffsets;

  DT::XferRequest * ptransfer2 =
    s_port.getTemplate(s_port.getEndPoint(), next_sp.getEndPoint()).
    createXferRequest();

  // Create the transfer from out output contol state to the next

  try {
    ptransfer2->copy(output_offsets->portSetControlOffset,
		     next_output_offsets->portSetControlOffset,
		     sizeof(OutputPortSetControl),
		     DT::XferRequest::FlagTransfer);
  } catch ( ... ) {
    FORMAT_TRANSFER_EC_RETHROW(&s_port, &next_sp);
  }
  pt->group(ptransfer2);
}

} // namespace DataTransport
} // namespace OCPI
