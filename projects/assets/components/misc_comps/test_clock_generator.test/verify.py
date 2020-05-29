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

import sys
import os.path
import numpy as np

dt = np.dtype('<u4')
with open(sys.argv[2], 'rb') as f:
    idata = np.fromfile(f, dtype=dt)

with open(sys.argv[1], 'rb') as f:
    odata = np.fromfile(f, dtype=dt)

if len(odata) != len(idata):
    print("    Output file length is unexpected")
    print("    Length = ", len(odata), "while expected length is = ", len(idata))
    sys.exit(1)
else:
    print("    Input and output file lengths match")

if np.array_equal(idata, odata):
    print("    Input and output data match")
else:
    print("    Input and output data don't match")
    sys.exit(1)
