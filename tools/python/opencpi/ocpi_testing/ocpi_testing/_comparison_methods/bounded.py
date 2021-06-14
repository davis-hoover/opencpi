#!/usr/bin/env python3

# Checker for bound match between reference and implementation data
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


import math
import pprint

from .base_comparison import BasicComparison


class BoundedDefaults:
    # This class houses all the default values used. The structure is designed
    # for importing and documenting in an easier way.

    # The : after the # of comments here ensures the comments are imported into
    # the build documentation.

    #: Sample values of the implementation-under-test must be within +/- of
    #: this bound value of their respective reference value for this comparison
    #: method to pass.
    BOUND = 2

    #: Set the lower and upper "wrap round" values (i.e. the values at which
    #: underflow and overflow occur). When set to ``[None, None]`` wrapping
    #: round of bounds will not be implemented.
    WRAP_ROUND_VALUES = [None, None]


class Bounded(BasicComparison):
    """ Check sample samples are within some fixed bound
    """

    def __init__(self, complex_, sample_data_type):
        """ Check messages sets are similar / the same

        Args:
            complex (bool): Indicate if the data type is complex (True) or not
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
        self.BOUND = BoundedDefaults.BOUND
        self.WRAP_ROUND_VALUES = BoundedDefaults.WRAP_ROUND_VALUES

    def variable_summary(self):
        """ Returns summary of the variables that control the comparison method

        Cannot rely on the values being fixed for all tests since may need to
        be changed depending on the component-under-tests performance.

        Returns:
            Dictionary which is the variable names as keys and their respective
                values as the items. Includes all variables that control the
                comparison method.
        """
        return {"BOUND": self.BOUND,
                "WRAP_ROUND_VALUES": self.WRAP_ROUND_VALUES}

    def same(self, reference, implementation):
        """ Checks if two output data sets are considered the same

        In this case same is where all data of all messages values match within
        some band.

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
            Bool, str. A boolean to indicate if the test passed (True) or
                failed (False). String that is the reason for any failure, in
                the case of tests which pass returns an empty string.
        """
        # Standard check from inherited class
        test_result, failure_message = self.correct_messages(reference,
                                                             implementation)
        if test_result is False:
            return False, failure_message

        for index, (reference_message, implementation_message) in \
                enumerate(zip(reference, implementation)):
            check_result, failure_message = self._check_message(
                reference_message, implementation_message)
            if check_result is False:
                return False, (
                    f"Message {index} (zero indexed) not the same in "
                    + "reference and implementation-under-test.\n"
                    + failure_message)

        # Checks pass, no failure message
        return True, ""

    def _check_message(self, reference, implementation):
        """ Check two messages are the same

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
        # No check for same opcodes as done as part of basic comparison
        if reference["opcode"] == "sample":
            result, fail_message = self._check_sample_data(
                reference["data"], implementation["data"])
            if result is False:
                return False, fail_message

        # Time and sample interval are a single data value
        elif reference["opcode"] in ["time", "sample_interval"]:
            if reference["data"] != implementation["data"]:
                return False, (
                    f"{reference['opcode'].capitalize()} data differs "
                    + "between reference and implementation-under-test.\n"
                    + f"Reference data                : {reference['data']}\n"
                    + "Implementation-under-test data: "
                    + f"{implementation['data']}")

        # Flush and discontinuity are messages without data
        elif reference["opcode"] in ["flush", "discontinuity"]:
            # No data is associated with flush and discontinuity messages
            pass

        elif reference["opcode"] == "metadata":
            if reference["data"]["id"] != implementation["data"]["id"] or \
                    reference["data"]["value"] != implementation["data"][
                        "value"]:
                return False, (
                    f"{reference['opcode'].capitalize()} data differs "
                    + "between reference and implementation-under-test.\n"
                    + "Reference data:\n"
                    + pprint.pformat(reference["data"])
                    + "Implementation-under-test data:\n"
                    + pprint.pformat(implementation["data"]))

        else:
            raise ValueError(f"Unsupported opcode of {reference['opcode']}")

        # Test will pass to reach here, no error message
        return True, ""

    def _check_sample_data(self, reference_data, implementation_data):
        """ Determine if all sample data values are within bound

        Checks if the difference between each data point is within the allowed
        bound, set by ``self.BOUND``.

        Args:
            reference_data (list): The reference data values to be used.
            implementation_data (list): The implementation data values being
                checked.

        Returns:
            Boolean which is ``True`` if all data values are within the allowed
                bound, otherwise returns ``False``. With string which is the
                failure message (and empty string if test passed).
        """
        if self._complex:
            for index in range(len(reference_data)):
                if self._within_bound(reference_data[index].real,
                                      implementation_data[index].real) is False:
                    show_from = max(0, index - 5)
                    show_to = min(len(reference_data),
                                  len(implementation_data), index + 5)
                    return False, (
                        "Sample data differs by more than allowed bound of "
                        + f"{self.BOUND}, for real value, at index {index} "
                        + "(zero indexed).\n"
                        + f"Reference samples {show_from} to {show_to} (zero "
                        + "indexed):\n"
                        + f"  {reference_data[show_from:show_to]}\n"
                        + f"Implementation-under-test samples {show_from} to "
                        + f"{show_to} (zero indexed):\n"
                        + f"  {implementation_data[show_from:show_to]}")
                if self._within_bound(reference_data[index].imag,
                                      implementation_data[index].imag) is False:
                    show_from = max(0, index - 5)
                    show_to = min(len(reference_data),
                                  len(implementation_data), index + 5)
                    return False, (
                        "Sample data differs by more than allowed bound of "
                        + f"{self.BOUND}, for imaginary value, at index "
                        + f"{index} (zero indexed).\n"
                        + f"Reference samples {show_from} to {show_to} (zero "
                        + "indexed):\n"
                        + f"  {reference_data[show_from:show_to]}\n"
                        + f"Implementation-under-test samples {show_from} to "
                        + f"{show_to} (zero indexed):\n"
                        + f"  {implementation_data[show_from:show_to]}")

        else:
            for index in range(len(reference_data)):
                if self._within_bound(reference_data[index],
                                      implementation_data[index]) is False:
                    show_from = max(0, index - 5)
                    show_to = min(len(reference_data),
                                  len(implementation_data), index + 5)
                    return False, (
                        "Sample data differs by more than allowed bound of "
                        + f"{self.BOUND} at index {index} (zero indexed).\n"
                        + f"Reference samples {show_from} to {show_to} (zero "
                        + "indexed):\n"
                        + f"  {reference_data[show_from:show_to]}\n"
                        + f"Implementation-under-test samples {show_from} to "
                        + f"{show_to} (zero indexed):\n"
                        + f"  {implementation_data[show_from:show_to]}")

        # Passes, no failure message
        return True, ""

    def _within_bound(self, reference, implementation):
        """ Check if two values are within allowed bound

        Reference and implementation value must differ by less than
        ``self.BOUND`` for test to pass.

        If ``self.WRAP_ROUND_VALUES`` are set then the allowed bounds variation
        includes allowing overflow, for example if ``self.WRAP_ROUND_VALUES``
        is ``[-128, 127]`` (i.e. set to character limits), with ``self.BOUND``
        set to ``5``. Then if ``reference`` is ``-127`` and ``implementation``
        is ``127`` this will pass as they are within the allowed bound when
        overflow occurs.

        If any values are not a number or +/- infinity, then if the reference
        and implementation are the same will pass.

        Args:
            reference (int, float): The reference value.
            implementation (int, float): The value to be checked.

        Returns:
            Boolean which is ``True`` when within allowed bound (including
                overflow / underflow when set), otherwise returns ``False``.
        """
        if abs(reference - implementation) <= self.BOUND:
            return True

        # Allow complex values that are the same. By definition float("nan") ==
        # float("nan") returns false, so check if both are not a number and if
        # so pass test
        if math.isnan(reference) and math.isnan(implementation):
            return True

        # The same values should always pass, mainly intended to capture +/-
        # infinity
        if reference == implementation:
            return True

        # Fail test when not allowing wrap round
        if all(bound is None for bound in self.WRAP_ROUND_VALUES):
            return False

        # Need a lower and upper bound set
        if any(bound is None for bound in self.WRAP_ROUND_VALUES):
            raise ValueError(
                "For wrap round bounds testing, both a lower and upper "
                + "bound must be set and neither can be None")

        # No value should ever be outside of self.WRAP_ROUND_VALUES. This is a
        # ValueError not a test fail as an error in the setting of the
        # self.WRAP_ROUND_VALUES not at the maximum and minimum for the sample
        # data type; rather than the test bound condition failing.
        if min([reference, implementation]) < min(self.WRAP_ROUND_VALUES):
            raise ValueError(
                "When wrap round bounds testing, self.WRAP_ROUND_VALUES "
                + "must contain the smallest value the sample data can take. "
                + "A reference or implementation-under-test value is less "
                + "than the lower value in self.WRAP_ROUND_VALUES of "
                + f"{min(self.WRAP_ROUND_VALUES)}")
        if max([reference, implementation]) > max(self.WRAP_ROUND_VALUES):
            raise ValueError(
                "When wrap round bounds testing, self.WRAP_ROUND_VALUES "
                + "must contain the largest value the sample data can take. A "
                + "reference or implementation-under-test value is greater "
                + "than the upper value in self.WRAP_ROUND_VALUES of "
                + f"{max(self.WRAP_ROUND_VALUES)}")

        # Find the distance the reference and implementation are to their
        # closest wrapping limit
        lower_value_to_lower_wrap = abs(min(self.WRAP_ROUND_VALUES) -
                                        min([reference, implementation]))
        upper_value_to_upper_wrap = abs(max(self.WRAP_ROUND_VALUES) -
                                        max([reference, implementation]))

        # Use the distance to wrapping round bounds to find if within bound. A
        # plus one since a variation of one is needed to cause the wrap round.
        variation = lower_value_to_lower_wrap + upper_value_to_upper_wrap + 1
        if variation > self.BOUND:
            return False

        return True

    def __repr__(self):
        """ Official string representation of object
        """
        return (f"ocpi_testing.Bounded(complex_={self._complex}, "
                + f"sample_data_type={self._sample_data_type})")

    def __str__(self):
        """ Informal string representation of object
        """
        return self.__repr__()
