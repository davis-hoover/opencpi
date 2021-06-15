.. file_read HDL worker

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

:orphan:

.. _file_read-HDL-worker:


``file_read`` HDL worker
========================
Application HDL worker that only runs on FPGA simulator platforms. This worker
will not run or be built for any FPGA hardware platforms because it contains
code that cannot be realized into RTL.

Detail
------

.. ocpi_documentation_worker::

   cwd: The current working directory of the application (required for HDL worker; cannot be determined automatically).

   CWD_MAX_LENGTH: The maximum string length for ``cwd``.

.. Note: the worker directive does not currently pick up the fileName and suppressEOF SpecProperties for this worker.
   
Worker ports
~~~~~~~~~~~~
.. Worker ports (worker properties table in data sheets) are not currently picked up by the worker directive. This information is hand-coded for now.

Outputs:

* ``out``: Data streamed from file.
  
  * Type: ``StreamInterface``
    
  * Data width: ``32``  

Utilisation
-----------
.. ocpi_documentation_utilisation::
