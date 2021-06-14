#!/usr/bin/env python3

# Get test case name from string
#
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
# A PARTICULAR PURPOSE. See the GNU Lesser General Public License for
# more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


import re
import sys


def get_test_case(case_containing_string=None):
    """ Get the test case ID

    Either pass a string which contains the case, or when no argument is passed
    the first argument (after the called script name) will be searched for a
    test case ID.

    The first argument can be used for when test verification is occurring, as
    when a verification script is called the first argument is the output data
    path which in the default case will start with a test case ID.

    The case IDs are in the format ``caseXX.YY``, where ``XX`` and ``YY`` are
    numbers with at least two digits.

    Args:
        case_containing_string (str, optional): If set will search string for a
            sub-string of the format case00.00 (where 00.00 is any pair of two
            digit numbers). If not set will attempt to use the first argument
            to find a string which looks like the case. If the string contains
            more than one case the first will be returned.

    Returns:
        String which is the found case. Will error if cannot find case string.
    """
    # No environment variables or other ways have been identified at run time
    # so using the path of the output data file is supported.

    if case_containing_string is None:
        search_string = sys.argv[1]
    else:
        search_string = case_containing_string

    case_results = re.findall("case\\d\\d+\\.\\d\\d+", search_string)
    if len(case_results) > 0:
        return case_results[0]
    else:
        raise ValueError("get_test_case() cannot find case string in " +
                         f"{search_string}")
