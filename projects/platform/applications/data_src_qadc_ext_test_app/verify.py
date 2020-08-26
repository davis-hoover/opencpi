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
Downsample: Verify output data

Output is verified by downsampling input data in python and comparing to actual 
output data
"""
import sys
import os.path
import numpy as np
import opencpi.unit_test_utils as utu
import opencpi.complexshortwithmetadata_utils as iqm

num_expected_diffs = 0
# left shift because dev signal port is MSB-justified and
# ADC_INPUT_IS_LSB_OF_OUT_PORT=false
expected_diff = (np.left_shift(1, 4))

msgs = iqm.parse_msgs_from_msgs_in_file('case00.00.out')
for msg in msgs:
    if(msg[utu.MESSAGE_OPCODE] == iqm.SAMPLES_OPCODE):
        first = True
        for sample in msg[utu.MESSAGE_DATA]:
            # take only magnitude bits from 12-bit value sign-extended to 16-bit
            # value
            i_or_q = sample & 0x7ff
            print(i_or_q)
            if((not first) and (i_or_q != 0)):
                diff = i_or_q - last_i_or_q
                if(diff != expected_diff):
                    msg1 = "ERROR: sample-to-sample diff was"
                    msg2 = "instead of" + expected_diff + "(I or Q value was"
                    print(msg1, diff, msg2, i_or_q, ")")
                    exit(1)
                else:
                    num_expected_diffs += 1
            last_i_or_q = i_or_q
            first = False

if(num_expected_diffs == 0):
    print("ERROR: 1 or more messages with 2 or more samples is expected in",
          "order to perform first backwards diff verification for ramp input")
    exit(1)
print("num_expected_diffs =", num_expected_diffs)
print("num_unexpected_diffs = 0")

exit(0)
