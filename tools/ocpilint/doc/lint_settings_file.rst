.. This documents the linter settings files.

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


Lint Settings File
==================
The linter can be controlled through ``ocpilint-cfg.yml`` files.

This file allows the customisation of the OpenCPI lint scripts. A project can contain multiple versions of this file, at different hierarchies.

For example, there could be a version of this file at the project root, then an additional version within the ``hdl/primitives`` directory.

Whether a configuration file inherits settings from parent directories is controlled via the "inherit_parent" setting. This can be set to ``false`` to *not* inherit any settings, or to ``true`` (the default) to inherit settings from the parent directory.

.. code-block:: yaml

   inherit-parent: true

If a configuration file is specified via the command line, then those settings are used with no inheritance of settings from other files on the file system.

Additional Python Modules
-------------------------
Extra python modules may be required as dependencies in order to run the scripts present within the project or directory. If the script is not installed then an error will be raised. If the script is installed, but not listed within a settings file then a warning will be raised.

This list of modules is required, as these modules will need to be installed on any system prior to the project being able to run any custom lint rules.

.. LINT EXCEPTION: rst_002: 4: Not an rst bullet point but a yaml code sample
.. code-block:: yaml

   extra_modules:
     - xml


Additional Rules
----------------
The "extra_rules" setting defines a list of files or modules which should be imported. These files could be background code, or additional tests. These entries need to either be on the standard python path, or relative to the configuration file defining them.

.. LINT EXCEPTION: rst_002: 4: Not an rst bullet point but a yaml code sample
.. code-block:: yaml

   extra_rules:
     - project_lint.py

An example "project_lint.py" file defining some extra linting classes:

.. code-block:: python

   class MyPythonCodeChecker(ocpi_linter.PythonCodeChecker):
      pass

   class MyTestXMLCodeChecker(ocpi_linter.BaseCodeChecker):
      pass

Within the configuration file the classes to include in linting must be listed. These are defined through the "lint_classes" setting. This can be used to replace existing checking classes, or to declare additional checkers.

.. code-block:: yaml

   lint_classes:
      # As this checker is derived from a standard checker, it should be
      # replacing the class that existed previously, or else the tests would
      # be run twice.
      python: MyPythonCodeChecker
      # As this is a new checker, it is added with a unique name
      my_testxml: MyTestXMLCodeChecker


Enabling Tests
--------------
If a test is to be enabled for a set of files, or a whole project, then it can be added to this list within the configuration file. This enables a test to be run against any files present in the same directory as the configuration file, or in subdirectories (if recursive mode is specified). This setting will override any enable/disable set in any parent directories.

Enabling is done through basic rule name matching.

.. LINT EXCEPTION: rst_002: 4: Not an rst bullet point but a yaml code sample
.. code-block:: yaml

   enable_tests:
     - rst_002 # This will enable the single test called rst_002


Disabling Tests
---------------
If a test is to be disabled for a set of files, or a whole project, then it can be added to this list within the configuration file. This prevents a test from being run against any files present in the same directory as the configuration file, or in subdirectories (if recursive mode is specified). This setting will override any enable/disable set in any parent directories and overrides an enable set in the same settings file.

Disabling is done through basic rule name matching.

.. LINT EXCEPTION: rst_002: 4: Not an rst bullet point but a yaml code sample
.. code-block:: yaml

   disable_tests:
     - rst_002 # This will disable the single test called rst_002

Precedence of Enabling / Disabling Tests
----------------------------------------

 * All tests are enabled by default.

 * If a settings file disables a test, it will be disabled in that directory and any subdirectories.

 * If a settings file enables a test, it will be enabled in that directory and any subdirectories.

 * If a settings file both enables and disables a test, it will be disabled in that directory and any subdirectories. A warning will also be emitted about two conflicting rules.

As an example consider the following directory structure, where "/" is the project root, and tests "Test1" and "Test2".

.. code-block::

   /
   /foo/
   /foo/bar/:
   /foo/bar/beer/
   /qux/

The settings file in `/foo/` has:

.. LINT EXCEPTION: rst_002: 4: Not an rst bullet point but a yaml code sample
.. code-block:: yaml

   disable_tests:
      - Test1

The settings file in /foo/bar/ has:

.. LINT EXCEPTION: rst_002: 7: Not an rst bullet point but a yaml code sample
.. LINT EXCEPTION: rst_002: 4: Not an rst bullet point but a yaml code sample
.. code-block:: yaml

   enable_tests:
      - Test1
   disable_tests:
      - Test2

With the above set-up:

+---------------+---------------------+
| Directory     | Tests that will run |
+===============+=====================+
| /             | Runs both tests     |
+---------------+---------------------+
| /foo/         | Runs only Test2     |
+---------------+---------------------+
| /foo/bar      | Runs only Test1     |
+---------------+---------------------+
| /foo/bar/beer | Runs only Test1     |
+---------------+---------------------+
| /qux/         | Runs both tests     |
+---------------+---------------------+

.. spelling::
   foo
   bar
   qux

Ignoring Files
--------------
Files can also be ignored from all lint tests through ``.gitignore`` style listing. This allows for complex path ignoring rules to be defined.

*Note: if the string doesn't start with an alphanumeric character then the string should be wrapped in quotation marks.*

.. LINT EXCEPTION: rst_002: 7: Not an rst bullet point but a yaml code sample
.. LINT EXCEPTION: rst_002: 7: Not an rst bullet point but a yaml code sample
.. LINT EXCEPTION: rst_002: 7: Not an rst bullet point but a yaml code sample
.. LINT EXCEPTION: rst_002: 7: Not an rst bullet point but a yaml code sample
.. code-block:: yaml

   ignore_pattern:
     - gen/                      # Ignore a directory
     - components/**/*comp/*.svg # Ignore svg files in components documentation
     - test_log.json             # Ignore all instances of this filename
     - "*.png"                   # Ignore all instances of this extension
