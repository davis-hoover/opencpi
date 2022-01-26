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

#include "UtilList.hh"
#include "OsAssert.hh"
#include "TimeEmitCategories.hh"
#include "TransportCircuit.hh"
#include "TransportPortSet.hh"
#include "TransportPartition.hh"
#include "TransportBuffer.hh"
#include "TransportOutputBuffer.hh"
#include "TransportInputBuffer.hh"
#include "TransportController.hh"

///
////  Transfer controller for pattern 4
///

namespace XF = OCPI::Xfer;
namespace OCPI {
namespace Transport {

// Create transfers for output port
void Controller4::
createOutputTransfers(Port &s_port) {
  ocpiAssert("pattern4 output"==0);
  /*
   *  For a WP / P(Parts) transfer, we need to be capable of transfering from any
   *  output buffer to all input port buffers.
   */
  ocpiDebug("In TransferTemplateGeneratorPattern4::createOutputTransfers");

  // Since this is a whole output distribution, only port 0 of the output
  // set gets to do anything.
  if (s_port.getPortSet()->getDataDistribution()->getMetaData()->distType ==
      DataDistributionMetaData::parallel &&
       s_port.getRank() != 0 ) {
    return;
  }

  unsigned n,
    n_s_buffers = m_output.getBufferCount(),
    n_t_buffers = m_input.getBufferCount(),
    n_t_ports = m_input.getPortCount();

  DataPartition *dpart = m_input.getDataDistribution()->getDataPartition();

  // Get the number of transfers that it is going to take to satisfy this output
  unsigned n_transfers_per_output_buffer = dpart->getTransferCount(&m_output, &m_input);

  // For this pattern we need a transfer count that is a least as large as the number
  // of input ports, since we have to inform everyone about the end of whole
  if (m_markEndOfWhole) {
    if (n_transfers_per_output_buffer < n_t_ports) {
      //                  n_transfers_per_output_buffer = n_t_ports;
    }
  }
  // Get the total number of parts that make up the whole
  unsigned parts_per_whole = dpart->getPartsCount(&m_output, &m_input);

  ocpiDebug("** There are %d transfers to complete this set", n_transfers_per_output_buffer);
  ocpiDebug("There are %d parts per whole", parts_per_whole );

  // We need a transfer template to allow a transfer from each output buffer to every
  // input buffer for this pattern.
  unsigned sequence;
  Transfer *root_temp = NULL, *temp = NULL;
  for (unsigned s_buffers = 0; s_buffers < n_s_buffers; s_buffers++) {
    // output buffer
    OutputBuffer* s_buf = s_port.getOutputBuffer(s_buffers);
    unsigned s_tid = s_buf->getTid();
    unsigned part_sequence;

    // We need a transfer template to allow a transfer to each input buffer
    for (unsigned t_buffers = 0; t_buffers < n_t_buffers; t_buffers++) {
      //Each output buffer may need more than 1 transfer to satisfy itself
      sequence = 0;
      part_sequence = 0;
      for (unsigned transfer_count = 0; transfer_count < n_transfers_per_output_buffer;
            transfer_count++, sequence++) {

        // Get the input port
        Port &in_port = *m_input.getPort(0);
        InputBuffer* t_buf = in_port.getInputBuffer(t_buffers);
        unsigned t_tid = t_buf->getTid();

        // We need to be capable of transfering the gated transfers to all input buffers
        for (unsigned t_gated_buffer = 0; t_gated_buffer < n_t_buffers+1; t_gated_buffer++) {
          // This may be gated transfer
          if (transfer_count == 0 && t_gated_buffer == 0) {
            temp = new Transfer(4);
            root_temp = temp;
            // Add the template to the controller, 
            setTemplate(*temp, s_port.getPortId(), s_tid, 0 ,t_tid, false, OUTPUT);
          } else {
            part_sequence = transfer_count * n_t_ports;
            temp = new Transfer(4);
            root_temp->addGatedTransfer( sequence, temp, 0, t_tid);
          }
          // We need to setup a transfer for each input port. 
          for (n = 0; n < n_t_ports; n++) {
            // Get the input port
            Port &t_port = *m_input.getPort(n);
            t_buf = t_port.getInputBuffer(t_buffers);

            struct PortMetaData::OutputPortBufferControlMap *output_offsets = 
              &s_port.getMetaData()->m_bufferData[s_tid].outputOffsets;

            struct PortMetaData::InputPortBufferControlMap *input_offsets = 
              &t_port.getMetaData()->m_bufferData[t_tid].inputOffsets;

            // Since this is a "parts" transfer, we dont allow zero copy
	    XF::XferRequest* ptransfer =
	      s_port.getTemplate(s_port.getEndPoint(), t_port.getEndPoint()).
	      createXferRequest();

            // Now we need to go to the data partition class and ask for some offsets
            DataPartition::BufferInfo *bi_tmp, *buffer_info;
            dpart->calculateBufferOffsets(transfer_count, s_buf, t_buf, &buffer_info);
            bi_tmp = buffer_info;
            unsigned total_bytes = 0;
            while (bi_tmp) {
              try {
                // Create the transfer that copys the output data to the input data
                ptransfer->copy(output_offsets->bufferOffset + bi_tmp->output_offset,
				input_offsets->bufferOffset + bi_tmp->input_offset,
				bi_tmp->length,
				XF::XferRequest::DataTransfer);
                total_bytes += bi_tmp->length;
              } catch ( ... ) {
                FORMAT_TRANSFER_EC_RETHROW(&s_port, &t_port);
              }
              bi_tmp = bi_tmp->next;
            }
            delete buffer_info;

            // At this point we need to tell the template what needs to be inserted into
            // the output meta-data prior to transfer, this includes the actual number
            // of bytes that were transfered and the end of whole indicator.
            bool end_of_whole = transfer_count == (n_transfers_per_output_buffer-1);
            temp->presetMetaData(s_buf->getMetaDataByIndex(t_port.getPortId()),
				 total_bytes, end_of_whole, parts_per_whole, part_sequence++);
            try {
              // Create the transfer that copys the output meta-data to the input meta-data
              ptransfer->copy (output_offsets->metaDataOffset + t_port.getPortId() * OCPI_SIZEOF(XF::Offset, BufferMetaData),
			       input_offsets->metaDataOffset + s_port.getPortId() * OCPI_SIZEOF(XF::Offset, BufferMetaData),
			       sizeof(OCPI::OS::uint64_t),
			       XF::XferRequest::MetaDataTransfer);
              // Create the transfer that copys the output state to the remote input state
              ptransfer->copy (output_offsets->localStateOffset + s_port.getPortId() * OCPI_SIZEOF(XF::Offset, BufferState),
			       input_offsets->localStateOffset + s_port.getPortId() * OCPI_SIZEOF(XF::Offset, BufferState),
			       sizeof(BufferState),
			       XF::XferRequest::FlagTransfer);
            } catch ( ... ) {
              FORMAT_TRANSFER_EC_RETHROW(&s_port, &t_port);
            }
            // Add the transfer 
            temp->addTransfer(ptransfer);
          } // end for each input port
          t_buf = in_port.getInputBuffer(t_gated_buffer%n_t_buffers);
          t_tid = t_buf->getTid();
        } // for each gated buffer
      } // end for each input buffer
    } // end for n transfers
  }  // end for each output buffer 
}

bool Controller4::
canProduce(Buffer* buffer) {
  // When s DD = whole only port 0 of the output port set can produce
  if (m_isWholeOutputSet && (buffer->getPort()->getRank() != 0))
    return true;
  // If there are no pending transfers, controller 1 will work.
  return Controller1::canProduce(buffer);
}

unsigned Controller4::
produce(Buffer *buffer, bool bcast) {
  // Determine if this is a gated transfer, we have to note that any controller
  // can add a transfer template to the output buffer and we can only handle ours
  unsigned n_pending = buffer->getPendingTransferCount();
  if (! n_pending)
    return Controller1::produce(buffer, bcast);
  // We have some pending transfers on this buffer
  List& l_pending = buffer->getPendingTxList();

#ifdef DEBUG_L2
  ocpiDebug("pending transfers on buffer = %d", n_pending );
#endif
  unsigned total = 0;
  unsigned n = 0;
  for (n = 0; n < n_pending; n++) {
    Transfer &temp = *static_cast<Transfer*>(get_entry(&l_pending, n));
    // If this is one ouf ours, produce and then break, we only get to produce once each time
    // "canProduce" is called.
    assert(&temp);
    if (temp.getTypeId() == 4) {

      // This is effectivly a broadcst to all port buffers, so we need to mark them as full
      for (PortOrdinal nn = 0; nn < m_input.getPortCount(); nn++) {
        Buffer* tbuf = static_cast<Buffer*>(m_input.getPort(nn)->getBuffer(m_nextTid));
        tbuf->markBufferFull();
      }
      total += temp.produceGated(0, m_nextTid);
      break;
    }
  }
#ifdef DEBUG_L2
  ocpiDebug("TransportController4::produce returning %d", total );
#endif
  return total;
}

Buffer *Controller4::
getNextFullInputBuffer(Port *input_port) {

#ifdef DEBUG_L2
  ocpiDebug("In TransportController4::getNextFullInputBuffer");
#endif

  // With this pattern, the data buffers are not deterministic, so we will always hand back
  // the buffer with the lowest output sequence AND the lowest whole sequence
  InputBuffer *buffer;
  InputBuffer *low_seq = NULL;

  for (unsigned n = 0; n < input_port->getBufferCount(); n++) {
    buffer = input_port->getInputBuffer(n);
    if (!buffer->isEmpty() && ! buffer->inUse()) {
      if (low_seq ) {
        if (buffer->getMetaData()->sequence < low_seq->getMetaData()->sequence)
          low_seq = buffer;
        else if ((buffer->getMetaData()->sequence == low_seq->getMetaData()->sequence) &&
		 (buffer->getMetaData()->partsSequence < low_seq->getMetaData()->partsSequence))
          low_seq = buffer;
      } else
        low_seq = buffer;
    }
  }
  if (low_seq)
    low_seq->setInUse( true );

#ifdef DEBUG_L2
  if (!low_seq)
    ocpiDebug("No Input buffers avail");
#endif
  return low_seq;
}

} // namespace DataTransport
} // namespace OCPI

