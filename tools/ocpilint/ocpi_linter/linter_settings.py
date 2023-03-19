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

"""Settings defaults and configuration file parsing for ocpilint."""

import yaml
import pathlib
import importlib
import ast
import pkgutil
import pkg_resources
import logging
import sys

from .any_code_checker import AnyCodeChecker
from .cpp_code_checker import CppCodeChecker
from .python_code_checker import PythonCodeChecker
from .rst_code_checker import RstCodeChecker
from .vhdl_code_checker import VhdlCodeChecker
from .xml_code_checker import XmlCodeChecker
from .yaml_code_checker import YamlCodeChecker
from .unknown_code_checker import UnknownCodeChecker
from . import utilities

LINTING_CLASSES = {
    "cpp": CppCodeChecker,
    "python": PythonCodeChecker,
    "rst": RstCodeChecker,
    "vhdl": VhdlCodeChecker,
    "xml": XmlCodeChecker,
    "yaml": YamlCodeChecker,
    "all": AnyCodeChecker
}


class LinterSettings:
    """Settings class, providing test, and files which are grouped."""

    def __init__(self,
                 filename="default",
                 ignore_pattern=[],
                 select_tests=[],
                 extra_rules=[],
                 extra_modules=[]
                 ):
        """Linter Configuration for a subset of files.

        Args:
            filename (str, optional): filename of loaded configuration. Defaults to "default".
            ignore_pattern (list, optional): List of ignore patterns to use for this configuration. Defaults to [].
            select_tests (dict, optional): Dictionary of enabled and disabled tests. Defaults to [].
            extra_rules (list, optional): List of additional rules to run for this set of files. Defaults to [].
            extra_modules (list, optional): List of additional python modules needed for rules . Defaults to [].
        """
        self.settings_file = pathlib.Path(filename)
        self.select_tests = dict(select_tests)
        self.extra_rules = set([self.settings_file.parent.joinpath(rule)
                                for rule in extra_rules])
        self.lint_classes = LINTING_CLASSES
        self._extra_modules = set(extra_modules)
        self._files = set()

        self.ignore_dir = set()
        self.ignore_ext = set()
        self.ignore_fullpath = set()

        # Always ignore a git folder, as lint should not reformat, or complain
        # about, anything in git's internal working area.
        self.ignore_dir.add(".git")

        for ignore in set(ignore_pattern):
            if ignore.endswith("/") and ignore.count("/") == 1:
                self.ignore_dir.add(ignore[:-1])
            elif ignore.startswith("*."):
                self.ignore_ext.add(ignore[1:])
            elif ignore.count("/") == 0:
                self.ignore_ext.add(ignore)
            else:
                if self.settings_file.parent != ".":
                    self.ignore_fullpath.add(
                        self.settings_file.parent / ignore)
                else:
                    self.ignore_fullpath.add(ignore)
        logging.info(f"Setting up new lint settings for: {self.settings_file}")
        logging.debug(f"ignore dirs: {self.ignore_dir}")
        logging.debug(f"ignore extensions: {self.ignore_ext}")
        logging.debug(f"ignore fullpath: {self.ignore_fullpath}")

        self._load_lint_rule_classes()

    @property
    def lint_files(self):
        """List of files within this configuration.

        Returns:
            list: List of filenames to parse
        """
        return sorted(self._files)

    @classmethod
    def from_yaml_file(cls, path):
        """Parse configuration from YAML file.

        Args:
            path (str or Path): Path of YAML configuration file.

        Returns:
            LinterSettings: New instance of the parsed settings
        """
        with open(path, "r") as cfg_file:
            cfg = yaml.safe_load(cfg_file)
        if cfg is None:
            print(utilities.PrintStyle.BOLD
                  + f"Configuration failed to load: {path}" +
                  utilities.PrintStyle.NORMAL)
            logging.error(f"Configuration failed to load: {path}")
            return cls()

        extra_modules = set(cfg.get("extra_modules", []))
        ignore_pattern = set(cfg.get("ignore_pattern", []))
        select_tests = dict([(test, True)
                             for test in cfg.get("enable_tests", [])])
        select_tests.update([(test, False)
                             for test in cfg.get("disable_tests", [])])
        # Log warning if a test is in both enable_tests and disable_test lists
        # within the same config file
        for test in cfg.get("enable_tests", []):
            if test in cfg.get("disable_tests", []):
                logging.warning(
                    f"Test \"{test}\" in both enable_tests and disable_tests"
                    f" lists in {pathlib.Path(path).absolute()}."
                    " Disable will take precedence.")

        return cls(path,
                   ignore_pattern,
                   select_tests,
                   cfg.get("extra_rules", []),
                   extra_modules)

    @classmethod
    def combine(cls, parent, child):
        """Combine 2 Settings objects.

        Takes the parent settings, applies the child settings on top.
        Configuration in the child will either overwrite or add to the parent
        settings.

        Args:
            parent (LinterSettings): Base settings
            child (LinterSettings): Settings to apply on top

        Returns:
            LinterSettings: The newly combined result
        """
        combined = cls(filename=child.settings_file)

        combined.select_tests.update(parent.select_tests)
        combined.select_tests.update(child.select_tests)

        combined.extra_rules.update(parent.extra_rules)
        combined.extra_rules.update(child.extra_rules)

        combined._extra_modules.update(parent._extra_modules)
        combined._extra_modules.update(child._extra_modules)

        combined._files.update(parent._files)
        combined._files.update(child._files)

        combined.ignore_dir.update(parent.ignore_dir)
        combined.ignore_dir.update(child.ignore_dir)
        combined.ignore_ext.update(parent.ignore_ext)
        combined.ignore_ext.update(child.ignore_ext)
        combined.ignore_fullpath.update(parent.ignore_fullpath)
        combined.ignore_fullpath.update(child.ignore_fullpath)

        logging.info(
            f"Setting up new combined lint settings for: {combined.settings_file}")
        logging.debug(f"combined ignore dirs: {combined.ignore_dir}")
        logging.debug(f"combined ignore extensions: {combined.ignore_ext}")
        logging.debug(f"combined ignore fullpath: {combined.ignore_fullpath}")

        return combined

    def _load_lint_rule_classes(self):
        """Parse the rules files mentioned within this LinterSettings.

        Raises:
            ModuleNotFoundError: If a required module is not installed on this system.
        """
        # Internal functions used to walk the import trees within files
        modules = set()

        def visit_Import(node):
            for name in node.names:
                modules.add(name.name.split(".")[0])

        def visit_ImportFrom(node):
            # if node.module is missing it's a "from . import ..." statement
            # if level > 0 it's a "from .submodule import ..." statement
            if node.module is not None and node.level == 0:
                modules.add(node.module.split(".")[0])

        node_iter = ast.NodeVisitor()
        node_iter.visit_Import = visit_Import
        node_iter.visit_ImportFrom = visit_ImportFrom

        modules_not_found = set([])
        modules_not_in_cfg = set([])
        for rule in self.extra_rules:
            filepath = pathlib.Path(
                self.settings_file).parent / pathlib.Path(rule)
            if filepath.exists():
                print(f"Adding rules from \"{filepath}\"")
            else:
                print(utilities.PrintStyle.RED +
                      f"Rule file \"{filepath}\" could not be found" +
                      utilities.PrintStyle.NORMAL)
                continue

            # Find only top level modules mentioned in imported files.
            with open(filepath) as cfg_file:
                node_iter.visit(ast.parse(cfg_file.read()))

            for module in modules:
                pkg = pkg_resources.Requirement(module)
                if module is "ocpi_linter":
                    # Skip inclusion of this module
                    pass
                elif module not in self._extra_modules:
                    modules_not_in_cfg.add(module)

                if (not pkg_resources.working_set.find(pkg)
                        and not (module in [m.name for m in list(pkgutil.iter_modules())])):
                    # Don't do anything if module is installed, otherwise add to
                    # error list
                    modules_not_found.add(module)

        if modules_not_in_cfg:
            print(utilities.PrintStyle.RED +
                  f"Modules \"{modules_not_in_cfg}\" is not located in the \"extra_modules\" list within configuration file {self.settings_file}" +
                  utilities.PrintStyle.NORMAL)

        if modules_not_found:
            raise ModuleNotFoundError(
                f"Unable to import modules: {modules_not_found}")

        for rule in self.extra_rules:
            spec = importlib.util.spec_from_file_location(
                "custom.ocpi_linter", filepath)
            modules = importlib.util.module_from_spec(spec)

            sys.modules["custom.ocpi_linter"] = modules
            spec.loader.exec_module(modules)

            if hasattr(modules, "LINTING_CLASSES"):
                self.lint_classes.update(getattr(modules, "LINTING_CLASSES"))
                print(utilities.PrintStyle.BOLD
                      + "Using the following custom linting rulesets: {}".format(
                          list(getattr(modules, "LINTING_CLASSES")))
                      + utilities.PrintStyle.NORMAL)
