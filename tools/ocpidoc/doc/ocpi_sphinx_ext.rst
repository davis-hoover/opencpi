.. Outline OpenCPI documentation sphinx extension

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


Sphinx extension
================
The documentation generation engine used within ``ocpi_documentation`` is Sphinx, an extension is provided to automate generation of some parts of the documentation.

Automatic generation of documentation is inserted into source documentation pages using 'directives', the directives included in the ``ocpi_sphinx_ext`` are listed below.

.. _directives:

Ports directive (``ocpi_documentation_ports``)
----------------------------------------------
Will list the ports of a component, as defined in the component specification.

The directive command is ``ocpi_documentation_ports``, no arguments are needed.

The options that can be used are:

 * ``component_spec`` allows overriding the automatically determined component specification path. When used the file path of the component specification relative to the current documentation file must be provided. When not set the directory above the directory the file this directive is in, will be searched for a component specification based on the current directory's name.

Additional text to describe each port can be added in the body of the directive. This text must be the name of the port followed by a colon symbol (``:``), with each port text on a new line. Additional port text is not passed as an option of the directive, as directive option names must be known at the time of writing the directive, which for port names is not possible.

An example of using this directive, where the component specification path is automatically determined and with extra text for the ``input`` port:

.. code-block:: restructuredtext

   .. ocpi_documentation_ports::

      input: The primary input port.

Properties directive (``ocpi_documentation_properties``)
--------------------------------------------------------
Will list the properties of a component, as defined in the component specification.

The directive command is ``ocpi_documentation_properties``, no arguments are needed.

The options that can be used are:

 * ``component_spec`` allows overriding the automatically determined component specification path. When used the file path of the component specification relative to the current documentation file must be provided. When not set the directory above will be searched for a component specification based on the current directory's name.

Additional text to describe each property can be added in the body of the directive. This text must be the name of the property followed by a colon symbol (``:``), with each property text on a new line. Additional property text is not passed as an option of the directive as directive option names must be known at the time of writing the directive, which for property names is not possible.

Implementation directive (``ocpi_documentation_implementation``)
----------------------------------------------------------------
Add worker implementation detail to a components documentation page. Note this directive should be used as part of component documentation, to automatically generate worker documentation sections in worker documentation use the ``ocpi_documentation_worker`` directive.

The directive command is ``ocpi_documentation_implementation`` with a each argument listing a path to the worker directory to be listed (a limit of 10 worker implementations is set).

An example of using this directive:

.. code-block:: restructuredtext

   .. ocpi_documentation_implementation:: ../some_worker.hdl ../some_worker.rcc

Worker directive (``ocpi_documentation_worker``)
------------------------------------------------
Add worker properties and build configurations to a worker documentation. Note this directive should be used to document workers, to add worker details to a component's documentation pages use the ``ocpi_documentation_implementation`` directive.

The directive command is ``ocpi_documentation_properties``, no arguments are needed.

The options that can be used are:

 * ``worker_description`` allows overriding the automatically determined worker description XML file path. When used the file path of the worker description relative to the current documentation file must be provided. When not set the directory the current documentation file is in will be search for a worker description.

  * ``build_file`` allows overriding the automatically determined worker build file path. When used the file path of the worker build file relative to the current documentation file must be provided. When not set the directory the current documentation file is in will be search for a worker description.

Additional text to describe any worker properties can be added in the body of the directive. This text must be the name of the property followed by a colon symbol (``:``), with each property text on a new line. Additional property text is not passed as an option of the directive as directive option names must be known at the time of writing the directive, which for property names is not possible.

An example of using this directive, where the worker's description and build file paths are automatically determined:

.. code-block:: restructuredtext

   .. ocpi_documentation_worker::

Testing result summary directive (``ocpi_documentation_test_result_summary``)
-----------------------------------------------------------------------------
Adds a testing summary table to the component documentation. This directive should be used with a single occurrence of the ``ocpi_documentation_test_detail`` directive.

The directive command is ``ocpi_documentation_test_result_summary``, no arguments are needed.

The options that can be used are:

 * ``test_log`` allows overriding the automatically determined component test log file path. When used the file path of the test log relative to the current documentation file must be provided. When not set the directory the current documentation file is in will be search for a test log.

An example of using this directive, where the component's test log path is automatically determined:

.. code-block:: restructuredtext

   .. ocpi_documentation_test_result_summary::

If this directive is not used with ``ocpi_documentation_test_detail`` then the links this directive creates will not be resolved.

Testing detail directive (``ocpi_documentation_testing_summary``)
-----------------------------------------------------------------
Lists, as sections, the different test cases and subcases. This directive provides the destination of the links generated by the ``ocpi_documentation_test_result_summary`` directive.

The directive command is ``ocpi_documentation_testing_summary``, no arguments are needed.

The options that can be used are:

 * ``test_log`` allows overriding the automatically determined component test log file path. When used the file path of the test log relative to the current documentation file must be provided. When not set the directory the current documentation file is in will be search for a test log.

An example of using this directive, where the component's test log path is automatically determined:

.. code-block:: restructuredtext

   .. ocpi_documentation_testing_summary::

Dependencies directive (``ocpi_documentation_dependencies``)
------------------------------------------------------------
**CURRENTLY NOT IMPLEMENTED**

Utilization directive (``ocpi_documentation_utilization``)
----------------------------------------------------------
**CURRENTLY NOT IMPLEMENTED**
