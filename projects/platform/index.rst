.. platform top level project documentation

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

OpenCPI Platform Project
========================
Built-in OpenCPI project that contains assets useful for OpenCPI
platform development, including reference platforms and support for
generic devices.

Criteria for content to exist in this OpenCPI project is as follows:

* ``specs/``:

   * Component specs must facilitate generic device worker or platform support.
   
* ``hdl/primitives/``:

   * HDL primitives must directly support assets within ``hdl/devices``, ``hdl/cards``, or ``hdl/platforms``, or be useful and used by devices in OSPs.
  
* ``hdl/devices/``:
  
   * Generic device workers belong here.
   
   * RF ADC/DAC command/control: HDL device proxies must implement the latest-generation ``drc`` component.
   
   * ADC/DAC data flow: de-interleaving/interleaving HDL subdevice workers must support the latest-generation ADC/DAC data flow paradigm HDL device workers ``data_src_qadc.hdl`` and ``data_sink_qdac.hdl``.
   
* ``hdl/cards/``:
  
    * Reusable card specs belong here.
    
    * Card-specific HDL device workers for reusable cards belong here.
    
* ``hdl/platforms/``:
  
   * Current reference platforms (relatively inexpensive and supported with high priority with as many software and hardware options as possible) exist here. For example, ``zed``, ultrascale/ZCU104, etc.
   
   * Non-reference platforms ("full-fledged OSPs") belong in their own, separate, OpenCPI projects.


.. toctree::
   :maxdepth: 2
   :glob:

   hdl/devices/devices
   specs/specs
   hdl/platforms/zed/doc/zed-gsg
   hdl/platforms/picoevb/doc/picoevb-gsg
..    components/components
..    hdl/primitives/primitives
