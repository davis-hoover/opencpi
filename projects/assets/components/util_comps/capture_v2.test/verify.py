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
Use this script to validate the data captured by the Capture_v2 worker.
"""

import os.path
import re
import sys
import numpy as np
import verify_funcs


if len(sys.argv) != 3:
    print ("Don't run this script manually, it is called by 'ocpidev test' or 'make test'")
    sys.exit(1)

stopOnFull = os.environ.get("OCPI_TEST_stopOnFull")

propsname = os.path.splitext(sys.argv[1])[0]
propsname = os.path.splitext(propsname)[0] + ".props"

max_bytes = 16384

# Do some parsing to grab the final values of the properties
ofile = open(propsname, 'r')
lines = ofile.read()
ofile.close()
obj1 = re.search(r'capture_v2 metadataCount (\w+)', lines)
obj2 = re.search(r'capture_v2 dataCount (\w+)', lines)
obj3 = re.search(r'capture_v2 metaFull (\w+)', lines)
obj4 = re.search(r'capture_v2 dataFull (\w+)', lines)
obj5 = re.search(r'capture_v2 totalBytes (\w+)', lines)
obj6 = re.search(r'\bcapture_v2 metadata\b', lines)
obj7 = re.search(r'\bcapture_v2 data\b', lines)
obj8 = re.search("capture_v2 ocpi_debug", lines)
metadata =  [int(x) for x in lines[obj6.end()+1:obj7.start()-1].replace("{", "").replace("}", "").split(',')]
# u4 is uint32 and setting it to little endian with "<"
dt = np.dtype('<u4')
odata = np.array(lines[obj7.end()+1:obj8.start()-1].split(','), dtype=dt)

metadataCount = int(obj1.group(1))
dataCount = int(obj2.group(1))
numRecords = int(os.environ.get("OCPI_TEST_numRecords"))
numDataWords = int(os.environ.get("OCPI_TEST_numDataWords"))
metaFull = obj3.group(1)
dataFull = obj4.group(1)
totalBytes = int(obj5.group(1))
stopOnZLM = os.environ.get("OCPI_TEST_stopOnZLM")
stopZLMOpcode = int(os.environ.get("OCPI_TEST_stopZLMOpcode"))
stopOnEOF = os.environ.get("OCPI_TEST_stopOnEOF")
testScenario = int(os.environ.get("OCPI_TEST_testScenario"))

print ("    stopOnFull: " + stopOnFull)
print ("    totalBytes: " + str(totalBytes))
print ("    metadataCount: " + str(metadataCount))
print ("    dataCount: " + str(dataCount))
print ("    numRecords: " + str(numRecords))
print ("    numDataWords: " + str(numDataWords))
print ("    metaFull: " + metaFull)
print ("    dataFull: " + dataFull)
print ("    stopOnZLM: " + stopOnZLM)
print ("    stopZLMOpcode: " + str(stopZLMOpcode))
print ("    stopOnEOF: " + stopOnEOF)
print ("    testScenario: " + str(testScenario))


# Check if the metadataCount matches the expected metadataCount
# Check if the dataCount matches the expected dataCount
# Check if the status (metaFull and dataFull) matches the expeceted status
# Check if the metadata words, message size and opcode, are correct. Also check
# if eom and som fraction timestamps are non-zero and are incrementing
# Check if data is correct
# Check if totalBytes is correct

if testScenario in [1,2,3,4,5]:
    verify_funcs.verify_metadataCount(testScenario, metadataCount, numRecords)
    verify_funcs.verify_dataCount(testScenario, dataCount, numDataWords, metadataCount, numRecords, stopOnFull)
    verify_funcs.verify_status(metaFull, dataFull, dataCount, numDataWords,metadataCount, numRecords)
    verify_funcs.verify_metadata(testScenario, metadata, metadataCount, stopZLMOpcode, max_bytes)
    verify_funcs.verify_data(testScenario, odata, dataCount, numDataWords, numRecords, stopOnFull)
    verify_funcs.verify_totalBytes(testScenario, totalBytes, numDataWords, numRecords)
else:
    print("Invalid test scenario: valid test scenarios are 1, 2, 3, 4 and 5")
    sys.exit(1)

print ("    Data matched expected results")
