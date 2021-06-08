.. data_sink_qdac HDL worker

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

.. _data_sink_qdac-HDL-worker:


``data_sink_qdac`` HDL device worker
====================================
HDL device worker implementation providing common functionality to all DAC device types.

Detail
------
Be sure to check the ``samp_count_before_first_underrun`` and ``num_underruns`` properties
at the end of an application run because they are not stable until then.  The worker does not use
clock domain crossing (cdc) HDL primitive library circuits
for these properties because it takes
advantage of the fact that they will have a stable value by the time the OpenCPI control
plane reads them at the end of an application run.

.. Comment out ocpi_documentation_worker:: for now. It doesn't work with HdlDevice XML.

Worker ports
~~~~~~~~~~~~

Inputs:

* ``in``: Size defined by ``IN_PORT_DATA_WIDTH``.
  
  * Type: ``StreamInterface``

  * Protocol: ``ComplexShortWithMetadata-prot``

  * Worker EOF: ``False``

  * InsertEOM: ``False``

  * ClockDirection: ``out``
    
  * Data width: ``IN_PORT_DATA_WIDTH``

Outputs:

* ``on_off``: See the *OpenCPI HDL Development Guide* for instructions on calculating the default value.
  
  * Type: ``StreamInterface``

  * Protocol: ``tx-event-prot``

  * Worker EOF: ``False``

  * InsertEOM: ``False``

  * Clock: ``in``
    
  * Data width: See the *OpenCPI HDL Development Guide* for instructions on calculating the default value.


Utilisation
-----------
.. ocpi_documentation_utilisation::
