#!/usr/bin/env python3

# Testing of code in unsigned_long_generator.py
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


import math
import unittest

import numpy

from ocpi_testing.generator import UnsignedLongGenerator


UNSIGNED_LONG_MIN = 0
UNSIGNED_LONG_MAX = (2**32) - 1


class TestUnsignedLongGenerator(unittest.TestCase):
    def setUp(self):
        self.test_generator = UnsignedLongGenerator()
        self.seed = 53127

    def assertUnsignedLong(self, value):
        self.assertIsInstance(value, int)
        self.assertGreaterEqual(value, UNSIGNED_LONG_MIN)
        self.assertLessEqual(value, UNSIGNED_LONG_MAX)

    def test_typical(self):
        messages = self.test_generator.generate(
            self.seed, "typical", None, "01", "02")

        # The value of data in sample messages is not checked as generated
        # using a random generator, so type and lengths of messages is checked
        # instead.
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(len(messages[0]["data"]),
                         self.test_generator.SAMPLE_DATA_LENGTH)
        for value in messages[0]["data"]:
            self.assertUnsignedLong(value)

    def test_typical_same_seed_same_messages(self):
        messages_1 = self.test_generator.generate(
            self.seed, "typical", None, "01", "02")
        messages_2 = self.test_generator.generate(
            self.seed, "typical", None, "01", "02")

        self.assertEqual(messages_1, messages_2)

    def test_typical_single_wave(self):
        frequency = 0.1
        amplitude = 50
        offset = UNSIGNED_LONG_MAX / 2
        self.test_generator.TYPICAL_NUMBER_OF_WAVES_MODAL = 1
        self.test_generator.TYPICAL_NUMBER_OF_WAVES_DISTRIBUTION_WIDTH = 1
        self.test_generator.TYPICAL_NUMBER_OF_WAVES_MIN = 1
        self.test_generator.TYPICAL_NUMBER_OF_WAVES_MAX = 1
        self.test_generator.TYPICAL_FREQUENCY_MEAN = frequency
        self.test_generator.TYPICAL_FREQUENCY_DISTRIBUTION_WIDTH = 0
        self.test_generator.TYPICAL_FREQUENCY_MIN = frequency
        self.test_generator.TYPICAL_FREQUENCY_MAX = frequency
        self.test_generator.TYPICAL_AMPLITUDE_MEAN = amplitude
        self.test_generator.TYPICAL_AMPLITUDE_DISTRIBUTION_WIDTH = 0

        messages = self.test_generator.generate(
            self.seed, "typical", None, "01", "02")

        # Cannot externally set the phase so determine
        # First keep value within acos support range
        scaled_data = (messages[0]["data"][0] - offset) / amplitude
        scaled_data = min(1, scaled_data)
        scaled_data = max(-1, scaled_data)
        phase = math.acos(scaled_data)
        # As inverse cosine (acos) is not unique for all inputs, determine the
        # gradient and so quadrant the wave is in
        if messages[0]["data"][0] < messages[0]["data"][1]:
            phase = -phase

        reference_data = [0] * len(messages[0]["data"])
        for index in range(len(reference_data)):
            reference_data[index] = int(
                amplitude * math.cos(2 * math.pi * frequency * index +
                                     phase) + offset)

        # Reference data will not be exact match, so ensure mean is small (in
        # relation to whole supported range of unsigned longs)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(len(messages[0]["data"]),
                         self.test_generator.SAMPLE_DATA_LENGTH)
        for index, (test_value, reference_value) in enumerate(
                zip(messages[0]["data"], reference_data)):
            self.assertUnsignedLong(test_value)
            # Ensure the error between values is less than 30
            self.assertLess(abs(test_value - reference_value), 30)

    def test_sample_all_zero_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "sample", "all_zero", "01", "02")

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(len(messages[0]["data"]),
                         self.test_generator.SAMPLE_DATA_LENGTH)
        for value in messages[0]["data"]:
            self.assertUnsignedLong(value)
            self.assertEqual(value, 0)

    def test_sample_all_maximum_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "sample", "all_maximum", "01", "02")

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(len(messages[0]["data"]),
                         self.test_generator.SAMPLE_DATA_LENGTH)
        for value in messages[0]["data"]:
            self.assertUnsignedLong(value)
            self.assertEqual(value, UNSIGNED_LONG_MAX)

    def test_sample_large_positive_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "sample", "large_positive", "01", "02")

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(len(messages[0]["data"]),
                         self.test_generator.SAMPLE_DATA_LENGTH)
        for value in messages[0]["data"]:
            self.assertUnsignedLong(value)

    def test_sample_near_zero_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "sample", "near_zero", "01", "02")

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(len(messages[0]["data"]),
                         self.test_generator.SAMPLE_DATA_LENGTH)
        for value in messages[0]["data"]:
            self.assertUnsignedLong(value)

    def test_sample_invalid_subcase(self):
        with self.assertRaises(ValueError):
            self.test_generator.generate(
                self.seed, "sample", "invalid_subcase", "01", "02")

    def test_message_size_longest_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "message_size", "longest", "01", "02")

        # Can only check message type here as data would normally be generated
        # by child class which would be for a specific protocol - however here
        # this is not implemented.
        self.assertEqual(len(messages),
                         self.test_generator.MESSAGE_SIZE_NUMBER_OF_MESSAGES)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(len(messages[0]["data"]),
                         self.test_generator.MESSAGE_SIZE_LONGEST)

    def test_full_scale_random_sample_values_none_number_of_samples(self):
        values = self.test_generator._full_scale_random_sample_values()

        self.assertEqual(len(values), self.test_generator.SAMPLE_DATA_LENGTH)
        for value in values:
            self.assertUnsignedLong(value)

    def test_full_scale_random_sample_values_set_number_of_samples(self):
        number_of_values = 100
        values = self.test_generator._full_scale_random_sample_values(
            number_of_values)

        self.assertEqual(len(values), number_of_values)
        for value in values:
            self.assertUnsignedLong(value)

    def test_get_sample_values_none_number_of_samples(self):
        values = self.test_generator._get_sample_values()

        self.assertEqual(len(values), self.test_generator.SAMPLE_DATA_LENGTH)
        for value in values:
            self.assertUnsignedLong(value)

    def test_get_sample_values_set_number_of_samples(self):
        number_of_values = 100
        values = self.test_generator._get_sample_values(number_of_values)

        self.assertEqual(len(values), number_of_values)
        for value in values:
            self.assertUnsignedLong(value)
