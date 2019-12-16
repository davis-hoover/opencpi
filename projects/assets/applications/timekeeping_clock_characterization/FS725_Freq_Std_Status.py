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
This script checks the status of the FS725 Frequency Standard
"""
import sys

try:
    import serial
except ImportError:
    # To be replaced in 2.0 with proper Python dependencies
    # Recommended way to use pip within a program (but not best practice)
    # https://pip.pypa.io/en/latest/user_guide/#using-pip-from-your-program
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--user', 'pyserial'])
    import os
    os.execv(__file__, sys.argv)

if len(sys.argv) != 2:
    print("Invalid arguments: usage is: FS725_Freq_Std_Status.py <serial-port>")
    sys.exit(1)

with serial.Serial(sys.argv[1], 9600, timeout=1) as ser:
    # Check ID string from FS725
    # The FS725 uses the rubidium oscillator SRS model PRS10
    ser.write(b'ID? \r') #expected output: PRS10_3.24_SN_47043
    if ser.readline().decode().split('_')[0] != "PRS10" :
        sys.exit(2)

    # Check external PPS 
    # There are 5 status bytes in the FS725. 
    # The 5th status byte related to Frequency Lock to External 1pps
    # A value of 4 indicates a valid PPS input. Any other value indicates an error
    ser.write(b'ST? \r') #expected output: 0,0,0,0,4,0
    if ser.readline().decode().split(',')[4] != "4":
        sys.exit(3)
