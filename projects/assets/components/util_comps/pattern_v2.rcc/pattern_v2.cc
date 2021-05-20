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
* -- Pattern_v2
* -------------------------------------------------------------------------------
* 
* Description:
* 
* The pattern v2 component provides the ability to output a pattern of messages
* by allowing the user to create a record of messages each having a configurable
* number of bytes and associated 8 bit opcode. Through a set of properties, the
* component may send messages (data and opcode) up to the amount dictated by
* the build-time parameters. The messages property defines the record of messages
* to send, as well as, defines the number of data bytes and an opcode for each
* message.
* 
* For example:
* When messages = {4, 255}, one message will be sent having 4
* bytes of data and an opcode of 255. When messages = {8, 251}, {6, 250}, two
* messages will be sent, the first having 8 bytes of data and an opcode of 251,
* and the second message having 6 bytes of data and an opcode of 250.
* 
* Data to be sent with a message is defined by the data property and is referred
* to as the data buffer. The number of data words in the data buffer is the
* number of data bytes for the messages. The component offers an additional
* feature when there are multiple messages via the dataRepeat property which
* indicates whether the a message starts at the beginning of the data buffer,
* or continues from its current index within the buffer.
* 
* For example:
* Given messages = {4, 251},{8, 252},{12, 253},{16, 254},{20, 255}
* 
* If dataRepeat = true, then numDataWords is 5. To calculate the numDataWords
* when dataRepeat is true, divide the largest message size (in bytes) by 4.
* Dividing by four required because the data is output as a 4 byte data
* word. Since the largest message size in the given messages assignment is 20,
* 20/4 = 5. 
* 
* When numDataWords = 5, then a valid data assignment would be
* data = {0, 1, 2, 3, 4}, and the data within each
* message would look like: msg1 = {0}, msg2 = {0, 1}, msg3 = {0, 1, 2},
* msg4 = {0, 1, 2, 3}, msg5 = {0, 1, 2, 3, 4}
* 
* If dataRepeat = false, then numDataWords is 15. To calculate the numDataWords
* when dataRepeat is false, divide the sum of all the message sizes (in bytes) 
* by 4. Dividing by four is required because the data is output as a 4 byte 
* data word. Since the sum of all message sizes in the given messages assignment 
* is (4+8+12+16+20)/4 = 15. 
* 
* When numDataWords = 15, then a valid data assignment 
* would be data = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14},
* and the data within each message would look like:
* msg1 = {0}, msg2 = {1, 2}, msg3 = {3, 4, 5}, msg4 = {6, 7, 8, 9},
* msg5 = {10, 11, 12, 13, 14}
* 
* There is also a messagesToSend property that sets the number of messages to send 
* and decrements as the messages are sent. When dataRepeat is true, 
* messagesToSend > numMessagesMax, and at the end of the messages buffer, the messages 
* buffer wraps around and starts at the beginning of the messages buffer. When dataRepeat 
* is false, this value must be less than or equal to numMessagesMax. The worker will 
* check for this and report an error if messagesToSend is greater than numMessagesMax. 

* 
* When using pattern_v2.hdl, the messagesToSend, messagesSent, and dataSent properties should 
* be checked at the end of an app run because they won't be stable until then. The worker doesn't 
* use cdc crossing circuits for them because it takes advantage that they will have a stable value 
* by the time the control plane reads those values at the end of an app run.
*/

#include "pattern_v2-worker.hh"

using namespace OCPI::RCC;
using namespace Pattern_v2WorkerTypes;

class Pattern_v2Worker : public Pattern_v2WorkerBase {
  uint32_t dataIndex = 0;
  uint32_t messageIndex = 0;
  static const uint32_t bytesPerSample = 4;
  bool keepRepeating = false;

  RCCResult start() {
    if (properties().messagesToSend > PATTERN_V2_NUMMESSAGESMAX && properties().dataRepeat)
      keepRepeating = true;
    else
      keepRepeating = false;

    // Report an error if messagesToSend is greater than numMessagesMax when dataRepeat is false
    if (properties().messagesToSend > PATTERN_V2_NUMMESSAGESMAX && !properties().dataRepeat) {
      return setError("messagesToSend (%u) is greater than numMessagesMax (%u). When dataRepeat is false, messagesToSend must be less than or equal to numMessagesMax.", 
                       properties().messagesToSend, PATTERN_V2_NUMMESSAGESMAX);
    }
    return RCC_OK;
  }

  RCCResult run(bool /*timedout*/) {
    // If no more messages to send send an EOF
    if (properties().messagesToSend == 0) {
      out.setEOF();
      return RCC_ADVANCE_DONE;
    }

    uint32_t *odata = (uint32_t*)out.data();
    size_t bytes  = (size_t)properties().messages[messageIndex][0];
    RCCOpCode opcode = properties().messages[messageIndex][1];
    out.setInfo(opcode, bytes);
    // Set the output port data
    for (uint32_t i = ((uint32_t)bytes)/bytesPerSample; i; --i) {
      *odata++ = properties().data[dataIndex];
      properties().dataSent++;
      if (dataIndex < PATTERN_V2_NUMDATAWORDS-1)
        dataIndex++;
    }
    
    properties().messagesSent++;
    properties().messagesToSend--;

    // Wrap around to beggining of messages buffer if keep repeating is true
    if (keepRepeating && messageIndex ==  PATTERN_V2_NUMMESSAGESMAX-1)
      messageIndex = 0;
    else
      messageIndex++;

    if (properties().dataRepeat)
      dataIndex = 0;

    return RCC_ADVANCE; 
  }
};

PATTERN_V2_START_INFO
// Insert any static info assignments here (memSize, memSizes, portInfo)
// e.g.: info.memSize = sizeof(MyMemoryStruct);
PATTERN_V2_END_INFO
