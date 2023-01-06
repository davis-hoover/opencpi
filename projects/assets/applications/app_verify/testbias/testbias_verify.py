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
This script is to be used by the pipeline to verify the testbias application ran succesfully. It simply compares the output produced by the application and a known good output (golden file). 
"""

import sys
import os.path
import filecmp
print("VERIFICATION of TESTBIAS in assets/applications")
print("------------------------------------")
if filecmp.cmp('test.output','app_verify/testbias/golden.output', shallow = False):
	print("Output matches goldenfile")
	print("------------------------------------")
	sys.exit(0)
else:
	print("Output does not match goldenfile")
	print("------------------------------------")
	sys.exit(1)
        
