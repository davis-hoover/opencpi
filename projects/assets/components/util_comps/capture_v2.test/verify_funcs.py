#!/usr/bin/env python3
# This file is protected by Copyright. Please refer to the COPYRIGHT file
# distributed with this source distribution.
#
# This file is part of OpenCPI <http://www.opencpi.org>
#
# OpenCPI is free software: you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# OpenCPI is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.

"""
This script defines the functions used to validate the data captured by the Capture worker and used
by the verify.py script.
"""

import sys
import numpy as np

# For testScenario 1
def verify_metadataCount1(metadataCount):
    # Because no messages were sent, metadataCount should be 0
    if metadataCount != 0:
        print ("    metadataCount is", metadataCount,  "while expected value is 0")
        sys.exit(1)
    else:
        print ("    metadataCount is correct")

# For testScenario 2 and 4
def verify_metadataCount2(metadataCount, numRecords):
    # metadataCount should be numRecords because made metadata full
    if metadataCount != numRecords:
        print ("    metadataCount is", metadataCount,  "while expected value is", numRecords)
        sys.exit(1)
    else:
        print ("    metadataCount is correct")

# For testScenario 3
def verify_metadataCount3(metadataCount):
    # metadataCount should be 3 because 3 messages are sent in this scenario
    if metadataCount != 3:
        print ("    metadataCount is", metadataCount,  "while expected value is 3")
        sys.exit(1)
    else:
        print ("    metadataCount is correct")


# For testScenario 5
def verify_metadataCount4(metadataCount):
    # Only one ZLM was sent so metadataCount should be 1
    if metadataCount != 1:
        print ("    metadataCount is", metadataCount,  "while expected value is 1")
        sys.exit(1)
    else:
        print ("    metadataCount is correct")

# For testScenario 1, 2, and 5
def verify_dataCount1(dataCount):
    # dataCount should be 0 since no data sent in these scenarios
    if dataCount != 0:
        print ("    dataCount is", dataCount,  "while expected value is 0")
        sys.exit(1)
    else:
        print ("    dataCount is correct")

# For testScenario 3
def verify_dataCount2(dataCount, numDataWords, stopOnFull):
    if stopOnFull == "false":
        # This scenario sends numDataWords+1 amount of data, so dataCount should be numDataWords+1 when stopOnFull is false
        if dataCount != numDataWords+1:
            print ("    dataCount is", dataCount,  "while expected value is", numDataWords+1)
            sys.exit(1)
        else:
            print ("    dataCount is correct")
    elif stopOnFull == "true":
        # For this scenario dataCount should be numDataWords when stopOnFull is true
        if dataCount != numDataWords:
            print ("    dataCount is", dataCount,  "while expected value is", numDataWords)
            sys.exit(1)
        else:
            print ("    dataCount is correct")

# For testScenario 4
def verify_dataCount3(dataCount, numDataWords, metadataCount, numRecords,stopOnFull):
    if stopOnFull == "false":
        # In this scenario, numDataWords amount of data is sent and then numRecords-6 amount of data is sent.
        # So when stopOnFull is true, dataCount should be numDataWords+numRecords-6
        if dataCount != numDataWords+numRecords-6:
            print ("    dataCount is", dataCount,  "while expected value is", numDataWords+numRecords-6)
            sys.exit(1)
        else:
            print ("    dataCount is correct")
    elif stopOnFull == "true":
        # For this scenario dataCount should be numDataWords when stopOnFull is true
        if dataCount != numDataWords:
            print ("    dataCount is", dataCount,  "while expected value is", numDataWords)
            sys.exit(1)
        else:
            print ("    dataCount is correct")

# For all testScenario
def verify_status(metaFull, dataFull, dataCount, numDataWords,metadataCount, numRecords):
    # Neither data or metadata are full
    if (dataCount < numDataWords and metadataCount < numRecords):
        if (metaFull != "false" or dataFull != "false"):
            print ("    metaFull and dataFull are " + metaFull + " and " + dataFull + " while expected values are false and false")
            sys.exit(1)
        else:
            print ("    status is correct")
    # Only metadata is full
    elif (metadataCount >= numRecords and dataCount < numDataWords):
        if (metaFull != "true" or dataFull != "false"):
            print ("    metaFull and dataFull are " + metaFull + " and " + dataFull + " while expected values are true and false")
            sys.exit(1)
        else:
            print ("    status is correct")
    # Only data is full
    elif (dataCount >= numDataWords and metadataCount < numRecords):
        if (metaFull != "false" or dataFull != "true"):
            print ("    metaFull and dataFull are " + metaFull + " and " + dataFull + " while expected values are false and true")
            sys.exit(1)
        else:
            print ("    status is correct")
    # Both data and metadata are full
    elif (dataCount >= numDataWords and metadataCount >= numRecords):
        if (metaFull != "true" or dataFull != "true"):
            print ("    metaFull and dataFull are " + metaFull + " and " + dataFull + " while expected values are true and true")
            sys.exit(1)
        else:
            print ("    status is correct")


# For testScenario 2
def verify_metadata1(metadata, metadataCount):
    # Multiplying metadataCount by 4 because there are 4 metadata words
    stop = 4*metadataCount
    for x in range(0, stop, 4):
        opcode = (metadata[x] & 0xFF000000) >> 24
        messageSize = (metadata[x] & 0x00FFFFFF)
        eom_fraction = metadata[x+1]
        som_fraction = metadata[x+2]
        som_seconds = metadata[x+3]
        # Check that timestamps are non-zero
        if eom_fraction == 0:
                print ("    For metadata record " + str((x//4)+1) + ", eom fraction time stamp is 0" )
                sys.exit(1)
        elif som_fraction == 0:
            print ("    For metadata record " + str((x//4)+1) + ", som fraction time stamp is 0")
            sys.exit(1)

        # All the messages sent were ZLMs of opcode 32, so message size should be 0 and opcode should be 32
        if opcode != 32:
            print ("    opcode is not correct")
            print ("    For metadata record " + str((x//4)+1) + ", ocpode is", opcode, "while expected value is 32")
            sys.exit(1)
        elif messageSize != 0:
            print ("    message size is not correct")
            print ("    For metadata record " + str((x//4)+1) +  ", message size is", messageSize, "while expected value is 0")
            sys.exit(1)
    print ("    metadata is correct")

# For testScenario 3
def verify_metadata2(metadata, max_bytes):
    # Only sending 3 messages so check only 3 of the records
    stop = 4*3
    for x in range(0, stop, 4):
        opcode = (metadata[x] & 0xFF000000) >> 24
        messageSize = (metadata[x] & 0x00FFFFFF)
        eom_fraction = metadata[x+1]
        som_fraction = metadata[x+2]
        som_seconds = metadata[x+3]
        # Check that timestamps are non-zero
        if eom_fraction == 0:
            print ("    For metadata record " + str((x//4)+1) + ", eom fraction time stamp is 0" )
            sys.exit(1)
        elif som_fraction == 0:
            print ("    For metadata record " + str((x//4)+1) + ", som fraction time stamp is 0")
            sys.exit(1)
        if (x == 0 or x == 4):
            # For this scenario when stopOnFull is true, the first and second metadata record's
            # message size should be max_bytes and opcode should be 255
            if opcode != 255:
                print ("    opcode is not correct")
                print ("    For metadata record " + str((x//4)+1) + ", ocpode is", opcode, "while expected value is 255")
                sys.exit(1)
            elif messageSize != max_bytes:
                print ("    message size is not correct")
                print ("    For metadata record " + str((x//4)+1) +  ", message size is", messageSize, "while expected value is", max_bytes)
                sys.exit(1)
        elif x == 8:
            if opcode != 255:
                print ("    opcode is not correct")
                print ("    For metadata record " + str((x//4)+1) + ", ocpode is", opcode, "while expected value is 255")
                sys.exit(1)
            elif messageSize != 4:
                print ("    message size is not correct")
                print ("    For metadata record " + str((x//4)+1) +  ", message size is", messageSize, "while expected value is 4")
                sys.exit(1)
    print ("    metadata is correct")

# For testScenario 4
def verify_metadata3(metadata, metadataCount, max_bytes):
    stop = 4*(metadataCount)
    for x in range(0, stop, 4):
        opcode = (metadata[x] & 0xFF000000) >> 24
        messageSize = (metadata[x] & 0x00FFFFFF)
        eom_fraction = metadata[x+1]
        som_fraction = metadata[x+2]
        som_seconds = metadata[x+3]
        # Check that timestamps are non-zero
        if eom_fraction == 0:
            print ("    For metadata record " + str((x//4)+1) + ", eom fraction time stamp is 0" )
            sys.exit(1)
        elif som_fraction == 0:
            print ("    For metadata record " + str((x//4)+1) + ", som fraction time stamp is 0")
            sys.exit(1)

        if x == 0:
            # The first metadata record should contain opcode of 1 and messageSize of 0 bytes
            if opcode != 1:
                print ("    opcode is not correct")
                print ("    For metadata record " + str((x//4)+1) +  ", ocpode is", opcode, "while expected value is 1")
                sys.exit(1)
            elif messageSize != 0:
                print ("    message size is not correct")
                print ("    For metadata record " + str((x//4)+1) +  ", message size is", messageSize, "while expected value is 0")
                sys.exit(1)
        elif x == 4:
            # The second metadata record should contain opcode of 2 and messageSize of 0 bytes
            if opcode != 2:
                print ("    opcode is not correct")
                print ("    For metadata record " + str((x//4)+1) +  ", ocpode is", opcode, "while expected value is 2")
                sys.exit(1)
            elif messageSize != 0:
                print ("    message size is not correct")
                print ("    For metadata record " + str((x//4)+1) +  ", message size is", messageSize, "while expected value is 0")
                sys.exit(1)
        elif x == 8:
            # The third metadata record should contain opcode of 3 and messageSize of 4 bytes
            if opcode != 3:
                print ("    opcode is not correct")
                print ("    For metadata record " + str((x//4)+1) +  ", ocpode is", opcode, "while expected value is 3")
                sys.exit(1)
            elif messageSize != 4:
                print ("    message size is not correct")
                print ("    For metadata record " + str((x//4)+1) +  ", message size is", messageSize, "while expected value is 4")
                sys.exit(1)
        elif x == 12:
            # The fourth metadata record should contain opcode of 0 and messageSize of max_bytes-4
            if opcode != 0:
                print ("    opcode is not correct")
                print ("    For metadata record " + str((x//4)+1) +  ", ocpode is", opcode, "while expected value is 0")
                sys.exit(1)
            elif messageSize != max_bytes-4:
                print ("    message size is not correct")
                print ("    For metadata record " + str((x//4)+1) +  ", message size is", messageSize, "while expected value is", max_bytes-4)
                sys.exit(1)
        elif x == 16:
            # The fifth metadata record should contain opcode of 0 and messageSize of max_bytes
            if opcode != 0:
                print ("    opcode is not correct")
                print ("    For metadata record " + str((x//4)+1) +  ", ocpode is", opcode, "while expected value is 0")
                sys.exit(1)
            elif messageSize != max_bytes:
                print ("    message size is not correct")
                print ("    For metadata record " + str((x//4)+1) +  ", message size is", messageSize, "while expected value is", max_bytes)
                sys.exit(1)
        elif x == 20:
            # The sixth metadata record should contain opcode of 4 and messageSize of 0 bytes
            if opcode != 4:
                print ("    opcode is not correct")
                print ("    For metadata record " + str((x//4)+1) +  ", ocpode is", opcode, "while expected value is 4")
                sys.exit(1)
            elif messageSize != 0:
                print ("    message size is not correct")
                print ("    For metadata record " + str((x//4)+1) +  ", message size is", messageSize, "while expected value is 0")
                sys.exit(1)
        elif x >= 24:
            # The other metadata records should contain opcode of 0 and messageSize of 4 bytes
            if opcode != 0:
                print ("    opcode is not correct")
                print ("    For metadata record " + str((x//4)+1) +  ", ocpode is", opcode, "while expected value is 0")
                sys.exit(1)
            elif messageSize != 4:
                print ("    message size is not correct")
                print ("    For metadata record " + str((x//4)+1) +  ", message size is", messageSize, "while expected value is 4")
                sys.exit(1)
    print ("    metadata is correct")

# For testScenario 5
def verify_metadata4(metadata, stopZLMOpcode):
    opcode = (metadata[0] & 0xFF000000) >> 24
    messageSize = (metadata[0] & 0x00FFFFFF)
    eom_fraction = metadata[1]
    som_fraction = metadata[2]

    # opcode should be stopZLMOpcode and message size should be 0
    if opcode != stopZLMOpcode:
        print ("    opcode is not correct")
        print ("    For metadata record 1, ocpode is", opcode, "while expected value is",  stopZLMOpcode)
        sys.exit(1)
    elif messageSize != 0:
        print ("    Message size is not correct")
        print ("    For metadata record 1, message size is", messageSize, "while expected value is 0")
        sys.exit(1)
    # Check that timestamps are non-zero
    elif eom_fraction == 0:
            print ("    For metadata record 1, eom fraction time stamp is 0")
            sys.exit(1)
    elif som_fraction == 0:
        print ("    For metadata record 1, som fraction time stamp is 0")
        sys.exit(1)
    print   ("    metadata is correct")

# For testScenario 3
def verify_data1(odata, dataCount, numDataWords, stopOnFull):
    # u4 is uint32 and setting it to little endian with "<"
    dt = np.dtype('<u4')
    idata = np.empty(numDataWords, dtype=dt)
    if stopOnFull == "true":
        for x in range(0, dataCount):
            idata[x] = x
    elif stopOnFull == "false":
        idata[0] = numDataWords
        for x in range(1, dataCount-1):
            idata[x] = x
    if np.array_equal(idata, odata):
        print ("    Input data and property data match")
    else:
        print ("    Input data and property data don't match")
        sys.exit(1)

# For testScenario 4
def verify_data2(odata, stopOnFull, numDataWords, numRecords):
    # u4 is uint32 and setting it to little endian with "<"
    dt = np.dtype('<u4')
    idata = np.empty(numDataWords, dtype=dt)
    if stopOnFull == "false":
        i = 0
        for x in range(numDataWords, numDataWords+numRecords-6):
            idata[i] = x
            i = i + 1
        for x in range(numDataWords+numRecords-6-numDataWords, numDataWords):
            idata[i] = x
            i = i + 1
    elif stopOnFull == "true":
        for x in range(0, numDataWords):
            idata[x] = x

    if np.array_equal(idata, odata):
        print ("    Input data and property data match")
    else:
        print ("    Input data and property data don't match")
        sys.exit(1)


def verify_metadataCount(testScenario, metadataCount, numRecords):
    if testScenario == 1:
        verify_metadataCount1(metadataCount)
    elif testScenario == 2:
        verify_metadataCount2(metadataCount, numRecords)
    elif testScenario == 3:
        verify_metadataCount3(metadataCount)
    elif testScenario == 4:
        verify_metadataCount2(metadataCount, numRecords)
    elif testScenario == 5:
        verify_metadataCount4(metadataCount)

def verify_dataCount(testScenario, dataCount, numDataWords, metadataCount, numRecords, stopOnFull):
    if testScenario == 1:
        verify_dataCount1(dataCount)
    elif testScenario == 2:
        verify_dataCount1(dataCount)
    elif testScenario == 3:
        verify_dataCount2(dataCount,numDataWords, stopOnFull)
    elif testScenario == 4:
        verify_dataCount3(dataCount,numDataWords, metadataCount, numRecords,stopOnFull)
    elif testScenario == 5:
        verify_dataCount1(dataCount)

def verify_metadata(testScenario, metadata, metadataCount, stopZLMOpcode, max_bytes):
    if testScenario == 2:
        verify_metadata1(metadata,metadataCount)
    elif testScenario == 3:
        verify_metadata2(metadata, max_bytes)
    elif testScenario == 4:
        verify_metadata3(metadata,metadataCount, max_bytes)
    elif testScenario == 5:
        verify_metadata4(metadata, stopZLMOpcode)

def verify_data(testScenario, odata, dataCount, numDataWords, numRecords, stopOnFull):
    if testScenario == 3:
        verify_data1(odata, dataCount, numDataWords, stopOnFull)
    elif testScenario == 4:
        verify_data2(odata, stopOnFull, numDataWords,numRecords)
        
def verify_totalBytes(testScenario, totalBytes, numDataWords, numRecords):
    if (testScenario == 1 or testScenario == 2 or testScenario == 5):
        if totalBytes == 0:
            print ("    totalBytes is correct")
        else:
            print ("    totalBytes is", totalBytes,  "while expected value is 0")
            sys.exit(1)
    elif testScenario == 3:
        if totalBytes == (numDataWords+1)*4:
            print ("    totalBytes is correct")
        else:
            print ("    totalBytes is", totalBytes,  "while expected value is", (numDataWords+1)*4)
            sys.exit(1)
    elif testScenario == 4:
        if totalBytes ==  (numDataWords+numRecords-6)*4:
            print ("    totalBytes is correct")
        else:
            print ("    totalBytes is", totalBytes,  "while expected value is", (numDataWords+numRecords-6)*4)
            sys.exit(1)