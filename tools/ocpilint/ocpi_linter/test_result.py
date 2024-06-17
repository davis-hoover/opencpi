#!/usr/bin/env python3

# Helper classes for Test results
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

"""Test Results related classes."""

from datetime import timedelta


class LintTestResult:
    """Provides a common set of information from a test run."""

    def __init__(self, test_name="", test_id="", duration=timedelta(0)):
        """New test result.

        Args:
            test_name (str, optional): Verbose name for this test.
                                       Defaults to "".
            test_id (str, optional): short id for this test (i.e. py_001).
                                     Defaults to "".
            duration (datetime.timedelta, optional): processing time this test
                                                     has taken. Defaults to
                                                     timedelta(0).
        """
        self.name = test_name
        self.id = test_id
        self.issues = []
        if isinstance(duration, timedelta):
            self.duration = duration
        else:
            self.duration = timedelta(duration)
        self.skipped = 0
        self.passed = 0

    @classmethod
    def passed(cls, test_name="", test_id="", duration=timedelta(0)):
        """Factory for passing tests.

        Args:
            test_name (str, optional): Verbose name of test. Defaults to "".
            test_id (str, optional): Short name of test. Defaults to "".
            duration (datetime.timedelta, optional): Processing time for this
                                     test. Defaults to timedelta(0).

        Returns:
            LintTestResult: Instance of LintTestResult
        """
        ret = cls(test_name, test_id, duration)
        ret.passed += 1
        return ret

    @classmethod
    def skipped(cls, test_name="", test_id="", duration=timedelta(0)):
        """Factory for skipped tests.

        Args:
            test_name (str, optional): Verbose name of test. Defaults to "".
            test_id (str, optional): Short name of test. Defaults to "".
            duration (datetime.timedelta, optional): Processing time for this
                                      test. Defaults to timedelta(0).

        Returns:
            LintTestResult: Instance of LintTestResult
        """
        ret = cls(test_name, test_id, duration)
        ret.skipped += 1
        return ret

    @classmethod
    def failed(cls, test_name="", test_id="", issues=[],
               duration=timedelta(0)):
        """Factory for Failing tests.

        Args:
            test_name (str, optional): Verbose name of test. Defaults to "".
            test_id (str, optional): Short name of test. Defaults to "".
            issues (list, optional): List of all issues found for this test.
                                     Defaults to "Unknown Failure".
            duration (datetime.timedelta, optional): Processing time for this
                                     test. Defaults to timedelta(0).

        Returns:
            LintTestResult: Instance of LintTestResult
        """
        if len(issues) == 0:
            issues.append({"message": "Unknown failure occurred", "line": 0})
        ret = cls(test_name, test_id, duration)
        ret.issues = issues
        return ret

    def __repr__(self) -> str:
        """Print LintTestResult class in format "P/F/S[id](details)".

        Returns:
            str: Prints summarised class details
        """
        if len(self.issues) > 0:
            return f"Failed[{self.id}]({self.issue_count})"
        elif self.skipped > 0:
            return f"Skipped[{self.id}]"
        elif self.passed > 0:
            return f"Passed[{self.id}]"
        else:
            return f"Not Tested[{self.id}]"

    @property
    def has_failed(self) -> bool:
        """Has this test failed?

        Returns:
            bool: True if the test has failed, otherwise False
        """
        return len(self.issues) > 0

    @property
    def has_passed(self) -> bool:
        """Has this test passed?

        Returns:
            bool: True if the test has passed, otherwise False
        """
        return self.passed

    @property
    def was_skipped(self) -> bool:
        """Was this test skipped?

        Returns:
            bool: True if the test was skipped, otherwise False
        """
        return self.skipped

    @property
    def issue_count(self) -> int:
        """Number of issues held by this LintTestResult.

        Returns:
            int: Number of issues present
        """
        return len(self.issues)
