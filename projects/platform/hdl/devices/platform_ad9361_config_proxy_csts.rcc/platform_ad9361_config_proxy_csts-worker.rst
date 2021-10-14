.. platform_ad9361_config_proxy_csts RCC worker

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

.. _platform_ad9361_config_proxy_csts-RCC-worker:


``platform_ad9361_config_proxy_csts`` RCC Worker
================================================

Detail
------
.. note::
   
   This device proxy worker is functionally equivalent to the AD9361 Config Proxy device proxy worker except that it specifies the Complex Short Timed Sample (CSTS) protocol in port definitions instead of the Complex Short With Metadata (CSWM) protocol. The CSTS version of this worker will replace the CSWM version in a future release.


No-OS features *platform layers*, which are ``.c``/``.h`` files that implement
hardware-specific SPI register accesses within generic API calls.
No-OS includes several platform layers, which are all specific to
the `Analog Devices HDL design <https://github.com/analogdevicesinc/hdl>`_.
To facilitate the use of No-OS with OpenCPI,
the ``platform_ad9361_config_proxy_csts.rcc`` code
implements a new platform layer (via the files
``ad9361_platform.cc``, ``ad9361_platform.h``, and ``parameter.h``) that
provides OpenCPI-specific functionality for SPI access via slave device property
reads/writes.

This worker implements every No-OS API call as a property, with
the matching ``ad9361 get...()`` / ``ad9361 set...()`` API calls collapsed
into a single volatile and writable ``platform_ad9361_config_proxy_csts.rcc`` property.
Each property’s type(s)/data structure(s) maps directly to the
type(s)/data structure(s) passed as argument(s) to that property’s
analogous No-OS function. The only exceptions to this methodology are:

* The No-OS ``ad9361 do mcs()`` function is not implemented as a worker property since it performs a multi-chip- sync operation which cannot currently be verified.
  
* The No-OS ``ad9361_set_rx_fir_config()`` / ``ad9361_get_rx_fir_config()`` and ``ad9361_set_tx_fir_config()`` / ``ad9361_get_tx_fir_config()`` functions are implemented as separate ``rx_fir_config_write`` / ``rx_fir_config_read`` and ``tx_fir_config_write`` / ``tx_fir_config_read`` properties, respectively, instead of collapsed into a single ``rx_fir_config`` and ``tx_fir_config`` properties due to the fact that the ``...get...()`` calls ignore the ``...path clks`` and ``bandwidth struct`` members, whereas the ``..set..()`` calls do not. Consequently, in an attempt to avoid confusion by the end user, different structs are implemented for the write properties than are for the read properties.

The No-OS API calls often require passing integer values which,
according to the No-OS documentation, are intended to correlate
with C macros. For example, the No-OS ``ad9361_set_rx_fir_en_dis()``
function has a argument of type ``uint8_t``, but the comments indicate
that its value should be one of the ENABLE or DISABLE ``ad9361_api.h`` integer macros:

.. code-block::

   /**
    * Enable/disable the RX FIR filter.
    * @param phy The AD9361 current state structure.
    * @param en_dis The option (ENABLE, DISABLE).
    *      Accepted values:
    *	    ENABLE (1)
    *	    DISABLE ( 0 )
    * @return 0 in case of success, negative error code otherwise.
    *
    * Note: This function will/may affect the data path.
   */
   int32_t ad9361_set_rx_fir_en_dis (struct ad9361_rf_phy *phy, uint8_t_en_dis)

Because there is a strict one-to-one mapping
between No-OS API calls and ``platform_ad9361_config_proxy_csts.rcc`` properties by design, and
because No-OS passes integers as arguments instead of forcing strictly-enumerated types,
this worker likewise uses integer types for properties instead of enumerated ones.
To help alleviate confusion when using this worker’s properties, many
of the No-OS C macros are mapped to this worker's parameter properties,
and the property descriptions reference the parameter properties that
are intended to be used. This way, parameter properties can be read at
runtime and the values that are read can be used to set a property.
For example, the ``ad9361_set_rx_fir_en_dis`` property’s description
references the ENABLE and DISABLE parameter properties, which have values of 1 and 0, respectively.

Other worker properties provide additional functionality, including
PLL lock status, low-level PLL divider values
which can be used to validate the LO frequencies read by No-OS,
fastlock memory management (deletion), the FPGA data mode
configuration (LVDS, CMOS, etc.) via the LVDS,
``single_port``, ``swap_ports``, ``half_duplex``, ``data_rate_config`` properties,
and the ``DATA_CLK_P_rate_Hz``.

Note also that this worker’s use of No-OS not only makes
SPI register accesses but also sets the AD9361 RESETB, ENABLE,
and TXNRX pins via the ``platform_ad9361_config_csts.hdl`` and ``platform_ad9361_spi_csts.hdl`` HDL device workers.

.. ocpi_documentation_worker::

Troubleshooting
---------------
The following error message, which is produced by the ADI No-OS library used by ``platform_ad9361_config_proxy_csts.rcc``,
indicates a hardware communication error between the FPGA and the AD9361.
This message occurs, for example, if the AD9361 resides on a card that is not plugged in to the PCB containing the FPGA.

``ad9361_init : Unsupported PRODUCT_ID 0xC0ad9361_init : AD936x initialization error``
