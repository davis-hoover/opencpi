.. OpenCPI Component linter documentation.

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


OpenCPI Component Linter (``ocpi_linter``)
==========================================
To help ensure code written for OpenCPI components meets the coding guidelines of the community, a set of linters and code checkers is available.

Here the term linter is used to cover linter, code style checks, static code checks and automatic formatting on any language.

.. toctree::
   :maxdepth: 1

   any_code_checker
   cpp_code_checker
   python_code_checker
   rst_code_checker
   vhdl_code_checker
   xml_code_checker
   yaml_code_checker
   unknown_code_checker
   code_checkers_functionality
   lint_settings_file

Installing
----------
``ocpi_linter`` is written for and tested with Python 3.6 - newer versions may work, older versions are not expected to. Python must be installed before attempting to install ``ocpi_linter``.

To install ``ocpi_linter`` if you have ``pip3`` installed, from the ``ocpi_linter`` directory (which contains ``setup.py``) use the command:

.. code-block:: bash

   pip3 install --user ./

Alternatively if you do not have ``pip3`` installed Python can be used directly:

.. code-block:: bash

   python3 setup.py install

Depending on your set-up you may need to run the above command as ``sudo``.

Requirements
------------
``ocpi_linter`` requires:

 * Python 3.6.

 * ``clang-format`` to run all tests for C++ files.

 * ``cpplint`` to run all tests for C++ files.

 * ``cppcheck`` to run all tests for C++ files.

 * ``autopep8`` to run all tests for Python files.

 * ``pycodestyle`` to run all tests for Python files.

 * ``pydocstyle`` to run all tests for Python files.

 * ``emacs`` to run all tests for VHDL files.

 * ``xmllint`` to run all tests for XML files.

 * ``git``

Usage
-----
Once installed the linter can be run using the command:

.. code-block:: bash

   ocpilint PATH

``PATH`` can be a file, directory or glob pattern.

.. LINT EXCEPTION: any_001: 12: This is the option, not a default comment.

Options available are:

 * ``-h`` / ``--help``: Shows a help message.

 * ``--junit [JUNIT]``: Generate a JUnit compatible test report, with the defined filename (if no filename is provided then defaults to: ``lint_report.xml``).

 * ``-r`` / ``--recursively``: When path is a directory, search recursively.

 * ``-n`` / ``--no-ignore``: Prevents ignore lists from being used (cannot be used with --ignore-unrecognised).

 * ``-u`` / ``--ignore-unrecognised``: Ignore files with unrecognised extensions, as opposed to marking as a lint error.

 * ``-s SETTINGS`` / ``--settings SETTINGS``: Override directory lint configuration searching with the named yaml file ``SETTINGS``.

 * ``--skeleton``: Copies an empty lint configuration file to the path defined as ``PATH``, then quits (if no path provided then defaults to: ``./ocpilint-cfg.yml``).

 * ``--verbose``: Stores a processing log to: ./lint_log_debug.log.


Marking Exceptions
~~~~~~~~~~~~~~~~~~
Exceptions from a specific linter check can be marked in the source code using a comment of the form ``<comment_symbol> LINT EXCEPTION: <test_number>: <line_offset>: <optional: reason>``, leading spaces are permitted but this must be the first text on the line. Where:

 * ``<comment_symbol>`` is the symbol(s) used to mark the start of a comment line (e.g. ``//`` for C++).

 * ``<test_number>`` is the test number being marked as having an exception, usually these are in a ``<language>_<number>`` format (e.g. ``cpp_004`` for test 004 of C++ checks, ``any_001`` for test 001 of the language agnostic checks).

 * ``<line_offset>`` is the offset from the current line below that the exception applies to (e.g. ``1`` would indicate the exception applies to the next line). Best practice is to keep this as small as possible. This is provided so small blocks of linked code do not have to be broken by a linter exception comment, and to allow multiple exceptions to be applied to a single line since only one exception comment can be given on each line.

 * ``<optional: reason>`` this is an optional field which allows a comment to be included as to why the linter exception is needed. Best practice is to include this.


Lint Settings
~~~~~~~~~~~~~
The linter operation can have it's behaviour customised for a project, or sub-directory within a project. This is achieved through searching for settings files, with the name ``ocpilint-cfg.yml``. These are YAML files containing configurations which are appended to any existing rule-sets provided (this follows the same principle as ``.gitignore`` files).

These files are covered in detail within :doc:`lint_settings_file`.
