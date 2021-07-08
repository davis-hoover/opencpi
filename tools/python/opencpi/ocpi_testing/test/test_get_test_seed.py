#!/usr/bin/env python3

# Test code in get_test_seed.py
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

from ocpi_testing import get_test_seed


class TestGetTestSeed(unittest.TestCase):
    def test_get_test_seed_single_int_argument(self):
        seed = get_test_seed(8)

        self.assertIsInstance(seed, int)
        self.assertGreater(seed, 0)

    def test_get_test_seed_single_float_argument(self):
        seed = get_test_seed(-17.5)

        self.assertIsInstance(seed, int)
        self.assertGreater(seed, 0)

    def test_get_test_seed_single_string_argument(self):
        seed = get_test_seed("input_string")

        self.assertIsInstance(seed, int)
        self.assertGreater(seed, 0)

    def test_get_test_seed_multiple_arguments(self):
        seed = get_test_seed(-10047, 3.6, "string")

        self.assertIsInstance(seed, int)
        self.assertGreater(seed, 0)

    def test_get_test_seed_no_arguments(self):
        with self.assertRaises(TypeError):
            get_test_seed()
