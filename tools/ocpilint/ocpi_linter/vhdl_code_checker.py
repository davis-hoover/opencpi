#!/usr/bin/env python3

# Runs code checks on VHDL source code files
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

"""Standard VHDL tests to run against ocpi projects."""

import pathlib
import subprocess
import re

from . import base_code_checker
from . import utilities


class VhdlCodeCheckerDefaults(base_code_checker.BaseCodeCheckerDefaults):
    """Default settings for VhdlCodeChecker class."""
    license_notice = (open(pathlib.Path(__file__).parent
                           .joinpath("license_notices").joinpath("vhdl.txt"), "r")
                      .read())


class VhdlCodeChecker(base_code_checker.BaseCodeChecker):
    """Code formatter and checker for VHDL."""
    checker_settings = VhdlCodeCheckerDefaults

    @staticmethod
    def get_supported_file_extensions():
        """Return a list of file extension this code checker supports.

        Returns:
            List of file extensions
        """
        return [".vhd"]

    def test_vhdl_000(self):
        """Run Emacs formatting on code.

        **Test name:** Emacs formatting

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "Emacs formatting"

        # Pre-process before emacs to ensure "library" and "use" vhdl
        # keywords do not occur on a single line multiple times otherwise
        # emacs will excessively indent everything
        reformat = []
        for line_text in self._code:
            end_pos = line_text.find("--")
            if end_pos == -1:
                end_pos = len(line_text) + 1
            semicolon_pos = (
                [match.start(0) for match in re.finditer(r";", line_text)])
            semicolon_pos = (
                [value for value in semicolon_pos if value < end_pos])
            keyword_count = line_text.lower().count("library", 0, end_pos)
            keyword_count += line_text.lower().count("use", 0, end_pos)
            if len(semicolon_pos) > 1 and keyword_count > 1:
                line_text = re.sub(
                    r";\s*", ";\n", line_text, len(semicolon_pos) - 1)
            reformat.append(line_text + "\n")

        # Ensure "\n" exists at the end to prevent emacs from hanging
        while reformat[-1] is "\n":
            reformat = reformat[:-1]
        if not reformat[-1].endswith("\n"):
            reformat[-1] += "\n"

        # Re-write file with changes
        with open(self.path, "w") as linted_file:
            linted_file.writelines(reformat)

        if self._check_installed("emacs"):
            before_code = list(self._code)
            emacs_lisp_file = str(pathlib.Path(__file__).parent.joinpath(
                "vhdl_format.el"))
            # As Emacs is used for formatting, what it reports the to terminal
            # can be ignored. Therefore pipe output to NULL, as Emacs prints
            # messages during formatting stderr so this is also needs to be
            # # redirected to hide these messages.
            process = subprocess.Popen([
                "emacs", "-batch", "-l", emacs_lisp_file, "--visit", self.path,
                "-f", "vhdl-format"], stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL)
            process.wait()

            # As file may have changed re-read in code
            self._read_in_code()

            # Check if reformatted
            if before_code != self._code:
                line_number = 0
                for i, (l1, l2) in enumerate(zip(before_code, self._code)):
                    if l1 != l2:
                        line_number = i+1
                        break
                return test_name, [
                    {"line": line_number,
                     "message": "File was reformatted by vhdl_format.el."}]

            return test_name, []  # Return no issues

        else:
            return test_name, [
                {"line": None,
                 "message": "Emacs not installed. Cannot run test."}]

    def test_vhdl_001(self):
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

        if self._code[0][0:2] != "--":
            issues.append({"line": 1,
                           "message": "Must be brief description."})

        if self._code[1] != "--":
            issues.append({"line": 2,
                           "message": "Must be blank comment line."})

        # License notice
        line_number = 2
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

    def test_vhdl_002(self):
        """Check there is a single space after the comment symbol.

        **Test name:** Comment space

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "Comment space"

        issues = []
        for line_number, line_text in enumerate(self._code):
            comment_start = line_text.find("--")
            # If does not contain a comment ignore line
            if comment_start == -1:
                continue
            # If nothing after the comment "--", the line can be ignored from
            # further checks as comment without value after is allowed
            if len(line_text) - comment_start <= 2:
                continue
            if line_text[comment_start + 2] != " ":
                # Ignore lines which are all comment symbols
                if all([char is "-" for char in line_text[comment_start:-1]]):
                    continue
                issues.append({
                    "line": line_number + 1,
                    "message": "No space after comment flag (\"--\")."})

        return test_name, issues

    def test_vhdl_003(self):
        """Check comment lines do not exceed maximum characters.

        **Test name:** Comments line length

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "Comments line length"

        issues = []
        for line_number, line_text in enumerate(self._code):
            if line_text.lstrip()[0:2] == "--":
                max_length = self.checker_settings.comment_maximum_line_length
                if len(line_text) > max_length:
                    issues.append({
                        "line": line_number + 1,
                        "message": "Comment lines must not exceed length "
                                   + f"limit ({max_length} characters)."})

        return test_name, issues
