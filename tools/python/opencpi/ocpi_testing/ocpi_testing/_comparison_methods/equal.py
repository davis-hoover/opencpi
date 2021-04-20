#!/usr/bin/env python3

# Checker for equal reference and implementation data
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


import pprint

from .base_comparison import BasicComparison


class Equal(BasicComparison):
    """ Check sample data samples are exactly equal
    """

    def variable_summary(self):
        """ Returns summary of the variables that control the comparison method

        Cannot rely on the values being fixed for all tests since may need to
        be changed depending on the component-under-tests performance.

        Returns:
            Dictionary which is the variable names as keys and their respective
                values as the items. Includes all variables that control the
                comparison method.
        """
        return {}

    def same(self, reference, implementation):
        """ Checks if two output data sets are considered the same

        In this case same is where all data of all messages is exactly equal.

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
            for index, (reference_value, implementation_value) in enumerate(
                    zip(reference["data"], implementation["data"])):
                if reference_value != implementation_value:
                    display_from = max(0, index - 5)
                    display_to = min(len(reference["data"]),
                                     len(implementation["data"]),
                                     index + 5)
                    return False, (
                        f"Sample data differs at sample {index} (zero " +
                        "indexed) between reference and implementation-" +
                        "under-test.\n" +
                        f"Reference samples {display_from} to {display_to} " +
                        "(zero indexed):\n" +
                        f"  {reference['data'][display_from:display_to]}\n" +
                        f"Implementation-under-test samples {display_from} " +
                        f"to {display_to} (zero indexed):\n" +
                        "  " +
                        f"{implementation['data'][display_from:display_to]}")

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

    def __repr__(self):
        """ Official string representation of object
        """
        return (f"ocpi_testing.Equal(complex_={self._complex}, " +
                f"sample_data_type={self._sample_data_type})")

    def __str__(self):
        """ Informal string representation of object
        """
        return self.__repr__()
