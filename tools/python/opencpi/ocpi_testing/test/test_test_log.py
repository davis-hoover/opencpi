#!/usr/bin/env python3

# Test code in _test_log.py
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


import json
import os
import pathlib
import shutil
import unittest

from ocpi_testing._test_log import TestLog


class TestTestLog(unittest.TestCase):
    def setUp(self):
        # Create a temporary test file structure
        self._test_directory_base = pathlib.Path(__file__).parent.joinpath(
            "temp")
        test_directory_structure = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp")
        test_directory_structure.mkdir(parents=True)
        test_directory_structure.joinpath("a_component.rcc").mkdir()
        test_directory_structure.joinpath("a_component.hdl").mkdir()
        test_directory_structure.joinpath("a_component.comp").joinpath(
            "source").mkdir(parents=True)
        test_directory_structure.joinpath("a_component.test").joinpath(
            "run").joinpath("test_platform").mkdir(parents=True)
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

    def test_record_generator(self):
        log_path = self._test_directory_base.joinpath("a_project").joinpath(
            "components").joinpath("dsp").joinpath(
            "a_component.comp").joinpath("test_log.json")
        log = TestLog(log_path)

        variables = {"value_1": 1, "value": 2}
        log.record_generator("01", "02", "typical", variables)

        with open(log_path, "r") as log_file:
            written_log = json.load(log_file)

        # Cannot just compare as equal for whole log as contains time which can
        # change between generating the record and checking.
        self.assertEqual(
            written_log["01"]["02"]["generator"],
            {"test": "typical", "variables": variables})

    def test_record_comparison_method(self):
        log_path = self._test_directory_base.joinpath("a_project").joinpath(
            "components").joinpath("dsp").joinpath(
            "a_component.comp").joinpath("test_log.json")
        log = TestLog(log_path)

        variables = {"value_1": 1, "value": 2}
        log.record_comparison_method("01", "02", "bounded", variables)

        with open(log_path, "r") as log_file:
            written_log = json.load(log_file)

        # Cannot just compare as equal for whole log as contains time which can
        # change between generating the record and checking.
        self.assertEqual(
            written_log["01"]["02"]["comparison_method"],
            {"method": "bounded", "variables": variables})

    def test_record_pass(self):
        log_path = self._test_directory_base.joinpath("a_project").joinpath(
            "components").joinpath("dsp").joinpath(
            "a_component.comp").joinpath("test_log.json")
        log = TestLog(log_path)

        log.record_pass("worker.rcc", "output", "00", "00")

        with open(log_path, "r") as log_file:
            written_log = json.load(log_file)

        # Cannot just compare as equal for whole log as contains time which can
        # change between generating the record and checking.
        self.assertEqual(
            written_log["00"]["00"]["worker.rcc"]["test_platform"]["result"][
                "output"],
            "PASSED")
        self.assertIn("date",
                      written_log["00"]["00"]["worker.rcc"]["test_platform"])
        self.assertIn("time",
                      written_log["00"]["00"]["worker.rcc"]["test_platform"])
        self.assertEqual(
            written_log["00"]["00"]["worker.rcc"]["test_platform"][
                "test_directory"],
            "components/dsp/a_component.test")
        self.assertIn("test_directory_commit_id",
                      written_log["00"]["00"]["worker.rcc"]["test_platform"])
        self.assertEqual(
            written_log["00"]["00"]["worker.rcc"]["test_platform"][
                "rcc_worker_directory"],
            "components/dsp/a_component.rcc")
        self.assertIn("rcc_worker_directory_commit_id",
                      written_log["00"]["00"]["worker.rcc"]["test_platform"])
        self.assertEqual(
            written_log["00"]["00"]["worker.rcc"]["test_platform"][
                "hdl_worker_directory"],
            "components/dsp/a_component.hdl")
        self.assertIn("hdl_worker_directory_commit_id",
                      written_log["00"]["00"]["worker.rcc"]["test_platform"])
        self.assertEqual(
            written_log["00"]["00"]["worker.rcc"]["test_platform"][
                "primitive_directory"],
            "hdl/primitives")
        self.assertIn("primitive_directory_commit_id",
                      written_log["00"]["00"]["worker.rcc"]["test_platform"])

    def test_record_fail(self):
        log_path = self._test_directory_base.joinpath("a_project").joinpath(
            "components").joinpath("dsp").joinpath(
            "a_component.comp").joinpath("test_log.json")
        log = TestLog(log_path)

        log.record_fail("worker.rcc", "output", "01", "02")

        with open(log_path, "r") as log_file:
            written_log = json.load(log_file)

        # Cannot just compare as equal for whole log as contains time which can
        # change between generating the record and checking.
        self.assertEqual(
            written_log["01"]["02"]["worker.rcc"]["test_platform"]["result"][
                "output"],
            "FAILED")
        self.assertIn("date",
                      written_log["01"]["02"]["worker.rcc"]["test_platform"])
        self.assertIn("time",
                      written_log["01"]["02"]["worker.rcc"]["test_platform"])
        self.assertEqual(
            written_log["01"]["02"]["worker.rcc"]["test_platform"][
                "test_directory"],
            "components/dsp/a_component.test")
        self.assertIn("test_directory_commit_id",
                      written_log["01"]["02"]["worker.rcc"]["test_platform"])
        self.assertEqual(
            written_log["01"]["02"]["worker.rcc"]["test_platform"][
                "rcc_worker_directory"],
            "components/dsp/a_component.rcc")
        self.assertIn("rcc_worker_directory_commit_id",
                      written_log["01"]["02"]["worker.rcc"]["test_platform"])
        self.assertEqual(
            written_log["01"]["02"]["worker.rcc"]["test_platform"][
                "hdl_worker_directory"],
            "components/dsp/a_component.hdl")
        self.assertIn("hdl_worker_directory_commit_id",
                      written_log["01"]["02"]["worker.rcc"]["test_platform"])
        self.assertEqual(
            written_log["01"]["02"]["worker.rcc"]["test_platform"][
                "primitive_directory"],
            "hdl/primitives")
        self.assertIn("primitive_directory_commit_id",
                      written_log["01"]["02"]["worker.rcc"]["test_platform"])

    def test_multiple_subcases(self):
        log_path = self._test_directory_base.joinpath("a_project").joinpath(
            "components").joinpath("dsp").joinpath(
            "a_component.comp").joinpath("test_log.json")
        log = TestLog(log_path)

        log.record_pass("worker.rcc", "output", "00", "01")
        log.record_fail("worker.rcc", "output", "00", "02")

        with open(log_path, "r") as log_file:
            written_log = json.load(log_file)

        # Cannot just compare as equal for whole log as contains time which can
        # change between generating the record and checking.

        # Pass record check
        self.assertEqual(
            written_log["00"]["01"]["worker.rcc"]["test_platform"]["result"][
                "output"],
            "PASSED")
        self.assertIn("date",
                      written_log["00"]["01"]["worker.rcc"]["test_platform"])
        self.assertIn("time",
                      written_log["00"]["01"]["worker.rcc"]["test_platform"])
        self.assertEqual(
            written_log["00"]["01"]["worker.rcc"]["test_platform"][
                "test_directory"],
            "components/dsp/a_component.test")
        self.assertIn("test_directory_commit_id",
                      written_log["00"]["01"]["worker.rcc"]["test_platform"])
        self.assertEqual(
            written_log["00"]["01"]["worker.rcc"]["test_platform"][
                "rcc_worker_directory"],
            "components/dsp/a_component.rcc")
        self.assertIn("rcc_worker_directory_commit_id",
                      written_log["00"]["01"]["worker.rcc"]["test_platform"])
        self.assertEqual(
            written_log["00"]["01"]["worker.rcc"]["test_platform"][
                "hdl_worker_directory"],
            "components/dsp/a_component.hdl")
        self.assertIn("hdl_worker_directory_commit_id",
                      written_log["00"]["01"]["worker.rcc"]["test_platform"])
        self.assertEqual(
            written_log["00"]["01"]["worker.rcc"]["test_platform"][
                "primitive_directory"],
            "hdl/primitives")
        self.assertIn("primitive_directory_commit_id",
                      written_log["00"]["01"]["worker.rcc"]["test_platform"])

        # Fail record check
        self.assertEqual(
            written_log["00"]["02"]["worker.rcc"]["test_platform"]["result"][
                "output"],
            "FAILED")
        self.assertIn("date", written_log["00"]
                      ["02"]["worker.rcc"]["test_platform"])
        self.assertIn("time", written_log["00"]
                      ["02"]["worker.rcc"]["test_platform"])
        self.assertEqual(
            written_log["00"]["02"]["worker.rcc"]["test_platform"][
                "test_directory"],
            "components/dsp/a_component.test")
        self.assertIn("test_directory_commit_id",
                      written_log["00"]["02"]["worker.rcc"]["test_platform"])
        self.assertEqual(
            written_log["00"]["02"]["worker.rcc"]["test_platform"][
                "rcc_worker_directory"],
            "components/dsp/a_component.rcc")
        self.assertIn("rcc_worker_directory_commit_id",
                      written_log["00"]["02"]["worker.rcc"]["test_platform"])
        self.assertEqual(
            written_log["00"]["02"]["worker.rcc"]["test_platform"][
                "hdl_worker_directory"],
            "components/dsp/a_component.hdl")
        self.assertIn("hdl_worker_directory_commit_id",
                      written_log["00"]["02"]["worker.rcc"]["test_platform"])
        self.assertEqual(
            written_log["00"]["02"]["worker.rcc"]["test_platform"][
                "primitive_directory"],
            "hdl/primitives")
        self.assertIn("primitive_directory_commit_id",
                      written_log["00"]["02"]["worker.rcc"]["test_platform"])

    def test_multiple_cases(self):
        log_path = self._test_directory_base.joinpath("a_project").joinpath(
            "components").joinpath("dsp").joinpath(
            "a_component.comp").joinpath("test_log.json")
        log = TestLog(log_path)

        log.record_pass("worker.rcc", "output", "00", "01")
        log.record_fail("worker.rcc", "output", "00", "02")
        log.record_pass("worker.rcc", "output", "03", "04")

        with open(log_path, "r") as log_file:
            written_log = json.load(log_file)

        # Cannot just compare as equal for whole log as contains time which can
        # change between generating the record and checking.

        # Pass record check (case 00.01)
        self.assertEqual(
            written_log["00"]["01"]["worker.rcc"]["test_platform"]["result"][
                "output"],
            "PASSED")
        self.assertIn("date", written_log["00"]
                      ["01"]["worker.rcc"]["test_platform"])
        self.assertIn("time", written_log["00"]
                      ["01"]["worker.rcc"]["test_platform"])
        self.assertEqual(
            written_log["00"]["01"]["worker.rcc"]["test_platform"][
                "test_directory"],
            "components/dsp/a_component.test")
        self.assertIn("test_directory_commit_id",
                      written_log["00"]["01"]["worker.rcc"]["test_platform"])
        self.assertEqual(
            written_log["00"]["01"]["worker.rcc"]["test_platform"][
                "rcc_worker_directory"],
            "components/dsp/a_component.rcc")
        self.assertIn("rcc_worker_directory_commit_id",
                      written_log["00"]["01"]["worker.rcc"]["test_platform"])
        self.assertEqual(
            written_log["00"]["01"]["worker.rcc"]["test_platform"][
                "hdl_worker_directory"],
            "components/dsp/a_component.hdl")
        self.assertIn("hdl_worker_directory_commit_id",
                      written_log["00"]["01"]["worker.rcc"]["test_platform"])
        self.assertEqual(
            written_log["00"]["01"]["worker.rcc"]["test_platform"][
                "primitive_directory"],
            "hdl/primitives")
        self.assertIn("primitive_directory_commit_id",
                      written_log["00"]["01"]["worker.rcc"]["test_platform"])

        # Fail record check (case 00.02)
        self.assertEqual(
            written_log["00"]["02"]["worker.rcc"]["test_platform"]["result"][
                "output"],
            "FAILED")
        self.assertIn("date", written_log["00"]
                      ["02"]["worker.rcc"]["test_platform"])
        self.assertIn("time", written_log["00"]
                      ["02"]["worker.rcc"]["test_platform"])
        self.assertEqual(
            written_log["00"]["02"]["worker.rcc"]["test_platform"][
                "test_directory"],
            "components/dsp/a_component.test")
        self.assertIn("test_directory_commit_id",
                      written_log["00"]["02"]["worker.rcc"]["test_platform"])
        self.assertEqual(
            written_log["00"]["02"]["worker.rcc"]["test_platform"][
                "rcc_worker_directory"],
            "components/dsp/a_component.rcc")
        self.assertIn("rcc_worker_directory_commit_id",
                      written_log["00"]["02"]["worker.rcc"]["test_platform"])
        self.assertEqual(
            written_log["00"]["02"]["worker.rcc"]["test_platform"][
                "hdl_worker_directory"],
            "components/dsp/a_component.hdl")
        self.assertIn("hdl_worker_directory_commit_id",
                      written_log["00"]["02"]["worker.rcc"]["test_platform"])
        self.assertEqual(
            written_log["00"]["02"]["worker.rcc"]["test_platform"][
                "primitive_directory"],
            "hdl/primitives")
        self.assertIn("primitive_directory_commit_id",
                      written_log["00"]["02"]["worker.rcc"]["test_platform"])

        # Pass record check (case 03.04)
        self.assertEqual(
            written_log["03"]["04"]["worker.rcc"]["test_platform"]["result"][
                "output"],
            "PASSED")
        self.assertIn("date", written_log["03"]
                      ["04"]["worker.rcc"]["test_platform"])
        self.assertIn("time", written_log["03"]
                      ["04"]["worker.rcc"]["test_platform"])
        self.assertEqual(
            written_log["03"]["04"]["worker.rcc"]["test_platform"][
                "test_directory"],
            "components/dsp/a_component.test")
        self.assertIn("test_directory_commit_id",
                      written_log["03"]["04"]["worker.rcc"]["test_platform"])
        self.assertEqual(
            written_log["03"]["04"]["worker.rcc"]["test_platform"][
                "rcc_worker_directory"],
            "components/dsp/a_component.rcc")
        self.assertIn("rcc_worker_directory_commit_id",
                      written_log["03"]["04"]["worker.rcc"]["test_platform"])
        self.assertEqual(
            written_log["03"]["04"]["worker.rcc"]["test_platform"][
                "hdl_worker_directory"],
            "components/dsp/a_component.hdl")
        self.assertIn("hdl_worker_directory_commit_id",
                      written_log["03"]["04"]["worker.rcc"]["test_platform"])
        self.assertEqual(
            written_log["03"]["04"]["worker.rcc"]["test_platform"][
                "primitive_directory"],
            "hdl/primitives")
        self.assertIn("primitive_directory_commit_id",
                      written_log["03"]["04"]["worker.rcc"]["test_platform"])

    def test_multiple_platforms(self):
        # Platform 1 - uses current working directory to determine platform,
        # setUp() makes this "test_platform".
        log_path = self._test_directory_base.joinpath("a_project").joinpath(
            "components").joinpath("dsp").joinpath(
            "a_component.comp").joinpath("test_log.json")
        first_platform_log = TestLog(log_path)
        first_platform_log = TestLog(log_path).record_pass(
            "worker.rcc", "output", "00", "01")

        # Change platform by changing current working directory and getting new
        # log handler
        second_platform_cwd = pathlib.Path.cwd().parent.joinpath(
            "second_platform")
        second_platform_cwd.mkdir(parents=True)
        os.chdir(second_platform_cwd)
        second_platform_log = TestLog(log_path)
        second_platform_log.record_fail("worker.rcc", "output", "02", "03")

        with open(log_path, "r") as log_file:
            written_log = json.load(log_file)

        # Cannot just compare as equal for whole log as contains time which can
        # change between generating the record and checking.

        # First platform check
        self.assertEqual(
            written_log["00"]["01"]["worker.rcc"]["test_platform"]["result"][
                "output"],
            "PASSED")
        self.assertIn("date", written_log["00"]
                      ["01"]["worker.rcc"]["test_platform"])
        self.assertIn("time", written_log["00"]
                      ["01"]["worker.rcc"]["test_platform"])
        self.assertEqual(
            written_log["00"]["01"]["worker.rcc"]["test_platform"][
                "test_directory"],
            "components/dsp/a_component.test")
        self.assertIn("test_directory_commit_id",
                      written_log["00"]["01"]["worker.rcc"]["test_platform"])
        self.assertEqual(
            written_log["00"]["01"]["worker.rcc"]["test_platform"][
                "rcc_worker_directory"],
            "components/dsp/a_component.rcc")
        self.assertIn("rcc_worker_directory_commit_id",
                      written_log["00"]["01"]["worker.rcc"]["test_platform"])
        self.assertEqual(
            written_log["00"]["01"]["worker.rcc"]["test_platform"][
                "hdl_worker_directory"],
            "components/dsp/a_component.hdl")
        self.assertIn("hdl_worker_directory_commit_id",
                      written_log["00"]["01"]["worker.rcc"]["test_platform"])
        self.assertEqual(
            written_log["00"]["01"]["worker.rcc"]["test_platform"][
                "primitive_directory"],
            "hdl/primitives")
        self.assertIn("primitive_directory_commit_id",
                      written_log["00"]["01"]["worker.rcc"]["test_platform"])

        # Second platform check
        self.assertEqual(
            written_log["02"]["03"]["worker.rcc"]["second_platform"]["result"][
                "output"],
            "FAILED")
        self.assertIn("date", written_log["02"]
                      ["03"]["worker.rcc"]["second_platform"])
        self.assertIn("time", written_log["02"]
                      ["03"]["worker.rcc"]["second_platform"])
        self.assertEqual(
            written_log["02"]["03"]["worker.rcc"]["second_platform"][
                "test_directory"],
            "components/dsp/a_component.test")
        self.assertIn("test_directory_commit_id",
                      written_log["02"]["03"]["worker.rcc"]["second_platform"])
        self.assertEqual(
            written_log["02"]["03"]["worker.rcc"]["second_platform"][
                "rcc_worker_directory"],
            "components/dsp/a_component.rcc")
        self.assertIn("rcc_worker_directory_commit_id",
                      written_log["02"]["03"]["worker.rcc"]["second_platform"])
        self.assertEqual(
            written_log["02"]["03"]["worker.rcc"]["second_platform"][
                "hdl_worker_directory"],
            "components/dsp/a_component.hdl")
        self.assertIn("hdl_worker_directory_commit_id",
                      written_log["02"]["03"]["worker.rcc"]["second_platform"])
        self.assertEqual(
            written_log["02"]["03"]["worker.rcc"]["second_platform"][
                "primitive_directory"],
            "hdl/primitives")
        self.assertIn("primitive_directory_commit_id",
                      written_log["02"]["03"]["worker.rcc"]["second_platform"])

    def test_no_hdl_worker_directory(self):
        # Delete the HDL directory made in self.setUp()
        hdl_worker_directory = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.hdl")
        hdl_worker_directory.rmdir()

        log_path = self._test_directory_base.joinpath("a_project").joinpath(
            "components").joinpath("dsp").joinpath(
            "a_component.comp").joinpath("test_log.json")
        log = TestLog(log_path)

        log.record_pass("worker.rcc", "output", "00", "01")

        with open(log_path, "r") as log_file:
            written_log = json.load(log_file)

        # Cannot just compare as equal for whole log as contains time which can
        # change between generating the record and checking.
        self.assertEqual(
            written_log["00"]["01"]["worker.rcc"]["test_platform"]["result"][
                "output"],
            "PASSED")
        self.assertIn("date", written_log["00"]
                      ["01"]["worker.rcc"]["test_platform"])
        self.assertIn("time", written_log["00"]
                      ["01"]["worker.rcc"]["test_platform"])
        self.assertEqual(
            written_log["00"]["01"]["worker.rcc"]["test_platform"][
                "test_directory"],
            "components/dsp/a_component.test")
        self.assertIn("test_directory_commit_id",
                      written_log["00"]["01"]["worker.rcc"]["test_platform"])
        self.assertEqual(
            written_log["00"]["01"]["worker.rcc"]["test_platform"][
                "rcc_worker_directory"],
            "components/dsp/a_component.rcc")
        self.assertIn("rcc_worker_directory_commit_id",
                      written_log["00"]["01"]["worker.rcc"]["test_platform"])
        self.assertNotIn("hdl_worker_directory",
                         written_log["00"]["01"]["worker.rcc"][
                             "test_platform"])
        self.assertNotIn("hdl_worker_directory_commit_id",
                         written_log["00"]["01"]["worker.rcc"][
                             "test_platform"])
        self.assertNotIn("primitive_directory",
                         written_log["00"]["01"]["worker.rcc"][
                             "test_platform"])
        self.assertNotIn("primitive_directory_commit_id",
                         written_log["00"]["01"]["worker.rcc"][
                             "test_platform"])

    def test_no_rcc_worker_directory(self):
        # Delete the RCC directory made in self.setUp()
        rcc_worker_directory = self._test_directory_base.joinpath(
            "a_project").joinpath("components").joinpath("dsp").joinpath(
            "a_component.rcc")
        rcc_worker_directory.rmdir()

        log_path = self._test_directory_base.joinpath("a_project").joinpath(
            "components").joinpath("dsp").joinpath(
            "a_component.comp").joinpath("test_log.json")
        log = TestLog(log_path)

        log.record_pass("worker.rcc", "output", "00", "01")

        with open(log_path, "r") as log_file:
            written_log = json.load(log_file)

        # Cannot just compare as equal for whole log as contains time which can
        # change between generating the record and checking.
        self.assertEqual(
            written_log["00"]["01"]["worker.rcc"]["test_platform"]["result"][
                "output"],
            "PASSED")
        self.assertIn("date", written_log["00"]
                      ["01"]["worker.rcc"]["test_platform"])
        self.assertIn("time", written_log["00"]
                      ["01"]["worker.rcc"]["test_platform"])
        self.assertEqual(
            written_log["00"]["01"]["worker.rcc"]["test_platform"][
                "test_directory"],
            "components/dsp/a_component.test")
        self.assertIn("test_directory_commit_id",
                      written_log["00"]["01"]["worker.rcc"]["test_platform"])
        self.assertNotIn("rcc_worker_directory",
                         written_log["00"]["01"]["worker.rcc"][
                             "test_platform"])
        self.assertNotIn("rcc_worker_directory_commit_id",
                         written_log["00"]["01"]["worker.rcc"][
                             "test_platform"])
        self.assertEqual(
            written_log["00"]["01"]["worker.rcc"]["test_platform"][
                "hdl_worker_directory"],
            "components/dsp/a_component.hdl")
        self.assertIn("hdl_worker_directory_commit_id",
                      written_log["00"]["01"]["worker.rcc"]["test_platform"])
        self.assertEqual(
            written_log["00"]["01"]["worker.rcc"]["test_platform"][
                "primitive_directory"],
            "hdl/primitives")
        self.assertIn("primitive_directory_commit_id",
                      written_log["00"]["01"]["worker.rcc"]["test_platform"])

    def test_no_log(self):
        log = TestLog(None)
        # Check that trying to save result when no log path does not raise
        # error
        log.record_pass("worker.rcc", "output", "00", "01")

        self.assertEqual(log.path, None)
