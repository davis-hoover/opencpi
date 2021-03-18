#!/usr/bin/env python3
# Ths file is protected by Copyright. Please refer to the COPYRIGHT file
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

import hashlib
import os.path
import re
import sys

if len(sys.argv) != 3: 
    print("Invalid arguments:  usage is: verify.py <case> <output-file>")
    sys.exit(1)

def get_hashes():
    """
    This funtion's purpose is to return OCPI variables
    as well as their md5 hashes
    """
    current = os.environ.get("OCPI_TEST_current") + "\n"
    current_hash = hashlib.md5(current.encode()).hexdigest()
    maxPatternLength = os.environ.get("OCPI_TEST_maxPatternLength") + "\n"
    maxPatternLength_hash = hashlib.md5(maxPatternLength.encode()).hexdigest()
    return [current_hash, maxPatternLength_hash]

def get_output(output_file):
    """ 
    This function is to return the output of the output file
    """
    with open(output_file, 'r') as f:
        output = f.read()
    return(output)
    
def compare_hashes(var_hash, expected_hash, out_var):
    """
    This function compares expected hashes with the hashes of either
    output, maxPatternLength, or current
    """
    if var_hash == expected_hash:
        print("   ", out_var, "hashes match \n")
        print("    Expected", out_var, "hash is: ", str(expected_hash))
        print("\n    Actual", out_var, "hash is:   ", str(var_hash))
        print("\n")
    else:
        print("   ", out_var, "hashes do not match. Exiting")
        sys.exit(1)

if int(sys.argv[1]) == 0:
    """
    Verification of Case_00, get current property, save into final
    Defaults (single ZLM on 0)
    """
    current_hash = get_hashes()[0]
    expected_current_hash = "90ae3585d1c2294c977b45fd6587854d"
    compare_hashes(current_hash, expected_current_hash, "Current")

    expected_output_hash = "d41d8cd98f00b204e9800998ecf8427e"
    output = get_output(sys.argv[2])
    output_hash = hashlib.md5(output.encode()).hexdigest()
    compare_hashes(output_hash, expected_output_hash, "Output")
    
elif int(sys.argv[1]) == 1:
    """
    Verification of Case_01, get current property and compare hashes
    Defaults (no ZLM; times out)
    """
    current_hash = get_hashes()[0]
    expected_current_hash = "65350d8636774adaadb9f6a93ddd8780"
    compare_hashes(current_hash,expected_current_hash, "Current")

elif int(sys.argv[1]) == 2:
    current_hash = get_hashes()[0] 
    expected_current_hash = "efbf60111ca74541be9384ce6d8cae0d"
    compare_hashes(current_hash, expected_current_hash, "Current")

    maxPatternLength_hash = get_hashes()[1]
    expected_maxPatternLength_hash = "26b4cb0930a3e3be4da8e9d738607427"
    compare_hashes(maxPatternLength_hash, expected_maxPatternLength_hash, "Max Pattern Length")

    hashPattern = ["693e9af84d3dfcc71e640e005bdc5e2e", "2228e977ebea8966e27929f43e39cb67", 
    "90c816cc40dc6f0bd4cd825507cc3624"]
    output = get_output(sys.argv[2])
    hashCounter = 0
    for i in range(0, len(output), 3):
        outputStr = str(output[i : i + 3])
        outputHash = hashlib.md5(outputStr.encode()).hexdigest()
        if hashCounter % 3 == 0 or hashCounter == 10:
            compare_hashes(outputHash, hashPattern[0], "Output")
            if hashCounter == 10:
                hashCounter = 0
        elif hashCounter % 3 == 1:
            compare_hashes(outputHash, hashPattern[1], "Output")
        elif hashCounter % 3 == 2:
            compare_hashes(outputHash, hashPattern[2], "Output")
        hashCounter += 1

elif int(sys.argv[1]) == 3:
    """
    Verification of Case_03
    From a value file, send three bytes to every tenth opcode fifty times,
    no ZLM (times out)
    exercising maxPatternLength=64
    """
    current_hash = get_hashes()[0]
    expected_current_hash = "852aeafceee314b8be580243d1452dc8"
    compare_hashes(current_hash, expected_current_hash, "Current")
    
    expected_maxPatternLength_hash = "9caff0735bc6e80121cedcb98ca51821"
    maxPatternLength_hash = get_hashes()[1]
    compare_hashes(maxPatternLength_hash, expected_maxPatternLength_hash, "Max Pattern Length")
    
    #The original case had 26 odata files which were the 3 bytes sent out, repeated 50 times
    expected_hash = ["87a4924b0060d1e79c729f24cd134986", "823f6bc883f64151417edbd7baccc932",
    "e4ba3f9428ccab2bb79f1738da0ca913"]
    output = get_output(sys.argv[2])
    string_c = 0 #keeps track of which 3 byte "string" the output is being written to
    pattern_c = 0 #Of 3 patterns, they repeat every 10 times
    opcode_list = ["" for i in range(26)] #store 26 output strings
    byte_list = [] #holds the 3 byte groups in a list

    for i in range(0, len(output), 3):
        output_str = str(output[i : i + 3])
        byte_list.append(output_str)
    for i in range(0, len(byte_list)):
        if string_c < 25:
            opcode_list[string_c] = opcode_list[string_c] + ''.join(byte_list[i])
            string_c += 1
        else:
            opcode_list[string_c] = opcode_list[string_c] + ''.join(byte_list[i])
            string_c = 0
    for i in range(0, 25):
        output_hash = hashlib.md5((opcode_list[i]).encode()).hexdigest()
        if pattern_c == 10:
            pattern_c = 0
        if pattern_c % 3 == 0:
            compare_hashes(output_hash, expected_hash[0],"Output")
        elif pattern_c % 3 == 1:
            compare_hashes(output_hash, expected_hash[1],"Output")
        elif pattern_c % 3 == 2:
            compare_hashes(output_hash, expected_hash[2],"Output")
        pattern_c += 1

elif int(sys.argv[1]) == 4:
    """
    Verification of Case_04
    2048 bytes from a value file, send three bytes to opcode 0 with no end, maxPatternLength=128
    """
    maxPatternLength_hash = get_hashes()[1]
    expected_maxPatternLength_hash = "650a1c9c9baa20730b4fcfdbe4cdc135"
    compare_hashes(maxPatternLength_hash, expected_maxPatternLength_hash, "Max pattern Length") 
    
    #The current.Total property will change depending on duration, need to take cut of the current.Opcode.*
    current_prop = os.environ.get("OCPI_TEST_current")
    current_str = str(re.findall("{bytes 0.*", current_prop)[0][:]) + "\n"
    expected_current_hash = "2d3d4d58dc49eb6d8f543dbf484c79ac"
    current_hash = hashlib.md5(current_str.encode())
    print("    Expected Current hash is:   ",expected_current_hash)
    print("    Actual of Current hash is: ", current_hash.hexdigest())
    if expected_current_hash == current_hash.hexdigest():
        print("    Curent hashes match")
    else:
        print("    Current hashes do not match. Exiting")
        sys.exit(1)
