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
This script checks the status of the FS740 GPS Time and Frequency System
"""
import sys

try:
    import vxi11
except ImportError:
    # To be replaced in 2.0 with proper Python dependencies
    # Recommended way to use pip within a program (but not best practice)
    # https://pip.pypa.io/en/latest/user_guide/#using-pip-from-your-program
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--user', 'python-vxi11'])
    import os
    os.execv(__file__, sys.argv)

# There are issues the Instrument class cleaning up properly 
# https://github.com/python-ivi/python-usbtmc/issues/44
def clean_exit(instrument_obj, err):
    instrument_obj.close()
    sys.exit(err)
    
if len(sys.argv) != 2:
    print("Invalid arguments: usage is: FS740_GPS_Freq_Ref_Status.py <ip-address-of-fs740>")
    sys.exit(1)

gps_freq_ref = vxi11.Instrument(sys.argv[1])
gps_freq_ref.timeout = 10

gps_freq_ref_status = gps_freq_ref.ask("STATus:GPS:CONDition?")

# Status bits are set when the receiver is not propertly locked
# 0 means no status bits are set. 64 indicates that position data has not been
# stored yet, which is not problematic for this use case
if gps_freq_ref_status != "0" and gps_freq_ref_status != "64":
    print("Unexpected GPS status register value: " + gps_freq_ref_status)
    clean_exit(gps_freq_ref, 2)

clean_exit(gps_freq_ref, 0)
