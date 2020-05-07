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
import sys
import numpy as np
import opencpi.unit_test_utils as utu
import opencpi.complexshortwithmetadata_utils as in_utils
import opencpi.iqstream_utils as out_utils

def test_input_samples_equal_output_samples(args):
    odata = out_utils.parse_samples_data_from_msgs_in_file(args.out_file)
    idata = in_utils.parse_samples_data_from_msgs_in_file(args.in_file)

    ss = "equal all samples in output file"
    if np.array_equal(idata,odata):
        print("    PASS: as expected, all samples in input file", ss)
    else:
        print("    FAILED: unexpected - all samples in input file equal did NOT",
              ss, "num input samples =", len(idata), "num output samples =",
              len(odata))
        exit(1)

def main():
    utu.print_cmd_and_args()
    parser = utu.ArgumentParser(
        description='Use this script to validate your output data against your '
        'input data.')
    parser.add_port_argument('out', 'output')
    parser.add_port_argument('in', 'input')
    args = parser.parse_args()
    test_input_samples_equal_output_samples(args)

if __name__ == "__main__":
    main()
