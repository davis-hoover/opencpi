.. file_write HDL worker
   
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

.. _file_write-HDL-worker:


``file_write`` HDL Worker
=========================
Application HDL worker that only runs on FPGA simulator platforms. This worker
will not run or be built for any FPGA hardware platforms because it contains
code that cannot be realized into RTL.

Detail
------
.. ocpi_documentation_worker::

  cwd: The current working directory of the application (required for HDL worker; cannot be determined automatically).

  CWD_MAX_LENGTH: The maximum string length for ``cwd``.

  in: Data written to file.

Utilization
-----------
.. ocpi_documentation_utilization::
