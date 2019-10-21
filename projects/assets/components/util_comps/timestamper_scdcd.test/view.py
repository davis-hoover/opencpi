#!/usr/bin/env python3
import sys
import os.path
import numpy as np
import opencpi.unit_test_utils as utu
import opencpi.complexshortwithmetadata_utils as iqm

output_filename = sys.argv[1]
msgs = iqm.parse_msgs_from_msgs_in_file(output_filename )

msg_idx = 0
for msg in msgs:
    #if(msg[utu.MESSAGE_OPCODE] == iqm.TIME_OPCODE):
    #    time = (msg[utu.MESSAGE_DATA][1] << 32) + msg[utu.MESSAGE_DATA][0]
    #    print("msg_idx:", msg_idx, ", TIME =", time)
    #if(msg[utu.MESSAGE_OPCODE] == iqm.SAMPLES_OPCODE):
    #    samples = []
    #    for sample in msg[utu.MESSAGE_DATA]:
    #        ii = (msg[utu.MESSAGE_DATA] & 0xffff)[0]
    #        qq = (msg[utu.MESSAGE_DATA] & 0xffff0000) >> 16
    #        if(qq > 32767):
    #            qq = int(qq) - 65536
    #        samples.append(complex(ii, qq))
    #    print("msg_idx:", msg_idx, ",SAMPLES =", samples)
    #if(msg[utu.MESSAGE_OPCODE] == iqm.SYNC_OPCODE):
    #    print("msg_idx:", msg_idx, ",SYNC")
    print("msg_idx:", msg_idx, ",opcode =", msg[utu.MESSAGE_OPCODE])
    msg_idx += 1
