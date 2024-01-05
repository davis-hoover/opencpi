#!/usr/bin/env python3

# Runs style checks on reStructuredText files
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

"""Standard ReStructuredTest tests to run against ocpi projects."""

import pathlib
import re

from . import base_code_checker
from . import utilities


class RstCodeCheckerDefaults(base_code_checker.BaseCodeCheckerDefaults):
    """Default settings for RstCodeChecker class."""
    license_notice = (open(pathlib.Path(__file__).parent
                           .joinpath("license_notices").joinpath("rst.txt"), "r")
                      .read())
    underline_symbols = ["=", "-", ":", "'", "\"", "~", "^", "_", "*", "+",
                         "#", "<", ">"]


class RstCodeChecker(base_code_checker.BaseCodeChecker):
    """Style checker for reStructuredText."""
    checker_settings = RstCodeCheckerDefaults

    @staticmethod
    def get_supported_file_extensions():
        """Return a list of file extension this code checker supports.

        Returns:
            List of file extensions
        """
        return [".rst", ".inc"]

    # test000 is reserved for automatic formatting. None currently implemented
    # for reStructuredText.

    def test_rst_001(self):
        """Check the first lines in file are in the correct format.

        **Test name:** Correct opening lines

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "Correct opening lines"

        issues = []

        if len(self._code) < self.minimum_number_of_lines:
            issues = [{"line": None,
                       "message": "File is not large enough to include license notice."}]
            return test_name, issues

        line_number = 0

        # First line must be an opening comment
        if self._code[line_number][0:3] != ".. ":
            issues.append({
                "line": 1,
                "message": "First line of file must be comment which is brief "
                           + "description of file."})

        # Move past multi line opening comment
        line_number = 1
        while (self._code[line_number][0:3] == ".. ") or (
                self._code[line_number][0:3] == "   "):
            line_number = line_number + 1

        # Blank line before license statement
        if self._code[line_number] != "":
            issues.append({
                "line": line_number + 1,
                "message": "Must be a blank line between opening description "
                           + "and copyright statement."})
        line_number = line_number + 1

        # License notice
        if (len(self._code) - line_number) < self.checker_settings.license_notice.count("\n"):
            issues.append({
                "line": None,
                "message": "File does not contain the expected license notice."})
            return test_name, issues

        for license_line in self.checker_settings.license_notice.splitlines():
            if self._code[line_number] != license_line:
                issues.append({
                    "line": line_number + 1,
                    "message": "License notice is incorrect, should be \""
                    + license_line + "\"."})
            line_number = line_number + 1

        # Blank line
        if self._code[line_number] != "":
            issues.append({
                "line": line_number + 1,
                "message": "Blank line does not follow license notice."})

        return test_name, issues

    def test_rst_002(self):
        """Blank lines about list items.

        **Test name:** Blank lines about list items

        All lists (bullet points and number) must have a blank line before and
        after each list element.

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "Blank lines about list items"

        issues = []
        for line_number, line_text in enumerate(self._code[:-1]):
            # Match for zero or more white-space (\*s) followed by:
            #     - An asterisk (\*), or
            #     - A hyphen (\-), or
            #     - A hash symbol followed by a dot (\#\.), or
            #     - A number followed by a dot (\d+\.)
            # Followed by one more spaces (\s+)
            # This match pattern should be a bullet point list of numbered list
            if (re.match(r"\s*(\*|\-|(\#\.)|(\d+\.))\s+", line_text)
                    is not None):
                # Before start and each list item the line must be blank
                if not self._code[line_number - 1] == "":
                    issues.append({
                        "line": line_number + 1,
                        "message": "Bullet point and numbered lists must have "
                                   + "a blank line before them and between "
                                   + "all list entries."})
                # Must end with blank line or not be end of list
                elif not self._code[line_number + 1] == "":
                    issues.append({
                        "line": line_number + 1,
                        "message": "Bullet point and numbered lists must have "
                                   + "a blank line before them and between "
                                   + "all list entries."})

        return test_name, issues

    def test_rst_003(self):
        """Ensure underlines are of correct length.

        **Test name:** Underline length

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "Underline length"

        issues = []
        for line_number, line_text in enumerate(self._code):
            if line_text != "":
                # Check if an underline by seeing if all characters in a line
                # are the same and an allowed underline symbol
                if line_text[0] in self.checker_settings.underline_symbols and all(
                        [character == line_text[0] for
                         character in line_text[1:]]):
                    if len(line_text) != len(self._code[line_number - 1]):
                        issues.append({
                            "line": line_number + 1,
                            "message": "Underlines must be the same length as "
                                       "the text on the previous line."})

        return test_name, issues
