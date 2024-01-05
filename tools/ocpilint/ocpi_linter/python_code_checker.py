#!/usr/bin/env python3

# Runs code checks on Python source code files
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

"""Standard Python tests to run against ocpi projects."""

import pathlib
import re
import subprocess
import pydocstyle
import logging

from . import base_code_checker
from . import utilities


class PythonCodeCheckerDefaults(base_code_checker.BaseCodeCheckerDefaults):
    """Default settings for PythonCodeChecker class."""
    license_notice = (open(pathlib.Path(__file__).parent.
                           joinpath("license_notices").joinpath("python.txt"), "r")
                      .read())
    maximum_line_length = 79
    comment_maximum_line_length = 79
    autopep8_other_options = []
    pycodestyle_other_options = []


class PythonCodeChecker(base_code_checker.BaseCodeChecker):
    """Code formatter and checker for Python."""
    checker_settings = PythonCodeCheckerDefaults

    @staticmethod
    def get_supported_file_extensions():
        """Return a list of file extension this code checker supports.

        Returns:
            List of file extensions
        """
        return [".py"]

    def test_py_000(self):
        """Run AutoPEP8 on code.

        **Test name:** AutoPEP8

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "AutoPEP8"

        if not self._check_installed("autopep8"):
            issues = [{"line": None,
                       "message": "AutoPEP8 not installed. Cannot run test."}]
        else:
            before_code = list(self._code)
            # Option -i means in-place so updates the file
            # Option --exit-code means return 2 if file was changed
            # Option --max-line-length allows custom line length limit
            process = subprocess.Popen(
                ["autopep8", "-i",
                    "--max-line-length", f"{self.checker_settings.maximum_line_length}",
                    "--exit-code",
                 ] + self.checker_settings.autopep8_other_options
                + [self.path])
            process.wait()

            # As file may have changed re-read in code
            self._read_in_code()

            if process.returncode == 0:
                issues = []  # No issues found
            elif process.returncode == 2:
                # Code was reformatted
                line_number = 0
                for i, (l1, l2) in enumerate(zip(before_code, self._code)):
                    if l1 != l2:
                        line_number = i+1
                        break
                issues = [{"line": line_number,
                           "message": "File was reformatted by AutoPEP8."}]
            else:
                issues = [{"line": None,
                           "message": "Error running AutoPEP8."}]
        return test_name, issues

    def test_py_001(self):
        """Run PyCodeStyle on code.

        **Test name:** PyCodeStyle

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "PyCodeStyle"

        if self._check_installed("pycodestyle"):
            process = subprocess.Popen([
                "pycodestyle",
                "--max-line-length", f"{self.checker_settings.maximum_line_length}",
                "--max-doc-length", f"{self.checker_settings.comment_maximum_line_length}",
            ] + self.checker_settings.pycodestyle_other_options
                + [self.path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
            process.wait()
            standard_out = process.communicate()[0]
            pycodestyle_issues = standard_out.decode("utf-8").split("\n")[:-1]

            issues = []
            for issue in pycodestyle_issues:
                if issue.count(":") > 3:
                    line_number = issue.split(":")[1]
                    message = issue.split(":", 2)[2]
                    issues.append({"line": line_number, "message": message})

        else:
            issues = [
                {"line": None,
                 "message": "PyCodeStyle not installed. Cannot run test."}]

        return test_name, issues

    def test_py_002(self):
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

        # Top line must be hash-bang
        if not self._code[0] == "#!/usr/bin/env python3":
            issues.append({
                "line": 1,
                "message": "Python 3 hashbang (#!/usr/bin/env python3) "
                           + "not on first line of file."})

        # Blank line must follow hash-bang
        if self._code[1] != "":
            issues.append({
                "line": 2,
                "message": "Blank line must follow hash-bang."})

        # Introduction sentence
        line_number = 2
        while (self._code[line_number][:1] == "#") and (
                len(self._code[line_number]) > 2):
            line_number = line_number + 1

        # Blank comment must follow introduction statement
        if self._code[line_number] != "#":
            issues.append({
                "line": line_number + 1,
                "message": "No blank comment line found after introduction "
                           + "sentence."})
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

    def test_py_003(self):
        """Check only double quotation marks are used.

        **Test name:** Double quotation marks

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "Double quotation marks"
        issues = []

        try:
            reduced_code = self._remove_comments_and_strings(
                "\"\"\"", "\"\"\"", "#")
        except base_code_checker.ParseWarning as e:
            issues.append({"line": e.line_number, "message": e.message})
            reduced_code = []

        for line_number, line_text in enumerate(reduced_code):
            if "'" in line_text:
                issues.append({
                    "line": line_number + 1,
                    "message": "Uses single quotation mark, double should be "
                               + "used."})

        return test_name, issues

    def test_py_004(self):
        """Check the complex literal is not used.

        **Test name:** No complex literal

        The ``complex()`` function rather than the complex literal ``j`` must
        be used, since there are some small differences in how negative zero
        is handled between each case.

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "No complex literal"

        reduced_code = self._remove_comments_and_strings("\"\"\"", "\"\"\"",
                                                         "#")
        issues = []
        for line_number, line_text in enumerate(reduced_code):
            if bool(re.search("\\d+\\.?j", line_text)):
                issues.append({
                    "line": line_number + 1,
                    "message": "Uses complex literal (i.e. j). Complex "
                               + "function, not complex literal, must be used "
                               + "for declaring complex values."})

        return test_name, issues

    def test_py_005(self):
        """Docstring checker test.

        Returns:
            tuple: tuple of test name, and dictionary of any issues.
        """
        test_name = "Python function docstrings"
        issues = []
        logging.getLogger("pydocstyle.utils").setLevel("WARN")
        issue = pydocstyle.check(filenames=[str(self.path)], select=list(
                                 pydocstyle.conventions["google"]))
        for i in issue:
            if hasattr(i, "message"):
                issues.append({
                    "line": getattr(i, "line", 0),
                    "message": getattr(i, "message")
                })
        return test_name, issues
