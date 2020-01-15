#!/usr/bin/env python3.4

"""
Use this script to validate your output data against your input data.
Args: <list-of-user-defined-args> <output-file> <input-files>
"""

import sys
import numpy as np
import opencpi.complexshortwithmetadata_utils as in_utils
import opencpi.iqstream_utils as out_utils

odata = out_utils.parse_samples_data_from_msgs_in_file(sys.argv[1])
idata = in_utils.parse_samples_data_from_msgs_in_file(sys.argv[2])

ss = "equal all samples in output file"
if np.array_equal(idata,odata):
    print("    PASS: as expected, all samples in input file", ss)
else:
    print("    FAILED: unexpected - all samples in input file equal did NOT",
          ss, "num input samples =", len(idata), "num output samples =",
          len(odata))
    exit(1)

exit(0)
