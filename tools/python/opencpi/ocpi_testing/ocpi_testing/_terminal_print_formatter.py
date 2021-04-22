#!/usr/bin/env python3

# Format printing to terminal
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


STANDARD_TERMINAL = "\033[0m"
BOLD = "\033[1m"
RED = "\033[91m"
ORANGE = "\033[38;5;202m"


def print_warning(message):
    """ Print warning to terminal

    Warnings are in orange and with the warning word in bold. Format is
        Warning: Message.

    Args:
        message (str): Warning message to be printed to the terminal.
    """
    print(ORANGE + BOLD + "Warning:" + STANDARD_TERMINAL,
          ORANGE + message + STANDARD_TERMINAL)


def print_fail(test_id, message):
    """ Print reason why a test has failed to terminal

    Test failure messages are red and all bold. Format is:
        FAIL (test_id): Message.

    Args:
        test_id (str): Test ID / case number of the test that has failed.
        message (str): Test failure message.
    """
    print(f"{BOLD}{RED}FAIL ({test_id.upper()}): {message}{STANDARD_TERMINAL}")
