#!/usr/bin/env python3

# Testing of code in equal.py
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

from ocpi_testing._comparison_methods.equal import Equal


class TestEqual(unittest.TestCase):
    def setUp(self):
        self.test_comparison = Equal(False, int)

    def test_same_passes(self):
        data = [{"opcode": "flush", "data": []},
                {"opcode": "sample_interval", "data": 0.001},
                {"opcode": "time", "data": 0.01},
                {"opcode": "sample", "data": [1, 2, 3]},
                {"opcode": "discontinuity", "data": []},
                {"opcode": "metadata", "data": {"id": 3, "value": 16}}]

        self.assertTrue(self.test_comparison.same(data, data)[0])

    def test_same_different_sample_values(self):
        data_1 = [{"opcode": "flush", "data": []},
                  {"opcode": "sample_interval", "data": 0.001},
                  {"opcode": "time", "data": 0.01},
                  {"opcode": "sample", "data": [1, 2, 3]},
                  {"opcode": "discontinuity", "data": []},
                  {"opcode": "metadata", "data": {"id": 3, "value": 6}}]
        data_2 = [{"opcode": "flush", "data": []},
                  {"opcode": "sample_interval", "data": 0.001},
                  {"opcode": "time", "data": 0.01},
                  {"opcode": "sample", "data": [1, 2, 4000]},
                  {"opcode": "discontinuity", "data": []},
                  {"opcode": "metadata", "data": {"id": 3, "value": 6}}]

        self.assertFalse(self.test_comparison.same(data_1, data_2)[0])

    def test_same_different_time_values(self):
        data_1 = [{"opcode": "flush", "data": []},
                  {"opcode": "sample_interval", "data": 0.001},
                  {"opcode": "time", "data": 0.01},
                  {"opcode": "sample", "data": [1, 2, 3]},
                  {"opcode": "discontinuity", "data": []},
                  {"opcode": "metadata", "data": {"id": 3, "value": 6}}]
        data_2 = [{"opcode": "flush", "data": []},
                  {"opcode": "sample_interval", "data": 0.001},
                  {"opcode": "time", "data": 0.011},
                  {"opcode": "sample", "data": [1, 2, 3]},
                  {"opcode": "discontinuity", "data": []},
                  {"opcode": "metadata", "data": {"id": 3, "value": 6}}]

        self.assertFalse(self.test_comparison.same(data_1, data_2)[0])

    def test_same_different_sample_interval_values(self):
        data_1 = [{"opcode": "flush", "data": []},
                  {"opcode": "sample_interval", "data": 0.001},
                  {"opcode": "time", "data": 0.01},
                  {"opcode": "sample", "data": [1, 2, 3]},
                  {"opcode": "discontinuity", "data": []},
                  {"opcode": "metadata", "data": {"id": 3, "value": 6}}]
        data_2 = [{"opcode": "flush", "data": []},
                  {"opcode": "sample_interval", "data": 0.002},
                  {"opcode": "time", "data": 0.01},
                  {"opcode": "sample", "data": [1, 2, 3]},
                  {"opcode": "discontinuity", "data": []},
                  {"opcode": "metadata", "data": {"id": 3, "value": 6}}]

        self.assertFalse(self.test_comparison.same(data_1, data_2)[0])

    def test_same_different_metadata_id(self):
        data_1 = [{"opcode": "flush", "data": []},
                  {"opcode": "sample_interval", "data": 0.001},
                  {"opcode": "time", "data": 0.01},
                  {"opcode": "sample", "data": [1, 2, 3]},
                  {"opcode": "discontinuity", "data": []},
                  {"opcode": "metadata", "data": {"id": 3, "value": 6}}]
        data_2 = [{"opcode": "flush", "data": []},
                  {"opcode": "sample_interval", "data": 0.001},
                  {"opcode": "time", "data": 0.01},
                  {"opcode": "sample", "data": [1, 2, 3]},
                  {"opcode": "discontinuity", "data": []},
                  {"opcode": "metadata", "data": {"id": 6, "value": 6}}]

        self.assertFalse(self.test_comparison.same(data_1, data_2)[0])

    def test_same_different_metadata_values(self):
        data_1 = [{"opcode": "flush", "data": []},
                  {"opcode": "sample_interval", "data": 0.001},
                  {"opcode": "time", "data": 0.01},
                  {"opcode": "sample", "data": [1, 2, 3]},
                  {"opcode": "discontinuity", "data": []},
                  {"opcode": "metadata", "data": {"id": 3, "value": 6}}]
        data_2 = [{"opcode": "flush", "data": []},
                  {"opcode": "sample_interval", "data": 0.001},
                  {"opcode": "time", "data": 0.01},
                  {"opcode": "sample", "data": [1, 2, 3]},
                  {"opcode": "discontinuous", "data": []},
                  {"opcode": "metadata", "data": {"id": 3, "value": 8}}]

        self.assertFalse(self.test_comparison.same(data_1, data_2)[0])

    def test_check_message_sample_pass(self):
        message = {"opcode": "sample", "data": [1, 2, 3]}

        self.assertTrue(
            self.test_comparison._check_message(message, message)[0])

    def test_check_message_sample_fail(self):
        message_1 = {"opcode": "sample", "data": [1, 2, 3]}
        message_2 = {"opcode": "sample", "data": [1, 4, 3]}

        self.assertFalse(
            self.test_comparison._check_message(message_1, message_2)[0])

    def test_check_message_time_pass(self):
        message = {"opcode": "time", "data": 1.1}

        self.assertTrue(
            self.test_comparison._check_message(message, message)[0])

    def test_check_message_time_fail(self):
        message_1 = {"opcode": "time", "data": 1.1}
        message_2 = {"opcode": "time", "data": 1.2}

        self.assertFalse(
            self.test_comparison._check_message(message_1, message_2)[0])

    # As sample interval are treated in the same way as time messages, no
    # additional test is included for these opcode types

    def test_check_message_metadata_pass(self):
        message = {"opcode": "metadata", "data": {"id": 1, "value": 5}}

        self.assertTrue(
            self.test_comparison._check_message(message, message)[0])

    def test_check_message_metadata_fail(self):
        message_1 = {"opcode": "metadata",
                     "data": {"id": 1, "value": 5}}
        message_2 = {"opcode": "metadata",
                     "data": {"id": 1, "value": 6}}

        self.assertFalse(
            self.test_comparison._check_message(message_1, message_2)[0])
