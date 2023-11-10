#!/usr/bin/env python3

# Run code checks on C++ source code files
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

"""Standard C/C++ tests to run against ocpi projects."""

import pathlib
import subprocess
import re

from . import base_code_checker
from . import utilities


class CppCodeCheckerDefaults(base_code_checker.BaseCodeCheckerDefaults):
    """Default settings for CppCodeChecker class."""
    license_notice = (open(pathlib.Path(__file__).parent
                           .joinpath("license_notices").joinpath("cpp.txt"), "r")
                      .read())
    cppcheck_enable_tests = "warning,style,performance,portability"
    cppcheck_suppress_tests = "noConstructor"
    cppcheck_std = "c++11"
    cppcheck_other_options = ["--inconclusive",
                              "--language=c++"]
    cpplint_other_options = ["--headers=hh"]
    platform = ["unix64",  # CppCheck for a Unix 64-bit platform
                "unix32",  # CppCheck for a Unix 32-bit platform
                "avr8",    # CppCheck for an AVR 8-bit platform
                "win64"]   # CppCheck for a Windows 64-bit platform


class CppCodeChecker(base_code_checker.BaseCodeChecker):
    """Code formatter and checker for C++."""
    checker_settings = CppCodeCheckerDefaults

    @staticmethod
    def get_supported_file_extensions():
        """Return a list of file extension this code checker supports.

        Returns:
            List of file extensions
        """
        return [".cc", ".hh"]

    def test_cpp_000(self):
        """Run clang-format on code.

        **Test name:** Clang format

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "Clang format"

        if self._check_installed("clang-format"):
            before_code = list(self._code)
            process = subprocess.Popen(["clang-format", "-i", "-style=Google",
                                        self.path])
            process.wait()

            # As file may have changed re-read in
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
                     "message": "File was reformatted by clang-format."}]

            return test_name, []    # return no issues

        else:
            return test_name, [
                {"line": None,
                 "message": "Clang-format not installed. Cannot run test."}]

    def test_cpp_001(self):
        """Runs CPP lint over code.

        **Test name:** CPP Lint

        CPP lint is set with the options:

         * Quiet enabled

         * A line length of 80 characters

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "CPP lint"

        if self._check_installed("cpplint"):
            process = subprocess.Popen(["cpplint",
                                        "--quiet",
                                        f"--linelength={self.checker_settings.maximum_line_length}"]
                                       + self.checker_settings.cpplint_other_options
                                       + [str(self.path)],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            process.wait()
            cpp_lint_issues = process.communicate()[1].decode(
                "utf-8").split("\n")[:-1]

            issues = []
            for issue in cpp_lint_issues:
                # Suppress error due to OpenCPI using a namespace
                if issue.find("Do not use namespace using-directives") > -1:
                    code_line = self._code[int(
                        issue[issue.find(":") + 1:issue.rfind(": ")]) - 1]
                    if code_line.upper().find("OCPI::RCC") > -1:
                        continue
                    if code_line.upper().find("WORKERTYPES;") > -1:
                        continue

                if issue.count(":") < 3:
                    continue

                line_number = issue.split(":")[1]
                message = ":".join(issue.split(":")[2:])
                issues.append({"line": int(line_number),
                               "message": message.strip()})

        else:
            issues = [{
                "line": None,
                "message": "cpplint not installed. Cannot run test."}]

        return test_name, issues

    def test_cpp_002(self):
        """Runs CPP check over code.

        **Test name:** CPP check

        CPP check is run four times, with each run being for a different
        platform. The four platforms CPP check is run for are; `unix64``,
        ``unix32``, ``avr8`` and ``win64``. On every run the options set are:

         * Enable warning, style, performance, portability, information and
           missing include.

         * Inconclusive

         * As C++11.

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "CPP Check"

        if self._check_installed("cppcheck"):
            cpp_check_issues = []

            for platform in self.checker_settings.platform:
                process = subprocess.Popen(["cppcheck"] + [
                    f"--enable={self.checker_settings.cppcheck_enable_tests}",
                    f"--suppress={self.checker_settings.cppcheck_suppress_tests}",
                    f"--platform={platform}",
                    f"--std={self.checker_settings.cppcheck_std}",
                ] + self.checker_settings.cppcheck_other_options +
                    [str(self.path)],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                process.wait()
                cpp_check_issues = (cpp_check_issues +
                                    process.communicate()[1].decode(
                                        "utf-8")[:-1].split("\n"))

            # Combine cppcheck outputs into single (non-repeating list)
            cpp_check_issues = list(set(cpp_check_issues))

            # Format output issues
            issues = []
            for issue in cpp_check_issues:
                if issue.count(":") > 3:
                    line = issue.split(":")[1]
                    message = ":".join(issue.split(":")[2:])
                    issues.append({"line": line, "message": message})

        else:
            issues = [{
                "line": None,
                "message": "Cppcheck not installed. Cannot run test."}]

        return test_name, issues

    def test_cpp_003(self):
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

        if self._code[0][0:2] != "//":
            issues.append({"line": 1,
                           "message": "Must be brief description."})

        if self._code[1] != "//":
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

    def test_cpp_004(self):
        """Ensure no block comments.

        **Test name:** No block comments

        Block comments are those that use ``/*`` ... ``*/``.

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "No block comments"

        issues = []
        for line_number, line_text in enumerate(self._code):
            if "/*" in line_text or "*/" in line_text:
                issues.append({
                    "line": line_number + 1,
                    "message": "Block comments (using /* or */) are not "
                               + "allowed. All comments must start with //."})

        return test_name, issues

    def test_cpp_005(self):
        """Ensure #define not used.

        **Test name:** #define check

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "#define check"

        issues = []
        for line_number, line_text in enumerate(self._code):
            if "#define " == line_text[0:8]:
                issues.append({
                    "line": line_number + 1,
                    "message": "Macros and #define are not allowed."})

        return test_name, issues

    def test_cpp_006(self):
        """Determine if C, rather than C++, header files are being used.

        **Test name:** C header file check

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "C header file check"

        issues = []
        for line_number, line_text in enumerate(self._code):
            if ".h>" in line_text:
                issues.append({
                    "line": line_number + 1,
                    "message": "Use C++, rather than C, libraries wherever "
                               + "possible."})

        return test_name, issues

    def test_cpp_007(self):
        """Test if ``iostream`` is being included.

        **Test name:** ``iostream`` check

        ``iostream`` is usually only used as a debug tool, so check if included
        and warn if is.

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "iostream check"

        issues = []
        for line_number, line_text in enumerate(self._code):
            if "<iostream>" in line_text:
                issues.append({
                    "line": line_number + 1,
                    "message": "Has iostream been left in as a debug tool, "
                               + "remove if unneeded."})

        return test_name, issues

    def test_cpp_008(self):
        """Check #include in correct position in file.

        **Test name:** #include position

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "#include position"

        issues = []

        # Get past header comment
        header_line = 0
        while self._code[header_line][0:2] == "//":
            header_line = header_line + 1
        # One blank line
        if self._code[header_line] != "":
            issues.append({
                "line": header_line + 1,
                "message": "A single blank line must follow the opening "
                           + "header comment."})
        header_line = header_line + 1

        # All includes next
        while self._code[header_line][0:9] == "#include ":
            header_line = header_line + 1

        # No other includes should be in file
        for line_number, line_text in enumerate(self._code[header_line:],
                                                start=header_line):
            if "#include " == line_text.strip()[0:9]:
                issues.append({
                    "line": line_number + 1,
                    "message": "All includes must be straight after opening "
                               + "comment block and a single blank line."})

        return test_name, issues

    def test_cpp_009(self):
        """Ensure RCC_FATAL is used not RCC_ERROR.

        **Test name:** RCC_FATAL rather than RCC_ERROR

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "RCC_FATAL rather than RCC_ERROR"

        issues = []
        for line_number, line_text in enumerate(self._code):
            if "RCC_ERROR" in line_text:
                issues.append({
                    "line": line_number + 1,
                    "message": "Preference that RCC_FATAL is returned rather "
                               + "than RCC_ERROR."})

        return test_name, issues

    def test_cpp_010(self):
        """Check each RCC_FATAL occurrence has a ``setError``.

        **Test name:** RCC_FATAL must have ``setError``

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "RCC_FATAL must have setError"

        issues = []
        number_rcc_fatal = 0
        number_seterror = 0
        for line_text in self._code:
            if "RCC_FATAL" in line_text:
                number_rcc_fatal = number_rcc_fatal + 1
            if "setError" in line_text:
                number_seterror = number_seterror + 1

        if number_rcc_fatal != number_seterror:
            issues.append(
                {"line": None,
                 "message": "Number of RCC_FATAL occurrences does not match "
                            + "the number of setError() occurrences. Each "
                            + "RCC_FATAL must have an error message set."})

        return test_name, issues

    def test_cpp_011(self):
        """Check no new C++ classes defined.

        **Test name:** No new classes

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "No new classes"

        found_worker_class = False

        issues = []
        for line_number, line_text in enumerate(self._code):
            if "class " == line_text.strip()[0:6]:
                # Allow one worker class to be found
                if ("Worker" in line_text.strip()[6:] and
                        found_worker_class is False):
                    found_worker_class = True
                else:
                    issues.append({
                        "line": line_number + 1,
                        "message": "New classes must not be defined, only one "
                                   + "worker class is allowed per the file."})

        return test_name, issues

    def test_cpp_012(self):
        """Check ``malloc`` and ``free`` are not used.

        **Test name:** No ``malloc`` or ``free``

        ``new`` and ``delete`` should be used for memory management, not
        ``malloc`` and ``free``.

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "No malloc or free"

        issues = []
        for line_number, line_text in enumerate(self._code):
            if (re.search(r"\bmalloc\(", line_text) or
                    re.search(r"\bfree\(", line_text)):
                issues.append({
                    "line": line_number + 1,
                    "message": "Do not use malloc or free, use new and delete "
                               + "instead."})

        return test_name, issues

    def test_cpp_013(self):
        """Check only OpenCPI types are used.

        **Test name:** Use OpenCPI types

        OpenCPI types are ``uint8_t``, ``RCCFloat``, etc. rather than ``int``,
        ``long``, ``float``, etc.

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "Use OpenCPI types"

        issues = []

        pattern = "\\b(int|char|short|long|float|double)\\b"

        try:
            reduced_code = self._remove_comments_and_strings("/*", "*/", "//")
        except base_code_checker.ParseWarning as e:
            issues.append({"line": e.line_number, "message": e.message})
            reduced_code = []

        for line_number, line_text in enumerate(reduced_code):
            match = re.search(pattern, line_text)
            if match:
                issues.append({
                    "line": line_number + 1,
                    "message": f"Use of \"{match.group(0)}\"."
                               " Use OpenCPI types instead."})

        return test_name, issues
