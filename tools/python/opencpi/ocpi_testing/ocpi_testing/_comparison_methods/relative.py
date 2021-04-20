#!/usr/bin/env python3

# Checker for relative match between reference and implementation data
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


class RelativeDefaults:
    # This class houses all the default values used. The structure is designed
    # for importing and documenting in an easier way.

    # The : after the # of comments here ensures the comments are imported into
    # the build documentation.

    #: Sample values of the implementation-under-test must be within this
    #: relative error bound of their respective reference value for this
    #: comparison method to pass. Default value set to match Python's
    #: ``math.isclose()`` default relative tolerance.
    RELATIVE_TOLERANCE = 1e-9

    #: The minimum permitted absolute tolerance, which is used for comparing to
    #: values near zero.
    ABSOLUTE_TOLERANCE = 1e-9


class Relative(BasicComparison):
    """ Check sample samples are within some relative bound

    Uses and matches behaviour of Python's ``math.isclose()``.
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
        self.RELATIVE_TOLERANCE = RelativeDefaults.RELATIVE_TOLERANCE
        self.ABSOLUTE_TOLERANCE = RelativeDefaults.ABSOLUTE_TOLERANCE

    def variable_summary(self):
        """ Returns summary of the variables that control the comparison method

        Cannot rely on the values being fixed for all tests since may need to
        be changed depending on the component-under-tests performance.

        Returns:
            Dictionary which is the variable names as keys and their respective
                values as the items. Includes all variables that control the
                comparison method.
        """
        return {"RELATIVE_TOLERANCE": self.RELATIVE_TOLERANCE,
                "ABSOLUTE_TOLERANCE": self.ABSOLUTE_TOLERANCE}

    def same(self, reference, implementation):
        """ Checks if two output data sets are considered the same

        In this case same is where all data of all messages values match within
        a relative (or the absolute minimum) band, as implemented by Python's
        ``math.isclose()`` function.

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
        """ Determine if all sample data values are within a relative bound

        Checks if the difference between each data point is within the allowed
        relative bound, set by ``self.RELATIVE_TOLERANCE``. Or for small values
        within the set absolute bound, set by ``self.ABSOLUTE_TOLERANCE``.

        Check implemented using Python's ``math.isclose()``.

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
            for index, (reference_value, implementation_value) in enumerate(
                    zip(reference_data, implementation_data)):
                if self._within_tolerance(reference_value.real,
                                          implementation_value.real) is False:
                    show_from = max(0, index - 5)
                    show_to = min(len(reference_data),
                                  len(implementation_data), index + 5)
                    return False, (
                        "Sample data differs by more than allowed relative "
                        + f"tolerance of {self.RELATIVE_TOLERANCE} (and "
                        + f"absolute tolerance of {self.ABSOLUTE_TOLERANCE}), "
                        + f"for real value, at index {index} (zero indexed).\n"
                        + f"Reference samples {show_from} to {show_to} (zero "
                        + "indexed):\n"
                        + f"  {reference_data[show_from:show_to]}\n"
                        + f"Implementation-under-test samples {show_from} to "
                        + f"{show_to} (zero indexed):\n"
                        + f"  {implementation_data[show_from:show_to]}")
                if self._within_tolerance(reference_value.imag,
                                          implementation_value.imag) is False:
                    show_from = max(0, index - 5)
                    show_to = min(len(reference_data),
                                  len(implementation_data), index + 5)
                    return False, (
                        "Sample data differs by more than allowed relative "
                        + f"tolerance of {self.RELATIVE_TOLERANCE} (and "
                        + f"absolute tolerance of {self.ABSOLUTE_TOLERANCE}), "
                        + f"for imaginary value, at index {index} (zero "
                        + "indexed).\n"
                        + f"Reference samples {show_from} to {show_to} (zero "
                        + "indexed):\n"
                        + f"  {reference_data[show_from:show_to]}\n"
                        + f"Implementation-under-test samples {show_from} to "
                        + f"{show_to} (zero indexed):\n"
                        + f"  {implementation_data[show_from:show_to]}")

        else:
            for index, (reference_value, implementation_value) in enumerate(
                    zip(reference_data, implementation_data)):
                if self._within_tolerance(reference_value,
                                          implementation_value) is False:
                    show_from = max(0, index - 5)
                    show_to = min(len(reference_data),
                                  len(implementation_data), index + 5)
                    return False, (
                        "Sample data differs by more than allowed relative "
                        + f"tolerance of {self.RELATIVE_TOLERANCE} (and "
                        + f"absolute tolerance of {self.ABSOLUTE_TOLERANCE}) "
                        + f"at index {index} (zero indexed).\n"
                        + f"Reference samples {show_from} to {show_to} (zero "
                        + "indexed):\n"
                        + f"  {reference_data[show_from:show_to]}\n"
                        + f"Implementation-under-test samples {show_from} to "
                        + f"{show_to} (zero indexed):\n"
                        + f"  {implementation_data[show_from:show_to]}")

        # Passes, no failure message
        return True, ""

    def _within_tolerance(self, reference, implementation):
        """ Check if two values are within allowed bound

        ``math.isclose()`` when given reference and implementation values must
        differ return ``True`` for test to pass.

        If any values are not a number or +/- infinity, then if the reference
        and implementation are the same will pass.

        Args:
            reference (int, float): The reference value.
            implementation (int, float): The value to be checked.

        Returns:
            Boolean which is ``True`` when within allowed bound (including
                overflow / underflow when set), otherwise returns ``False``.
        """
        # Allow complex values that are the same. By definition float("nan") ==
        # float("nan") returns false, so check if both are not a number and if
        # so pass test
        if math.isnan(reference) and math.isnan(implementation):
            return True

        # The same values should always pass, mainly intended to capture +/-
        # infinity
        if reference == implementation:
            return True

        return math.isclose(reference, implementation,
                            rel_tol=self.RELATIVE_TOLERANCE,
                            abs_tol=self.ABSOLUTE_TOLERANCE)

    def __repr__(self):
        """ Official string representation of object
        """
        return (f"ocpi_testing.Relative(complex_={self._complex}, "
                + f"sample_data_type={self._sample_data_type})")

    def __str__(self):
        """ Informal string representation of object
        """
        return self.__repr__()
