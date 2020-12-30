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
#include "OcpiCircuit.h"
#include "OcpiPortSet.h"
#include "OcpiBuffer.h"
#include "OcpiOutputBuffer.h"
#include "OcpiInputBuffer.h"
#include "DtHandshakeControl.h"
#include "OcpiIntDataDistribution.h"
#include "TransportController.hh"

///
////  ActiveFlowControle Transfer controller for pattern 1 
///

namespace DDT = DtOsDataTypes;
namespace DT = DataTransfer;
namespace OCPI {
namespace DataTransport {

// Create transfers for a output port that has a ActiveFlowControl role.  This means that the 
// the only transfer that takes place is the "flag" transfer.  It is the responibility of the 
// remote "pull" port to tell us when our output buffer becomes free.
void Controller1AFC::
createOutputTransfers(Port &s_port) {
  // Since this is a whole output distribution, only port 0 of the output
  // set gets to do anything.
  if (s_port.getPortSet()->getDataDistribution()->getMetaData()->distType ==
      DataDistributionMetaData::parallel &&
       s_port.getRank() != 0)
    return;
  unsigned n_s_buffers = m_output.getBufferCount();
  unsigned n_t_buffers = m_input.getBufferCount();
  PortOrdinal n_t_ports = m_input.getPortCount();

  // We need a transfer template to allow a transfer from each output buffer to every
  // input buffer for this pattern.
  for (unsigned s_buffers = 0; s_buffers < n_s_buffers; s_buffers++) {
    // output buffer
    OutputBuffer* s_buf = s_port.getOutputBuffer(s_buffers);
    s_buf->setSlave();
    unsigned s_tid = s_buf->getTid();

    // We need a transfer template to allow a transfer to each input buffer
    for (unsigned t_buffers = 0; t_buffers < n_t_buffers; t_buffers++) {
      // input buffer
      InputBuffer* t_buf = m_input.getPort(0)->getInputBuffer(t_buffers);
      unsigned t_tid = t_buf->getTid();

      // Create a template
      // Transfer *temp = new TransferAFC(1);
      Transfer &temp = *new Transfer(1);


      // Add the template to the controller, for this pattern the output port
      // and the input ports remains constant
      ocpiDebug("output port id = %d, buffer id = %d, input id = %d", 
		s_port.getPortId(), s_tid, t_tid);
      ocpiDebug("Template address = %p", &temp);

      setTemplate(temp, s_port.getPortId(), s_tid, 0 ,t_tid, false, OUTPUT);

      // We need to setup a transfer for each input port. 
      ocpiDebug("Number of input ports = %d", n_t_ports);

      for (PortOrdinal n = 0; n < n_t_ports; n++) {
        // Get the input port
        Port &t_port = *m_input.getPort(n);
        t_buf = t_port.getInputBuffer(t_buffers);

        struct PortMetaData::OutputPortBufferControlMap *output_offsets =
          &s_port.getMetaData()->m_bufferData[s_tid].outputOffsets;

        struct PortMetaData::InputPortBufferControlMap *input_offsets =
          &t_port.getMetaData()->m_bufferData[t_tid].inputOffsets;

        // We need to determine if this can be a Zero copy transfer.  If so,
        // we dont need to create a transfer template
        if ( m_zcopyEnabled && s_port.supportsZeroCopy(&t_port)) {
          ocpiDebug("** ZERO COPY TransferTemplateGeneratorPattern1AFC::createOutputTransfers from %p, to %p",
		    s_buf, t_buf);
          temp.addZeroCopyTransfer(s_buf, t_buf);
          continue;
        }

        // Create the transfer that copys the output data to the input data
	DT::XferRequest* ptransfer =
	  s_port.getTemplate(s_port.getEndPoint(), t_port.getEndPoint()).createXferRequest();
        // Note that in the ActiveFlowControl mode we only send the state to indicate that our
        // buffer is ready for the remote actor to pull data.
        try {
	  ptransfer->copy(t_port.getMetaData()->m_descriptor.options & (1 << FlagIsMeta) ?
			  output_offsets->metaDataOffset +
			  s_port.getPortId() * OCPI_SIZEOF(DDT::Offset, BufferMetaData) +
			  OCPI_OFFSETOF(DDT::Offset, RplMetaData, xferMetaData) :
			  output_offsets->localStateOffset +
			  s_port.getPortId() * OCPI_SIZEOF(DDT::Offset, BufferState),
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

// This base class provides a default pattern for the input buffers which is to
// broadcast a input buffers availability to all shadows
void Controller1AFC::
createInputTransfers(Port &input) {
  // We need to create the transfers to tell all of our shadow ports that a buffer
  // became available,
  BufferOrdinal n_t_buffers = input.getBufferCount();

  // We need a transfer template to allow a transfer for each input buffer to its
  // associated shadows
  for (BufferOrdinal t_buffers = 0; t_buffers < n_t_buffers; t_buffers++) {
    // input buffer
    InputBuffer* t_buf = input.getInputBuffer(t_buffers);
    unsigned t_tid = t_buf->getTid();

    // Create a template
    // Transfer* temp = new TransferAFC(0);
    Transfer &temp = *new Transfer(0);

    ocpiDebug("*&*&* Adding template for tpid = %d, ttid = %d, template = %p",
	      input.getPortId(), t_tid, &temp);

    //Add the template to the controller
    setTemplate(temp, 0, 0, input.getPortId(), t_tid, false, INPUT);
 
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
      if ((s_port.getPortSet()->getDataDistribution()->getMetaData()->distType ==
	   DataDistributionMetaData::parallel) &&
           s_port.getRank() != 0)
        continue;

      // Attach zero-copy for co-location
      if (m_zcopyEnabled && s_port.supportsZeroCopy(&input)) {
        ocpiDebug("Adding Zery copy for input response");
        temp.addZeroCopyTransfer(NULL, t_buf);
      }
      sent[s_pid] = 1;
    } // end for each input buffer
  } // end for each output port
}

// In AFC mode, the shadow port is responsible for pulling the data from the real output port, and then
// Telling the output port that its buffer is empty.
void Controller1AFCShadow::
createOutputTransfers(Port &s_port) {
  ocpiAssert("pattern1AFCshadow output"==0);

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

    // We need a transfer template to allow a transfer to each input buffer
    for (unsigned t_buffers = 0; t_buffers < n_t_buffers; t_buffers++) {
      // input buffer
      InputBuffer* t_buf = m_input.getPort(0)->getInputBuffer(t_buffers);
      unsigned t_tid = t_buf->getTid();

      // Create a template
      Transfer &temp = *new Transfer(1);

      // Add the template to the controller, for this pattern the output port
      // and the input ports remains constant
      ocpiDebug("output port id = %d, buffer id = %d, input id = %d", 
		s_port.getPortId(), s_tid, t_tid);
      ocpiDebug("Template address = %p", &temp);

      setTemplate(temp, s_port.getPortId(), s_tid, 0 ,t_tid, false, OUTPUT);
      /*
       *  This transfer is used to mark the local input shadow buffer as full
       */
      // We need to setup a transfer for each input port. 
      ocpiDebug("Number of input ports = %d", n_t_ports);

      for (n = 0; n < n_t_ports; n++) {
        // Get the input port
        Port& t_port = *m_input.getPort(n);
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
	DT::XferRequest *ptransfer =
	  s_port.getTemplate(s_port.getEndPoint(), t_port.getEndPoint()).createXferRequest();
        try {
          // Create the data buffer transfer
          ptransfer->copy (output_offsets->bufferOffset,
			   input_offsets->bufferOffset,
			   output_offsets->bufferSize,
			   DT::XferRequest::DataTransfer);

          // Create the transfer that copies the output meta-data to the input meta-data 
          ptransfer->copy(output_offsets->metaDataOffset + s_port.getPortId() * OCPI_SIZEOF(DDT::Offset, BufferMetaData),
			  input_offsets->metaDataOffset + s_port.getPortId() * OCPI_SIZEOF(DDT::Offset, BufferMetaData),
			  sizeof(OCPI::OS::int64_t),
			  DT::XferRequest::MetaDataTransfer);

          // FIXME.  We need to allocate a separate local flag for this.  (most dma engines dont have
          // an immediate mode).
          // Create the transfer that copies our state to back to the output to indicate that its buffer
          // is now available for re-use.
          ptransfer->copy(input_offsets->localStateOffset + s_port.getPortId() * OCPI_SIZEOF(DDT::Offset, BufferState),
			  output_offsets->localStateOffset + s_port.getPortId() * OCPI_SIZEOF(DDT::Offset, BufferState),
			  sizeof(BufferState),
			  DT::XferRequest::FlagTransfer);

        } catch( ... ) {
          FORMAT_TRANSFER_EC_RETHROW(&s_port, &t_port);
        }
        // Add the transfer
        temp.addTransfer( ptransfer );
      } // end for each input buffer
    } // end for each output buffer
  }  // end for each input port
}

bool Controller1AFCShadow::
canProduce(Buffer */*buffer*/) {
  return true;
}

void Controller1AFCShadow::
modifyOutputOffsets(Buffer */*me*/, Buffer */*new_buffer*/, bool /*reverse*/) {
  ocpiAssert("AFCShadowTransferController::modifyOutputOffsets() Should never be called !!\n"==0);
}

unsigned Controller1AFCShadow::
produce(Buffer *buffer, bool bcast) {
  ocpiDebug("In TransferController1AFCShadow::produce");

  if (bcast) {
    ocpiDebug("*** producing via broadcast, rank == %d !!", buffer->getPort()->getRank());
    if (!buffer->getMetaData()->endOfStream)
      ocpiDebug("*** ERROR *** EOS not set via broadcast !!");
  }

  // With this pattern, only port 0 of the output port set can produce
  if (m_isWholeOutputSet && buffer->getPort()->getRank() != 0) {
    ocpiDebug("My rank != 0 so i am not producing !!!");

    // Next input buffer
    m_nextTid = (m_nextTid + 1) % m_input.getBufferCount();
    ocpiDebug("AFCTransferController:: m_nextTid = %d", m_nextTid );

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

  /*
   *  For this pattern the output port and input port are constants when we look 
   *  up the template that we need to produce.  So, since the output tid is a given,
   *  the only calculation is the input tid that we are going to produce to.
   */
  auto &temp = 
    getTemplate(buffer->getPort()->getPortId(), buffer->getTid(), 0, m_nextTid, bcast, OUTPUT);

#ifdef DEBUG_L2
  ocpiDebug("output port id = %d, buffer id = %d, input id = %d, template = %p", 
	    buffer->getPort()->getPortId(), buffer->getTid(), m_nextTid, temp);
#endif

  // We need to mark the local buffer as free
  buffer->markBufferFull();

  // Start producing, this may be asynchronous
  temp.produce();
  insert_to_list(&buffer->getPendingTxList(), &temp, 64, 8);  // Add the template to our list

  // Next input buffer 
  m_nextTid = (m_nextTid + 1) % m_input.getBufferCount();

#ifdef DEBUG_L2
  ocpiDebug("next tid = %d, num buf = %d", m_nextTid, m_input.getBufferCount());
  ocpiDebug("Returning max gated sequence = %d", temp.getMaxGatedSequence());
#endif

  return temp.getMaxGatedSequence();
}

/**********************************
 * This marks the input buffer as "Empty" and informs all interested outputs that
 * the input is now available.
 *********************************/
Buffer *Controller1AFCShadow::
consume(Buffer *buffer) {
  // We need to mark the local buffer as free
  buffer->markBufferEmpty();

#ifdef DTI_PORT_COMPLETE
  buffer->setBusyFactor( buffer->getPort()->getCircuit()->getRelativeLoadFactor() );
#endif
  auto &temp = getTemplate(0, 0, buffer->getPort()->getPortId(), buffer->getTid(), false, INPUT);

#ifdef DEBUG_L2
  ocpiDebug("Set load factor to %d", buffer->getState()->pad);
  ocpiDebug("Consuming using tpid = %d, ttid = %d, template = 0x%x",buffer->getPort()->getPortId(),
	    buffer->getTid(), temp);
#endif
  // Tell everyone that we are empty
  return temp.consume();
}



#if 0
/**********************************
 * This method gets the next available buffer from the specified output port
 *********************************/
Buffer* 
TransferController1AFCShadow::
getNextEmptyOutputBuffer( 
                                                     OCPI::DataTransport::Port* src_port        
                                                     )
{
  OutputBuffer* boi=NULL;        
  OCPI::OS::uint32_t &n = src_port->getLastBufferTidProcessed();
  boi = static_cast<OutputBuffer*>(src_port->getBuffer(n));
  n = (n+1) % src_port->getBufferCount();
  return boi;
}
#endif


Buffer *Controller1AFCShadow::
getNextFullInputBuffer(Port* input_port) {
  InputBuffer* buffer;
  if (hasFullInputBuffer(input_port, &buffer)) {
    BufferOrdinal
      &lo = input_port->getLastBufferOrd(),
      tlo = ((lo+1)%input_port->getBufferCount());
    lo = tlo;    
    buffer->setInUse( true );
    buffer->m_pullTransferInProgress = NULL;
    return buffer;
  }
  return NULL;
}



// A input buffer with a AFC output has the following states:
//  
//   Empty - No data available
//   Empty - Data available at output
//   Empty - Data transfer in progress
//   Full  - Not in use
//   Full  - In use
//   Empty - No data available

bool Controller1AFCShadow::
hasFullInputBuffer(Port* input_port, InputBuffer** retb) const {
  InputBuffer* buffer;
  BufferOrdinal
    &lo = input_port->getLastBufferOrd(),
    tlo = ((lo+1)%input_port->getBufferCount());
  *retb = buffer = static_cast<InputBuffer*>(input_port->getBuffer(tlo));
  volatile BufferState* state = buffer->getState();
  //  ocpiAssert(!"AFC buffer check");
  if ((state->bufferIsFull & FF_MASK) == FF_EMPTY_VALUE || buffer->inUse())
    return false;
  // At this point we have determined that the output port has a buffer available for us. 
  if ( !buffer->m_pullTransferInProgress ) {
    // Start the pull transfer now
    buffer->m_pullTransferInProgress = 
      input_port->getCircuit()->getOutputPortSet()->pullData( buffer );
  } else {
    if ( buffer->m_pullTransferInProgress->isEmpty())
      return true;
  }
  return false;
}

} // namespace DataTransport
} // namespace OCPI
