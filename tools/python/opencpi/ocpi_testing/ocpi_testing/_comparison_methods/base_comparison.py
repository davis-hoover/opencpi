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


class BaseComparison:
    """ Comparison class other comparison methods inherit from
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
        self._complex = complex_
        self._sample_data_type = sample_data_type

    @abc.abstractmethod
    def variable_summary(self):
        """ Returns summary of the variables that control the comparison method

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
        """ Checks if two output data sets are considered the same

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


class BasicComparison(BaseComparison):
    """ Run check every comparison method should do
    """

    def correct_messages(self, reference, implementation):
        """ Check correct type (opcode) of messages and data length

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
