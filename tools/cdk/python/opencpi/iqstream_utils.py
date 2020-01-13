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

