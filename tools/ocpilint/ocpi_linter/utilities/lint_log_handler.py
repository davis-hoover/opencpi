#!/usr/bin/env python3

# Handle interaction with the linting log files
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

"""Linting logger for ocpilint project."""

import datetime
import json
import pathlib
import subprocess

LOG_NAME = "lint_log.json"


class LintLogHandler:
    """Lint Log Handler class."""

    def __init__(self, path):
        """Initialise linting log.

        Args:
            path (str): Path of the file being linted and for the log entry to
                be recorded.

        Returns:
            An initialised LintLogHandler instance.
        """
        self.path = pathlib.Path(path).resolve().absolute()

        # Find the OpenCPI project root directory, walk up the file structure
        # from the file being linted until a ".project" file is found in a
        # directory, which will be the top directory of a project. Or walk to
        # top of file structure at which point quit.
        search_directory = self.path
        while (len(list(search_directory.glob(".project"))) == 0) and (
                str(search_directory) != "/"):
            search_directory = search_directory.parent
        if len(list(search_directory.glob(".project"))) > 0:
            self._project_directory = search_directory
        else:
            self._project_directory = None
            print("Project root direction not found. Folder paths and "
                  + "commit IDs will not be saved.")

        # Set log path for worker implementations or component test files.
        if self.path.parent.suffix in [".rcc", ".hdl", ".test"]:
            self._log_path = self.path.parent.with_suffix(".comp").joinpath(
                LOG_NAME)

        # Set log path for component documentation files.
        elif self.path.match("*/components/*/*.comp/*.rst"):
            self._log_path = self.path.parent.joinpath(LOG_NAME)

        # Set log path for component specification files.
        elif self.path.match("*/components/*/specs/*.xml"):
            component_name = self.path.stem.replace("-spec", "")
            self._log_path = self.path.parent.parent.joinpath(
                component_name + ".comp").joinpath(LOG_NAME)

        # Set log path for primitive VHDL files.
        elif self.path.match("*/hdl/primitives/*/*/src/*.vhd"):
            self._log_path = self.path.parent.parent.joinpath(
                LOG_NAME)

        # Set log path for primitive documentation files.
        elif self.path.match("*/hdl/primitives/*/*/*.rst"):
            self._log_path = self.path.parent.joinpath(LOG_NAME)

        # No log path
        else:
            print("Linting log save location cannot be determined. Log not " +
                  "being saved.")
            self._log_path = None
            return

        if not self._log_path.parent.exists():
            self._log_path.parent.mkdir(parents=True)

        # If log file doesn't exist, create a blank log
        if not self._log_path.exists():
            self._write_log({})

        # Make sure there is an entry for this file in the log
        log = self._read_log()
        self._relative_path = str(
            self.path.relative_to(self._project_directory))
        if self._relative_path not in log:
            log[self._relative_path] = {}
            self._write_log(log)

    def record(self, test_number, test_name, number_of_issues):
        """Store a test result to the log.

        Args:
            test_number (str): The test number.
            test_name (str): The test name.
            number_of_issues (int): Number of issues the test had.
        """
        if self._log_path is not None:
            log = self._read_log()

            if number_of_issues == 0:
                result = "PASSED"
            else:
                result = "FAILED"

            now = datetime.datetime.now()
            time = now.strftime("%H:%M:%S")
            date = now.strftime("%d/%m/%Y")

            commit_id = self._get_file_commit_id()

            log[self._relative_path][test_number] = {
                "result": result,
                "date": date,
                "time": time,
                "commit_id": commit_id}

            self._write_log(log)

    def _read_log(self):
        """Read in a lint log file.

        Returns:
            Any existing log (as a dict) for the file being linted.
            Returns ``None`` if no file currently exists.
        """
        if self._log_path is not None:
            with open(self._log_path, "r") as log_file:
                log = json.load(log_file)
            return log
        else:
            return None

    def _write_log(self, log):
        """Write lint log to file.

        Args:
            log (dict): The log to be written to file.
        """
        if self._log_path is not None:
            with open(self._log_path, "w+") as log_file:
                json.dump(log, log_file)

    def _get_file_commit_id(self):
        """Get the Git commit ID for the current file being edited.

        Returns:
            A string containing the git commit ID hash for the file.
        """
        file_path = str(self.path)
        git_process = subprocess.Popen(["git", "log", "-n", "1",
                                        "--pretty=format:%H", "--", file_path],
                                       cwd=str(self.path.parent),
                                       stderr=subprocess.DEVNULL,
                                       stdout=subprocess.PIPE)
        git_process.wait()
        return git_process.communicate()[0].decode("utf-8")
