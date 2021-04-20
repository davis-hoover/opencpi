#!/usr/bin/env python3

# Class for all protocol generator types to inherit from
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
import decimal
import pathlib
import random

import opencpi.ocpi_protocols as ocpi_protocols

from opencpi.ocpi_testing.ocpi_testing._test_log import TestLog
from opencpi.ocpi_testing.ocpi_testing._terminal_print_formatter import print_warning


DECIMAL_PRECISION = 50

# Some maximum values need more precision than given by a standard float; in
# these cases a decimal is used.
decimal.getcontext().prec = DECIMAL_PRECISION


class GeneratorDefaults:
    # This class houses all the default values used for the different
    # generator types. The structure is designed for importing and documenting
    # in an easier way.

    decimal.getcontext().prec = DECIMAL_PRECISION

    # The : after the # of comments here ensures the comments are imported into
    # the build documentation.

    #: For tests that need random sample data but not testing full scale sample
    #: data (i.e. not an all maximum the factor for the full range of the
    #: sample data type to limit the random samples values to).
    LIMITED_SCALE_FACTOR = 0.8

    #: Number of samples in sample messages when the length of the sample
    #: message is not under test.
    SAMPLE_DATA_LENGTH = 1024

    #: Mean of the Gaussian probability distribution function of the random
    #: number generator used to set the number of sinusoidal waves that are
    #: combined in a sample message for typical test case.
    TYPICAL_NUMBER_OF_WAVES_MODAL = 3.5

    #: Width of the Gaussian probability distribution function of the random
    #: number generator used to set the number of sinusoidal waves that are
    #: combined in a sample message for typical test case.
    TYPICAL_NUMBER_OF_WAVES_DISTRIBUTION_WIDTH = 1.5

    #: Minimum number of sinusoidal waves that are combined in a sample message
    #: for typical test case.
    TYPICAL_NUMBER_OF_WAVES_MIN = 1

    #: Maximum number of sinusoidal waves that are combined in a sample message
    #: for typical test case.
    TYPICAL_NUMBER_OF_WAVES_MAX = 5

    #: Mean of the probability distribution used as the random number generator
    #: to set the frequency of the sinusoidal waves that are combined in a
    #: sample message for typical test case.
    TYPICAL_FREQUENCY_MEAN = 0.05

    #: Width of the probability distribution used as the random number
    #: generator to set the frequency of the sinusoidal waves that are combined
    #: in a sample message for typical test case.
    TYPICAL_FREQUENCY_DISTRIBUTION_WIDTH = 0.01

    #: Maximum frequency of the sinusoidal waves that are combined in a sample
    #: message for typical test case.
    TYPICAL_FREQUENCY_MIN = 0.02

    #: Minimum frequency of the sinusoidal waves that are combined in a sample
    #: message for typical test case.
    TYPICAL_FREQUENCY_MAX = 0.2

    #: Range that is used for when values are described as "near" in sample
    #: subcases.
    SAMPLE_NEAR_RANGE = 5

    #: Number of samples in a sample message for the message size test case and
    #: shortest test subcase.
    MESSAGE_SIZE_SHORTEST = 1

    #: Number of sample messages used in message size test cases.
    MESSAGE_SIZE_NUMBER_OF_MESSAGES = 5

    #: Maximum number of messages when used for the message size test case and
    #: different sizes test subcase.
    MESSAGE_SIZE_MAX_NUMBER_OF_MESSAGES = 8

    #: Minimum value the time field allows.
    TIME_MIN = 0

    #: Maximum value the time field allows.
    TIME_MAX = decimal.Decimal(2**32) - decimal.Decimal(2**-40)

    #: Minimum value the sample interval field allows.
    SAMPLE_INTERVAL_MIN = 0

    #: Maximum value the sample interval field allows.
    SAMPLE_INTERVAL_MAX = decimal.Decimal(2**32) - decimal.Decimal(2**-40)

    #: Maximum value the ID field of a meta-data message allows.
    METADATA_ID_MAX = (2**32) - 1

    #: Maximum value the value field of a meta-data message allows.
    METADATA_VALUE_MAX = (2**64) - 1

    #: Mean of the Gaussian probability distribution function of the random
    #: number generator used to set the number of messages that are included in
    #: the input data for a soak test case and all opcode test subcase.
    SOAK_ALL_OPCODE_AVERAGE_NUMBER_OF_MESSAGES = 4.2

    #: Width of the Gaussian probability distribution function of the random
    #: number generator used to set the number of messages that are included in
    #: the input data for a soak test case and all opcode test subcase.
    SOAK_ALL_OPCODE_STANDARD_DEVIATION_NUMBER_OF_MESSAGES = 1.4


class BaseGenerator():
    """ Class for all protocol generator to inherit from
    """

    def __init__(self, test_log_file_path=""):
        """ Initialise base generator class

        Defines the default values for the variables that control the values
        and size of messages that are generated.

        Args:
            test_log_file_path (string, optional): Use to override the default
                test log file path - will attempt to store test logs in the
                .comp directory. If the directory cannot be found, no test log
                will be saved. If a test log is found at either the default or
                set file path, will over-write any existing entries. If no test
                log is required in this case, set to None.

        Returns:
            An initialised BaseGenerator instance.
        """
        # Some maximum values need more precision than given by a standard
        # float; in these cases a decimal is used.
        decimal.getcontext().prec = DECIMAL_PRECISION

        # Set variables as local as may be modified when set in the specific
        # generator. Keep the same variable names to ensure documentation
        # matches.
        self.LIMITED_SCALE_FACTOR = GeneratorDefaults.LIMITED_SCALE_FACTOR
        self.SAMPLE_DATA_LENGTH = GeneratorDefaults.SAMPLE_DATA_LENGTH
        self.TYPICAL_NUMBER_OF_WAVES_MODAL = \
            GeneratorDefaults.TYPICAL_NUMBER_OF_WAVES_MODAL
        self.TYPICAL_NUMBER_OF_WAVES_DISTRIBUTION_WIDTH = \
            GeneratorDefaults.TYPICAL_NUMBER_OF_WAVES_DISTRIBUTION_WIDTH
        self.TYPICAL_NUMBER_OF_WAVES_MIN = \
            GeneratorDefaults.TYPICAL_NUMBER_OF_WAVES_MIN
        self.TYPICAL_NUMBER_OF_WAVES_MAX = \
            GeneratorDefaults.TYPICAL_NUMBER_OF_WAVES_MAX
        self.TYPICAL_FREQUENCY_MEAN = GeneratorDefaults.TYPICAL_FREQUENCY_MEAN
        self.TYPICAL_FREQUENCY_DISTRIBUTION_WIDTH = \
            GeneratorDefaults.TYPICAL_FREQUENCY_DISTRIBUTION_WIDTH
        self.TYPICAL_FREQUENCY_MIN = GeneratorDefaults.TYPICAL_FREQUENCY_MIN
        self.TYPICAL_FREQUENCY_MAX = GeneratorDefaults.TYPICAL_FREQUENCY_MAX
        self.SAMPLE_NEAR_RANGE = GeneratorDefaults.SAMPLE_NEAR_RANGE
        self.MESSAGE_SIZE_SHORTEST = GeneratorDefaults.MESSAGE_SIZE_SHORTEST
        self.MESSAGE_SIZE_NUMBER_OF_MESSAGES = \
            GeneratorDefaults.MESSAGE_SIZE_NUMBER_OF_MESSAGES
        self.MESSAGE_SIZE_MAX_NUMBER_OF_MESSAGES = \
            GeneratorDefaults.MESSAGE_SIZE_MAX_NUMBER_OF_MESSAGES
        self.TIME_MIN = GeneratorDefaults.TIME_MIN
        self.TIME_MAX = GeneratorDefaults.TIME_MAX
        self.SAMPLE_INTERVAL_MIN = GeneratorDefaults.SAMPLE_INTERVAL_MIN
        self.SAMPLE_INTERVAL_MAX = GeneratorDefaults.SAMPLE_INTERVAL_MAX
        self.METADATA_ID_MAX = GeneratorDefaults.METADATA_ID_MAX
        self.METADATA_VALUE_MAX = GeneratorDefaults.METADATA_VALUE_MAX
        self.SOAK_ALL_OPCODE_AVERAGE_NUMBER_OF_MESSAGES = \
            GeneratorDefaults.SOAK_ALL_OPCODE_AVERAGE_NUMBER_OF_MESSAGES
        self.SOAK_ALL_OPCODE_STANDARD_DEVIATION_NUMBER_OF_MESSAGES = \
            GeneratorDefaults.SOAK_ALL_OPCODE_STANDARD_DEVIATION_NUMBER_OF_MESSAGES

        # Define all possible cases, and link to target method when that case
        # is to have messages generated for it. Avoids used of getattr() so
        # limits which methods of the class can be called.
        self.CASES = {
            "typical": self.typical,
            "property": self.property,
            "property_change": self.property,
            "sample": self.sample,
            "sample_other_port": self.sample_other_port,
            "input_stressing": self.input_stressing,
            "input_stressing_other_port": self.input_stressing,
            "message_size": self.message_size,
            "time": self.time,
            "time_other_port": self.time_other_port,
            "sample_interval": self.sample_interval,
            "sample_interval_other_port": self.sample_interval_other_port,
            "flush": self.flush,
            "flush_other_port": self.flush_other_port,
            "discontinuity": self.discontinuity,
            "discontinuity_other_port": self.discontinuity_other_port,
            "metadata": self.metadata,
            "metadata_other_port": self.metadata_other_port,
            "soak": self.soak,
            "custom": self.custom}

        # Set up, where needed, the test log handler
        if test_log_file_path == "":
            search_directory = pathlib.Path.cwd()
            while search_directory.suffix != ".test" and \
                    not search_directory.samefile("/"):
                search_directory = search_directory.parent
            if search_directory.suffix == ".test":
                self._test_log = TestLog(
                    search_directory.with_suffix(".comp").joinpath(
                        "test_log.json"))
            else:
                print_warning("Suitable test log directory not found.")
                self._test_log = TestLog(None)
        else:
            self._test_log = TestLog(test_log_file_path)
        if self._test_log.path is None:
            print_warning("Results are not being written to a test log.")
        else:
            print("Test log being saved at:")
            print(f"  {self._test_log.path}")

    def generate(self, seed, case, subcase, test_case_number,
                 test_subcase_number="00"):
        """ Generate the message set for this test case

        Args:
            seed (int): Value to seed random number generation with, so
                repeated runs with the same seed will give the same outputs.
            case (string): Name of the test case messages are to be generated
                for.
            subcase (sting): Name of the test subcase messages are to be
                generated for.
            test_case_number (int): Number indexing the test case.
            test_subcase_number (int, optional): Number indexing the test
                subcase.

        Returns:
            List of messages for the test case requested.
        """
        # Find relevant variables that can be set - these are all upper case
        # and start with the name of the subcase they relate to
        generator_variables = {}
        for attribute in dir(self):
            if (attribute.isupper() and
                    not callable(getattr(self, attribute)) and
                    attribute.startswith(case.upper())):
                generator_variables[attribute] = getattr(self, attribute)
                if isinstance(generator_variables[attribute], decimal.Decimal):
                    generator_variables[attribute] = str(
                        generator_variables[attribute])
        generator_variables["subcase"] = subcase
        self._test_log.record_generator(test_case_number, test_subcase_number,
                                        case, generator_variables)

        return self.CASES[case](seed, subcase)

    @abc.abstractmethod
    def typical(self, seed, subcase):
        """ Generate a sample message with typical data inputs

        Typical data inputs could often be a sinusoidal wave, or superposition
        of wave.

        Usually called via ``self.generate()``.

        Must be implemented by inheriting class.

        Args:
            seed (int): The seed value to use for random number generation.
            subcase (str): Name of the subcase messages are to be generated
                for.

        Returns:
            Messages for the typical case and the stated subcase.
        """
        raise NotImplementedError(
            "typical() must be implemented by child class")

    def property(self, seed, subcase):
        """ Generate sample message to allow property value testing

        Generates random data for the input port.

        Usually called via ``self.generate()``.

        Args:
            seed (int): The seed value to use for random number generation.
            subcase (str): Name of the subcase messages are to be generated
                for.

        Returns:
            Messages for the property testing.
        """
        random.seed(seed)
        return [{"opcode": "sample", "data": self._get_sample_values()}]

    @abc.abstractmethod
    def sample(self, seed, subcase):
        """ Messages when testing a port's handling of sample messages

        Must be implemented by inheriting class.

        Usually called via ``self.generate()``.

        Args:
            seed (int): The seed value to use for random number generation.
            subcase (str): Name of the subcase messages are to be generated
                for.

        Returns:
            Messages for the typical case and the stated subcase.
        """
        raise NotImplementedError(
            "sample() must be implemented by child class")

    @abc.abstractmethod
    def sample_other_port(self, seed, subcase):
        """ Messages when testing another port's handling of sample messages

        Must be implemented by inheriting class.

        Usually called via ``self.generate()``.

        Args:
            seed (int): The seed value to use for random number generation.
            subcase (str): Name of the subcase messages are to be generated
                for.

        Returns:
            Messages for the typical case and the stated subcase.
        """
        raise NotImplementedError(
            "sample_other_port() must be implemented by child class")

    def input_stressing(self, seed, subcase):
        """ Messages when testing a port's handling of input stressing

        Generates random data for the input port.

        Usually called via ``self.generate()``.

        Args:
            seed (int): The seed value to use for random number generation.
            subcase (str): Name of the subcase messages are to be generated
                for.

        Returns:
            Messages for the input port stress testing.
        """
        random.seed(seed)
        return [{"opcode": "sample", "data": self._get_sample_values()}]

    def message_size(self, seed, subcase):
        """ Messages when testing a port's handling of different message sizes

        Usually called via ``self.generate()``.

        Args:
            seed (int): The seed value to use for random number generation.
            subcase (str): Name of the subcase messages are to be generated
                for.

        Returns:
            Messages for the message size testing.
        """
        random.seed(seed)
        if subcase == "shortest":
            return [{"opcode": "sample",
                     "data": self._get_sample_values(
                         self.MESSAGE_SIZE_SHORTEST)}
                    for _ in range(self.MESSAGE_SIZE_NUMBER_OF_MESSAGES)]

        elif subcase == "longest":
            return [{"opcode": "sample",
                     "data": self._get_sample_values(self.MESSAGE_SIZE_LONGEST)
                     } for _ in range(self.MESSAGE_SIZE_NUMBER_OF_MESSAGES)]

        elif subcase == "different_sizes":
            # This subcase is intended for multiple input port components. To
            # test each port having the same amount of total data provided, but
            # over a different number and length of messages rather than all
            # messages to all ports being the same size

            total_number_of_messages = random.randint(
                2, self.MESSAGE_SIZE_MAX_NUMBER_OF_MESSAGES)

            # Assign the message lengths. The total length of all messages will
            # be self.SAMPLE_DATA_LENGTH. All messages apart from the last
            # message are randomly given a length between one and the total
            # message length (self.SAMPLE_DATA_LENGTH) minus the number of
            # messages remaining to be given a length. This is so that if the
            # largest number in the possible range is selected all remaining
            # messages will have a length on one.
            message_lengths = [0] * total_number_of_messages
            for index in range(total_number_of_messages - 1):
                remaining_messages = total_number_of_messages - index - 1
                maximum_message_length = (self.SAMPLE_DATA_LENGTH
                                          - sum(message_lengths)
                                          - remaining_messages)
                message_lengths[index] = random.randint(1,
                                                        maximum_message_length)

            # The last message has a length to ensure the total message length
            # equals self.SAMPLE_DATA_LENGTH
            message_lengths[-1] = (self.SAMPLE_DATA_LENGTH
                                   - sum(message_lengths[0:-1]))

            messages = []
            for message_length in message_lengths:
                messages.append(
                    {"opcode": "sample",
                     "data": self._get_sample_values(message_length)})

            return messages

        else:
            raise ValueError(
                f"Unexpected subcase of {subcase} for message_size()")

    def time(self, seed, subcase):
        """ Messages when testing a port's handling of time messages

        Usually called via ``self.generate()``.

        Args:
            seed (int): The seed value to use for random number generation.
            subcase (str): Name of the subcase messages are to be generated
                for.

        Returns:
            Messages for the requested time test subcase.
        """
        random.seed(seed)
        if subcase == "zero":
            return [{"opcode": "sample", "data": self._get_sample_values()},
                    {"opcode": "time", "data": 0.0},
                    {"opcode": "sample", "data": self._get_sample_values()}]

        elif subcase == "positive":
            return [{"opcode": "sample", "data": self._get_sample_values()},
                    {"opcode": "time",
                     "data": random.uniform(0.0, float(self.TIME_MAX))},
                    {"opcode": "sample", "data": self._get_sample_values()}]

        elif subcase == "maximum":
            return [{"opcode": "sample", "data": self._get_sample_values()},
                    {"opcode": "time", "data": self.TIME_MAX},
                    {"opcode": "sample", "data": self._get_sample_values()}]

        elif subcase == "consecutive":
            return [{"opcode": "sample", "data": self._get_sample_values()},
                    {"opcode": "time",
                     "data": random.uniform(0.0, float(self.TIME_MAX))},
                    {"opcode": "time",
                     "data": random.uniform(0.0, float(self.TIME_MAX))},
                    {"opcode": "sample", "data": self._get_sample_values()}]

        else:
            raise ValueError(f"Unexpected subcase of {subcase} for time()")

    def time_other_port(self, seed, subcase):
        """ Messages when testing another port's handling of time messages

        Usually called via ``self.generate()``.

        Args:
            seed (int): The seed value to use for random number generation.
            subcase (str): Name of the subcase messages are to be generated
                for.

        Returns:
            Messages for an input port while another input port is under time
                opcode testing.
        """
        random.seed(seed)
        if subcase == "zero":
            return [{"opcode": "sample", "data": self._get_sample_values()},
                    {"opcode": "sample", "data": self._get_sample_values()}]

        elif subcase == "positive":
            return [{"opcode": "sample", "data": self._get_sample_values()},
                    {"opcode": "sample", "data": self._get_sample_values()}]

        elif subcase == "maximum":
            return [{"opcode": "sample", "data": self._get_sample_values()},
                    {"opcode": "sample", "data": self._get_sample_values()}]

        elif subcase == "consecutive":
            return [{"opcode": "sample", "data": self._get_sample_values()},
                    {"opcode": "sample", "data": self._get_sample_values()}]

        else:
            raise ValueError(
                f"Unexpected subcase of {subcase} for time_other_port()")

    def sample_interval(self, seed, subcase):
        """ Messages when testing a port's handling of sample_interval messages

        Usually called via ``self.generate()``.

        Args:
            seed (int): The seed value to use for random number generation.
            subcase (str): Name of the subcase messages are to be generated
                for.

        Returns:
            Messages for the requested sample interval test subcase.
        """
        random.seed(seed)
        if subcase == "zero":
            return [{"opcode": "sample", "data": self._get_sample_values()},
                    {"opcode": "sample_interval", "data": 0.0},
                    {"opcode": "sample", "data": self._get_sample_values()}]

        elif subcase == "positive":
            return [{"opcode": "sample", "data": self._get_sample_values()},
                    {"opcode": "sample_interval",
                     "data": random.uniform(0.0,
                                            float(self.SAMPLE_INTERVAL_MAX))},
                    {"opcode": "sample", "data": self._get_sample_values()}]

        elif subcase == "maximum":
            return [{"opcode": "sample", "data": self._get_sample_values()},
                    {"opcode": "sample_interval",
                     "data": self.SAMPLE_INTERVAL_MAX},
                    {"opcode": "sample", "data": self._get_sample_values()}]

        elif subcase == "consecutive":
            return [{"opcode": "sample", "data": self._get_sample_values()},
                    {"opcode": "sample_interval",
                     "data": random.uniform(0.0,
                                            float(self.SAMPLE_INTERVAL_MAX))},
                    {"opcode": "sample_interval",
                     "data": random.uniform(0.0,
                                            float(self.SAMPLE_INTERVAL_MAX))},
                    {"opcode": "sample", "data": self._get_sample_values()}]

        else:
            raise ValueError(
                f"Unexpected subcase of {subcase} for sample_interval()")

    def sample_interval_other_port(self, seed, subcase):
        """ Messages when testing another port's handling of sample interval

        Usually called via ``self.generate()``.

        Args:
            seed (int): The seed value to use for random number generation.
            subcase (str): Name of the subcase messages are to be generated
                for.

        Returns:
            Messages for an input port while another input port is under sample
                interval opcode testing.
        """
        random.seed(seed)
        if subcase == "zero":
            return [{"opcode": "sample", "data": self._get_sample_values()},
                    {"opcode": "sample", "data": self._get_sample_values()}]

        elif subcase == "positive":
            return [{"opcode": "sample", "data": self._get_sample_values()},
                    {"opcode": "sample", "data": self._get_sample_values()}]

        elif subcase == "maximum":
            return [{"opcode": "sample", "data": self._get_sample_values()},
                    {"opcode": "sample", "data": self._get_sample_values()}]

        elif subcase == "consecutive":
            return [{"opcode": "sample", "data": self._get_sample_values()},
                    {"opcode": "sample", "data": self._get_sample_values()}]

        else:
            raise ValueError(
                f"Unexpected subcase of {subcase} for " +
                "sample_interval_other_port()")

    def flush(self, seed, subcase):
        """ Messages when testing a port's handling of flush messages

        Usually called via ``self.generate()``.

        Args:
            seed (int): The seed value to use for random number generation.
            subcase (str): Name of the subcase messages are to be generated
                for.

        Returns:
            Messages for the requested flush test subcase.
        """
        random.seed(seed)
        if subcase == "single":
            return [{"opcode": "sample", "data": self._get_sample_values()},
                    {"opcode": "flush", "data": None},
                    {"opcode": "sample", "data": self._get_sample_values()}]

        elif subcase == "consecutive":
            return [{"opcode": "sample", "data": self._get_sample_values()},
                    {"opcode": "flush", "data": None},
                    {"opcode": "flush", "data": None},
                    {"opcode": "sample", "data": self._get_sample_values()}]

        else:
            raise ValueError(f"Unexpected subcase of {subcase} for flush()")

    def flush_other_port(self, seed, subcase):
        """ Messages when testing another port's handling of flush messages

        Usually called via ``self.generate()``.

        Args:
            seed (int): The seed value to use for random number generation.
            subcase (str): Name of the subcase messages are to be generated
                for.

        Returns:
            Messages for an input port while another input port is under flush
                opcode testing.
        """
        random.seed(seed)
        if subcase == "single":
            return [{"opcode": "sample", "data": self._get_sample_values()},
                    {"opcode": "sample", "data": self._get_sample_values()}]

        elif subcase == "consecutive":
            return [{"opcode": "sample", "data": self._get_sample_values()},
                    {"opcode": "sample", "data": self._get_sample_values()}]

        else:
            raise ValueError(
                f"Unexpected subcase of {subcase} for flush_other_port()")

    def discontinuity(self, seed, subcase):
        """ Messages when testing a port's handling of discontinuity messages

        Usually called via ``self.generate()``.

        Args:
            seed (int): The seed value to use for random number generation.
            subcase (str): Name of the subcase messages are to be generated
                for.

        Returns:
            Messages for the requested discontinuous test subcase.
        """
        random.seed(seed)
        if subcase == "single":
            return [{"opcode": "sample", "data": self._get_sample_values()},
                    {"opcode": "discontinuity", "data": None},
                    {"opcode": "sample", "data": self._get_sample_values()}]

        elif subcase == "consecutive":
            return [{"opcode": "sample", "data": self._get_sample_values()},
                    {"opcode": "discontinuity", "data": None},
                    {"opcode": "discontinuity", "data": None},
                    {"opcode": "sample", "data": self._get_sample_values()}]

        else:
            raise ValueError(
                f"Unexpected subcase of {subcase} for discontinuity()")

    def discontinuity_other_port(self, seed, subcase):
        """ Messages when testing another port's handling of discontinuity

        Usually called via ``self.generate()``.

        Args:
            seed (int): The seed value to use for random number generation.
            subcase (str): Name of the subcase messages are to be generated
                for.

        Returns:
            Messages for an input port while another input port is under
                discontinuity opcode testing.
        """
        random.seed(seed)
        if subcase == "single":
            return [{"opcode": "sample", "data": self._get_sample_values()},
                    {"opcode": "sample", "data": self._get_sample_values()}]

        elif subcase == "consecutive":
            return [{"opcode": "sample", "data": self._get_sample_values()},
                    {"opcode": "sample", "data": self._get_sample_values()}]

        else:
            raise ValueError(
                f"Unexpected subcase of {subcase} for " +
                "discontinuity_other_port()")

    def metadata(self, seed, subcase):
        """ Messages when testing a port's handling of sample metadata

        Usually called via ``self.generate()``.

        Args:
            seed (int): The seed value to use for random number generation.
            subcase (str): Name of the subcase messages are to be generated
                for.

        Returns:
            Messages for the requested sample metadata test subcase.
        """
        random.seed(seed)
        if subcase == "zero":
            return [{"opcode": "sample", "data": self._get_sample_values()},
                    {"opcode": "metadata", "data": {"id": 0,
                                                    "value": 0}},
                    {"opcode": "sample", "data": self._get_sample_values()}]

        elif subcase == "positive":
            return [{"opcode": "sample", "data": self._get_sample_values()},
                    {"opcode": "metadata",
                     "data": {
                         "id": random.randint(1, self.METADATA_ID_MAX),
                         "value": random.randint(1, self.METADATA_VALUE_MAX)}},
                    {"opcode": "sample", "data": self._get_sample_values()}]

        elif subcase == "maximum":
            return [{"opcode": "sample", "data": self._get_sample_values()},
                    {"opcode": "metadata",
                     "data": {"id": self.METADATA_ID_MAX,
                              "value": self.METADATA_VALUE_MAX}},
                    {"opcode": "sample", "data": self._get_sample_values()}]

        elif subcase == "consecutive":
            return [{"opcode": "sample", "data": self._get_sample_values()},
                    {"opcode": "metadata",
                     "data": {
                         "id": random.randint(1, self.METADATA_ID_MAX),
                         "value": random.randint(1, self.METADATA_VALUE_MAX)}},
                    {"opcode": "metadata",
                     "data": {
                         "id": random.randint(1, self.METADATA_ID_MAX),
                         "value": random.randint(1, self.METADATA_VALUE_MAX)}},
                    {"opcode": "sample", "data": self._get_sample_values()}]

        else:
            raise ValueError(
                f"Unexpected subcase of {subcase} for metadata()")

    def metadata_other_port(self, seed, subcase):
        """ Messages when testing another port's handling of sample metadata

        Usually called via ``self.generate()``.

        Args:
            seed (int): The seed value to use for random number generation.
            subcase (str): Name of the subcase messages are to be generated
                for.

        Returns:
            Messages for an input port while another input port is under sample
                metadata opcode testing.
        """
        random.seed(seed)
        if subcase == "zero":
            return [{"opcode": "sample", "data": self._get_sample_values()},
                    {"opcode": "sample", "data": self._get_sample_values()}]

        elif subcase == "positive":
            return [{"opcode": "sample", "data": self._get_sample_values()},
                    {"opcode": "sample", "data": self._get_sample_values()}]

        elif subcase == "maximum":
            return [{"opcode": "sample", "data": self._get_sample_values()},
                    {"opcode": "sample", "data": self._get_sample_values()}]

        elif subcase == "consecutive":
            return [{"opcode": "sample", "data": self._get_sample_values()},
                    {"opcode": "sample", "data": self._get_sample_values()}]

        else:
            raise ValueError(
                f"Unexpected subcase of {subcase} for metadata_other_port()")

    def soak(self, seed, subcase):
        """ Generate messages for soak test cases

        Usually called via ``self.generate()``.

        Args:
            seed (int): The seed value to use for random number generation.
            subcase (str): Name of the subcase messages are to be generated
                for.

        Returns:
            Messages for the requested soak test subcase.
        """
        random.seed(seed)

        # Set the number and opcode of messages
        number_of_messages = round(random.gauss(
            self.SOAK_ALL_OPCODE_AVERAGE_NUMBER_OF_MESSAGES,
            self.SOAK_ALL_OPCODE_STANDARD_DEVIATION_NUMBER_OF_MESSAGES))
        if number_of_messages > 8:
            number_of_messages = 8
        elif number_of_messages < 1:
            number_of_messages = 1

        messages = []

        if subcase == "sample_only":
            message_lengths = [0] * number_of_messages

            # The total of all messages should be self.SAMPLE_DATA_LENGTH
            for index in range(number_of_messages - 1):
                remaining_messages = number_of_messages - index - 1
                # Set a maximum which ensures that all messages have at least
                # one data sample.
                maximum_message_length = (self.SAMPLE_DATA_LENGTH -
                                          sum(message_lengths) -
                                          remaining_messages)
                message_lengths[index] = random.randint(
                    1, maximum_message_length)
            # The final message will have a length to ensure that all sample
            # messages have a length which totals self.SAMPLE_DATA_LENGTH.
            message_lengths[-1] = self.SAMPLE_DATA_LENGTH - sum(
                message_lengths[0:-1])

            if message_lengths[-1] == 0:
                del message_lengths[-1]

            for length in message_lengths:
                messages.append({
                    "opcode": "sample",
                    "data": self._full_scale_random_sample_values(length)})

        elif subcase == "all_opcodes":
            sample_data_included = 0
            sample_message_size = self.SAMPLE_DATA_LENGTH // number_of_messages
            for opcode in random.choices(list(ocpi_protocols.OPCODES.keys()),
                                         k=number_of_messages):
                # As opcode keys are opcode names and values, if an int this
                # will be the value. In which case get the name.
                if isinstance(opcode, int):
                    opcode = ocpi_protocols.OPCODES[opcode]

                if opcode == "sample":
                    messages.append({
                        "opcode": "sample",
                        "data": self._full_scale_random_sample_values(
                            sample_message_size)})
                    sample_data_included = (sample_data_included +
                                            sample_message_size)
                elif opcode == "time":
                    messages.append({
                        "opcode": "time",
                        "data": random.uniform(self.TIME_MIN,
                                               float(self.TIME_MAX))})
                elif opcode == "sample_interval":
                    messages.append({
                        "opcode": "sample_interval",
                        "data": random.uniform(self.SAMPLE_INTERVAL_MIN,
                                               float(self.SAMPLE_INTERVAL_MAX))
                    })
                elif opcode == "flush":
                    messages.append({"opcode": "flush", "data": None})
                elif opcode == "discontinuity":
                    messages.append({"opcode": "discontinuity", "data": None})
                elif opcode == "metadata":
                    messages.append({
                        "opcode": "metadata",
                        "data": {
                            "id": random.randint(0, self.METADATA_ID_MAX),
                            "value": random.randint(
                                0, self.METADATA_VALUE_MAX)}})
                else:
                    raise ValueError(
                        f"Unexpected opcode of {opcode} for soak()")

            # Add a final sample message to ensure the total length of all
            # sample messages is self.SAMPLE_DATA_LENGTH. But don't add
            # a zero length message.
            if (self.SAMPLE_DATA_LENGTH - sample_data_included):
                messages.append({
                    "opcode": "sample",
                    "data": self._get_sample_values(self.SAMPLE_DATA_LENGTH -
                                                    sample_data_included)})

        else:
            raise ValueError(f"Unexpected subcase of {subcase} for soak()")

        return messages

    def custom(self, seed, subcase):
        """ Generate messages for sample custom test cases

        If custom test cases are to be included they must be defined separately
        and override this method.

        Usually called via ``self.generate()``.

        Args:
            seed (int): The seed value to use for random number generation.
            subcase (str): Name of the subcase messages are to be generated
                for.

        Returns:
            Messages for the requested sample metadata test subcase.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def _full_scale_random_sample_values(self, number_of_samples=None):
        """ Generate random sample numbers over the whole supported range

        This is to generate random values that would be valid in a sample
        message's data field. Full supported range here means from the maximum
        to minimum values the data type allows.

        This method must be defined in inheriting child classes for specific
        protocol types.

        Args:
            number_of_samples (int, optional): The number of random values to
                be generated. If not set will default to None, which means the
                number of samples defined by self.SAMPLE_DATA_LENGTH will be
                generated.

        Returns:
            List of the generated random values.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def _get_sample_values(self, number_of_samples=None):
        """ Generates sample values

        Generate random values that would be valid in a sample message's data
        field. Typically runs to 80% of the maximum sample values can be, not
        full scale as specific sample tests test at full scale values.

        This method must be defined in inheriting child classes for specific
        protocol types.

        Args:
            number_of_samples (int, optional): The number of random values to
                be generated. If not set will default to None, which means the
                number of samples defined by self.SAMPLE_DATA_LENGTH will be
                generated.

        Returns:
            List of the generated random values.
        """
        raise NotImplementedError
