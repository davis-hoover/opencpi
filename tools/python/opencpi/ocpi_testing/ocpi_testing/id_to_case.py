#!/usr/bin/env python3

# Convert test ID / name to case and subcase
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


def id_to_case(test_id):
    """ Converts a test ID or name in case00.00 format to case and subcase

    The case00.00 format is the default used when OpenCPI has no test name set.
    If a different test_id format is detected then will return the test_id as
    the test_case and an empty string as the subcase.

    For test_id value of case01.02 then the case would be 01 and the subcase
    02.

    Args:
        test_id (str): The test ID (or name) to be searched for a test case and
            subcase.

    Returns:
        A pair of strings which are the test case and test subcase.
    """
    # IndexError means two numbers have not been found in the string, so
    # not in case00.00 format. Therefore set to defaults.
    try:
        test_case = re.findall(r"\d+", test_id)[0]
        test_subcase = re.findall(r"\d+", test_id)[1]
    except IndexError:
        test_case = test_id
        test_subcase = ""

    return test_case, test_subcase
