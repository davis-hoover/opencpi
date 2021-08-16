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
Verify output data
"""
import sys
import os.path
import numpy as np
import opencpi.unit_test_utils as utu
import opencpi.complexshortwithmetadata_utils as iqm

if len(sys.argv) != 3:
    print("Invalid arguments:  usage is: verify.py <output-file> <input-file>")
    sys.exit(1)

# parse output file as complex samples
odata = np.fromfile(sys.argv[1], dtype=utu.dt_iq_pair, count=-1)

# parse input file as complex samples
idata = np.fromfile(sys.argv[2], dtype=utu.dt_iq_pair, count=-1)

ADC_WIDTH_BITS=int(os.environ.get("OCPI_TEST_ADC_WIDTH_BITS"))
ADC_INPUT_IS_LSB_OF_OUT_PORT=os.environ.get("OCPI_TEST_ADC_INPUT_IS_LSB_OF_OUT_PORT")
bitshift = iqm.SAMPLES_BIT_WIDTH - ADC_WIDTH_BITS
if ADC_INPUT_IS_LSB_OF_OUT_PORT == "true":
    print("    Comparing Expected I data to Actual I Data")
    utu.compare_arrays(np.right_shift(idata['real_idx'],bitshift), odata['real_idx'])
    print("    Comparing Expected Q data to Actual Q Data")
    utu.compare_arrays(np.right_shift(idata['imag_idx'],bitshift), odata['imag_idx'])
else:
    print("    Comparing Expected I data to Actual I Data")
    utu.compare_arrays(np.right_shift(idata['real_idx'],bitshift), np.right_shift(odata['real_idx'],bitshift))
    print("    Comparing Expected Q data to Actual Q Data")
    utu.compare_arrays(np.right_shift(idata['imag_idx'],bitshift), np.right_shift(odata['imag_idx'],bitshift))

