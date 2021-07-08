#!/usr/bin/env python3

# Test code in write_stream_file.py
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

from ocpi_protocols import WriteStreamFile


class TestWriteStreamFile(unittest.TestCase):
    # Testing of the stream parser / reader will be allowed to use the
    # WriteStreamFile class - which is under-test here. To prevent a circular
    # test dependency testing of the WriteStreamFile class must not use this
    # TestWriteStreamFile class.
    _test_file = "test_data.bin"

    def setUp(self):
        if os.path.isfile(self._test_file):
            os.remove(self._test_file)

    def tearDown(self):
        if os.path.isfile(self._test_file):
            os.remove(self._test_file)

    def test_write_data(self):
        shorts = list(range(256, 1024, 2))

        test_data = [0] * (2 * len(shorts))
        for index, value in enumerate(shorts):
            test_data[2 * index] = value & 0xFF
            test_data[2 * index + 1] = (value >> 8) & 0xFF
        test_data = bytes(test_data)

        with WriteStreamFile(self._test_file, "short_timed_sample") as file:
            file.write(shorts)

        with open(self._test_file, "rb") as binary_file:
            self.assertEqual(binary_file.read(), test_data)

    def test_write_raw_data(self):
        shorts = list(range(256, 1024, 2))

        test_data = [0] * (2 * len(shorts))
        for index, value in enumerate(shorts):
            test_data[2 * index] = value & 0xFF
            test_data[2 * index + 1] = (value >> 8) & 0xFF
        test_data = bytes(test_data)

        with WriteStreamFile(self._test_file, "long_timed_sample") as file:
            file.write(test_data, raw_data=True)

        with open(self._test_file, "rb") as binary_file:
            self.assertEqual(binary_file.read(), test_data)

    def test_write_multiple_data(self):
        shorts = list(range(256, 2048, 2))

        test_data = [0] * (2 * len(shorts))
        for index, value in enumerate(shorts):
            test_data[2 * index] = value & 0xFF
            test_data[2 * index + 1] = (value >> 8) & 0xFF
        test_data = bytes(test_data)

        with WriteStreamFile(self._test_file, "short_timed_sample") as file:
            file.write(shorts[0:len(shorts) // 2])
            file.write(shorts[len(shorts) // 2:])

        with open(self._test_file, "rb") as binary_file:
            self.assertEqual(binary_file.read(), test_data)

    def test_incorrect_data_type(self):
        with WriteStreamFile(
                self._test_file, "complex_short_timed_sample") as file:
            file.write([4])

    def test_not_as_context_manager(self):
        shorts = list(range(256, 2048, 2))

        test_data = [0] * (2 * len(shorts))
        for index, value in enumerate(shorts):
            test_data[2 * index] = value & 0xFF
            test_data[2 * index + 1] = (value >> 8) & 0xFF
        test_data = bytes(test_data)

        file = WriteStreamFile(self._test_file, "short_timed_sample")
        file.write(shorts[0:len(shorts) // 2])
        file.write(shorts[len(shorts) // 2:])
        file.close()

        with open(self._test_file, "rb") as binary_file:
            self.assertEqual(binary_file.read(), test_data)

    def test_has_repr(self):
        with WriteStreamFile(self._test_file, "char_timed_sample") as file:
            self.assertIsInstance(repr(file), str)

    def test_has_str(self):
        with WriteStreamFile(self._test_file, "char_timed_sample") as file:
            self.assertIsInstance(str(file), str)
