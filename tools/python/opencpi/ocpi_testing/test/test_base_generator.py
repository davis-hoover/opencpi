#!/usr/bin/env python3

# Testing of code in base_generator.py
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

from ocpi_testing.generator.base_generator import BaseGenerator


class TestGenerator(BaseGenerator):
    def typical(self, seed, subcase):
        return [{"opcode": "sample", "data": [1]}]

    def sample(self, seed, subcase):
        return [{"opcode": "sample", "data": [1]}]

    def _full_scale_random_sample_values(self, number_of_samples=None):
        if number_of_samples is None:
            number_of_samples = self.SAMPLE_DATA_LENGTH
        return [1] * number_of_samples

    def _get_sample_values(self, number_of_samples=None):
        if number_of_samples is None:
            number_of_samples = self.SAMPLE_DATA_LENGTH
        return [1] * number_of_samples


class TestBaseGenerator(unittest.TestCase):
    def setUp(self):
        self.test_generator = TestGenerator()
        self.seed = 5

    def assertSampleMessagesLengthEqual(self, messages_1, messages_2):
        # Check total data length is same as for main port
        messages_1_data_length = 0
        messages_2_data_length = 0
        for message in messages_1:
            if message["opcode"] == "sample":
                messages_1_data_length = \
                    messages_1_data_length + len(message["data"])
        for message in messages_2:
            if message["opcode"] == "sample":
                messages_2_data_length = \
                    messages_2_data_length + len(message["data"])

        self.assertEqual(messages_1_data_length, messages_2_data_length)

    def test_typical(self):
        messages = self.test_generator.generate(
            self.seed, "typical", None, "01", "02")

    def test_property(self):
        messages = self.test_generator.generate(
            self.seed, "property", None, "01", "02")

        # Can only check message type here as data would normally be generated
        # by child class which would be for a specific protocol - however here
        # this is not implemented.
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["opcode"], "sample")

    def test_input_stressing(self):
        messages = self.test_generator.generate(
            self.seed, "input_stressing", None, "01", "02")

        # Can only check message type here as data would normally be generated
        # by child class which would be for a specific protocol - however here
        # this is not implemented.
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["opcode"], "sample")

    def test_input_stressing_other_port(self):
        messages = self.test_generator.generate(
            self.seed, "input_stressing_other_port", None, "01", "02")

        # Can only check message type here as data would normally be generated
        # by child class which would be for a specific protocol - however here
        # this is not implemented.
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["opcode"], "sample")

    def test_message_size_shortest_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "message_size", "shortest", "01", "02")

        # Can only check message type here as data would normally be generated
        # by child class which would be for a specific protocol - however here
        # this is not implemented.
        self.assertEqual(len(messages),
                         self.test_generator.MESSAGE_SIZE_NUMBER_OF_MESSAGES)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(len(messages[0]["data"]),
                         self.test_generator.MESSAGE_SIZE_SHORTEST)

    def test_message_size_different_sizes(self):
        messages_1 = self.test_generator.generate(
            self.seed, "message_size", "different_sizes", "01", "02")
        messages_2 = self.test_generator.generate(
            self.seed, "message_size", "different_sizes", "01", "02")

        # All messages should have a sample opcode
        for message in messages_1:
            self.assertEqual(message["opcode"], "sample")
        for message in messages_2:
            self.assertEqual(message["opcode"], "sample")

        # Total number of data samples in all messages should be equal
        messages_1_total_data = 0
        messages_2_total_data = 0
        # Cannot do as one loop as there may be a different number of messages
        for message in messages_1:
            messages_1_total_data = \
                messages_1_total_data + len(message["data"])
        for message in messages_2:
            messages_2_total_data = \
                messages_2_total_data + len(message["data"])
        self.assertEqual(messages_1_total_data, messages_2_total_data)

    def test_message_size_invalid_subcase(self):
        with self.assertRaises(ValueError):
            self.test_generator.generate(
                self.seed, "message_size", "invalid_subcase", "01", "02")

    def test_time_zero_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "time", "zero", "01", "02")

        # The data in sample messages is not checked as generated by the test
        # implementation, as in a true use case the child class would define
        # the data content for the specific protocol this is used for. However,
        # that a sample message is present is checked.
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(messages[1]["opcode"], "time")
        self.assertEqual(messages[1]["data"], 0.0)
        self.assertEqual(messages[2]["opcode"], "sample")

    def test_time_positive_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "time", "positive", "01", "02")

        # The data in sample messages is not checked as generated by the test
        # implementation, as in a true use case the child class would define
        # the data content for the specific protocol this is used for. However,
        # that a sample message is present is checked.
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(messages[1]["opcode"], "time")
        self.assertGreater(messages[1]["data"], 0.0)
        self.assertLess(messages[1]["data"], self.test_generator.TIME_MAX)
        self.assertEqual(messages[2]["opcode"], "sample")

    def test_time_maximum_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "time", "maximum", "01", "02")

        # The data in sample messages is not checked as generated by the test
        # implementation, as in a true use case the child class would define
        # the data content for the specific protocol this is used for. However,
        # that a sample message is present is checked.
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(messages[1]["opcode"], "time")
        self.assertEqual(messages[1]["data"], self.test_generator.TIME_MAX)
        self.assertEqual(messages[2]["opcode"], "sample")

    def test_time_consecutive_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "time", "consecutive", "01", "02")

        # The data in sample messages is not checked as generated by the test
        # implementation, as in a true use case the child class would define
        # the data content for the specific protocol this is used for. However,
        # that a sample message is present is checked.
        self.assertEqual(len(messages), 4)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(messages[1]["opcode"], "time")
        self.assertGreater(messages[1]["data"], 0.0)
        self.assertLess(messages[1]["data"], self.test_generator.TIME_MAX)
        self.assertEqual(messages[2]["opcode"], "time")
        self.assertGreater(messages[2]["data"], 0.0)
        self.assertLess(messages[2]["data"], self.test_generator.TIME_MAX)
        self.assertEqual(messages[3]["opcode"], "sample")

    def test_time_invalid_subcase(self):
        with self.assertRaises(ValueError):
            self.test_generator.generate(
                self.seed, "time", "invalid_subcase", "01", "02")

    def test_time_other_port_zero_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "time_other_port", "zero", "01", "02")

        # The data in sample messages is not checked as generated by the test
        # implementation, as in a true use case the child class would define
        # the data content for the specific protocol this is used for. However,
        # that a sample message is present is checked.
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(messages[1]["opcode"], "sample")

        main_port = self.test_generator.generate(
            self.seed, "time", "zero", "01", "02")
        self.assertSampleMessagesLengthEqual(messages, main_port)

    def test_time_other_port_positive_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "time_other_port", "positive", "01", "02")

        # The data in sample messages is not checked as generated by the test
        # implementation, as in a true use case the child class would define
        # the data content for the specific protocol this is used for. However,
        # that a sample message is present is checked.
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(messages[1]["opcode"], "sample")

        main_port = self.test_generator.generate(
            self.seed, "time", "positive", "01", "02")
        self.assertSampleMessagesLengthEqual(messages, main_port)

    def test_time_other_port_maximum_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "time_other_port", "maximum", "01", "02")

        # The data in sample messages is not checked as generated by the test
        # implementation, as in a true use case the child class would define
        # the data content for the specific protocol this is used for. However,
        # that a sample message is present is checked.
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(messages[1]["opcode"], "sample")

        main_port = self.test_generator.generate(
            self.seed, "time", "maximum", "01", "02")
        self.assertSampleMessagesLengthEqual(messages, main_port)

    def test_time_other_port_consecutive_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "time_other_port", "consecutive", "01", "02")

        # The data in sample messages is not checked as generated by the test
        # implementation, as in a true use case the child class would define
        # the data content for the specific protocol this is used for. However,
        # that a sample message is present is checked.
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(messages[1]["opcode"], "sample")

        main_port = self.test_generator.generate(
            self.seed, "time", "consecutive", "01", "02")
        self.assertSampleMessagesLengthEqual(messages, main_port)

    def test_time_other_port_invalid_subcase(self):
        with self.assertRaises(ValueError):
            self.test_generator.generate(
                self.seed, "time_other_port", "invalid_subcase", "01", "02")

    def test_sample_interval_zero_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "sample_interval", "zero", "01", "02")

        # The data in sample messages is not checked as generated by the test
        # implementation, as in a true use case the child class would define
        # the data content for the specific protocol this is used for. However,
        # that a sample message is present is checked.
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(messages[1]["opcode"], "sample_interval")
        self.assertEqual(messages[1]["data"], 0.0)
        self.assertEqual(messages[2]["opcode"], "sample")

    def test_sample_interval_positive_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "sample_interval", "positive", "01", "02")

        # The data in sample messages is not checked as generated by the test
        # implementation, as in a true use case the child class would define
        # the data content for the specific protocol this is used for. However,
        # that a sample message is present is checked.
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(messages[1]["opcode"], "sample_interval")
        self.assertGreater(messages[1]["data"], 0.0)
        self.assertLess(messages[1]["data"],
                        self.test_generator.SAMPLE_INTERVAL_MAX)
        self.assertEqual(messages[2]["opcode"], "sample")

    def test_sample_interval_maximum_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "sample_interval", "maximum", "01", "02")

        # The data in sample messages is not checked as generated by the test
        # implementation, as in a true use case the child class would define
        # the data content for the specific protocol this is used for. However,
        # that a sample message is present is checked.
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(messages[1]["opcode"], "sample_interval")
        self.assertEqual(messages[1]["data"],
                         self.test_generator.SAMPLE_INTERVAL_MAX)
        self.assertEqual(messages[2]["opcode"], "sample")

    def test_sample_interval_consecutive_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "sample_interval", "consecutive", "01", "02")

        # The data in sample messages is not checked as generated by the test
        # implementation, as in a true use case the child class would define
        # the data content for the specific protocol this is used for. However,
        # that a sample message is present is checked.
        self.assertEqual(len(messages), 4)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(messages[1]["opcode"], "sample_interval")
        self.assertGreater(messages[1]["data"], 0.0)
        self.assertLess(messages[1]["data"],
                        self.test_generator.SAMPLE_INTERVAL_MAX)
        self.assertEqual(messages[2]["opcode"], "sample_interval")
        self.assertGreater(messages[2]["data"], 0.0)
        self.assertLess(messages[2]["data"],
                        self.test_generator.SAMPLE_INTERVAL_MAX)
        self.assertEqual(messages[3]["opcode"], "sample")

    def test_sample_interval_invalid_subcase(self):
        with self.assertRaises(ValueError):
            self.test_generator.generate(
                self.seed, "sample_interval", "invalid_subcase", "01", "02")

    def test_sample_interval_other_port_zero_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "sample_interval_other_port", "zero", "01", "02")

        # The data in sample messages is not checked as generated by the test
        # implementation, as in a true use case the child class would define
        # the data content for the specific protocol this is used for. However,
        # that a sample message is present is checked.
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(messages[1]["opcode"], "sample")

        main_port = self.test_generator.generate(
            self.seed, "sample_interval", "zero", "01", "02")
        self.assertSampleMessagesLengthEqual(messages, main_port)

    def test_sample_interval_other_port_positive_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "sample_interval_other_port", "positive", "01", "02")

        # The data in sample messages is not checked as generated by the test
        # implementation, as in a true use case the child class would define
        # the data content for the specific protocol this is used for. However,
        # that a sample message is present is checked.
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(messages[1]["opcode"], "sample")

        main_port = self.test_generator.generate(
            self.seed, "sample_interval", "positive", "01", "02")
        self.assertSampleMessagesLengthEqual(messages, main_port)

    def test_sample_interval__other_port_maximum_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "sample_interval_other_port", "maximum", "01", "02")

        # The data in sample messages is not checked as generated by the test
        # implementation, as in a true use case the child class would define
        # the data content for the specific protocol this is used for. However,
        # that a sample message is present is checked.
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(messages[1]["opcode"], "sample")

        main_port = self.test_generator.generate(
            self.seed, "sample_interval", "maximum", "01", "02")
        self.assertSampleMessagesLengthEqual(messages, main_port)

    def test_sample_interval_other_port_consecutive_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "sample_interval_other_port", "consecutive", "01", "02")

        # The data in sample messages is not checked as generated by the test
        # implementation, as in a true use case the child class would define
        # the data content for the specific protocol this is used for. However,
        # that a sample message is present is checked.
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(messages[1]["opcode"], "sample")

        main_port = self.test_generator.generate(
            self.seed, "sample_interval", "consecutive", "01", "02")
        self.assertSampleMessagesLengthEqual(messages, main_port)

    def test_sample_interval_other_port_invalid_subcase(self):
        with self.assertRaises(ValueError):
            self.test_generator.generate(
                self.seed, "sample_interval_other_port", "invalid_subcase", "01", "02")

    def test_flush_single_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "flush", "single", "01", "02")

        # The data in sample messages is not checked as generated by the test
        # implementation, as in a true use case the child class would define
        # the data content for the specific protocol this is used for. However,
        # that a sample message is present is checked.
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(messages[1]["opcode"], "flush")
        self.assertIsNone(messages[1]["data"])
        self.assertEqual(messages[2]["opcode"], "sample")

    def test_flush_consecutive_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "flush", "consecutive", "01", "02")

        # The data in sample messages is not checked as generated by the test
        # implementation, as in a true use case the child class would define
        # the data content for the specific protocol this is used for. However,
        # that a sample message is present is checked.
        self.assertEqual(len(messages), 4)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(messages[1]["opcode"], "flush")
        self.assertIsNone(messages[1]["data"])
        self.assertEqual(messages[2]["opcode"], "flush")
        self.assertIsNone(messages[2]["data"])
        self.assertEqual(messages[3]["opcode"], "sample")

    def test_flush_invalid_subcase(self):
        with self.assertRaises(ValueError):
            self.test_generator.generate(
                self.seed, "flush", "invalid_subcase", "01", "02")

    def test_flush_other_port_single_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "flush_other_port", "single", "01", "02")

        # The data in sample messages is not checked as generated by the test
        # implementation, as in a true use case the child class would define
        # the data content for the specific protocol this is used for. However,
        # that a sample message is present is checked.
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(messages[1]["opcode"], "sample")

        main_port = self.test_generator.generate(
            self.seed, "flush", "single", "01", "02")
        self.assertSampleMessagesLengthEqual(messages, main_port)

    def test_flush_other_port_consecutive_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "flush_other_port", "consecutive", "01", "02")

        # The data in sample messages is not checked as generated by the test
        # implementation, as in a true use case the child class would define
        # the data content for the specific protocol this is used for. However,
        # that a sample message is present is checked.
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(messages[1]["opcode"], "sample")

        main_port = self.test_generator.generate(
            self.seed, "flush", "single", "01", "02")
        self.assertSampleMessagesLengthEqual(messages, main_port)

    def test_flush_other_port_invalid_subcase(self):
        with self.assertRaises(ValueError):
            self.test_generator.generate(
                self.seed, "flush_other_port", "invalid_subcase", "01", "02")

    def test_discontinuity_single_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "discontinuity", "single", "01", "02")

        # The data in sample messages is not checked as generated by the test
        # implementation, as in a true use case the child class would define
        # the data content for the specific protocol this is used for. However,
        # that a sample message is present is checked.
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(messages[1]["opcode"], "discontinuity")
        self.assertIsNone(messages[1]["data"])
        self.assertEqual(messages[2]["opcode"], "sample")

    def test_discontinuity_consecutive_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "discontinuity", "consecutive", "01", "02")

        # The data in sample messages is not checked as generated by the test
        # implementation, as in a true use case the child class would define
        # the data content for the specific protocol this is used for. However,
        # that a sample message is present is checked.
        self.assertEqual(len(messages), 4)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(messages[1]["opcode"], "discontinuity")
        self.assertIsNone(messages[1]["data"])
        self.assertEqual(messages[2]["opcode"], "discontinuity")
        self.assertIsNone(messages[2]["data"])
        self.assertEqual(messages[3]["opcode"], "sample")

    def test_discontinuity_invalid_subcase(self):
        with self.assertRaises(ValueError):
            self.test_generator.generate(
                self.seed, "discontinuity", "invalid_subcase", "01", "02")

    def test_discontinuity_other_port_single_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "discontinuity_other_port", "single", "01", "02")

        # The data in sample messages is not checked as generated by the test
        # implementation, as in a true use case the child class would define
        # the data content for the specific protocol this is used for. However,
        # that a sample message is present is checked.
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(messages[1]["opcode"], "sample")

        main_port = self.test_generator.generate(
            self.seed, "discontinuity", "single", "01", "02")
        self.assertSampleMessagesLengthEqual(messages, main_port)

    def test_discontinuity_other_port_consecutive_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "discontinuity_other_port", "consecutive", "01", "02")

        # The data in sample messages is not checked as generated by the test
        # implementation, as in a true use case the child class would define
        # the data content for the specific protocol this is used for. However,
        # that a sample message is present is checked.
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(messages[1]["opcode"], "sample")

        main_port = self.test_generator.generate(
            self.seed, "discontinuity", "consecutive", "01", "02")
        self.assertSampleMessagesLengthEqual(messages, main_port)

    def test_discontinuity_other_port_invalid_subcase(self):
        with self.assertRaises(ValueError):
            self.test_generator.generate(
                self.seed, "discontinuity_other_port", "invalid_subcase", "01", "02")

    def test_metadata_zero_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "metadata", "zero", "01", "02")

        # The data in sample messages is not checked as generated by the test
        # implementation, as in a true use case the child class would define
        # the data content for the specific protocol this is used for. However,
        # that a sample message is present is checked.
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(messages[1]["opcode"], "metadata")
        self.assertEqual(messages[1]["data"]["id"], 0)
        self.assertEqual(messages[1]["data"]["value"], 0)
        self.assertEqual(messages[2]["opcode"], "sample")

    def test_metadata_positive_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "metadata", "positive", "01", "02")

        # The data in sample messages is not checked as generated by the test
        # implementation, as in a true use case the child class would define
        # the data content for the specific protocol this is used for. However,
        # that a sample message is present is checked.
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(messages[1]["opcode"], "metadata")
        self.assertGreater(messages[1]["data"]["id"], 0)
        self.assertLess(messages[1]["data"]["id"],
                        self.test_generator.METADATA_ID_MAX)
        self.assertGreater(messages[1]["data"]["value"], 0)
        self.assertLess(messages[1]["data"]["value"],
                        self.test_generator.METADATA_VALUE_MAX)
        self.assertEqual(messages[2]["opcode"], "sample")

    def test_metadata_maximum_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "metadata", "maximum", "01", "02")

        # The data in sample messages is not checked as generated by the test
        # implementation, as in a true use case the child class would define
        # the data content for the specific protocol this is used for. However,
        # that a sample message is present is checked.
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(messages[1]["opcode"], "metadata")
        self.assertEqual(messages[1]["data"]["id"],
                         self.test_generator.METADATA_ID_MAX)
        self.assertEqual(messages[1]["data"]["value"],
                         self.test_generator.METADATA_VALUE_MAX)
        self.assertEqual(messages[2]["opcode"], "sample")

    def test_metadata_consecutive_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "metadata", "consecutive", "01", "02")

        # The data in sample messages is not checked as generated by the test
        # implementation, as in a true use case the child class would define
        # the data content for the specific protocol this is used for. However,
        # that a sample message is present is checked.
        self.assertEqual(len(messages), 4)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(messages[1]["opcode"], "metadata")
        self.assertGreater(messages[1]["data"]["id"], 0)
        self.assertLess(messages[1]["data"]["id"],
                        self.test_generator.METADATA_ID_MAX)
        self.assertGreater(messages[1]["data"]["value"], 0)
        self.assertLess(messages[1]["data"]["value"],
                        self.test_generator.METADATA_VALUE_MAX)
        self.assertEqual(messages[2]["opcode"], "metadata")
        self.assertGreater(messages[2]["data"]["id"], 0)
        self.assertLess(messages[2]["data"]["id"],
                        self.test_generator.METADATA_ID_MAX)
        self.assertGreater(messages[2]["data"]["value"], 0)
        self.assertLess(messages[2]["data"]["value"],
                        self.test_generator.METADATA_VALUE_MAX)
        self.assertEqual(messages[3]["opcode"], "sample")

    def test_metadata_invalid_subcase(self):
        with self.assertRaises(ValueError):
            self.test_generator.generate(
                self.seed, "metadata", "invalid_subcase", "01", "02")

    def test_metadata_other_port_zero_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "metadata_other_port", "zero", "01", "02")

        # The data in sample messages is not checked as generated by the test
        # implementation, as in a true use case the child class would define
        # the data content for the specific protocol this is used for. However,
        # that a sample message is present is checked.
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(messages[1]["opcode"], "sample")

        main_port = self.test_generator.generate(
            self.seed, "metadata", "zero", "01", "02")
        self.assertSampleMessagesLengthEqual(messages, main_port)

    def test_metadata_other_port_positive_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "metadata_other_port", "positive", "01", "02")

        # The data in sample messages is not checked as generated by the test
        # implementation, as in a true use case the child class would define
        # the data content for the specific protocol this is used for. However,
        # that a sample message is present is checked.
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(messages[1]["opcode"], "sample")

        main_port = self.test_generator.generate(
            self.seed, "metadata", "positive", "01", "02")
        self.assertSampleMessagesLengthEqual(messages, main_port)

    def test_metadata_other_port_maximum_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "metadata_other_port", "maximum", "01", "02")

        # The data in sample messages is not checked as generated by the test
        # implementation, as in a true use case the child class would define
        # the data content for the specific protocol this is used for. However,
        # that a sample message is present is checked.
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(messages[1]["opcode"], "sample")

        main_port = self.test_generator.generate(
            self.seed, "metadata", "maximum", "01", "02")
        self.assertSampleMessagesLengthEqual(messages, main_port)

    def test_metadata_other_port_consecutive_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "metadata_other_port", "consecutive", "01", "02")

        # The data in sample messages is not checked as generated by the test
        # implementation, as in a true use case the child class would define
        # the data content for the specific protocol this is used for. However,
        # that a sample message is present is checked.
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["opcode"], "sample")
        self.assertEqual(messages[1]["opcode"], "sample")

        main_port = self.test_generator.generate(
            self.seed, "metadata", "consecutive", "01", "02")
        self.assertSampleMessagesLengthEqual(messages, main_port)

    def test_metadata_other_port_invalid_subcase(self):
        with self.assertRaises(ValueError):
            self.test_generator.generate(
                self.seed, "metadata_other_port", "invalid_subcase", "01", "02")

    def test_soak_sample_only_subcase(self):
        messages = self.test_generator.generate(
            self.seed, "soak", "sample_only", "01", "02")

        # The data in sample messages is not checked as generated by the test
        # implementation, as in a true use case the child class would define
        # the data content for the specific protocol this is used for. However,
        # that a sample message is present is checked.
        self.assertGreater(len(messages), 0)
        self.assertLess(len(messages), 9)
        for index, message in enumerate(messages):
            self.assertEqual(message["opcode"], "sample",
                             msg=f"Message {index} not a sample message")

        # Ensure the total length of all messages is SAMPLE_DATA_LENGTH.
        total_sample_length = 0
        for message in messages:
            if message["opcode"] == "sample":
                total_sample_length = total_sample_length + len(
                    message["data"])
        self.assertEqual(self.test_generator.SAMPLE_DATA_LENGTH,
                         total_sample_length)

        # Make sure all sample messages have a length greater than zero
        for message in messages:
            self.assertGreater(len(message["data"]), 0)

    def test_soak_sample_only_subcase_same_seed_same_message(self):
        messages_1 = self.test_generator.generate(
            self.seed, "soak", "sample_only", "01", "02")
        messages_2 = self.test_generator.generate(
            self.seed, "soak", "sample_only", "01", "02")

        self.assertEqual(messages_1, messages_2)

    def test_soak_all_opcodes(self):
        messages = self.test_generator.generate(
            self.seed, "soak", "all_opcodes", "01", "02")

        # The data in sample messages is not checked as generated by the test
        # implementation, as in a true use case the child class would define
        # the data content for the specific protocol this is used for. However,
        # that a sample message is present is checked.
        self.assertGreater(len(messages), 0)
        self.assertLess(len(messages), 9)

        # Ensure the total length of all messages is SAMPLE_DATA_LENGTH.
        total_sample_length = 0
        for message in messages:
            if message["opcode"] == "sample":
                total_sample_length = total_sample_length + len(
                    message["data"])
        self.assertEqual(self.test_generator.SAMPLE_DATA_LENGTH,
                         total_sample_length)

        # Make sure all sample messages have a length greater than zero
        for message in messages:
            if message["opcode"] == "sample":
                self.assertGreater(len(message["data"]), 0)

    def test_soak_invalid_subcase(self):
        with self.assertRaises(ValueError):
            self.test_generator.generate(
                self.seed, "soak", "invalid_subcase", "01", "02")
