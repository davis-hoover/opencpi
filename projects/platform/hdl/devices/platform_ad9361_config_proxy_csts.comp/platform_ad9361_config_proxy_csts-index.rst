.. platform_ad9361_config_proxy_csts documentation

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

.. _platform_ad9361_config_proxy_csts:


AD9361 Config Proxy CSTS (``platform_ad9361_config_proxy_csts``)
================================================================
Defines properties that map to functions in the Analog Devices No-OS software library
used by the proxy device worker implementation for AD9361 device control.
``platform_ad9361_config_proxy_csts`` is an asset in the ``ocpi.platform.devices`` component library
Implementations include the
:ref:`platform_ad9361_config_proxy_csts-RCC-worker` (``platform_ad9361_config_proxy_csts.rcc``).
Tested platforms include Agilent Zedboard/Analog Devices FMCOMMS2 (xilinx13 3 RCC platform only),
Agilent Zedboard/Analog Devices FMCOMMS3 (``xilinx13_3`` RCC platform only), x86/Xilinx ML605/Analog Devices
FMCOMMS2 (``centos7`` RCC platform only), x86/Xilinx ML605/Analog Devices FMCOMMS3 (``centos7`` RCC platform only),
Ettus E310 (``xilinx13_4`` RCC platform only).

Design
------

.. note::
   This component is functionally equivalent to the AD9361 Config Proxy component except that it specifies the Complex Short Timed Sample (CSTS) protocol in component port definitions instead of the Complex Short With Metadata (CSWM) protocol. The CSTS version of this component will replace the CSWM version in a future release.

This component defines the properties used by the AD9361 config proxy device worker, which is
a software wrapper for
`No-OS software library <https://wiki.analog.com/resources/eval/user-guides/ad-fmcomms2-ebz/software/no-os-functions>`_
from Analog Devices, Incorporated (ADI).
No-OS provides command and control of the `AD9361 integrated circuit (IC) <https://www.analog.com/en/products/ad9361.html#>`_
via a high-level API that ultimately controls Serial Peripheral Interface (SPI) writes to the AD9361 register set.
The component properties used by the device proxy worker implementation map one-to-one with No-OS API functions.

A block diagram representation of the implementation is given in :numref:`platform_ad9361_config_proxy_csts-diagram`

.. _platform_ad9361_config_proxy_csts-diagram:

.. figure:: platform_ad9361_config_proxy_csts_block.svg
   :align: center

   AD9361 Config Proxy CSTS HDL Device Proxy Worker Block Diagram

Interface
---------
.. literalinclude:: ../specs/ad9361_config_proxy-spec.xml
   :language: xml

Properties
~~~~~~~~~~
.. ocpi_documentation_properties::

Ports
~~~~~
.. ocpi_documentation_ports::

Implementations
---------------
.. ocpi_documentation_implementations:: ../platform_ad9361_config_proxy_csts.rcc

Example Application
-------------------
To be supplied: a meaningful example, if relevant to this type of worker.

.. literalinclude:: example_app.xml
   :language: xml

Dependencies
------------

The dependencies on other elements in OpenCPI are:

 *  ``libad9361.a`` (no-OS static library installed with OpenCPI)

There is also a dependency on:

 *  ``ad9361/sw/ad9361_api.h`` (see https://github.com/analogdevicesinc/no-os.git).

 *  `No-OS GitHub commit 8c52aa42e74841e3975a6f33cc5303ed2a67012 <https://github.com/analogdevicesinc/no-OS/commit/8c52aa42e74841e3975a6f33cc5303ed2a670124>`_ (the latest commit in the Analog Devices-recommended latest 2018 R2 release branch at the time of development.)

Limitations
-----------
Limitations of ``platform_ad9361_config_proxy_csts`` are:

 * None.

Testing
-------
No unit test for this component exists. However, a hardware-in-the-loop
application (which is *not* a unit test) exists for testing purposes (see
``projects/platform/applications/ad9361_config_proxy_test``).

.. ocpi_documentation_test_result_summary::
