#!/usr/bin/env python3

# Linter for OpenCPI Projects
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

"""Top Class for OcpiLinter module."""

from datetime import datetime, timedelta
from fnmatch import fnmatch
import logging
import pathlib
import xml.etree.ElementTree as ElementTree
import xml.dom.minidom as minidom

from . import utilities
from .linter_settings import LinterSettings
from .unknown_code_checker import UnknownCodeChecker


class OcpiLinter:
    """OcpiLinter Linting class for OpenCPI project."""

    def __init__(self, paths, recursive=False,
                 ignore_unrecognised=False, no_ignore=False,
                 settings_file=None, junit_filename=None, to_console=False):
        """Initialise a OcpiLinter instance.

        Determines the files to be checked during initialisation of class.

        Args:
            paths (list): The files or directories to be checked.
            recursive (bool, optional): True if a recursive file search is
                to be completed, False if not.
            ignore_unrecognised (bool, optional): When False, an error is
                raised when asked to lint an unknown file type. When true,
                unrecognised file types are silently ignored.
            no_ignore (bool, optional): When True ignore lists will not be
                parsed from settings files.
            settings_file (str, optional): Specifies a yaml file used to
                customise the ruleset used by the linter.
            junit_filename (str, optional): Specifies the JUnit XML output file
                if desired, set to None to not produce the report.
            to_console (bool, optional): Should log messages be output to the console?

        Returns:
            Initialised OcpiLinter instance.
        """
        self._ignore_unrecognised = ignore_unrecognised
        self._no_ignore = no_ignore
        self._errors = set([])

        # Dictionary of settings used across the found files
        self._settings = {
            "default": LinterSettings.from_yaml_file(
                pathlib.Path(__file__).parent.joinpath(
                    "ocpilint-cfg.default.yml").resolve())
        }
        self.number_files_to_check = 0
        self.number_files_ignored = 0
        for path in paths:
            self._parse_tree(path, recursive, settings_file)

        self._junit_filename = junit_filename
        self._junit_report = ElementTree.Element(
            "testsuites",
            attrib={"timestamp": str(datetime.now().strftime("%Y-%m-%dT%H:%M:%S")),
                    "name": "AllTests",
                    "tests": "0", "failures": "0", "time": "0"})
        self.to_console = to_console

    def lint(self):
        """Run formatters and code checkers.

        Returns:
            Integer to mark the number of identified linter issues.
        """
        total_issue_count = 0

        for cfg in self._settings.values():
            lint_results = {}
            start = datetime.now()
            for file in cfg.lint_files:
                print(utilities.PrintStyle.BOLD
                      + f"Checking file: {file} ..."
                      + utilities.PrintStyle.NORMAL)

                linting_result = self._lint_file(file, cfg)
                # Always update the files linting log, if it has one.
                file_issue_count = 0
                for test_number, test in linting_result.items():
                    file_issue_count = file_issue_count + test.issue_count
                lint_results[file] = linting_result
                logging.debug(f"file {file} : {linting_result}")
                if file_issue_count > 0:
                    print(utilities.PrintStyle.BOLD
                          + utilities.PrintStyle.RED
                          + f"FAILED ({file_issue_count} issues in file)"
                          + utilities.PrintStyle.NORMAL)
                else:
                    print(utilities.PrintStyle.BOLD
                          + utilities.PrintStyle.GREEN
                          + "Passed"
                          + utilities.PrintStyle.NORMAL)
                total_issue_count = total_issue_count + file_issue_count

            stop = datetime.now()
            if self._junit_filename is not None:
                self._save_junit_report(cfg, lint_results, stop-start)

        print(utilities.PrintStyle.BOLD
              + utilities.PrintStyle.UNDERLINE
              + f"OpenCPI Lint Result:"
              + utilities.PrintStyle.NORMAL)
        if total_issue_count > 0:
            print(utilities.PrintStyle.BOLD
                  + utilities.PrintStyle.RED
                  + f"FAILED ({total_issue_count} issues)"
                  + utilities.PrintStyle.NORMAL)
        else:
            print(utilities.PrintStyle.BOLD
                  + utilities.PrintStyle.GREEN
                  + "Passed"
                  + utilities.PrintStyle.NORMAL)

        return total_issue_count

    def _lint_file(self, path, settings):
        """Lint a file.

        Args:
            path (str): Path of the file to be linted.
            settings (LinterSettings): Lint settings to use with this file.

        Returns:
            A dictionary with the test results.
        """
        file_extension = pathlib.Path(path).suffix or pathlib.Path(path).name

        rule_found = False
        issues = {}
        if pathlib.Path(path).is_symlink():
            logging.debug(f"Skipping symlink {path}")
            rule_found = True
        else:
            for linter in settings.lint_classes.values():
                if (file_extension in linter.get_supported_file_extensions() and
                        file_extension not in linter.get_ignored_file_extensions()):
                    issues.update(linter(path, settings,
                                         self.to_console).lint())
                    rule_found = True

        if not rule_found:
            if self._ignore_unrecognised:
                print(f"Ignoring unrecognised file: {pathlib.Path(path).name}")
                return {}
            else:
                issues.update(UnknownCodeChecker(path, settings,
                                                 self.to_console).lint())

        # Run language agnostic checks, run these after language specific
        # checks since the language formatters will do things such as remove
        # trailing blank spaces which is checked with the language agnostic
        # checker.
        if "all" in settings.lint_classes:
            linter = settings.lint_classes["all"]
            if file_extension not in linter.get_ignored_file_extensions():
                issues.update(linter(path, settings, self.to_console).lint())

        return issues

    def _check_file_ignore(self, path, settings):
        """Check whether a file should be included or ignored.

        Args:
            path (PathLike): Path to test
            settings (LinterSettings): Settings object to use

        Returns:
            bool : True on ignore, False otherwise
        """
        if self._no_ignore:
            return False

        if path.suffix in settings.ignore_ext:
            # Extension
            logging.debug(
                f"file ignored, based on extension: {path} [{settings.settings_file}]")
            return True
        elif any([fnmatch(path, f"**/{i}/**") for i in settings.ignore_dir]):
            logging.debug(
                f"file ignored, through directory match: {path} [{settings.settings_file}]")
            return True
        elif path.name in settings.ignore_ext:
            logging.debug(
                f"file ignored, based on filename match: {path} [{settings.settings_file}]")
            return True
        elif len(path.parents) <= 1:
            if any([fnmatch(path, i) for i in settings.ignore_dir]):
                logging.debug(
                    f"file ignored, through full path match: {path} [{settings.settings_file}]")
                return True
        # .is_relative_to was only added in v3.9, so use a resolved path string comp
        elif any([str(i) in str(path.resolve()) for i in settings.ignore_fullpath]):
            logging.debug(
                f"file ignored, through full path match: {path} [{settings.settings_file}]")
            return True
        return False

    def _parse_tree(self, path, recursive=False, settings_file=None):
        """Parse file tree, looking for lint configuration while recursing.

        Args:
            path (str or Path): Root of path to parse files in
            recursive (bool, optional): Run only for current directory, or recurse into subdirectories. Defaults to False.
            settings_file (LinterSettings, optional): Settings object to use. Searches for local configuration if None.
        """
        # If the settings file is defined, then only load it once
        settings = self.load_settings_file(path, settings_file)

        if path.is_symlink():
            logging.debug(f"Skipping symlink {path}")
            return

        if path.is_file():
            if not self._check_file_ignore(path, settings):
                logging.debug(
                    f"file added to lint list: {path} [{settings.settings_file}]")
                self.number_files_to_check += 1
                settings._files.add(str(path))
            else:
                self.number_files_ignored += 1

        elif path.is_dir():
            # If it is a directory, then only parse based on the pattern
            # rules.
            dir_contents = list(path.iterdir())

            for file_item in dir_contents:
                if recursive and file_item.is_dir():
                    if any([fnmatch(file_item, f"**/{i}") or fnmatch(file_item, i) for i in settings.ignore_dir]):
                        logging.debug(
                            f"dir ignored, through partial path match: {file_item} [{settings.settings_file}]")
                        continue
                    elif any([fnmatch(file_item, pathlib.Path(settings.settings_file.parent, i)) for i in settings.ignore_fullpath]):
                        logging.debug(
                            f"dir ignored, through full path match: {file_item} [{settings.settings_file}]")
                        continue
                    elif file_item in settings.ignore_fullpath:
                        logging.debug(
                            f"dir ignored, through full pathname match: {file_item} [{settings.settings_file}]")
                        continue
                    # Recurse into this directory
                    self._parse_tree(file_item, recursive, settings_file)
                    # Reload settings after potentially adding sub-directory
                    settings = self.load_settings_file(path, settings_file)

                elif file_item.is_file():
                    if not self._check_file_ignore(file_item, settings):
                        logging.debug(
                            f"file added to lint list: {file_item} [{settings.settings_file}]")
                        self.number_files_to_check += 1
                        settings._files.add(str(file_item))
                    else:
                        self.number_files_ignored += 1
        else:
            print(f"{path} not a valid file or directory, will not be "
                  + "checked / formatted.")

    def _save_junit_report(self, test_suite, test_results, suite_duration=timedelta(0)):
        """Generate JUnit report.

        Args:
            test_suite (LinterSettings): Configuration these tests belong to.
            test_results (Dict): Dictionary of result values.
            suite_duration (timedelta, optional): Time taken for this whole test suite. Defaults to 0 duration.
        """
        num_failures = sum([sum([test.has_failed for test in results.values()])
                            for results in test_results.values()])
        suite = ElementTree.SubElement(
            self._junit_report,
            "testsuite",
            attrib={"name": str(test_suite.settings_file),
                    "tests": str(sum([len(result) for result in test_results])),
                    "failures": str(num_failures),
                    "time": str(suite_duration.total_seconds())})
        # Only mention failing rules
        for filename, results in test_results.items():
            for rule_name, result in results.items():
                # See if test has already been ran
                rule_result = list(suite.iterfind(f"./*[@name='{rule_name}']"))
                if len(rule_result) == 0:
                    test = ElementTree.SubElement(
                        suite,
                        "testcase",
                        attrib={"name": rule_name,
                                "time": str(result.duration.total_seconds()),
                                "status": "run"})
                    if result.was_skipped:
                        test.attrib["status"] = "skipped"
                else:
                    test = rule_result[0]
                    if not result.was_skipped:
                        test.attrib["status"] = "run"
                        test.attrib["time"] = str(
                            float(test.attrib["time"]) + result.duration.total_seconds())

                if result.has_failed:
                    for fail in result.issues:
                        failure = ElementTree.SubElement(
                            test,
                            "failure",
                            attrib={
                                "message": "{}:{} {}".format(
                                    str(filename), fail["line"], fail["message"]),
                                "type": "ERROR"})
                        failure.text = "<![CDATA[{}:{}\n{}\nDescription: {}]]>".format(
                            str(filename), fail["line"], rule_name, fail["message"])

        self._junit_report.attrib["tests"] = str(
            int(self._junit_report.attrib["tests"]) + int(suite.attrib["tests"]))
        self._junit_report.attrib["failures"] = str(
            int(self._junit_report.attrib["failures"]) + int(suite.attrib["failures"]))
        self._junit_report.attrib["time"] = str(
            float(self._junit_report.attrib["time"]) + float(suite.attrib["time"]))

        # Pretty print/indent to file, overwriting if already exists
        xml_str = ElementTree.tostring(self._junit_report)
        xml_str = minidom.parseString(xml_str).toprettyxml(indent="  ")
        with open(self._junit_filename, "wt") as f:
            f.write(xml_str)
        print(f"JUnit report written to: {self._junit_filename}")

    def load_settings_file(self, path, settings_file=None):
        """Load and parse LinterSettings file.

        Args:
            path (str or Path): Path to start search (backwards) for settings file.
            settings_file (LinterSettings, optional): Force configuration file to use. Defaults to None.

        Returns:
            LinterSettings: Configuration to use (either found, or forced)
        """
        if settings_file:
            # Been given an explicit file
            if settings_file not in self._settings:
                print(utilities.PrintStyle.BOLD
                      + f"Loading configuration file: {settings_file}"
                      + utilities.PrintStyle.NORMAL)
                self._settings[settings_file] = LinterSettings.combine(
                    self._settings["default"],
                    LinterSettings.from_yaml_file(settings_file),
                    parent_is_defaults=True)
            return self._settings[settings_file]

        stem = pathlib.Path(path).resolve()
        if stem.is_file():
            stem = stem.parent
        leaf = pathlib.Path("ocpilint-cfg.yml")

        longest_path = ""
        inherit = True
        # Walk backwards up the path till / or settings set to not inherit
        logging.debug(stem)
        while (stem.parent != stem and inherit):
            if (stem/leaf).exists():
                if not longest_path:
                    longest_path = str(stem/leaf)
                    if str(stem/leaf) not in self._settings:
                        print(utilities.PrintStyle.BOLD
                              + f"Loading configuration file:  {longest_path}"
                              + utilities.PrintStyle.NORMAL)
                        logging.info(
                            f"Loading configuration file: {longest_path}")
                        self._settings[longest_path] = LinterSettings.from_yaml_file(
                            longest_path)
                    else:
                        self._settings[longest_path] = LinterSettings.combine(
                            self._settings["default"],
                            self._settings[longest_path],
                            parent_is_defaults=True)
                        return self._settings[longest_path]
                else:
                    print(utilities.PrintStyle.BOLD +
                          f"Updating configuration from: {longest_path} inheriting: {str(stem/leaf)}"
                          + utilities.PrintStyle.NORMAL)
                    logging.debug(
                        f"Combining {str(stem/leaf)} under {longest_path}")
                    self._settings[longest_path] = LinterSettings.combine(
                        LinterSettings.from_yaml_file(str(stem/leaf)),
                        self._settings[longest_path])
                # Check inherit value to see if we should check parent folders
                inherit = self._settings[longest_path]._inherit_parent

            stem = stem.parent

        # Setting now loaded if found. Return result.
        if longest_path:
            logging.debug(f"Using settings from: {longest_path}")
            self._settings[longest_path] = LinterSettings.combine(
                self._settings["default"],
                self._settings[longest_path],
                parent_is_defaults=True)
            return self._settings[longest_path]
        elif leaf.exists():
            if str(leaf) not in self._settings:
                print(utilities.PrintStyle.BOLD
                      + f"Loading configuration file: {str(leaf)}"
                      + utilities.PrintStyle.NORMAL)
                logging.info(f"Loading configuration file: {str(leaf)}")
                self._settings[str(leaf)] = LinterSettings.from_yaml_file(
                    str(leaf))
            logging.debug(f"Using settings from {str(leaf)}")
            self._settings[str(leaf)] = LinterSettings.combine(
                self._settings["default"],
                self._settings[str(leaf)],
                parent_is_defaults=True)
            return self._settings[str(leaf)]
        else:
            logging.debug("Using default ruleset")
            return self._settings["default"]
