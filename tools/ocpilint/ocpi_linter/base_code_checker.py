#!/usr/bin/env python3

# Parent class for language specific code checkers
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


"""Base classes, from which all tests/checkers used should be derived."""

import pathlib
import re
import shutil
import logging
from datetime import datetime

from . import utilities
from .test_result import LintTestResult


class BaseCodeCheckerDefaults:
    """Default settings for language specific checker classes."""
    comment_maximum_line_length = 80
    maximum_line_length = 80
    license_notice = ""


class BaseCodeChecker:
    """Parent class for the language specific code checkers."""
    checker_settings = None

    def __init__(self, path: str, settings):
        """Initialise a BaseCodeChecker instance.

        Args:
            path (str): The file to be linted.
            settings (LinterSettings): Settings to lint against.

        Returns:
            Initialised BaseCodeChecker instance.
        """
        self.path = pathlib.Path(path).expanduser().resolve()
        self._settings = settings

        # Set bare minimum number of lines needed for header and start of
        # license to be present
        self.minimum_number_of_lines = 3

    @staticmethod
    def get_supported_file_extensions():
        """Return a list of file extension this code checker supports.

        Returns:
            List of file extensions
        """
        return []

    @staticmethod
    def get_ignored_file_extensions():
        """Return a list of file extension this code checker should ignore.

        Returns:
            List of file extensions
        """
        return []

    def lint(self):
        """Run all tests on file.

        Tests are defined in child classes which inherit from this class. All
        tests should be methods which have a name that starts ``test`` or
        ``user_test``.

        Returns:
            A dictionary of the result of the tests that have been run.
        """
        completed_tests = {}

        if (not self._read_in_code()):
            completed_tests["BadFile_0"] = LintTestResult.failed(
                "Parsing of file", "BadFail_0", [{"message": "Failure parsing file", "line": 0}], 0)
            return completed_tests

        for attribute in sorted(dir(self)):
            # Skip internal and non callable functions
            if attribute[0] == "_" or not callable(getattr(self, attribute)):
                continue

            test_function = None
            if attribute[0:5] == "test_":
                test_number = attribute[5:]
                test_function = getattr(self, attribute)
            elif attribute[0:10] == "user_test_":
                test_number = int(attribute[10:])
                test_function = getattr(self, attribute)

            if test_function:
                # Check if test enabled/disabled is settings
                test_enabled = self._settings.select_tests.get(
                    test_number, True)
                if not test_enabled:
                    completed_tests[test_number] = LintTestResult.skipped(
                        test_id=test_number)
                else:
                    # Call the test function - passing the settings if any
                    start = datetime.now()
                    test_name, issues = test_function() or ("", [])
                    stop = datetime.now()

                    # Remove any issues that are identified as allowed exceptions
                    if test_number in self._allowed_exceptions:
                        issues = [issue for issue in issues if issue["line"]
                                  not in self._allowed_exceptions[test_number]]

                    if len(issues) > 0:
                        self._print_issues(test_number, test_name, issues)
                        completed_tests[test_number] = LintTestResult.failed(
                            test_name, test_number, issues, stop-start)
                    else:
                        completed_tests[test_number] = LintTestResult.passed(
                            test_name, test_number, stop-start)

        return completed_tests

    def _read_in_code(self):
        """Read source file into local variable.

        Each line in the source code file is an element in the list stored in
        ``self._code``.

        Returns:
            True on parsing success, else False
        """
        self._code = []
        self._allowed_exceptions = {}

        with open(self.path, "r") as source_file:
            # Add new line so all blank line at end of file is read in
            try:
                self._code = (source_file.read() + "\n").splitlines()
            except UnicodeDecodeError:
                # File is not a text file
                self._code = ""
                self._print_issues(
                    "N/A", "NON-TEXT FILE",
                    [{
                        "line": 0,
                        "message": "File could not be parsed as a UTF-8 compliant file"
                    }])
                return False

        for line_number, line in enumerate(self._code):
            line = line.lstrip()
            # Regular expression pattern to match any line starting with
            # comment symbol (// for C++, # for Python, .. for Restructured
            # Text, -- for VHDL and <!-- for XML), then single space, then the
            # string "LINT EXCEPTION: "
            if re.match(r"^((\/\/)|#|(\.\.)|(--)|(<!--)) LINT EXCEPTION: ",
                        line):
                try:
                    test_number, line_offset = line.split(":")[1:3]
                except ValueError:
                    self._print_issues(
                        "N/A", "LINT EXCEPTION FORMAT",
                        [{
                            "line": 0,
                            "message": f"Line {line_number + 1}: Linter exception format incorrect."
                        }])
                    return False

                test_number = test_number.strip().lower()
                exception_line = line_number + 1 + int(line_offset.strip())
                if test_number in self._allowed_exceptions:
                    self._allowed_exceptions[test_number].append(
                        exception_line)
                else:
                    self._allowed_exceptions[test_number] = [exception_line]
        return True

    def _check_installed(self, program_name):
        """Check if a program is installed.

        Args:
            program_name (str): The name, used at the command line, of the
                program to be checked whether installed or not.

        Returns:
            Boolean of True if the program is installed, False otherwise.
        """
        if shutil.which(program_name) is None:
            print(utilities.PrintStyle.BOLD + utilities.PrintStyle.YELLOW +
                  f"WARNING: {program_name} not installed and so cannot be " +
                  "used as part of the linter.\n" +
                  utilities.PrintStyle.NORMAL +
                  f"  It is recommend you install {program_name} and re-run " +
                  "the linter.")
            return False
        else:
            return True

    def _print_issues(self, test_number, test_name, issues):
        """Print the issues found to the terminal.

        Args:
            test_number (str): The test number that found these issues.
            test_name (str): The name of the tests that found these issues.
            issues (list): The list of issues to be printed.
        """
        if len(issues) > 0:
            print(
                utilities.PrintStyle.BOLD + utilities.PrintStyle.UNDERLINE +
                utilities.PrintStyle.RED +
                f"Test {test_number} ({test_name}) output:" +
                utilities.PrintStyle.NORMAL)
            for issue in issues:
                if issue["line"] is not None:
                    print(f"{self.path}:{issue['line']}: "
                          + issue["message"].strip())
                    logging.error(f"{self.path}:{issue['line']}: "
                                  + issue["message"].strip())
                else:
                    print(f"{self.path}: {issue['message'].strip()}")
                    logging.error(f"{self.path}: {issue['message'].strip()}")

    def _remove_strings(self, input_lines):
        """Remove strings from code.

        String quote marks are left but content within string are removed.

        Args:
            List of code lines

        Returns:
            List of the code without strings.
        """
        reduced_code = [""] * len(input_lines)

        for line_number, line_text in enumerate(input_lines):
            # Remove strings
            single_quote = self._find_unescaped_symbol(line_text, "'")
            double_quote = self._find_unescaped_symbol(line_text, "\"")
            while not (single_quote is None and double_quote is None):
                if single_quote is None:
                    string_start = double_quote + 1
                    string_symbol = "\""
                elif double_quote is None:
                    string_start = single_quote + 1
                    string_symbol = "'"
                elif single_quote < double_quote:
                    string_start = single_quote + 1
                    string_symbol = "'"
                else:
                    string_start = double_quote + 1
                    string_symbol = "\""
                string_end = self._find_unescaped_symbol(
                    line_text[string_start:], string_symbol)
                if string_end is None:
                    raise ValueError(
                        "Cannot find end of string in text ("
                        + f"{line_text[string_start:]}). From line "
                        + f"{line_number + 1}")
                # Add offset for the sub-string searched
                string_end = string_end + string_start
                line_text = (line_text[:string_start] +
                             line_text[string_end:])
                # If there is no more text to search return None, since this is
                # what self._find_unescaped_symbol() would return if the symbol
                # is not found. Otherwise search the rest of the line for any
                # more strings.
                if string_start + 2 >= len(line_text):
                    single_quote = None
                    double_quote = None
                else:
                    # Use string_start as start position for searching as the
                    # string content has been removed now, so string_end is no
                    # longer valid
                    single_quote = self._find_unescaped_symbol(
                        line_text[string_start + 1:], "'")
                    double_quote = self._find_unescaped_symbol(
                        line_text[string_start + 1:], "\"")
                    if single_quote is not None:
                        single_quote = single_quote + string_start + 1
                    if double_quote is not None:
                        double_quote = double_quote + string_start + 1

            reduced_code[line_number] = line_text

        return reduced_code

    def _remove_block_comments(self, input_lines, block_comment_start, block_comment_end):
        """Remove comment symbols and their content from the file content.

        Args:
            input_lines (List of str): The content of the file
            block_comment_start (str): Token starts a block comment e.g. "<!--" or "/*"
            block_comment_end (str): Token that ends a block comment e.g. "-->" or "*/"

        Returns:
            List of strings representing the file content without the comments.
        """
        reduced_content = [""] * len(input_lines)

        # Remove comments
        currently_in_comment = False
        for line_number, line_text in enumerate(input_lines):

            while len(line_text) > 0:
                # If in a comment, check if ended and use any trailing content
                if currently_in_comment:
                    endPos = line_text.find(block_comment_end)
                    if endPos >= 0:
                        _, line_text = line_text.split(block_comment_end, 1)
                        currently_in_comment = False
                    else:
                        # Comment continues over lines
                        line_text = ""

                # If not currently a comment, check if one starts this line
                if not currently_in_comment:
                    if line_text.find(block_comment_start) >= 0:
                        content, line_text = line_text.split(
                            block_comment_start, 1)
                        reduced_content[line_number] += content
                        currently_in_comment = True
                    # Otherwise not a comment so take whole line
                    else:
                        reduced_content[line_number] += line_text
                        line_text = ""

        return reduced_content

    def _remove_line_comments(self, input_lines, comment_start):
        """Remove end-of-line comment symbols and their content from the file content.

        Args:
            input_lines (List of str): The content of the file
            comment_start (str): Token that starts a comment e.g. "//" or "#"

        Returns:
            List of strings representing the file content without the comments.
        """

        reduced_code = [""] * len(input_lines)
        for line_number, line_text in enumerate(input_lines):
            # Remove comments
            comment_position = line_text.find(comment_start)
            if comment_position >= 0:
                # Check not part of a string
                single_quote_position = self._find_unescaped_symbol(
                    line_text, "'")
                double_quote_position = self._find_unescaped_symbol(
                    line_text, "\"")
                if single_quote_position is not None:
                    if single_quote_position > comment_position:
                        line_text = line_text[0:comment_position]
                elif double_quote_position is not None:
                    if double_quote_position > comment_position:
                        line_text = line_text[0:comment_position]
                else:
                    line_text = line_text[0:comment_position]

            reduced_code[line_number] = line_text

        return reduced_code

    def _find_unescaped_symbol(self, text, symbol):
        """Find next symbol in text, ignoring escaped versions.

        Any symbol escaped with a '\' character within search text will
        be not be found.

        Args:
            text (``str``): Text to be searched.
            symbol (``str``): The symbol to be found.

        Returns:
            Index position the unescaped symbol was found in the text. Or
            ``None`` if the symbol is not found.
        """
        # If first character then cannot be escaped, and regex pattern will not
        # find the pattern
        if len(text) > 0:
            if text[0] == symbol:
                return 0

        # Regular expression pattern searches for the symbol but must not have
        # a leading "\"
        search_result = re.search(r"[^\\\\]" + symbol, text)
        if search_result is None:
            return None
        else:
            # Add one because searches for symbol and checks previous character
            return search_result.start() + 1
