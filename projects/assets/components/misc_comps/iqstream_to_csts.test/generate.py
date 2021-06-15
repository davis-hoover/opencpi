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

from argparse import ArgumentParser
import sys
import os.path
import numpy as np
import array
import opencpi.unit_test_utils as utu
import opencpi.iqstream_utils as iqm

def main():
    parser = ArgumentParser(
        description='Use this script to validate your output data against your '
        'input data.')
    parser.add_argument('output_file', help='output file to be read by file_read')
    args = parser.parse_args()
 
    # from arguments to generate.py (-test.xml)
    #max_bytes_in = int(os.environ.get("OCPI_TEST_ocpi_max_bytes_in")) # UNDOCUMENTED / SUBJECT TO CHANGE

    # Generate enough samples to generate number_of_samples_messages max_bytes_in sized input messages
    number_of_samples_messages = 1
    bytes_per_sample = 4
    num_samples_to_generate = 2048 // 4 # number_of_samples_messages * max_bytes_in // bytes_per_sample

    # Create ramp from 0 to num-samples-1
    ramp = np.arange(num_samples_to_generate)

    # Initialize empty array, sized to store interleaved I/Q 16bit samples
    out_data = np.array(np.zeros(len(ramp)), dtype=utu.dt_iq_pair)

    # Put ramp in generated output
    out_data['real_idx'] = np.int16(ramp)
    out_data['imag_idx'] = -np.int16(ramp)

    # Write to file
    with open(args.output_file, 'wb') as f:
        iqm.add_samples(f, out_data, 1, int(num_samples_to_generate))

if __name__ == "__main__":
    main()
