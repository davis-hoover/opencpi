#!/usr/bin/env python3

# Simple comparison classes full comparison classes can inherit from
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


import abc
import collections
import decimal


class BaseComparison:
    """Comparison class other comparison methods inherit from."""

    def __init__(self, complex_, sample_data_type):
        """Check messages sets are similar / the same.

        Args:
            complex (bool): Indicate if the data type is complex (True) or not
                (False).
            sample_data_type (type): The Python type that a single sample data
                value is most like. E.g. for character protocol would be an
                int, for a complex short protocol would be int.

        Returns:
            Initialised class.
        """
        self._complex = complex_
        self._sample_data_type = sample_data_type

    @abc.abstractmethod
    def variable_summary(self):
        """Returns summary of the variables that control the comparison method.

        Cannot rely on the values being fixed for all tests since may need to
        be changed depending on the component-under-tests performance.

        Must be over-written by a child method since each set of variables will
        differ depending on the comparison method.

        Returns:
            Dictionary which is the variable names as keys and their respective
                values as the items. Includes all variables that control the
                comparison method.
        """
        raise NotImplementedError(
            "Child class must define own variable_summary() method.")

    @abc.abstractmethod
    def same(self, reference, implementation):
        """Checks if two output data sets are considered the same.

        Must be over-written by a child method using the specific checks
        defined for that class.

        Args:
            reference (list): List of reference messages. A message is a
                dictionary with an "opcode" and "data" key word, which have
                values of the opcode name and the data value for that message.
                Reference messages are typically from running a (Python)
                reference implementation against the input data.
            implementation (list): List of the messages to be checked. A
                message is a dictionary with an "opcode" and "data" key word,
                which have values of the opcode name and the data value for
                that message. Typically from the implementation-under-test
                being provided with the input test data.

        Returns:
            Bool, str. A boolean to indicate if the test passed (True) or
                failed (False). String that is the reason for any failure, in
                the case of tests which pass returns an empty string.
        """
        raise NotImplementedError("Child class must define own same() method.")


class BasicComparisonDefaults:
    """This class houses all the default values used.

    The structure is designed for importing and documenting in an easier way.
    """

    # The : after the # of comments here ensures the comments are imported into
    # the build documentation.

    #: The number of most significant bits of the fractional part of time
    #: values to compare.  Allows for some tests to pass if the time values
    #: are *almost* the same, bar some minor rounding/precision that is deemed
    #: insignificant.
    TIME_FRACTIONAL_BITS_PRECISION = 64


class BasicComparison(BaseComparison):
    """Run check every comparison method should do."""

    def __init__(self, complex_, sample_data_type):
        """Initialise the BasicComparison class.

        Args:
            complex_ (bool): Indicate if the data type is complex (True) or not
                (False).
            sample_data_type (type): The Python type that a single sample data
                value is most like. E.g. for character protocol would be an
                int, for a complex short protocol would be int.

        Returns:
            Initialised class.
        """
        super().__init__(complex_, sample_data_type)

        # Set variables as local as may be modified when set in the comparison
        # method instance in a specific test. Keep the same variable names to
        # ensure documentation matches.
        self.TIME_FRACTIONAL_BITS_PRECISION = BasicComparisonDefaults.TIME_FRACTIONAL_BITS_PRECISION

    def correct_messages(self, reference, implementation):
        """Check correct type (opcode) of messages and data length.

        Does not check the data content of messages as this must be done by
        inherited classes using the same() method each child class must define.

        Args:
            reference (list): List of reference messages. A message is a
                dictionary with an "opcode" and "data" key word, which have
                values of the opcode name and the data value for that message.
                Typically from running a Python reference implementation
                against the input data.
            implementation (list): List of the messages to be checked. A
                message is a dictionary with an "opcode" and "data" key word,
                which have values of the opcode name and the data value for
                that message. Typically from applying the implementation-under-
                test to the input data.

        Returns:
            A boolean to indicate if the test passed (True) or failed (False).
                Also returns a string that is the reason for any failure, in
                the case of tests which pass returns an empty string.
        """
        # Check same number of messages on all output ports
        if len(reference) != len(implementation):
            return False, (
                "Reference and implementation-under-test have a different "
                + "number of messages.\n"
                + f"Reference                : {len(reference)} messages\n"
                + f"Implementation-under-test: {len(implementation)} "
                + "messages\n")

        for index, (reference_message, implementation_message) in \
                enumerate(zip(reference, implementation)):
            # Check message opcodes are the same
            if reference_message["opcode"] != implementation_message["opcode"]:
                return False, (
                    f"Message {index} (zero indexed) has a different opcode "
                    + "in reference and implementation-under-test.\n"
                    + "Reference message opcode                : "
                    + f"{reference_message['opcode']}\n"
                    + "Implementation-under-test message opcode: "
                    + f"{implementation_message['opcode']}")

            # Check sample message have data of the same length
            if reference_message["opcode"] == "sample":
                if len(reference_message["data"]) != \
                        len(implementation_message["data"]):
                    return False, (
                        f"Message {index} (zero indexed) has different data "
                        + "length in reference and implementation-under-"
                        + "test.\n"
                        + "Reference data length                : "
                        + f"{len(reference_message['data'])} values\n"
                        + "Implementation-under-test data length: "
                        + f"{len(implementation_message['data'])} values")

        # All checks passed, no failure message
        return True, ""

    def _time_to_hex_string(self, value):
        """Convert a Q32.64 time value to a hex string for output.

        Args:
            value (Decimal/float): The value to convert.

        Returns:
            str: The value in "(int,fractional)" format with "0x" prefixes.
        """
        int_part = int(value)
        fraction = int((value - int_part) * (2**64))
        return f"(0x{int_part:08X},0x{fraction:016X})"

    def _check_time_message(self, reference, implementation):
        """Check two time or sample interval messages are the same.

        Args:
            reference (dict): The reference message to check the implementation
                message against. A dictionary with the keys "opcode" and
                "data".
            implementation (dict): Message to check against reference. A
                dictionary with the keys "opcode" and "data".

        Returns:
            A boolean to indicate if the test passed (True) or failed (False).
                Also returns a string that is the reason for any failure, in
                the case of tests which pass returns an empty string.
        """
        if reference["data"] == implementation["data"]:
            # Data matches exactly
            return True, ""

        # Data doesn't match exactly, so zero any data below
        # the number of fraction bits precision
        multiplier = (2**self.TIME_FRACTIONAL_BITS_PRECISION)
        reference_value = decimal.Decimal(
            int(decimal.Decimal(reference["data"]) * multiplier)
        ) / multiplier
        implementation_value = decimal.Decimal(
            int(decimal.Decimal(implementation["data"]) * multiplier)
        ) / multiplier

        if reference_value == implementation_value:
            # Data matches as far as the first N bits of the fractional value.
            return True, ""

        # Values don't match to this level of precision
        # Create a usefully formatted and aligned error message
        reference_str = str(reference["data"])
        implementation_str = str(implementation["data"])
        width = max(len(reference_str), len(implementation_str))

        reference_str = (f"{reference_str:{width}} ==> " +
                         self._time_to_hex_string(reference_value))
        implementation_str = (f"{implementation_str:{width}} ==> " +
                              self._time_to_hex_string(implementation_value))
        return False, (
            f"{reference['opcode'].capitalize()} data differs "
            + "between reference and implementation-under-test.\n"
            + f"Reference                : {reference_str}\n"
            + f"Implementation-under-test: {implementation_str}\n"
        )
