.. data_src_qadc HDL worker

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

.. _data_src_qadc-HDL-worker:


``data_src_qadc`` HDL device worker
===================================
HDL device worker implementation providing common functionality to all ADC device types.

Detail
------

The data source QADC HDL device worker receives sampled data from an ADC on
its ``dev`` devsignal port.
The worker sign-extends and justifies the samples to 16-bit real, 16-bit complex values,
which is the standard provided by the ``sample`` argument of the
``complex_short_timed_sample-prot`` protocol used by the ``out`` port.
The HDL device worker performs justification within the 16-bit values according to
the value of the ``ADC_INPUT_IS_LSB_OF_OUT_PORT`` parameter property.

The ADC samples are sent along with the ADC clock on the ``dev`` devsignal port.
The ouput port clock is driven by the ADC clock, and backpressure from the output
port’s ready signal is not expected under normal operation. When backpressure is
experienced, the ``overrun_sticky_error`` property is set to ``true``; in this
case, an ``out`` port samples message will be ended if one is in progress, and
a discontinuity message will be sent to the output port.

The ``samp_count_before_irst_samp_drop`` property
gives the number of samples before the first dropped sample and the
``num_dropped_samps`` property gives the number of samples dropped.
Be sure to check these two properties
at the end of an application run because they are not stable until then.
The worker does not use clock domain crossing (cdc) HDL primitive library circuits
for these properties because it takes advantage of the fact that they will have
a stable value by the time the OpenCPI control
plane reads them at the end of an application run.

When set to ``true``, the ``suppress_discontinuity_opcode`` property prevents the HDL device worker from
sending ``discontinuity`` opcodes.

.. Comment out ocpi_documentation_worker:: for now. It doesn't work with HdlDevice XML.

Worker ports
~~~~~~~~~~~~

Outputs:

* ``out``: Sign-extended justified 16-bit IQ samples
  
  * Type: ``StreamInterface``

  * Protocol: ``complex_short_timed_sample-prot``

  * Worker EOF: ``False``

  * InsertEOM: ``True``

  * ClockDirection: ``out``
    
  * Data width: ``OUT_PORT_DATA_WIDTH``


Utilisation
-----------
.. ocpi_documentation_utilisation::
