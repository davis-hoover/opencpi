#!/usr/bin/env python3

# Testing of code in base_comparison.py
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

from ocpi_testing._comparison_methods.base_comparison import BasicComparison


class TestComparison(BasicComparison):
    def same(self):
        # Overload this method in the child class as required, but since no
        # checks are being made using this method, just return False
        print("No check made by TestComparison.same()")
        return False


class TestBasicComparison(unittest.TestCase):
    def setUp(self):
        self.test_comparison = TestComparison(False, int)

    def test_correct_messages_passes(self):
        # Use different data values as this checker should not check data value
        # and should allow these values to pass
        messages_1 = [{"opcode": "time", "data": 0.01},
                      {"opcode": "sample", "data": [1, 2, 3]},
                      {"opcode": "flush", "data": None},
                      {"opcode": "sample", "data": [10, 11, 13]},
                      {"opcode": "sample", "data": [21, 22, 23]}]
        messages_2 = [{"opcode": "time", "data": 0.02},
                      {"opcode": "sample", "data": [4, 5, 6]},
                      {"opcode": "flush", "data": None},
                      {"opcode": "sample", "data": [14, 15, 16]},
                      {"opcode": "sample", "data": [24, 25, 26]}]

        self.assertTrue(
            self.test_comparison.correct_messages(messages_1, messages_2)[0])

    def test_correct_messages_different_number_of_messages(self):
        # Use different data values as this checker should not check data value
        # and should allow these values to pass
        messages_1 = [{"opcode": "time", "data": 0.01},
                      {"opcode": "sample", "data": [1, 2, 3]},
                      {"opcode": "flush", "data": None},
                      {"opcode": "sample", "data": [10, 11, 13]},
                      {"opcode": "sample", "data": [21, 22, 23]},
                      {"opcode": "sample", "data": [31, 32, 33]}]
        messages_2 = [{"opcode": "time", "data": 0.02},
                      {"opcode": "sample", "data": [4, 5, 6]},
                      {"opcode": "flush", "data": None},
                      {"opcode": "sample", "data": [14, 15, 16]},
                      {"opcode": "sample", "data": [24, 25, 26]}]

        self.assertFalse(
            self.test_comparison.correct_messages(messages_1, messages_2)[0])

    def test_correct_messages_different_opcodes(self):
        # Use different data values as this checker should not check data value
        # and should allow these values to pass
        messages_1 = [{"opcode": "time", "data": 0.01},
                      {"opcode": "sample", "data": [1, 2, 3]},
                      {"opcode": "flush", "data": None},
                      {"opcode": "sample", "data": [10, 11, 13]},
                      {"opcode": "sample", "data": [21, 22, 23]}]
        messages_2 = [{"opcode": "sample_interval", "data": 0.02},
                      {"opcode": "sample", "data": [4, 5, 6]},
                      {"opcode": "flush", "data": None},
                      {"opcode": "sample", "data": [14, 15, 16]},
                      {"opcode": "sample", "data": [24, 25, 26]}]

        self.assertFalse(
            self.test_comparison.correct_messages(messages_1, messages_2)[0])

    def test_correct_messages_different_data_length(self):
        # Use different data values as this checker should not check data value
        # and should allow these values to pass
        messages_1 = [{"opcode": "time", "data": 0.01},
                      {"opcode": "sample", "data": [1, 2, 3]},
                      {"opcode": "flush", "data": None},
                      {"opcode": "sample", "data": [10, 11, 13]},
                      {"opcode": "sample", "data": [21, 22, 23, 40]}]
        messages_2 = [{"opcode": "time", "data": 0.02},
                      {"opcode": "sample", "data": [4, 5, 6]},
                      {"opcode": "flush", "data": None},
                      {"opcode": "sample", "data": [14, 15, 16]},
                      {"opcode": "sample", "data": [24, 25, 26]}]

        self.assertFalse(
            self.test_comparison.correct_messages(messages_1, messages_2)[0])
