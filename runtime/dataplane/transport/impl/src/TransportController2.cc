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
////  Transfer controller for pattern 2
///

namespace DDT = DtOsDataTypes;
namespace DT = DataTransfer;
namespace OCPI {
namespace DataTransport {

Controller2::
Controller2(PortSet &output, PortSet &input)
  : Controller(output, input) {
  ocpiAssert(input.getDataDistribution()->getMetaData()->distSubType ==
	     DataDistributionMetaData::least_busy);
}

void Controller2::
addTransferPreState(DT::XferRequest */*pt*/, Port &/*s_port*/, unsigned /*s_tid*/,
		    Port &/*t_port*/, unsigned /*t_tid*/) {
}
void Controller2::
createOutputTransfers(Port &s_port) {
  ocpiAssert("pattern2 output"==0);
  /*
   *        For a WP / SW transfer, we need to be capable of transfering from any
   *  output buffer to any one input buffer.
   */
  ocpiDebug("In createOutputTransfers, pattern #2");
  // Since this is a whole output distribution, only port 0 of the output
  // set gets to do anything.
  if (s_port.getPortSet()->getDataDistribution()->getMetaData()->distType ==
      DataDistributionMetaData::parallel &&
       s_port.getRank() != 0)
    return;
  unsigned n,
    n_s_buffers = m_output.getBufferCount(),
    n_t_buffers = m_input.getBufferCount(),
    n_t_ports = m_input.getPortCount();

  // We need a transfer template to allow a transfer from each output buffer to every
  // input buffer for this pattern.
  for (unsigned s_buffers = 0; s_buffers < n_s_buffers; s_buffers++) {
    // output buffer
    OutputBuffer* s_buf = s_port.getOutputBuffer(s_buffers);
    unsigned s_tid = s_buf->getTid();

    // Now we need to create a template for each input port
    for (n = 0; n < n_t_ports; n++) {
      // Get the input port
      Port &t_port = *m_input.getPort(n);

      // We need a transfer template to allow a transfer to each input buffer
      for (unsigned t_buffers = 0; t_buffers < n_t_buffers; t_buffers++) {
        // Get the buffer for the current port
        // input buffer
        InputBuffer* t_buf = t_port.getInputBuffer(t_buffers);
        unsigned t_tid = t_buf->getTid();

        // Create a template
        Transfer &temp = *new Transfer(2);

        // Add the template to the controller, for this pattern the output port
        // and the input ports remains constant

        ocpiDebug("output port id = %d, buffer id = %d, input id = %d, temp=%p", 
		  s_port.getPortId(), s_tid, t_tid, &temp);
        setTemplate(temp, s_port.getPortId(), s_tid, t_port.getPortId() ,t_tid, false, OUTPUT );

        struct PortMetaData::OutputPortBufferControlMap *output_offsets = 
          &s_port.getMetaData()->m_bufferData[s_tid].outputOffsets;

        struct PortMetaData::InputPortBufferControlMap *input_offsets = 
          &t_port.getMetaData()->m_bufferData[t_tid].inputOffsets;

	//        TDataInterface tdi(s_port,s_tid,t_port,t_tid);

        // We need to determine if this can be a Zero copy transfer.  If so, 
        // we dont need to create a transfer template
        bool standard_transfer = true;
        if (m_zcopyEnabled && s_port.supportsZeroCopy(&t_port)) {
          ocpiDebug("** ZERO COPY TransferTemplateGeneratorPattern2::createOutputTransfers from %p, to %p",
		    s_buf, t_buf);
          temp.addZeroCopyTransfer(s_buf, t_buf);
          standard_transfer = false;
        }

	DT::XferRequest::Flags flags;
	DT::XferRequest *ptransfer =
	  s_port.getTemplate(s_port.getEndPoint(), t_port.getEndPoint()).createXferRequest();

        // Pre-data transfer hook
#if 1
	flags = DT::XferRequest::DataTransfer;
#else
	!! there is no implementation that returns true from addTransferPreData
        bool added = addTransferPreData(ptransfer, tdi);
        flags =added ? DT::XferRequest::None : DT::XferRequest::DataTransfer;
#endif

        // Create the transfer that copys the output data to the input data
        if (standard_transfer) {
          try {
            ptransfer->copy (output_offsets->bufferOffset,
			     input_offsets->bufferOffset,
			     output_offsets->bufferSize,
			     (DT::XferRequest::Flags)(flags | DT::XferRequest::DataTransfer));
          } catch ( ... ) {
            FORMAT_TRANSFER_EC_RETHROW(&s_port, &t_port);
          }
        }
        // Post-data transfer hook
#if 0
	!! there is no implementation that returns true from addTransferPostData
        addTransferPostData(ptransfer, tdi);
#endif
        // Create the transfer that copys the output meta-data to the input meta-data
        if (standard_transfer) {
          try {
            ptransfer->copy (output_offsets->metaDataOffset + s_port.getPortId() * OCPI_SIZEOF(DDT::Offset, BufferMetaData),
			     input_offsets->metaDataOffset + s_port.getPortId() * OCPI_SIZEOF(DDT::Offset, BufferMetaData),
			     sizeof(OCPI::OS::int64_t),
			     DT::XferRequest::MetaDataTransfer);
          } catch ( ... ) {
            FORMAT_TRANSFER_EC_RETHROW(&s_port, &t_port);
          }
        }
        // Pre-state transfer hook
        addTransferPreState(ptransfer, s_port, s_tid, t_port, t_tid);
        // Create the transfer that copys the output state to the remote input state
        if (standard_transfer) {
          try {
            ptransfer->copy (output_offsets->localStateOffset + s_port.getPortId() * OCPI_SIZEOF(DDT::Offset, BufferState),
			     input_offsets->localStateOffset + s_port.getPortId() * OCPI_SIZEOF(DDT::Offset, BufferState),
			     sizeof(BufferState),
			     DT::XferRequest::FlagTransfer);
          } catch ( ... ) {
            FORMAT_TRANSFER_EC_RETHROW(&s_port, &t_port);
          }
        }
        // Add the transfer 
	temp.addTransfer(ptransfer);
      } // end for each input buffer
    } // end for each input port
  }  // end for each output buffer
}

bool Controller2::
canProduce(Buffer* buffer) {
  // With this pattern, only port 0 of the output port set can produce
  if (m_isWholeOutputSet && buffer->getPort()->getRank() != 0)
    return true;
  // Broadcast is a special case
  if (buffer->getMetaData()->endOfStream) {
#ifdef DEBUG_L2
    ocpiDebug("*** Testing canproduce via broacast !!");
#endif
    return canBroadcast(buffer);
  }

  // Make sure we have the barrier token
  OutputBuffer *s_buf = static_cast<OutputBuffer*>(buffer);
  if (!haveOutputBarrierToken(s_buf))
    return false;

  m_inputPort = NULL;

  // We will go to each of our shadows and figure out if they are empty

  // With this pattern, we sequence the output buffers to ensure that the input always
  // has the next buffer of data in one of its buffers, but we dont have to worry about 
  // sequencing through its buffers in order because the inputs have the logic needed
  // to re-sequence there own buffers

  for (PortOrdinal n = 0; n < m_input.getPortCount(); n++) {
    Port *port = m_input.getPort(n);
    for (unsigned p = 0; p < m_input.getBufferCount(); p++) {

#ifdef DEBUG_L2
      ocpiDebug("canProduce:: busy factor for port %d = %d", n, port->getBusyFactor() ) ;
#endif
      if (port->getBuffer(p)->isEmpty()) {
        if (m_inputPort) {
          if (port->getBusyFactor() < m_inputPort->getBusyFactor()) {
            m_nextTid = p;
            m_inputPort = port;
          }
        } else {
          m_nextTid = p;
          m_inputPort = port;
        }
        break;
      }
    }
  }

#ifdef DEBUG_L2
  if (m_inputPort) 
    ocpiDebug("Selected Port %d with BF = %d", m_inputPort->getPortId(), m_inputPort->getBusyFactor() );
#endif

  return m_inputPort ? true : false;
}

unsigned Controller2::
produce(Buffer* b, bool bcast) {
  OutputBuffer* buffer = static_cast<OutputBuffer*>(b);

  if (bcast) {
#ifdef DEBUG_L2
    ocpiDebug("*** producing via broadcast, rank == %d !!", b->getPort()->getRank());
#endif
    if (! buffer->getMetaData()->endOfStream)
      ocpiDebug("*** ERROR *** EOS not set via broadcast !!");
  }

  // With this pattern, only port 0 of the output port set can produce
  if (m_isWholeOutputSet && b->getPort()->getRank() != 0) {
#ifdef DEBUG_L2
    ocpiDebug("My rank != 0 so i am not producing !!!");
#endif
    // We need to mark the local buffer as free
    buffer->markBufferEmpty();
    return 0;
  }

  // Broadcast if requested
  if (bcast) {
    broadCastOutput(buffer);
    return 0;
  }

  // We need to mark our buffer as full
  buffer->markBufferFull();

  // Here we will mark the lstate of the input port as full
  Buffer* tbuf = static_cast<Buffer*>(m_inputPort->getBuffer(m_nextTid));
  tbuf->markBufferFull();

  // We need to increment the token value to enable the next output port
  buffer->getControlBlock()->sequentialControlToken = 
    (buffer->getControlBlock()->sequentialControlToken + 1) %
    buffer->getPort()->getPortSet()->getPortCount();
  /*
   *  For this pattern the output port and input port are constants when we look 
   *  up the template that we need to produce.  So, since the output tid is a given,
   *  the only calculation is the input tid that we are going to produce to.
   */
  auto &temp = getTemplate(buffer->getPort()->getPortId(), buffer->getTid(),
			   m_inputPort->getPortId(), m_nextTid, bcast, OUTPUT);
#ifdef DEBUG_L2
  ocpiDebug("output port id = %d, buffer id = %d, input id = %d, template = %p",
	    buffer->getPort()->getPortId(), buffer->getTid(), m_nextTid, temp);
#endif

  // Start producing, this may be asynchronous
  OCPI_EMIT_CAT__("Start Data Transfer",OCPI_EMIT_CAT_WORKER_DEV,OCPI_EMIT_CAT_WORKER_DEV_BUFFER_FLOW, buffer );
  temp.produce();
  insert_to_list(&buffer->getPendingTxList(), &temp, 64, 8);  // Add the template to our list
  return 0;
}

// This marks the input buffer as "Empty" and informs all interested outputs that
// the input is now available.
Buffer *Controller2::
consume(Buffer *input) {
  Buffer* buffer = static_cast<Buffer*>(input);

  // We need to mark the local buffer as free
  buffer->markBufferEmpty();

#ifdef DTI_PORT_COMPLETE
  buffer->setBusyFactor( buffer->getPort()->getCircuit()->getRelativeLoadFactor() );
#endif


#ifdef DEBUG_L2
  ocpiDebug("Set load factor to %d", buffer->getState()->pad);
  ocpiDebug("Consuming [0][0][%d][%d][0][1]",input->getPort()->getPortId(),input->getTid());
#endif

  // Tell everyone that we are empty
  return getTemplate(0, 0, input->getPort()->getPortId(), input->getTid(), false, INPUT).consume();
}

Buffer *Controller2::
getNextFullInputBuffer(Port *input_port) {
  // With this pattern, the data buffers are not deterministic, so we will always hand back
  // the buffer with the lowest sequence
  InputBuffer* buffer;
  InputBuffer *low_seq = NULL;

  for (unsigned n = 0; n < input_port->getBufferCount(); n++) {
    buffer = input_port->getInputBuffer(n);
    if (!buffer->isEmpty() && !buffer->inUse()) {
      if (low_seq) {
        if (buffer->getMetaData()->sequence < low_seq->getMetaData()->sequence)
          low_seq = buffer;
      } else
        low_seq = buffer;
    }
  }
  if (low_seq)
    low_seq->setInUse(true);

#ifdef DEBUG_L2
  if (!low_seq)
    ocpiDebug("No Input buffers avail");
#endif
  return low_seq;
}

} // namespace DataTransport
} // namespace OCPI
