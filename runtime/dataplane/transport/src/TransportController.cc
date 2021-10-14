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
#include "OsAssert.hh"
#include "OcpiTimeEmitCategories.h"
#include "OcpiCircuit.h"
#include "TransportPortSet.hh"
#include "OcpiBuffer.h"
#include "OcpiOutputBuffer.h"
#include "OcpiInputBuffer.h"
#include "OcpiTransport.h"
#include "TransportController.hh"

namespace DT = DataTransfer;
namespace DDT = DtOsDataTypes;
namespace OCPI {
namespace DataTransport {

Controller &
controllerNotSupported(PortSet &/*output*/, PortSet &/*input*/) {
  ocpiAssert("Unsupported data transfer request rejected !!\n"==0);
  throw OCPI::Util::EmbeddedException("Unsupported data transfer request rejected !!\n");
}

Controller::
Controller(PortSet &output, PortSet &input)
  :  m_EmptyQPtr(0), m_output(output), m_input(input), m_nextTid(0), m_zcopyEnabled(true) {
  // For convenience
  m_isWholeOutputSet =
    output.getDataDistribution()->getMetaData()->distType == DataDistributionMetaData::parallel;

  unsigned
    inSize = input.getPortCount(),
    outSize = output.getPortCount(),
    in2outSize = inSize * outSize,
    inBuffers = input.getBufferCount(),
    outBuffers = output.getBufferCount(),
    in2outBuffers = inBuffers * outBuffers;
  m_inPort2outPort.resize(in2outSize);
  for (unsigned n = 0; n < in2outSize; ++n) {
    m_inPort2outPort[n].m_outputTransfers.resize(in2outBuffers);
    m_inPort2outPort[n].m_outputBroadcastTransfers.resize(in2outBuffers); // can this be conditional?
    m_inPort2outPort[n].m_inputTransfers.resize(in2outBuffers);
    m_inPort2outPort[n].m_inputBroadcastTransfers.resize(in2outBuffers); // can this be conditional?
  }
}

/**********************************
 * Destructor
 *********************************/
Controller::~Controller()
{
  for (unsigned p = 0; p < m_inPort2outPort.size(); ++p) {
    auto &io = m_inPort2outPort[p];
    for (unsigned b = 0; b < io.m_outputTransfers.size(); ++b) {
      delete  io.m_outputTransfers[b];
      delete  io.m_outputBroadcastTransfers[b];
      delete  io.m_inputTransfers[b];
      delete  io.m_inputBroadcastTransfers[b];
    }
  }
}

// After construction (of derived classes) this finishes the initialization
void Controller::
init() {
  bool generated = false;
  (void)generated;

  // We need to create transfers for every output and destination port
  // the exists in the context of this Transport (container)
  for (PortOrdinal s_n = 0; s_n < m_output.getPortCount(); s_n++) {
    Port &s_port = *m_output.getPort(s_n);
    if (s_port.isShadow())
      continue;
    ocpiDebug("s port endpoints = %s, %s, %s",
           s_port.getRealShemServices()->endPoint().name().c_str(),
           s_port.getShadowShemServices()->endPoint().name().c_str(),
           s_port.getLocalShemServices()->endPoint().name().c_str() );
    createOutputTransfers(s_port);
    //    createOutputBroadcastTemplates(s_port);
    generated = true;
  }

  for (PortOrdinal t_n = 0; t_n < m_input.getPortCount(); t_n++) {
    Port &t_port = *m_input.getPort(t_n);
    ocpiDebug("t port endpoints = %s, %s, %s",
	      t_port.getRealShemServices()->endPoint().name().c_str(),
	      t_port.getShadowShemServices()->endPoint().name().c_str(),
	      t_port.getLocalShemServices()->endPoint().name().c_str() );
    // If the output port is not local, but the transfer role requires us to move data,
    // we need to create transfers for the remote port
    if (!m_input.getCircuit()->getTransport().isLocalEndpoint(t_port.getRealShemServices()->endPoint()))
      break;
    createInputTransfers(t_port);
    //createInputBroadcastTemplates(t_port);
    generated = true;
  }
  ocpiAssert(generated);
  m_input.setTxController(this);
  m_output.setTxController(this);
}

// Create the input broadcast template for this port
void Controller::
createInputBroadcastTemplates(Port &input) {
  // We need to create the transfers to tell all of our shadow ports that a buffer
  // became available
  BufferOrdinal n_t_buffers = input.getBufferCount();

  // We need a transfer template to allow a transfer for each input buffer to its
  // associated shadows
  for (BufferOrdinal t_buffers = 0; t_buffers < n_t_buffers; t_buffers++) {
    // input buffer
    InputBuffer *t_buf = static_cast<InputBuffer*>(input.getBuffer(t_buffers));
    unsigned t_tid = t_buf->getTid();

    // Create a template
    Transfer &temp = *new Transfer(0);

    //Add the template to the controller
    ocpiDebug("*&*&* Adding template for tpid = %d, ttid = %u, template = %p",
	      input.getPortId(), t_tid, &temp);

    setTemplate(temp, 0, 0, input.getPortId(), t_tid, true, INPUT);

    struct PortMetaData::InputPortBufferControlMap *input_offsets =
      &input.getMetaData()->m_bufferData[t_tid].inputOffsets;

    // We need to setup a transfer for each shadow, they exist in the unique output circuits
    for (PortOrdinal n = 0; n < m_output.getPortCount(); n++) {

      // Since the shadows only exist in the circuits with instances of real
      // output ports, the offsets are indexed via the output port ordinals.
      // If the output is co-located with us, no shadow exists.
      Port &s_port = *m_output.getPort(n);
      unsigned s_pid = s_port.getMailbox();

      // We dont need to do anything for co-location
      if (m_zcopyEnabled && s_port.supportsZeroCopy(&input)) {
        temp.addZeroCopyTransfer(NULL, t_buf);
	continue;
      }

      ocpiDebug("CreateInputBroadcastTransfers: localStateOffset 0x%llx", 
		(long long)input_offsets->localStateOffset);
      ocpiDebug("CreateInputBroadcastTransfers: RemoteStateOffsets %p",
		input_offsets->myShadowsRemoteStateOffsets);
      ocpiDebug("CreateInputBroadcastTransfers: s_pid %d", s_pid);

      // Create the copy in the template
      DT::XferRequest* ptransfer =
	input.getTemplate(input.getEndPoint(), s_port.getEndPoint()).createXferRequest();
      try { // FIXME:  what normal exceptions could possible happen that we would want to catch here?
        ptransfer->copy(input_offsets->localStateOffset,
			input_offsets->myShadowsRemoteStateOffsets[s_pid],
			sizeof(BufferState),
			DT::XferRequest::DataTransfer);
      } catch ( ... ) {
        FORMAT_TRANSFER_EC_RETHROW(&input, &s_port);
      }
      // Add the transfer to the template
      temp.addTransfer(ptransfer);
    } // end for each input buffer
  } // end for each output port
}

void Controller::
createOutputBroadcastTemplates(Port &s_port) {
  unsigned n,
    n_s_buffers = m_output.getBufferCount(),
    n_t_buffers = m_input.getBufferCount(),
    n_t_ports = m_input.getPortCount();

  // We need a transfer template to allow a transfer from each output buffer to every
  // input buffer for this pattern.
  for (unsigned s_buffers = 0; s_buffers < n_s_buffers; s_buffers++) {

    // output buffer
    OutputBuffer* s_buf = static_cast<OutputBuffer*>(s_port.getOutputBuffer(s_buffers));
    unsigned s_tid = s_buf->getTid();
    unsigned t_tid;

    // We need a transfer template to allow a transfer to each input buffer
    for (unsigned t_buffers = 0; t_buffers < n_t_buffers; t_buffers++) {

      // input buffer
      InputBuffer* t_buf = static_cast<InputBuffer*>(m_input.getPort(0)->getInputBuffer(t_buffers));
      t_tid = t_buf->getTid();

      // Create a template
      Transfer &temp = *new Transfer(0);

      // Add the template to the controller, for this pattern the output port
      // and the input ports remains constant

      ocpiDebug("output port id = %d, buffer id = %d, input id = %d",
		s_port.getPortId(), s_tid, t_tid );
      ocpiDebug("Template address = %p", &temp);

      setTemplate(temp, s_port.getPortId(), s_tid, 0, t_tid, true, OUTPUT);

      // This transfer is used to mark the local input shadow buffer as full

      struct PortMetaData::OutputPortBufferControlMap *output_offsets =
        &s_port.getMetaData()->m_bufferData[s_tid].outputOffsets;

      // We need to setup a transfer for each input port. 
      ocpiDebug("Number of input ports = %d", n_t_ports);
      for ( n=0; n < n_t_ports; n++) {

        // Get the input port
        Port  &t_port = *m_input.getPort(n);
        t_buf = static_cast<InputBuffer*>(t_port.getBuffer(t_buffers));

        struct PortMetaData::InputPortBufferControlMap *input_offsets = 
          &t_port.getMetaData()->m_bufferData[t_tid].inputOffsets;

        // We need to determine if this can be a Zero copy transfer.  If so, 
        // we dont need to create a transfer template
        if (m_zcopyEnabled && s_port.supportsZeroCopy(&t_port)) {

          ocpiDebug("** ZERO COPY TransferTemplateGenerator::createOutputBroadcastTemplates from %p, to %p",
		    s_buf, t_buf);
          temp.addZeroCopyTransfer(s_buf, t_buf);
          continue;
        }
	DT::XferRequest* ptransfer =
	  s_port.getTemplate(s_port.getEndPoint(), t_port.getEndPoint()).createXferRequest();
        try {
	  ptransfer->copy(output_offsets->bufferOffset,
			  input_offsets->bufferOffset,
			  output_offsets->bufferSize,
			  DT::XferRequest::DataTransfer);
          // Create the transfer that copys the output meta-data to the input meta-data
	  ptransfer->copy(output_offsets->metaDataOffset + s_port.getPortId() * OCPI_SIZEOF(DDT::Offset, BufferMetaData),
			   input_offsets->metaDataOffset + s_port.getPortId() * OCPI_SIZEOF(DDT::Offset, BufferMetaData),
			   sizeof(int64_t),
			  DT::XferRequest::MetaDataTransfer );

          // Create the transfer that copys the output state to the remote input state
          ptransfer->copy(output_offsets->localStateOffset + s_port.getPortId() * OCPI_SIZEOF(DDT::Offset, BufferState),
			  input_offsets->localStateOffset + s_port.getPortId() * OCPI_SIZEOF(DDT::Offset, BufferState),
			  sizeof(BufferState),
			  DT::XferRequest::FlagTransfer);
        } catch ( ... ) {
          FORMAT_TRANSFER_EC_RETHROW(&s_port, &t_port);
        }
        // Add the transfer
        temp.addTransfer(ptransfer);

      } // end for each input buffer

      // And now to all other outputs

      // A output braodcast must also send to all other outputs to update them as well
      // Now we need to pass the output control baton onto the next output port
      DT::XferRequest* ptransfer2 = NULL;
      for (PortOrdinal ns = 0; ns < s_port.getPortSet()->getPortCount(); ns++) {
        Port &next_sp =
          *static_cast<Port*>(s_port.getPortSet()->getPortFromIndex(ns));
        if (&next_sp == &s_port)
          continue;

        struct PortMetaData::OutputPortBufferControlMap *next_output_offsets =
          &next_sp.getMetaData()->m_bufferData[s_tid].outputOffsets;
	ptransfer2 =
	  s_port.getTemplate(s_port.getEndPoint(), next_sp.getEndPoint()).createXferRequest();
        // Create the transfer from out output contol state to the next
        try {
          ptransfer2->copy (output_offsets->portSetControlOffset,
			    next_output_offsets->portSetControlOffset,
			    sizeof(OutputPortSetControl),
			    DT::XferRequest::FlagTransfer);
	} catch( ... ) {
	  FORMAT_TRANSFER_EC_RETHROW(&s_port, &next_sp);
	}
      }

      // Add the transfer 
      if (ptransfer2)
	temp.addTransfer(ptransfer2);
    } // end for each output buffer
  }  // end for each input port
}

// This base class method provides a default pattern for the input buffers which is to
// braodcast an input buffers availability to all shadows
void Controller::
createInputTransfers(Port &input) {
  // We need to create the transfers to tell all of our shadow ports that a buffer
  // became available
  size_t n_t_buffers = input.getBufferCount();

  // We need a transfer template to allow a transfer for each input buffer to its
  // associated shadows
  for (size_t t_buffers=0; t_buffers < n_t_buffers; t_buffers++) {

    // input buffer
    InputBuffer* t_buf = input.getInputBuffer(t_buffers);
    unsigned t_tid = t_buf->getTid();

    // Create a template
    Transfer &temp = *new Transfer(0);

    ocpiDebug("*&*&* Adding template for tpid = %d, ttid = %d, template = %p",
	      input.getPortId(), t_tid, &temp);

    // Add the template to the controller
    setTemplate(temp, 0, 0, input.getPortId(), t_tid, false, INPUT);

    struct PortMetaData::InputPortBufferControlMap *input_offsets =
      &input.getMetaData()->m_bufferData[t_tid].inputOffsets;

    // Since there may be multiple output ports on 1 processs, we need to make sure we dont send
    // more than 1 time
    int sent[MAX_PCONTRIBS];
    memset(sent,0,sizeof(int)*MAX_PCONTRIBS);

    // We need to setup a transfer for each shadow, they exist in the unique output circuits
    for (PortOrdinal n = 0; n < m_output.getPortCount(); n++) {
      // Since the shadows only exist in the circuits with instances of real
      // output ports, the offsets are indexed via the output port ordinals.
      // If the output is co-located with us, no shadow exists.
      Port &s_port = *m_output.getPort(n);
      unsigned s_pid = s_port.getRealShemServices()->endPoint().mailBox();

      if (sent[s_pid])
        continue;

      // If we are creating a template for whole transfers, we do not recognize anything
      // but output port 0
      if ( (s_port.getPortSet()->getDataDistribution()->getMetaData()->distType ==
	    DataDistributionMetaData::parallel) &&
           s_port.getRank() != 0)
        continue;

      // Attach zero-copy for co-location
      if (m_zcopyEnabled && s_port.supportsZeroCopy(&input)) {
        ocpiDebug("Adding Zery copy for input response");
        temp.addZeroCopyTransfer(NULL, t_buf);
	continue;
      }
      sent[s_pid] = 1;
      DT::XferRequest *ptransfer =
	input.getTemplate(input.getEndPoint(), s_port.getEndPoint()).createXferRequest();
      try {
        // Create the copy in the template
        ptransfer->copy(input_offsets->localStateOffset +
			(OCPI_SIZEOF(DDT::Offset, BufferState) * MAX_PCONTRIBS) +
			(OCPI_SIZEOF(DDT::Offset, BufferState)* input.getPortId()),
			input_offsets->myShadowsRemoteStateOffsets[s_pid],
			sizeof(BufferState),
			DT::XferRequest::FlagTransfer);
      } catch( ... ) {
        FORMAT_TRANSFER_EC_RETHROW(&input, &s_port);
      }
      // Add the transfer to the template
      temp.addTransfer(ptransfer);
    } // end for each input buffer
  } // end for each output port
}

//================================================================================
// Runtime methods
bool Controller::
hasEmptyOutputBuffer(Port *src_port) const {
  BufferOrdinal &n = src_port->getLastBufferTidProcessed();
  OutputBuffer* buffer =  src_port->getOutputBuffer(n);
  return buffer->isEmpty() && !buffer->inUse();
}

bool Controller::
hasFullInputBuffer(Port *input_port, InputBuffer** retb) const {
  InputBuffer* buffer;
  BufferOrdinal
    &lo = input_port->getLastBufferOrd(),
    tlo = ((lo+1)%input_port->getBufferCount());
  *retb = buffer = input_port->getInputBuffer(tlo);
  return !buffer->isEmpty() && !buffer->inUse();
}

#if 0
void Controller::
bufferFull(Port *port) {
  // We treat the input buffers as a circular queue, so we only need to check
  // the next buffer
  port->getBuffer(m_FillQPtr)->markBufferFull();
  m_FillQPtr++ ;
  if (m_FillQPtr >= port->getBufferCount())
    m_FillQPtr = 0;
}
#endif

void Controller::
freeBuffer(Port *port) {
  // We treat the input buffers as a circular queue, so we only need to check
  // the next buffer 
  port->getBuffer(m_EmptyQPtr)->markBufferEmpty();
  m_EmptyQPtr++;
  if (m_EmptyQPtr >= port->getBufferCount())
    m_EmptyQPtr = 0;
}

Buffer *Controller::
getNextEmptyOutputBuffer(OCPI::DataTransport::Port* src_port) {
  // This default implementation simply finds the first available output buffer
  OutputBuffer* boi=NULL;
  BufferOrdinal &n = src_port->getLastBufferTidProcessed();
  OutputBuffer* buffer = src_port->getOutputBuffer(n);
  if (buffer->isEmpty() && ! buffer->inUse())
    boi = buffer;
  if (boi) {
    boi->setInUse( true );
    n = (n+1) % src_port->getBufferCount();
  }
  return boi;
}

Buffer *Controller::
getNextFullInputBuffer(OCPI::DataTransport::Port* input_port) {

#ifdef SEQ_RETURN
  // This default implementation simply makes sure that each output buffer
  // gets processed in sequence.

  DataDistributionMetaData::DistributionType d_type = 
    input_port->getCircuit()->getConnection()->getDataDistribution()->getMetaData()->distType;

  InputBuffer** buffers = input_port->getInputBuffers();
  InputBuffer* boi=NULL;

  int &seq = input_port->getLastBufferTidProcessed();

  ocpiDebug("getNextFullInputBuffer, last seq processed = %d", seq );

  InputBuffer *low_seq = NULL;
  int full_count=0;
  for (unsigned n=0; n<input_port->getBufferCount(); n++) {
    if (!buffers[n]->isEmpty() && !buffers[n]->inUse()) {
      full_count++;

      // If we have a parellel distribution on the connection, all of the buffers need 
      // to be in order
      if (d_type == DataDistributionMetaData::sequential) {
        unsigned inc = input_port->getCircuit()->getInputPortSetCount();
        if (seq == 0) {
          seq = buffers[n]->getMetaData()->sequence;
          boi = buffers[n];
          seq += inc;
          break;
        } else if (buffers[n]->getMetaData()->sequence == seq) {
          boi = buffers[n];
          seq += inc;
          break;
        } else if ( buffers[n]->getMetaData()->broadCast == 1 ) {   
	  // A broadcast may be out of sequence
          boi = buffers[n];
          seq += inc;
          break;
        }
      } else if (buffers[n]->getMetaData()->sequence == seq) {
        boi = buffers[n];
        seq++;
        break;
      }
    }
  }
  if (boi)
    boi->setInUse( true );
  // Check for programming error
  if ( (full_count == input_port->getBufferCount()) && ! boi ) {
    ocpiDebug("*** INTERNAL ERROR ***, got a full set of input buffers, but cant find expected sequence");
    ocpiAssert(0);
  }
  return boi;
#else

#define SIMPLE_AND_FAST
#ifdef SIMPLE_AND_FAST

  InputBuffer* buffer = NULL;
  BufferOrdinal
    &lo = input_port->getLastBufferOrd(),
    tlo = ((lo+1)%input_port->getBufferCount());
  buffer = input_port->getInputBuffer(tlo);
  if (!buffer->isEmpty() && ! buffer->inUse()) {
    lo = tlo;
    buffer->setInUse(true);
    return buffer;
  }
  return NULL;
#else
  // With this pattern, the data buffers are not deterministic, so we will always hand back
  // the buffer with the lowest sequence
  InputBuffer *buffer;
  InputBuffer *low_seq = NULL;

  for (unsigned n = 0; n<input_port->getBufferCount(); n++) {
    buffer = input_port->getInputBuffer(n);
    if (!buffer->isEmpty() && !buffer->inUse()) {
      if (low_seq) {
        if (buffer->getMetaData()->sequence < low_seq->getMetaData()->sequence) {
          low_seq = buffer;
        } else if ((buffer->getMetaData()->sequence == low_seq->getMetaData()->sequence) &&
		   (buffer->getMetaData()->partsSequence < low_seq->getMetaData()->partsSequence) ) {
          low_seq = buffer;
        }
      } else
        low_seq = buffer;
    }
  }
  if (low_seq)
    low_seq->setInUse(true);
  if (!low_seq)
    ocpiDebug("No Input buffers avail");
  return low_seq;
#endif
#endif
}

bool Controller::
canBroadcast(Buffer *buffer) {
  // When s DD = whole only port 0 of the output port set can produce
  if (m_isWholeOutputSet && buffer->getPort()->getRank() != 0)
    return true;
  bool l_produce = false;

  // We will go to each of our shadows and figure out if they are empty
  // With this pattern, we sequence the output buffers to ensure that the input always
  // has the next buffer of data in one of its buffers, but we dont have to worry about 
  // sequencing through its buffers in order because the inputs have the logic needed
  // to re-sequence there own buffers

  for (unsigned p = 0; p < m_input.getBufferCount(); p++) {
    for (PortOrdinal n = 0; n < m_input.getPortCount(); n++) {
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
  return l_produce;
}

void Controller::
broadCastOutput(Buffer *b) {
  OutputBuffer *buffer = static_cast<OutputBuffer*>(b);

  ocpiDebug("TransferController::broadCastOutput( Buffer* b ), setting EOS !!");

  // In the case of a braodcast, we will copy some of the buffers meta-data
  // attributes to the output control structure
  buffer->getControlBlock()->endOfStream = buffer->getMetaData()->endOfStream;
  buffer->getControlBlock()->endOfWhole = buffer->getMetaData()->endOfWhole;

  // We need to mark the buffer as full
  buffer->markBufferFull();

  for (PortOrdinal n = 0; n < m_input.getPortCount(); n++) {
    Buffer* tbuf = static_cast<Buffer*>(m_input.getPort(n)->getBuffer(m_nextTid));
    tbuf->markBufferFull();
  }
  /*
   *  For this pattern the output port and input port are constants when we look
   *  up the template that we need to produce.  So, since the output tid is a given,
   *  the only calculation is the input tid that we are going to produce to.
   */
  // auto temp = m_templates[buffer->getPort()->getPortId()][buffer->getTid()][0][m_nextTid][1][OUTPUT];
  auto &temp = getTemplate(buffer->getPort()->getPortId(), buffer->getTid(), 0, m_nextTid, true, OUTPUT);
  ocpiDebug("output port id = %d, buffer id = %d, input id = %d, template = %p",
	    buffer->getPort()->getPortId(), buffer->getTid(), m_nextTid, &temp);

  // Start producing, this may be asynchronous
  OCPI_EMIT_CAT__("Start Data Transfer",OCPI_EMIT_CAT_WORKER_DEV,OCPI_EMIT_CAT_WORKER_DEV_BUFFER_FLOW, buffer );
  temp.produce();
  insert_to_list(&buffer->getPendingTxList(), &temp, 64, 8);  // Add the template to our list
}

void Controller::
modifyOutputOffsets(Buffer *me, Buffer *new_buffer, bool reverse) {
  auto &temp = getTemplate(me->getPort()->getPortId(), me->getTid(), 0, m_nextTid, false, OUTPUT);
  // If this is already a zero copy from output to the next input we need to deal with that
  if (temp.m_zCopy) {
    Buffer *cme =  static_cast<Buffer*>(me);
    Buffer *cnew_buffer =  static_cast<Buffer*>(new_buffer);
    if (! reverse)
      cme->attachZeroCopy( cnew_buffer );
    else
      cme->detachZeroCopy();
  } else {
    // Note: this needs to me augmented for DRI
    DtOsDataTypes::Offset new_offsets[2];
    new_offsets[1] = 0;
    DtOsDataTypes::Offset old_offsets[2];
    Buffer* nb;
    Buffer *cnew_buffer =  static_cast<Buffer*>(new_buffer);
    if (cnew_buffer->m_zeroCopyFromBuffer)
      nb = cnew_buffer->m_zeroCopyFromBuffer;
    else
      nb = cnew_buffer;
    if (!reverse) {
      new_offsets[0] = nb->m_startOffset;
      temp.modify( new_offsets, old_offsets);
    } else {
      new_offsets[0] = me->m_startOffset;
      temp.modify( new_offsets, old_offsets);
    }
  }
}

void Controller::
freeAllBuffersLocal(Port *port) {
  ocpiAssert(!port->isOutput());
  m_EmptyQPtr = 0;
  for (unsigned int n = 0; n < port->getBufferCount(); n++)
    port->getBuffer(n)->markBufferEmpty();
}

void Controller::
consumeAllBuffersLocal(Port *port) {
  ocpiAssert( port->isOutput() );
  for (unsigned int n = 0; n < port->getBufferCount(); n++)
    port->getBuffer(n)->markBufferEmpty();
}

} // namespace DataTransport
} // namespace OCPI
