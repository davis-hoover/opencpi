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

.. comment out the ocpi_documentation_worker directive for now. It doesn't recognize HdlDevice.

Worker Ports
~~~~~~~~~~~~

.. this is hand-entered for now to suggest a format that the XML parser might use to automatically generate it.

.. this source does not contain the configuration data path details given in the data sheet.

Outputs:

* ``dev_data_dac``: Data bus that drives configuration-specific AD9361 pins that correspond to the TX data path. See the worker's OWD for details.

  * Type: ``DevSignal``

  * Count: ``1``

  * Optional: ``true``

  * Master: ``false``

  * Signal: ``data``

  * Width: ``24``

* ``dev_data_dac``: Signal that drives the output buffer that drives the AD9361 ``TX_FRAME_P`` pin.

  * Type: ``DevSignal``

  * Count: ``1``

  * Optional: ``true``

  * Master: ``false``

  * Signal: ``tx_frame``

  * Width: ``1``

* ``dev_txen_dat``: Description to be supplied.

  * Type: ``DevSignal``

  * Count: ``1``

  * Optional: ``true``

  * Master: ``false``

  * Signal: ``txen``

  * Width: ``1``

Inputs:

* ``dev_cfg_data_port``: Description to be supplied.

  * Type: ``DevSignal``

  * Count: ``1``

  * Optional: ``false``

  * Master: ``false``

  * Signals:

    * ``iostandard_is_lvds``: Set to ``1`` if the build-time configuration specified LVDS mode; set to ``0`` otherwise.

    * ``p0_p1_are_swapped``: Set to ``1`` if the build-time configuration inverted P0 and P1 data port roles; set to ``0`` otherwise.

  * Width: ``1``

* ``dev_data_clk``: Buffered version of the ``AD9361 DATA_CLK_P`` pin.

  * Type: ``DevSignal``

  * Count: ``3``

  * Optional: ``true``

  * Master: ``false``

  * Signal: ``DATA_CLK_P``

  * Width: ``1``
  
* ``dev_data_adc``: Data bus driven by configuration-specific AD9361 pins that correspond to the RX data path. See the worker's OWD for details.

  * Type: ``DevSignal``

  * Count: ``1``

  * Optional: ``true``

  * Master: ``false``

  * Signal: ``data``

  * Width: ``24``

* ``dev_data_adc``: Output buffer whose input is the AD9361 ``RX_FRAME_P`` pin's signal.

  * Type: ``DevSignal``

  * Count: ``1``

  * Optional: ``true``

  * Master: ``false``

  * Signal: ``rx_frame``

  * Width: ``1``

* ``dev_rxen_config``: Description to be supplied.

  * Type: ``DevSignal``

  * Count: ``1``

  * Optional: ``true``

  * Master: ``false``

  * Signal: ``rxen``

  * Width: ``1``
    
* ``dev_txen_config``: Description to be supplied.

  * Type: ``DevSignal``

  * Count: ``1``

  * Optional: ``true``

  * Master: ``false``

  * Signal: ``txen``

  * Width: ``1``

SubDevice Connections
~~~~~~~~~~~~~~~~~~~~~

* Worker port ``dev_cfg_data_port``:

  * Port index: 0

  * Worker supported: ``ad9361_config``

  * Worker port supported: ``dev_cfg_data_port``

* Worker port ``dev_rxen_config``:

  * Port index: 0

  * Worker supported: ``ad9361_config``

  * Worker port supported: ``dev_rxen_data_sub``

* Worker port ``dev_txen_config``:

  * Port index: 0

  * Worker supported: ``ad9361_config``

  * Worker port supported: ``dev_txen_data_sub``

* Worker port ``dev_data_adc``:

  * Port index: 2

  * Worker supported: ``ad9361_config``

  * Worker port supported: ``dev_data_clk``

* Worker port ``dev_data_clk``:

  * Port index: 0

  * Worker supported: ``ad9361_adc_sub``

  * Worker port supported: ``dev_data_clk``

* Worker port ``dev_data_adc``:

  * Port index: 0

  * Worker supported: ``ad9361_adc_sub``

  * Worker port supported: ``dev_data_from_pins``

* Worker port ``dev_data_clk``:

  * Index: 1

  * Worker supported: ``ad9361_dac_sub``

  * Worker port supported: ``dev_data_clk``

* Worker port ``dev_data_adc``:

  * Port index: 0

  * Worker supported: ``ad9361_dac_sub``

  * Worker port supported: ``dev_data_to_pins``


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
