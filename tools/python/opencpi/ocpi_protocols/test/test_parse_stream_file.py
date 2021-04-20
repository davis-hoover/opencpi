#!/usr/bin/env python3

# Test code in parse_stream_file.py
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

from ocpi_protocols import ParseStreamFile, WriteStreamFile


class TestParseStreamFile(unittest.TestCase):
    # The testing of the WriteStreamFile class does not use the ParseStreamFile
    # class, so the assumption is made that the WriteStreamFile is correct and
    # can be used here as that has been tested independently.
    _test_file = "test_data.bin"

    def setUp(self):
        if os.path.isfile(self._test_file):
            os.remove(self._test_file)

        self._test_shorts = list(range(23, 2000, 107))

        with WriteStreamFile(
                self._test_file, "short_timed_sample") as stream_file:
            stream_file.write(self._test_shorts)

    def tearDown(self):
        if os.path.isfile(self._test_file):
            os.remove(self._test_file)

    def test_data_non_sequential_access(self):
        with ParseStreamFile(
                self._test_file, "short_timed_sample") as stream_file:
            self.assertEqual(stream_file.data[4], self._test_shorts[4])
            self.assertEqual(stream_file.data[14], self._test_shorts[14])
            self.assertEqual(stream_file.data[1], self._test_shorts[1])

    def test_negative_data_index(self):
        with ParseStreamFile(
                self._test_file, "short_timed_sample") as stream_file:
            self.assertEqual(stream_file.data[-4], self._test_shorts[-4])

    def test_iterate_data(self):
        data_from_file = []
        with ParseStreamFile(
                self._test_file, "short_timed_sample") as stream_file:
            for value in stream_file.data:
                data_from_file.append(value)

        self.assertEqual(data_from_file, self._test_shorts)

    def test_read_whole_file(self):
        with ParseStreamFile(
                self._test_file, "short_timed_sample") as stream_file:
            self.assertEqual(stream_file.read(), self._test_shorts)

    def test_read_first_entries(self):
        with ParseStreamFile(
                self._test_file, "short_timed_sample") as stream_file:
            self.assertEqual(stream_file.read(10), self._test_shorts[0:10])

    def test_read_after_seek(self):
        with ParseStreamFile(
                self._test_file, "short_timed_sample") as stream_file:
            stream_file.seek(10)
            self.assertEqual(stream_file.read(10), self._test_shorts[10:10])

    def test_read_request_more_values_than_in_file(self):
        read_from_index = len(self._test_shorts) // 2
        with ParseStreamFile(
                self._test_file, "short_timed_sample") as stream_file:
            stream_file.seek(read_from_index)
            self.assertEqual(stream_file.read(len(self._test_shorts)),
                             self._test_shorts[read_from_index:])

    def test_not_as_context_manager(self):
        stream_file = ParseStreamFile(self._test_file, "short_timed_sample")
        self.assertEqual(stream_file.read(4), self._test_shorts[0:4])
        stream_file.close()

    def test_has_repr(self):
        with ParseStreamFile(self._test_file, "char_timed_sample") as file:
            self.assertIsInstance(repr(file), str)

    def test_has_str(self):
        with ParseStreamFile(self._test_file, "float_timed_sample") as file:
            self.assertIsInstance(str(file), str)
