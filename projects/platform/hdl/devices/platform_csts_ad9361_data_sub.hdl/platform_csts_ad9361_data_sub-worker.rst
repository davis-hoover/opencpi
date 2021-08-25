.. platform_ad9361_data_sub HDL worker

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

.. _platform_ad9361_data_sub-HDL-worker:


``platform_ad9361_data_sub`` HDL Worker
=======================================

Detail
------
This worker’s ``LVDS_p``, ``HALF_DUPLEX_p``, ``SINGLE_PORT_p``, and ``SWAP_PORTS_p`` build-time
configuration parameter properties
enforce build-time configuration for all of the following AD9361 data pin interface configurations
described in the `Analog Devices AD9361 Reference Manual UG570 <https://www.manualslib.com/manual/1071572/Analog-Devices-Ad9361.html>`_:

* CMOS Single Port Half Duplex
  
* CMOS Single Port Half Duplex Swapped Ports
  
* CMOS Single Port Full Duplex
  
* CMOS Single Port Full Duplex Swapped Ports
  
* CMOS Dual Port Half Duplex
  
* CMOS Dual Port Half Duplex Swapped Ports
  
* CMOS Dual Port Full Duplex
  
* CMOS Dual Port Full Duplex Swapped Ports, and • LVDS (Dual Port Full Duplex)
  
Note that the half duplex data interface formats allow for AD9361 P0/P1 port routing to be runtime-dynamic.

.. ocpi_documentation_worker::

   dev_data_dac: Interface for data bus that drives configuration-specific AD9361 pins that correspond to the TX data path, and also a signal that drives the output buffer that drives the AD9361 ``TX_FRAME_P`` pin. See the worker's OWD for details.
   dev_data_adc: Interface for data bus driven by configuration-specific AD9361 pins that correspond to the RX data path, and also a signal output of buffer whose input is the AD9361 ``RX_FRAME_p`` pin's signal. See the worker's OWD for details.
   dev_data_clk: Buffered version of the ``AD9361 DATA_CLK_P`` pin.
..   iostandard_is_lvds: Set to ``1`` if the build-time configuration specified LVDS mode; set to ``0`` otherwise.
..   p0_p1_are_swapped: Set to ``1`` if the build-time configuration inverted P0 and P1 data port roles; set to ``0`` otherwise.

Worker Configuration Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Because every possible build-time configuration parameter combination of
the AD9361 data sub HDL subdevice worker
has no control plane and no registered data paths, no registers or LUTS
are used and the ``Fmax`` measurement does not exist.


Control Timing and Signals
--------------------------
Because AD9361 data sub HDl subdevice worker does not include a control plane and serves purely as an IC pin
buffering and routing mechanism, there are no latency or clock domain considerations.
For considerations specific to the RX/TX data paths, see the supports-connected
`AD9361 ADC sub <https://opencpi.gitlab.io/releases/develop/docs/assets/AD9361_ADC_Sub.pdf>`_
and `AD9361 DAC sub <https://opencpi.gitlab.io/releases/develop/docs/assets/AD9361_DAC_Sub.pdf>`_
HDL subdevice worker descriptions.


Utilization
-----------
.. ocpi_documentation_utilization::
