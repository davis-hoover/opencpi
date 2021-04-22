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

    def verify(self, test_id, input_file_paths, test_output_file_paths):
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
            test_output_file_paths (list): List of file paths for the output
                from each output port of the implementation-under-test. The
                order of output ports order should match the order output port
                values are given by the implementation's ``process_messages()``
                function.

        Returns:
            Boolean to indicate if the unit test passed (True) or failed
                (False).
        """
        test_case, test_subcase = id_to_case(test_id)
        # Only record first comparison method as should only be one per verify
        # script
        self._test_log.record_comparison_method(
            test_case, test_subcase, type(self.comparison[0]).__name__.lower(),
            self.comparison[0].variable_summary())

        result, message = self.verify_without_save(input_file_paths,
                                                   test_output_file_paths)

        # No runtime variables has the worker under test so use the output data
        # file name
        case_worker_port = pathlib.Path(
            test_output_file_paths[0]).stem.split(".")
        # Extract the worker and port number - indexing from the end as the
        # case name could be set by a variable and so risk this could change
        port = case_worker_port[-1]
        worker = f"{case_worker_port[-3]}.{case_worker_port[-2]}"

        if result is True:
            self.test_passed(worker, port, test_case, test_subcase)
            return True
        else:
            self.test_failed(worker, port, test_case, test_subcase, message)
            return False

    def verify_without_save(self, input_file_paths, test_output_file_paths):
        """ Determine if unit test passes

        Check if the implementation-under-test's output matches that of the
        output of the reference implementation, when given the same input data.

        Does not save test result to test log or print user output.

        Args:
            input_file_paths (list): List of file paths for each of the input
                ports. The order of input ports in this list should match the
                expected input order of arguments for the implementation's
                functions.
            test_output_file_paths (list): List of file paths for the output
                from each output port of the implementation-under-test. The
                order of output ports order should match the order output port
                values are given by the implementation's ``process_messages()``
                function.

        Returns:
            Boolean to indicate if the unit test passed (True) or failed
                (False). And string which is the failure reason, which will be
                an empty string if test passes.
        """
        if self._port_types_set is False:
            raise RuntimeError("set_port_types() must be called and port " +
                               "protocol types set before verify() is called.")

        # Get input test data
        # While for single input it would be more efficient to only read one
        # message at a time and pass to the implementation to get one output at
        # a time; in the case of multiple ports this cannot be done - to allow
        # the same code to be used in both cases the multiple port case is used
        # for the single port case with a loss of efficiency.
        test_input_data = []
        for data_path, protocol in zip(input_file_paths,
                                       self._input_port_protocols):
            with ocpi_protocols.ParseMessagesFile(data_path, protocol) as \
                    data_file:
                test_input_data.append(data_file.get_all_messages())

        reference_output = self._generate_reference_output(*test_input_data)

        # Save the result of applying the Python reference implementation to
        # the input data to file.
        for port_name, port_protocol, port_data, output_path in zip(
                self._reference_implementation.output_ports,
                self._output_port_protocols,
                reference_output,
                test_output_file_paths):
            save_path = pathlib.Path(output_path).with_suffix(".reference")
            if port_name not in str(save_path):
                raise ValueError("Reference output save path of " +
                                 f"{str(save_path)} does not include port " +
                                 f"{port_name}. No way to identify output " +
                                 "for each port. Ensure " +
                                 "test_output_file_paths are in same order " +
                                 "as output_ports of implementation.")
            with ocpi_protocols.WriteMessagesFile(
                    save_path, port_protocol) as output_file:
                output_file.write_dict_messages(port_data)

        # If reading the implementation-under-test's output from file is
        # failing, is likely when the implementation-under-test ran it did not
        # write to file correctly. This will be because the data the
        # implementation-under-test returned during its test run was not
        # correctly formatted. Therefore, the test must fail.
        try:
            test_implementation_output = self._import_saved_messages(
                test_output_file_paths, self._output_port_protocols)
        except struct.error:
            return False, (
                "Cannot import implementation-under-test messages from " +
                "file. Likely badly formatted data outputted by " +
                "implementation-under-test and so badly formatted data " +
                "written to file during test run.")

        # For each output port run the comparison test
        for index, (comparison, reference, implementation) in enumerate(
                zip(self.comparison, reference_output,
                    test_implementation_output)):
            test_result, test_message = comparison.same(reference,
                                                        implementation)
            if test_result is False:
                return False, f"For port {index}; {test_message}"

        # All comparison checks pass
        return True, ""

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

    def _generate_reference_output(self, *inputs):
        """ Generate the reference output to validate test data against

        The reference output is generated by passing the input to the reference
        implementation.

        Args:
            *inputs (lists): An input argument should be given for each input
                port. All inputs must be a list of messages. All messages are
                dictionaries which must have the keys "opcode" and "data".

        Returns:
            Tuple of the output messages. The tuple length will match the
                number output ports. Each element of the tuple will contain a
                list of the output messages.
        """
        self._reference_implementation.reset()
        return self._reference_implementation.process_messages(*inputs)

    def _import_saved_messages(self, import_files, file_protocols):
        """ Read in messages from multiple files

        Args:
            import_files (list): Each of the file to be read in.
            file_protocols (list): List of the names of the protocols used for
                each of the import files.

        Returns:
            Tuple of all the imported message files, the order of elements in
                tuple will match that of ``import_files``.
        """
        imported_data = []
        for file_path, protocol in zip(import_files, file_protocols):
            with ocpi_protocols.ParseMessagesFile(file_path, protocol) as \
                    import_file:
                imported_data.append(import_file.get_all_messages())

        return tuple(imported_data)

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
