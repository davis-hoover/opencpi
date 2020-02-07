#!/usr/bin/env python3.4
import sys
import os.path
import numpy as np
import opencpi.unit_test_utils as utu
import opencpi.complexshortwithmetadata_utils as iqm

output_filename = sys.argv[1]
msgs = iqm.parse_msgs_from_msgs_in_file(output_filename )

msg_idx = 0
for msg in msgs:
    print("msg_idx:", msg_idx, ",opcode =", msg[utu.MESSAGE_OPCODE])
    msg_idx += 1
