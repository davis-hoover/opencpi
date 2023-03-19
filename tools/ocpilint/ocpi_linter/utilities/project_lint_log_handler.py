#!/usr/bin/env python3

# Saves linting log when linting run on whole OpenCPI project
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

"""Screen Logger for used within Lint reporting."""


class ProjectLintLogHandler:
    """Lint logger for when in project mode."""

    def __init__(self, log_path):
        """Initialise ProjectLintLogHandler.

        Args:
            log_path (str): File path location to save the project linting log.

        Returns:
            Initialised ProjectLintLogHandler instance.
        """
        self._log_path = log_path
        with open(self._log_path, "w+") as log:
            # Set blank file
            pass

    def write(self, linted_file_path, test_number, test_name, issue_count):
        """Save test result to file.

        Only saves results to file where there are issues to report (i.e. if
        there are no issues, so the test passes) does not record any result.

        Args:
            linted_file_path (str): The file path of the file that has been
                linted.
            test_number (str): Test number being recorded.
            test_name (str): Test name of the test being recorded.
            issue_count (list): List of all the issues found in the file as a result
                of this test.
        """
        if issue_count > 0:
            with open(self._log_path, "a") as log:
                log.write(f"{linted_file_path}: {test_number}, "
                          + f"{test_name}, {issue_count} issues\n")
