#!/usr/bin/env python3

# Run code checks that are language agnostic
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

"""Standard Tests to run against all files present within ocpi projects."""

from . import base_code_checker
from . import utilities


class AnyCodeCheckerDefaults(base_code_checker.BaseCodeCheckerDefaults):
    """Default settings for AnyCodeChecker class."""
    maximum_blank_lines = 2


class AnyCodeChecker(base_code_checker.BaseCodeChecker):
    """Language agnostic format checker."""
    checker_settings = AnyCodeCheckerDefaults

    @staticmethod
    def get_ignored_file_extensions():
        """Return a list of file extension this code checker should ignore.

        Returns:
            List of file extensions
        """
        return ["Makefile", ".mk"]   # Ignore Makefiles

    def test_any_000(self):
        """No trailing white-space.

        **Test name:** No trailing white-space

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "No trailing white-space"

        issues = []
        for line_number, line_text in enumerate(self._code):
            if line_text != "":
                if line_text[-1] == " ":
                    issues.append({
                        "line": line_number + 1,
                        "message": "There should not be trailing white-space "
                                   + "on any line."})

        return test_name, issues

    def test_any_001(self):
        """Find if any default template code is present.

        **Test name:** Default code check

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "Default code check"

        issues = []
        for line_number, line_text in enumerate(self._code):
            # LINT EXCEPTION: any_001: 2: To check for the default code pattern
            # the search string needs to be included here.
            if "skeleton" in line_text.lower():
                issues.append({
                    "line": line_number + 1,
                    "message": "May be a default comment, update for " +
                               "implementation."})

        return test_name, issues

    def test_any_002(self):
        """Check there are never more than the allowed number of blank lines.

        **Test name:** Maximum blank lines

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "Max blank lines"

        issues = []
        blank_line_count = 0
        for line_number, line_text in enumerate(self._code):
            if line_text == "":
                blank_line_count = blank_line_count + 1
            else:
                blank_line_count = 0
            if blank_line_count > self.checker_settings.maximum_blank_lines:
                issues.append({
                    "line": line_number + 1,
                    "message": "Too many consecutive blank lines, limit is "
                              + f"{self.checker_settings.maximum_blank_lines}"
                              + " consecutive blank lines."})

        return test_name, issues

    def test_any_003(self):
        """Check single blank line at end of file.

        **Test name:** End of file blank line

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "End of file blank line"

        issues = []

        if len(self._code) > 1:
            if not (self._code[-1] == "" and self._code[-2] != ""):
                issues = [{
                    "line": len(self._code),
                    "message": "File must end with a single blank line."}]

        return test_name, issues

    def test_any_004(self):
        """Check spaces not tabs are used.

        **Test name:** Spaces not tabs

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "Spaces not tabs"

        issues = []
        for line_number, line_text in enumerate(self._code):
            if "\t" in line_text:
                issues.append({
                    "line": line_number + 1,
                    "message": "Spaces must be used, not tabs."})

        return test_name, issues
