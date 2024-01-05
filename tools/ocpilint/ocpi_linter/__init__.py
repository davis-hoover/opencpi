#!/usr/bin/env python3

# __init__.py for ocpi_linter
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
from .base_code_checker import BaseCodeCheckerDefaults, BaseCodeChecker
from .any_code_checker import AnyCodeCheckerDefaults, AnyCodeChecker
from .cpp_code_checker import CppCodeCheckerDefaults, CppCodeChecker
from .python_code_checker import PythonCodeCheckerDefaults, PythonCodeChecker
from .rst_code_checker import RstCodeCheckerDefaults, RstCodeChecker
from .vhdl_code_checker import VhdlCodeCheckerDefaults, VhdlCodeChecker
from .xml_code_checker import XmlCodeCheckerDefaults, XmlCodeChecker
from .yaml_code_checker import YamlCodeCheckerDefaults, YamlCodeChecker
from .unknown_code_checker import UnknownCodeChecker
from . import utilities

from .linter_settings import LinterSettings
from .test_result import LintTestResult

# Finally include the actual linter
from .ocpi_linter import OcpiLinter
