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

/*
 * Abstract:
 *   This file contains the implementation for the OCPI output buffer class.
 *
 * Revision History: 
 * 
 *    Author: John F. Miller
 *    Date: 1/2005
 *    Revision Detail: Created
 */
#include <inttypes.h>
#include "TransportHandshakeControl.hh"
#include "TransportOutputBuffer.hh"
#include "TransportInputBuffer.hh"
#include "TransportPort.hh"
#include "TransportTransfer.hh"
#include "TransportCircuit.hh"
#include "OsAssert.hh"
#include "UtilAutoMutex.hh"
#include "TimeEmitCategories.hh"

namespace OCPI {
namespace Transport {
/**********************************
 * Constructors
 *********************************/
OutputBuffer::OutputBuffer( Port* port, OCPI::OS::uint32_t tid )
  : Buffer(port, tid ), m_spsControl(NULL), m_bcsVaddr(NULL), m_slave(false)
{
  m_bVaddr = 0;
  m_bsVaddr = 0;
  m_bmdVaddr = 0;
  m_bcsVaddr = 0;

  // update
  ocpiDebug("OutputBuffer: port %p bmd %p offset 0x%" OCPI_UTIL_RESADDR_PRIx,
	    port, port->getMetaData()->m_bufferData,
	    port->getMetaData()->m_bufferData[0].outputOffsets.bufferOffset);
  update(0);
}


/**********************************
 * Get/Set the number of bytes transfered
 *********************************/
void OutputBuffer::setNumberOfBytes2Transfer(OCPI::OS::uint32_t length)
{
  getMetaData()->ocpiMetaDataWord.length = length;
}


/**********************************
 * Update offsets
 *********************************/
void OutputBuffer::update(bool critical)
{
  ( void ) critical;
  OCPI::Util::AutoMutex guard ( m_threadSafeMutex, true ); 
  unsigned tid = getTid();
  struct PortMetaData::OutputPortBufferControlMap *output_offsets = 
    &getPort()->getMetaData()->m_bufferData[tid].outputOffsets;

  ocpiDebug("Output buffer update: %p (casted %p) tid %u mbv %p bo %u",
	    this, static_cast<Buffer*>(this), tid, m_bVaddr, output_offsets->bufferOffset);
  if ( this->m_port->isShadow()) {
    return;
  }

  // First we will map our buffer
  if ( !m_bVaddr && output_offsets->bufferOffset ) {

    ocpiDebug("OutputBuffer:update: port %p bmd %p mapping buffer %p tid %d offset 0x%"
	      OCPI_UTIL_RESADDR_PRIx" at %p",
	      getPort(), getPort()->getMetaData()->m_bufferData,
	      this, tid, output_offsets->bufferOffset, output_offsets);

    m_bVaddr = getPort()->getLocalShemServices()->mapTx
      (output_offsets->bufferOffset, 
       output_offsets->bufferSize);
    m_startOffset = output_offsets->bufferOffset;
    m_length = output_offsets->bufferSize;
    memset(m_bVaddr, 0, output_offsets->bufferSize);
    m_buffer = /*m_baseAddress = */ m_bVaddr;

#ifdef DEBUG_L2
    ocpiDebug("*** Output buffer addr = 0x%x, size = %d", m_buffer, output_offsets->bufferSize );
#endif

  }
 
  // map our states
  if ( !m_bsVaddr && output_offsets->localStateOffset ) {

    ocpiDebug("OutputBuffer:%p update: mapping states", this);

    m_bsVaddr = getPort()->getLocalShemServices()->mapTx
      (output_offsets->localStateOffset, 
       sizeof(BufferState)*MAX_PCONTRIBS*2);

    m_state = static_cast<volatile BufferState (*)[MAX_PCONTRIBS]>(m_bsVaddr);
    // These EMPTY are the non-shadow local flags indicating emptiness/availability
    // Written by remote side when evacuated by remote side by pull
    // or set by us when a transfer is done
    for ( unsigned int y=0; y<MAX_PCONTRIBS; y++ ) {
      m_state[0][y].bufferIsEmpty = EF_EMPTY_VALUE;
    }
    // These FULL flags will be set by the output side to FULL and sent to the input side
    // This separates the flag that we get from the input side (pull) and the flag that we send to
    // the other side.  This is constant staging.
    for ( unsigned int y=MAX_PCONTRIBS; y<MAX_PCONTRIBS*2; y++ ) {
      m_state[0][y].bufferIsFull = FF_FULL_VALUE;
    }
  }
 
  // map our meta-data
  if ( !m_bmdVaddr && output_offsets->metaDataOffset ) {

    ocpiDebug("OutputBuffer:update: mapping metadata");

    m_bmdVaddr = getPort()->getLocalShemServices()->mapTx
      (output_offsets->metaDataOffset, 
       sizeof(BufferMetaData)*MAX_PCONTRIBS);

    memset(m_bmdVaddr, 0, sizeof(BufferMetaData)*MAX_PCONTRIBS);
    m_sbMd = static_cast<volatile BufferMetaData (*)[MAX_PCONTRIBS]>(m_bmdVaddr);
  }


  // map our output control structure
  if ( !m_bcsVaddr && output_offsets->portSetControlOffset ) {

    ocpiDebug("OutputBuffer: mapping control structure");

    m_bcsVaddr = getPort()->getLocalShemServices()->mapTx
      (output_offsets->portSetControlOffset, 
       sizeof(OutputPortSetControl));

    ocpiDebug("m_bcsVaddr %p, portSetControlOffset %lld",
           m_bcsVaddr, (long long)output_offsets->portSetControlOffset);

                 
    memset(m_bcsVaddr, 0, sizeof(OutputPortSetControl));
    m_spsControl = static_cast<OutputPortSetControl*>(m_bcsVaddr);
    getPort()->setOutputControlBlock( m_spsControl );
  }

}

/**********************************
 * Get this buffers local state structure
 **********************************/              
volatile BufferState* OutputBuffer::getState()
{
  //  ocpiDebug("ob %p shadow %d m_pid %u",
  //	    this, this->m_port->isShadow(), m_pid);
  if ( m_dependentZeroCopyCount ) {
    //    ocpiDebug("ob %p zc %u dep ports %u",
    //	      this, m_dependentZeroCopyCount,
    //	      m_dependentZeroCopyPorts.size());
    PortOrdinal c=0;
    for ( PortOrdinal n=0;
          c<m_dependentZeroCopyCount && n<(PortOrdinal)m_dependentZeroCopyPorts.size(); n++) {
      if ( m_dependentZeroCopyPorts[n] ) {
	PortOrdinal i = static_cast<InputBuffer*>(m_dependentZeroCopyPorts[n])->getPort()->getPortId();
	// If any of our dependent zc inputs are still full,
	// then we must be treated as still full (still not evacuated).
	uint32_t state = m_state[0][i].bufferIsEmpty & EF_MASK;
	ocpiAssert(state == EF_EMPTY_VALUE ||state == EF_FULL_VALUE);
        if (state == EF_FULL_VALUE ) {
	    return &m_state[0][i];
        }
        c++;
      }
    }
  }

  //  ocpiDebug("Output buffer %p m_pid %u empty state = 0x%llx",
  //	    this, m_pid, (long long)m_state[0][m_pid].bufferIsEmpty );
  uint32_t state = m_state[0][m_pid].bufferIsEmpty & EF_MASK;
  ocpiAssert(state == EF_EMPTY_VALUE ||state == EF_FULL_VALUE);
  return &m_state[0][m_pid];
}




/**********************************
 * Is this buffer empty
 *********************************/
bool OutputBuffer::isEmpty()
{
  ocpiAssert(!getPort()->isShadow());
  if ( Buffer::isEmpty() == false ) {
    return false;
  }
  OCPI::Util::AutoMutex guard ( m_threadSafeMutex,
                               true ); 

#ifdef DEBUG_L2
  ocpiDebug("Checking output isEmpty, m_dependentZeroCopyCount = %d, NOT CHECKING THEM !!",
	    m_dependentZeroCopyCount);
#endif

  // If we have any pending transfers, we will check them here to determine if
  // they are done
  unsigned n_pending = get_nentries(&m_pendingTransfers);

#ifdef DEBUG_L2
  ocpiDebug("** there are %d pending output transfers", n_pending );
#endif

  for (unsigned i=0; i < n_pending; i++) {
    Transfer* temp = static_cast<Transfer*>(get_entry(&m_pendingTransfers, i));
    if ( temp->isComplete() ) {
      remove_from_list( &m_pendingTransfers, temp );
      n_pending = get_nentries(&m_pendingTransfers);
      i = 0;
    }
    else {
      return false;
    }
  }

  if ( ! m_slave ) {

    //    ocpiDebug("Not Slave port, manually setting DMA complete flag");

    if ( n_pending == 0 ) {
      ocpiAssert(m_state[0][m_pid].bufferIsEmpty == EF_EMPTY_VALUE ||
		 m_state[0][m_pid].bufferIsEmpty == EF_FULL_VALUE);
      m_state[0][m_pid].bufferIsEmpty = EF_EMPTY_VALUE;
    }
  }

#if 0
  if ( getPort()->isShadow() ) {
    return true;
  }
#endif
  volatile BufferState* state = this->getState();

  //  ocpiDebug("isEmpty: Output empty buffer %p state = %d", this, state->bufferIsEmpty );
  uint32_t empty = state->bufferIsEmpty & EF_MASK;
  ocpiAssert(empty == EF_EMPTY_VALUE || empty == EF_FULL_VALUE);
  return empty == EF_EMPTY_VALUE;
}

/**********************************
 * Get the offset to this ports meta-data
 **********************************/
volatile BufferMetaData* OutputBuffer::getMetaData()
{
  if ( m_zeroCopyFromBuffer ) {
    return m_zeroCopyFromBuffer->getMetaData();
  }

  return &m_sbMd[0][m_pid];
}


/**********************************
 * Get/Set the number of bytes transfered
 *********************************/
OCPI::OS::uint32_t OutputBuffer::getNumberOfBytesTransfered()
{
  return (OCPI::OS::uint32_t) getMetaDataByIndex(0)->ocpiMetaDataWord.length;
}

void OutputBuffer::setMetaData()
{
  for ( PortOrdinal b=0; b< m_port->getCircuit()->getMaxPortOrd(); b++ ) {
    if (b != m_pid) {
      memcpy((void*) &m_sbMd[0][b].ocpiMetaDataWord, (void*)&m_sbMd[0][m_pid].ocpiMetaDataWord, sizeof(RplMetaData) );

      m_sbMd[0][b].zcopy           = m_sbMd[0][m_pid].zcopy;
      m_sbMd[0][b].sequence       = m_sbMd[0][m_pid].sequence;
      m_sbMd[0][b].broadCast      = m_sbMd[0][m_pid].broadCast;
      m_sbMd[0][b].srcRank        = m_sbMd[0][m_pid].srcRank;
      m_sbMd[0][b].srcTemporalId  = m_sbMd[0][m_pid].srcTemporalId;
      m_sbMd[0][b].endOfWhole     = m_sbMd[0][m_pid].endOfWhole;
      m_sbMd[0][b].endOfStream    = m_sbMd[0][m_pid].endOfStream;
    }
  }
}

OutputBuffer::~OutputBuffer(){}

}
}
