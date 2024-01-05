.. Language agnostic code checker outline

.. This file is protected by Copyright. Please refer to the COPYRIGHT file
   distributed with this source distribution.

   This file is part of OpenCPI <http://www.opencpi.org>

   OpenCPI is free software: you can redistribute it and/or modify it under the
   terms of the GNU Lesser General Public License as published by the Free
   Software Foundation, either version 3 of the License, or (at your option) any
   later version.

   OpenCPI is distributed in the hope that it will be useful, but WITHOUT ANY
   WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
   A PARTICULAR PURPOSE. See the GNU Lesser General Public License for
   more details.

   You should have received a copy of the GNU Lesser General Public License
   along with this program. If not, see <http://www.gnu.org/licenses/>.


Language Agnostic Code Checker (``ocpi_linter.AnyCodeChecker``)
===============================================================
Code checker for checks that are not language specific.

Checking of a file will normally be done by using the command line instruction ``ocpilint``. This checker is applied to all files regardless of the language.

Tests
-----

.. autoclass:: ocpi_linter.any_code_checker.AnyCodeChecker
   :members:
