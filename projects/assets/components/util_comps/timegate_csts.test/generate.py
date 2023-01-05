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
Timegate_csts: Generate test input data 

Generate args: 
 - target file

To test timegate_csts component a messages file is generated with one timestamp and 
sample data. This ensures that the component can process the complex short time
sample timestamp (96 bits) correctly and eventually opens the timegate to allow sample 
data to flow to the output port. 
"""
import sys
byteorder = sys.byteorder

# Creates OCPI message headers
def add_message_header(opcode, data):
    assert type(data) == bytes

    return len(data).to_bytes(4, byteorder=byteorder, signed=False) + \
           opcode.to_bytes(4, byteorder=byteorder, signed=False) + \
           data


# Write data to a file
def to_file(file_name, messages):
    # Open output file
    with open(file_name, 'wb') as f:
        for msg in messages:
            f.write(msg)


if __name__ == '__main__':
    print("\n","*"*80)
    print("*** Python: Timegate_csts ***")

    print("*** Generate input (messages in file) ***")
    if len(sys.argv) < 2:
        print("Exit: Enter an input filename")
        sys.exit(1)

    filename = sys.argv[1]

    # Generate complex short message
    complex_short_vals = [0x1, 0x1, 0x2, 0x2, 0x3, 0x3, 0x4, 0x4]
    complex_short_samp = b''
    for x in complex_short_vals:
        complex_short_samp += x.to_bytes(4, byteorder=byteorder, signed=True)


    # Generate timestamp
    # if the gate reaches internal error state aka locking up, samples would not flow 
    seconds=0x0
    fraction_40=0x0FFFFFFFFF00000
    csts_ts = fraction_40.to_bytes(8, byteorder=byteorder, signed=False) + \
              seconds.to_bytes(4, byteorder=byteorder, signed=False) 

    # Add Message Headers
    random_data = add_message_header(0, complex_short_samp)
    valid_csts_ts = add_message_header(1, csts_ts)

    # Create message stream with four timestamps
    valid_csts_msgs = [random_data, valid_csts_ts, random_data, valid_csts_ts, random_data, valid_csts_ts, random_data, valid_csts_ts, random_data]

    # Write to file
    to_file(filename, valid_csts_msgs)
