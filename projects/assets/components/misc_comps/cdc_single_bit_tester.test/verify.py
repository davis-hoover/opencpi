#!/usr/bin/env python3.4
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

import math
import numpy as np
import sys
import os.path

dt = np.dtype('<u4')

# Open input file and grab samples as uint32


with open(sys.argv[1], 'rb') as f:
    goldendata = np.fromfile(f, dtype=dt)

with open(sys.argv[2], 'rb') as f:
    odata = np.fromfile(f, dtype=dt)

# Ensure that output data is the expected amount of data
if len(odata) != len(goldendata):
    print("    Output file length is unexpected")
    print("    Length = ", len(odata), "while expected length is = ", len(goldendata))
    sys.exit(1)
else:
    print("    Golden and output file lengths match")

correlation = np.corrcoef(odata,goldendata)[1,0]
if (correlation >= 0.7):
    print("    Output data and golden data correlation is greater than or equal to 70%")
else:
    print("    Output data and golden data correlation is less than 70%")
    print("    Correlation: " + str(correlation))
    sys.exit(1)
