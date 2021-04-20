#!/usr/bin/env python3

# Test code in parse_messages_file.py
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


import cProfile
import itertools
import os
import unittest

from ocpi_protocols import ParseMessagesFile, WriteMessagesFile


class TestParseMessagesFile(unittest.TestCase):
    # Testing of the protocol file parser / reader is allowed to use this
    # protocol file writer class. Since the testing of the file writer class
    # has not been allowed to use the file reader / parser the testing does not
    # have a circular test dependency. There is also a need for the file parser
    # and writer to work as opposites which is to be tested here.
    _test_file = "test_data.bin"

    def setUp(self):
        if os.path.isfile(self._test_file):
            os.remove(self._test_file)

        self._sample_data_1 = tuple([1] * 10)
        self._sample_data_2 = tuple([2] * 10)

        self._headers = [{"opcode": "sample_interval", "size": 12},
                         {"opcode": "time", "size": 12},
                         {"opcode": "discontinuity", "size": 0},
                         {"opcode": "sample", "size": 20},
                         {"opcode": "sample", "size": 20},
                         {"opcode": "flush", "size": 0}]

        with WriteMessagesFile(
                self._test_file, "short_timed_sample") as protocol:
            protocol.write_message("sample_interval", 2**-26)
            protocol.write_message("time", 0.0)
            protocol.write_message("discontinuity")
            protocol.write_message("sample", self._sample_data_1)
            protocol.write_message("sample", self._sample_data_2)
            protocol.write_message("flush")

    def tearDown(self):
        if os.path.isfile(self._test_file):
            os.remove(self._test_file)

    def test_header_read(self):
        with ParseMessagesFile(
                self._test_file, "short_timed_sample") as protocol:
            self.assertEqual(
                protocol.headers[2], self._headers[2])  # Can index
            self.assertEqual(protocol.headers, self._headers)

    def test_header_iterate(self):
        with ParseMessagesFile(
                self._test_file, "short_timed_sample") as protocol:
            for index, header in enumerate(protocol.headers):
                self.assertEqual(header, self._headers[index])

    def test_raw_data_read_non_sequential(self):
        with ParseMessagesFile(
                self._test_file, "short_timed_sample") as protocol:
            # Discontinuity
            self.assertEqual(protocol.messages_raw_data[2], bytes())
            # Sample data
            self.assertEqual(protocol.messages_raw_data[4], bytes(
                list(itertools.chain(*zip(self._sample_data_2,
                                          [0] * len(self._sample_data_2))))))
            # Sample interval
            self.assertEqual(protocol.messages_raw_data[0], bytes(
                [0x00, 0x00, 0x00, 0x00, 0x40, 0x00, 0x00, 0x00,
                 0x00, 0x00, 0x00, 0x00]))

    def test_raw_data_iterate(self):
        messages_raw_data = [
            # Sample interval
            bytes(
                [0x00, 0x00, 0x00, 0x00, 0x40, 0x00, 0x00, 0x00,
                 0x00, 0x00, 0x00, 0x00]),
            # Time
            bytes([0x00] * 12),
            # Discontinuity
            bytes(),
            # Sample data
            bytes(
                list(itertools.chain(*zip(self._sample_data_1,
                                          [0] * len(self._sample_data_1))))),
            # Sample data
            bytes(
                list(itertools.chain(*zip(self._sample_data_2,
                                          [0] * len(self._sample_data_2))))),
            # Flush
            bytes()
        ]
        with ParseMessagesFile(
                self._test_file, "short_timed_sample") as protocol:
            read_data = []
            for raw_data in protocol.messages_raw_data:
                read_data.append(raw_data)
        self.assertEqual(read_data, messages_raw_data)

    def test_raw_data_slice(self):
        messages_raw_data = [
            bytes([0x00] * 12),     # Time
            bytes(                  # Sample data
                list(itertools.chain(*zip(self._sample_data_1,
                                          [0] * len(self._sample_data_1)))))
        ]
        with ParseMessagesFile(
                self._test_file, "short_timed_sample") as protocol:
            self.assertEqual(protocol.messages_raw_data[1:5:2],
                             messages_raw_data)

    def test_raw_data_slice_no_start_index(self):
        messages_raw_data = [
            # Sample interval
            bytes(
                [0x00, 0x00, 0x00, 0x00, 0x40, 0x00, 0x00, 0x00,
                 0x00, 0x00, 0x00, 0x00]),
            # Time
            bytes([0x00] * 12),
            # Discontinuity (no data)
            bytes()]
        with ParseMessagesFile(
                self._test_file, "short_timed_sample") as protocol:
            self.assertEqual(protocol.messages_raw_data[:3],
                             messages_raw_data)

    def test_raw_data_slice_no_stop_index(self):
        messages_raw_data = [
            bytes(                              # Sample data
                list(itertools.chain(*zip(self._sample_data_2,
                                          [0] * len(self._sample_data_2))))),
            bytes()                             # Flush
        ]
        with ParseMessagesFile(
                self._test_file, "short_timed_sample") as protocol:
            self.assertEqual(protocol.messages_raw_data[4:],
                             messages_raw_data)

    def test_raw_data_negative_index(self):
        with ParseMessagesFile(
                self._test_file, "short_timed_sample") as protocol:
            self.assertEqual(protocol.messages_raw_data[-1], bytes())

    def test_raw_data_slice_negative(self):
        messages_raw_data = [
            bytes(                              # Sample data
                list(itertools.chain(*zip(self._sample_data_2,
                                          [0] * len(self._sample_data_2)))))
        ]

        with ParseMessagesFile(
                self._test_file, "short_timed_sample") as protocol:
            self.assertEqual(protocol.messages_raw_data[-2:-3:-1],
                             messages_raw_data)

    def test_data_read_non_sequential(self):
        with ParseMessagesFile(
                self._test_file, "short_timed_sample") as protocol:
            self.assertEqual(protocol.messages_data[2], None)
            self.assertEqual(protocol.messages_data[4], self._sample_data_2)
            self.assertEqual(protocol.messages_data[0], 2**-26)

    def test_data_iterate(self):
        messages_data = [2**-26,
                         0.0,
                         None,
                         self._sample_data_1,
                         self._sample_data_2,
                         None]
        with ParseMessagesFile(
                self._test_file, "short_timed_sample") as protocol:
            read_data = []
            for data in protocol.messages_data:
                read_data.append(data)
        self.assertEqual(read_data, messages_data)

    def test_data_slice(self):
        messages_data = [0.0,
                         self._sample_data_1]
        with ParseMessagesFile(
                self._test_file, "short_timed_sample") as protocol:
            self.assertEqual(protocol.messages_data[1:5:2], messages_data)

    def test_data_slice_no_start_index(self):
        messages_data = [2**-26,
                         0.0,
                         None]
        with ParseMessagesFile(
                self._test_file, "short_timed_sample") as protocol:
            self.assertEqual(protocol.messages_data[:3], messages_data)

    def test_data_slice_no_stop_index(self):
        messages_data = [self._sample_data_2,
                         None]
        with ParseMessagesFile(
                self._test_file, "short_timed_sample") as protocol:
            self.assertEqual(protocol.messages_data[4:], messages_data)

    def test_data_negative_index(self):
        with ParseMessagesFile(
                self._test_file, "short_timed_sample") as protocol:
            self.assertEqual(protocol.messages_data[-2], self._sample_data_2)

    def test_data_slice_negative(self):
        messages_data = [self._sample_data_2]

        with ParseMessagesFile(
                self._test_file, "short_timed_sample") as protocol:
            self.assertEqual(protocol.messages_data[-2:-3:-1],
                             messages_data)

    def test_get_all_messages(self):
        messages_data = [{"opcode": "sample_interval", "data": 2**-26},
                         {"opcode": "time", "data": 0.0, },
                         {"opcode": "discontinuity", "data": None, },
                         {"opcode": "sample", "data": self._sample_data_1, },
                         {"opcode": "sample", "data": self._sample_data_2, },
                         {"opcode": "flush", "data": None}]
        with ParseMessagesFile(
                self._test_file, "short_timed_sample") as protocol:
            self.assertEqual(protocol.get_all_messages(), messages_data)

    def test_get_all_messages_filter(self):
        messages_non_data = [{"opcode": "sample_interval", "data": 2**-26},
                             {"opcode": "time", "data": 0.0},
                             {"opcode": "discontinuity", "data": None},
                             {"opcode": "flush", "data": None}]
        non_data_opcodes = ["time", "sample_interval", "flush",
                            "discontinuity", "application"]
        with ParseMessagesFile(
                self._test_file, "short_timed_sample") as protocol:
            self.assertEqual(
                protocol.get_all_messages(only_opcodes=non_data_opcodes),
                messages_non_data)

    def test_get_all_sample_data(self):
        sample_data = self._sample_data_1 + self._sample_data_2
        with ParseMessagesFile(
                self._test_file, "short_timed_sample") as protocol:
            self.assertEqual(protocol.get_sample_data(), list(sample_data))

    def test_get_all_sample_data_split_stop(self):
        # A different test data file is needed in this case
        data = [complex(real, imaginary) for real, imaginary in
                zip(range(10), range(10))]
        with WriteMessagesFile(
                self._test_file, "complex_long_timed_sample") as protocol:
            protocol.write_message("sample", data)
            protocol.write_message("discontinuity")
            protocol.write_message("sample", data)
            protocol.write_message("sample", data)
            protocol.write_message("discontinuity")
            protocol.write_message("discontinuity")
            protocol.write_message("sample", data)
            protocol.write_message("flush")
            protocol.write_message("sample", data)
            protocol.write_message("discontinuity")
            protocol.write_message("sample", data)

        with ParseMessagesFile(
                self._test_file, "complex_long_timed_sample") as protocol:
            self.assertEqual(
                protocol.get_sample_data(split_on=["discontinuity"],
                                         stop_on=["flush"]),
                [data, data + data, [], data])

    def test_get_sample_data_length(self):
        with ParseMessagesFile(
                self._test_file, "short_timed_sample") as protocol:
            self.assertEqual(20, protocol.get_sample_data_length())

    def test_get_sample_data_length_in_bytes(self):
        with ParseMessagesFile(
                self._test_file, "short_timed_sample") as protocol:
            self.assertEqual(40, protocol.get_sample_data_length(
                length_in_samples=False))

    def test_get_sample_data_length_no_sample_data(self):
        # A different test data file is needed in this case
        with WriteMessagesFile(
                self._test_file, "complex_long_timed_sample") as protocol:
            protocol.write_message("discontinuity")
            protocol.write_message("discontinuity")
            protocol.write_message("discontinuity")
            protocol.write_message("flush")
            protocol.write_message("discontinuity")

        with ParseMessagesFile(
                self._test_file, "complex_long_timed_sample") as protocol:
            self.assertEqual(0, protocol.get_sample_data_length())

    def test_has_repr(self):
        with ParseMessagesFile(self._test_file, "char_timed_sample") as file:
            self.assertIsInstance(repr(file), str)

    def test_has_str(self):
        with ParseMessagesFile(self._test_file, "float_timed_sample") as file:
            self.assertIsInstance(str(file), str)
