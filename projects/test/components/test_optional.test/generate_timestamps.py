#!/usr/bin/env python3
"""
Generate a string for both ports samples_in and timestamps_in
Use is generate.py <case> <output-file>:
"""

import sys
import os.path
import struct

if len(sys.argv) != 2:
    print("Invalid arguments:  usage is: generate.py <output-file>")
    sys.exit(1)
filename=sys.argv[1]
f=open(filename, 'wb')
f.write(struct.pack("I", 0)) # length
f.close()
