#!/usr/bin/env python3

# Runs code checks on files with unrecognised file extensions
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

"""Tests to run against ocpi projects with unrecognised files."""

from . import base_code_checker


class UnknownCodeChecker(base_code_checker.BaseCodeChecker):
    """Code checker for Unrecognised files.

    (with an always failing test of "Unrecognised file extension")
    """

    def _read_in_code(self):
        """Read source file into local variable.

        Note. Overridden from BaseCodeChecker and alter to *NOT* read in the
        code into ``self._code``, as this class will not check the code at all.
        """
        self._code = []
        self._allowed_exceptions = {}

    def test_unknown_999(self):
        """Test that always fails, returning unrecognised file extension error.

        **Test name:** Unrecognised file extension

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "Unrecognised file extension"

        return test_name, [
            {"line": None,
             "message":  "Not a recognised file extension (case sensitive) " +
             "and so should not be used. File will not be formatted or checked."}]
