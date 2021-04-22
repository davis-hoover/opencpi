#!/usr/bin/env python3

# Test code in _terminal_print_formatter.py
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


import contextlib
import io
import unittest


from ocpi_testing._terminal_print_formatter import print_warning, print_fail


# Set to True and a user must confirm correct result for some tests. Cannot
# be set to True when part of an automated test suite.
USER_CONFIRM = False


class TestPrintTerminalFormatter(unittest.TestCase):
    def test_print_warning_no_error(self):
        print_warning("This is a test warning message.")

        # Just checking no errors are raised, so getting to the next line will
        # have passed this test
        self.assertTrue(True)

    def test_print_check_output(self):
        message = "This is a test warning message"
        stdout_handler = io.StringIO()
        with contextlib.redirect_stdout(stdout_handler):
            print_warning(message)
        printed_message = stdout_handler.getvalue()

        # Checks need to ignore ANSI escape characters used for terminal print
        # formatting
        self.assertIn(message, printed_message)

    @unittest.skipIf(USER_CONFIRM is False, "Skipping user confirmation tests")
    def test_print_warning_visual_user_confirm(self):
        # Need to start new line as unit test prints to terminal as well
        print("")

        message = "This is a test warning message."
        print_warning(message)

        print(f"On the above line a formatted warning should say \"{message}"
              + "\". This text should be in the default colour and style.")
        user_response = input("Is this correct? (Y / N) ")
        while user_response.upper() not in ["Y", "YES", "N", "NO"]:
            user_response = input(
                "Only yes or no (Y / N) are suitable responses: ")
        self.assertIn(user_response.upper(), ["Y", "YES"])

    def test_print_fail_no_error(self):
        print_fail("case00.00", "This is a test failure message.")

        # Just checking no errors are raised, so getting to the next line will
        # have passed this test
        self.assertTrue(True)

    def test_print_fail_check_output(self):
        message = "This is a test fail message"
        case = "case00.00"
        stdout_handler = io.StringIO()
        with contextlib.redirect_stdout(stdout_handler):
            print_fail(case, message)
        printed_message = stdout_handler.getvalue()

        self.assertIn(message, printed_message)

    @unittest.skipIf(USER_CONFIRM is False, "Skipping user confirmation tests")
    def test_print_fail_visual_user_confirm_returned_to_default(self):
        # Need to start new line as unit test prints to terminal as well
        print("")

        message = "This is a test failure message."
        case = "case00.00"
        print_fail(case, message)

        print("On the above line a formatted fail message should say "
              + f"\"{message}\". This text should be in the default colour "
              + "and style.")
        user_response = input("Is this correct? (Y / N) ")
        while user_response.upper() not in ["Y", "YES", "N", "NO"]:
            user_response = input(
                "Only yes or no (Y / N) are suitable responses: ")
        self.assertIn(user_response.upper(), ["Y", "YES"])
