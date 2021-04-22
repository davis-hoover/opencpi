.. User guide for xml_tools.parse

.. This file is protected by Copyright. Please refer to the COPYRIGHT file
   distributed with this source distribution.

   This file is part of OpenCPI <http://www.opencpi.org>

   OpenCPI is free software: you can redistribute it and/or modify it under the
   terms of the GNU Lesser General Public License as published by the Free
   Software Foundation, either version 3 of the License, or (at your option)
   any later version.

   OpenCPI is distributed in the hope that it will be useful, but WITHOUT ANY
   WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
   FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for
   more details.

   You should have received a copy of the GNU Lesser General Public License
   along with this program. If not, see <http://www.gnu.org/licenses/>.


Parse OpenXPI XML files (``xml_tools.parser``)
==============================================
A set of parsers are available for the different type of OpenCPI XML files that may need to be read.

These parsers can be used as a context manager using the ``with`` keyword in a similar way to the ``open()`` function, for example:

.. code-block:: python

   import xml_tools

   with xml_tools.parser.ComponentSpecParser(
           component_specification_path) as file_parser:
       component_specification = file_parser.get_dictionary()

OpenCPI component specification (OCS) file parser
-------------------------------------------------
.. autoclass:: xml_tools.parser.ComponentSpecParser
   :members:

OpenCPI worker definition (OWD) file parser
-------------------------------------------
.. autoclass:: xml_tools.parser.WorkerSpecParser
   :members:

OpenCPI worker build file parser
--------------------------------
.. autoclass:: xml_tools.parser.BuildParser
   :members:
