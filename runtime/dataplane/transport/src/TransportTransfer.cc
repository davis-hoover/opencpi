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

#include "OsAssert.hh"
#include "TransportPortSet.hh"
#include "TransportTransfer.hh"

namespace OCPI {
namespace DataTransport {

Transfer::
Transfer(unsigned id)
  : m_id(id), n_transfers(0), m_maxSequence(0), m_zCopy(NULL) {
}

Transfer::
~Transfer() {
  delete m_zCopy;
  // DO NOT DELETE from m_xferReq array since they are owned by the controller
}

// Make sure we dont already have this pair
bool Transfer::
isDuplicate(OutputBuffer *output, InputBuffer *input) {
  if (m_zCopy)
    for (ZCopy *z = m_zCopy; z; z = z->next)
      if (z->output == output && z->input == input)
        return true;
  return false;
}

// Add a xero copy transfer request
void Transfer::
addZeroCopyTransfer(OutputBuffer* output, InputBuffer* input) {
  ocpiDebug("addZeroCopyTransfer, adding Zero copy transfer, output = %p, input = %p", output, input);
  if (isDuplicate( output, input))
    return;
  ZCopy  *zc = new ZCopy(output,input);
  if (!m_zCopy)
    m_zCopy = zc;
  else
    m_zCopy->add(zc);
}

// Is this transfer complete
bool Transfer::
isComplete() {
  // If we have any gated transfers pending, we are not done
  if (m_sequence < m_maxSequence)
    return false;

  // Make sure all of our transfers are complete
  for (unsigned n = 0; n < n_transfers; n++)
    if (m_xferReq[n]->getStatus() != 0)
      return false;

  // now make sure all of the gated transfers are complete
  unsigned n_pending = get_nentries(&m_gatedTransfersPending);

  ocpiDebug("There are %d gated transfers", n_pending);

  for (unsigned i = 0; i < n_pending; i++) {
    Transfer* temp = static_cast<Transfer*>(get_entry(&m_gatedTransfersPending, i));
    if (temp->isComplete()) {
      remove_from_list(&m_gatedTransfersPending, temp);
      n_pending = get_nentries(&m_gatedTransfersPending);
      i = 0;
    } else
      return false;
  }
  return true;
}

unsigned Transfer::
produceGated(unsigned port_id, unsigned tid) {
  // See if we have any other transfers of this type left
  ocpiDebug("m_sequence = %d", m_sequence );
  Transfer *temp = getNextGatedTransfer(port_id, tid);

  if (temp)
    temp->produce();
  else {
    ocpiDebug("ERROR !!! Transfer::produceGated got a NULL template, p = %d, t = %d",
           port_id, tid);
    ocpiAssert(0);
  }
  // Add the template to our list
  insert_to_list(&m_gatedTransfersPending, temp, 64, 8);
  return (unsigned)(m_maxSequence - m_sequence);
}

// Presets values into output meta-data prior to kicking off a transfer
void Transfer::
presetMetaData(volatile BufferMetaData* data, unsigned length, bool end_of_whole,
	       unsigned parts_per_whole, unsigned sequence) {
  unsigned seq_inc = 0;
  PresetMetaData *pmd = new PresetMetaData();

  pmd->ptr = data;
  pmd->length = length;
  pmd->endOfWhole = end_of_whole ? 1 : 0;
  pmd->nPartsPerWhole = parts_per_whole;
  pmd->sequence = sequence + seq_inc;
  seq_inc++;
  // Add the structure to our list
  insert_to_list(&m_PresetMetaData, pmd, 64, 8);
}

// Preset values into the output meta-data prior to kicking off a transfer
void Transfer::
presetMetaData() {
  unsigned n_pending = get_nentries(&m_PresetMetaData);
  for (unsigned i = 0; i < n_pending; i++) {
    PresetMetaData *pmd = static_cast<PresetMetaData*>(get_entry(&m_PresetMetaData, i));
    pmd->ptr->ocpiMetaDataWord.length = pmd->length;
    pmd->ptr->endOfWhole         = pmd->endOfWhole;
    pmd->ptr->nPartsPerWhole     = pmd->nPartsPerWhole;
    pmd->ptr->partsSequence      = pmd->sequence;
  }
}

// start the transfer
void Transfer::
produce() {
  // start the transfers now
  ocpiDebug("Producing %d transfers", n_transfers);

  // At this point we need to pre-set the meta-data if needed
  presetMetaData();

  // If we have a list of attached buffers, it means that we need to 
  // inform the local buffers that there is zero copy data available
  if (m_zCopy)
    for (ZCopy *z = m_zCopy; z; z = z->next) {
      ocpiDebug("Attaching %p to %p", z->output, z->input);
      z->input->attachZeroCopy( z->output );
    }
  // Remote transfers
  for (unsigned n = 0; n < n_transfers; n++)
    m_xferReq[n]->post();

  // Now increment our gated transfer control
  m_sequence = 0;
}

// start the transfer
Buffer* Transfer::
consume() {
  Buffer *rb = NULL;

  ocpiDebug("Consuming %d transfers", n_transfers);
  // If we have a list of attached buffers, it means that we are now
  // done with the local zero copy buffers and need to mark them 
  // as available
  if (m_zCopy)
    for (ZCopy *z = m_zCopy; z; z = z->next) {
      ocpiDebug("Detaching %p to %p", z->output, z->input);
      rb = z->input->detachZeroCopy();
    }
  // Remote transfers
  for (unsigned n = 0; n < n_transfers; n++)
    m_xferReq[n]->post();
  return rb;
}

void Transfer::
modify(DtOsDataTypes::Offset new_off[], DtOsDataTypes::Offset old_off[]) {
  for (unsigned n = 0; n < n_transfers; n++)
    m_xferReq[n]->modify(new_off, old_off);
}

void Transfer::ZCopy::
add( ZCopy * zc ) {
  ZCopy* t = this;
  while (t->next)
    t = t->next;
  t->next = zc;
}

}
}
