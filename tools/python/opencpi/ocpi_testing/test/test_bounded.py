#!/usr/bin/env python3

# Testing of code in bounded.py
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

from ocpi_testing._comparison_methods.bounded import Bounded


class TestBounded(unittest.TestCase):
    def setUp(self):
        self.test_comparison = Bounded(False, int)

    def test_same_passes(self):
        data = [{"opcode": "flush", "data": []},
                {"opcode": "sample_interval", "data": 0.001},
                {"opcode": "time", "data": 0.01},
                {"opcode": "sample", "data": [1, 2, 3]},
                {"opcode": "discontinuity", "data": []},
                {"opcode": "metadata", "data": {"id": 3, "value": 16}}]

        self.assertTrue(self.test_comparison.same(data, data)[0])

    def test_same_within_bound(self):
        data_1 = [{"opcode": "flush", "data": []},
                  {"opcode": "sample_interval", "data": 0.001},
                  {"opcode": "time", "data": 0.01},
                  {"opcode": "sample", "data": [1, 2, 3]},
                  {"opcode": "discontinuity", "data": []},
                  {"opcode": "metadata", "data": {"id": 3, "value": 6}}]
        data_2 = [{"opcode": "flush", "data": []},
                  {"opcode": "sample_interval", "data": 0.001},
                  {"opcode": "time", "data": 0.01},
                  {"opcode": "sample", "data": [2, 3, 2]},
                  {"opcode": "discontinuity", "data": []},
                  {"opcode": "metadata", "data": {"id": 3, "value": 6}}]

        self.assertTrue(self.test_comparison.same(data_1, data_2)[0])

    def test_same_within_bound_complex(self):
        # Normally set using __init__() but as testing easier to set (private)
        # value directly.
        self.test_comparison._complex = True

        data_1 = [{"opcode": "flush", "data": []},
                  {"opcode": "sample_interval", "data": 0.001},
                  {"opcode": "time", "data": 0.01},
                  {"opcode": "sample", "data": [complex(1, -1),
                                                complex(2, -2),
                                                complex(3, -3)]},
                  {"opcode": "discontinuity", "data": []},
                  {"opcode": "metadata", "data": {"id": 3, "value": 6}}]
        data_2 = [{"opcode": "flush", "data": []},
                  {"opcode": "sample_interval", "data": 0.001},
                  {"opcode": "time", "data": 0.01},
                  {"opcode": "sample", "data": [complex(2, -1),
                                                complex(2, -2),
                                                complex(3, -3)]},
                  {"opcode": "discontinuity", "data": []},
                  {"opcode": "metadata", "data": {"id": 3, "value": 6}}]

        self.assertTrue(self.test_comparison.same(data_1, data_2)[0])

    def test_same_expand_bound(self):
        self.test_comparison.BOUND = 5
        data_1 = [{"opcode": "flush", "data": []},
                  {"opcode": "sample_interval", "data": 0.001},
                  {"opcode": "time", "data": 0.01},
                  {"opcode": "sample", "data": [1, 2, 3]},
                  {"opcode": "discontinuity", "data": []},
                  {"opcode": "metadata", "data": {"id": 3, "value": 6}}]
        data_2 = [{"opcode": "flush", "data": []},
                  {"opcode": "sample_interval", "data": 0.001},
                  {"opcode": "time", "data": 0.01},
                  {"opcode": "sample", "data": [1, 2, 7]},
                  {"opcode": "discontinuity", "data": []},
                  {"opcode": "metadata", "data": {"id": 3, "value": 6}}]

        self.assertTrue(self.test_comparison.same(data_1, data_2)[0])

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

    def test_same_within_overflow_bound(self):
        self.test_comparison.WRAP_ROUND_VALUES = [-128, 127]

        data_1 = [{"opcode": "flush", "data": []},
                  {"opcode": "sample_interval", "data": 0.001},
                  {"opcode": "time", "data": 0.01},
                  {"opcode": "sample", "data": [1, 2, 127]},
                  {"opcode": "discontinuity", "data": []},
                  {"opcode": "metadata", "data": {"id": 3, "value": 6}}]
        data_2 = [{"opcode": "flush", "data": []},
                  {"opcode": "sample_interval", "data": 0.001},
                  {"opcode": "time", "data": 0.01},
                  {"opcode": "sample", "data": [1, 2, -127]},
                  {"opcode": "discontinuity", "data": []},
                  {"opcode": "metadata", "data": {"id": 3, "value": 6}}]

        self.assertTrue(self.test_comparison.same(data_1, data_2)[0])

    def test_same_overflow_bound_set_but_different(self):
        self.test_comparison.WRAP_ROUND_VALUES = [-128, 127]

        data_1 = [{"opcode": "flush", "data": []},
                  {"opcode": "sample_interval", "data": 0.001},
                  {"opcode": "time", "data": 0.01},
                  {"opcode": "sample", "data": [1, 2, 124]},
                  {"opcode": "discontinuity", "data": []},
                  {"opcode": "metadata", "data": {"id": 3, "value": 6}}]
        data_2 = [{"opcode": "flush", "data": []},
                  {"opcode": "sample_interval", "data": 0.001},
                  {"opcode": "time", "data": 0.01},
                  {"opcode": "sample", "data": [1, 2, -124]},
                  {"opcode": "discontinuity", "data": []},
                  {"opcode": "metadata", "data": {"id": 3, "value": 6}}]

        self.assertFalse(self.test_comparison.same(data_1, data_2)[0])

    def test_same_with_nan(self):
        data_1 = [{"opcode": "flush", "data": []},
                  {"opcode": "sample_interval", "data": 0.001},
                  {"opcode": "time", "data": 0.01},
                  {"opcode": "sample", "data": [1.5, 2.5, float("nan")]},
                  {"opcode": "discontinuity", "data": []},
                  {"opcode": "metadata", "data": {"id": 3, "value": 6}}]
        data_2 = [{"opcode": "flush", "data": []},
                  {"opcode": "sample_interval", "data": 0.001},
                  {"opcode": "time", "data": 0.01},
                  {"opcode": "sample", "data": [1.5, 2.2, float("nan")]},
                  {"opcode": "discontinuity", "data": []},
                  {"opcode": "metadata", "data": {"id": 3, "value": 6}}]

        self.assertTrue(self.test_comparison.same(data_1, data_2)[0])

    def test_same_with_inf(self):
        data_1 = [{"opcode": "flush", "data": []},
                  {"opcode": "sample_interval", "data": 0.001},
                  {"opcode": "time", "data": 0.01},
                  {"opcode": "sample", "data": [1.5, 2.5, float("inf")]},
                  {"opcode": "discontinuity", "data": []},
                  {"opcode": "metadata", "data": {"id": 3, "value": 6}}]
        data_2 = [{"opcode": "flush", "data": []},
                  {"opcode": "sample_interval", "data": 0.001},
                  {"opcode": "time", "data": 0.01},
                  {"opcode": "sample", "data": [1.5, 2.2, float("inf")]},
                  {"opcode": "discontinuity", "data": []},
                  {"opcode": "metadata", "data": {"id": 3, "value": 6}}]

        self.assertTrue(self.test_comparison.same(data_1, data_2)[0])

    def test_same_with_negative_inf(self):
        data_1 = [{"opcode": "flush", "data": []},
                  {"opcode": "sample_interval", "data": 0.001},
                  {"opcode": "time", "data": 0.01},
                  {"opcode": "sample", "data": [1.5, 2.5, -float("inf")]},
                  {"opcode": "discontinuity", "data": []},
                  {"opcode": "metadata", "data": {"id": 3, "value": 6}}]
        data_2 = [{"opcode": "flush", "data": []},
                  {"opcode": "sample_interval", "data": 0.001},
                  {"opcode": "time", "data": 0.01},
                  {"opcode": "sample", "data": [1.5, 2.2, -float("inf")]},
                  {"opcode": "discontinuity", "data": []},
                  {"opcode": "metadata", "data": {"id": 3, "value": 6}}]

        self.assertTrue(self.test_comparison.same(data_1, data_2)[0])

    def test_same_fail_inf_compare_to_negative_inf(self):
        data_1 = [{"opcode": "flush", "data": []},
                  {"opcode": "sample_interval", "data": 0.001},
                  {"opcode": "time", "data": 0.01},
                  {"opcode": "sample", "data": [1.5, 2.5, -float("inf")]},
                  {"opcode": "discontinuity", "data": []},
                  {"opcode": "metadata", "data": {"id": 3, "value": 6}}]
        data_2 = [{"opcode": "flush", "data": []},
                  {"opcode": "sample_interval", "data": 0.001},
                  {"opcode": "time", "data": 0.01},
                  {"opcode": "sample", "data": [1.5, 2.2, float("inf")]},
                  {"opcode": "discontinuity", "data": []},
                  {"opcode": "metadata", "data": {"id": 3, "value": 6}}]

        self.assertFalse(self.test_comparison.same(data_1, data_2)[0])

    def test_same_with_nan_complex(self):
        # Normally set using __init__() but as testing easier to set (private)
        # value directly.
        self.test_comparison._complex = True

        data_1 = [{"opcode": "flush", "data": []},
                  {"opcode": "sample_interval", "data": 0.001},
                  {"opcode": "time", "data": 0.01},
                  {"opcode": "sample", "data": [complex(1.5, 1.5),
                                                complex(2.5, 2.5),
                                                complex(3.5, float("nan"))]},
                  {"opcode": "discontinuity", "data": []},
                  {"opcode": "metadata", "data": {"id": 3, "value": 6}}]
        data_2 = [{"opcode": "flush", "data": []},
                  {"opcode": "sample_interval", "data": 0.001},
                  {"opcode": "time", "data": 0.01},
                  {"opcode": "sample", "data": [complex(1.5, 1.5),
                                                complex(2.2, 2.5),
                                                complex(3.5, float("nan"))]},
                  {"opcode": "discontinuity", "data": []},
                  {"opcode": "metadata", "data": {"id": 3, "value": 6}}]

        self.assertTrue(self.test_comparison.same(data_1, data_2)[0])

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
        message_2 = {"opcode": "sample", "data": [1, 5, 3]}

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

    # As sample interval messages are treated in the same way as time messages,
    # no additional test is included for these opcode types

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
