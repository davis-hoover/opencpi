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
iqstream Utils

Commonly used functions and definitions used in the generation and verification
unit test scripts of workers using the iqstream protocol

Note: There is an internal ticket (AV-5545) to standardize and auto-generate 
helper functions for each protocol, so this file should be considered temporary
"""

import numpy as np
import opencpi.unit_test_utils as utu

SAMPLES_OPCODE = 0

def parse_samples_data_from_msgs_in_file(file_to_be_parsed):
    """
    Return samples data from file generated with messagesInFile=true in an 
    array of type dt_iq_pair
    """
    #Read data as uint32
    f = open(file_to_be_parsed, 'rb')
    data = np.fromfile(f, dtype=np.uint32, count=-1)
    f.close()
    #Parse messages
    index = 0
    msg_count = 0
    msg = []
    samples_data_array = []
    while index < len(data):
        msg.append(utu.get_msg(data[index:]))
        #print(msg[msg_count])
        if msg[msg_count][utu.MESSAGE_DATA] is None:
            index = index + 2
        else:
            index = index + len(msg[msg_count][utu.MESSAGE_DATA]) + 2
        msg_count += 1
    for i in range(0,len(msg)):
        if(msg[i][utu.MESSAGE_OPCODE]==SAMPLES_OPCODE):
            if(msg[i][utu.MESSAGE_LENGTH] != 0):
                samples_data_array.extend(msg[i][utu.MESSAGE_DATA])
    return np.array(samples_data_array, dtype=utu.dt_iq_pair)

def parse_msgs_from_msgs_in_file(file_to_be_parsed):
    """
    Get messages (data) from file generated 
    with messagesInFile=true
    """
    #Read data as uint32
    f = open(file_to_be_parsed, 'rb')
    data = np.fromfile(f, dtype=np.uint32, count=-1)
    f.close()
    #Parse messages
    index = 0
    msg_count = 0
    msg = []
    msg_array = []
    while index < len(data):
        msg.append(utu.get_msg(data[index:]))
        if msg[msg_count][utu.MESSAGE_DATA] is None:
            index = index + 2
        else:
            index = index + len(msg[msg_count][utu.MESSAGE_DATA]) + 2
        msg_count += 1
    for i in range(0,len(msg)):
        msg_array.append(msg[i])
    return msg_array

def add_samples(f, data, num_cycles,samples_per_message):
    """
    Write samples message data and metadata to a file in messagesInFile=true format
    with a specified message size. Data can be added num_cycles number of times
    """
    for i in range(num_cycles):
        a = 0
        while a < len(data):
            if len(data) - a < samples_per_message:
                utu.add_msg(f, SAMPLES_OPCODE, data[a:len(data)])
            else:
                utu.add_msg(f, SAMPLES_OPCODE, data[a:a+samples_per_message])
            a+=samples_per_message

