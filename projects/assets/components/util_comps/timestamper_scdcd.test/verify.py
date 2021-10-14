#!/usr/bin/env python3

"""
Use this script to validate your output data against your input data.
Args: <list-of-user-defined-args> <output-file> <input-files>
"""

import sys
import os.path
import numpy as np
import opencpi.unit_test_utils as utu
import opencpi.complexshortwithmetadata_utils as iqm

def do_fail(msg):
    print("    FAILED:", msg)
    exit(1)

def do_pass(msg):
    print("    PASS:", msg)

def test_expected(val, exp_val, descr):
    if(val != exp_val):
        tmp = " did not match expected value: "
        do_fail(descr + " value of " + str(val) + tmp + str(exp_val))

def get_total_num_samps(msgs):
    ret = 0
    for msg in msgs:
        if(msg[utu.MESSAGE_OPCODE] == iqm.SAMPLES_OPCODE):
            ret += len(msg[utu.MESSAGE_DATA])
    return ret

input_filename = sys.argv[2]
output_filename = sys.argv[1]

max_bytes_in = int(os.environ.get("OCPI_TEST_ocpi_max_bytes_in")) # UNDOCUMENTED / SUBJECT TO CHANGE
msgs = iqm.parse_msgs_from_msgs_in_file(output_filename )

vv = "OCPI_TEST_samples_per_timestamp"
samples_per_timestamp = int(os.environ.get(vv))
bypass = os.environ.get("OCPI_TEST_bypass") == "true"

if(bypass):
    bytes_per_sample = 4
    total_num_in_samps = max_bytes_in // bytes_per_sample
    total_num_out_samps = get_total_num_samps(msgs)
    tmp1 = "for bypass mode, total number of input samples ("
    tmp1 += str(total_num_in_samps)
    tmp2 = "the total number of output samples ("
    tmp2 += str(total_num_out_samps)
    if(total_num_in_samps == total_num_out_samps):
        do_pass(tmp1 + ") matched " + tmp2 + ")")
    else:
        do_fail(tmp1 + ") did not match " + tmp2 + ")")
    exit(0)

msg_idx = 0
expected_i = 0
expected_q = 0
first = True
num_samples_per_timestamp = 0
num_samples_msgs = 0
num_time_msgs = 0
num_sync_msgs = 0
for msg in msgs:
    if(msg[utu.MESSAGE_OPCODE] == iqm.TIME_OPCODE):
        num_time_msgs += 1
        if(not first):
            if(num_samples_per_timestamp < samples_per_timestamp):
                tmp = "num_samples_per_timestamp (" + str(num_samples_per_timestamp)
                tmp += ") was less than samples_per_timestamp ("
                tmp += str(samples_per_timestamp) + ")"
                do_fail(tmp)
            tmp = " "
            if(num_samples_per_timestamp == 1):
                tmp += "sample"
            else:
                tmp += "samples"
            tmp += " per timestamp"
            do_pass("received " + str(num_samples_per_timestamp) + tmp)
            num_samples_per_timestamp = 0
        first=False
    if(msg[utu.MESSAGE_OPCODE] == iqm.SAMPLES_OPCODE):
        num_samples_msgs += 1
        if not msg[utu.MESSAGE_LENGTH] > 0:
            do_fail("Empty message: Invalid message length: SAMPLES msg[%d]" \
              % (num_samples_msgs - 1))
        for sample in msg[utu.MESSAGE_DATA]:
            ii = int((sample & 0xffff))
            qq = int((sample & 0xffff0000) >> 16)
            if(qq > 32767):
                qq = qq - 65536
            test_expected(ii, expected_i, "I")
            test_expected(qq, expected_q, "Q")
            expected_i += 1 # positive ramp
            expected_q -= 1 # negative ramp
            num_samples_per_timestamp += 1
    if(msg[utu.MESSAGE_OPCODE] == iqm.SYNC_OPCODE):
        num_sync_msgs += 1
    msg_idx += 1

if(num_samples_msgs < 1):
    do_fail("at least one SAMPLES messages expected, but received 0")
else:
    do_pass(str(num_samples_msgs) + " SAMPLES messages received")
if(num_time_msgs < 1):
    do_fail("at least one TIME messages expected, but received 0")
else:
    do_pass(str(num_samples_msgs) + " TIME messages received")
do_pass("all I values matched positive ramp function")
do_pass("all Q values matched negative ramp function")
if(num_sync_msgs == 1):
    do_pass(str(num_sync_msgs) + " SYNC messages received")
else:
    tmp = "exactly one SYNC messages expected, but received "
    do_fail(tmp + str(num_sync_msgs))

exit(0)
