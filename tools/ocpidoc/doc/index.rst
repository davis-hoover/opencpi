.. ocpi_documentation documentation

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


OpenCPI asset documentation generator (``ocpi_documentation``)
==============================================================
``ocpi_documentation`` is a Python module for building and managing documentation of OpenCPI projects and artefacts.

The main parts that make up the documentation generator are:

.. toctree::
   :maxdepth: 1

   ocpi_sphinx_ext

Installing
----------
``ocpi_documentation`` is written for and tested with Python 3.6 - newer versions may work, older versions are not expected to. Python must be installed before attempting to install ``ocpi_documentation``.

To install ``ocpi_documentation`` use the command:

.. code-block:: bash

   pip3 install --user ./

Alternatively, when ``pip3`` is not installed:

.. code-block:: bash

   python3 setup.py install

Depending on your setup you may need to run the above command with ``sudo``.

Use
---
Once installed the documentation generator can be run using the command:

.. code-block:: bash

   ocpidoc [options] OPERATION [operation specific options]

The possible ``OPERATION`` values are:

 * ``create`` which will create a documentation templates for the documentation type specified. When using ``create`` the documentation type and name must also be specified.

 * ``build`` which will build the documentation.

 * ``clean`` which will delete built documentation files.

Options that are valid for all ``OPERATION`` values are:

 * ``-d`` / ``--directory`` to specify the operation to happen in a specific directory, if not set the current directory will be used.

 * ``-h`` / ``--help`` to display the help. This can be specified with each ``OPERATION`` value to display the help associated to that operation (e.g. ``ocpi_doc build --help``).

Sphinx extensions are uses to enable the automatic generation of parts of the documentation, this is achieved using :ref:`directives <directives>`.

Requirements
------------
``ocpi_documentation`` requires:

 * Python 3.6.

 * Sphinx and all its dependencies.

 * ``sphinxcontrib.spelling`` and all its dependencies.

 * ``sphinx-rtd-theme``

 * ``xml_tools`` which is part of the the OpenCPI Python tools.

Library testing
---------------
``ocpi_documentation`` has been tested using the Python ``unittest`` module. Tests are most easily run by using the following command in the top most ``ocpi_documentation`` directory:

.. code-block:: python

   python3 -m unittest
