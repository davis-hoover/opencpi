#!/usr/bin/env python3

# Test code in vhdl_code_checker.py
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


import os
import pathlib
import unittest

from ocpilint.ocpi_linter.vhdl_code_checker import VhdlCodeChecker
from ocpilint.ocpi_linter.linter_settings import LinterSettings


class TestVhdlCodeChecker(unittest.TestCase):
    def setUp(self):
        self.test_file_path = pathlib.Path("test_file.vhd")
        self.test_file_path.touch()
        self.test_settings = LinterSettings()

        self.test_checker = VhdlCodeChecker(
            self.test_file_path, self.test_settings)

    def tearDown(self):
        if self.test_file_path.is_file():
            os.remove(self.test_file_path)

    expected_copyright = """-- This file is protected by Copyright. Please refer to the COPYRIGHT file
-- distributed with this source distribution.
--
-- This file is part of OpenCPI <http://www.opencpi.org>
--
-- OpenCPI is free software: you can redistribute it and/or modify it under the
-- terms of the GNU Lesser General Public License as published by the Free
-- Software Foundation, either version 3 of the License, or (at your option) any
-- later version.
--
-- OpenCPI is distributed in the hope that it will be useful, but WITHOUT ANY
-- WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
-- A PARTICULAR PURPOSE. See the GNU Lesser General Public License for
-- more details.
--
-- You should have received a copy of the GNU Lesser General Public License
-- along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

    def test_vhdl_empty(self):
        code_sample = ""
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = VhdlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        results = code_checker.lint()

        # Check an empty file fails lint without raising an exception
        self.assertGreater(len(results), 0)

    # Functionality of linter test 000 is not tested here since this uses an
    # external code formatter and it is assumed this is tested separately.
    # Only reporting of errors is tested here.

    def test_vhdl_000_pass(self):
        code_sample = (
            "library ieee;\n" +
            "use ieee.std_logic_1164.all;\n" +
            "use ieee.numeric_std.all;\n"
        )
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = VhdlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_vhdl_000()

        self.assertEqual([], issues)

    def test_vhdl_000_fail(self):
        code_sample = (
            "library ieee;" +
            "use ieee.std_logic_1164.all;" +
            "use ieee.numeric_std.all;\n"
        )
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = VhdlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_vhdl_000()

        self.assertEqual(len(issues), 1)
        self.assertEqual(1, issues[0]["line"])

    def test_vhdl_001_pass(self):
        code_sample = (
            "-- Brief description\n" +
            "--\n" +
            self.expected_copyright +
            "\n" +
            "This would be the start of the main file.")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = VhdlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_vhdl_001()

        self.assertEqual([], issues)

    def test_vhdl_001_fail_no_header(self):
        code_sample = "A single line of text"
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = VhdlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_vhdl_001()

        self.assertEqual(1, len(issues))

    def test_vhdl_001_fail_license_notice_typo(self):
        code_sample = (
            "-- Brief description\n" +
            "--\n" +
            self.expected_copyright.replace("modify it under the",
                                            "modify ti under the") +
            "\n" +
            "This would be the start of the main file.")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = VhdlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_vhdl_001()

        self.assertEqual(1, len(issues))
        self.assertEqual(8, issues[0]["line"])

    def test_vhdl_001_fail_no_blank_line_after_header(self):
        code_sample = (
            "-- Brief description\n" +
            "--\n" +
            self.expected_copyright +
            "This would be the start of the main file.")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = VhdlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_vhdl_001()

        self.assertEqual(1, len(issues))
        self.assertEqual(20, issues[0]["line"])

    def test_vhdl_002_pass(self):
        code_sample = ("-- A comment. Formatting style below allowed.\n" +
                       "---------------------------------------------\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = VhdlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_vhdl_002()

        self.assertEqual([], issues)

    def test_vhdl_002_fail(self):
        code_sample = ("--A bad comment. Formatting style below allowed.\n" +
                       "------------------------------------------------\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = VhdlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_vhdl_002()

        self.assertEqual(1, len(issues))
        self.assertEqual(1, issues[0]["line"])

    def test_vhdl_003_pass(self):
        code_sample = ("-- A comment. Formatting style below allowed.\n" +
                       "---------------------------------------------\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = VhdlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_vhdl_003()

        self.assertEqual([], issues)

    def test_vhdl_003_fail(self):
        code_sample = (
            "    -- A valid comment line.\n" +
            "    -- A very long comment line, that exceeds the limit of 80 " +
            "characters per comment line.\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = VhdlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_vhdl_003()

        self.assertEqual(1, len(issues))
        self.assertEqual(2, issues[0]["line"])

    def test_exception(self):
        code_sample = (
            "-- Brief description\n" +
            "--\n" +
            self.expected_copyright +
            "\n" +
            "-- LINT EXCEPTION: vhdl_003: 1: All a long comment line next.\n" +
            "-- This is a comment line that needs to exceed the normal " +
            "limit of 80 characters. Note the Python version is split over " +
            "multiple lines, but there is not new line character for when " +
            "written to file during linter testing.\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = VhdlCodeChecker(self.test_file_path, self.test_settings)
        completed_tests = code_checker.lint()

        self.assertEqual(0, completed_tests["vhdl_003"].issue_count)
