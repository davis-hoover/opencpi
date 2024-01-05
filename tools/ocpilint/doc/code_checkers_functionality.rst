.. Outline of language code checkers functionality and structure

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


Code Checkers Functionality
===========================
For each language a specific code checker completes similar steps;

 #. An automatic formatter is applied, this will change the contents of the file being linted so that spacing and similar layout style elements are consistent.

 #. Third party automatic code checkers are applied to the file. This will report any issues identified.

 #. Additional checks are run. These are coded into the language specific code checker.

The result of linting is written to log files.

Adding Additional Checks
------------------------
All checks should be placed in the relevant language specific linter.

Checks that are automated should be a method of the linter class ``test_LANGUAGE_NNN``, where ``LANGUAGE`` is the built-in language type (``any``, ``cpp``, ``py``, ``vhdl``, ``rst``, ``xml``, ``yaml`` or ``unknown``) and ``NNN`` is the test index. The method must return a pair of variables ``test_name`` and ``issues``. ``test_name`` is a string of the test name. ``issues`` is a list of dictionaries, where each entry in the list outlines where and how the source code has failed the test, with keys ``line`` for source code line number and ``message``. If the test passes then ``issues`` should be a list of length 0 (i.e. ``[]``).

By naming additional tests in the way outlined above they will be called automatically whenever the relevant file type is being linted.

To aid test implementation the class member ``self._code`` is a list of strings, where each entry in the list is a line in the source code file.
