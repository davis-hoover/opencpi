#!/usr/bin/env python3

# Bounded checker between reference and implementation with allowed exceptions
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
from .bounded import BoundedDefaults


class BoundedWithExceptionDefaults:
    # This class houses all the default values used. The structure is designed
    # for importing and documenting in an easier way.

    # The : after the # of comments here ensures the comments are imported into
    # the build documentation.

    #: Wider bound that a sample must be within if it exceeds ``BOUND``, so
    #: long as the percentage of samples between ``BOUND`` and
    #: ``EXCEPTION_BOUND`` in a message does not exceed the
    #: ``ALLOWED_EXCEPTION_RATE``.
    EXCEPTION_BOUND = 10

    #: Rate of the number of samples in a sample message that may be above
    #: ``BOUND`` but below ``EXCEPTION_BOUND`` for the comparison test to pass
    #: for a message. A rate of 1 equates to 100%. Even with a low rate and
    #: a short message at least one exception will always be allowed.
    ALLOWED_EXCEPTION_RATE = 0.01


class BoundedWithException(BasicComparison):
    """ Check rate of sample difference above bound is below exception rate

    Checks all the differences between respective samples in reference and
    implementation-under-test are below the allowed standard bound. If above
    this a number of samples are allowed to be above the standard bound so long
    as they are below the exception bound. The number of samples that are
    allowed to be above the standard bound, but less than the exception bound
    is based on the message length and the allowed exception rate (settable);
    however will always allow at least one exception regardless of message
    length or exception rate.
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
        self.EXCEPTION_BOUND = BoundedWithExceptionDefaults.EXCEPTION_BOUND
        self.ALLOWED_EXCEPTION_RATE = \
            BoundedWithExceptionDefaults.ALLOWED_EXCEPTION_RATE
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
                "EXCEPTION_BOUND": self.EXCEPTION_BOUND,
                "ALLOWED_EXCEPTION_RATE": self.ALLOWED_EXCEPTION_RATE,
                "WRAP_ROUND_VALUES": self.WRAP_ROUND_VALUES}

    def same(self, reference, implementation):
        """ Checks if two output data sets are considered the same

        In this case same is where all data of all messages values match within
        a standard bound or a set number of values match within a larger bound.

        Args:
            reference (list): List of reference messages. A message is a
                dictionary with an "opcode" and "data" key word, which have
                values of the opcode name and the data value for that message.
                Reference messages are typically from running a (Python)
                reference implementation against the input data.
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
                    f"Message {index} (zero indexed) not the same in " +
                    "reference and implementation-under-test.\n" +
                    failure_message)

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
                    f"{reference['opcode'].capitalize()} data differs " +
                    "between reference and implementation-under-test.\n" +
                    f"Reference data                : {reference['data']}\n" +
                    "Implementation-under-test data: " +
                    f"{implementation['data']}")

        # Flush and discontinuity are messages without data
        elif reference["opcode"] in ["flush", "discontinuity"]:
            # No data is associated with flush and discontinuity messages
            pass

        elif reference["opcode"] == "metadata":
            if reference["data"]["id"] != implementation["data"]["id"] or \
                    reference["data"]["value"] != implementation["data"][
                        "value"]:
                return False, (
                    f"{reference['opcode'].capitalize()} data differs " +
                    "between reference and implementation-under-test.\n" +
                    "Reference data:\n" +
                    pprint.pformat(reference["data"]) +
                    "Implementation-under-test data:\n" +
                    pprint.pformat(implementation["data"]))

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
        exception_count = 0
        # Always allow at least one exception. As otherwise would encourage a
        # high exception rate to ensure short messages pass.
        allowed_exceptions = max(1, int(self.ALLOWED_EXCEPTION_RATE *
                                        len(reference_data)))
        if self._complex:
            for index, (reference_value, implementation_value) in enumerate(
                    zip(reference_data, implementation_data)):
                if self._within_bound(reference_value.real,
                                      implementation_value.real,
                                      self.BOUND) is False:
                    if self._within_bound(reference_value.real,
                                          implementation_value.real,
                                          self.EXCEPTION_BOUND) is True:
                        exception_count = exception_count + 1
                    else:
                        show_from = max(0, index - 5)
                        show_to = min(len(reference_data),
                                      len(implementation_data), index + 5)
                        return False, (
                            "Sample data differs by more than allowed " +
                            f"standard bound of {self.BOUND} and exception " +
                            f"bound of {self.EXCEPTION_BOUND} for real " +
                            f"value at index {index} (zero indexed).\n" +
                            f"Reference samples {show_from} to {show_to} " +
                            "(zero indexed):\n" +
                            f"  {reference_data[show_from:show_to]}\n" +
                            f"Implementation-under-test samples {show_from} " +
                            f"to {show_to} (zero indexed):\n" +
                            f"  {implementation_data[show_from:show_to]}")
                if self._within_bound(reference_value.imag,
                                      implementation_value.imag,
                                      self.BOUND) is False:
                    if self._within_bound(reference_value.imag,
                                          implementation_value.imag,
                                          self.EXCEPTION_BOUND) is True:
                        exception_count = exception_count + 1
                    else:
                        show_from = max(0, index - 5)
                        show_to = min(len(reference_data),
                                      len(implementation_data), index + 5)
                        return False, (
                            "Sample data differs by more than allowed " +
                            f"standard bound of {self.BOUND} and exception " +
                            f"bound of {self.EXCEPTION_BOUND} for imaginary " +
                            f"value at index {index} (zero indexed).\n" +
                            f"Reference samples {show_from} to {show_to} " +
                            "(zero indexed):\n" +
                            f"  {reference_data[show_from:show_to]}\n" +
                            f"Implementation-under-test samples {show_from} " +
                            f"to {show_to} (zero indexed):\n" +
                            f"  {implementation_data[show_from:show_to]}")
                if exception_count > allowed_exceptions:
                    return False, (
                        "Sample data has more exceptions than the allowed " +
                        f"rate of {self.ALLOWED_EXCEPTION_RATE} for a " +
                        f"message of {len(reference_data)}.\n" +
                        "  Allowed number of exceptions: " +
                        f"{allowed_exceptions}")

        else:
            for index, (reference_value, implementation_value) in enumerate(
                    zip(reference_data, implementation_data)):
                if self._within_bound(reference_value,
                                      implementation_value,
                                      self.BOUND) is False:
                    if self._within_bound(reference_value,
                                          implementation_value,
                                          self.EXCEPTION_BOUND) is True:
                        exception_count = exception_count + 1
                    else:
                        show_from = max(0, index - 5)
                        show_to = min(len(reference_data),
                                      len(implementation_data), index + 5)
                        return False, (
                            "Sample data differs by more than allowed " +
                            f"standard bound of {self.BOUND} and exception " +
                            f"bound of {self.EXCEPTION_BOUND} at index " +
                            f"{index} (zero indexed).\n" +
                            f"Reference samples {show_from} to {show_to} " +
                            "(zero indexed):\n" +
                            f"  {reference_data[show_from:show_to]}\n" +
                            f"Implementation-under-test samples {show_from} " +
                            f"to {show_to} (zero indexed):\n" +
                            f"  {implementation_data[show_from:show_to]}")
                if exception_count > allowed_exceptions:
                    return False, (
                        "Sample data has more exceptions than the allowed " +
                        f"rate of {self.ALLOWED_EXCEPTION_RATE} for a " +
                        f"message of {len(reference_data)}.\n" +
                        "  Allowed number of exceptions: " +
                        f"{allowed_exceptions}")

        # Passes, no failure message
        return True, ""

    def _within_bound(self, reference, implementation, bound):
        """ Check if two values are within allowed bound

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
            bound (int, float): Limit values must not differ by.

        Returns:
            Boolean which is ``True`` when within allowed bound (including
                overflow / underflow when set), otherwise returns ``False``.
        """
        if abs(reference - implementation) <= bound:
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
                "For wrap round bounds testing, both a lower and upper " +
                "bound must be set and neither can be None")

        # No value should ever be outside of self.WRAP_ROUND_VALUES. This is a
        # ValueError not a test fail as an error in the setting of the
        # self.WRAP_ROUND_VALUES not at the maximum and minimum for the sample
        # data type; rather than the test bound condition failing.
        if min([reference, implementation]) < min(self.WRAP_ROUND_VALUES):
            raise ValueError(
                "When wrap round bounds testing, self.WRAP_ROUND_VALUES " +
                "must contain the smallest value the sample data can take. " +
                "A reference or implementation-under-test value is less " +
                "than the lower value in self.WRAP_ROUND_VALUES of " +
                f"{min(self.WRAP_ROUND_VALUES)}")
        if max([reference, implementation]) > max(self.WRAP_ROUND_VALUES):
            raise ValueError(
                "When wrap round bounds testing, self.WRAP_ROUND_VALUES " +
                "must contain the largest value the sample data can take. A " +
                "reference or implementation-under-test value is greater " +
                "than the upper value in self.WRAP_ROUND_VALUES of " +
                f"{max(self.WRAP_ROUND_VALUES)}")

        # Find the distance the reference and implementation are to their
        # closest wrapping limit
        lower_value_to_lower_wrap = abs(min(self.WRAP_ROUND_VALUES)
                                        - min([reference, implementation]))
        upper_value_to_upper_wrap = abs(max(self.WRAP_ROUND_VALUES)
                                        - max([reference, implementation]))

        # Use the distance to wrapping round bounds to find if within bound. A
        # plus one since a variation of one is needed to cause the wrap round.
        variation = lower_value_to_lower_wrap + upper_value_to_upper_wrap + 1
        if variation > bound:
            return False

        return True

    def __repr__(self):
        """ Official string representation of object
        """
        return (f"ocpi_testing.Bounded(complex_={self._complex}, " +
                f"sample_data_type={self._sample_data_type})")

    def __str__(self):
        """ Informal string representation of object
        """
        return self.__repr__()
