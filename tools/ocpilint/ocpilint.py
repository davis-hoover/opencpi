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

"""Command line script to format files in expected format."""

import argparse
# This should probably be "from pathlib import Path"
import pathlib
import shutil
import logging
import sys

from ocpi_linter import ocpi_linter

assert sys.version_info >= (
    3, 6), "The OpenCPI linter must be run with Python 3.6 or later."

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Formats files and runs ocpi project code checks.")
    parser.add_argument("path", type=pathlib.Path, nargs="*",
                        help="File or directory path to check. Glob " +
                        "patterns are valid. If empty then the current " +
                        "directory will be checked.")

    # LINT EXCEPTION: any_001: 1: Not a default comment/implementation
    parser.add_argument("--skeleton", action="store_true",
                        help="Copies an empty lint configuration file to the "
                             "path defined, then quits (if no path provided "
                             "then defaults to: ./ocpilint-cfg.yml).")

    parser.add_argument("-r", "--recursive", action="store_true",
                        help="When path is a directory, search recursively.")

    parser.add_argument("-s", "--settings", type=str, default=None,
                        help="Override directory lint configuration searching "
                             "with the named yaml file.")

    # Ignore/no-ignore options
    ignore_group = parser.add_mutually_exclusive_group(required=False)
    ignore_group.add_argument("-n", "--no-ignore", action="store_true",
                              help="Prevents ignore lists from being used (cannot be "
                              "used with --ignore-unrecognised).")
    ignore_group.add_argument("-u", "--ignore-unrecognised", action="store_true",
                              help="Ignore files with unrecognised extensions.")

    # Logging/output options
    logging_group = parser.add_argument_group("logging arguments")
    logging_group.add_argument("-j", "--junit", type=str, nargs="?", const="lint_report.xml",
                               default=None,
                               help="Generate a JUnit compatible test report, with " +
                               "the defined filename (if no filename is provided " +
                               "then defaults to: lint_report.xml).")
    logging_group.add_argument("-v", "--verbose", type=str, default=None,
                               choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                               help="Sets the verbosity: DEBUG, INFO, WARNING, ERROR. " +
                               "Defaults to off (or DEBUG if --logging)")
    logging_group.add_argument("-l", "--logging", type=str, default=None, nargs="?",
                               const="./lint_log_debug.log",
                               help="Stores a processing log to the specified location " +
                               "(if none specified then defaults to ./lint_log_debug.log)")
    logging_group.add_argument("-c", "--console", action="store_true",
                               help="Show linting issues on the console.")

    arguments = parser.parse_args()


    # If a path or list of paths given verify their existence
    # These "paths" can be either a file or directory
    for path in arguments.path:
        if not path.exists():
            parser.error(f"Path \"{path}\" does not exist, exiting!")

    # If a settings file is given, verify it is a file and its existence
    if arguments.settings and (
            not pathlib.Path(arguments.settings).exists() or
            not pathlib.Path(arguments.settings).is_file()):
        parser.error(f"Setting file \"{arguments.settings}\" does not exist"
                     " or is not a file, exiting!")

    # If a junit file is given, make sure it doesn't already exist
    if arguments.junit and pathlib.Path(arguments.junit).exists():
        parser.error(
            f"JUnit file \"{arguments.junit}\" already exists, exiting!")

    # Check if log file already exist
    if arguments.logging and pathlib.Path(arguments.logging).exists():
        parser.error(
            f"Log file \"{arguments.logging}\" already exists, exiting!")

    # LINT EXCEPTION: any_001: 5: Not a default comment/implementation
    # LINT EXCEPTION: any_001: 1: Not a default comment/implementation
    if arguments.skeleton:
        if len(arguments.path) > 1:
            parser.error(
                "Only a single filepath should be included with --skeleton")
        elif len(arguments.path) == 0:
            arguments.path.append("ocpilint-cfg.yml")
        filepath = pathlib.Path(arguments.path[0]).absolute()
        if filepath.is_dir():
            filepath = filepath.joinpath("ocpilint-cfg.yml")
        print(f"Saving to: {filepath}")
        if filepath.exists():
            parser.error(
                "File already exists, please remove or select a different filename")
        default_file = pathlib.Path(ocpi_linter.__file__).parent.joinpath(
            "ocpilint-cfg.default.yml").resolve()
        shutil.copyfile(default_file, filepath)
        sys.exit(0)

    if not arguments.verbose:
        if arguments.logging:
            arguments.verbose = "DEBUG"
        else:
            arguments.verbose = "CRITICAL"
    log_level = logging.getLevelName(arguments.verbose)
    if str(log_level).startswith("Level "):
        parser.error(f"Invalid logging level given: {arguments.verbose}")

    if not arguments.logging:
        logging.basicConfig(level=log_level)
    else:
        print("Creating log file:", arguments.logging)
        try:
            logging.basicConfig(filename=arguments.logging,
                                filemode="w", level=log_level)
        except Exception as e:
            parser.error(
                f"Failed to trying to set logfile: {arguments.logging}\n{e}")

    if len(arguments.path) == 0:
        arguments.path.append(pathlib.Path.cwd())
    linter = ocpi_linter.OcpiLinter(arguments.path, arguments.recursive,
                                    arguments.ignore_unrecognised, arguments.no_ignore,
                                    arguments.settings, arguments.junit,
                                    arguments.console)
    if linter.number_files_to_check == 0:
        if linter.number_files_ignored > 0:
            print(
                f"All files have been ignored for file path {arguments.path}")
        else:
            print(f"No files found using file path {arguments.path}")
            sys.exit(1)
    else:
        result = linter.lint()
        if result:
            if arguments.logging:
                print(f"Logging can be found at {arguments.logging}")
            elif not arguments.console:
                print("Consider adjusting --logging, --verbose and --console"
                      + " options to learn more")
        sys.exit(result)
