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
Data Sink DAC: Verify output data

Output is verified by:
1. Checking for underrun. It is expected when dac_clk_freq_hz > SDP_CLK_FREQ
2. Comparing input and output data. Data should be the same when underrun
   hasn't occurred
"""
import sys
import os.path
import numpy as np
import opencpi.unit_test_utils as utu
import opencpi.complexshortwithmetadata_utils as iqm

if len(sys.argv) != 3:
    print("Invalid arguments:  usage is: verify.py <output-file> <input-file>")
    sys.exit(1)

# from OCS or OWD
DAC_WIDTH_BITS=int(os.environ.get("OCPI_TEST_DAC_WIDTH_BITS"))
DAC_OUTPUT_IS_LSB_OF_IN_PORT=os.environ.get("OCPI_TEST_DAC_OUTPUT_IS_LSB_OF_IN_PORT")
dac_clk_freq_hz=int(os.environ.get("OCPI_TEST_dac_clk_freq_hz"))
underrun_sticky_error=os.environ.get("OCPI_TEST_underrun_sticky_error")
num_input_samples = int(os.environ.get("OCPI_TEST_num_input_samples"))
samp_count_before_first_underrun=int(os.environ.get("OCPI_TEST_samp_count_before_first_underrun"))
num_underruns=int(os.environ.get("OCPI_TEST_num_underruns"))

SDP_CLK_FREQ=100e6

if ((dac_clk_freq_hz > SDP_CLK_FREQ) or (samp_count_before_first_underrun == num_input_samples and  num_underruns == 1)):
    if underrun_sticky_error == "true":
        print("    Expected underrun detected")
    else:
        print("    ERROR: Expected underrun not detected")
        sys.exit(2)
else:
    if underrun_sticky_error  == "true":
        print("    ERROR: Unexpected underrun detected")
        sys.exit(3)

# parse output file as complex samples
odata = np.fromfile(sys.argv[1], dtype=utu.dt_iq_pair, count=-1)

# parse input file as complex samples
idata = np.fromfile(sys.argv[2], dtype=utu.dt_iq_pair, count=-1)

#Compare expected output to actual output
bitshift = iqm.SAMPLES_BIT_WIDTH - DAC_WIDTH_BITS
if DAC_OUTPUT_IS_LSB_OF_IN_PORT == "true":
    print("    Comparing Expected Real (I, In-Phase) data to Actual Real (I, In-Phase) Data")
    utu.compare_arrays(np.left_shift(idata['real_idx'],bitshift), odata['real_idx'])
    print("    Comparing Expected Imaginary (Q, Quadrature) data to Actual Imaginary (Q, Quadrature) Data")
    utu.compare_arrays(np.left_shift(idata['imag_idx'],bitshift), odata['imag_idx'])
else:
    print("    Comparing Expected Real (I, In-Phase) data to Actual Real (I, In-Phase) Data")
    utu.compare_arrays(np.right_shift(idata['real_idx'],bitshift), np.right_shift(odata['real_idx'],bitshift))
    print("    Comparing Expected Imaginary (Q, Quadrature) data to Actual Imaginary (Q, Quadrature) Data")
    utu.compare_arrays(np.right_shift(idata['imag_idx'],bitshift), np.right_shift(odata['imag_idx'],bitshift))
