#!/usr/bin/env python3

# Testing of code in complex_double_generator.py
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

from ocpi_testing.generator import ComplexDoubleGenerator


# The below lines are longer than permitted under the style guidelines, however
# there is not a sensible way to maintain these numbers without casting being
# strings or integers, and to prevent the risk of the incorrect value being
# stored this deviation from the style guide is allowed.
DOUBLE_MIN = -179769313486231570814527423731704356798070567525844996598917476803157260780028538760589558632766878171540458953514382464234321326889464182768467546703537516986049910576551282076245490090389328944075868508455133942304583236903222948165808559332123348274797826204144723168738177180919299881250404026184124858368.0
DOUBLE_MAX = 179769313486231570814527423731704356798070567525844996598917476803157260780028538760589558632766878171540458953514382464234321326889464182768467546703537516986049910576551282076245490090389328944075868508455133942304583236903222948165808559332123348274797826204144723168738177180919299881250404026184124858368.0


class TestComplexDoubleGenerator(unittest.TestCase):
    def setUp(self):
        self.test_generator = ComplexDoubleGenerator()
        self.seed = 1166

    def assertComplexDouble(self, value):
        self.assertIsInstance(value, complex)
        if math.isnan(value.real) or math.isnan(value.imag) or \
                math.isinf(value.real) or math.isinf(value.imag):
            return
        self.assertGreaterEqual(value.real, DOUBLE_MIN)
        self.assertLessEqual(value.real, DOUBLE_MAX)
        self.assertGreaterEqual(value.imag, DOUBLE_MIN)
        self.assertLessEqual(value.imag, DOUBLE_MAX)

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
            self.assertComplexDouble(value)

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
                int(amplitude * math.cos(2 * math.pi * frequency * index +
                                         phase)),
                int(amplitude * math.sin(2 * math.pi * frequency * index +
                                         phase)))

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(len(messages[0]["data"]),
                         self.test_generator.SAMPLE_DATA_LENGTH)
        for index, (test_value, reference_value) in enumerate(
                zip(messages[0]["data"], reference_data)):
            self.assertComplexDouble(test_value)
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
            self.assertComplexDouble(value)
            self.assertEqual(value, complex(0, 0))

    def test_sample_all_maximum_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "sample", "all_maximum", "01", "02")

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(len(messages[0]["data"]),
                         self.test_generator.SAMPLE_DATA_LENGTH)
        for value in messages[0]["data"]:
            self.assertComplexDouble(value)
            self.assertEqual(value, complex(DOUBLE_MAX, DOUBLE_MAX))

    def test_sample_all_minimum_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "sample", "all_minimum", "01", "02")

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(len(messages[0]["data"]),
                         self.test_generator.SAMPLE_DATA_LENGTH)
        for value in messages[0]["data"]:
            self.assertComplexDouble(value)
            self.assertEqual(value, complex(DOUBLE_MIN, DOUBLE_MIN))

    def test_sample_real_zero_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "sample", "real_zero", "01", "02")

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(len(messages[0]["data"]),
                         self.test_generator.SAMPLE_DATA_LENGTH)
        for value in messages[0]["data"]:
            self.assertComplexDouble(value)
            self.assertEqual(value.real, 0)

    def test_sample_imaginary_zero_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "sample", "imaginary_zero", "01", "02")

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(len(messages[0]["data"]),
                         self.test_generator.SAMPLE_DATA_LENGTH)
        for value in messages[0]["data"]:
            self.assertComplexDouble(value)
            self.assertEqual(value.imag, 0)

    def test_sample_large_positive_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "sample", "large_positive", "01", "02")

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(len(messages[0]["data"]),
                         self.test_generator.SAMPLE_DATA_LENGTH)
        # Ensure the error between values is less than 0.1%
        min_expected_value = DOUBLE_MAX - \
            (1.001 * self.test_generator.SAMPLE_NEAR_RANGE)
        for value in messages[0]["data"]:
            self.assertComplexDouble(value)
            self.assertGreaterEqual(value.real, min_expected_value)
            self.assertGreaterEqual(value.imag, min_expected_value)

    def test_sample_large_negative_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "sample", "large_negative", "01", "02")

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(len(messages[0]["data"]),
                         self.test_generator.SAMPLE_DATA_LENGTH)
        # Ensure the error between values is less than 0.1%
        max_expected_value = DOUBLE_MIN + \
            (1.001 * self.test_generator.SAMPLE_NEAR_RANGE)
        for value in messages[0]["data"]:
            self.assertComplexDouble(value)
            self.assertLessEqual(value.real, max_expected_value)
            self.assertLessEqual(value.imag, max_expected_value)

    def test_sample_near_zero_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "sample", "near_zero", "01", "02")

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(len(messages[0]["data"]),
                         self.test_generator.SAMPLE_DATA_LENGTH)
        # Ensure the error between values is less than 0.1%
        max_expected_value = (1.001 * self.test_generator.SAMPLE_NEAR_RANGE)
        for value in messages[0]["data"]:
            self.assertComplexDouble(value)
            self.assertLessEqual(abs(value.real), max_expected_value)
            self.assertLessEqual(abs(value.imag), max_expected_value)

    def test_sample_positive_infinity_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "sample", "positive_infinity", "01", "02")

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(len(messages[0]["data"]),
                         self.test_generator.SAMPLE_DATA_LENGTH)
        self.assertIn(complex(float("inf"), float("inf")), messages[0]["data"])
        for value in messages[0]["data"]:
            self.assertComplexDouble(value)

    def test_sample_negative_infinity_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "sample", "negative_infinity", "01", "02")

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(len(messages[0]["data"]),
                         self.test_generator.SAMPLE_DATA_LENGTH)
        self.assertIn(complex(-float("inf"), -float("inf")),
                      messages[0]["data"])
        for value in messages[0]["data"]:
            self.assertComplexDouble(value)

    def test_sample_not_a_number_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "sample", "not_a_number", "01", "02")

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(len(messages[0]["data"]),
                         self.test_generator.SAMPLE_DATA_LENGTH)
        # Cannot use float("nan") in messages[0]["data"] as by convention all
        # comparisons to NaN return false, including the in list check.
        self.assertTrue(
            any([math.isnan(value.real) and math.isnan(value.imag) for
                 value in messages[0]["data"]]))
        for value in messages[0]["data"]:
            self.assertComplexDouble(value)

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
            self.assertComplexDouble(value)

    def test_full_scale_random_sample_values_set_number_of_samples(self):
        number_of_values = 100
        values = self.test_generator._full_scale_random_sample_values(
            number_of_values)

        self.assertEqual(len(values), number_of_values)
        for value in values:
            self.assertComplexDouble(value)

    def test_get_sample_values_none_number_of_samples(self):
        values = self.test_generator._get_sample_values()

        self.assertEqual(len(values), self.test_generator.SAMPLE_DATA_LENGTH)
        for value in values:
            self.assertComplexDouble(value)

    def test_get_sample_values_set_number_of_samples(self):
        number_of_values = 100
        values = self.test_generator._get_sample_values(number_of_values)

        self.assertEqual(len(values), number_of_values)
        for value in values:
            self.assertComplexDouble(value)
