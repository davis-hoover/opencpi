#!/usr/bin/env python3

# Test code in id_to_case.py
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

import unittest

from ocpi_testing.id_to_case import id_to_case


class TestIdToCase(unittest.TestCase):
    def test_default_name_format(self):
        case, subcase = id_to_case("case05.07")

        self.assertEqual("05", case)
        self.assertEqual("07", subcase)

    def test_non_default_name_format(self):
        case, subcase = id_to_case("custom_name")

        self.assertEqual("custom_name", case)
        self.assertEqual("", subcase)
