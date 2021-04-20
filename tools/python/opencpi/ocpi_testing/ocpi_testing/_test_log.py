#!/usr/bin/env python3

# Manages writing to the test log file
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


import datetime
import json
import pathlib
import shutil
import subprocess


from ._terminal_print_formatter import print_warning


class TestLog:
    def __init__(self, log_path):
        """ Initialise test log handler

        Args:
            log_path (str): Path where the test log is to be saved to. If set
                to None, no log with be saved.

        Returns:
            Initialised TestLog instance.
        """
        if log_path is None:
            print_warning("Log path set to None, no log will be saved.")
            self.path = None
            return
        self.path = pathlib.Path(log_path)
        if not self.path.parent.exists():
            print_warning(
                f"Log save directory ({self.path.parent}) does not exist, log "
                + "will not be saved.")
            self.path = None
            return

        # If test log does not exists, make blank log
        if not self.path.is_file():
            self._save_log({})

        self._test_directory = pathlib.Path.cwd().parents[1]

        # Find the root project directory, walk up the file structure from the
        # test directory until a ".project" file is found in the directory (as
        # this is the top directory of a project. Or walk to top of file
        # structure at which point quit.
        project_search_directory = self._test_directory
        while len(list(project_search_directory.glob(".project"))) == 0 and \
                str(project_search_directory) != "/":
            project_search_directory = project_search_directory.parent
        if len(list(project_search_directory.glob(".project"))) > 0:
            self._project_directory = project_search_directory
        else:
            self._project_directory = None
            print_warning("Root project directory not found. Folder paths and "
                          + "commit ID will not be saved.")

        # Check Git is installed
        if shutil.which("git") is None:
            print_warning("Commit ID's will not be saved as Git is not "
                          + "installed")

        if self._check_in_repo(self._test_directory) is False:
            print_warning("Not working under a Git repository, commit IDs "
                          + "will not be saved.")

    def record_generator(self, test_case, test_subcase, test_name,
                         generator_variables):
        """ Save details of the generator used to the test log

        Args:
            test_case (str, int): Test case value this generator is used for.
            test_subcase (str, int): Subtest case value this generator is used
                for.
            test_name (str): Name of the test used in the generator.
            generator_variables (dict): Variables used in this generator.
        """
        # If no log cannot complete this action
        if self.path is None:
            return

        log = self._read_log()

        # Make sure there is an entry for this test case in the log
        if test_case not in log:
            log[test_case] = {}

        # Make sure this is an entry for this test subcase in this case
        if test_subcase not in log[test_case]:
            log[test_case][test_subcase] = {}

        if "generator" not in log[test_case][test_subcase]:
            log[test_case][test_subcase]["generator"] = {}

        log[test_case][test_subcase]["generator"] = {
            "test": test_name,
            "variables": generator_variables}

        self._save_log(log)

    def record_comparison_method(self, test_case, test_subcase,
                                 comparison_method_name,
                                 comparison_method_variables):
        """ Save details of the comparison method to the test log

        Args:
            test_case (str, int): Test case value this comparison method is
                used for.
            test_subcase (str, int): Subtest case value this comparison is used
                for.
            comparison_method_name (str): Name of the comparison method used.
            comparison_method_variables (dict): Variables used in this
                comparison method.
        """
        # If no log cannot complete this action
        if self.path is None:
            return

        log = self._read_log()

        # Make sure there is an entry for this test case in the log
        if test_case not in log:
            log[test_case] = {}

        # Make sure this is an entry for this test subcase in this case
        if test_subcase not in log[test_case]:
            log[test_case][test_subcase] = {}

        if "comparison_method" not in log[test_case][test_subcase]:
            log[test_case][test_subcase]["comparison_method"] = {}

        log[test_case][test_subcase]["comparison_method"] = {
            "method": comparison_method_name,
            "variables": comparison_method_variables}

        self._save_log(log)

    def record_pass(self, worker, port, test_case, test_subcase=None):
        """ Save a passed test result to the test log

        Args:
            worker (str): The worker that was tested.
            port (str): The port output that has been verified.
            test_case (str, int): Test case value this result is for.
            test_subcase (str, int, optional): Subtest case value this result
                is for.
        """
        self._save_result("PASSED", worker, port, test_case, test_subcase)

    def record_fail(self, worker, port, test_case, test_subcase=None):
        """ Save a failed test result to the test log

        Args:
            worker (str): The worker that was tested.
            port (str): The port output that has been verified.
            test_case (str, int): Test case value this result is for.
            test_subcase (str, int, optional): Subtest case value this result
                is for.
        """
        self._save_result("FAILED", worker, port, test_case, test_subcase)

    def _save_result(self, result, worker, port, test_case, test_subcase="00"):
        """ Add test result to log file

        Reads any already existing log file, updates this and then saves back
        to disk.

        Args:
            result (str): Test result string to be saved. Typically "PASSED" or
                "FAILED".
            worker (str): The worker that was tested.
            port (str): The port output that has been verified.
            test_case (str): The test case name.
            test_subcase (str, optional): The test subcase name. If not
                supplied default of "00" will be used".
        """
        # If no log cannot complete this action
        if self.path is None:
            return

        log = self._read_log()

        # No run-time environment variables store the test platform, so use the
        # current working directory to determine this
        platform = pathlib.Path.cwd().name

        now = datetime.datetime.now()
        time = now.strftime("%H:%M:%S")
        date = now.strftime("%d/%m/%Y")

        if self._project_directory is not None:
            test_directory = self._test_directory.relative_to(
                self._project_directory)
            test_directory_commit = self._get_commit_id(
                self._test_directory)
        else:
            test_directory = ""
            test_directory_commit = ""

        # Make sure there is an entry for this test case in the log
        if test_case not in log:
            log[test_case] = {}

        # Make sure this is an entry for this test subcase in this case
        if test_subcase not in log[test_case]:
            log[test_case][test_subcase] = {}

        # Make sure this is an entry for this worker in this subcase
        if worker not in log[test_case][test_subcase]:
            log[test_case][test_subcase][worker] = {}

        # Make sure this is an entry for this platform in this worker run
        if platform not in log[test_case][test_subcase][worker]:
            log[test_case][test_subcase][worker][platform] = {}

        if "result" not in log[test_case][test_subcase][worker][platform]:
            log[test_case][test_subcase][worker][platform]["result"] = {}
        log[test_case][test_subcase][worker][platform]["result"][port] = result

        # No need to record the data time and commit IDs for each port
        log[test_case][test_subcase][worker][platform]["date"] = date
        log[test_case][test_subcase][worker][platform]["time"] = time
        log[test_case][test_subcase][worker][platform][
            "test_directory"] = str(test_directory)
        log[test_case][test_subcase][worker][platform][
            "test_directory_commit_id"] = test_directory_commit

        # Without maintaining a list of which workers different platforms
        # use there is no way to know if the implementation under test is a
        # RCC or HDL implementation, so store both directories details. If
        # the directory exists
        if self._test_directory.with_suffix(".rcc").is_dir():
            if self._project_directory is not None:
                worker_directory = \
                    self._test_directory.with_suffix(".rcc").relative_to(
                        self._project_directory)
                worker_directory_commit = self._get_commit_id(
                    self._test_directory.with_suffix(".rcc"))
            else:
                worker_directory = ""
                worker_directory_commit = ""
            log[test_case][test_subcase][worker][platform][
                "rcc_worker_directory"] = str(worker_directory)
            log[test_case][test_subcase][worker][platform][
                "rcc_worker_directory_commit_id"] = worker_directory_commit
        if self._test_directory.with_suffix(".hdl").is_dir():
            if self._project_directory is not None:
                worker_directory = \
                    self._test_directory.with_suffix(".hdl").relative_to(
                        self._project_directory)
                worker_directory_commit = self._get_commit_id(
                    self._test_directory.with_suffix(".hdl"))
            else:
                worker_directory = ""
                worker_directory_commit = ""
            log[test_case][test_subcase][worker][platform][
                "hdl_worker_directory"] = str(worker_directory)
            log[test_case][test_subcase][worker][platform][
                "hdl_worker_directory_commit_id"] = worker_directory_commit
            # As primitives used in HDL workers are not currently tracked
            # in a way that can be accessed at testing time, store the
            # commit ID of the whole primitive directory.
            if self._project_directory is not None:
                primitive_directory = "hdl/primitives"
                primitive_directory_commit = self._get_commit_id(
                    self._project_directory.joinpath("hdl").joinpath("primitives"))
            else:
                primitive_directory = ""
                primitive_directory_commit = ""
            log[test_case][test_subcase][worker][platform][
                "primitive_directory"] = str(primitive_directory)
            log[test_case][test_subcase][worker][platform][
                "primitive_directory_commit_id"] = primitive_directory_commit

        self._save_log(log)

    def _read_log(self):
        """ Read any test log from file

        Returns:
            Dictionary which is any test log that has been read from file. If
                no log is on disk will return an empty dictionary.
        """
        if self.path is None:
            return {}

        with open(self.path, "r") as testing_log:
            try:
                return json.load(testing_log)
            except json.decoder.JSONDecodeError:
                print_warning("Existing test log not in expected format. " +
                              "New test log entries will not be saved.")
                self.path = None
                return {}

    def _save_log(self, log):
        """ Save test log to disk

        Args:
            log (dict): The test log to be saved as a dictionary.
        """
        if self.path is not None:
            with open(self.path, "w") as testing_log:
                json.dump(log, testing_log)

    def _get_commit_id(self, path):
        """ Get the Git commit ID for a set path

        Args:
            path (str): File path to find the Git commit ID of.

        Returns:
            String of the commit ID hash. If cannot find commit ID will return
                empty string.
        """
        # If Git not installed cannot find commit ID so do not return any
        if shutil.which("git") is None:
            return ""

        if path.exists():
            if self._check_in_repo(path) is False:
                return ""

            git_process = subprocess.Popen(["git", "log", "-n", "1",
                                            "--pretty=format:%H", "--", path],
                                           stdout=subprocess.PIPE)
            git_process.wait()
            return git_process.communicate()[0].decode("utf-8")
        else:
            return ""

    def _check_in_repo(self, path):
        """ Check path is part of Git repository

        Args:
            path (str): Path to check if in Git repository.

        Returns:
            Boolean. True when path is part of Git repository, otherwise
                returns False.
        """
        repo_check = subprocess.Popen(
            ["git", "rev-parse", "--is-inside-work-tree"], cwd=path,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        check_result = repo_check.communicate()
        if len(check_result) > 0:
            if check_result[0].decode("utf-8").lower().startswith("true"):
                return True
            else:
                return False
        else:
            return False
