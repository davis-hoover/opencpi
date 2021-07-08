#!/usr/bin/env python3

# Test code in ocpi_protocols.py
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
import decimal
import unittest

from ocpi_protocols.ocpi_protocols import _interleave_complex, OcpiProtocols


PROFILING = False


# Increase the decimal precision, needed to handle time and sample interval
# values to their maximum supported accuracy
decimal.getcontext().prec = 50


class TestInterleaveComplex(unittest.TestCase):
    def test_expected_data(self):
        complex_list = [complex(real_value, imaginary_value) for
                        real_value, imaginary_value in zip(range(0, 20, 2),
                                                           range(1, 20, 2))]
        self.assertEqual(_interleave_complex(complex_list),
                         [float(value) for value in range(20)])

    def test_empty_list(self):
        self.assertEqual(_interleave_complex([]), [])

    def test_real_first(self):
        complex_list = [complex(0, 0) * 10]
        complex_list[0] = complex(10, 0)

        self.assertEqual(_interleave_complex(complex_list)[0], 10)

    def test_return_type_int(self):
        complex_list = [complex(real_value, imaginary_value) for
                        real_value, imaginary_value in zip(range(0, 20, 2),
                                                           range(1, 20, 2))]
        self.assertEqual(_interleave_complex(complex_list, return_type=int),
                         list(range(20)))
        self.assertTrue(isinstance(
            _interleave_complex(complex_list, return_type=int)[0], int))

    @unittest.skipIf(PROFILING is False, "Not profiling test")
    def test_speed_profiling(self):
        complex_list = [complex(real_value, imaginary_value) for
                        real_value, imaginary_value in zip(range(0, 32000, 2),
                                                           range(1, 32000, 2))]
        cProfile.runctx("_interleave_complex(complex_list)", globals(),
                        {"complex_list": complex_list})


class TestOcpiProtocols(unittest.TestCase):
    def test_pack_sample_boolean_input_booleans(self):
        protocol_handler = OcpiProtocols("bool_timed_sample")
        data = [True, False] * 10

        self.assertEqual(protocol_handler.pack_data("sample", data),
                         bytes([1, 0] * 10))

    def test_pack_sample_boolean_input_integers(self):
        protocol_handler = OcpiProtocols("bool_timed_sample")
        data = [1, 0] * 10

        self.assertEqual(protocol_handler.pack_data("sample", data),
                         bytes(data))

    def test_pack_sample_boolean_empty_list(self):
        protocol_handler = OcpiProtocols("bool_timed_sample")

        self.assertEqual(protocol_handler.pack_data("sample", []),
                         bytes())

    def test_pack_sample_unsigned_char(self):
        protocol_handler = OcpiProtocols("uchar_timed_sample")
        data = list(range(255))

        self.assertEqual(protocol_handler.pack_data("sample", data),
                         bytes(data))

    def test_pack_sample_char(self):
        protocol_handler = OcpiProtocols("char_timed_sample")
        data = list(range(-128, 128, 1))

        # Generate the result of packing, without using struct.pack as this is
        # used in the implementation-under-test.
        packed_chars = bytes(list(range(256)))
        packed_chars = \
            packed_chars[128:] + packed_chars[0:128]    # Equivalent to two's
        # complement

        self.assertEqual(protocol_handler.pack_data("sample", data),
                         bytes(packed_chars))

    def test_pack_sample_unsigned_short(self):
        protocol_handler = OcpiProtocols("ushort_timed_sample")
        max_short = 2**16
        data = list(range(max_short))

        # Generate the result of packing, without using struct.pack as this is
        # used in the implementation-under-test.
        packed_chars = bytes(list(range(256)))
        # Multiple by two, as two bytes
        packed_shorts = [0] * (max_short * 2)
        # needed for each short
        for upper_index, upper_byte in zip(range(0, 2**16, 256), packed_chars):
            for lower_index, lower_byte in enumerate(packed_chars):
                packed_shorts[2 * (lower_index + upper_index)] = lower_byte
                packed_shorts[2 * (lower_index + upper_index) + 1] = upper_byte

        self.assertEqual(protocol_handler.pack_data("sample", data),
                         bytes(packed_shorts))

    def test_pack_sample_short(self):
        protocol_handler = OcpiProtocols("short_timed_sample")
        data = list(range(-2**15, 2**15, 1))

        # Generate the result of packing, without using struct.pack as this is
        # used in the implementation-under-test.
        packed_chars = bytes(list(range(256)))
        # Multiple by two, as two bytes
        packed_shorts = [0] * ((2**16) * 2)
        # needed for each short
        for upper_index, upper_byte in zip(range(0, 2**16, 256), packed_chars):
            for lower_index, lower_byte in enumerate(packed_chars):
                packed_shorts[2 * (lower_index + upper_index)] = lower_byte
                packed_shorts[2 * (lower_index + upper_index) + 1] = upper_byte
        packed_shorts = \
            packed_shorts[2**16:] + packed_shorts[0:2**16]  # Equivalent to
        # two's complement

        self.assertEqual(protocol_handler.pack_data("sample", data),
                         bytes(packed_shorts))

    def test_pack_sample_complex_short(self):
        protocol_handler = OcpiProtocols("complex_short_timed_sample")
        data = [complex(real_, imaginary_) for real_, imaginary_ in zip(
            range(-2**15, 2**15, 2), range(-2**15 + 1, 2**15, 2))]

        # Generate the result of packing, without using struct.pack as this is
        # used in the implementation-under-test.
        packed_chars = bytes(list(range(256)))
        # Multiple by two, as two bytes
        packed_shorts = [0] * ((2**16) * 2)
        # needed for each short
        for upper_index, upper_byte in zip(range(0, 2**16, 256), packed_chars):
            for lower_index, lower_byte in enumerate(packed_chars):
                packed_shorts[2 * (lower_index + upper_index)] = lower_byte
                packed_shorts[2 * (lower_index + upper_index) + 1] = upper_byte
        packed_shorts = \
            packed_shorts[2**16:] + packed_shorts[0:2**16]  # Equivalent to
        # two's complement

        self.assertEqual(protocol_handler.pack_data("sample", data),
                         bytes(packed_shorts))

    def test_pack_sample_unsigned_long(self):
        protocol_handler = OcpiProtocols("ulong_timed_sample")
        data = list(range(2**14, 2**27, 543))

        # Generate the result of packing, without using struct.pack as this is
        # used in the implementation-under-test.
        packed_longs = [0] * (4 * len(data))
        for index, long_value in enumerate(data):
            packed_longs[4 * index] = long_value & 0xFF
            packed_longs[4 * index + 1] = (long_value >> 8) & 0xFF
            packed_longs[4 * index + 2] = (long_value >> 16) & 0xFF
            packed_longs[4 * index + 3] = (long_value >> 24) & 0xFF

        self.assertEqual(protocol_handler.pack_data("sample", data),
                         bytes(packed_longs))

    def test_pack_sample_long(self):
        protocol_handler = OcpiProtocols("long_timed_sample")
        positive_data = list(range(0, 2**20, 1287))
        negative_data = list(range(-1, 2**20, 973))
        data = positive_data + negative_data

        # Generate the result of packing, without using struct.pack as this is
        # used in the implementation-under-test.
        total_data_length = len(positive_data) + len(negative_data)
        packed_longs = [0] * (4 * total_data_length)
        for index, long_value in enumerate(positive_data):
            packed_longs[4 * index] = long_value & 0xFF
            packed_longs[4 * index + 1] = (long_value >> 8) & 0xFF
            packed_longs[4 * index + 2] = (long_value >> 16) & 0xFF
            packed_longs[4 * index + 3] = (long_value >> 24) & 0xFF
        for index, long_value in zip(
                range(len(positive_data), total_data_length),
                negative_data):
            long_value = 2**32 + long_value     # Two's complement equivalent
            # Add as all negative values
            packed_longs[4 * index] = long_value & 0xFF
            packed_longs[4 * index + 1] = (long_value >> 8) & 0xFF
            packed_longs[4 * index + 2] = (long_value >> 16) & 0xFF
            packed_longs[4 * index + 3] = (long_value >> 24) & 0xFF

        self.assertEqual(protocol_handler.pack_data("sample", data),
                         bytes(packed_longs))

    def test_pack_sample_complex_long(self):
        protocol_handler = OcpiProtocols("complex_long_timed_sample")
        positive_data = [complex(value, value) for
                         value in range(2**10, 2**20, 2799)]
        negative_data = [complex(value, value) for
                         value in range(-2**10, -2**20, 2799)]
        data = positive_data + negative_data

        # Generate the result of packing, without using struct.pack as this is
        # used in the implementation-under-test.
        total_data_length = len(positive_data) + len(negative_data)
        packed_longs = [0] * (8 * total_data_length)
        for index, long_value in enumerate(positive_data):
            real_value = int(long_value.real)
            imaginary_value = int(long_value.imag)
            packed_longs[8 * index] = real_value & 0xFF
            packed_longs[8 * index + 1] = (real_value >> 8) & 0xFF
            packed_longs[8 * index + 2] = (real_value >> 16) & 0xFF
            packed_longs[8 * index + 3] = (real_value >> 24) & 0xFF
            packed_longs[8 * index + 4] = imaginary_value & 0xFF
            packed_longs[8 * index + 5] = (imaginary_value >> 8) & 0xFF
            packed_longs[8 * index + 6] = (imaginary_value >> 16) & 0xFF
            packed_longs[8 * index + 7] = (imaginary_value >> 24) & 0xFF
        for index, long_value in zip(
                range(len(positive_data), total_data_length),
                negative_data):
            real_value = 2**32 + int(long_value.real)
            imaginary_value = 2**32 + int(long_value.imag)
            packed_longs[8 * index] = real_value & 0xFF
            packed_longs[8 * index + 1] = (real_value >> 8) & 0xFF
            packed_longs[8 * index + 2] = (real_value >> 16) & 0xFF
            packed_longs[8 * index + 3] = (real_value >> 24) & 0xFF
            packed_longs[8 * index + 4] = imaginary_value & 0xFF
            packed_longs[8 * index + 5] = (imaginary_value >> 8) & 0xFF
            packed_longs[8 * index + 6] = (imaginary_value >> 16) & 0xFF
            packed_longs[8 * index + 7] = (imaginary_value >> 24) & 0xFF

        self.assertEqual(protocol_handler.pack_data("sample", data),
                         bytes(packed_longs))

    def test_pack_sample_float(self):
        protocol_handler = OcpiProtocols("float_timed_sample")
        data = [123456.789]

        self.assertEqual(protocol_handler.pack_data("sample", data),
                         bytes([0x65, 0x20, 0xF1, 0x47]))

    def test_pack_sample_complex_float(self):
        protocol_handler = OcpiProtocols("complex_float_timed_sample")
        data = [complex(123456.789, -123.456789)]

        self.assertEqual(
            protocol_handler.pack_data("sample", data),
            bytes([0x65, 0x20, 0xF1, 0x47, 0xE0, 0xE9, 0xF6, 0xC2]))

    def test_pack_sample_double(self):
        protocol_handler = OcpiProtocols("double_timed_sample")
        data = [123456.789]

        self.assertEqual(
            protocol_handler.pack_data("sample", data),
            bytes([0xC9, 0x76, 0xBE, 0x9F, 0x0C, 0x24, 0xFE, 0x40]))

    def test_pack_sample_complex_double(self):
        protocol_handler = OcpiProtocols("complex_double_timed_sample")
        data = [complex(123456.789, -123.456789)]

        self.assertEqual(
            protocol_handler.pack_data("sample", data),
            bytes([0xC9, 0x76, 0xBE, 0x9F, 0x0C, 0x24, 0xFE, 0x40,
                   0x0B, 0x0B, 0xEE, 0x07, 0x3C, 0xDD, 0x5E, 0xC0]))

    def test_pack_time(self):
        protocol_handler = OcpiProtocols("char_timed_sample")

        self.assertEqual(protocol_handler.pack_data("time", 1.0000000001),
                         bytes([
                             0x00, 0x00, 0x00, 0x6D, 0x00, 0x00, 0x00, 0x00,
                             0x01, 0x00, 0x00, 0x00]))

    def test_pack_time_negative(self):
        protocol_handler = OcpiProtocols("char_timed_sample")

        with self.assertRaises(ValueError):
            self.assertEqual(protocol_handler.pack_data("time", -1.75))

    def test_pack_time_maximum(self):
        protocol_handler = OcpiProtocols("char_timed_sample")

        self.assertEqual(
            protocol_handler.pack_data(
                "time", decimal.Decimal(2**32) - decimal.Decimal(2**-40)),
            bytes([0x00, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
                   0xFF, 0xFF, 0xFF, 0xFF]))

    def test_pack_time_minimum(self):
        protocol_handler = OcpiProtocols("char_timed_sample")

        self.assertEqual(protocol_handler.pack_data("time", 2**(-40)),
                         bytes([0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00,
                                0x00, 0x00, 0x00, 0x00]))

    def test_pack_time_zero(self):
        protocol_handler = OcpiProtocols("char_timed_sample")

        self.assertEqual(protocol_handler.pack_data("time", 0.0),
                         bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                0x00, 0x00, 0x00, 0x00]
                               ))

    def test_pack_sample_interval(self):
        protocol_handler = OcpiProtocols("char_timed_sample")

        self.assertEqual(
            protocol_handler.pack_data("sample_interval", 1.0000000001),
            bytes([0x00, 0x00, 0x00, 0x6D, 0x00, 0x00, 0x00, 0x00,
                   0x01, 0x00, 0x00, 0x00]))

    def test_pack_sample_interval_negative(self):
        protocol_handler = OcpiProtocols("char_timed_sample")

        with self.assertRaises(ValueError):
            protocol_handler.pack_data("sample_interval", -100.00390625)

    def test_pack_sample_interval_maximum(self):
        protocol_handler = OcpiProtocols("char_timed_sample")

        self.assertEqual(
            protocol_handler.pack_data(
                "sample_interval",
                decimal.Decimal(2**32) - decimal.Decimal(2**-40)),
            bytes([0x00, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
                   0xFF, 0xFF, 0xFF, 0xFF]))

    def test_pack_sample_interval_minimum(self):
        protocol_handler = OcpiProtocols("char_timed_sample")

        self.assertEqual(
            protocol_handler.pack_data("sample_interval", 2**(-40)),
            bytes([0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00,
                   0x00, 0x00, 0x00, 0x00]))

    def test_pack_flush(self):
        protocol_handler = OcpiProtocols("char_timed_sample")

        self.assertEqual(protocol_handler.pack_data("flush", []), bytes())

    def test_pack_discontinuity(self):
        protocol_handler = OcpiProtocols("char_timed_sample")

        self.assertEqual(protocol_handler.pack_data("discontinuity", []),
                         bytes())

    def test_pack_metadata(self):
        protocol_handler = OcpiProtocols("char_timed_sample")

        self.assertEqual(protocol_handler.pack_data("metadata",
                                                    {"id": 1, "value": 2}),
                         bytes([0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
                               ))

    def test_pack_sample_incorrect_data_type(self):
        protocol_handler = OcpiProtocols("char_timed_sample")
        data = [complex(12.34, 34.56)]

        with self.assertRaises(ValueError):
            protocol_handler.pack_data("sample", data)

    def test_unpack_sample_boolean(self):
        protocol_handler = OcpiProtocols("bool_timed_sample")
        packed_data = bytes([1, 0] * 10)

        self.assertEqual(protocol_handler.unpack_data("sample", packed_data),
                         (True, False) * 10)

    def test_unpack_sample_unsigned_char(self):
        protocol_handler = OcpiProtocols("uchar_timed_sample")
        chars = tuple(range(255))
        packed_data = bytes(chars)

        self.assertEqual(protocol_handler.unpack_data("sample", packed_data),
                         chars)

    def test_unpack_sample_char(self):
        protocol_handler = OcpiProtocols("char_timed_sample")
        chars = tuple(range(-128, 128, 1))

        # Indexes used to get equivalent to two's complement
        packed_data = bytes(list(range(128, 256)) + list(range(128)))

        self.assertEqual(protocol_handler.unpack_data("sample", packed_data),
                         chars)

    def test_unpack_sample_unsigned_short(self):
        protocol_handler = OcpiProtocols("ushort_timed_sample")
        max_short = 2**16
        shorts = tuple(range(max_short))

        # Generate the result of packing, as the input data
        chars = list(range(256))
        packed_data = [0] * (max_short * 2)     # Multiple by two, as two bytes
        # needed for each short
        for upper_index, upper_byte in zip(range(0, 2**16, 256), chars):
            for lower_index, lower_byte in enumerate(chars):
                packed_data[2 * (lower_index + upper_index)] = lower_byte
                packed_data[2 * (lower_index + upper_index) + 1] = upper_byte
        packed_data = bytes(packed_data)

        self.assertEqual(protocol_handler.unpack_data("sample", packed_data),
                         shorts)

    def test_unpack_sample_short(self):
        protocol_handler = OcpiProtocols("short_timed_sample")
        shorts = tuple(range(-2**15, 2**15, 1))

        # Generate the result of packing, as the input data
        chars = list(range(256))
        packed_data = [0] * ((2**16) * 2)     # Multiple by two, as two bytes
        # needed for each short
        for upper_index, upper_byte in zip(range(0, 2**16, 256), chars):
            for lower_index, lower_byte in enumerate(chars):
                packed_data[2 * (lower_index + upper_index)] = lower_byte
                packed_data[2 * (lower_index + upper_index) + 1] = upper_byte
        packed_data = \
            packed_data[2**16:] + packed_data[0:2**16]  # Equivalent to two's
        # complement
        packed_data = bytes(packed_data)

        self.assertEqual(protocol_handler.unpack_data("sample", packed_data),
                         shorts)

    def test_unpack_sample_complex_short(self):
        protocol_handler = OcpiProtocols("complex_short_timed_sample")
        complex_shorts = tuple(
            [complex(real_, imaginary_) for real_, imaginary_ in
             zip(range(-2**15, 2**15, 2), range(-2**15 + 1, 2**15, 2))])

        # Generate the result of packing, as the input data
        chars = list(range(256))
        packed_data = [0] * ((2**16) * 2)     # Multiple by two, as two bytes
        # needed for each short
        for upper_index, upper_byte in zip(range(0, 2**16, 256), chars):
            for lower_index, lower_byte in enumerate(chars):
                packed_data[2 * (lower_index + upper_index)] = lower_byte
                packed_data[2 * (lower_index + upper_index) + 1] = upper_byte
        packed_data = \
            packed_data[2**16:] + packed_data[0:2**16]  # Equivalent to two's
        # complement
        packed_data = bytes(packed_data)

        self.assertEqual(protocol_handler.unpack_data("sample", packed_data),
                         complex_shorts)

    def test_unpack_sample_unsigned_long(self):
        protocol_handler = OcpiProtocols("ulong_timed_sample")
        longs = tuple(range(2**14, 2**27, 543))

        # Generate the result of packing, as the input data
        packed_data = [0] * (4 * len(longs))
        for index, long_value in enumerate(longs):
            packed_data[4 * index] = long_value & 0xFF
            packed_data[4 * index + 1] = (long_value >> 8) & 0xFF
            packed_data[4 * index + 2] = (long_value >> 16) & 0xFF
            packed_data[4 * index + 3] = (long_value >> 24) & 0xFF
        packed_data = bytes(packed_data)

        self.assertEqual(protocol_handler.unpack_data("sample", packed_data),
                         longs)

    def test_unpack_sample_long(self):
        protocol_handler = OcpiProtocols("long_timed_sample")
        positive_longs = tuple(range(0, 2**20, 1287))
        negative_longs = tuple(range(-1, 2**20, 973))
        longs = positive_longs + negative_longs

        # Generate the result of packing, as input data
        packed_data = [0] * (4 * len(longs))
        for index, long_value in enumerate(positive_longs):
            packed_data[4 * index] = long_value & 0xFF
            packed_data[4 * index + 1] = (long_value >> 8) & 0xFF
            packed_data[4 * index + 2] = (long_value >> 16) & 0xFF
            packed_data[4 * index + 3] = (long_value >> 24) & 0xFF
        for index, long_value in zip(range(len(positive_longs), len(longs)),
                                     negative_longs):
            long_value = 2**32 + long_value     # Two's complement equivalent
            # Add as all negative values
            packed_data[4 * index] = long_value & 0xFF
            packed_data[4 * index + 1] = (long_value >> 8) & 0xFF
            packed_data[4 * index + 2] = (long_value >> 16) & 0xFF
            packed_data[4 * index + 3] = (long_value >> 24) & 0xFF
        packed_data = bytes(packed_data)

        self.assertEqual(protocol_handler.unpack_data("sample", packed_data),
                         longs)

    def test_unpack_sample_complex_long(self):
        protocol_handler = OcpiProtocols("complex_long_timed_sample")
        positive_complex_longs = tuple(
            [complex(value, value) for value in range(2**10, 2**20, 2799)])
        negative_complex_longs = tuple(
            [complex(value, value) for value in range(-2**10, -2**20, 2799)])
        complex_longs = positive_complex_longs + negative_complex_longs

        # Generate the result of packing, as input data
        packed_data = [0] * (8 * len(complex_longs))
        for index, long_value in enumerate(positive_complex_longs):
            real_value = int(long_value.real)
            imaginary_value = int(long_value.imag)
            packed_data[8 * index] = real_value & 0xFF
            packed_data[8 * index + 1] = (real_value >> 8) & 0xFF
            packed_data[8 * index + 2] = (real_value >> 16) & 0xFF
            packed_data[8 * index + 3] = (real_value >> 24) & 0xFF
            packed_data[8 * index + 4] = imaginary_value & 0xFF
            packed_data[8 * index + 5] = (imaginary_value >> 8) & 0xFF
            packed_data[8 * index + 6] = (imaginary_value >> 16) & 0xFF
            packed_data[8 * index + 7] = (imaginary_value >> 24) & 0xFF
        for index, long_value in zip(
                range(len(positive_complex_longs), len(complex_longs)),
                negative_complex_longs):
            real_value = 2**32 + int(long_value.real)
            imaginary_value = 2**32 + int(long_value.imag)
            packed_data[8 * index] = real_value & 0xFF
            packed_data[8 * index + 1] = (real_value >> 8) & 0xFF
            packed_data[8 * index + 2] = (real_value >> 16) & 0xFF
            packed_data[8 * index + 3] = (real_value >> 24) & 0xFF
            packed_data[8 * index + 4] = imaginary_value & 0xFF
            packed_data[8 * index + 5] = (imaginary_value >> 8) & 0xFF
            packed_data[8 * index + 6] = (imaginary_value >> 16) & 0xFF
            packed_data[8 * index + 7] = (imaginary_value >> 24) & 0xFF
        packed_data = bytes(packed_data)

        self.assertEqual(protocol_handler.unpack_data("sample", packed_data),
                         complex_longs)

    def test_unpack_sample_float(self):
        protocol_handler = OcpiProtocols("float_timed_sample")
        packed_data = bytes([0x65, 0x20, 0xF1, 0x47])

        unpacked_data = protocol_handler.unpack_data("sample", packed_data)
        self.assertAlmostEqual(unpacked_data[0], 123456.789, places=3)

    def test_unpack_sample_complex_float(self):
        protocol_handler = OcpiProtocols("complex_float_timed_sample")
        packed_data = bytes([0x65, 0x20, 0xF1, 0x47, 0xE0, 0xE9, 0xF6, 0xC2])

        unpacked_data = protocol_handler.unpack_data("sample", packed_data)
        self.assertAlmostEqual(unpacked_data[0].real, 123456.789, places=3)
        self.assertAlmostEqual(unpacked_data[0].imag, -123.456789, places=5)

    def test_unpack_sample_double(self):
        protocol_handler = OcpiProtocols("double_timed_sample")
        packed_data = bytes([0xC9, 0x76, 0xBE, 0x9F, 0x0C, 0x24, 0xFE, 0x40])

        self.assertEqual(protocol_handler.unpack_data("sample", packed_data),
                         tuple([123456.789]))

    def test_unpack_sample_complex_double(self):
        protocol_handler = OcpiProtocols("complex_double_timed_sample")
        packed_data = bytes([0xC9, 0x76, 0xBE, 0x9F, 0x0C, 0x24, 0xFE, 0x40,
                             0x0B, 0x0B, 0xEE, 0x07, 0x3C, 0xDD, 0x5E, 0xC0])

        unpacked_data = protocol_handler.unpack_data("sample", packed_data)
        self.assertAlmostEqual(unpacked_data[0].real, 123456.789, places=3)
        self.assertAlmostEqual(unpacked_data[0].imag, -123.456789, places=5)

    def test_unpack_time(self):
        protocol_handler = OcpiProtocols("char_timed_sample")

        self.assertEqual(float(protocol_handler.unpack_data("time", bytes([
            0x67, 0x7F, 0xF3, 0x6D, 0x00, 0x00, 0x00, 0x00,
            0x01, 0x00, 0x00, 0x00]))),
            1.0000000001)

    def test_unpack_time_zero(self):
        protocol_handler = OcpiProtocols("char_timed_sample")

        self.assertEqual(protocol_handler.unpack_data("time", bytes([
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00])),
            0.0)

    def test_unpack_time_maximum(self):
        protocol_handler = OcpiProtocols("char_timed_sample")

        self.assertEqual(protocol_handler.unpack_data("time", bytes([
            0x00, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
            0xFF, 0xFF, 0xFF, 0xFF])),
            decimal.Decimal(2**32) - decimal.Decimal(2**-40))

    def test_unpack_time_minimum(self):
        protocol_handler = OcpiProtocols("char_timed_sample")

        self.assertEqual(protocol_handler.unpack_data("time", bytes([
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00])),
            (2**-40))

    def test_unpack_sample_interval(self):
        protocol_handler = OcpiProtocols("char_timed_sample")

        self.assertEqual(
            float(protocol_handler.unpack_data("sample_interval", bytes(
                [0x67, 0x7F, 0xF3, 0x6D, 0x00, 0x00, 0x00, 0x00,
                 0x01, 0x00, 0x00, 0x00]))),
            1.0000000001)

    def test_unpack_sample_interval_maximum(self):
        protocol_handler = OcpiProtocols("char_timed_sample")

        self.assertEqual(protocol_handler.unpack_data("sample_interval", bytes(
            [0x00, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
             0xFF, 0xFF, 0xFF, 0xFF])),
            decimal.Decimal(2**32) - decimal.Decimal(2**-40))

    def test_unpack_sample_interval_minimum(self):
        protocol_handler = OcpiProtocols("char_timed_sample")

        self.assertEqual(protocol_handler.unpack_data("sample_interval", bytes(
            [0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00,
             0x00, 0x00, 0x00, 0x00])),
            (2**-40))

    def test_unpack_flush(self):
        protocol_handler = OcpiProtocols("char_timed_sample")

        self.assertEqual(protocol_handler.unpack_data("flush", bytes()),
                         None)

    def test_unpack_discontinuity(self):
        protocol_handler = OcpiProtocols("char_timed_sample")

        self.assertEqual(
            protocol_handler.unpack_data("discontinuity", bytes()),
            None)

    def test_unpack_metadata(self):
        protocol_handler = OcpiProtocols("bool_timed_sample")

        self.assertEqual(protocol_handler.unpack_data("metadata", bytes(
            [0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
             0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])),
            {"id": 1, "value": 2})

    def test_incorrect_protocol_name(self):
        with self.assertRaises(ValueError):
            protocol_handler = OcpiProtocols("Non-existant_protocol")

    def test_has_pack_data(self):
        protocol_handler = OcpiProtocols("complex_short_timed_sample")
        self.assertTrue(getattr(protocol_handler, "pack_data"))
        self.assertTrue(callable(protocol_handler.pack_data))

    def test_has_unpack_data(self):
        protocol_handler = OcpiProtocols("complex_long_timed_sample")
        self.assertTrue(getattr(protocol_handler, "unpack_data"))
        self.assertTrue(callable(protocol_handler.unpack_data))

    def test_has_repr(self):
        protocol_handler = OcpiProtocols("char_timed_sample")
        self.assertIsInstance(repr(protocol_handler), str)

    def test_has_str(self):
        protocol_handler = OcpiProtocols("char_timed_sample")
        self.assertIsInstance(str(protocol_handler), str)
