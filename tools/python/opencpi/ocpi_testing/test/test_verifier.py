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
class SomeImplementation(ocpi_testing.Implementation):
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
        implementation = SomeImplementation()
        test_verifier = ocpi_testing.Verifier(implementation)

        self.assertIsNotNone(test_verifier._test_log)

    def test_verify_equal_correct_data(self):
        # Create input data file
        input_file_path = self._test_directory_base.joinpath("a_project").joinpath(
            "components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("gen").joinpath("inputs").joinpath(
            "test.port")
        with ocpi_protocols.WriteMessagesFile(
                input_file_path, "short_timed_sample") as input_data_file:
            input_data_file.write_message("discontinuity", None)
            input_data_file.write_message("time", 1.23)
            input_data_file.write_message("sample", [10, 11, 12])

        # Create output data file
        output_file_path = self._test_directory_base.joinpath("a_project").joinpath(
            "components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output.out")
        with ocpi_protocols.WriteMessagesFile(
                output_file_path, "short_timed_sample") as output_data_file:
            output_data_file.write_message("discontinuity", None)
            output_data_file.write_message("time", 1.23)
            output_data_file.write_message("sample", [10, 11, 12])

        implementation = SomeImplementation()
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
        input_file_path = self._test_directory_base.joinpath("a_project").joinpath(
            "components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("gen").joinpath("inputs").joinpath(
            "test.port")
        with ocpi_protocols.WriteMessagesFile(
                input_file_path, "short_timed_sample") as input_data_file:
            input_data_file.write_message("discontinuity", None)
            input_data_file.write_message("time", 1.23)
            input_data_file.write_message("sample", [10, 11, 12])

        # Create output data file
        output_file_path = self._test_directory_base.joinpath("a_project").joinpath(
            "components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output.out")
        with ocpi_protocols.WriteMessagesFile(
                output_file_path, "short_timed_sample") as output_data_file:
            output_data_file.write_message("discontinuity", None)
            output_data_file.write_message("time", 1.23)
            output_data_file.write_message("sample", [20, 21, 22])

        implementation = SomeImplementation()
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
        input_file_path = self._test_directory_base.joinpath("a_project").joinpath(
            "components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("gen").joinpath("inputs").joinpath(
            "test.port")
        with ocpi_protocols.WriteMessagesFile(
                input_file_path, "short_timed_sample") as input_data_file:
            input_data_file.write_message("discontinuity", None)
            input_data_file.write_message("time", 1.23)
            input_data_file.write_message("sample", [10, 11, 12])

        # Create output data file
        output_file_path = self._test_directory_base.joinpath("a_project").joinpath(
            "components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "caseXX.XX.a_component.worker_type.output.out")
        with ocpi_protocols.WriteMessagesFile(
                output_file_path, "short_timed_sample") as output_data_file:
            output_data_file.write_message("discontinuity", None)
            output_data_file.write_message("time", 1.23)
            output_data_file.write_message("sample", [10, 11, 12])

        implementation = SomeImplementation()
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
            "caseXX.XX.a_component.worker_type.output.reference")
        self.assertTrue(reference_file_path.exists())
        with open(reference_file_path, "rb") as reference_file:
            reference_data = reference_file.read()
        self.assertGreater(len(reference_data), 0)

    def test_verify_statistical_incorrect_data(self):
        # Create input data file
        input_file_path = self._test_directory_base.joinpath("a_project").joinpath(
            "components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("gen").joinpath("inputs").joinpath(
            "test.port")
        with ocpi_protocols.WriteMessagesFile(
                input_file_path, "short_timed_sample") as input_data_file:
            input_data_file.write_message("discontinuity", None)
            input_data_file.write_message("time", 1.23)
            input_data_file.write_message("sample", [10, 11, 12])

        # Create output data file
        output_file_path = self._test_directory_base.joinpath("a_project").joinpath(
            "components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "caseXX.XX.a_component.worker_type.output.out")
        with ocpi_protocols.WriteMessagesFile(
                output_file_path, "short_timed_sample") as output_data_file:
            output_data_file.write_message("discontinuity", None)
            output_data_file.write_message("time", 1.23)
            output_data_file.write_message("sample", [20, 21, 22])

        implementation = SomeImplementation()
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
            "caseXX.XX.a_component.worker_type.output.reference")
        self.assertTrue(reference_file_path.exists())
        with open(reference_file_path, "rb") as reference_file:
            reference_data = reference_file.read()
        self.assertGreater(len(reference_data), 0)

    def test_verify_bad_output_data_file(self):
        # As the data files to be imported are the output of implementation-
        # under-test it is possible this data output may not be perfect (as
        # it comes from the test target). Therefore importing such data that is
        # not correctly formatted in an file is a possible occurance, so should
        # be handled - and therefore tested.

        sample_data_1 = [1] * 10
        sample_data_2 = [2] * 10

        # Create input data file
        input_file_path = self._test_directory_base.joinpath("a_project").joinpath(
            "components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("gen").joinpath("inputs").joinpath(
            "test.port")
        with ocpi_protocols.WriteMessagesFile(input_file_path, "short_timed_sample") as \
                input_data_file:
            input_data_file.write_message("sample_interval", 2**-26)
            input_data_file.write_message("time", 1.0)
            input_data_file.write_message("sample", sample_data_1)
            input_data_file.write_message("sample", sample_data_2)

        # Create output data file - which contains a error
        output_file_path = self._test_directory_base.joinpath("a_project").joinpath(
            "components").joinpath("dsp").joinpath(
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

        implementation = SomeImplementation()
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
        implementation = SomeImplementation()
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
        implementation = SomeImplementation()
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

    def test_verify_no_docs_directory(self):
        # Delete the documentation directory made during setup()
        self._test_directory_base = pathlib.Path(__file__).parent.joinpath(
            "temp")
        test_directory_structure = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp")
        shutil.rmtree(test_directory_structure.joinpath("a_component.comp"))

        # Create input data file
        input_file_path = self._test_directory_base.joinpath("a_project").joinpath(
            "components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("gen").joinpath("inputs").joinpath(
            "test.port")
        with ocpi_protocols.WriteMessagesFile(
                input_file_path, "short_timed_sample") as input_data_file:
            input_data_file.write_message("discontinuity", None)
            input_data_file.write_message("time", 1.23)
            input_data_file.write_message("sample", [10, 11, 12])

        # Create output data file
        output_file_path = self._test_directory_base.joinpath("a_project").joinpath(
            "components").joinpath("dsp").joinpath(
            "a_component.test").joinpath("run").joinpath(
            "test_platform").joinpath(
            "case00.01.a_component.worker_type.output.out")
        with ocpi_protocols.WriteMessagesFile(
                output_file_path, "short_timed_sample") as output_data_file:
            output_data_file.write_message("discontinuity", None)
            output_data_file.write_message("time", 1.23)
            output_data_file.write_message("sample", [10, 11, 12])

        implementation = SomeImplementation()
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
