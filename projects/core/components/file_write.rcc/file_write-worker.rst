.. file_write RCC worker

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

.. _file_write-RCC-worker:


``file_write`` RCC Worker
=========================
Application RCC worker implemented in the C language version of the RCC model. Newer RCC workers
are usually implemented in the C++ language version of the RCC model.

Detail
------

.. ocpi_documentation_worker::

   suppressWrites: Do not write any data to the file.

   countData: Check that the data is a series of 32-bit incrementing values starting at zero.

   bytesPerSecond: The data rate during the application.



