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
Generate patterns for test_02-04. 
Use is generate.py <case> <output-file>:
"""

import sys

if len(sys.argv) != 3:
    print("Invalid arguments:  usage is: generate.py <case> <output-file>")
    sys.exit(1)
    
if int(sys.argv[1]) == 2:
    opcode_list = []
    byte_list = []
    byte_counter_00 = 1
    byte_counter_01 = 0
    BYTE_VECTOR_1 = "0, 0, 0"
    BYTE_VECTOR_2 = "10, 10, 10"
    BYTE_VECTOR_3 = "20, 20, 20"
    for x in range(0, 260, 10):
        if byte_counter_00 == 1:
            opcode_list.append(x)
            byte_list.append(BYTE_VECTOR_1)
        elif byte_counter_00 == 2:
            opcode_list.append(x)
            byte_list.append(BYTE_VECTOR_2)
        elif byte_counter_00 == 3:
            opcode_list.append(x)
            byte_list.append(BYTE_VECTOR_3)
            byte_counter_00 = 0
        byte_counter_00 = byte_counter_00 + 1
        byte_counter_01 = byte_counter_01 + 1
        if byte_counter_01 == 10:
            byte_counter_00 = 1
            byte_counter_01 = 0 
    with open(sys.argv[2], 'w') as f:
        for x in range(0, 26):
            f.write('{Opcode ')
            f.write(str(opcode_list[x]))
            f.write(', Bytes {')
            f.write(str(byte_list[x]))
            f.write('}}')
            f.write('\n')

if int(sys.argv[1]) == 3:
    opcode_list = []
    byte_list = []
    BYTE_VECTOR_1 = "0,0,0"
    BYTE_VECTOR_2 = "10,10,10"
    BYTE_VECTOR_3 = "0x14,20,0x14"
    loop_c = 1
    while loop_c <= 2:
        byte_counter_00 = 1
        byte_counter_01 = 0
        for x in range(1, 261, 10):
            if byte_counter_00 == 1:
                opcode_list.append(x)
                byte_list.append(BYTE_VECTOR_1)
            elif byte_counter_00 == 2:
                opcode_list.append(x)
                byte_list.append(BYTE_VECTOR_2)
            elif byte_counter_00 == 3:
                opcode_list.append(x)
                byte_list.append(BYTE_VECTOR_3)
                byte_counter_00 = 0
            byte_counter_00 = byte_counter_00 + 1
            byte_counter_01 = byte_counter_01 + 1
            if byte_counter_01 == 10:
                byte_counter_00 = 1
                byte_counter_01 = 0 
        loop_c += 1
    with open(sys.argv[2], 'w') as f:
        for x in range(0, 52):
            f.write('{Opcode ')
            f.write(str(opcode_list[x]))
            f.write(', Bytes {')
            f.write(str(byte_list[x]))
            f.write('}}')
            f.write('\n')

if int(sys.argv[1]) == 4:
    pattern = []
    for x in range(0, 2049):
        pattern.append(0)
    with open(sys.argv[2], 'w') as f:
        f.write('{Opcode 0, Bytes {')
        for x in range(1, 2049):
            f.write(str(pattern[x]))
            if x % 25 == 0:
                f.write('\n')
            elif x == 2048:
                f.write('}}')
                f.write('\n')
            else:
                f.write(',')
