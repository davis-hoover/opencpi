#!/usr/bin/env python3

# Test code in any_code_checker.py
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

from ocpilint.ocpi_linter.any_code_checker import AnyCodeChecker
from ocpilint.ocpi_linter.linter_settings import LinterSettings


class TestAnyCodeChecker(unittest.TestCase):
    def setUp(self):
        self.test_file_path = pathlib.Path("test_file.any")
        self.test_file_path.touch()
        self.test_settings = LinterSettings()

    def tearDown(self):
        if self.test_file_path.is_file():
            os.remove(self.test_file_path)

    def test_any_empty(self):
        code_sample = ""
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = AnyCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        results = code_checker.lint()

        # Check an empty file fails lint without raising an exception
        self.assertGreater(len(results), 0)

    def test_any_000_pass(self):
        code_sample = ("This is a line of text\n" +
                       "\n" +
                       "Another line.\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = AnyCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_any_000()

        self.assertEqual([], issues)

    def test_any_000_fail(self):
        code_sample = ("This is a line of text\n" +
                       "\n" +
                       "Another line, but now has a space at the end \n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = AnyCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_any_000()

        self.assertEqual(1, len(issues))
        self.assertEqual(3, issues[0]["line"])

    def test_any_001_pass(self):
        code_sample = ("This is a line of text\n" +
                       "\n" +
                       "Another line.\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = AnyCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_any_001()

        self.assertEqual([], issues)

    def test_any_001_fail(self):
        # LINT EXCEPTION: any_001: 3: Need to include pattern to cause failure
        code_sample = ("This is a line of text\n" +
                       "\n" +
                       "Skeleton line: Another line\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = AnyCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_any_001()

        self.assertEqual(1, len(issues))
        self.assertEqual(3, issues[0]["line"])

    def test_any_002_pass(self):
        code_sample = ("This is a line of text\n" +
                       "\n" +
                       "Another line.\n" +
                       "Consecutive text.\n" +
                       "\n" +
                       "\n" +
                       "That was two blank lines.")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = AnyCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_any_002()

        self.assertEqual([], issues)

    def test_any_002_fail(self):
        code_sample = ("This is a line of text\n" +
                       "\n" +
                       "Another line.\n" +
                       "Consecutive text.\n" +
                       "\n" +
                       "\n" +
                       "That was two blank lines.\n" +
                       "\n" +
                       "\n" +
                       "\n" +
                       "That was three blank lines.")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = AnyCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_any_002()

        self.assertEqual(1, len(issues))
        self.assertEqual(10, issues[0]["line"])

    def test_any_003_pass(self):
        code_sample = ("This is a line of text\n" +
                       "\n" +
                       "Another line.\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = AnyCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_any_003()

        self.assertEqual([], issues)

    def test_any_003_fail_no_line(self):
        code_sample = ("This is a line of text\n" +
                       "\n" +
                       "Another line.")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = AnyCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_any_003()

        self.assertEqual(1, len(issues))
        self.assertEqual(3, issues[0]["line"])

    def test_any_003_fail_too_many_lines(self):
        code_sample = ("This is a line of text\n" +
                       "\n" +
                       "Another line.\n" +
                       "\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = AnyCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_any_003()

        self.assertEqual(1, len(issues))
        self.assertEqual(5, issues[0]["line"])

    def test_any_004_pass(self):
        code_sample = ("This is a line of text\n" +
                       "\n" +
                       "    Another line, but indented.\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = AnyCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_any_004()

        self.assertEqual([], issues)

    def test_any_004_fail_tab_at_start(self):
        code_sample = ("This is a line of text\n" +
                       "\n" +
                       "\tAnother line.")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = AnyCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_any_004()

        self.assertEqual(1, len(issues))
        self.assertEqual(3, issues[0]["line"])

    def test_any_004_fail_tab_mid_line(self):
        code_sample = ("This is a line of text\n" +
                       "\n" +
                       "    Another line. \t # Perhaps a comment")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = AnyCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_any_004()

        self.assertEqual(1, len(issues))
        self.assertEqual(3, issues[0]["line"])
