#!/usr/bin/env python3

# Testing of code in verifier.py
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


import contextlib
import io
import json
import os
import pathlib
import shutil
import unittest

import opencpi.ocpi_protocols.ocpi_protocols as ocpi_protocols
import ocpi_testing


# A simple pass through implementation as the sample data handling
class SingleOutputPortImplementation(ocpi_testing.Implementation):
    def reset(self):
        pass

    def sample(self, *inputs):
        # If the number of input and output ports do not match, put all sample
        # data on the first port
        if len(self.input_ports) != len(self.output_ports):
            # Do not use "[[]] * n" type code in the below line as creates
            # shallow copies (i.e. nested lists are to the same pointer so
            # cannot be individually modified).
            resultant_messages = [[] for _ in self.output_ports]
            for port_data in inputs:
                resultant_messages[0].append(
                    {"opcode": "sample", "data": port_data})
        else:
            resultant_messages = []
            for port_data in inputs:
                resultant_messages.append(
                    [{"opcode": "sample", "data": port_data}])

        return self.output_formatter(*resultant_messages)


class MultiOutputPortImplementation(ocpi_testing.Implementation):
    def __init__(self):
        super().__init__()

        self.input_ports = ["input_1", "input_2"]
        self.output_ports = ["output_1", "output_2"]

    def reset(self):
        pass

    def select_input(self, input_1, input_2):
        if input_1 is not None:
            return 0
        else:
            return 1

    def sample(self, input_1, input_2):
        return self._inputs_to_outputs_data_pass_through(
            "sample", input_1, input_2)

    def time(self, input_1, input_2):
        return self._inputs_to_outputs_data_pass_through(
            "time", input_1, input_2)

    def sample_interval(self, input_1, input_2):
        return self._inputs_to_outputs_data_pass_through(
            "sample_interval", input_1, input_2)

    def discontinuity(self, input_1, input_2):
        return self._inputs_to_outputs_no_data_pass_through(
            "discontinuity", input_1, input_2)

    def flush(self, input_1, input_2):
        return self._inputs_to_outputs_no_data_pass_through(
            "flush", input_1, input_2)

    def metadata(self, input_1, input_2):
        return self._inputs_to_outputs_data_pass_through(
            "metadata", input_1, input_2)

    def _inputs_to_outputs_data_pass_through(self, opcode, *inputs):
        # For opcodes with data (i.e. sample, time, sample interval and
        # metadata)
        outputs = [[] for _ in inputs]
        for index, input_data in enumerate(inputs):
            if input_data is not None:
                outputs[index].append({"opcode": opcode, "data": input_data})
        return self.output_formatter(*outputs)

    def _inputs_to_outputs_no_data_pass_through(self, opcode, *inputs):
        # For opcodes without data (i.e. discontinuity and flush)
        outputs = [[] for _ in inputs]
        for index, input_data in enumerate(inputs):
            if input_data is True:
                outputs[index].append({"opcode": opcode, "data": None})
        return self.output_formatter(*outputs)


class TestVerifier(unittest.TestCase):
    def setUp(self):
        # Create a temporary test file structure
        self._test_directory_base = pathlib.Path(__file__).parent.joinpath(
            "temp")
        test_directory_structure = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp")
        test_directory_structure.mkdir(parents=True)
        test_directory_structure.joinpath("a_component.rcc").mkdir()
        test_directory_structure.joinpath("a_component.hdl").mkdir()
        test_directory_structure.joinpath("a_component.comp").mkdir(
            parents=True)
        test_directory_structure.joinpath("a_component.test").joinpath(
            "run").joinpath("test_platform").mkdir(parents=True)
        test_directory_structure.joinpath("a_component.test").joinpath(
            "gen").joinpath("inputs").mkdir(parents=True)
        test_directory_structure.joinpath("a_component.test").joinpath(
            "a_implementation.py").touch()
        self._test_directory_base.joinpath(
            "a_project").joinpath(".project").touch()

        # Get the current working directory
        self._starting_working_directory = pathlib.Path.cwd()

        # Change the current working directory to the test directory
        os.chdir(test_directory_structure.joinpath(
            "a_component.test").joinpath("run").joinpath("test_platform"))

    def tearDown(self):
        # Move back to the original working directory
        os.chdir(self._starting_working_directory)

        # Delete the test directory structure
        shutil.rmtree(self._test_directory_base)

    # Test case for verifier with mostly default values
    def test_verifier_init(self):
        implementation = SingleOutputPortImplementation()
        test_verifier = ocpi_testing.Verifier(implementation)

        self.assertIsNotNone(test_verifier._test_log)

    def test_verify_equal_correct_data(self):
        # Create input data file
        input_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("gen").joinpath("inputs").joinpath(
            "test.port")
        with ocpi_protocols.WriteMessagesFile(
                input_file_path, "short_timed_sample") as input_data_file:
            input_data_file.write_message("discontinuity", None)
            input_data_file.write_message("time", 1.23)
            input_data_file.write_message("sample", [10, 11, 12])

        # Create output data file
        output_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output.out")
        with ocpi_protocols.WriteMessagesFile(
                output_file_path, "short_timed_sample") as output_data_file:
            output_data_file.write_message("discontinuity", None)
            output_data_file.write_message("time", 1.23)
            output_data_file.write_message("sample", [10, 11, 12])

        implementation = SingleOutputPortImplementation()
        test_verifier = ocpi_testing.Verifier(implementation)
        test_verifier.set_port_types(["short_timed_sample"], [
                                     "short_timed_sample"], ["equal"])

        self.assertTrue(
            test_verifier.verify("case00.01", [input_file_path],
                                 [output_file_path]))

        # Check there is a reference output file in the reference output
        # directory - to check the reference data has been written to this
        # directory.
        reference_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output.reference")
        self.assertTrue(reference_file_path.exists())
        with open(reference_file_path, "rb") as reference_file:
            reference_data = reference_file.read()
        self.assertGreater(len(reference_data), 0)

    def test_verify_equal_incorrect_data(self):
        # Create input data file
        input_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("gen").joinpath("inputs").joinpath(
            "test.port")
        with ocpi_protocols.WriteMessagesFile(
                input_file_path, "short_timed_sample") as input_data_file:
            input_data_file.write_message("discontinuity", None)
            input_data_file.write_message("time", 1.23)
            input_data_file.write_message("sample", [10, 11, 12])

        # Create output data file
        output_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output.out")
        with ocpi_protocols.WriteMessagesFile(
                output_file_path, "short_timed_sample") as output_data_file:
            output_data_file.write_message("discontinuity", None)
            output_data_file.write_message("time", 1.23)
            output_data_file.write_message("sample", [20, 21, 22])

        implementation = SingleOutputPortImplementation()
        test_verifier = ocpi_testing.Verifier(implementation)
        test_verifier.set_port_types(["short_timed_sample"], [
                                     "short_timed_sample"], ["equal"])

        self.assertFalse(
            test_verifier.verify("case00.01", [input_file_path],
                                 [output_file_path]))

        # Check there is a reference output file in the reference output
        # directory - to check the reference data has been written to this
        # directory.
        reference_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output.reference")
        self.assertTrue(reference_file_path.exists())
        with open(reference_file_path, "rb") as reference_file:
            reference_data = reference_file.read()
        self.assertGreater(len(reference_data), 0)

    def test_verify_statistical_correct_data(self):
        # Create input data file
        input_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("gen").joinpath("inputs").joinpath(
            "test.port")
        with ocpi_protocols.WriteMessagesFile(
                input_file_path, "short_timed_sample") as input_data_file:
            input_data_file.write_message("discontinuity", None)
            input_data_file.write_message("time", 1.23)
            input_data_file.write_message("sample", [10, 11, 12])

        # Create output data file
        output_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output.out")
        with ocpi_protocols.WriteMessagesFile(
                output_file_path, "short_timed_sample") as output_data_file:
            output_data_file.write_message("discontinuity", None)
            output_data_file.write_message("time", 1.23)
            output_data_file.write_message("sample", [10, 11, 12])

        implementation = SingleOutputPortImplementation()
        test_verifier = ocpi_testing.Verifier(implementation)
        test_verifier.set_port_types(["short_timed_sample"], [
                                     "short_timed_sample"], ["statistical"])

        self.assertTrue(
            test_verifier.verify("case00.01", [input_file_path],
                                 [output_file_path]))

        # Check there is a reference output file in the reference output
        # directory - to check the reference data has been written to this
        # directory.
        reference_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output.reference")
        self.assertTrue(reference_file_path.exists())
        with open(reference_file_path, "rb") as reference_file:
            reference_data = reference_file.read()
        self.assertGreater(len(reference_data), 0)

    def test_verify_statistical_incorrect_data(self):
        # Create input data file
        input_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("gen").joinpath("inputs").joinpath(
            "test.port")
        with ocpi_protocols.WriteMessagesFile(
                input_file_path, "short_timed_sample") as input_data_file:
            input_data_file.write_message("discontinuity", None)
            input_data_file.write_message("time", 1.23)
            input_data_file.write_message("sample", [10, 11, 12])

        # Create output data file
        output_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output.out")
        with ocpi_protocols.WriteMessagesFile(
                output_file_path, "short_timed_sample") as output_data_file:
            output_data_file.write_message("discontinuity", None)
            output_data_file.write_message("time", 1.23)
            output_data_file.write_message("sample", [20, 21, 22])

        implementation = SingleOutputPortImplementation()
        test_verifier = ocpi_testing.Verifier(implementation)
        test_verifier.set_port_types(["short_timed_sample"], [
                                     "short_timed_sample"], ["statistical"])

        self.assertFalse(
            test_verifier.verify("case00.01", [input_file_path],
                                 [output_file_path]))

        # Check there is a reference output file in the reference output
        # directory - to check the reference data has been written to this
        # directory.
        reference_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output.reference")
        self.assertTrue(reference_file_path.exists())
        with open(reference_file_path, "rb") as reference_file:
            reference_data = reference_file.read()
        self.assertGreater(len(reference_data), 0)

    def test_verify_bad_output_data_file(self):
        # As the data files to be imported are the output of implementation-
        # under-test it is possible this data output may not be perfect (as
        # it comes from the test target). Therefore importing such data that is
        # not correctly formatted in an file is a possible occurrence, so
        # should be handled - and therefore tested.

        sample_data_1 = [1] * 10
        sample_data_2 = [2] * 10

        # Create input data file
        input_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("gen").joinpath("inputs").joinpath(
            "test.port")
        with ocpi_protocols.WriteMessagesFile(
                input_file_path, "short_timed_sample") as input_data_file:
            input_data_file.write_message("sample_interval", 2**-26)
            input_data_file.write_message("time", 1.0)
            input_data_file.write_message("sample", sample_data_1)
            input_data_file.write_message("sample", sample_data_2)

        # Create output data file - which contains a error
        output_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output.out")
        headers = [
            # Sample interval
            [0x10, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00],
            # Time - with no length / data, a purposefully incorrect message
            [0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00],
            # Sample
            [0x0A, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
            # Sample
            [0x0A, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]]
        data = [
            # Sample interval
            [0x00, 0x00, 0x00, 0x00, 0x40, 0x00, 0x00, 0x00,
             0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
            # Time - with no data, a purposefully incorrect message
            [],
            # Sample
            sample_data_1,
            # Sample
            sample_data_2]
        test_data = []
        for header, data_body in zip(headers, data):
            test_data = test_data + header + data_body
        with open(output_file_path, "wb") as binary_file:
            binary_file.write(bytes(test_data))

        implementation = SingleOutputPortImplementation()
        test_verifier = ocpi_testing.Verifier(implementation)
        test_verifier.set_port_types(["short_timed_sample"], [
                                     "short_timed_sample"], ["equal"])

        self.assertFalse(
            test_verifier.verify("case00.01", [input_file_path],
                                 [output_file_path]))

    def test_test_passed(self):
        case = "02"
        subcase = "04"
        worker = "test_worker.rcc"
        port = "output"
        implementation = SingleOutputPortImplementation()
        test_verifier = ocpi_testing.Verifier(implementation)
        test_verifier.set_port_types(["short_timed_sample"], [
                                     "short_timed_sample"], ["equal"])
        test_verifier.test_passed(worker, port, case, subcase)

        log_path = self._test_directory_base.joinpath("a_project").joinpath(
            "components").joinpath("dsp").joinpath(
            "a_component.comp").joinpath("test_log.json")
        with open(log_path, "r") as log_file:
            written_log = json.load(log_file)
        # Cannot just compare as equal for whole log as contains time which can
        # change between generating the record and checking.
        self.assertEqual(
            written_log[case][subcase][worker]["test_platform"]["result"][
                port],
            "PASSED")
        self.assertIn("date",
                      written_log[case][subcase][worker]["test_platform"])
        self.assertIn("time",
                      written_log[case][subcase][worker]["test_platform"])
        self.assertEqual(
            written_log[case][subcase][worker]["test_platform"][
                "test_directory"],
            "components/dsp/a_component.test")
        self.assertIn("test_directory_commit_id",
                      written_log[case][subcase][worker]["test_platform"])
        self.assertEqual(
            written_log[case][subcase][worker]["test_platform"][
                "rcc_worker_directory"],
            "components/dsp/a_component.rcc")
        self.assertIn("rcc_worker_directory_commit_id",
                      written_log[case][subcase][worker]["test_platform"])
        self.assertEqual(
            written_log[case][subcase][worker]["test_platform"][
                "hdl_worker_directory"],
            "components/dsp/a_component.hdl")
        self.assertIn("hdl_worker_directory_commit_id",
                      written_log[case][subcase][worker]["test_platform"])
        self.assertEqual(
            written_log[case][subcase][worker]["test_platform"][
                "primitive_directory"],
            "hdl/primitives")
        self.assertIn("primitive_directory_commit_id",
                      written_log[case][subcase][worker]["test_platform"])

    def test_test_failed(self):
        case = "03"
        subcase = "05"
        worker = "test_worker.hdl"
        port = "output"
        failure_message = "Testing of test_failed()"
        implementation = SingleOutputPortImplementation()
        test_verifier = ocpi_testing.Verifier(implementation)
        test_verifier.set_port_types(["short_timed_sample"], [
                                     "short_timed_sample"], ["equal"])

        stdout_handler = io.StringIO()
        with contextlib.redirect_stdout(stdout_handler):
            test_verifier.test_failed(worker, port, case,
                                      subcase, failure_message)

        # Error message printed check
        printed_message = stdout_handler.getvalue()
        self.assertIn(failure_message, printed_message)

        log_path = self._test_directory_base.joinpath("a_project").joinpath(
            "components").joinpath("dsp").joinpath(
            "a_component.comp").joinpath("test_log.json")
        with open(log_path, "r") as log_file:
            written_log = json.load(log_file)
        # Cannot just compare as equal for whole log as contains time which can
        # change between generating the record and checking.
        self.assertEqual(
            written_log[case][subcase][worker]["test_platform"]["result"][
                port],
            "FAILED")
        self.assertIn("date",
                      written_log[case][subcase][worker]["test_platform"])
        self.assertIn("time",
                      written_log[case][subcase][worker]["test_platform"])
        self.assertEqual(
            written_log[case][subcase][worker]["test_platform"][
                "test_directory"],
            "components/dsp/a_component.test")
        self.assertIn("test_directory_commit_id",
                      written_log[case][subcase][worker]["test_platform"])
        self.assertEqual(
            written_log[case][subcase][worker]["test_platform"][
                "rcc_worker_directory"],
            "components/dsp/a_component.rcc")
        self.assertIn("rcc_worker_directory_commit_id",
                      written_log[case][subcase][worker]["test_platform"])
        self.assertEqual(
            written_log[case][subcase][worker]["test_platform"][
                "hdl_worker_directory"],
            "components/dsp/a_component.hdl")
        self.assertIn("hdl_worker_directory_commit_id",
                      written_log[case][subcase][worker]["test_platform"])
        self.assertEqual(
            written_log[case][subcase][worker]["test_platform"][
                "primitive_directory"],
            "hdl/primitives")
        self.assertIn("primitive_directory_commit_id",
                      written_log[case][subcase][worker]["test_platform"])

    def test_verify_no_comp_directory(self):
        # Delete the documentation directory made during setup()
        self._test_directory_base = pathlib.Path(__file__).parent.joinpath(
            "temp")
        test_directory_structure = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp")
        shutil.rmtree(test_directory_structure.joinpath("a_component.comp"))

        # Create input data file
        input_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("gen").joinpath("inputs").joinpath(
            "test.port")
        with ocpi_protocols.WriteMessagesFile(
                input_file_path, "short_timed_sample") as input_data_file:
            input_data_file.write_message("discontinuity", None)
            input_data_file.write_message("time", 1.23)
            input_data_file.write_message("sample", [10, 11, 12])

        # Create output data file
        output_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output.out")
        with ocpi_protocols.WriteMessagesFile(
                output_file_path, "short_timed_sample") as output_data_file:
            output_data_file.write_message("discontinuity", None)
            output_data_file.write_message("time", 1.23)
            output_data_file.write_message("sample", [10, 11, 12])

        implementation = SingleOutputPortImplementation()
        test_verifier = ocpi_testing.Verifier(implementation)
        test_verifier.set_port_types(["short_timed_sample"], [
                                     "short_timed_sample"], ["equal"])

        self.assertTrue(
            test_verifier.verify("case00.01", [input_file_path],
                                 [output_file_path]))

        # Check there is a reference output file in the reference output
        # directory - to check the reference data has been written to this
        # directory.
        reference_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output.reference")
        self.assertTrue(reference_file_path.exists())
        with open(reference_file_path, "rb") as reference_file:
            reference_data = reference_file.read()
        self.assertGreater(len(reference_data), 0)

    def test_multiple_outputs_correct_data(self):
        # Create input data files
        input_1_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("gen").joinpath("inputs").joinpath(
            "input_1.port")
        with ocpi_protocols.WriteMessagesFile(
                input_1_file_path, "short_timed_sample") as input_1_data_file:
            input_1_data_file.write_message("discontinuity", None)
            input_1_data_file.write_message("time", 1.23)
            input_1_data_file.write_message("sample", [10, 11, 12])
        input_2_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("gen").joinpath("inputs").joinpath(
            "input_2.port")
        with ocpi_protocols.WriteMessagesFile(
                input_2_file_path, "short_timed_sample") as input_2_data_file:
            input_2_data_file.write_message("flush", None)
            input_2_data_file.write_message("sample_interval", 0.1)
            input_2_data_file.write_message("sample", [100, 200, 300])

        # Create output data files
        output_1_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output_1.out")
        with ocpi_protocols.WriteMessagesFile(
                output_1_file_path,
                "short_timed_sample") as output_1_data_file:
            output_1_data_file.write_message("discontinuity", None)
            output_1_data_file.write_message("time", 1.23)
            output_1_data_file.write_message("sample", [10, 11, 12])
        output_2_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output_2.out")
        with ocpi_protocols.WriteMessagesFile(
                output_2_file_path,
                "short_timed_sample") as output_2_data_file:
            output_2_data_file.write_message("flush", None)
            output_2_data_file.write_message("sample_interval", 0.1)
            output_2_data_file.write_message("sample", [100, 200, 300])

        implementation = MultiOutputPortImplementation()
        test_verifier = ocpi_testing.Verifier(implementation)
        test_verifier.set_port_types(
            ["short_timed_sample", "short_timed_sample"],
            ["short_timed_sample", "short_timed_sample"],
            ["equal", "equal"])

        self.assertTrue(
            test_verifier.verify("case00.01",
                                 [input_1_file_path, input_2_file_path],
                                 output_1_file_path, port_select=1))

        # Check reference outputs have been written to file
        reference_1_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output_1.reference")
        self.assertTrue(reference_1_file_path.exists())
        with open(reference_1_file_path, "rb") as reference_1_file:
            self.assertGreater(len(reference_1_file.read()), 0)
        reference_2_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output_2.reference")
        self.assertTrue(reference_2_file_path.exists())
        with open(reference_2_file_path, "rb") as reference_2_file:
            self.assertGreater(len(reference_2_file.read()), 0)

        # Purposefully make output 1's data incorrect so if the wrong port is
        # being verified it will fail, and since this unit test aims to test
        # correct data outputs the unit test will also fail
        with ocpi_protocols.ParseMessagesFile(
                reference_1_file_path,
                "short_timed_sample") as reference_1_file:
            reference_1_data = reference_1_file.get_all_messages()
        with ocpi_protocols.WriteMessagesFile(
                reference_1_file_path,
                "short_timed_sample") as reference_1_file:
            for index, message in enumerate(reference_1_data):
                if message["opcode"] == "sample":
                    data = [value + 1 for value in reference_1_data[index]["data"]]
                    reference_1_file.write_message("sample", data)
                else:
                    reference_1_file.write_dict_message(message)

        # Get the time the reference files were modified as these should not be
        # regenerated between output verifications where the implementation-
        # under-test data is not new.
        reference_1_file_modification_time = os.path.getmtime(
            reference_1_file_path)
        reference_2_file_modification_time = os.path.getmtime(
            reference_2_file_path)

        self.assertTrue(
            test_verifier.verify("case00.01",
                                 [input_1_file_path, input_2_file_path],
                                 output_2_file_path, port_select=2))

        # Check the reference files have not been regenerated
        self.assertEqual(reference_1_file_modification_time,
                         os.path.getmtime(reference_1_file_path))
        self.assertEqual(reference_2_file_modification_time,
                         os.path.getmtime(reference_2_file_path))

    def test_require_rerun_reference_new_implementation_output(self):
        # Test that the reference is generated in cases where the
        # implementation-under-test output is newer than any existing
        # reference. Since verify only generates reference output when expected
        # to be required, but need to ensure reference being used is always
        # up-to-date.

        # Create input data files
        input_1_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("gen").joinpath("inputs").joinpath(
            "input_1.port")
        with ocpi_protocols.WriteMessagesFile(
                input_1_file_path, "short_timed_sample") as input_1_data_file:
            input_1_data_file.write_message("discontinuity", None)
            input_1_data_file.write_message("time", 1.23)
            input_1_data_file.write_message("sample", [10, 11, 12])
        input_2_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("gen").joinpath("inputs").joinpath(
            "input_2.port")
        with ocpi_protocols.WriteMessagesFile(
                input_2_file_path, "short_timed_sample") as input_2_data_file:
            input_2_data_file.write_message("flush", None)
            input_2_data_file.write_message("sample_interval", 0.1)
            input_2_data_file.write_message("sample", [100, 200, 300])

        # Create output data files. Additionally output 2 will be made
        # incorrect so when testing verify with output 1 ensuring only one
        # ports test will pass so checking the correct port is being tested.
        output_1_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output_1.out")
        with ocpi_protocols.WriteMessagesFile(
                output_1_file_path,
                "short_timed_sample") as output_1_data_file:
            output_1_data_file.write_message("discontinuity", None)
            output_1_data_file.write_message("time", 1.23)
            output_1_data_file.write_message("sample", [10, 11, 12])
        output_2_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output_2.out")
        with ocpi_protocols.WriteMessagesFile(
                output_2_file_path,
                "short_timed_sample") as output_2_data_file:
            output_2_data_file.write_message("flush", None)
            output_2_data_file.write_message("sample_interval", 0.1)
            output_2_data_file.write_message("sample", [50, 50, 50])

        implementation = MultiOutputPortImplementation()
        test_verifier = ocpi_testing.Verifier(implementation)
        test_verifier.set_port_types(
            ["short_timed_sample", "short_timed_sample"],
            ["short_timed_sample", "short_timed_sample"],
            ["equal", "equal"])

        self.assertTrue(
            test_verifier.verify("case00.01",
                                 [input_1_file_path, input_2_file_path],
                                 output_1_file_path, port_select=1))

        # Check reference outputs have been written to file
        reference_1_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output_1.reference")
        self.assertTrue(reference_1_file_path.exists())
        with open(reference_1_file_path, "rb") as reference_1_file:
            self.assertGreater(len(reference_1_file.read()), 0)
        reference_2_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output_2.reference")
        self.assertTrue(reference_2_file_path.exists())
        with open(reference_2_file_path, "rb") as reference_2_file:
            self.assertGreater(len(reference_2_file.read()), 0)

        # Get the time the reference files were modified as these should not be
        # regenerated between output verifications where the implementation-
        # under-test data is not new.
        reference_1_file_modification_time = os.path.getmtime(
            reference_1_file_path)
        reference_2_file_modification_time = os.path.getmtime(
            reference_2_file_path)

        # Make new implementation-under-test output data files, which should
        # trigger the verifier to make new reference output files at the next
        # verify. Additionally output 1 will be made incorrect so when testing
        # verify with output 2 ensuring only one ports test will pass so
        # checking the correct port is being tested.
        output_1_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output_1.out")
        with ocpi_protocols.WriteMessagesFile(
                output_1_file_path,
                "short_timed_sample") as output_1_data_file:
            output_1_data_file.write_message("discontinuity", None)
            output_1_data_file.write_message("time", 1.23)
            output_1_data_file.write_message("sample", [20, 20, 20])
        output_2_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output_2.out")
        with ocpi_protocols.WriteMessagesFile(
                output_2_file_path,
                "short_timed_sample") as output_2_data_file:
            output_2_data_file.write_message("flush", None)
            output_2_data_file.write_message("sample_interval", 0.1)
            output_2_data_file.write_message("sample", [100, 200, 300])

        self.assertTrue(
            test_verifier.verify("case00.01",
                                 [input_1_file_path, input_2_file_path],
                                 output_2_file_path, port_select=2))

    def test_require_rerun_reference_new_python_implementation(self):
        # Test that the reference is generated in cases where the Python
        # implementation is newer than any existing reference output data.
        # Since verify only generates reference output when expected to be
        # required, but need to ensure reference being used is always
        # up-to-date.

        # Create input data files
        input_1_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("gen").joinpath("inputs").joinpath(
            "input_1.port")
        with ocpi_protocols.WriteMessagesFile(
                input_1_file_path, "short_timed_sample") as input_1_data_file:
            input_1_data_file.write_message("discontinuity", None)
            input_1_data_file.write_message("time", 1.23)
            input_1_data_file.write_message("sample", [10, 11, 12])
        input_2_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("gen").joinpath("inputs").joinpath(
            "input_2.port")
        with ocpi_protocols.WriteMessagesFile(
                input_2_file_path, "short_timed_sample") as input_2_data_file:
            input_2_data_file.write_message("flush", None)
            input_2_data_file.write_message("sample_interval", 0.1)
            input_2_data_file.write_message("sample", [100, 200, 300])

        # Create output data files.
        output_1_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output_1.out")
        with ocpi_protocols.WriteMessagesFile(
                output_1_file_path,
                "short_timed_sample") as output_1_data_file:
            output_1_data_file.write_message("discontinuity", None)
            output_1_data_file.write_message("time", 1.23)
            output_1_data_file.write_message("sample", [10, 11, 12])
        output_2_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output_2.out")
        with ocpi_protocols.WriteMessagesFile(
                output_2_file_path,
                "short_timed_sample") as output_2_data_file:
            output_2_data_file.write_message("flush", None)
            output_2_data_file.write_message("sample_interval", 0.1)
            output_2_data_file.write_message("sample", [100, 200, 300])

        implementation = MultiOutputPortImplementation()
        test_verifier = ocpi_testing.Verifier(implementation)
        test_verifier.set_port_types(
            ["short_timed_sample", "short_timed_sample"],
            ["short_timed_sample", "short_timed_sample"],
            ["equal", "equal"])

        self.assertTrue(
            test_verifier.verify("case00.01",
                                 [input_1_file_path, input_2_file_path],
                                 output_1_file_path, port_select=1))

        # Check reference outputs have been written to file
        reference_1_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output_1.reference")
        self.assertTrue(reference_1_file_path.exists())
        with open(reference_1_file_path, "rb") as reference_1_file:
            self.assertGreater(len(reference_1_file.read()), 0)
        reference_2_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output_2.reference")
        self.assertTrue(reference_2_file_path.exists())
        with open(reference_2_file_path, "rb") as reference_2_file:
            self.assertGreater(len(reference_2_file.read()), 0)

        # Get the time the reference files were modified as these should not be
        # regenerated between output verifications where the implementation-
        # under-test data is not new.
        reference_1_file_modification_time = os.path.getmtime(
            reference_1_file_path)
        reference_2_file_modification_time = os.path.getmtime(
            reference_2_file_path)

        # Update / modify a Python implementation file
        self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("a_implementation.py").touch()

        self.assertTrue(
            test_verifier.verify("case00.01",
                                 [input_1_file_path, input_2_file_path],
                                 output_2_file_path, port_select=2))

        # Check the reference files have been regenerated
        self.assertGreater(os.path.getmtime(reference_1_file_path),
                           reference_1_file_modification_time)
        self.assertGreater(os.path.getmtime(reference_2_file_path),
                           reference_2_file_modification_time)

    def test_multiple_outputs_one_pass_one_fail(self):
        # Create input data files
        input_1_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("gen").joinpath("inputs").joinpath(
            "input_1.port")
        with ocpi_protocols.WriteMessagesFile(
                input_1_file_path, "short_timed_sample") as input_1_data_file:
            input_1_data_file.write_message("discontinuity", None)
            input_1_data_file.write_message("time", 1.23)
            input_1_data_file.write_message("sample", [10, 11, 12])
        input_2_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("gen").joinpath("inputs").joinpath(
            "input_2.port")
        with ocpi_protocols.WriteMessagesFile(
                input_2_file_path, "short_timed_sample") as input_2_data_file:
            input_2_data_file.write_message("flush", None)
            input_2_data_file.write_message("sample_interval", 0.1)
            input_2_data_file.write_message("sample", [100, 200, 300])

        # Create output data files
        output_1_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output_1.out")
        with ocpi_protocols.WriteMessagesFile(
                output_1_file_path,
                "short_timed_sample") as output_1_data_file:
            output_1_data_file.write_message("discontinuity", None)
            output_1_data_file.write_message("time", 1.23)
            output_1_data_file.write_message("sample", [10, 11, 12])
        output_2_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output_2.out")
        with ocpi_protocols.WriteMessagesFile(
                output_2_file_path,
                "short_timed_sample") as output_2_data_file:
            output_2_data_file.write_message("flush", None)
            output_2_data_file.write_message("sample_interval", 0.1)
            output_2_data_file.write_message("sample", [151, 252, 353])

        implementation = MultiOutputPortImplementation()
        test_verifier = ocpi_testing.Verifier(implementation)
        test_verifier.set_port_types(
            ["short_timed_sample", "short_timed_sample"],
            ["short_timed_sample", "short_timed_sample"],
            ["equal", "equal"])

        self.assertTrue(
            test_verifier.verify("case00.01",
                                 [input_1_file_path, input_2_file_path],
                                 output_1_file_path, port_select=1))
        self.assertFalse(
            test_verifier.verify("case00.01",
                                 [input_1_file_path, input_2_file_path],
                                 [output_2_file_path], port_select=2))

        # Check reference outputs have been written to file
        reference_1_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output_1.reference")
        self.assertTrue(reference_1_file_path.exists())
        with open(reference_1_file_path, "rb") as reference_1_file:
            self.assertGreater(len(reference_1_file.read()), 0)
        reference_2_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output_2.reference")
        self.assertTrue(reference_2_file_path.exists())
        with open(reference_2_file_path, "rb") as reference_2_file:
            self.assertGreater(len(reference_2_file.read()), 0)

    def test_multiple_outputs_one_fail_one_pass(self):
        # The pass / fail port order here is the opposite way round to the test
        # test_multiple_outputs_one_pass_one_fail

        # Create input data files
        input_1_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("gen").joinpath("inputs").joinpath(
            "input_1.port")
        with ocpi_protocols.WriteMessagesFile(
                input_1_file_path, "short_timed_sample") as input_1_data_file:
            input_1_data_file.write_message("discontinuity", None)
            input_1_data_file.write_message("time", 1.23)
            input_1_data_file.write_message("sample", [10, 11, 12])
        input_2_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("gen").joinpath("inputs").joinpath(
            "input_2.port")
        with ocpi_protocols.WriteMessagesFile(
                input_2_file_path, "short_timed_sample") as input_2_data_file:
            input_2_data_file.write_message("flush", None)
            input_2_data_file.write_message("sample_interval", 0.1)
            input_2_data_file.write_message("sample", [100, 200, 300])

        # Create output data files
        output_1_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output_1.out")
        with ocpi_protocols.WriteMessagesFile(
                output_1_file_path,
                "short_timed_sample") as output_1_data_file:
            output_1_data_file.write_message("discontinuity", None)
            output_1_data_file.write_message("time", 1.23)
            output_1_data_file.write_message("sample", [-1, -2, -3])
        output_2_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output_2.out")
        with ocpi_protocols.WriteMessagesFile(
                output_2_file_path,
                "short_timed_sample") as output_2_data_file:
            output_2_data_file.write_message("flush", None)
            output_2_data_file.write_message("sample_interval", 0.1)
            output_2_data_file.write_message("sample", [100, 200, 300])

        implementation = MultiOutputPortImplementation()
        test_verifier = ocpi_testing.Verifier(implementation)
        test_verifier.set_port_types(
            ["short_timed_sample", "short_timed_sample"],
            ["short_timed_sample", "short_timed_sample"],
            ["equal", "equal"])

        self.assertFalse(
            test_verifier.verify("case00.01",
                                 [input_1_file_path, input_2_file_path],
                                 output_1_file_path, port_select=1))
        self.assertTrue(
            test_verifier.verify("case00.01",
                                 [input_1_file_path, input_2_file_path],
                                 output_2_file_path, port_select=2))

        # Check reference outputs have been written to file
        reference_1_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output_1.reference")
        self.assertTrue(reference_1_file_path.exists())
        with open(reference_1_file_path, "rb") as reference_1_file:
            self.assertGreater(len(reference_1_file.read()), 0)
        reference_2_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output_2.reference")
        self.assertTrue(reference_2_file_path.exists())
        with open(reference_2_file_path, "rb") as reference_2_file:
            self.assertGreater(len(reference_2_file.read()), 0)

    def test_multiple_outputs_different_comparison_methods(self):
        # Create input data files
        input_1_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("gen").joinpath("inputs").joinpath(
            "input_1.port")
        with ocpi_protocols.WriteMessagesFile(
                input_1_file_path, "short_timed_sample") as input_1_data_file:
            input_1_data_file.write_message("discontinuity", None)
            input_1_data_file.write_message("time", 1.23)
            input_1_data_file.write_message("sample", [10, 11, 12])
        input_2_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("gen").joinpath("inputs").joinpath(
            "input_2.port")
        with ocpi_protocols.WriteMessagesFile(
                input_2_file_path, "short_timed_sample") as input_2_data_file:
            input_2_data_file.write_message("flush", None)
            input_2_data_file.write_message("sample_interval", 0.1)
            input_2_data_file.write_message("sample", [100, 200, 300])

        # Create output data files, make the output 2 data pass a bounded
        # comparison but not equal comparison test
        output_1_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output_1.out")
        with ocpi_protocols.WriteMessagesFile(
                output_1_file_path,
                "short_timed_sample") as output_1_data_file:
            output_1_data_file.write_message("discontinuity", None)
            output_1_data_file.write_message("time", 1.23)
            output_1_data_file.write_message("sample", [10, 11, 12])
        output_2_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output_2.out")
        with ocpi_protocols.WriteMessagesFile(
                output_2_file_path,
                "short_timed_sample") as output_2_data_file:
            output_2_data_file.write_message("flush", None)
            output_2_data_file.write_message("sample_interval", 0.1)
            output_2_data_file.write_message("sample", [100, 204, 301])

        implementation = MultiOutputPortImplementation()
        test_verifier = ocpi_testing.Verifier(implementation)
        test_verifier.set_port_types(
            ["short_timed_sample", "short_timed_sample"],
            ["short_timed_sample", "short_timed_sample"],
            ["equal", "bounded"])
        test_verifier.comparison[1].BOUND = 5

        self.assertTrue(
            test_verifier.verify("case00.01",
                                 [input_1_file_path, input_2_file_path],
                                 output_1_file_path, port_select=1))
        self.assertTrue(
            test_verifier.verify("case00.01",
                                 [input_1_file_path, input_2_file_path],
                                 output_2_file_path, port_select=2))

        # Check reference outputs have been written to file
        reference_1_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output_1.reference")
        self.assertTrue(reference_1_file_path.exists())
        with open(reference_1_file_path, "rb") as reference_1_file:
            self.assertGreater(len(reference_1_file.read()), 0)
        reference_2_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output_2.reference")
        self.assertTrue(reference_2_file_path.exists())
        with open(reference_2_file_path, "rb") as reference_2_file:
            self.assertGreater(len(reference_2_file.read()), 0)

    def test_multiple_outputs_verify_invalid_port(self):
        # Test behaviour for multiple port verification when the port to be
        # verified does not exist

        # Create input data files
        input_1_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("gen").joinpath("inputs").joinpath(
            "input_1.port")
        with ocpi_protocols.WriteMessagesFile(
                input_1_file_path, "short_timed_sample") as input_1_data_file:
            input_1_data_file.write_message("discontinuity", None)
            input_1_data_file.write_message("time", 1.23)
            input_1_data_file.write_message("sample", [10, 11, 12])
        input_2_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("gen").joinpath("inputs").joinpath(
            "input_2.port")
        with ocpi_protocols.WriteMessagesFile(
                input_2_file_path, "short_timed_sample") as input_2_data_file:
            input_2_data_file.write_message("flush", None)
            input_2_data_file.write_message("sample_interval", 0.1)
            input_2_data_file.write_message("sample", [100, 200, 300])

        # Create output data files
        output_1_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output_1.out")
        with ocpi_protocols.WriteMessagesFile(
                output_1_file_path,
                "short_timed_sample") as output_1_data_file:
            output_1_data_file.write_message("discontinuity", None)
            output_1_data_file.write_message("time", 1.23)
            output_1_data_file.write_message("sample", [10, 20, 30])
        output_2_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output_2.out")
        with ocpi_protocols.WriteMessagesFile(
                output_2_file_path,
                "short_timed_sample") as output_2_data_file:
            output_2_data_file.write_message("flush", None)
            output_2_data_file.write_message("sample_interval", 0.1)
            output_2_data_file.write_message("sample", [100, 200, 300])

        implementation = MultiOutputPortImplementation()
        test_verifier = ocpi_testing.Verifier(implementation)
        test_verifier.set_port_types(
            ["short_timed_sample", "short_timed_sample"],
            ["short_timed_sample", "short_timed_sample"],
            ["equal", "equal"])

        with self.assertRaises(ValueError):
            test_verifier.verify("case00.01",
                                 [input_1_file_path, input_2_file_path],
                                 [output_1_file_path, output_2_file_path],
                                 port_select=3)

    def test_set_port_types_incorrect_number_inputs(self):
        implementation = MultiOutputPortImplementation()
        test_verifier = ocpi_testing.Verifier(implementation)

        with self.assertRaises(ValueError):
            test_verifier.set_port_types(
                ["short_timed_sample"],
                ["short_timed_sample", "short_timed_sample"],
                ["equal", "equal"])

    def test_set_port_types_incorrect_number_outputs(self):
        implementation = MultiOutputPortImplementation()
        test_verifier = ocpi_testing.Verifier(implementation)

        with self.assertRaises(ValueError):
            test_verifier.set_port_types(
                ["short_timed_sample", "short_timed_sample"],
                ["short_timed_sample"],
                ["equal", "equal"])

    def test_set_port_types_not_called(self):
        # Create input data file
        input_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("gen").joinpath("inputs").joinpath(
            "test.port")
        with ocpi_protocols.WriteMessagesFile(
                input_file_path, "short_timed_sample") as input_data_file:
            input_data_file.write_message("discontinuity", None)
            input_data_file.write_message("time", 1.23)
            input_data_file.write_message("sample", [10, 11, 12])

        # Create output data file
        output_file_path = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output.out")
        with ocpi_protocols.WriteMessagesFile(
                output_file_path, "short_timed_sample") as output_data_file:
            output_data_file.write_message("discontinuity", None)
            output_data_file.write_message("time", 1.23)
            output_data_file.write_message("sample", [10, 11, 12])

        implementation = SingleOutputPortImplementation()
        test_verifier = ocpi_testing.Verifier(implementation)

        with self.assertRaises(RuntimeError):
            test_verifier.verify("case00.01", [input_file_path],
                                 [output_file_path])
