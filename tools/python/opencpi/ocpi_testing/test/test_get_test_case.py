#!/usr/bin/env python3

# Test code in get_test_case.py
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


import pathlib
import unittest
import unittest.mock

import ocpi_testing


class TestGetTestCase(unittest.TestCase):
    def test_get_test_case_from_input_string_at_start(self):
        self.assertEqual("case01.02",
                         ocpi_testing.get_test_case("case01.02.input"))

    def test_get_test_case_from_input_string_as_path(self):
        test_string = str(pathlib.Path.cwd().joinpath("case01.02.input"))
        self.assertEqual("case01.02",
                         ocpi_testing.get_test_case(test_string))

    def test_get_test_case_from_sys_arguments(self):
        with unittest.mock.patch("sys.argv",
                                 ["script_name.py", "case02.03.input"]):
            self.assertEqual("case02.03",
                             ocpi_testing.get_test_case())

    def test_get_test_case_invalid_string(self):
        with self.assertRaises(ValueError):
            ocpi_testing.get_test_case("String_without_test_case")
