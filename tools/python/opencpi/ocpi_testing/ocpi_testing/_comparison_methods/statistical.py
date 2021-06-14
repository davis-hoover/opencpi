#!/usr/bin/env python3

# Checker for comparing reference and implementation data statistically
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

import numpy

from .base_comparison import BasicComparison


MEAN_DIFFERENCE_WARNING_LIMIT = 2.5
STANDARD_DEVIATION_WARNING_LIMIT = 4
STANDARD_DEVIATION_MULTIPLE_WARNING_LIMIT = 4


class StatisticalDefaults:
    # This class houses all the default values used. The structure is designed
    # for importing and documenting in an easier way.

    # The : after the # of comments here ensures the comments are imported into
    # the build documentation.

    #: The limit the mean (average) of all differences between reference and
    #: implementation-under-test values must be less than for the comparison to
    #: pass.
    MEAN_DIFFERENCE_LIMIT = 0.5

    #: The limit the standard deviation of all differences between reference
    #: and implementation-under-test values must be less than for the
    #: comparison to pass.
    STANDARD_DEVIATION_LIMIT = 0.5

    #: The number of multiples of the standard deviation a difference between a
    #: reference and its respective implementation-under-test value can be
    #: before the comparison method fails due to one pair of values being too
    #: far apart.
    STANDARD_DEVIATION_MULTIPLE = 3


# Duplicating print_warning() from ../_terminal_print_formatter.py since
# relative imports cannot go to a parent directory. The alternative of
# modifying sys.path is not desirable since this file is part of a module and
# so cannot guarantee installed location.
def print_warning(message):
    """ Print warning to terminal

    Warnings are in orange and with the warning word in bold. Format is
        Warning: Message.

    Args:
        message (str): Warning message to be printed to the terminal.
    """
    STANDARD_TERMINAL = "\033[0m"
    BOLD = "\033[1m"
    ORANGE = "\033[38;5;202m"
    print(ORANGE + BOLD + "Warning:" + STANDARD_TERMINAL,
          ORANGE + message + STANDARD_TERMINAL)


class Statistical(BasicComparison):
    """ Statistical sample data comparison
    """

    def __init__(self, complex, sample_data_type):
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
        if sample_data_type is bool:
            raise ValueError(
                "Statistical comparison is not suitable for boolean data")

        super().__init__(complex, sample_data_type)

        # Set variables as local as may be modified when set in the comparison
        # method instance in a specific test. Keep the same variable names to
        # ensure documentation matches.
        self.MEAN_DIFFERENCE_LIMIT = StatisticalDefaults.MEAN_DIFFERENCE_LIMIT
        self.STANDARD_DEVIATION_LIMIT = \
            StatisticalDefaults.STANDARD_DEVIATION_LIMIT
        self.STANDARD_DEVIATION_MULTIPLE = \
            StatisticalDefaults.STANDARD_DEVIATION_MULTIPLE

    def variable_summary(self):
        """ Returns summary of the variables that control the comparison method

        Cannot rely on the values being fixed for all tests since may need to
        be changed depending on the component-under-tests performance.

        Returns:
            Dictionary which is the variable names as keys and their respective
                values as the items. Includes all variables that control the
                comparison method.
        """
        return {"MEAN_DIFFERENCE_LIMIT": self.MEAN_DIFFERENCE_LIMIT,
                "STANDARD_DEVIATION_LIMIT": self.STANDARD_DEVIATION_LIMIT,
                "STANDARD_DEVIATION_MULTIPLE": self.STANDARD_DEVIATION_MULTIPLE
                }

    def same(self, reference, implementation):
        """ Checks if two output data sets are considered the same

        In this case same is where the difference between all data points is
        within some bound defined by the mean and standard deviation.

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

        # If the user has changed the failure limits to values considered to be
        # wide and so relaxed, print a warning.
        if self.MEAN_DIFFERENCE_LIMIT > MEAN_DIFFERENCE_WARNING_LIMIT:
            print_warning(
                "Mean difference limit is larger than found to be typically "
                + "needed, from experimental testing. Consider reducing the "
                + "size the mean difference limit is set to - the smallest "
                + "possible value makes the most effective testing.\n"
                + f"Mean difference limit set to {self.MEAN_DIFFERENCE_LIMIT}")
        if self.STANDARD_DEVIATION_LIMIT > STANDARD_DEVIATION_WARNING_LIMIT:
            print_warning(
                "Standard deviation of difference limit is larger than found "
                + "to be typically needed, from experimental testing. "
                + "Consider reducing the size of the standard deviation "
                + "limit - the smallest possible value makes the most "
                + "effective testing.\n"
                + "Standard deviation limit set to "
                + f"{self.STANDARD_DEVIATION_LIMIT}")
        if self.STANDARD_DEVIATION_MULTIPLE > \
                STANDARD_DEVIATION_MULTIPLE_WARNING_LIMIT:
            print_warning(
                "Multiplier applied to standard deviation to give bound of "
                + "allowed difference from mean is larger than found to be "
                + "typically needed, from experimental testing.\n"
                + "Standard deviation multiplier set to "
                + f"{self.STANDARD_DEVIATION_MULTIPLE}")

        # Calculate the difference between all values in all sample messages in
        # Python reference implementation and implementation-under-test.
        if self._complex:
            self._differences = {"real": [], "imaginary": []}
        else:
            self._differences = []

        for index, (reference_message, implementation_message) in \
                enumerate(zip(reference, implementation)):
            # Check non-sample messages
            if reference_message["opcode"] != "sample":
                check_result, fail_reason = self._check_non_sample_message(
                    reference_message, implementation_message)
                if check_result is False:
                    return False, (
                        f"Message {index} (zero indexed) not the same in "
                        + "reference and implementation-under-test.\n"
                        + failure_message)

            # Get the data difference for sample messages
            else:
                check_result, failure_message = self._parse_sample_message(
                    reference_message, implementation_message)
                if check_result is False:
                    return False, (
                        f"Message {index} (zero indexed). Sample data not "
                        + "similar.\n"
                        + failure_message)

        # Rest of the checks are to evaluate all of the sample data. But if
        # there have been no sample messages these checks are not needed.
        if self._complex:
            if len(self._differences["real"]) == 0 and len(
                    self._differences["imaginary"]) == 0:
                return True, ""
        else:
            if len(self._differences) == 0:
                return True, ""

        check_result, failure_message = self._statistical_check()
        if check_result is False:
            return False, f"Sample data not similar. {failure_message}"

        # Checks pass, no failure message
        return True, ""

    def _parse_sample_message(self, reference_message, implementation_message):
        """ Read in a sample message set for later statistical analysis

        As the statistical analysis is completed over all messages, the data in
        all sample messages needs to be read in - with some initial checks.

        Args:
            reference_message (dict): The reference message with the data to be
                read in data for later analysis.
            implementation_message. The implementation message with the data to
                be read in for later analysis.

        Returns:
            ``bool``, ``str``. A boolean to indicate if no reason to fail the
                test at this stage (``True``), or if the test should fail now
                from initial read in of the data (``False``). String that is
                the reason for any failure, in the case where there is no
                reason to fail the test returns an empty string.
        """
        if self._complex:
            for index, (reference, implementation) in enumerate(zip(
                    reference_message["data"],
                    implementation_message["data"])):
                difference, valid, fail_message = self._get_difference(
                    reference.real, implementation.real)
                if valid is False:
                    return False, (
                        "At sample index {index} (zero indexed). For real"
                        + f"axis.\n{fail_message}")
                if difference is not None:
                    self._differences["real"].append(difference)

                difference, valid, fail_message = self._get_difference(
                    reference.imag, implementation.imag)
                if valid is False:
                    return False, (
                        "At sample index {index} (zero indexed). For real"
                        + f"axis.\n{fail_message}")
                if difference is not None:
                    self._differences["imaginary"].append(difference)

        else:
            for index, (reference, implementation) in enumerate(zip(
                    reference_message["data"],
                    implementation_message["data"])):
                difference, valid, fail_message = self._get_difference(
                    reference, implementation)
                if valid is False:
                    return False, (
                        "At sample index {index} (zero indexed).\n"
                        + fail_message)
                if difference is not None:
                    self._differences.append(difference)

        self._store_smallest(reference_message["data"])
        self._store_largest(reference_message["data"])

        # No issue found
        return True, ""

    def _get_difference(self, reference, implementation):
        """ Find the difference between values and handle Nan and +/- inf

        When a NaN or a +/- inf are encountered check that the value is the
        same in both the reference and implementation, otherwise report the
        case where the data is not the same.

        Args:
            reference (int, float): Reference value to use in calculating the
                difference. Reference is typically from a Python reference
                implementation.
            implementation (int, float): Implementation-under-test value to use
                in calculating the difference.

        Returns:
            difference (float or None), valid (bool), fail message (str). The
                first returned value is the difference, if there is no
                difference to be used in statistical analysis returns None. The
                second returned value is a boolean to mark if calculating the
                difference was valid, if ``False`` there is an error in this
                data comparison (so the test should fail). The third, and last,
                value returned is the failure message, will be an empty string
                if the valid flag was ``True``.
        """
        if math.isnan(reference):
            if not math.isnan(implementation):
                return None, False, (
                    "Reference data has a not-a-number(NaN) value while "
                    + "implementation does not."
                    + f"  Reference:      {reference}\n"
                    + f"  Implementation: {implementation}")
            else:
                # In cases where the reference and implementation are both NaN
                # then remove the value from the set of values to be
                # statistically analysed. So do not add to self._differences.
                return None, True, ""
        if math.isnan(implementation):
            return None, False, (
                "Implementation data has a not-a-number (NaN) value while "
                + f"reference does not.\n"
                + f"  Reference:      {reference}\n"
                + f"  Implementation: {implementation}")
        if (reference in [float("inf"), -float("inf")]) or (
                implementation in [float("inf"), -float("inf")]):
            if reference != implementation:
                return None, False, (
                    "Reference and / or implementation contain +inf or -inf, "
                    + "but are not the same.\n"
                    + f"  Reference:      {reference}\n"
                    + f"  Implementation: {implementation}")
            else:
                # In cases where the reference and implementation are +/-
                # inf then remove the value from the set of values to be
                # statistically analysed. So do not add to self._differences.
                return None, True, ""

        return implementation - reference, True, ""

    def _statistical_check(self):
        """ Ensure the difference values are within allowed statistical bounds

        Uses ``self._differences`` as the differences between respective
        reference and implementation-under-test sample samples. Uses
        ``self._data_smallest`` and ``self._data_largest`` as the values of the
        smallest and largest values in the data by magnitude, respectively.

        Returns:
            Boolean and string. The boolean returned is ``True`` if the
                statistical checks on the data pass, otherwise will be
                ``False``. The string is the reason why the test failed, in
                cases where the test passes will be an empty string.
        """
        if self._complex:
            check_result, fail_reason = self._statistical_check_data(
                self._differences["real"], self._data_smallest.real,
                self._data_largest.real)
            if check_result is False:
                return False, f"On real axis; {fail_reason}"
            check_result, fail_reason = self._statistical_check_data(
                self._differences["imaginary"], self._data_smallest.imag,
                self._data_largest.imag)
            if check_result is False:
                return False, f"On imaginary axis; {fail_reason}"
            # Checks pass, no failure message
            return True, ""

        else:
            return self._statistical_check_data(
                self._differences, self._data_smallest, self._data_largest)

    def _statistical_check_data(self, data_difference, data_smallest,
                                data_largest):
        """ Ensure the difference values are within allowed statistical bounds

        For real (not imaginary) data values only.

        To pass this test all of the following conditions must be met:

         * The mean difference of all difference values must be less than a set
           limit.

         * The standard deviation of all difference values must be less than a
           set limit.

         * No difference can be more than ``self.STANDARD_DEVIATION_MULTIPLE``s
           standard deviations from the mean difference.

         * The mean difference limit and standard deviation limit set must not
           be set to values that does not provide assurance in relation to the
           data size (e.g. cannot be so large in proportion to all the data
           values being considered).

        Args:
            data_difference (list): A list of floats which is the difference
                between respective reference and implementation-under-test
                sample samples.
            data_smallest (float, int): The values of the smallest (in
                magnitude) value in the reference sample data.
            data_largest (float, int): The values of the largest (in
                magnitude) value in the reference sample data.

        Returns:
            Boolean and string. The boolean returned is ``True`` if the
                statistical checks on the data pass, otherwise will be
                ``False``. The string is the reason why the test failed, in
                cases where the test passes will be an empty string.
        """
        mean_difference = numpy.mean(data_difference)
        standard_deviation = numpy.std(data_difference)

        # When using the smallest and largest data values for checks if these
        # are near zero then a small increment will be needed. The small
        # increment used differs for integers and floats - note not the
        # smallest possible increment as noise in values causes error in this
        # case.
        if self._sample_data_type is int:
            small_data_increment = 2
        elif self._sample_data_type is float:
            small_data_increment = 2**(-60)
        else:
            raise TypeError(
                "Unsupported sample data type of "
                + f"{type(self._sample_data_type).__name__}")

        # Limit that the mean and standard deviation must be less then. Set
        # based on the data properties to ensure the mean and standard
        # deviation limits are not disproportional to the data size.
        statistical_value_limit = max(0.25 * data_largest,
                                      2 * small_data_increment)

        # With the smallest and largest data values check the mean difference
        # limit is reasonable.
        # Do not complete this check when the smallest data value is near zero
        # as in this case will always give a warning.
        if (self.MEAN_DIFFERENCE_LIMIT > data_smallest) and (
                data_smallest > small_data_increment):
            # Only give a warning, not an error since if the data contains very
            # small and very large values then it is quite possible that the
            # smallest value will be less than the mean difference limit. As
            # the absolute mean difference will be effected by the difference
            # between large values - which while relatively small for these
            # large values, will be large for small values.
            print_warning(
                "Mean of the difference limit for sample data values is "
                + "greater than the smallest data.\n"
                + f"Mean difference limit: {self.MEAN_DIFFERENCE_LIMIT:.50f}"
                + "\n"
                + f"Smallest data value  : {data_smallest:.50f}")
        if self.MEAN_DIFFERENCE_LIMIT > statistical_value_limit:
            # If the mean difference limit is a significant percentage of the
            # largest data value then the this testing is not going to give
            # confidence the sample values are similar.
            return False, (
                "Mean difference limit is significantly different to data "
                + "being compared to. Test fails as limit is not small enough "
                + "to provide assurance all values of reference and "
                + "implementation-under-test are similar.\n"
                + "Mean difference limit        : "
                + f"{self.MEAN_DIFFERENCE_LIMIT:.50f}\n"
                + "Upper limit on mean different: "
                + f"{statistical_value_limit:.50f}")

        # With the smallest and largest data values check the standard
        # deviation of the difference limit is reasonable.
        # Do not complete this check when the smallest data value is near zero
        # as in this case will always give a warning.
        if self.STANDARD_DEVIATION_LIMIT > data_smallest and \
                data_smallest > small_data_increment:
            # Only give a warning, not an error since if the data contains very
            # small and very large values then it is quite possible that the
            # smallest value will be less than the standard deviation of the
            # difference limit. As the standard deviation will be effected by
            # the difference between any large values - which while relatively
            # small to these large values may be large in comparison to any
            # small values.
            print_warning(
                "Standard deviation of the difference limit for sample data "
                + "values is greater than the smallest data value.\n"
                + "Standard deviation limit: "
                + f"{self.STANDARD_DEVIATION_LIMIT:.50f}\n" +
                + f"Smallest data value    : {data_smallest:.50f}")
        if self.STANDARD_DEVIATION_LIMIT > statistical_value_limit:
            # If the standard deviation of the difference limit is a
            # significant percentage of the largest data value then any checks
            # using this limit are unlikely give confidence that the Python
            # implementation and implementation-under-test are similar.
            return False, (
                "Standard deviation limit is significantly different to data "
                + "being compared to. Test fails as limit is not small enough "
                + "to provide assurance all values of reference and "
                + "implementation-under-test are similar.\n"
                + "Mean difference limit              : "
                + f"{self.STANDARD_DEVIATION_LIMIT:.50f}\n"
                + "Upper limit on mean different limit: "
                + f"{statistical_value_limit:.50f}")

        # Set limit of difference variation.
        if standard_deviation > small_data_increment:
            allowed_mean_variation = abs(
                self.STANDARD_DEVIATION_MULTIPLE * standard_deviation)
        else:
            # To handle very small variations and integers. Since integers
            # take more "discrete" values than the standard deviation (which
            # will be a float) use the integer step size.
            allowed_mean_variation = (self.STANDARD_DEVIATION_MULTIPLE *
                                      small_data_increment)

        # Check the allowed variation is not a significant proportion of the
        # whole data range
        limit_of_allowed_variation = max(
            0.2 * (data_largest - data_smallest),
            self.STANDARD_DEVIATION_MULTIPLE * small_data_increment,
            0.005 * data_largest)
        if allowed_mean_variation > limit_of_allowed_variation:
            return False, (
                "Allowed variation of the mean difference between reference " +
                "and implementation-under-test sample data is a significant " +
                "proportion of the total data range. Test fails as limit is " +
                "not small enough to provide assurance all values of the " +
                "reference and implementation-under-test are similar.\n" +
                "Allowed mean variation         : " +
                f"{allowed_mean_variation:.50f}\n" +
                "Limit on allowed mean variation: " +
                f"{limit_of_allowed_variation:.50f}")

        mean_difference_limits = {
            "lower": mean_difference - allowed_mean_variation,
            "upper": mean_difference + allowed_mean_variation}
        # Always allow zero difference to pass. If the standard deviation is
        # small (a good thing) the bound around the mean may not cover zero
        # difference, so check this and widen to cover zero difference between
        # the reference and implementation.
        if (mean_difference_limits["upper"] > 0) and (
                mean_difference_limits["lower"] > 0):
            mean_difference_limits["lower"] = 0 - small_data_increment
        if (mean_difference_limits["upper"] < 0) and (
                mean_difference_limits["lower"] < 0):
            mean_difference_limits["upper"] = 0 + small_data_increment

        # Check all values are within the allowed variation of the mean first,
        # as this will identify incorrect values early, and these incorrect
        # values are likely making the mean and standard deviation of the
        # difference large, so likely to cause those tests to fail as well.
        # But running other checks on the value of the mean and standard
        # deviation first is likely to hide the true error.
        for index, difference in enumerate(data_difference):
            if difference > mean_difference_limits["upper"]:
                return False, (
                    "Difference between reference and implementation-under-" +
                    f"test sample data sample at index {index} (zero " +
                    "indexed) differ by more than the allowed variation, in " +
                    "a positive direction.\n" +
                    "Maximum allowed difference: " +
                    f"{mean_difference_limits['upper']:.50f}\n" +
                    f"Difference at this sample : {difference:.50f}")
            if difference < mean_difference_limits["lower"]:
                return False, (
                    "Difference between reference and implementation-under-" +
                    f"test sample data sample at index {index} (zero " +
                    "indexed) differ by more than the allowed variation, in " +
                    "a negative direction.\n" +
                    "Minimum allowed difference: " +
                    f"{mean_difference_limits['lower']:.50f}\n" +
                    f"Difference at this sample : {difference:.50f}")

        # Mean must be small (below allowed magnitude), so average difference
        # is near zero so the general trend of value is similar.
        if abs(mean_difference) > self.MEAN_DIFFERENCE_LIMIT:
            return False, (
                "Magnitude of mean difference between reference and " +
                "implementation-under-test sample samples is greater than " +
                "mean difference limit.\n" +
                "Mean difference limit:\n" +
                f"  {self.MEAN_DIFFERENCE_LIMIT:.50f}\n" +
                "Mean difference between reference and implentation-under-" +
                "test samples:\n" +
                f"  {mean_difference:.50f}")

        # Standard deviation must be small (below allowed magnitude), so the
        # general difference between the Python implementation and
        # implementation-under-test is not significant.
        if abs(standard_deviation) > self.STANDARD_DEVIATION_LIMIT:
            return False, (
                "Magnitude of standard deviation of the difference between " +
                "sample samples in reference and implementation-under-test " +
                "is greater than allowed standard deviation limit.\n" +
                "Standard deviation of difference limit:\n" +
                f"{self.STANDARD_DEVIATION_LIMIT:.50f}\n" +
                "Standard deviation of difference of between reference and " +
                "implementation-under-test:\n" +
                f"{standard_deviation:.50f}")

        # Checks pass, no failure message
        return True, ""

    def _check_non_sample_message(self, reference_message,
                                  implementation_message):
        """ Check messages which are not sample messages are the same

        All non-sample messages are checked that data fields are exactly equal.

        Will raise error if given a message which is a sample message.

        Args:
            reference_message (dict): One of the messages to be checked is the
                same as the other. Typically from a Python reference
                implementation being used in the testing.
            implementation_message (dict): One of the messages to be checked is
                the same as the other. Typically from an implementation-under-
                test being tested in this testing.


        Returns:
            check_result (bool), fail_reason (str). Check result is True if the
                messages are determined to be the same, otherwise is False.
                Fail reason will be an empty string if if the test passes,
                otherwise will be a string describing why the test failed.
        """
        if reference_message["opcode"] == "sample":
            raise ValueError(
                "_check_non_sample_message() can only be used to check " +
                "messages which are not sample messages, reference_message " +
                "has an opcode of sample")
        if implementation_message["opcode"] == "sample":
            raise ValueError(
                "_check_non_sample_message() can only be used to check " +
                "messages which are not sample messages, " +
                "implementation_message has an opcode of sample")

        if reference_message["opcode"] != implementation_message["opcode"]:
            return False, (
                "Different message opcodes in reference and implementation-" +
                "under-test.\n" +
                "Reference message opcode        : " +
                f"{reference_message['opcode']}\n" +
                "Implementation-under-test opcode: "
                f"{implementation_message['opcode']}")

        if reference_message["data"] != implementation_message["data"]:
            return False, (
                f"{reference_message['opcode'].capitalize()} data differs " +
                "between reference and implementation-under-test.\n" +
                "Reference message:\n" +
                pprint.pformat(reference_message["data"]) +
                "Implementation-under-test message:\n" +
                pprint.pformat(implementation_message["data"]))

        # All checks passed
        return True, ""

    def _store_smallest(self, values):
        """ Store the smallest value in magnitude to ``self._data_smallest``

        When considering complex values, the real and imaginary axes will be
        considered separately and the value returned can update only one axis
        if a smaller value has been found on that axis only.

        Args:
            values (list): A list of integers, floating point numbers or
                complex numbers from which the smallest value is to be found
                from. The list must be of all the same type and as the same
                type as ``current_smallest`` if that is not set to ``None``.
        """
        if "_data_smallest" not in dir(self):
            self._data_smallest = None

        if self._complex:
            real_values = [0] * len(values)
            imaginary_values = [0] * len(values)
            for index, value in enumerate(values):
                real_values[index] = abs(value.real)
                imaginary_values[index] = abs(value.imag)

            if self._data_smallest is None:
                self._data_smallest = complex(min(real_values),
                                              min(imaginary_values))
            else:
                self._data_smallest = complex(
                    min(self._data_smallest.real, real_values),
                    min(self._data_smallest.imag, imaginary_values))

        else:
            if self._data_smallest is None:
                self._data_smallest = abs(min(values, key=abs))
            else:
                self._data_smallest = min(self._data_smallest,
                                          abs(min(values, key=abs)))

    def _store_largest(self, values):
        """ Store the largest value in magnitude to ``self._data_largest``

        When considering complex values, the real and imaginary axes will be
        considered separately and the value returned can update only one axis
        if a smaller value has been found on that axis only.

        Args:
            values (list): A list of integers, floating point numbers or
                complex numbers from which the largest value is to be found
                from. The list must be of all the same type and as the same
                type as ``current_largest`` if that is not set to ``None``.
        """
        if "_data_largest" not in dir(self):
            self._data_largest = None

        if isinstance(values[0], complex):
            real_values = [0] * len(values)
            imaginary_values = [0] * len(values)
            for index, value in enumerate(values):
                real_values[index] = abs(value.real)
                imaginary_values[index] = abs(value.imag)

            if self._data_largest is None:
                self._data_largest = complex(max(real_values),
                                             max(imaginary_values))
            else:
                self._data_largest = complex(
                    max(self._data_largest.real, real_values),
                    max(self._data_largest.imag, imaginary_values))

        else:
            if self._data_largest is None:
                self._data_largest = abs(max(values, key=abs))
            else:
                self._data_largest = max()(self._data_largest,
                                           abs(max(values, key=abs)))

    def __repr__(self):
        """ Official string representation of object
        """
        return (f"ocpi_testing.Statistical(complex_={self._complex}, " +
                f"sample_data_type={self._sample_data_type})")

    def __str__(self):
        """ Informal string representation of object
        """
        return self.__repr__()
