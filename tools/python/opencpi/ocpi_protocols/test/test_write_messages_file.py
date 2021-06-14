#!/usr/bin/env python3

# Test code in write_messages_file.py
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


import os
import unittest

from ocpi_protocols import WriteMessagesFile


class TestWriteMessagesFile(unittest.TestCase):
    # Testing of the protocol file parser / reader will be allowed to use
    # this file reader, so to prevent a circular test dependency this class and
    # testing must not use the protocol file parser / reader.
    _test_file = "test_data.bin"

    def setUp(self):
        if os.path.isfile(self._test_file):
            os.remove(self._test_file)

    def tearDown(self):
        if os.path.isfile(self._test_file):
            os.remove(self._test_file)

    def test_write_message_bool_sample(self):
        with WriteMessagesFile(
                self._test_file, "bool_timed_sample") as protocol:
            protocol.write_message("sample", [True, False] * 10)

        header = [0x14, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        data = [0x01, 0x00] * 10
        with open(self._test_file, "rb") as binary_file:
            self.assertEqual(binary_file.read(), bytes(header + data))

    def test_multiple_write_message(self):
        sample_data_1 = [1] * 10
        sample_data_2 = [2] * 10
        with WriteMessagesFile(
                self._test_file, "uchar_timed_sample") as protocol:
            protocol.write_message("sample_interval", 2**-26)
            protocol.write_message("time", 0.0)
            protocol.write_message("discontinuity")
            protocol.write_message("sample", sample_data_1)
            protocol.write_message("sample", sample_data_2)
            protocol.write_message("flush")

        # Generate the expected data to verify against
        headers = [
            # Sample interval
            [0x0C, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00],
            # Time
            [0x0C, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00],
            # Discontinuity
            [0x00, 0x00, 0x00, 0x00, 0x04, 0x00, 0x00, 0x00],
            # Sample
            [0x0A, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
            # Sample
            [0x0A, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
            # Flush
            [0x00, 0x00, 0x00, 0x00, 0x03, 0x00, 0x00, 0x00]]
        data = [
            # Sample interval
            [0x00, 0x00, 0x00, 0x00, 0x40, 0x00, 0x00, 0x00,
             0x00, 0x00, 0x00, 0x00],
            # Time
            [0x00] * 12,
            # Discontinuity
            [],
            # Sample
            sample_data_1,
            # Sample
            sample_data_2,
            # Flush
            []]
        test_data = []
        for header, data_body in zip(headers, data):
            test_data = test_data + header + data_body

        with open(self._test_file, "rb") as binary_file:
            self.assertEqual(binary_file.read(), bytes(test_data))

    def test_write_messages(self):
        sample_data_1 = [1] * 10
        sample_data_2 = [2] * 10

        # Test write
        headers = ({"opcode": "sample_interval"},
                   {"opcode": "time"},
                   {"opcode": "discontinuity"},
                   {"opcode": "sample"},
                   {"opcode": "sample"},
                   {"opcode": "flush"})
        messages_data = [2**-26,            # Sample interval
                         0.0,               # Time
                         [],                # Discontinuity
                         sample_data_1,     # Sample
                         sample_data_2,     # Sample
                         []]                # Flush
        with WriteMessagesFile(
                self._test_file, "uchar_timed_sample") as protocol:
            protocol.write_messages(headers, messages_data)

        # Generate the expected data to verify against
        headers = [
            # Sample interval
            [0x0C, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00],
            # Time
            [0x0C, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00],
            # Discontinuity
            [0x00, 0x00, 0x00, 0x00, 0x04, 0x00, 0x00, 0x00],
            # Sample
            [0x0A, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
            # Sample
            [0x0A, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
            # Flush
            [0x00, 0x00, 0x00, 0x00, 0x03, 0x00, 0x00, 0x00]]
        data = [
            # Sample interval
            [0x00, 0x00, 0x00, 0x00, 0x40, 0x00, 0x00, 0x00,
             0x00, 0x00, 0x00, 0x00],
            # Time
            [0x00] * 12,
            # Discontinuity
            [],
            # Sample
            sample_data_1,
            # Sample
            sample_data_2,
            # Flush
            []]
        test_data = []
        for header, data_body in zip(headers, data):
            test_data = test_data + header + data_body

        with open(self._test_file, "rb") as binary_file:
            self.assertEqual(binary_file.read(), bytes(test_data))

    def test_write_message_raw_data(self):
        data = bytes([0x01] * 10)
        with WriteMessagesFile(
                self._test_file, "uchar_timed_sample") as protocol:
            protocol.write_message("sample", data, raw_data=True)

        header = bytes([0x0A, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        with open(self._test_file, "rb") as binary_file:
            self.assertEqual(binary_file.read(), header + data)

    def test_write_dict_message(self):
        with WriteMessagesFile(
                self._test_file, "bool_timed_sample") as protocol:
            protocol.write_dict_message({"opcode": "sample",
                                         "data": [True, False] * 10})

        header = [0x14, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        data = [0x01, 0x00] * 10
        with open(self._test_file, "rb") as binary_file:
            self.assertEqual(binary_file.read(), bytes(header + data))

    def test_write_dict_messages(self):
        sample_data_1 = [1] * 10
        sample_data_2 = [2] * 10

        # Test write
        messages = ({"opcode": "sample_interval", "data": 2**-26},
                    {"opcode": "time", "data": 0.0},
                    {"opcode": "discontinuity", "data": []},
                    {"opcode": "sample", "data": sample_data_1},
                    {"opcode": "sample", "data": sample_data_2},
                    {"opcode": "flush", "data": []})

        with WriteMessagesFile(
                self._test_file, "uchar_timed_sample") as protocol:
            protocol.write_dict_messages(messages)

        # Generate the expected data to verify against
        headers = [
            # Sample interval
            [0x0c, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00],
            # Time
            [0x0c, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00],
            # Discontinuity
            [0x00, 0x00, 0x00, 0x00, 0x04, 0x00, 0x00, 0x00],
            # Sample
            [0x0A, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
            # Sample
            [0x0A, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
            # Flush
            [0x00, 0x00, 0x00, 0x00, 0x03, 0x00, 0x00, 0x00]]
        data = [
            # Sample interval
            [0x00, 0x00, 0x00, 0x00, 0x40, 0x00, 0x00, 0x00,
             0x00, 0x00, 0x00, 0x00],
            # Time
            [0x00] * 12,
            # Discontinuity
            [],
            # Sample
            sample_data_1,
            # Sample
            sample_data_2,
            # Flush
            []]
        test_data = []
        for header, data_body in zip(headers, data):
            test_data = test_data + header + data_body

        with open(self._test_file, "rb") as binary_file:
            self.assertEqual(binary_file.read(), bytes(test_data))

    def test_not_as_context_manager(self):
        protocol_file = WriteMessagesFile(self._test_file,
                                          "uchar_timed_sample")
        protocol_file.close()

        with open(self._test_file, "rb") as binary_file:
            self.assertEqual(binary_file.read(), bytes())

    def test_has_repr(self):
        with WriteMessagesFile(self._test_file, "char_timed_sample") as file:
            self.assertIsInstance(repr(file), str)

    def test_has_str(self):
        with WriteMessagesFile(self._test_file, "float_timed_sample") as file:
            self.assertIsInstance(str(file), str)
