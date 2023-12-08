#!/usr/bin/env python3

# Testing of code in base_comparison.py
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
import decimal

from ocpi_testing._comparison_methods.base_comparison import BasicComparison


class TestComparison(BasicComparison):
    def same(self):
        # Overload this method in the child class as required, but since no
        # checks are being made using this method, just return False
        print("No check made by TestComparison.same()")
        return False


class TestBasicComparison(unittest.TestCase):
    def setUp(self):
        self.test_comparison = TestComparison(False, int)

    def test_correct_messages_passes(self):
        # Use different data values as this checker should not check data value
        # and should allow these values to pass
        messages_1 = [{"opcode": "time", "data": 0.01},
                      {"opcode": "sample", "data": [1, 2, 3]},
                      {"opcode": "flush", "data": None},
                      {"opcode": "sample", "data": [10, 11, 13]},
                      {"opcode": "sample", "data": [21, 22, 23]}]
        messages_2 = [{"opcode": "time", "data": 0.02},
                      {"opcode": "sample", "data": [4, 5, 6]},
                      {"opcode": "flush", "data": None},
                      {"opcode": "sample", "data": [14, 15, 16]},
                      {"opcode": "sample", "data": [24, 25, 26]}]

        self.assertTrue(
            self.test_comparison.correct_messages(messages_1, messages_2)[0])

    def test_correct_messages_different_number_of_messages(self):
        # Use different data values as this checker should not check data value
        # and should allow these values to pass
        messages_1 = [{"opcode": "time", "data": 0.01},
                      {"opcode": "sample", "data": [1, 2, 3]},
                      {"opcode": "flush", "data": None},
                      {"opcode": "sample", "data": [10, 11, 13]},
                      {"opcode": "sample", "data": [21, 22, 23]},
                      {"opcode": "sample", "data": [31, 32, 33]}]
        messages_2 = [{"opcode": "time", "data": 0.02},
                      {"opcode": "sample", "data": [4, 5, 6]},
                      {"opcode": "flush", "data": None},
                      {"opcode": "sample", "data": [14, 15, 16]},
                      {"opcode": "sample", "data": [24, 25, 26]}]

        self.assertFalse(
            self.test_comparison.correct_messages(messages_1, messages_2)[0])

    def test_correct_messages_different_opcodes(self):
        # Use different data values as this checker should not check data value
        # and should allow these values to pass
        messages_1 = [{"opcode": "time", "data": 0.01},
                      {"opcode": "sample", "data": [1, 2, 3]},
                      {"opcode": "flush", "data": None},
                      {"opcode": "sample", "data": [10, 11, 13]},
                      {"opcode": "sample", "data": [21, 22, 23]}]
        messages_2 = [{"opcode": "sample_interval", "data": 0.02},
                      {"opcode": "sample", "data": [4, 5, 6]},
                      {"opcode": "flush", "data": None},
                      {"opcode": "sample", "data": [14, 15, 16]},
                      {"opcode": "sample", "data": [24, 25, 26]}]

        self.assertFalse(
            self.test_comparison.correct_messages(messages_1, messages_2)[0])

    def test_correct_messages_different_data_length(self):
        # Use different data values as this checker should not check data value
        # and should allow these values to pass
        messages_1 = [{"opcode": "time", "data": 0.01},
                      {"opcode": "sample", "data": [1, 2, 3]},
                      {"opcode": "flush", "data": None},
                      {"opcode": "sample", "data": [10, 11, 13]},
                      {"opcode": "sample", "data": [21, 22, 23, 40]}]
        messages_2 = [{"opcode": "time", "data": 0.02},
                      {"opcode": "sample", "data": [4, 5, 6]},
                      {"opcode": "flush", "data": None},
                      {"opcode": "sample", "data": [14, 15, 16]},
                      {"opcode": "sample", "data": [24, 25, 26]}]

        self.assertFalse(
            self.test_comparison.correct_messages(messages_1, messages_2)[0])

    def test_check_time_message_exactly_equal(self):
        # Check different time values pass
        reference     = {"opcode": "time", "data": decimal.Decimal(123.456)}
        same_value    = {"opcode": "time", "data": decimal.Decimal(123.456)}
        diff_integer  = {"opcode": "time", "data": decimal.Decimal(987.456)}
        diff_fraction = {"opcode": "time", "data": decimal.Decimal(123.465)}

        success, msg = self.test_comparison._check_time_message(reference, same_value)
        self.assertTrue(success, "'reference' and 'same' value DO NOT match.\n"+msg)

        success, msg = self.test_comparison._check_time_message(reference, diff_integer)
        self.assertFalse(success, "'reference' and 'diff_integer' value DO match - but shouldn't.")

        success, msg = self.test_comparison._check_time_message(reference, diff_fraction)
        self.assertFalse(success, "'reference' and 'different_fraction' value DO match - but shouldn't.")

    def test_check_time_message_equal_within_precision(self):
        orig_precision = decimal.getcontext().prec
        decimal.getcontext().prec = 128
        for precision, input in [(p, i)
                                 for p in [40, 45, 62, 63, 64, 65]
                                 for i in [123.456, "0.1", "123456.66666666666666666"]
                                ]:
            # Use value divided by 3, as that is an awkward
            # recurring fraction in a decimal representation
            ref_value = decimal.Decimal(input) / 3

            # Set precision
            self.test_comparison.TIME_FRACTIONAL_BITS_PRECISION = precision
            print(f"\nprecision: {precision}")

            # Get the smallest difference detectable at this precision
            smallest_diff = decimal.Decimal(1/(2**precision))

            # Expect plus or minus the smallest difference to be detected
            # as not the same by the comparison.
            reference        = {"opcode": "time", "data": ref_value}
            plus_small_diff  = {"opcode": "time", "data": ref_value + smallest_diff}
            minus_small_diff = {"opcode": "time", "data": ref_value - smallest_diff}

            print(f"smallest      : {smallest_diff           :<55} i.e.", self.test_comparison._time_to_hex_string(smallest_diff))
            print(f"ref           : {ref_value               :<55} i.e.", self.test_comparison._time_to_hex_string(ref_value))
            print(f"+ smallest    : {plus_small_diff['data'] :<55} i.e.", self.test_comparison._time_to_hex_string(plus_small_diff['data']))
            print(f"- smallest    : {minus_small_diff['data']:<55} i.e.", self.test_comparison._time_to_hex_string(minus_small_diff['data']))

            success, msg = self.test_comparison._check_time_message(reference, plus_small_diff)
            self.assertFalse(success, "'reference' and 'plus_small_diff' value DO match - but shouldn't.")

            success, msg = self.test_comparison._check_time_message(reference, minus_small_diff)
            self.assertFalse(success, "'reference' and 'minus_small_diff' value DO match - but shouldn't.")

            # Create values with all bits below the precision set or cleared, expect
            # these to be compared as the same value.
            # To create test values with more data than required precision, shift
            # fraction up by 128bits assuming that is more than precision required
            number_of_bits = 128
            integer_part = int(ref_value)
            fraction_bits = int((ref_value - integer_part) * (2**number_of_bits))
            precision_mask = ((2**number_of_bits) - (2**(number_of_bits-precision)))
            zeros_fraction = (fraction_bits & precision_mask)
            ones_fraction = (~(~fraction_bits & precision_mask)) & ((2**number_of_bits)-1)
            zeros_value = decimal.Decimal(integer_part) + (decimal.Decimal(zeros_fraction) / (2**number_of_bits))
            ones_value  = decimal.Decimal(integer_part) + (decimal.Decimal(ones_fraction)  / (2**number_of_bits))

            all_zero_below_precision = {"opcode": "time", "data": zeros_value}
            all_ones_below_precision = {"opcode": "time", "data": ones_value}

            print(f"precision_mask: 0x{precision_mask:032X}")
            print(f"fraction_bits : 0x{fraction_bits :032X}")
            print(f"zeros_fraction: 0x{zeros_fraction:032X}")
            print(f"ones_fraction : 0x{ones_fraction :032X}")
            print(f"smallest      : {smallest_diff:<55} i.e.", self.test_comparison._time_to_hex_string(smallest_diff))
            print(f"ref           : {ref_value    :<55} i.e.", self.test_comparison._time_to_hex_string(ref_value))
            print(f"zeros_value   : {zeros_value  :<55} i.e.", self.test_comparison._time_to_hex_string(zeros_value))
            print(f"ones_value    : {ones_value   :<55} i.e.", self.test_comparison._time_to_hex_string(ones_value))

            success, msg = self.test_comparison._check_time_message(reference, all_zero_below_precision)
            self.assertTrue(success, "'reference' and 'all_zero_below_precision' value DO NOT match.\n"+msg)
            success, msg = self.test_comparison._check_time_message(reference, all_ones_below_precision)
            self.assertTrue(success, "'reference' and 'all_ones_below_precision' value DO NOT match.\n"+msg)

        decimal.getcontext().prec = orig_precision

