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
* -------------------------------------------------------------------------------
* -- Capture_v2
* -------------------------------------------------------------------------------
* 
* Description:
* 
* The capture_v2 worker provides the ability to store an input port's
* data. Two modes are supported:
* * 'leading' - capture all messages from input port until the buffer is full.
* This has the affect of capturing messages from the start of an application.
* * 'trailing' - capture all messages from input port and allow the buffer's
* content to be overwritten while application is in operation. This has the affect
* of capturing all messages (a buffers worth) near the end of an application.
* 
* This worker provides an optional output port, so that, it may be
* placed between two workers. The input messages are directly passed to
* the output port.
* 
* The capture_v2 worker takes input port messages and stores their data in a
* buffer via the data property as 4 byte words. Metadata associated with each
* message is stored as a record in a metadata buffer via the metadata property.
* It captures four 4 byte words of metadata. The first metadata word is the
* opcode of the message and message size (bytes); opcode 8 MSB and message
* size 24 LSB. The second word is the fraction time stamp for the EOM. The
* third word is the fraction time stamp for the SOM. And the fourth word is
* the seconds timestamp for the SOM. For capture_v2.rcc, the second and third words 
* have the same value since there is no concept of start and end of message for RCC 
* workers. So that the metadata can be read on a little-endian processor, the 
* ordering of the metadata is as follows:
* 1) opcode (8-bit) & message size (24-bit)
* 2) eom fraction (32-bit)
* 3) som fraction (32-bit)
* 4) som seconds (32-bit)
* 
* The capture_v2 worker counts the number of metadata records (metadataCount)
* have been captured and how many data words have been captured (dataCount), 
* and the total number of bytes that were passed through the worker 
* during an app run (totalBytes). It allows for the option to wrap around and 
* continue to capture data and metadata once the buffers are full or to stop 
* capturing data and metadata when the data and metadata buffers are full 
* via the stoponFull property.
* 
* When stopOnFull is true (leading), data and metadata will be captured as long as
* the metadata buffer is not full. The data buffer will loop if it is not full
* and the metadata buffer is not full. The metadata buffer will loop independently
* until it is not full. When stopOnFull is false (trailing), the data and
* metadata buffers loop independently. There will be a wrap around when the data
* and metadata buffers are full and data and metadata will continue to be captured.
* 
* The worker also has properties that keep track of whether or not the
* metadata and data buffers are full; metaFull and dataFull.
*/

#include "capture_v2-worker.hh"

using namespace OCPI::RCC;
using namespace Capture_v2WorkerTypes;

class Capture_v2Worker : public Capture_v2WorkerBase {
  unsigned dataIndex = 0;
  unsigned metadataIndex = 0;
  bool metadataDisable = false;
  bool dataDisable = false;
  static const unsigned bytesPerSample = 4;
  
  RCCResult run(bool /*timedout*/) {
    const uint64_t timeStamp = (uint64_t)getTime();
    const size_t messageSize = in.length();
    bool eof = in.getEOF();
    bool outIsConnected = out.isConnected();
    if (outIsConnected) {
      out.checkLength(messageSize);
      out.setLength(messageSize);
      out.setOpCode(in.getOpCode());
    }
    if (!eof) {
      const uint32_t *idata = (uint32_t*)in.data();
      uint32_t *odata = (uint32_t*)out.data();
      for (unsigned i = messageSize/bytesPerSample; i; --i) {    
        if (!metadataDisable && !dataDisable)      
          properties().data[dataIndex] =  *idata;
        // Take data while buffer is in wrapping mode (stopOnFull=false) or
        // single capture (stopOnFull=true) and data and metadata counts
        // have not reached their respective maximum.
        if ((properties().stopOnFull && properties().dataCount != CAPTURE_V2_NUMDATAWORDS && 
            properties().metadataCount != CAPTURE_V2_NUMRECORDS) || !properties().stopOnFull)
          properties().dataCount++;
        // Configured for a single buffer capture
        if (properties().stopOnFull && properties().dataCount != CAPTURE_V2_NUMDATAWORDS 
           && properties().metadataCount != CAPTURE_V2_NUMRECORDS)
          dataIndex++;
        else { // Configured for wrap-around buffer capture
          if (dataIndex == CAPTURE_V2_NUMDATAWORDS-1)
            dataIndex = 0;
          else
            dataIndex++;
        }
        
        if (outIsConnected)
          *odata++ = *idata; // copy this message to output buffer
    
        *idata++;
      }
      properties().totalBytes += messageSize;
      if (!metadataDisable) {
        properties().metadata[metadataIndex][0] = (uint32_t)((in.getOpCode() << 24) + messageSize);
        properties().metadata[metadataIndex][1] = (uint32_t)(timeStamp & 0x00000000FFFFFFFF);
        properties().metadata[metadataIndex][2] = (uint32_t)(timeStamp & 0x00000000FFFFFFFF);
        properties().metadata[metadataIndex][3] = (uint32_t)((timeStamp & 0xFFFFFFFF00000000) >> 32);
      }
      // Store metadata after each message or if stopOnFull is true store metadata until data full or metadata full
      if ((properties().stopOnFull && properties().metadataCount != CAPTURE_V2_NUMRECORDS) || !properties().stopOnFull)
        properties().metadataCount++;
      // Configured for a single buffer capture
      if (properties().stopOnFull && properties().metadataCount != CAPTURE_V2_NUMRECORDS)
        metadataIndex++;
      else { // Configured for wrap-around buffer capture
        if (metadataIndex == CAPTURE_V2_NUMRECORDS-1)
          metadataIndex = 0;
        else
          metadataIndex++;
      }
      if (properties().dataCount == CAPTURE_V2_NUMDATAWORDS) {
        properties().dataFull = true;
        // Disable writing to data buffer when data is full
        if (properties().stopOnFull)
          dataDisable = true;
      }
      if (properties().metadataCount == CAPTURE_V2_NUMRECORDS) {
        properties().metaFull = true;
        // Disable writing to metadata and data buffers when metadata are full
        if (properties().stopOnFull)
          metadataDisable = true;
      }
    }
    

    // Determines when the worker is finished.
    // For stopOnEOF, if there is a EOF and stopOnEOF is true then return RCC_ADVANCE_DONE.
    // For stopOnZLM, if there is a ZLM the input opcode is equal to stopZLMOpcode, and 
    // stopOnZLM is true then return RCC_ADVANCE_DONE.
    if ((eof && properties().stopOnEOF) ||
       (messageSize == 0 && in.getOpCode() == properties().stopZLMOpcode && properties().stopOnZLM))
        return RCC_ADVANCE_DONE;

    return RCC_ADVANCE;
  }
};

CAPTURE_V2_START_INFO
// Insert any static info assignments here (memSize, memSizes, portInfo)
// e.g.: info.memSize = sizeof(MyMemoryStruct);
CAPTURE_V2_END_INFO
