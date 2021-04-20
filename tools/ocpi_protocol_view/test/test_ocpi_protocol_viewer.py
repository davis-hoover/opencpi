#!/usr/bin/env python3

# Test code in ocpi_protocol_viewer.py
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


import contextlib
import io
import os
import unittest

from opencpi.ocpi_protocols import WriteMessagesFile
from ocpi_protocol_view.ocpi_protocol_viewer import OcpiProtocolViewer


class TestOcpiProtocolViewer(unittest.TestCase):

    def setUp(self):
        self._test_file_1 = "/tmp/ocpi_protocol_viewer_test_1.bin"
        self._test_file_2 = "/tmp/ocpi_protocol_viewer_test_2.bin"
        self._test_file_3 = "/tmp/ocpi_protocol_viewer_test_3.bin"
        self._test_file_4 = "/tmp/ocpi_protocol_viewer_test_4.bin"

        with WriteMessagesFile(
                self._test_file_1, "complex_short_timed_sample") as file:
            file.write_message("sample", [complex(1, 2),
                                          complex(3, 4),
                                          complex(5, 6),
                                          complex(7, 8),
                                          complex(9, 10)])
            file.write_message("sample", [complex(11, 12),
                                          complex(13, 14),
                                          complex(15, 16),
                                          complex(17, 18),
                                          complex(19, 20)])
            file.write_message("sample", [complex(21, 22),
                                          complex(23, 24),
                                          complex(25, 26),
                                          complex(27, 28),
                                          complex(29, 30)])

        with WriteMessagesFile(
                self._test_file_2, "complex_short_timed_sample") as file:
            file.write_message("sample", [complex(31, 32),
                                          complex(33, 34),
                                          complex(35, 36),
                                          complex(37, 38),
                                          complex(39, 40)])
            file.write_message("sample", [complex(41, 42),
                                          complex(43, 44),
                                          complex(45, 46),
                                          complex(47, 48),
                                          complex(49, 50)])
            # Time value chosen as can be exactly represented by a floating
            # point number so direct comparion will work in tests.
            file.write_message("time", 1.0625)
            file.write_message("sample", [complex(51, 52),
                                          complex(53, 54),
                                          complex(55, 56),
                                          complex(57, 58),
                                          complex(59, 60)])

        with WriteMessagesFile(
                self._test_file_3, "complex_short_timed_sample") as file:
            file.write_message("time", 0.0625)
            file.write_message("flush")
            file.write_message("metadata", {"id": 1, "value": 100})
            file.write_message("metadata", {"id": 1234, "value": 987654321})

        with WriteMessagesFile(
                self._test_file_4, "complex_short_timed_sample") as file:
            file.write_message("sample_interval", 0.5625)
            file.write_message("discontinuity")
            file.write_message("metadata", {"id": 2, "value": 200})

    def tearDown(self):
        os.remove(self._test_file_1)
        os.remove(self._test_file_2)
        os.remove(self._test_file_3)
        os.remove(self._test_file_4)

    def test_show_headers_one_file(self):
        viewer = OcpiProtocolViewer(
            "complex_short_timed_sample", [self._test_file_1])

        stdout_handler = io.StringIO()
        with contextlib.redirect_stdout(stdout_handler):
            viewer.show_headers()
        displayed_text = stdout_handler.getvalue()

        expected_text = ("  # :             Opcode         (size)\n"
                         + "  0 :             sample     (20 bytes)\n"
                         + "  1 :             sample     (20 bytes)\n"
                         + "  2 :             sample     (20 bytes)\n")
        self.assertEqual(expected_text, displayed_text)

    def test_show_headers_two_files(self):
        viewer = OcpiProtocolViewer("complex_short_timed_sample",
                                    [self._test_file_1, self._test_file_2])

        stdout_handler = io.StringIO()
        with contextlib.redirect_stdout(stdout_handler):
            viewer.show_headers()
        displayed_text = stdout_handler.getvalue()

        expected_text = (
            "  # :             Opcode         (size) |"
            + "             Opcode         (size)\n"
            + "  0 :             sample     (20 bytes) |"
            + "             sample     (20 bytes)\n"
            + "  1 :             sample     (20 bytes) |"
            + "             sample     (20 bytes)\n"
            + "  2 :             sample     (20 bytes) |"
            + "               time     (12 bytes)\n"
            + "  3 :                 [Out of messages] |"
            + "             sample     (20 bytes)\n")
        self.assertEqual(expected_text, displayed_text)

    def test_show_headers_bad_file_path(self):
        viewer = OcpiProtocolViewer("complex_short_timed_sample", [
            "/some/random/path.file"])

        stdout_handler = io.StringIO()
        with contextlib.redirect_stdout(stdout_handler):
            viewer.show_headers()
        displayed_text = stdout_handler.getvalue()

        self.assertIn("does not exist", displayed_text)

    def test_show_headers_bad_file_format(self):
        with open(self._test_file_1, "rb") as file:
            binary_data = file.read()
        with open(self._test_file_1, "wb") as file:
            # Make file 'corrupted' by setting opcode value to be incorrect
            file.write(bytes([binary_data[0] + 20]))
            file.write(binary_data[1:])
        viewer = OcpiProtocolViewer(
            "complex_short_timed_sample", [self._test_file_1])

        with self.assertRaises(KeyError):
            viewer.show_headers()

    def test_show_messages_zeroth_message(self):
        viewer = OcpiProtocolViewer(
            "complex_short_timed_sample", [self._test_file_1])

        stdout_handler = io.StringIO()
        with contextlib.redirect_stdout(stdout_handler):
            viewer.show_messages(0)
        displayed_text = stdout_handler.getvalue()

        expected_text = (
            "  # : Opcode / Sample index             \n"
            + "  0 : sample                            \n"
            + "    :     0:          1.0 +         2.0j\n"
            + "    :     1:          3.0 +         4.0j\n"
            + "    :     2:          5.0 +         6.0j\n"
            + "    :     3:          7.0 +         8.0j\n"
            + "    :     4:          9.0 +        10.0j\n")
        self.assertEqual(expected_text, displayed_text)

    def test_show_messages_multiple_files_same_opcodes(self):
        viewer = OcpiProtocolViewer(
            "complex_short_timed_sample",
            [self._test_file_1, self._test_file_2])

        stdout_handler = io.StringIO()
        with contextlib.redirect_stdout(stdout_handler):
            viewer.show_messages(1)
        displayed_text = stdout_handler.getvalue()

        expected_text = (
            "  # : Opcode / Sample index              |"
            + " Opcode / Sample index             \n"
            + "  1 : sample                             |"
            + " sample                            \n"
            + "    :     0:         11.0 +        12.0j |"
            + "     0:         41.0 +        42.0j\n"
            + "    :     1:         13.0 +        14.0j |"
            + "     1:         43.0 +        44.0j\n"
            + "    :     2:         15.0 +        16.0j |"
            + "     2:         45.0 +        46.0j\n"
            + "    :     3:         17.0 +        18.0j |"
            + "     3:         47.0 +        48.0j\n"
            + "    :     4:         19.0 +        20.0j |"
            + "     4:         49.0 +        50.0j\n")
        self.assertEqual(expected_text, displayed_text)

    def test_show_messages_multiple_files_different_opcodes(self):
        viewer = OcpiProtocolViewer("complex_short_timed_sample",
                                    [self._test_file_1, self._test_file_2])

        stdout_handler = io.StringIO()
        with contextlib.redirect_stdout(stdout_handler):
            viewer.show_messages(2)
        displayed_text = stdout_handler.getvalue()

        expected_text = (
            "  # : Opcode / Sample index              |"
            + " Opcode / Sample index             \n"
            + "  2 : sample                             |"
            + " time                              \n"
            + "    :     0:         21.0 +        22.0j |"
            + "                             1.0625\n"
            + "    :     1:         23.0 +        24.0j |"
            + "            [No samples to display]\n"
            + "    :     2:         25.0 +        26.0j |"
            + "            [No samples to display]\n"
            + "    :     3:         27.0 +        28.0j |"
            + "            [No samples to display]\n"
            + "    :     4:         29.0 +        30.0j |"
            + "            [No samples to display]\n")
        self.assertEqual(expected_text, displayed_text)

    def test_show_messages_multiple_files_non_sample_message(self):
        viewer = OcpiProtocolViewer("complex_short_timed_sample",
                                    [self._test_file_3, self._test_file_4])

        stdout_handler = io.StringIO()
        with contextlib.redirect_stdout(stdout_handler):
            viewer.show_messages(0)
        displayed_text = stdout_handler.getvalue()

        expected_text = (
            "  # : Opcode / Sample index              |"
            + " Opcode / Sample index             \n"
            + "  0 : time                               |"
            + " sample_interval                   \n"
            + "    :                             0.0625 |"
            + "                             0.5625\n")
        self.assertEqual(expected_text, displayed_text)

    def test_show_messages_multiple_files_non_data_opcodes(self):
        viewer = OcpiProtocolViewer("complex_short_timed_sample", [self._test_file_3,
                                                                   self._test_file_4])

        stdout_handler = io.StringIO()
        with contextlib.redirect_stdout(stdout_handler):
            viewer.show_messages(1)
        displayed_text = stdout_handler.getvalue()

        expected_text = (
            "  # : Opcode / Sample index              |"
            + " Opcode / Sample index             \n"
            + "  1 : flush                              |"
            + " discontinuity                     \n"
            + "    :               [Opcode has no data] |"
            + "               [Opcode has no data]\n")
        self.assertEqual(expected_text, displayed_text)

    def test_show_messages_multiple_files_message_index_only_in_one_file(self):
        viewer = OcpiProtocolViewer("complex_short_timed_sample", [self._test_file_1,
                                                                   self._test_file_2])

        stdout_handler = io.StringIO()
        with contextlib.redirect_stdout(stdout_handler):
            viewer.show_messages(3)
        displayed_text = stdout_handler.getvalue()

        expected_text = (
            "  # : Opcode / Sample index              |"
            + " Opcode / Sample index             \n"
            + "  3 : [Out of messages]                  | "
            + "sample                            \n"
            + "    :                  [Out of messages] | "
            + "    0:         51.0 +        52.0j\n"
            + "    :                  [Out of messages] | "
            + "    1:         53.0 +        54.0j\n"
            + "    :                  [Out of messages] | "
            + "    2:         55.0 +        56.0j\n"
            + "    :                  [Out of messages] | "
            + "    3:         57.0 +        58.0j\n"
            + "    :                  [Out of messages] | "
            + "    4:         59.0 +        60.0j\n")
        self.assertEqual(expected_text, displayed_text)

    def test_show_messages_first_message_too_big(self):
        viewer = OcpiProtocolViewer(
            "complex_short_timed_sample", [self._test_file_1])

        stdout_handler = io.StringIO()
        with contextlib.redirect_stdout(stdout_handler):
            viewer.show_messages(10)
        displayed_text = stdout_handler.getvalue()

        expected_text = "  # : Opcode / Sample index             \n"
        self.assertEqual(expected_text, displayed_text)

    def test_show_messages_multiple_messages(self):
        viewer = OcpiProtocolViewer(
            "complex_short_timed_sample", [self._test_file_1])

        stdout_handler = io.StringIO()
        with contextlib.redirect_stdout(stdout_handler):
            viewer.show_messages(0, 3)
        displayed_text = stdout_handler.getvalue()

        expected_text = (
            "  # : Opcode / Sample index             \n"
            + "  0 : sample                            \n"
            + "    :     0:          1.0 +         2.0j\n"
            + "    :     1:          3.0 +         4.0j\n"
            + "    :     2:          5.0 +         6.0j\n"
            + "    :     3:          7.0 +         8.0j\n"
            + "    :     4:          9.0 +        10.0j\n"
            + "  1 : sample                            \n"
            + "    :     0:         11.0 +        12.0j\n"
            + "    :     1:         13.0 +        14.0j\n"
            + "    :     2:         15.0 +        16.0j\n"
            + "    :     3:         17.0 +        18.0j\n"
            + "    :     4:         19.0 +        20.0j\n"
            + "  2 : sample                            \n"
            + "    :     0:         21.0 +        22.0j\n"
            + "    :     1:         23.0 +        24.0j\n"
            + "    :     2:         25.0 +        26.0j\n"
            + "    :     3:         27.0 +        28.0j\n"
            + "    :     4:         29.0 +        30.0j\n")
        self.assertEqual(expected_text, displayed_text)

    def test_show_messages_first_sample_set(self):
        viewer = OcpiProtocolViewer(
            "complex_short_timed_sample", [self._test_file_1])

        stdout_handler = io.StringIO()
        with contextlib.redirect_stdout(stdout_handler):
            viewer.show_messages(0, 1, 2)
        displayed_text = stdout_handler.getvalue()

        expected_text = (
            "  # : Opcode / Sample index             \n"
            + "  0 : sample                            \n"
            + "    :     2:          5.0 +         6.0j\n"
            + "    :     3:          7.0 +         8.0j\n"
            + "    :     4:          9.0 +        10.0j\n")
        self.assertEqual(expected_text, displayed_text)

    def test_show_messages_first_sample_set_too_big(self):
        viewer = OcpiProtocolViewer(
            "complex_short_timed_sample", [self._test_file_1])

        stdout_handler = io.StringIO()
        with contextlib.redirect_stdout(stdout_handler):
            viewer.show_messages(0, 1, 20)
        displayed_text = stdout_handler.getvalue()

        expected_text = (
            "  # : Opcode / Sample index             \n"
            + "  0 : sample                            \n"
            + "    :    20:            [Out of samples]\n")
        self.assertEqual(expected_text, displayed_text)

    def test_show_messages_sample_count_greater_than_total_samples(self):
        viewer = OcpiProtocolViewer(
            "complex_short_timed_sample", [self._test_file_1])

        stdout_handler = io.StringIO()
        with contextlib.redirect_stdout(stdout_handler):
            viewer.show_messages(0, 1, 2, 100)
        displayed_text = stdout_handler.getvalue()

        expected_text = (
            "  # : Opcode / Sample index             \n"
            + "  0 : sample                            \n"
            + "    :     2:          5.0 +         6.0j\n"
            + "    :     3:          7.0 +         8.0j\n"
            + "    :     4:          9.0 +        10.0j\n")
        self.assertEqual(expected_text, displayed_text)

    def test_show_messages_custom_format(self):
        viewer = OcpiProtocolViewer(
            "complex_short_timed_sample", [self._test_file_1])

        stdout_handler = io.StringIO()
        with contextlib.redirect_stdout(stdout_handler):
            viewer.show_messages(
                0, 1, 2, 100, custom_format="{sample.real} + j{sample.imag}")
        displayed_text = stdout_handler.getvalue()

        expected_text = (
            "  # : Opcode / Sample index             \n"
            + "  0 : sample                            \n"
            + "    :     2: 5.0 + j6.0\n"
            + "    :     3: 7.0 + j8.0\n"
            + "    :     4: 9.0 + j10.0\n")
        self.assertEqual(expected_text, displayed_text)

    def test_show_messages_custom_format_bad_format(self):
        viewer = OcpiProtocolViewer(
            "complex_short_timed_sample", [self._test_file_1])

        with self.assertRaises(ValueError):
            viewer.show_messages(
                0, 1, 2, 100, custom_format="{sample:some_random_format}")
