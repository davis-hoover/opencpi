#!/usr/bin/env python3

# Make OpenCPI asset linter available
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

"""OCPILint Externally facing modules."""

# Allow the default checkers to be accessed
from .ocpi_linter.base_code_checker import BaseCodeCheckerDefaults, BaseCodeChecker
from .ocpi_linter.any_code_checker import AnyCodeCheckerDefaults, AnyCodeChecker
from .ocpi_linter.cpp_code_checker import CppCodeCheckerDefaults, CppCodeChecker
from .ocpi_linter.python_code_checker import PythonCodeCheckerDefaults, PythonCodeChecker
from .ocpi_linter.rst_code_checker import RstCodeCheckerDefaults, RstCodeChecker
from .ocpi_linter.vhdl_code_checker import VhdlCodeCheckerDefaults, VhdlCodeChecker
from .ocpi_linter.xml_code_checker import XmlCodeCheckerDefaults, XmlCodeChecker
from .ocpi_linter.yaml_code_checker import YamlCodeCheckerDefaults, YamlCodeChecker
from .ocpi_linter.unknown_code_checker import UnknownCodeChecker
from .ocpi_linter import utilities


from .ocpi_linter.linter_settings import LinterSettings
from .ocpi_linter.test_result import LintTestResult

# Finally include the actual linter
from .ocpi_linter.ocpi_linter import OcpiLinter
