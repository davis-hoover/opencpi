.. Outlines XML tools library

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


XML tools (``xml_tools``)
=========================
``xml_tools`` is a Python module to aid reading of OpenCPI XML files.

.. toctree::
   :maxdepth: 1

   parser

Use
---
``xml_tools`` is used as a library, so accessed using ``import xml_tools`` in Python testing files. Each of the pages linked in the contents above outline more detail about how to use the functionality contained within ``xml_tools``.

Requirements
------------
``xml_tools`` requires:

 * Python 3.6.

Library testing
---------------
``xml_tools`` has been tested using the Python's ``unittest`` module. Tests are most easily run by using the following command in the top most ``xml_tools`` directory:

.. code-block:: python

   python3 -m unittest
