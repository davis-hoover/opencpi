#!/usr/bin/env python3

# Test code in rst_code_checker.py
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

from ocpilint.ocpi_linter.rst_code_checker import RstCodeChecker
from ocpilint.ocpi_linter.linter_settings import LinterSettings


class TestRstCodeChecker(unittest.TestCase):
    def setUp(self):
        self.test_file_path = pathlib.Path("test_file.rst")
        self.test_file_path.touch()
        self.test_settings = LinterSettings()

        self.test_checker = RstCodeChecker(
            self.test_file_path, self.test_settings)

    def tearDown(self):
        if self.test_file_path.is_file():
            os.remove(self.test_file_path)

    expected_copyright = """.. This file is protected by Copyright. Please refer to the COPYRIGHT file
   distributed with this source distribution.

   This file is part of OpenCPI <http://www.opencpi.org>

   OpenCPI is free software: you can redistribute it and/or modify it under the
   terms of the GNU Lesser General Public License as published by the Free
   Software Foundation, either version 3 of the License, or (at your option) any
   later version.

   OpenCPI is distributed in the hope that it will be useful, but WITHOUT ANY
   WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
   A PARTICULAR PURPOSE. See the GNU Lesser General Public License for
   more details.

   You should have received a copy of the GNU Lesser General Public License
   along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

    def test_rst_empty(self):
        code_sample = ""
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = RstCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        results = code_checker.lint()

        # Check an empty file fails lint without raising an exception
        self.assertGreater(len(results), 0)

    # Functionality of linter test 000 is not tested here since test000 is
    # reserved for automatic formatting. None currently implemented
    # for reStructuredText.

    def test_rst_001_pass(self):
        code_sample = (
            ".. Brief description\n" +
            "\n" +
            self.expected_copyright +
            "\n" +
            "This would be the start of the main file.")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = RstCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_rst_001()

        self.assertEqual([], issues)

    def test_rst_001_fail_no_header(self):
        code_sample = "A single line of text"
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = RstCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_rst_001()

        self.assertEqual(1, len(issues))

    def test_rst_001_fail_license_notice_typo(self):
        code_sample = (
            ".. Brief description\n" +
            "\n" +
            self.expected_copyright.replace("at your option",
                                            "at yor option") +
            "\n" +
            "This would be the start of the main file.")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = RstCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_rst_001()

        self.assertEqual(1, len(issues))
        self.assertEqual(10, issues[0]["line"])

    def test_rst_001_fail_no_blank_line_after_header(self):
        code_sample = (
            ".. Brief description\n" +
            "\n" +
            self.expected_copyright +
            "This would be the start of the main file.\n" +
            "Another line here.\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = RstCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_rst_001()

        self.assertEqual(1, len(issues))
        self.assertEqual(20, issues[0]["line"])

    def test_rst_002_pass_star_list(self):
        code_sample = ("Introducing a list:\n" +
                       "\n" +
                       " * A list item.\n" +
                       "\n" +
                       " * Another list item.\n" +
                       "\n" +
                       " * A third list item.\n" +
                       "\n" +
                       "    * A nested list item.\n" +
                       "\n"
                       "Then something that isn't a list.\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = RstCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_rst_002()

        self.assertEqual([], issues)

    def test_rst_002_pass_dash_list(self):
        code_sample = ("Introducing a list:\n" +
                       "\n" +
                       " - A list item.\n" +
                       "\n" +
                       " - Another list item.\n" +
                       "\n" +
                       " - A third list item.\n" +
                       "\n" +
                       "    - A nested list item.\n" +
                       "\n"
                       "Then something that isn't a list.\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = RstCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_rst_002()

        self.assertEqual([], issues)

    def test_rst_002_pass_auto_numbered_list(self):
        code_sample = ("Introducing a list:\n" +
                       "\n" +
                       " #. A list item.\n" +
                       "\n" +
                       " #. Another list item.\n" +
                       "\n" +
                       " #. A third list item.\n" +
                       "\n" +
                       "     #. A nested list item.\n" +
                       "\n"
                       "Then something that isn't a list.\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = RstCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_rst_002()

        self.assertEqual([], issues)

    def test_rst_002_pass_manually_numbered_list(self):
        code_sample = ("Introducing a list:\n" +
                       "\n" +
                       " 1. A list item.\n" +
                       "\n" +
                       " 2. Another list item.\n" +
                       "\n" +
                       " 3. A third list item.\n" +
                       "\n" +
                       "     1. A nested list item.\n" +
                       "\n"
                       "Then something that isn't a list.\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = RstCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_rst_002()

        self.assertEqual([], issues)

    def test_rst_002_fail(self):
        code_sample = ("Introducing a list:\n" +
                       "\n" +
                       " * A list item.\n" +
                       " * Another list item.\n" +
                       " * A third list item.\n" +
                       "\n" +
                       "    * A nested list item.\n" +
                       "\n"
                       "Then something that isn't a list.\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = RstCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_rst_002()

        self.assertEqual(3, len(issues))
        self.assertEqual(3, issues[0]["line"])
        self.assertEqual(4, issues[1]["line"])
        self.assertEqual(5, issues[2]["line"])

    def test_rst_003_pass(self):
        code_sample = (
            "Some title\n" +
            "==========\n" +
            "Some text after the title.\n"
            "\n" +
            "Also a table as these have similar elements to underlines.\n" +
            "\n" +
            "+----------+----------+\n" +
            "| Column 1 | Column 2 |\n" +
            "+==========+==========+\n" +
            "| Word     | Word     |\n" +
            "+----------+----------+\n" +
            "| Word     | Word     |\n" +
            "+----------+----------+\n" +
            "\n" +
            "A line of text.\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = RstCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_rst_003()

        self.assertEqual([], issues)

    def test_rst_003_fail_line_too_long(self):
        code_sample = ("Some title\n" +
                       "===========\n" +
                       "Some text after the title.\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = RstCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_rst_003()

        self.assertEqual(1, len(issues))
        self.assertEqual(2, issues[0]["line"])

    def test_rst_003_fail_line_too_short(self):
        code_sample = ("Some title\n" +
                       "=========\n" +
                       "Some text after the title.\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = RstCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_rst_003()

        self.assertEqual(1, len(issues))
        self.assertEqual(2, issues[0]["line"])
