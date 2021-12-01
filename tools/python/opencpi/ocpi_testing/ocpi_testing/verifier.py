#!/usr/bin/env python3

# Verifier to check if component unit test has passed testing
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


import inspect
import pathlib
import struct

import opencpi.ocpi_protocols.ocpi_protocols as ocpi_protocols

from .id_to_case import id_to_case
from .implementation import Implementation as implementation_type
from ._comparison_methods import COMPARISON_METHODS
from ._comparison_methods.base_comparison import BaseComparison
from ._test_log import TestLog
from ._terminal_print_formatter import print_warning, print_fail


class Verifier:
    """ Verify output of components under unit test
    """

    def __init__(self, reference_implementation, test_log_file_path=""):
        """ Initialise verify checker

        Args:
            reference_implementation (class): An initialised Python
                implementation of the component functionality under test. It is
                strongly encouraged that this implementation inherits from
                ``ocpi_testing.Implementation``.
            test_log_file_path (string, optional): Use to override the default
                test log file path - will attempt to store test logs in the
                .comp directory. If the directory cannot be found, no test log
                will be saved. If a test log is found at either the default or
                set file path, will over-write any existing entries. If no test
                log is required in this case, set to None.

        Returns:
            Initialised verifier checker.
        """
        self._check_valid_reference_implementation(reference_implementation)
        self._reference_implementation = reference_implementation

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

        self._port_types_set = False

    def set_port_types(self, input_port_protocols, output_port_protocols,
                       comparisons):
        """ Set the input and output port types

        Set the input and output port types, and the type of comparison applied
        to each output port.

        Args:
            input_port_protocols (list): List of strings, where each string is
                the name of the input port's protocol. The order of input ports
                in this list should match the expected input order of arguments
                for the implementation's functions.
            output_port_protocols (list): List of strings, where each string is
                the name of the output port's protocol. The order of output
                ports order should match the order output port values are given
                by the implementation's ``process_messages()`` function.
            comparisons (list): Sets the type of comparison method for
                each port used to verify implementation-under-test's output
                matches the output of the reference implementation, for the
                same input data. Each element in the list can be set to a
                string of one of the provided comparison methods. Or an
                initialised class of the comparison can be passed.
        """
        if len(output_port_protocols) != len(comparisons):
            raise ValueError("output_port_protocols and comparisons must be "
                             + "lists of the same size. Length of "
                             + "output_port_protocols is "
                             + f"{len(output_port_protocols)}. Length of "
                             + f"comparisons is {len(comparisons)}.")
        if len(input_port_protocols) != len(
                self._reference_implementation.input_ports):
            raise ValueError(
                "Protocols not set for all input ports. " +
                f"{len(input_port_protocols)} input port protocols set " +
                "while reference implementation has " +
                f"{len(self._reference_implementation.input_ports)} input " +
                "ports")
        if len(output_port_protocols) != len(
                self._reference_implementation.output_ports):
            raise ValueError(
                "Protocols not set for all output ports. " +
                f"{len(output_port_protocols)} output port protocols set " +
                "while reference implementation has " +
                f"{len(self._reference_implementation.output_ports)} output " +
                "ports")

        self._input_port_protocols = input_port_protocols
        self._output_port_protocols = output_port_protocols

        # Set comparison method, by setting class that completes checks
        self.comparison = []
        for comparison, protocol in zip(comparisons, output_port_protocols):
            # If a string, use a built in comparison type of that name
            if isinstance(comparison, str):
                self.comparison.append(COMPARISON_METHODS[comparison](
                    ocpi_protocols.PROTOCOLS[protocol].complex,
                    ocpi_protocols.PROTOCOLS[protocol].sample_python_type))

            # Check if inherits from BaseComparison (to be a custom comparison)
            elif isinstance(comparison, BaseComparison):
                self.comparison.append(comparison)

            # Unsupported type
            else:
                raise ValueError(f"{comparison} (type: {type(comparison)}) "
                                 + "is not a valid comparison type in "
                                 + "comparisons argument")

        self._port_types_set = True

    def verify(self, test_id, input_file_paths, verify_output_file_path,
               port_select=None):
        """ Determine if unit test passes

        Check if the implementation-under-test's output matches that of the
        output of the reference implementation, when given the same input data.

        Will save the reference implementation's output to file. Will record
        the test result to the test log file.

        Args:
            test_id (str): ID / name of the test case that is being verified.
            input_file_paths (list): List of file paths for each of the input
                ports. The order of input ports in this list should match the
                expected input order of arguments for the implementation's
                functions.
            verify_output_file_path (str, list): File paths of the output to be
                checked is correct. Can be a list of one element, to maintain
                backwards compatibility.
            port_select (str, int, optional): For multiple output components
                this specifies which output port is to be verified, and only
                this output is verified - so each output port should be
                verified in turn. For single output port components this does
                not need to be set.

        Returns:
            Boolean to indicate if the unit test passed (True) or failed
                (False).
        """
        if self._port_types_set is False:
            raise RuntimeError("set_port_types() must be called and port " +
                               "protocol types set before verify() is called.")

        # To maintain backward compability this argument can be a list, however
        # if is a list then must be a list of one element
        if isinstance(verify_output_file_path, list):
            if len(verify_output_file_path) != 1:
                raise ValueError("verify_output_file_path can be a list for " +
                                 "backward compability only. When used as a " +
                                 "list must be a list of one element")
            verify_output_file_path = verify_output_file_path[0]

        if len(self._reference_implementation.output_ports) == 1:
            port_index = 0
        else:
            if port_select is None:
                raise ValueError("For multiple output components " +
                                 "verify_output must be set as either the " +
                                 "port number or name to be verified")
            if isinstance(port_select, int):
                # Less one as by the input argument definition port indexes are
                # counted from 1
                port_index = port_select - 1
            else:
                port_index = self._reference_implementation.output_ports.index(
                    port_select)

            if port_index >= len(self._reference_implementation.output_ports):
                raise ValueError(
                    f"Attempting to verify port {port_index} (from port " +
                    f"select value {port_select}) however there are only " +
                    f"{len(self._reference_implementation.output_ports)} " +
                    "output ports")

        implementation_file_path = pathlib.Path(verify_output_file_path)
        reference_file_path = pathlib.Path(
            verify_output_file_path).with_suffix(".reference")

        test_case, test_subcase = id_to_case(test_id)

        # No runtime variables has the worker under test so use the output data
        # file name, these values are used for test result reporting
        case_worker_port = reference_file_path.stem.split(".")
        # Extract the worker and port number - indexing from the end as the
        # case name could be set by a variable and so risk this could change
        port = case_worker_port[-1]
        worker = f"{case_worker_port[-3]}.{case_worker_port[-2]}"

        # To maintain compatibility with documentation generator, only one
        # comparison method can be recorded - so record first one
        self._test_log.record_comparison_method(
            test_case, test_subcase, type(self.comparison[0]).__name__.lower(),
            self.comparison[0].variable_summary())

        try:
            implementation_file_time = implementation_file_path.stat().st_mtime
        except FileNotFoundError as exception_:
            print("Test implementation file cannot be accessed. Check run " +
                  "stage of test have completed and generated an output.")
            raise exception_

        # There are three cases when the reference should be generated:
        #  1. No reference currently exists
        #  2. The implementation-under-test is newer, so the reference may be
        #     out-of-date / generated with a different input data set.
        #  3. Any of the file that control the tests have been updated more
        #     recently than a reference has been generated, which could include
        #     the Python reference implementation being updated.
        # Do as separate if / elif statements, as prevents stat() lookups on
        # reference output file when does not exit, and more readable than when
        # on if with "or" conditions.
        if not reference_file_path.is_file():
            self._generate_reference_output(
                input_file_paths, implementation_file_path.parent, test_id,
                worker)
        elif reference_file_path.stat().st_mtime < implementation_file_time:
            self._generate_reference_output(
                input_file_paths, implementation_file_path.parent, test_id,
                worker)
        elif any([test_directory_file.stat().st_mtime >
                  reference_file_path.stat().st_mtime for
                  test_directory_file in
                  reference_file_path.parent.parent.parent.glob("*.*")]):
            self._generate_reference_output(
                input_file_paths, implementation_file_path.parent, test_id,
                worker)
        reference_output = self._import_saved_messages(
            reference_file_path, self._output_port_protocols[port_index])

        try:
            implementation_output = self._import_saved_messages(
                implementation_file_path,
                self._output_port_protocols[port_index])
        except struct.error:
            self.test_failed(worker, port, test_case, test_subcase,
                             "Cannot import implementation-under-test " +
                             "messages from file. Likely badly formatted " +
                             "data outputted by implementation-under-test " +
                             "and so badly formatted data written to file " +
                             "during test run.")
            return False

        test_result, test_message = self.comparison[port_index].same(
            reference_output, implementation_output)

        if test_result is True:
            self.test_passed(worker, port, test_case, test_subcase)
            return True
        else:
            self.test_failed(worker, port, test_case,
                             test_subcase, test_message)
            return False

    def test_passed(self, worker, port, test_case, test_subcase):
        """ Report that test has passed

        Updates test log with passed result.

        Args:
            worker (str): The name of the worker that is being tested.
            port (str): The name of the port which output data is being
            verified.
            test_case (str): Test case.
            test_subcase (str): Test subcase, if there is none set to "".

        """
        self._test_log.record_pass(worker, port, test_case, test_subcase)

    def test_failed(self, worker, port, test_case, test_subcase,
                    failure_reason):
        """ Report that test has failed

        Updates test log with failure result and prints a test failure message
        to the terminal.

        Args:
            worker (str): The name of the worker that is being tested.
            port (str): The name of the port which output data is being
                verified.
            test_case (str): Test case.
            test_subcase (str): Test subcase, if there is none set to "".
            failure_reason (str): The reason the test failed to be printed as
                the test failure message.
        """
        test_name = test_case
        if test_subcase != "":
            test_name = f"{test_name}.{test_subcase}"

        print_fail(test_name, failure_reason)

        self._test_log.record_fail(worker, port, test_case, test_subcase)

    def _check_valid_reference_implementation(self, implementation):
        """ Check the reference implementation is suitable

        For a reference implementation to be suitable it must be either:
        1. A class which inherits from ``ocpi_testing.Implementation``. Or;
        2. A class which has methods ``reset()`` and ``process_messages()``.

        If any checks fail an exception will be raised.

        Args:
            implementation (class): The implementation being checked.
        """
        # If inherits from the implementation class in ocpi_testing, then will
        # meet the required format and have to define the needed methods.
        if isinstance(implementation, implementation_type):
            return

        if hasattr(implementation, "reset") is False:
            raise NotImplementedError("Reference implementation does not " +
                                      "have an attribute called \"reset\"")
        if callable(implementation.reset) is False:
            raise NotImplementedError("reset of reference implementation " +
                                      "is not callable")
        if hasattr(implementation, "process_messages") is False:
            raise NotImplementedError("Reference implementation does not " +
                                      "have an attribute called " +
                                      "\"process_messages\"")
        if callable(implementation.process_messages) is False:
            raise NotImplementedError("process_messages of reference " +
                                      "implementation is not callable")

    def _generate_reference_output(self, inputs, save_directory, test_id, worker):
        """ Generate and saves the reference output

        The reference output is generated by passing the input to the reference
        implementation.

        Args:
            inputs (lists): File path of the input for each input port.
            save_directory (str): Directory to save the reference output(s) to.
            test_id (str): Test ID, used for setting the file name the
                reference output is saved to.
            worker (str): Worker name, used for setting the file name the
                reference output is saved to.
        """
        input_data = []
        for input_, protocol in zip(inputs, self._input_port_protocols):
            input_data.append(self._import_saved_messages(input_, protocol))

        self._reference_implementation.reset()
        reference_output = self._reference_implementation.process_messages(
            *input_data)

        save_directory = pathlib.Path(save_directory)

        for port_name, port_protocol, port_data in zip(
                self._reference_implementation.output_ports,
                self._output_port_protocols,
                reference_output):
            save_path = save_directory.joinpath(
                f"{test_id}.{worker}.{port_name}.reference")
            with ocpi_protocols.WriteMessagesFile(
                    save_path, port_protocol) as output_file:
                output_file.write_dict_messages(port_data)

    def _import_saved_messages(self, file_path, protocol):
        """ Read in messages from a file

        Args:
            file_path (str): Path of the messages file to be read
            protocol (str): Names of the protocols used for reading in
                the file.

        Returns:
            List of all the messages in a file.
        """
        with ocpi_protocols.ParseMessagesFile(file_path, protocol) as \
                import_file:
            messages = import_file.get_all_messages()
        return messages

    def __repr__(self):
        """ Official string representation of object
        """
        return (
            f"<ocpi_testing.Verifier(reference_implementation=" +
            f"{type(self._reference_implementation).__name__}, comparison=" +
            f"{type(self.comparison).__name__}, test_log_file_path=" +
            f"{self._test_log.path})>")

    def __str__(self):
        """ Informal string representation of object
        """
        return self.__repr__()
