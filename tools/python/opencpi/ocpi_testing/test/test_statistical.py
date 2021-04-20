#!/usr/bin/env python3

# Testing of code in statistical.py
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


import random
import unittest

from ocpi_testing._comparison_methods.statistical import Statistical


class TestStatistical(unittest.TestCase):
    def setUp(self):
        self.test_comparison = Statistical(False, int)

    def test_same_passes(self):
        messages = [{"opcode": "flush", "data": []},
                    {"opcode": "sample_interval", "data": 0.001},
                    {"opcode": "time", "data": 0.01},
                    {"opcode": "sample", "data": [1, 2, 3]},
                    {"opcode": "discontinuity", "data": []},
                    {"opcode": "metadata", "data": {"id": 3,
                                                    "value": 16}}]

        self.assertTrue(self.test_comparison.same(messages, messages)[0])

    def test_same_different_sample_values(self):
        messages_1 = [{"opcode": "flush", "data": []},
                      {"opcode": "sample_interval", "data": 0.001},
                      {"opcode": "time", "data": 0.01},
                      {"opcode": "sample", "data": [1, 2, 3]},
                      {"opcode": "discontinuity", "data": []},
                      {"opcode": "metadata", "data": {"id": 3,
                                                      "value": 3}}]
        messages_2 = [{"opcode": "flush", "data": []},
                      {"opcode": "sample_interval", "data": 0.001},
                      {"opcode": "time", "data": 0.01},
                      {"opcode": "sample", "data": [1, 2, 4000]},
                      {"opcode": "discontinuity", "data": []},
                      {"opcode": "metadata", "data": {"id": 3,
                                                      "value": 3}}]

        self.assertFalse(self.test_comparison.same(messages_1, messages_2)[0])

    def test_same_sample_small_difference_passes(self):
        # Statistical check should allow a small difference in values to pass

        random.seed(34786)
        data = [index * 25 + 147 for index in range(10)]
        messages_1 = [{"opcode": "sample", "data": data}]
        messages_2 = [
            {"opcode": "sample",
             "data": [value + round(random.gauss(0, 0.25)) for value in data]}]

        self.assertTrue(self.test_comparison.same(messages_1, messages_2)[0])

    def test_same_mean_limit_larger_than_largest_data_fail(self):
        message = [{"opcode": "sample", "data": [1] * 10}]
        self.test_comparison.MEAN_DIFFERENCE_LIMIT = 6

        self.assertFalse(self.test_comparison.same(message, message)[0])

    def test_same_standard_deviation_limit_larger_than_largest_data_fail(self):
        random.seed(4934)
        message = [{"opcode": "sample",
                    "data": [random.gauss(0, 10) for _ in range(100)]}]
        self.test_comparison.STANDARD_DEVIATION_LIMIT = 500

        self.assertFalse(self.test_comparison.same(message, message)[0])

    def test_same_allowed_variation_greater_than_largest_data_fail(self):
        random.seed(716864)
        data = [index * 1.2 for index in range(100)]
        message_1 = [{"opcode": "sample", "data": data}]
        message_2 = [
            {"opcode": "sample",
             "data": [value + random.gauss(0, 6) for value in data]}]
        self.test_comparison.STANDARD_DEVIATION_LIMIT = 10
        self.test_comparison.STANDARD_DEVIATION_MULTIPLE = 50

        self.assertFalse(self.test_comparison.same(message_1, message_2)[0])

    def test_same_one_value_above_allowed_variation_fail(self):
        data = [index * 25 + 147 for index in range(10)]
        message_1 = [{"opcode": "sample", "data": data}]
        message_2 = [
            {"opcode": "sample",
             "data": [value + random.randint(-2, 2) for value in data]}]

        # Make one value notably further
        message_2[0]["data"][6] = message_2[0]["data"][6] + 12

        self.assertFalse(self.test_comparison.same(message_1, message_2)[0])

    def test_same_one_value_below_allowed_variation_fail(self):
        data = [index * 25 + 147 for index in range(10)]
        message_1 = [{"opcode": "sample", "data": data}]
        message_2 = [
            {"opcode": "sample",
             "data": [value + random.randint(-2, 2) for value in data]}]

        # Make one value notably further
        message_2[0]["data"][6] = message_2[0]["data"][6] - 8

        self.assertFalse(self.test_comparison.same(message_1, message_2)[0])

    def test_same_mean_difference_greater_than_limit_fail(self):
        data = [index * 25 + 147 for index in range(10)]
        message_1 = [{"opcode": "sample", "data": data}]
        # Fixed offset will cause large difference in mean - small difference
        # in standard deviation.
        message_2 = [{"opcode": "sample",
                      "data": [value + 20 for value in data]}]

        self.assertFalse(self.test_comparison.same(message_1, message_2)[0])

    def test_same_standard_deviation_greater_than_limit_fail(self):
        data = [index * 2 + 147 for index in range(100)]
        message_1 = [{"opcode": "sample", "data": data}]
        message_2 = [
            {"opcode": "sample",
             "data": [value + random.randint(-10, 10) for value in data]}]

        self.assertFalse(self.test_comparison.same(message_1, message_2)[0])

    def test_same_with_nan_inf_pass(self):
        message = [{"opcode": "sample", "data": [0.0,
                                                 1.1,
                                                 float("nan"),
                                                 2.2,
                                                 float("inf"),
                                                 3.3,
                                                 -float("inf"),
                                                 4.4]}]

        self.assertTrue(self.test_comparison.same(message, message)[0])

    def test_same_nan_number_compare_fail(self):
        message_1 = [
            {"opcode": "sample", "data": [1.1, float("nan"), 2.2, 3.3, 4.4]}]
        message_2 = [
            {"opcode": "sample", "data": [1.1, 1.8, 2.2, 3.3, 4.4]}]

        self.assertFalse(self.test_comparison.same(message_1, message_2)[0])

    def test_same_nan_positive_inf_compare_fail(self):
        message_1 = [
            {"opcode": "sample", "data": [1.1, float("nan"), 2.2, 3.3, 4.4]}]
        message_2 = [
            {"opcode": "sample", "data": [1.1, float("inf"), 2.2, 3.3, 4.4]}]

        self.assertFalse(self.test_comparison.same(message_1, message_2)[0])

    def test_same_nan_negative_inf_compare_fail(self):
        message_1 = [
            {"opcode": "sample", "data": [1.1, float("nan"), 2.2, 3.3, 4.4]}]
        message_2 = [
            {"opcode": "sample", "data": [1.1, -float("inf"), 2.2, 3.3, 4.4]}]

        self.assertFalse(self.test_comparison.same(message_1, message_2)[0])

    def test_same_positive_inf_number_compare_fail(self):
        message_1 = [
            {"opcode": "sample", "data": [1.1, float("inf"), 2.2, 3.3, 4.4]}]
        message_2 = [
            {"opcode": "sample", "data": [1.1, 1.8, 2.2, 3.3, 4.4]}]

        self.assertFalse(self.test_comparison.same(message_1, message_2)[0])

    def test_same_positive_inf_negative_inf_compare_fail(self):
        message_1 = [
            {"opcode": "sample", "data": [1.1, float("inf"), 2.2, 3.3, 4.4]}]
        message_2 = [
            {"opcode": "sample", "data": [1.1, -float("inf"), 2.2, 3.3, 4.4]}]

        self.assertFalse(self.test_comparison.same(message_1, message_2)[0])

    def test_same_negative_inf_number_compare_fail(self):
        message_1 = [
            {"opcode": "sample", "data": [1.1, -float("inf"), 2.2, 3.3, 4.4]}]
        message_2 = [
            {"opcode": "sample", "data": [1.1, 1.8, 2.2, 3.3, 4.4]}]

        self.assertFalse(self.test_comparison.same(message_1, message_2)[0])

    def test_same_complex_data_sample_same_data_pass(self):
        # Normally if a complex data set set as part of __init__() however as
        # set in setUp() of part of Test class need to set manually here
        self.test_comparison._complex = True

        data = [complex(index * 2 + 7, index * 3 + 9) for index in range(100)]
        message = [{"opcode": "sample", "data": data}]

        self.assertTrue(self.test_comparison.same(message, message)[0])

    def test_same_complex_data_sample_pass(self):
        # Normally if a complex data set set as part of __init__() however as
        # set in setUp() of part of Test class need to set manually here
        self.test_comparison._complex = True

        random.seed(378)
        data = [complex(index * 2 + 7, index * 3 + 9) for index in range(100)]
        message_1 = [{"opcode": "sample", "data": data}]
        message_2 = [{
            "opcode": "sample",
            "data": [complex(value.real + random.gauss(0, 0.4),
                             value.imag + random.gauss(0, 0.4)) for value in
                     data]}]

        self.assertTrue(self.test_comparison.same(message_1, message_2)[0])

    def test_same_complex_data_sample_fail(self):
        # Normally if a complex data set set as part of __init__() however as
        # set in setUp() of part of Test class need to set manually here
        self.test_comparison._complex = True

        random.seed(234)
        data = [complex(index * 2 + 7, index * 3 + 9) for index in range(100)]
        message_1 = [{"opcode": "sample", "data": data}]
        message_2 = [{
            "opcode": "sample",
            "data": [complex(value.real + random.gauss(0, 0.8),
                             value.imag + random.gauss(0, 0.8)) for value in
                     data]}]

        message_2[0]["data"][10] = message_2[0]["data"][10] + complex(0,
                                                                      12)

        self.assertFalse(self.test_comparison.same(message_1, message_2)[0])

    def test_same_different_time_values(self):
        messages_1 = [{"opcode": "flush", "data": []},
                      {"opcode": "sample_interval", "data": 0.001},
                      {"opcode": "time", "data": 0.01},
                      {"opcode": "sample", "data": [1, 2, 3]},
                      {"opcode": "discontinuity", "data": []}]
        messages_2 = [{"opcode": "flush", "data": []},
                      {"opcode": "sample_interval", "data": 0.001},
                      {"opcode": "time", "data": 0.011},
                      {"opcode": "sample", "data": [1, 2, 3]},
                      {"opcode": "discontinuity", "data": []}]

        self.assertFalse(self.test_comparison.same(messages_1, messages_2)[0])

    def test_same_different_sample_interval_values(self):
        messages_1 = [{"opcode": "flush", "data": []},
                      {"opcode": "sample_interval", "data": 0.001},
                      {"opcode": "time", "data": 0.01},
                      {"opcode": "sample", "data": [1, 2, 3]},
                      {"opcode": "discontinuity", "data": []}]
        messages_2 = [{"opcode": "flush", "data": []},
                      {"opcode": "sample_interval", "data": 0.002},
                      {"opcode": "time", "data": 0.01},
                      {"opcode": "sample", "data": [1, 2, 3]},
                      {"opcode": "discontinuity", "data": []}]

        self.assertFalse(self.test_comparison.same(messages_1, messages_2)[0])

    def test_same_different_metadata_id(self):
        messages_1 = [{"opcode": "flush", "data": []},
                      {"opcode": "sample_interval", "data": 0.001},
                      {"opcode": "time", "data": 0.01},
                      {"opcode": "sample", "data": [1, 2, 3]},
                      {"opcode": "discontinuity", "data": []},
                      {"opcode": "metadata", "data": {"id": 3,
                                                      "value": 16}}]
        messages_2 = [{"opcode": "flush", "data": []},
                      {"opcode": "sample_interval", "data": 0.001},
                      {"opcode": "time", "data": 0.01},
                      {"opcode": "sample", "data": [1, 2, 3]},
                      {"opcode": "discontinuity", "data": []},
                      {"opcode": "metadata", "data": {"id": 6,
                                                      "value": 16}}]

        self.assertFalse(self.test_comparison.same(messages_1, messages_2)[0])

    def test_same_different_metadata_values(self):
        messages_1 = [{"opcode": "flush", "data": []},
                      {"opcode": "sample_interval", "data": 0.001},
                      {"opcode": "time", "data": 0.01},
                      {"opcode": "sample", "data": [1, 2, 3]},
                      {"opcode": "discontinuity", "data": []},
                      {"opcode": "metadata", "data": {"id": 3,
                                                      "value": 16}}]
        messages_2 = [{"opcode": "flush", "data": []},
                      {"opcode": "sample_interval", "data": 0.001},
                      {"opcode": "time", "data": 0.01},
                      {"opcode": "sample", "data": [1, 2, 3]},
                      {"opcode": "discontinuous", "data": []},
                      {"opcode": "metadata", "data": {"id": 3,
                                                      "value": 160}}]

        self.assertFalse(self.test_comparison.same(messages_1, messages_2)[0])

    def test_store_smallest_real(self):
        self.test_comparison._store_smallest([1, 2, -3])
        self.assertEqual(1, self.test_comparison._data_smallest)

    def test_store_smallest_real_float(self):
        self.test_comparison._store_smallest([5.2, 2.5, 300.1])
        self.assertEqual(2.5, self.test_comparison._data_smallest)

    def test_store_smallest_complex_(self):
        # Normally if a complex data set set as part of __init__() however as
        # set in setUp() of part of Test class need to set manually here
        self.test_comparison._complex = True

        self.test_comparison._store_smallest([complex(1, -5),
                                              complex(5, -1)])
        self.assertEqual(complex(1, 1), self.test_comparison._data_smallest)

    def test_store_largest_real(self):
        self.test_comparison._store_largest([1, 2, -3])
        self.assertEqual(3, self.test_comparison._data_largest)

    def test_store_largest_real_float(self):
        self.test_comparison._store_largest([5.2, 2.5, 300.1])
        self.assertEqual(300.1, self.test_comparison._data_largest)

    def test_store_largest_complex_(self):
        # Normally if a complex data set set as part of __init__() however as
        # set in setUp() of part of Test class need to set manually here
        self.test_comparison._complex = True

        self.test_comparison._store_largest([complex(1, -5),
                                             complex(5, -1)])
        self.assertEqual(complex(5, 5), self.test_comparison._data_largest)
