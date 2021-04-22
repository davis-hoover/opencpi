#!/usr/bin/env python3

# Testing of code in complex_long_generator.py
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

from ocpi_testing.generator import ComplexLongGenerator


LONG_MIN = -(2**31)
LONG_MAX = (2**31) - 1


class TestComplexLongGenerator(unittest.TestCase):
    def setUp(self):
        self.test_generator = ComplexLongGenerator()
        self.seed = 67123

    def assertComplexLong(self, value):
        self.assertIsInstance(value, complex)
        self.assertGreaterEqual(value.real, LONG_MIN)
        self.assertLessEqual(value.real, LONG_MAX)
        self.assertGreaterEqual(value.imag, LONG_MIN)
        self.assertLessEqual(value.imag, LONG_MAX)

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
            self.assertComplexLong(value)

    def test_typical_same_seed_same_messages(self):
        messages_1 = self.test_generator.generate(
            self.seed, "typical", None, "01", "02")
        messages_2 = self.test_generator.generate(
            self.seed, "typical", None, "01", "02")

        self.assertEqual(messages_1, messages_2)

    def test_typical_single_wave(self):
        frequency = 0.1
        amplitude = 2500000
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
        scaled_data = messages[0]["data"][0].real / amplitude
        scaled_data = min(1, scaled_data)
        scaled_data = max(-1, scaled_data)
        phase = math.acos(scaled_data)
        # As inverse cosine (acos) is not unique for all inputs, determine the
        # gradient and so quadrant the wave is in
        if messages[0]["data"][0].real < messages[0]["data"][1].real:
            phase = -phase

        reference_data = [0] * len(messages[0]["data"])
        for index in range(len(reference_data)):
            reference_data[index] = complex(
                int(amplitude * math.cos(2 * math.pi * frequency * index
                                         + phase)),
                int(amplitude * math.sin(2 * math.pi * frequency * index +
                                         phase)))

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(len(messages[0]["data"]),
                         self.test_generator.SAMPLE_DATA_LENGTH)
        for index, (test_value, reference_value) in enumerate(
                zip(messages[0]["data"], reference_data)):
            self.assertComplexLong(test_value)
            # Ensure the error between values is less than 4
            self.assertLess(abs(test_value - reference_value), 4)

    def test_sample_all_zero_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "sample", "all_zero", "01", "02")

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(len(messages[0]["data"]),
                         self.test_generator.SAMPLE_DATA_LENGTH)
        for value in messages[0]["data"]:
            self.assertComplexLong(value)
            self.assertEqual(value, complex(0, 0))

    def test_sample_all_maximum_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "sample", "all_maximum", "01", "02")

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(len(messages[0]["data"]),
                         self.test_generator.SAMPLE_DATA_LENGTH)
        for value in messages[0]["data"]:
            self.assertComplexLong(value)
            self.assertEqual(value, complex(LONG_MAX, LONG_MAX))

    def test_sample_all_minimum_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "sample", "all_minimum", "01", "02")

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(len(messages[0]["data"]),
                         self.test_generator.SAMPLE_DATA_LENGTH)
        for value in messages[0]["data"]:
            self.assertComplexLong(value)
            self.assertEqual(value, complex(LONG_MIN, LONG_MIN))

    def test_sample_real_zero_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "sample", "real_zero", "01", "02")

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(len(messages[0]["data"]),
                         self.test_generator.SAMPLE_DATA_LENGTH)
        for value in messages[0]["data"]:
            self.assertComplexLong(value)
            self.assertEqual(value.real, 0)

    def test_sample_imaginary_zero_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "sample", "imaginary_zero", "01", "02")

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(len(messages[0]["data"]),
                         self.test_generator.SAMPLE_DATA_LENGTH)
        for value in messages[0]["data"]:
            self.assertComplexLong(value)
            self.assertEqual(value.imag, 0)

    def test_sample_large_positive_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "sample", "large_positive", "01", "02")

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(len(messages[0]["data"]),
                         self.test_generator.SAMPLE_DATA_LENGTH)
        for value in messages[0]["data"]:
            self.assertComplexLong(value)

    def test_sample_large_negative_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "sample", "large_negative", "01", "02")

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(len(messages[0]["data"]),
                         self.test_generator.SAMPLE_DATA_LENGTH)
        for value in messages[0]["data"]:
            self.assertComplexLong(value)

    def test_sample_near_zero_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "sample", "near_zero", "01", "02")

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(len(messages[0]["data"]),
                         self.test_generator.SAMPLE_DATA_LENGTH)
        for value in messages[0]["data"]:
            self.assertComplexLong(value)

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
            self.assertComplexLong(value)

    def test_full_scale_random_sample_values_set_number_of_samples(self):
        number_of_values = 100
        values = self.test_generator._full_scale_random_sample_values(
            number_of_values)

        self.assertEqual(len(values), number_of_values)
        for value in values:
            self.assertComplexLong(value)

    def test_get_sample_values_none_number_of_samples(self):
        values = self.test_generator._get_sample_values()

        self.assertEqual(len(values), self.test_generator.SAMPLE_DATA_LENGTH)
        for value in values:
            self.assertComplexLong(value)

    def test_get_sample_values_set_number_of_samples(self):
        number_of_values = 100
        values = self.test_generator._get_sample_values(number_of_values)

        self.assertEqual(len(values), number_of_values)
        for value in values:
            self.assertComplexLong(value)
