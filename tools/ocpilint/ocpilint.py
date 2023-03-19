#!/usr/bin/env python3

# Command line script to format files in expected format
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

import argparse
import pathlib
import shutil
import logging
import sys

from ocpi_linter import ocpi_linter

assert sys.version_info >= (3, 6), "ocpi_linter must be run with Python 3.6 or later."

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Formats files and runs ocpi project code checks.")
    parser.add_argument("path", type=str, nargs="*",
                        help="File or directory path to check. Glob " +
                        "patterns are valid. If empty then the current "+
                        "directory will be checked.")
    parser.add_argument("--junit", type=str, nargs="?", const="lint_report.xml",
                        default=None,
                        help="Generate a JUnit compatible test report, with " +
                        "the defined filename (if no filename is provided " +
                        "then defaults to: lint_report.xml).")
    parser.add_argument("-r", "--recursively", action="store_true",
                        help="When path is a directory, search recursively.")
    parser.add_argument("-n", "--no-ignore", action="store_true",
                        help="Prevents ignore lists from being used (cannot be "
                             "used with --ignore-unrecognised).")
    parser.add_argument("-u", "--ignore-unrecognised", action="store_true",
                        help="Ignore files with unrecognised extensions.")
    parser.add_argument("-s", "--settings", type=str, default=None,
                        help="Override directory lint configuration searching "
                             "with the named yaml file.")
    # LINT EXCEPTION: any_001: 1: Not a default comment/implementation
    parser.add_argument("--skeleton", action="store_true",
                        help="Copies an empty lint configuration file to the "
                             "path defined, then quits (if no path provided "
                             "then defaults to: ./ocpilint-cfg.yml).")
    parser.add_argument("--verbose", action="store_true",
                        help="Stores a processing log to: ./lint_log_debug.log.")

    arguments = parser.parse_args()

    # LINT EXCEPTION: any_001: 4: Not a default comment/implementation
    # LINT EXCEPTION: any_001: 1: Not a default comment/implementation
    if arguments.skeleton:
        if len(arguments.path) > 1:
            print("Only a single filepath should be included with skeleton")
            sys.exit(1)
        elif len(arguments.path) == 0:
            arguments.path.append("ocpilint-cfg.yml")
        filepath = pathlib.Path(arguments.path[0]).absolute()
        if filepath.is_dir():
            filepath = filepath.joinpath("ocpilint-cfg.yml")
        print(f"Saving to: {filepath}")
        if filepath.exists():
            print("File already exists, please remove or select a different filename")
            sys.exit(1)
        default_file = pathlib.Path(ocpi_linter.__file__).parent.joinpath(
            "ocpilint-cfg.yml").resolve()
        shutil.copyfile(default_file, filepath)
        sys.exit(0)

    if arguments.verbose:
        logging.basicConfig(filename="lint_log_debug.log", filemode="w", level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    if arguments.no_ignore and arguments.ignore_unrecognised:
        print("The no-ignore and the ignore-unrecognised commands are mutually "
              "exclusive, therefore only one of these can be set.")
        sys.exit(1)

    if len(arguments.path) == 0:
        arguments.path.append(".")
    linter = ocpi_linter.OcpiLinter(arguments.path, arguments.recursively,
                                    arguments.ignore_unrecognised, arguments.no_ignore,
                                    arguments.settings, arguments.junit)
    if linter.number_files_to_check == 0:
        if linter.number_files_ignored > 0:
            print(f"All files have been ignored for file path {arguments.path}")
        else:
            print(f"No files found using file path {arguments.path}")
            sys.exit(1)
    else:
        sys.exit(linter.lint())
