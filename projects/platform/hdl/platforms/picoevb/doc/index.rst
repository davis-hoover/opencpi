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

   "v2.x.x", "Initial PicoEVB release", "x/2021"



Overview 
--------

This document provides installation information that is specific
to the RHS Research\ |trade| PicoEVB.  Use this document when performing the tasks described
in the chapter "Enabling OpenCPI Development for Embedded Systems"
in the `OpenCPI Installation Guide <https://opencpi.gitlab.io/releases/latest/docs/OpenCPI_Installation_Guide.pdf>`_.  The following documents can also be used as reference to the tasks described in this document:

* `OpenCPI User Guide <https://opencpi.gitlab.io/releases/latest/docs/OpenCPI_User_Guide.pdf>`_
  
* `OpenCPI Glossary <https://opencpi.gitlab.io/releases/latest/docs/OpenCPI_Glossary.pdf>`_

Note that the *OpenCPI Glossary* is also contained in both the *OpenCPI Installation Guide* and the
*OpenCPI User Guide*.

This document assumes a basic understanding of standard PC motherboard connections, as well as the Linux command line (or "shell") environment.


The PicoEVB is a low cost FPGA device from RHS Research\ |trade|. The board is designed around the Xilinx Artix 7 (XC7A50T) FPGA with a PCIe x1 interface.  The PicoEVB will work in the following slots:

* M.2 2230 Key A
* M.2 2230 Key E
* M.2 2280 Key M
* Full length mini PCIe (with carrier board)
* PCIe x1, x4, x8, or x16 slot (with carrier board)

See RHS Research website `<https://rhsresearch.com/>`_
for more information about the PicoEVB device.  Note the OpenCPI HDL (FPGA) platform 
for the PicoEVB is called the "``picoevb``".

:numref:`picoevb-hw` lists the items in the required for setting up the PicoEVB for 
OpenCPI installation and deployment.

.. _picoevb-hw:

.. csv-table:: Hardware Items Required for PicoEVB HDL platform
   :header: "Item", "Usage"
   :widths: 40,60
   :class: tight-table

   "PicoEVB", "OpenCPI target HDL platform"
   "M.2 PCIe carrier board", "M.2 to PCIe for connecting to PCIe edge slot"
   "Development Host System", "Development host running OpenCPI"
   "4x2 USB-to-JTAG connector cable", "Connection between motherboard USB hub and PicoEVB"

.. _picoevb-sw:

.. csv-table:: Software Items Required for PicoEVB HDL platform
   :header: "Item", "Usage"
   :widths: 40,60
   :class: tight-table

   "CentOS 7 Operating system", "Builds FPGA artifacts for PicoEVB"
   "Vivado 2019.2", "Builds FPGA artifacts for PicoEVB"
   "OpenCPI installed on Development Host system", "OpenCPI builds, development, and deployment"

See the OpenCPI Installation Guide
`OpenCPI Installation Guide <https://opencpi.gitlab.io/releases/latest/docs/OpenCPI_Installation_Guide.pdf>`_
for detailed instatllation instructions for OpenCPI.

Supported OpenCPI Platforms and Vendor Tools
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:numref:`sfw-reqs` lists the OpenCPI hardware (HDL (FPGA) platforms used for the PicoEVB
and the third-party/vendor tools on which they depend.

.. I used ascii art for this table to be able to control line breaks in column text.
   
.. Need to find out how to turn off "no line wrap" in HTML renderer so that column text will wrap in csv-table and list-table.

.. _sfw-reqs:

.. table:: Supported OpenCPI Platforms for the PicoEVB USRP and their Dependencies
	   
   +------------------------+-------------------+---------------------------+---------------------------------------+
   | OpenCPI                + Description       + OpenCPI                   + Required Third-Party/                 |
   |                        +                   +                           +                                       |
   | Platform Name          +                   + Project/Repo              + Vendor Tools                          |
   +========================+===================+===========================+=======================================+
   | ``picoevb``            + RHS PicoEVB       + ``ocpi.platform.picoevb`` + Xilinx Vivado\ |reg| 2019.2           |
   +------------------------+-------------------+---------------------------+---------------------------------------+


The PicoEVB HDL platform does not have an embedded RCC platform.  Rather the host development controls the FPGA resources directly via the PCIe interface

Quickstart Setup for the PicoEVB HDL Platform
----------------------------------------------

The following sections provide a step-by-step guide for enabling the PicoEVB including the following:

#. Attaching PicoEVB to PCIe/M.2 Carrier Board (optional)
#. Physical Installation of PicoEVB/Carrier board into PCIe Slot
#. Connecting PicoEVB to the motherboard's internal USB port using the USB-to-JTAG cable
#. OpenCPI installation of the PicoEVB platform
#. Memory Reservation for OpenCPI Kernel Driver
#. Loading the OpenCPI Driver
#. Running reference applications

Physical Installation of PicoEVB Board on Host Platform
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#. Connect PicoEVB to M.2 PCIe carrier board.  If M.2 slot is readily available on the development host, the adapter board is not required.

#. Connect the 8-pin USB port to an internal USB port on the motherboard of the development host using a standard 4x2 header cable.


Installing and Building the OpenCPI Platforms for the PicoEVB
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Before installing and building the OpenCPI platforms for the PicoEVB, Xilinx vendor tools must be installed.  Follow the instructions in the "Installing Xilinx Tools" section 
of the “Installing Third-party/Vendor Tools” chapter within the
`OpenCPI Installation Guide <https://opencpi.gitlab.io/releases/latest/docs/OpenCPI_Installation_Guide.pdf>`_
to install the Xilinx tools listed as platform dependencies in Software Requirements Table :numref:`sfw-reqs`

After installing the required vendor tools, follow the instructions in the section “Installation Steps for Platforms” in the
`OpenCPI Installation Guide <https://opencpi.gitlab.io/releases/latest/docs/OpenCPI_Installation_Guide.pdf>`_
to install and build the ``picoevb`` 
platforms for the PicoEVB.  In summary the platform must be installed and built with ``ocpiadmin install platform``
For example:

.. code-block:: bash
   
   ocpiadmin install platform picoevb

See the `ocpiadmin(1) man page <https://opencpi.gitlab.io/releases/latest/man/ocpiadmin.1.html>`_ for command usage details.

Building this hdl platform will build the components necessary to build HDL assemblies, and run applications on the platform.  For the puprposes of getting started, we will focus on the running the ``test_source_sink`` and ``test_source_to_dev_null`` applications. The test_sink_application requires the ``test_internal_assy`` HDL assembly, while the ``test_source_to_dev_null`` application requires the ``test_source_assy`` HDL assembly.  Next, we will build these two FPGA assemblies:

* Navigate to the test_internal_assembly directory, and build the assembly for the picoevb hdl platform:

.. code-block:: bash

   cd opencpi/projects/assets/hdl/assemblies/test_internal_assy
   ocpidev build --hdl-platform picoevb

* Navigate to the test_source_assy assembly directory, and build the assembly for the picoevb hdl platform:

.. code-block:: bash

   cd opencpi/projects/assets/hdl/assemblies/test_source_assy
   ocpidev build --hdl-platform picoevb

Building the these assemblies will each take several minutes to complete.  The test_source_assy assembly will be utilized in the following section to program the FPGA's flash.  This is a one-time setup step that enables enumeration of the picoevb on the PCIe bus when the development host is booted.

Initial Preparation and Programming of the PicoEVB
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The picoevb hdl platform must initially be programmed with an OpenCPI-compliant assembly.  Therefore a precompiled version of OpenOCD \ |trade| JTAG utility is included with the OpenCPI distribution to facilitate JTAG programming of the Flash.  Perform following steps to unzip the compressed OpenOCD executable and perform initial FPGA flash programming from the development host.

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

With the FPGA flash programmed, the development host must be power-cycled for the PCIe interface of the picoevb to be enumerated in the bios.

Memory Reservation for OpenCPI Kernel Driver
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When OpenCPI communicates to cards via PCI, it uses a loadable Linux kernel device driver for discovery and DMA-based communication, which requires local (reserved) DMA memory resources. DMA memory resources must be allocated or reserved on the CPU-side memory, that is accessible to both the CPU (via the local mmap system call), as well as, OpenCPI’s PCI DMA engine with the board is issuing PCI READ or WRITE TLPs. By default, Linux allocates 128 KB of memory for the OpenCPI driver. However, OpenCPI applications may have buffering requirements that necessitate additional memory resources. 

The remainder of this section provides the method for reserving memory in the kernel where special measures ``(memmap=)`` are used to allocate 128 MB of memory. The memmap parameter is used to reserve more block memory from the Linux kernel. While this variable supports many formats, the following usage has proven to be sufficient:

``memmap=SIZE$START``

Where ``SIZE`` is the number of bytes to reserve in either hexadecimal or decimal, 
and ``START`` is the physical address in hexadecimal bytes. It is required that the pages for all addresses and sizes are on even boundaries (0x1000 or 4096 bytes).

At this time, the OpenCPI PCI DMA engine requires that the user-mode DMA memory pool be in a 32 or 64-bit
memory range and due to the manner with which Linux manages memory, it is recommended that the address be
higher than the first 24 bits. With these requirements, the first step is to find a usable contiguous memory range by
examining the BIOS physical RAM map as reported by dmesg.

Run dmesg and filter on BIOS to review the physical RAM map:

.. code-block:: bash

   dmesg | grep BIOS


The output should look similar to the following:

.. code-block:: bash

   BIOS-provided physical RAM map:
     BIOS-e820: 0000000000000000 - 000000000009f800 (usable)
     BIOS-e820: 000000000009f800 - 00000000000a0000 (reserved)
     BIOS-e820: 00000000000ca000 - 00000000000cc000 (reserved)
     BIOS-e820: 00000000000dc000 - 00000000000e4000 (reserved)
     BIOS-e820: 00000000000e8000 - 0000000000100000 (reserved)
     BIOS-e820: 0000000000100000 - 000000005fef0000 (usable)
     BIOS-e820: 000000005fef0000 - 000000005feff000 (ACPI data)
     BIOS-e820: 000000005feff000 - 000000005ff00000 (ACPI NVS)
     BIOS-e820: 000000005ff00000 - 0000000060000000 (usable)
     BIOS-e820: 00000000e0000000 - 00000000f0000000 (reserved)
     BIOS-e820: 00000000fec00000 - 00000000fec10000 (reserved)
     BIOS-e820: 00000000fee00000 - 00000000fee01000 (reserved)
     BIOS-e820: 00000000fffe0000 - 0000000100000000 (reserved)


Select a ”(usable)” section of memory and reserve a subsection of that memory. Once the memory is reserved, the
Linux kernel will ignore it. In this case, there are three usable sections to consider:

.. code-block:: bash

   BIOS-e820: 0000000000000000 - 000000000009f800 (usable)
   BIOS-e820: 0000000000100000 - 000000005fef0000 (usable)
   BIOS-e820: 000000005ff00000 - 0000000060000000 (usable)

Upon close inspection of the usable regions, the first range is too small and below the first 24 bits, while the third ranges is simply too small. Fortunately the second address space meets the address range requirement (between 24 and 32 bits) and it is large enough for to reserve several hundred megabytes of memory.

The starting memory address for the user-mode DMA region is calculated by subtracting 0x08000000 (128 MB)
from the largest memory region available, as long as it is greater than 0x08000000 (128MB) and inside the 32-bit
address range (address is less than 4GB). In this example, the 2nd region is the largest: 0x5FEF0000 - 0x100000 =
0x5FDF0000 = 1,608,450,048 ( 1.6GB) and it is inside of the 32-bit address space. The starting memory address
(0x5FEF0000 - 0x08000000) is 0x57EF0000. And this is the value that used to construct the memmap parameter, as shown below:

.. code-block:: bash

   memmap=128M$0x57EF0000

When calculating the starting address, the user must ensure that address occurs on an even page boundary of 4
KB. This may necessitate an additional adjustment to the starting address.  In some cases, the $dmesg | grep BIOS returns a value like 0x5FEFFFFF. It is recommended that the user simply change this address, such that, its low word is all zeros, ex. 0x5FEF0000, prior to calculating the starting address.

Once the memmap parameter as been calculated, it will need to be added to the kernel command line in the boot loader.  
For CentOS, the  utility “grubby” can be used to add the parameter to all kernels in the start-up menu. The single quotes are REQUIRED or the shell will interpret the $0:

CentOS 7 uses grub2, which requires a DOUBLE backslash:

.. code-block:: bash

   sudo grubby --update-kernel=ALL --args=memmap='128M\\$0x57EF0000'

To verify the current kernel has the argument set:

.. code-block:: bash

   sudo -v
   sudo grubby --info $(sudo grubby --default-kernel)


CentOS 7 displays a SINGLE backslash before the $, for example:

.. code-block:: bash

   args="ro rdblacklist=nouveau crashkernel=auto rd.lvm.lv=vg.0/root quiet audit=1 boot=UUID=96933\
   cb5-f478-4933-a0d4-16953cf47f5c memmap=128M\$0x57EF0000 LANG=en_US.UTF-8"

If no longer desired, the parameter can also be removed with the following:

.. code-block:: bash

   sudo grubby --update-kernel=ALL --remove-args=memmap


More information concerning grubby can be found at:
`<https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html/system_administrators_guide/ch-working_with_the_grub_2_boot_loader>`_


For the memmap parameter:
`<https://www.kernel.org/doc/html/latest/admin-guide/kernel-parameters.html>`_

Reboot the system to apply the the new configuration for memory reservation.  Once the system has finished booting, examine the state of the physical RAM map to confirm that the desired memory has been reserved:

.. code-block:: bash

   dmesg | more
   Linux version 3.10.0-1160.31.1.el7.x86_64 (mockbuild@kbuilder.bsys.centos.org) (gcc version 4.8.5 20150623 (Red Hat 4.8.5-44) (GCC) ) #1 SMP Thu Jun 10 13:32:12 UTC 2021 
   Command line: BOOT_IMAGE=/vmlinuz-3.10.0-1160.31.1.el7.x86_64 root=/dev/mapper/centos-root ro crashkernel=auto rd.lvm.lv=centos/root rd.lvm.lv=centos/swap rhgb quiet LANG=en_US.UTF-8 memmap=128M$0x57EF0000
   BIOS-provided physical RAM map:
     BIOS-e820: 0000000000000000 - 000000000009f800 (usable)
     BIOS-e820: 000000000009f800 - 00000000000a0000 (reserved)
     BIOS-e820: 00000000000ca000 - 00000000000cc000 (reserved)
     BIOS-e820: 00000000000dc000 - 00000000000e4000 (reserved)
     BIOS-e820: 00000000000e8000 - 0000000000100000 (reserved)
     BIOS-e820: 0000000000100000 - 000000005fef0000 (usable)
     BIOS-e820: 000000005fef0000 - 000000005feff000 (ACPI data)
     BIOS-e820: 000000005feff000 - 000000005ff00000 (ACPI NVS)
     BIOS-e820: 000000005ff00000 - 0000000060000000 (usable)
     BIOS-e820: 00000000e0000000 - 00000000f0000000 (reserved)
     BIOS-e820: 00000000fec00000 - 00000000fec10000 (reserved)
     BIOS-e820: 00000000fee00000 - 00000000fee01000 (reserved)
     BIOS-e820: 00000000fffe0000 - 0000000100000000 (reserved)
   user-defined physical RAM map:
    user: 0000000000000000 - 000000000009f800 (usable)
    user: 000000000009f800 - 00000000000a0000 (reserved)
    user: 00000000000ca000 - 00000000000cc000 (reserved)
    user: 00000000000dc000 - 00000000000e4000 (reserved)
    user: 00000000000e8000 - 0000000000100000 (reserved)
    user: 0000000000100000 - 0000000057ef0000 (usable)
    user: 0000000057ef0000 - 000000005fef0000 (reserved) <== New
    user: 000000005fef0000 - 000000005feff000 (ACPI data)
    user: 000000005feff000 - 000000005ff00000 (ACPI NVS)
    user: 000000005ff00000 - 0000000060000000 (usable)
    user: 00000000e0000000 - 00000000f0000000 (reserved)
    user: 00000000fec00000 - 00000000fec10000 (reserved)
    user: 00000000fee00000 - 00000000fee01000 (reserved)
    user: 00000000fffe0000 - 0000000100000000 (reserved)
   DMI present.

A new ”(reserved)” area is shown between the second ”(useable)” section and the (ACPI data) section. Now, when the ”ocpidriver load” is ran, it will detect the new reserved area, and pass that data to the OpenCPI kernel module.

.. note::
   
   When available, the driver will attempt to make use of the CMA region for direct memory access. In use cases where many memory allocations are made, the user may receive the following kernel message:

   .. code-block:: bash

      alloc_contig_range test_pages_isolated([memory start], [memory end]) failed

   This is a kernel warning, but does not indicate that a memory allocation failure occurred, only that the CMA engine could not allocate memory in the first pass. Its default behavior is to make a second pass, and if that succeeded, the end user should not see any more error messages. This message cannot be suppressed, but can be safely ignored. An actual allocation failure will generate unambiguous error messages.


Loading the OpenCPI Driver
^^^^^^^^^^^^^^^^^^^^^^^^^^
When OpenCPI is installed via RPMs, the OpenCPI driver should have been installed. However, when developing with source OpenCPI, the user is required to manage the loading of the OpenCPI driver.  The following terminal outputs are intended to provide the user with expected behavior of when the driver is not and is loaded. The user should note that only when the driver is installed can the PicoEVB be discovered as a valid OpenCPI container.

.. code-block:: bash

   ocpidriver unload
   The driver module was successfully unloaded

.. code-block:: bash

   ocpidriver load 
   Found generic reserved DMA memory on the linux boot command line and assuming it is for OpenCPI: [memmap=128M$0xB1258000]
   Driver loaded successfully.

   ocpidriver unload 
   The driver module was successfully unloaded.

   ocpirun -C
   OCPI( 2:412.0211): When searching for PCI device '0000:04:00.0': Can't open /dev/mem, forgot to load the driver? sudo?
   OCPI( 2:412.0233): In HDL Container driver, got PCI search error: Can't open /dev/mem, forgot to load the driver? sudo?
   Available containers:
    #  Model Platform            OS     OS-Version  Arch     Name
    0  rcc   centos7             linux  c7          x86_64   rcc0

   ocpidriver load 
   Found generic reserved DMA memory on the linux boot command line and assuming it is for OpenCPI: [memmap=128M$0xB1258000]
   Driver loaded successfully.

   ocpirun -C
   Available containers:
    #  Model Platform            OS     OS-Version  Arch     Name
    0  hdl   picoevb                                         PCI:0000:04:00.0
    1  rcc   centos7             linux  c7          x86_64   rcc0


Running the Reference Applications
----------------------------------

Before running the Reference Applicaitons, the ``OCPI_LIBRARY_PATH``
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


Note that the picoevb platform container was selected and chosen for the test_source component, while the centos7 rcc worker was chosen for file_write component.  You will also notice that 8388608 values (each consisting of 4 bytes) were sent to the file_write component and written to the file test.output.  Next, verify that the test.output file is the correct size of (4 x 8388608) bytes, or 32MB :

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


