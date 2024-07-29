#!/usr/bin/env python3

# Test code in base_code_checker.py
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

from ocpilint.ocpi_linter.base_code_checker import BaseCodeChecker
from ocpilint.ocpi_linter.linter_settings import LinterSettings
from ocpilint.ocpi_linter.test_result import LintTestResult


class ACodeChecker(BaseCodeChecker):
    """Simple code checker used to test base class."""

    def test_000(self):
        """A failing test."""
        return "Test name 000", [
            {"line": 0, "message": "An issue"},
            {"line": 123, "message": "Another issue"}
        ]

    def test_001(self):
        """A passing test."""
        return "Test name 001", []


class TestBaseCodeChecker(unittest.TestCase):
    def setUp(self):
        self.test_file_path = pathlib.Path("test_file.cc")
        self.test_file_path.touch()
        self.linter_settings = LinterSettings()

        self.test_checker = ACodeChecker(
            self.test_file_path, self.linter_settings)

    def tearDown(self):
        os.remove(self.test_file_path)

    def test_lint(self):
        lint_result = self.test_checker.lint()

        result_000 = lint_result["000"]
        result_001 = lint_result["001"]

        self.assertTrue(result_000.has_failed)
        self.assertTrue(result_001.has_passed)

    def test_check_installed_true(self):
        self.assertTrue(self.test_checker._check_installed("python3"))

    def test_check_installed_false(self):
        print("\nTesting will print an error to the terminal. Safe to ignore.")
        self.assertFalse(self.test_checker._check_installed("some_program"))
