#!/usr/bin/env python3

# Testing of code in boolean_generator.py
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

from ocpi_testing.generator import BooleanGenerator


class TestBooleanGenerator(unittest.TestCase):
    def setUp(self):
        self.test_generator = BooleanGenerator()
        self.seed = 7

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
        for index, value in enumerate(messages[0]["data"]):
            self.assertIsInstance(value, bool,
                                  msg=f"Value {index} is not a boolean")

    def test_typical_same_seed_same_messages(self):
        messages_1 = self.test_generator.generate(
            self.seed, "typical", None, "01", "02")
        messages_2 = self.test_generator.generate(
            self.seed, "typical", None, "01", "02")

        self.assertEqual(messages_1, messages_2)

    def test_sample_all_zero_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "sample", "all_zero", "01", "02")

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(len(messages[0]["data"]),
                         self.test_generator.SAMPLE_DATA_LENGTH)
        for index, value in enumerate(messages[0]["data"]):
            self.assertFalse(value, msg=f"Value {index} is not False")

    def test_sample_all_maximum_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "sample", "all_maximum", "01", "02")

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(len(messages[0]["data"]),
                         self.test_generator.SAMPLE_DATA_LENGTH)
        for index, value in enumerate(messages[0]["data"]):
            self.assertTrue(value, msg=f"Value {index} is not True")

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

    def test_sample_invalid_subcase(self):
        with self.assertRaises(ValueError):
            self.test_generator.generate(
                self.seed, "sample", "invalid_subcase", "01", "02")

    def test_full_scale_random_sample_values_none_number_of_samples(self):
        values = self.test_generator._full_scale_random_sample_values()

        self.assertEqual(len(values), self.test_generator.SAMPLE_DATA_LENGTH)
        for index, value in enumerate(values):
            self.assertIsInstance(value, bool,
                                  msg=f"Value {index} is not a boolean")

    def test_full_scale_random_sample_values_set_number_of_samples(self):
        number_of_values = 100
        values = self.test_generator._full_scale_random_sample_values(
            number_of_values)

        self.assertEqual(len(values), number_of_values)
        for index, value in enumerate(values):
            self.assertIsInstance(value, bool,
                                  msg=f"Value {index} is not a boolean")

    def test_get_sample_values_none_number_of_samples(self):
        values = self.test_generator._get_sample_values()

        self.assertEqual(len(values), self.test_generator.SAMPLE_DATA_LENGTH)
        for index, value in enumerate(values):
            self.assertIsInstance(value, bool,
                                  msg=f"Value {index} is not a boolean")

    def test_get_sample_values_set_number_of_samples(self):
        number_of_values = 100
        values = self.test_generator._get_sample_values(number_of_values)

        self.assertEqual(len(values), number_of_values)
        for index, value in enumerate(values):
            self.assertIsInstance(value, bool,
                                  msg=f"Value {index} is not a boolean")
