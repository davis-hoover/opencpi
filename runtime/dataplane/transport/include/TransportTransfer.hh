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

// This file declares the class that represents the *transport-layer* notion
// of "a transfer", which is an ordered set of individual lower-level DaataTransfer::XferRequests.
// A transfer at this transport level performs things like:
// -- send a message
// -- send an indication that a message can be "pulled"
// -- send an indication that a buffer has become empty
// I.e. these transfers are used to implement the RDMA multibuffering protocol.
// Note that these tranfers are built from the lower level XferRequest objects that
// are managed at the lower "xfer" level of endpoints and point-to-point contiguous DMAs.

#ifndef OCPI_DataTransport_Transfer_H_
#define OCPI_DataTransport_Transfer_H_

#include "OcpiTransportConstants.h"
#include "OcpiOutputBuffer.h"
#include "OcpiInputBuffer.h"
#include "OcpiList.h"
#include "OsAssert.hh"

namespace OCPI {
namespace DataTransport {
  class Port;

  class Transfer {
    struct ZCopy {
      ZCopy():output(NULL),input(NULL),next(NULL){}
      ZCopy( OutputBuffer* s, InputBuffer* t )
	:output(s),input(t),next(NULL){}
      void add( ZCopy* );
      OutputBuffer* output;
      InputBuffer* input;
      ZCopy* next;

    };
    unsigned m_id; // Our transfer type id
    unsigned n_transfers;
    DataTransfer::XferRequest* m_xferReq[MAX_TRANSFERS];

    // For some templates, there are mutiple transfers that have to take place from
    // a single output buffer, such is the case for whole to parts when the number of
    // parts exceed the number of buffers+input ports.
    //                       transfer sequence          input port    input buffer
    Transfer *m_nextTransfer[MAX_TRANSFERS_PER_BUFFER][MAX_PCONTRIBS][MAX_BUFFERS];
    List m_gatedTransfersPending;
    unsigned m_sequence;
    unsigned m_maxSequence;

    // List of preset meta-data structures
    struct PresetMetaData {
      volatile BufferMetaData *ptr;
      uint32_t length;
      uint32_t endOfWhole;
      uint32_t nPartsPerWhole;
      uint32_t sequence;
    };
    List m_PresetMetaData;
    // Next input
    Port* m_nextPort;
    unsigned   m_nextTid;
  public:
    ZCopy *m_zCopy;

    Transfer(unsigned id);
    virtual ~Transfer();
    // Is this transfer pending
    bool isPending() { return false; }
    // Is this transfer in use
    bool isComplete();
    // Start the output/input transfer
    void produce();
    // Start the input reply transfer
    Buffer *consume();
    // Start the input reply transfer
    void modify(DtOsDataTypes::Offset new_off[], DtOsDataTypes::Offset old_off[]);
    // Get/Set transfer type id
    void setTypeId(unsigned id) { m_id = id;}
    unsigned getTypeId() {return m_id; }
    // Check for duplicates
    bool isDuplicate(OutputBuffer *output, InputBuffer *input);
    // Add a transfer request
    void addTransfer(DataTransfer::XferRequest* tx_request) {
      ocpiAssert(n_transfers < MAX_TRANSFERS);
      m_xferReq[n_transfers++] = tx_request;
    }
    // Add a zero copy transfer request
    void addZeroCopyTransfer(OutputBuffer *output, InputBuffer *input);
    // Add a gated transfer, gated transfers are additional transfers that
    void addGatedTransfer(unsigned sequence,
			  Transfer *gated_transfer,
			  PortOrdinal input_port_id,
			  unsigned buffer_tid) {
      if (sequence > m_maxSequence) {
	m_maxSequence = sequence;
      }
      ocpiDebug("*** Adding a gated transfer to this[%d][%d][%d] \n",
		m_maxSequence,input_port_id, buffer_tid);
      m_nextTransfer[sequence][input_port_id][buffer_tid] = gated_transfer;
    }
    // Get a gated transfer
    Transfer *getNextGatedTransfer(PortOrdinal input_port_id, unsigned buffer_tid) {
      return m_nextTransfer[m_sequence++][input_port_id][buffer_tid];
    }
    // Get the maximum post produce sequence this class should transfer
    unsigned getMaxGatedSequence() {
      return m_maxSequence;
    }
// Produce the next gated tansfer of this type
    unsigned produceGated(unsigned port_id, unsigned tid);
    // Intializes the presets values into the output meta-data prior to kicking off a transfer
    void presetMetaData(volatile BufferMetaData *data,
			unsigned    length,
			bool        end_of_whole,
			unsigned    nPartsPerWhole,
			unsigned    sequence);
    // Sets the next input port and tid
    void setInput(Port *p, unsigned tid) {
      m_nextPort = p; m_nextTid = tid;
    }
    // Executes preset's
    void presetMetaData();
  };
} // namespace DataTransport
} // namespace OCPI

#endif
