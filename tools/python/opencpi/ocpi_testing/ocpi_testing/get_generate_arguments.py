#!/usr/bin/env python3

# Input argument handling for component testing generate scripts
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


import argparse
import pathlib

from .generator.base_generator import BaseGenerator


def get_generate_arguments(custom_cases=None):
    """ Handle arguments for generate scripts used in component unit testing

    Args:
        custom_cases (``list``, optional): If a custom generator is
            used, this defines additional test cases. If not set, or set to
            ``None`` will use the default test cases as the allowed set of test
            cases.

    Returns:
        A named tuple of the input arguments.
    """
    parser = argparse.ArgumentParser(
        description="Component unit testing input port message generation")
    cases = list(BaseGenerator().CASES.keys())
    if custom_cases is not None:
        # Convert to set to ensure unique elements
        cases = set(cases + custom_cases)
    parser.add_argument("-c", "--case", type=str, choices=cases,
                        required=True, help="Set the test case type name.")
    parser.add_argument("-s", "--seed", type=int, default=0, required=False,
                        help="Optional argument to pass seed value to " +
                             "generate script")
    parser.add_argument("save_path", type=str,
                        help="File path to save input test port messages to.")

    arguments = parser.parse_args()

    case = pathlib.Path(arguments.save_path).stem
    if case.startswith("case"):
        case_number = case[4:].split(".")[0]
        subcase_number = case[4:].split(".", 1)[1]
    else:
        case_number = case
        subcase_number = "00"
    # setattr is used as this is added but the current code interface needs to
    # be kept
    setattr(arguments, "case_number", case_number)
    setattr(arguments, "subcase_number", subcase_number)

    return arguments
