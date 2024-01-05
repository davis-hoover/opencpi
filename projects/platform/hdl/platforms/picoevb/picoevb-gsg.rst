.. picoevb_gsg PicoEVB Getting Started Guide documentation

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


.. _picoevb_gsg:


.. |trade| unicode:: U+2122
   :ltrim:

.. |reg| unicode:: U+00AE
   :ltrim:

      
OpenCPI RHS Research PicoEVB Getting Started Guide
==================================================
.. csv-table:: Revision History
   :header: "OpenCPI Version", "Description of Change", "Date"
   :widths: 10,30,10
   :class: tight-table

   "v2.3.0", "Initial PicoEVB release", "8/2021"
   "v2.4.x", "update to refer to User and Install Guides", "12/2022"

How to Use This Document
------------------------
This document provides installation information that is specific
to the RHS Research\ |trade| PicoEVB.  Use this document when performing the tasks described
in the chapter "Setting up PCI Express-based HDL Platforms"
in the `OpenCPI Installation Guide <https://opencpi.gitlab.io/releases/latest/docs/OpenCPI_Installation_Guide.pdf>`_.
This document supplies details about enabling OpenCPI development and execution for the PicoEVB
that can be applied to the procedures described in the referenced *OpenCPI Installation Guide* chapter.
The recommended method is to have the *OpenCPI Installation Guide* and this document
open in separate windows and refer to this document for any platform-specific details
while following the OpenCPI setup tasks described in the Installation Guide.

The following documents can also be used as reference to the tasks described in this document:

* `OpenCPI User Guide <https://opencpi.gitlab.io/releases/latest/docs/OpenCPI_User_Guide.pdf>`_
  
* `OpenCPI Glossary <https://opencpi.gitlab.io/releases/latest/docs/OpenCPI_Glossary.pdf>`_

Note that the *OpenCPI Glossary* is also contained in both the *OpenCPI Installation Guide* and the
*OpenCPI User Guide*.

This document assumes a basic understanding of standard PC motherboard connections, as well as the Linux command line (or "shell") environment.

Overview 
--------
The PicoEVB is a low-cost FPGA device from RHS Research\ |trade|. The board is designed around the Xilinx\ |reg| Artix 7 (XC7A50T) FPGA
with a PCI Express (PCIe) x1 interface.  The PicoEVB works in the following slots:

* M.2 2230 Key A
* M.2 2230 Key E
* M.2 2280 Key M
* Full length mini PCIe (with carrier board)
* PCIe x1, x4, x8, or x16 slot (with carrier board)

See the RHS Research website `<https://rhsresearch.com/>`_
for more information about the PicoEVB device.  In OpenCPI, the HDL (FPGA) platform 
for the PicoEVB is called the "``picoevb``".

Installation Prerequisites
--------------------------
:numref:`picoevb-hw` lists the items required for setting up the PicoEVB for 
OpenCPI installation and deployment.

.. _picoevb-hw:

.. csv-table:: Hardware Items Required for PicoEVB HDL Platform
   :header: "Item", "Usage"
   :widths: 40,60
   :class: tight-table

   "PicoEVB", "OpenCPI target HDL platform"
   "M.2 PCIe carrier board", "M.2 to PCIe for connecting to PCIe edge slot"
   "Development host system", "Development host running OpenCPI"
   "4x2 USB-to-JTAG connector cable", "Connection between motherboard USB hub and PicoEVB"

.. _picoevb-sw:

.. csv-table:: Software Items Required for PicoEVB HDL Platform
   :header: "Item", "Usage"
   :widths: 40,60
   :class: tight-table

   "CentOS 7 operating system", "Builds FPGA artifacts for PicoEVB"
   "Xilinx Vivado 2019.2", "Builds FPGA artifacts for PicoEVB"
   "OpenCPI installed on development host system", "OpenCPI builds, development, and deployment"

See the `OpenCPI Installation Guide <https://opencpi.gitlab.io/releases/latest/docs/OpenCPI_Installation_Guide.pdf>`_
for detailed installation instructions for OpenCPI.

Note that the PicoEVB HDL platform does not have an embedded RCC platform.
The development host controls the FPGA resources directly via the PCIe interface.

Installation Summary
--------------------
To set up the PicoEVB for OpenCPI application development and execution,
perform the following steps:

* Install the PicoEVB board on the development host

* Install the OpenCPI PicoEVB HDL platform

* Build the required HDL assemblies
  
* Prepare and program the PicoEVB flash

* If necessary, reserve additional memory for the OpenCPI Linux kernel device driver

* Load the OpenCPI Linux kernel device driver
  
* Run the reference applications

Installing the PicoEVB Board
----------------------------
To physically install the board on the development host:

* Connect the PicoEVB to the M.2 PCIe carrier board. If the M.2 slot is readily available on the development host, the carrier board is not required.

* Connect the 8-pin USB port on the PicoEVB to an internal USB port on the motherboard of the development host using a standard 4x2 USB-to-JTAG connector cable.

Installing the OpenCPI HDL Platform
-----------------------------------
To install and build the OpenCPI HDL platform for the PicoEVB on the development host:

* Follow the instructions in the "Installing Xilinx Tools" section of the “Installing Third-party/Vendor Tools” chapter within the `OpenCPI Installation Guide <https://opencpi.gitlab.io/releases/latest/docs/OpenCPI_Installation_Guide.pdf>`_ to install the Xilinx tools listed as platform dependencies for the ``picoevb`` HDL platform in the "Table of Supported Platforms" in the guide.

* Follow the instructions in the section “Installation Steps for Platforms” in the `OpenCPI Installation Guide <https://opencpi.gitlab.io/releases/latest/docs/OpenCPI_Installation_Guide.pdf>`_ to install and build the ``picoevb`` HDL platform with the `ocpiadmin(1) tool <https://opencpi.gitlab.io/releases/latest/man/ocpidriver.1.html>`_. Building this HDL platform builds the items necessary to build HDL assemblies and run applications on the platform.

Building the Test HDL Assembiles
--------------------------------
Next, on the development host, build the HDL assemblies required for running the ``test_source_sink`` and ``test_source_to_dev_null`` reference applications. The ``test_source_sink`` application requires the ``test_internal_assy`` HDL assembly, while the ``test_source_to_dev_null`` application requires the ``test_source_assy`` HDL assembly.

* Navigate to the ``test_internal_assembly`` directory, and build the HDL assembly for the ``picoevb`` HDL platform:

.. code-block:: bash

   cd opencpi/projects/assets/hdl/assemblies/test_internal_assy
   ocpidev build --hdl-platform picoevb

* Navigate to the ``test_source_assy`` assembly directory, and build the HDL assembly for the ``picoevb`` HDL platform:

.. code-block:: bash

   cd opencpi/projects/assets/hdl/assemblies/test_source_assy
   ocpidev build --hdl-platform picoevb

Building each assembly takes several minutes to complete.  The ``test_source_assy`` assembly is used
in the next section to program the FPGA's flash memory.  This is a one-time setup step that enables
enumeration of the PicoEVB on the PCIe bus when the development host is booted.

Preparing and Programming the PicoEVB Flash
-------------------------------------------
The ``picoevb`` HDL platform must initially be programmed with an OpenCPI-compliant assembly.  Therefore, a precompiled version of OpenOCD \ |trade| JTAG utility is included with the OpenCPI distribution to facilitate JTAG programming of the flash.  Perform the following steps to unzip the compressed OpenOCD executable and perform initial FPGA flash programming from the development host.

* Unzip the OpenOCD executable as follows:

.. code-block:: bash
   
   cd opencpi/runtime/hdl-support/xilinx/cfgFiles_openocd
   
   bzip2 -dk openocd.bz2

* Program the picoevb's FPGA flash as follows:

.. code-block:: bash

   cd opencpi/projects/platform/hdl/platforms/picoevb

   ./loadFlash_picoevb ../../../../assets/hdl/assemblies/test_source_assy/container-test_source_assy_picoevb_base/target-artix7/test_source_assy_picoevb_base.bit 

The output should look similar to the following:

.. code-block:: bash

   Input bit file : ../../../../assets/hdl/assemblies/test_source_assy/container-test_source_assy_picoevb_base/target-artix7/test_source_assy_picoevb_base.bit
   
   Flash write operations started...
      NOTE: This may take several minutes
   Sun Aug  8 11:39:00 EDT 2021
   
   Open On-Chip Debugger 0.10.0+dev-01514-ga8edbd020-dirty (2020-11-29-22:43)
   Licensed under GNU GPL v2
   For bug reports, read
      http://openocd.org/doc/doxygen/bugs.html
   debug_level: 2
   
   Info : only one transport option; autoselect 'jtag'
   Warn : Transport "jtag" was already selected
   Info : clock speed 3000 kHz
   Info : JTAG tap: xc7.tap tap/device found: 0x0362c093 (mfg: 0x049 (Xilinx), part: 0x362c, ver: 0x0)
   Info : JTAG tap: xc7.tap tap/device found: 0x0362c093 (mfg: 0x049 (Xilinx), part: 0x362c, ver: 0x0)
   Info : Found flash device 'sp s25fl132k' (ID 0x00164001)
   Info : Found flash device 'sp s25fl132k' (ID 0x00164001)
   Info : Found flash device 'sp s25fl132k' (ID 0x00164001)
   Info : Found flash device 'sp s25fl132k' (ID 0x00164001)
   Info : sector 0 took 377 ms
   Info : sector 1 took 386 ms
   Info : sector 2 took 406 ms
   Info : sector 3 took 396 ms
   Info : sector 4 took 420 ms
   Info : sector 5 took 392 ms
   Info : sector 6 took 364 ms
   Info : sector 7 took 366 ms
   Info : sector 8 took 396 ms
   Info : sector 9 took 380 ms
   Info : sector 10 took 390 ms
   Info : sector 11 took 424 ms
   Info : sector 12 took 405 ms
   Info : sector 13 took 364 ms
   Info : sector 14 took 368 ms
   Info : sector 15 took 358 ms
   Info : sector 16 took 348 ms
   Info : sector 17 took 328 ms
   Info : sector 18 took 334 ms
   Info : sector 19 took 346 ms
   Info : sector 20 took 328 ms
   Info : sector 21 took 390 ms
   Checking for QSPI capable flash
   
   Found S25FL
   
   Enabling QSPI write for sp s25fl132k
   
   Info : Found flash device 'sp s25fl132k' (ID 0x00164001)
   shutdown command invoked
   Flash write operations successful!
   Sun Aug  8 11:42:06 EDT 2021

With the FPGA flash programmed, the development host must be power-cycled for the PCIe interface of the ``picoevb`` to be enumerated in the BIOS.

Reserving Additional Memory for the OpenCPI Linux Kernel Device Driver
----------------------------------------------------------------------
If additional memory for DMA-based communication on the PCIe system is required, follow the
instructions in the section "Reserving Additional Memory for the Linux Kernel Device Driver" in the 
`OpenCPI User Guide <https://opencpi.gitlab.io/releases/latest/docs/OpenCPI_User_Guide.pdf>`_ to reserve it.

Loading the OpenCPI Linux Kernel Device Driver
----------------------------------------------
Follow the instructions in the section "Check and Load OpenCPI Linux Kernel Device Driver" in the
section "Setting up PCI Express-based HDL Platforms"
in the `OpenCPI Installation Guide <https://opencpi.gitlab.io/releases/latest/docs/OpenCPI_Installation_Guide.pdf>`_
to check and load the OpenCPI Linux kernel device driver.
Also see the `ocpidriver(1) man page <https://opencpi.gitlab.io/releases/latest/man/ocpidriver.1.html>`_ for command usage details.

Running the Reference Applications
----------------------------------
Before running the reference applications, the ``OCPI_LIBRARY_PATH``
variable must be set properly via the command line.  Run the following command, replacing ``sandbox`` with the path where you previously cloned, built, and installed OpenCPI:

.. code-block:: bash

   export OCPI_LIBRARY_PATH=$OCPI_LIBRARY_PATH:/sandbox/opencpi/projects/assets/artifacts/
   export OCPI_LIBRARY_PATH=$OCPI_LIBRARY_PATH:/sandbox/opencpi/projects/core/artifacts/


We are now ready to run the reference applications.  Each of the following applications are run from the applications directory under the assets projects (``opencpi/projects/assets/applications``).  Navigate to the applications directory to run each of the following reference applications.

* **Reference Application 1: test_source_to_dev_null.xml**

.. code-block:: bash

   ocpirun -v -d -m test_source=hdl -m file_write=rcc -p test_source=valuestosend=8388608 -p file_write=filename=./test.output test_source_to_dev_null.xml 

The output should look similar to the following:

.. code-block:: bash

   Available containers are:  0: PCI:0000:04:00.0 [model: hdl os:  platform: picoevb], 1: rcc0 [model: rcc os: linux platform: centos7]
   Actual deployment is:
     Instance  0 test_source (spec ocpi.assets.util_comps.test_source) on hdl container 0: PCI:0000:04:00.0, using test_source/a/test_source in /home/sandbox/opencpi/projects/assets/artifacts//ocpi.assets.test_source_assy_picoevb_base.hdl.0.picoevb.bitz dated Wed Aug  4 13:08:53 2021
     Instance  1 file_write (spec ocpi.core.file_write) on rcc container 1: rcc0, using file_write in /home/sandbox/opencpi/projects/core/artifacts//ocpi.core.file_write.rcc.0.centos7.so dated Tue Jun 15 10:59:09 2021
   Application XML parsed and deployments (containers and artifacts) chosen [0 s 86 ms]
   Application established: containers, workers, connections all created [0 s 2 ms]
   Dump of all initial property values:
   Property   0: test_source.clockDivisor = "1" (cached)
   Property   1: test_source.valuesToSend = "8388608" (cached)
   Property   2: test_source.suppressWrites = "false"
   Property   3: test_source.countBeforeBackpressure = "4294967295"
   Property   4: test_source.valuesSent = "0"
   Property   8: test_source.fraction = "0"
   Property   9: test_source.timed = "false"
   Property  10: test_source.time_to_send = "0"
   Property  19: file_write.fileName = "./test.output" (cached)
   Property  20: file_write.messagesInFile = "false" (cached)
   Property  21: file_write.bytesWritten = "0"
   Property  22: file_write.messagesWritten = "0"
   Property  23: file_write.stopOnEOF = "true" (cached)
   Property  27: file_write.suppressWrites = "false"
   Property  28: file_write.countData = "false"
   Property  29: file_write.bytesPerSecond = "0"
   Application started/running [0 s 7 ms]
   Waiting for application to finish (no time limit)
   Application finished [0 s 90 ms]
   Dump of all final property values:
   Property   0: test_source.clockDivisor = "1" (cached)
   Property   1: test_source.valuesToSend = "8388608" (cached)
   Property   2: test_source.suppressWrites = "false" (cached)
   Property   3: test_source.countBeforeBackpressure = "4100"
   Property   4: test_source.valuesSent = "8388608"
   Property   8: test_source.fraction = "0" (cached)
   Property   9: test_source.timed = "false" (cached)
   Property  10: test_source.time_to_send = "0"
   Property  19: file_write.fileName = "./test.output" (cached)
   Property  20: file_write.messagesInFile = "false" (cached)
   Property  21: file_write.bytesWritten = "33554432"
   Property  22: file_write.messagesWritten = "4096"
   Property  23: file_write.stopOnEOF = "true" (cached)
   Property  27: file_write.suppressWrites = "false" (cached)
   Property  28: file_write.countData = "false" (cached)
   Property  29: file_write.bytesPerSecond = "401032579"


Note that the ``picoevb`` platform container was selected and chosen for the ``test_source`` component, while the ``centos7`` RCC worker was chosen for the ``file_write`` component.  Also note that 8388608 values (each consisting of 4 bytes) were sent to the ``file_write`` component and written to the file ``test.output``.  Next, verify that the ``test.output`` file is the correct size of (4 x 8388608) bytes, or 32MB :

.. code-block:: bash

   ls test.output -sh
   32M test.output

* **Reference Application 2: test_source_sink.xml**

.. code-block:: bash

   ocpirun -v -d -m test_source=hdl -Ptest_source=picoevb -p test_source=valuestosend=8388608 test_source_sink.xml  --duration=2 

The output should look similar to the following:

.. code-block:: bash

   Available containers are:  0: PCI:0000:04:00.0 [model: hdl os:  platform: picoevb], 1: rcc0 [model: rcc os: linux platform: centos7]
   Actual deployment is:
     Instance  0 test_source (spec ocpi.assets.util_comps.test_source) on hdl container 0: PCI:0000:04:00.0, using test_source/a/test_source in /home/sanndbox/opencpi/projects/assets/artifacts//ocpi.assets.test_internal_assy_picoevb_base.hdl.0.picoevb.bitz dated Tue Jun 29 11:49:06 2021
     Instance  1 test_sink (spec ocpi.assets.util_comps.test_sink) on hdl container 0: PCI:0000:04:00.0, using test_sink/a/test_sink in /home/sandbox/opencpi/projects/assets/artifacts//ocpi.assets.test_internal_assy_picoevb_base.hdl.0.picoevb.bitz dated Tue Jun 29 11:49:06 2021
   Application XML parsed and deployments (containers and artifacts) chosen [0 s 84 ms]
   Application established: containers, workers, connections all created [0 s 0 ms]
   Dump of all initial property values:
   Property   0: test_source.clockDivisor = "1" (cached)
   Property   1: test_source.valuesToSend = "8388608" (cached)
   Property   2: test_source.suppressWrites = "false"
   Property   3: test_source.countBeforeBackpressure = "4294967295"
   Property   4: test_source.valuesSent = "0"
   Property   8: test_source.fraction = "0"
   Property   9: test_source.timed = "false"
   Property  10: test_source.time_to_send = "0"
   Property  19: test_sink.countError = "false"
   Property  20: test_sink.valuesReceived = "0"
   Property  21: test_sink.timeFirst = "0"
   Property  22: test_sink.timeEOF = "0"
   Property  23: test_sink.suppressReads = "false"
   Application started/running [0 s 0 ms]
   Waiting for up to 2 seconds for application to finish
   Application is now considered finished after waiting 2 seconds [2 s 2 ms]
   Dump of all final property values:
   Property   0: test_source.clockDivisor = "1" (cached)
   Property   1: test_source.valuesToSend = "8388608" (cached)
   Property   2: test_source.suppressWrites = "false" (cached)
   Property   3: test_source.countBeforeBackpressure = "4294967295"
   Property   4: test_source.valuesSent = "8388608"
   Property   8: test_source.fraction = "0" (cached)
   Property   9: test_source.timed = "false" (cached)
   Property  10: test_source.time_to_send = "0"
   Property  19: test_sink.countError = "false"
   Property  20: test_sink.valuesReceived = "8388608"
   Property  21: test_sink.timeFirst = "0"
   Property  22: test_sink.timeEOF = "0"
   Property  23: test_sink.suppressReads = "false" (cached)


Note that the total number of ``valuesReceived`` by the ``test_sink`` component equals the total number of values sent by the ``test_source`` component.


