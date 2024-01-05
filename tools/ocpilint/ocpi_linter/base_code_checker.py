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


class ParseWarning(UserWarning):
    """Exception raised when an issue is found parsing a file."""

    def __init__(self, line_number, message):
        """Initialise the ParseWarning exception.

        Args:
            line_number (int): Line number on which the parse error occurred.
            message (str): Descriptive message.
        """
        super().__init__(message)
        self.line_number = line_number
        self.message = message


class BaseCodeChecker:
    """Parent class for the language specific code checkers."""
    checker_settings = None

    def __init__(self, path: str, settings, to_console=True):
        """Initialise a BaseCodeChecker instance.

        Args:
            path (str): The file to be linted.
            settings (LinterSettings): Settings to lint against.
            to_console (bool): Should message be output to the console?

        Returns:
            Initialised BaseCodeChecker instance.
        """
        self.given_path = path
        self.path = pathlib.Path(path).expanduser().resolve()
        self._settings = settings
        self.to_console = to_console

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
            test_name = "Parsing of file"
            test_number = "BadFile_0"
            issues = [{"message": "Failure parsing file", "line": 0}]
            completed_tests[test_number] = LintTestResult.failed(
                test_name, test_number, issues, 0)
            self._print_issues(test_number, test_name, issues)
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
            logging.error(
                f"Test {test_number} ({test_name}) identified issues:")
            if self.to_console:
                print(
                    utilities.PrintStyle.RED +
                    utilities.PrintStyle.UNDERLINE +
                    f"Test {test_number} ({test_name}) identified issues:" +
                    utilities.PrintStyle.NORMAL)
            for issue in issues:
                if issue["line"] is not None:
                    logging.error(f"{self.path}:{issue['line']}: "
                                  + issue["message"].strip())
                    if self.to_console:
                        print(
                            utilities.PrintStyle.RED +
                            f"  {self.given_path}:{issue['line']}: " +
                            issue["message"].strip() +
                            utilities.PrintStyle.NORMAL)
                else:
                    logging.error(f"{self.path}: {issue['message'].strip()}")
                    if self.to_console:
                        print(
                            utilities.PrintStyle.RED +
                            f"  {self.given_path}: {issue['message'].strip()}" +
                            utilities.PrintStyle.NORMAL)

    def _remove_comments_and_strings(self, block_comment_start, block_comment_end, line_comment_start):
        """Remove comments and string content from code.

        String quote marks are left but content within string are removed.
        Comment content and comment symbols are removed.

        Uses self._code() as the input code to be filtered.

        Args:
            block_comment_start (str): Start of block comment e.g. "/*" or "<!--"
            block_comment_end (str): End of block comment e.g. "*/" or "-->"
            line_comment_start (str): Start of line comment e.g. "//" or "#"

        Raises:
            ParseWarning: If the end of a string or block comment cannot be found.

        Returns:
            List of the code without comments, and without string contents.
        """
        input_lines = self._code
        reduced_code = [""] * len(input_lines)

        currently_in_block_comment = False
        block_comment_began_on_line = 0
        for line_number, line_text in enumerate(input_lines):
            while len(line_text) > 0:
                # If in a comment, check if ended and use any trailing content
                if currently_in_block_comment:
                    endPos = line_text.find(block_comment_end)
                    if endPos >= 0:
                        _, line_text = line_text.split(block_comment_end, 1)
                        currently_in_block_comment = False
                    else:
                        # Comment continues over lines
                        line_text = ""

                # Find start positions of comments or strings
                line_comment_position = None
                block_comment_position = None
                quote_position = None
                quote_char = None
                escaped = False
                pos = 0
                found = False
                while (not found) and (pos < len(line_text)):
                    if line_comment_start is not None and line_text[pos:].startswith(line_comment_start):
                        line_comment_position = pos
                        found = True
                    elif line_text[pos:].startswith(block_comment_start):
                        block_comment_position = pos
                        block_comment_began_on_line = line_number + 1
                        found = True
                    elif not escaped:
                        char = line_text[pos]
                        if char == "\\":
                            escaped = True
                        elif char == "'":
                            quote_position = pos
                            quote_char = "'"
                            found = True
                        elif char == "\"":
                            quote_position = pos
                            quote_char = "\""
                            found = True
                    else:
                        escaped = (char == "\\")
                    pos += 1

                if line_comment_position is not None:
                    # Use the line upto the line comment position
                    reduced_code[line_number] += line_text[:line_comment_position]
                    line_text = ""

                elif block_comment_position is not None:
                    # Use the line upto the block comment position
                    reduced_code[line_number] += line_text[:block_comment_position]
                    # Next, process rest of line looking for end of comment
                    line_text = line_text[block_comment_position +
                                          len(block_comment_start):]
                    currently_in_block_comment = True

                elif quote_position is not None:
                    # Use the line upto the quote position plus an empty string
                    reduced_code[line_number] += line_text[:quote_position]
                    reduced_code[line_number] += f"{quote_char}{quote_char}"
                    # Find end of string
                    string_end = self._find_unescaped_symbol(
                        line_text, quote_char, quote_position+1)
                    if string_end < 0:
                        raise ParseWarning(
                            line_number + 1,
                            "Cannot find end of string in text ("
                            + f"{line_text[quote_position:]}). From line "
                            + f"{line_number + 1}")
                    # Next, process any line after the string
                    line_text = line_text[string_end+1:]

                else:
                    # Otherwise not a comment, or string, so take whole line
                    reduced_code[line_number] += line_text
                    line_text = ""

        if currently_in_block_comment:
            raise ParseWarning(
                block_comment_began_on_line,
                "Reached end of file without finding end of block comment.")

        return reduced_code

    def _find_unescaped_symbol(self, text, symbol, start_pos=0):
        r"""Find next symbol in text, ignoring escaped versions.

        Any symbol escaped with a '\\' character within search text will
        be not be found.

        Args:
            text (``str``): Text to be searched.
            symbol (``str``): The symbol to be found.
            start_pos (``int``): The position to start searching from.

        Returns:
            Index position the unescaped symbol was found in the text. Or
            -1 if the symbol is not found.
        """
        # Skip to the start position
        text = text[start_pos:]

        # Go through each character, checking if escaped or not, then check if
        # it is the character
        escaped = False
        for pos, char in enumerate(text):
            if escaped:
                escaped = False
            elif char == symbol:
                return start_pos + pos
            elif char == "\\":
                escaped = True

        # Failed to find symbol
        return -1
