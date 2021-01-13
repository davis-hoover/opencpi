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
#include "TransportPortSet.hh"
#include "OcpiBuffer.h"
#include "OcpiOutputBuffer.h"
#include "OcpiInputBuffer.h"
#include "TransportController.hh"

///
////  Transfer controller for pattern 1
///

namespace DDT = DtOsDataTypes;
namespace DT = DataTransfer;
namespace OCPI {
namespace DataTransport {

// Create transfers for output port for the pattern w[p] -> w[p]
void Controller1::
createOutputTransfers(Port &s_port) {
  // Since this is a whole output distribution, only port 0 of the output
  // set gets to do anything.
  if (s_port.getPortSet()->getDataDistribution()->getMetaData()->distType ==
      DataDistributionMetaData::parallel && s_port.getRank() != 0)
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

    // We need a transfer template to allow a transfer to each input buffer
    for (unsigned t_buffers = 0; t_buffers < n_t_buffers; t_buffers++) {
      // input buffer
      InputBuffer* t_buf = m_input.getPort(0)->getInputBuffer(t_buffers);
      unsigned t_tid = t_buf->getTid();

      // Create a template
      Transfer &temp = *new Transfer(1);

      // Add the template to the controller, for this pattern the output port
      // and the input ports remains constant
      ocpiDebug("output port id = %d, buffer id = %d, input id = %d, temp=%p\n",
		s_port.getPortId(), s_tid, t_tid, &temp);

      setTemplate(temp, s_port.getPortId(), s_tid, 0 ,t_tid, false, OUTPUT);
      /*
       *  This transfer is used to mark the local input shadow buffer as full
       */
      // We need to setup a transfer for each input port.
      ocpiDebug("Number of input ports = %d\n", n_t_ports);

      for (n = 0; n < n_t_ports; n++) {
        // Get the input port
        Port &t_port = *m_input.getPort(n);
        t_buf = t_port.getInputBuffer(t_buffers);

        struct PortMetaData::OutputPortBufferControlMap *output_offsets =
          &s_port.getMetaData()->m_bufferData[s_tid].outputOffsets;

        struct PortMetaData::InputPortBufferControlMap *input_offsets =
          &t_port.getMetaData()->m_bufferData[t_tid].inputOffsets;

        // We need to determine if this can be a Zero copy transfer.  If so,
        // we dont need to create a transfer template
        if (m_zcopyEnabled && s_port.supportsZeroCopy(&t_port)) {
          ocpiDebug("** ZERO COPY TransferTemplateGeneratorPattern1::createOutputTransfers from %p, to %p",
		    s_buf, t_buf);
          temp.addZeroCopyTransfer(s_buf, t_buf);
          continue;
        }

        // Create the transfer that copys the output data to the input data
	DT::XferRequest* ptransfer =
	  s_port.getTemplate(s_port.getEndPoint(), t_port.getEndPoint()).createXferRequest();
        try {
          ptransfer->copy(output_offsets->bufferOffset,
			  input_offsets->bufferOffset,
			  output_offsets->bufferSize,
			  DT::XferRequest::DataTransfer);

	  DtOsDataTypes::Offset	metaOffset =
	    output_offsets->metaDataOffset +
	    s_port.getPortId() * OCPI_SIZEOF(DDT::Offset, BufferMetaData);
	  uint32_t options = t_port.getMetaData()->m_descriptor.options;

	  if (!(options & (1 << FlagIsMeta)))
	    // Create the transfer that copys the output meta-data to the input meta-data
	    ptransfer->copy(metaOffset,
			    input_offsets->metaDataOffset +
			    s_port.getPortId() * OCPI_SIZEOF(DDT::Offset, BufferMetaData),
			    sizeof(OCPI::OS::int64_t),
			    DT::XferRequest::MetaDataTransfer);
	  // The flag transfer which could be three things
	  ptransfer->copy(// source offset, depends on mode
			  options & (1 << FlagIsCounting) ?
			  metaOffset + OCPI_OFFSETOF(DDT::Offset, RplMetaData, timestamp) :
			  options & (1 << FlagIsMeta) ?
			  metaOffset + OCPI_OFFSETOF(DDT::Offset, RplMetaData, xferMetaData) :
			  output_offsets->localStateOffset +
			  OCPI_SIZEOF(DDT::Offset, BufferState) * MAX_PCONTRIBS +
			  s_port.getPortId() * OCPI_SIZEOF(DDT::Offset, BufferState),
			  // destination offset
			  input_offsets->localStateOffset +
			  s_port.getPortId() * OCPI_SIZEOF(DDT::Offset, BufferState),
			  sizeof(BufferState),
			  DT::XferRequest::FlagTransfer);
        } catch( ... ) {
          FORMAT_TRANSFER_EC_RETHROW(&s_port, &t_port);
        }
        // Add the transfer 
        temp.addTransfer(ptransfer);
      } // end for each input buffer
    } // end for each output buffer
  }  // end for each input port
}

bool Controller1::
canProduce(Buffer *buffer) {
  // When s DD = whole only port 0 of the output port set can produce
  if ( m_isWholeOutputSet && buffer->getPort()->getRank() != 0)
    return true;

  // Broadcast is a special case
  if (buffer->getMetaData()->endOfStream)
    return canBroadcast(buffer);

  bool l_produce = false;

  // We will go to each of our shadows and figure out if they are empty

#ifdef RANDOM_INPUTS
  // With this pattern, we sequence the output buffers to ensure that the input always
  // has the next buffer of data in one of its buffers, but we dont have to worry about 
  // sequencing through its buffers in order because the inputs have the logic needed
  // to re-sequence there own buffers

  for (unsigned p = 0; p < m_input.getBufferCount(); p++) {
    for (unsigned n = 0; n < m_input.getPortCount(); n++ ) {
      Port *port = m_input.getPort(n);
      if (port->getBuffer(p)->isEmpty())
        l_produce = true;
      else {
        l_produce = false;
        break;
      }
    }
    // All inputs have a free buffer
    if (l_produce) {
      m_nextTid = p;
      break;
    }
  }
#else
  // We treat the input buffers as a circular queue, so we only need to check
  // the next buffer 
  for (PortOrdinal n = 0; n < m_input.getPortCount(); n++) {
    Port *port = m_input.getPort(n);
    if (port->getBuffer(m_nextTid)->isEmpty())
      l_produce = true;
    else {
      l_produce = false;
      break;
    }
  }
#endif
  return l_produce;
}

unsigned Controller1::
produce(Buffer* b, bool bcast) {
  Buffer* buffer = static_cast<Buffer*>(b);

  if (bcast) {
#ifdef DEBUG_L2
    ocpiDebug("*** producing via broadcast, rank == %d !!", b->getPort()->getRank());
#endif
    if (!buffer->getMetaData()->endOfStream)
      ocpiDebug("*** ERROR *** EOS not set via broadcast !!");
  }
  // With this pattern, only port 0 of the output port set can produce
  if (m_isWholeOutputSet && b->getPort()->getRank() != 0) {
#ifdef DEBUG_L2
    ocpiDebug("My rank != 0 so i am not producing !!!");
#endif
    // We need to mark the local buffer as free
    buffer->markBufferEmpty();
    // Next input buffer 
    m_nextTid = (m_nextTid + 1) % m_input.getBufferCount();
    //#define DELAY_FOR_TEST
#ifdef DELAY_FOR_TEST
    Sleep( 500 );
#endif
    return 0;
  }

  // Broadcast if requested
  if (bcast) {
    broadCastOutput(buffer);
    return 0;
  }

  // We need to mark the buffer as full
  buffer->markBufferFull();

  for (PortOrdinal n = 0; n < m_input.getPortCount(); n++) {
    Buffer* tbuf = static_cast<Buffer*>(m_input.getPort(n)->getBuffer(m_nextTid) );
    tbuf->markBufferFull();
  }
  /*
   *  For this pattern the output port and input port are constants when we look
   *  up the template that we need to produce.  So, since the output tid is a given,
   *  the only calculation is the input tid that we are going to produce to.
   */

  // Start producing, this may be asynchronous
  auto &temp =
    getTemplate(buffer->getPort()->getPortId(), buffer->getTid(), 0, m_nextTid, bcast, OUTPUT);
#ifdef DEBUG_L2
  ocpiDebug("output port id = %d, buffer id = %d, input id = %d, template = %p",
	    buffer->getPort()->getPortId(), buffer->getTid(), m_nextTid, temp);
#endif

  OCPI_EMIT_CAT__("Start Data Transfer",OCPI_EMIT_CAT_WORKER_DEV,OCPI_EMIT_CAT_WORKER_DEV_BUFFER_FLOW, buffer );
  temp.produce();
  insert_to_list(&buffer->getPendingTxList(), &temp, 64, 8); // Add the template to our list
  // Next input buffer
  m_nextTid = (m_nextTid + 1) % m_input.getBufferCount();

#ifdef DEBUG_L2
  ocpiDebug("next tid = %d, num buf = %d", m_nextTid, m_input.getBufferCount());
  ocpiDebug("Returning max gated sequence = %d", temp.getMaxGatedSequence());
#endif
  return temp.getMaxGatedSequence();
}

// This marks the input buffer as "Empty" and informs all interested outputs that
Buffer *Controller1::
consume(Buffer *input) {
  Buffer* buffer = static_cast<Buffer*>(input);

  // We need to mark the local buffer as free
  buffer->markBufferEmpty();

#ifdef DTI_PORT_COMPLETE
  buffer->setBusyFactor(buffer->getPort()->getCircuit()->getRelativeLoadFactor());
#endif

  auto &temp = getTemplate(0, 0, input->getPort()->getPortId(), input->getTid(), false, INPUT);

#ifdef DEBUG_L2
  ocpiDebug("Set load factor to %d", buffer->getState()->pad);
  ocpiDebug("Consuming using tpid = %d, ttid = %d, template = 0x%x",input->getPort()->getPortId(),
	    input->getTid(), temp);
#endif
  // Tell everyone that we are empty
  return temp.consume();
}

} // namespace DataTransport
} // namespace OCPI

