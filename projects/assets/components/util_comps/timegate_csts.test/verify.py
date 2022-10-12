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
Use this script to validate your output data against your input data.
Args: <list-of-user-defined-args> <output-file> <input-files>
"""

import struct
import numpy as np
import sys
import os.path

if len(sys.argv) != 3:
    print("Invalid arguments: usage is: verify.py <output-file> <input-file>")
    sys.exit(1)

# open output file and grab samples as int32
OFILENAME = open(sys.argv[1], 'rb')
odata = np.fromfile(OFILENAME, dtype=np.uint32, count=-1)
OFILENAME.close()

# test that odata has the expected length 
if len(odata) != 40:
    print("    FAILED: Output file length is unexpected")
    print("Did not receive expected samples at the output port")
    sys.exit(1)

# if we got samples through the gate the test passed
print("    PASS: timegate passed samples")
