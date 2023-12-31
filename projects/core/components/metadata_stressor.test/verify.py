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
Stream Meta Test: Verify output data
The metadata test worker provides non-standard stream interface behavior to test
a worker's robustness during development. It outputs valid combinations of
metadata, with an option to include delays. It can be built into a worker's unit
test HDL assembly. It passes through the data it receives without change.

This worker does not manipulate the data, but simply passes it through.
Validation of this worker, requires passing a known input data pattern
through the worker, under its various modes and comparing the input and
output files to verify that the data is unchanged.

Because this worker does not manipulate the data and validation of the
output is performed simply by comparing to the input, any non-zero input
data would be sufficient. Due to its simplicity, and usage in other unit
tests, a binary data file is generated containing complex signed 16-bit
samples with a tone at a configurable center frequency and sample
frequency.

Verify args:
1. input data file used for comparison
2. output data file to verify

Validation Tests:
#1: Not all zeros
#2: Is the expected amount
#3: Matches the input data
"""
import sys
import os.path
import opencpi.colors as color
import numpy as np


if len(sys.argv) != 3:
    print("Invalid arguments:  usage is: verify.py  <output-file> <input-file>")
    sys.exit(1)
print("    VALIDATE (binary data file):")

bypass = os.environ.get("OCPI_TEST_bypass")

# Read all output data as complex int16 samples
ofilename = open(sys.argv[1], 'rb')
odata = np.fromfile(ofilename, dtype=np.uint32, count=-1)
ofilename.close()

# Read all input data as complex int16 samples
ifilename = open(sys.argv[2], 'rb')
idata = np.fromfile(ifilename, dtype=np.uint32, count=-1)
ifilename.close()

#Test #1 - Check that output data is not all zeros
if all(odata == 0):
    print('    ' + color.RED + color.BOLD + 'FAIL, values are all zero' + color.END)
    sys.exit(1)
else:
    print('    PASS: File is not all zeros')

#Test #2 - Check that output data is the expected amount
if len(odata) != len(idata):
    print('    ' + color.RED + color.BOLD + 'FAIL, input file length is unexpected' + color.END)
    print('    ' + color.RED + color.BOLD + 'Length dout = ', len(odata), 'while expected length is = ' + color.END, len(idata))
    sys.exit(1)
else:
    print('    PASS: Input and output file lengths match')

#Test #3 - Check that output data matches the input data
if np.array_equal(idata, odata):
    print('    PASS: Input and output data files match')
else:
    print('    FAIL: Input and output data files not match')
    sys.exit(1)

print('    Data matched expected results.')
print('    ' + color.GREEN + color.BOLD + 'PASSED' + color.END)
