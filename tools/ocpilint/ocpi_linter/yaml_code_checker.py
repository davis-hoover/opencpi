#!/usr/bin/env python3

# Runs code checks on Yaml files
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

"""Standard YAML tests to run against ocpi projects."""

import pathlib

from . import base_code_checker
from . import utilities


class YamlCodeCheckerDefaults(base_code_checker.BaseCodeCheckerDefaults):
    """Default settings for YamlCodeChecker class."""
    license_notice = (open(pathlib.Path(__file__).parent
                           .joinpath("license_notices")
                           .joinpath("python.txt"), "r")
                      .read())


class YamlCodeChecker(base_code_checker.BaseCodeChecker):
    """Code formatter and checker for YAML."""
    checker_settings = YamlCodeCheckerDefaults

    @staticmethod
    def get_supported_file_extensions():
        """Return a list of file extension this code checker supports.

        Returns:
            List of file extensions
        """
        return [".yml", ".yaml"]

    def test_yaml_000(self):
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
                       "message": "File is not large enough to include " +
                                  "license notice."}]
            return test_name, issues

        if not self._code[0].startswith("#"):
            issues.append({"line": 1,
                           "message": "Must be brief description."})

        if self._code[1] != "#":
            issues.append({"line": 2,
                           "message": "Must be blank comment line."})

        # License notice
        line_number = 2
        if (len(self._code) - line_number <
                self.checker_settings.license_notice.count("\n")):
            issues.append({
                "line": None,
                "message": "File does not contain the expected" +
                           " license notice."})
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

    def test_yaml_001(self):
        """Check there is a single space after the comment symbol.

        **Test name:** Comment space

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "Comment space"

        issues = []
        for line_number, line_text in enumerate(self._code):
            comment_start = line_text.find("#")
            # If does not contain a comment ignore line
            if comment_start == -1:
                continue
            # If nothing after the comment "#", the line can be ignored from
            # further checks as comment without value after is allowed
            if len(line_text) - comment_start <= 1:
                continue
            if line_text[comment_start + 1] != " ":
                # Ignore lines which are all comment symbols
                if all([char is "#" for char in line_text[comment_start:-1]]):
                    continue
                issues.append({
                    "line": line_number + 1,
                    "message": "No space after comment flag (\"#\")."})
        return test_name, issues

    def test_yaml_002(self):
        """Check comment lines do not exceed maximum characters.

        **Test name:** Comments line length

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "Comments line length"

        issues = []
        for line_number, line_text in enumerate(self._code):
            if line_text.lstrip().startswith("#"):
                max_length = self.checker_settings.comment_maximum_line_length
                if len(line_text) > max_length:
                    issues.append({
                        "line": line_number + 1,
                        "message": "Comment lines must not exceed length "
                                   + f"limit ({max_length} characters)."})

        return test_name, issues
