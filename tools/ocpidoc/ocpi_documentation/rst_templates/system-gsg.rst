.. %%NAME-CODE%% Getting Started Guide Documentation


.. _%%NAME-CODE%%-gsg:

.. This is a template for creating an OpenCPI Getting Started Guide
   for an OpenCPI system. Copy this template file, rename it, and
   edit the contents to your requirements.

.. Below are definitions for copyright and trademark symbols.

.. |trade| unicode:: U+2122
   :ltrim:

.. |reg| unicode:: U+00AE
   :ltrim:

.. Below are default substitution strings used in this template
   in headings and text as placeholders for the given system
   name, its vendor, and the product family it belongs to,
   if any. Use any or all of these strings "as is" or customize
   them to your requirements.

.. Details on how to use substitution strings are given in the
   section "Using Include Files and Substitution Strings to
   Share Common Information" in the OpenCPI User Guide.
   
.. |system_name| replace:: MySystemName

.. The |system_name| definition above specifies a substitution
   string for the name for the system to be used when referring
   to the system in section headings and text. Replace "MySystemName"
   with the common/shorthand name used for the given system in the
   product vendor's documentation. Examples: "ZedBoard", "ZCU102"
   "E310", "PlutoSDR".

.. |vendor_name| replace:: MySystemVendor
			   
.. The |vendor_name| definition above specifies a substitution
   string for the name for the system's vendor to be used in
   section headings and text. Replace "MySystemVendor" with
   the system vendor's name. Examples: "Digilent", "Xilinx"
   "Ettus Research", "Analog Devices".

.. |product_family| replace:: MySystemProductFamily

.. The |product_family| definition above defines a substitution string
   for the name of the product family/ product category/series to which
   the system belongs (if any) to be used when introducing the system
   in the Overview section and in other locations as necessary.
   Replace "MySystemProductFamily" with the system's product family
   name. Examples: "Zynq-7000", "Zynq", "Universal Software Radio Peripheral (USRP)",
   "ADALM-PLUTO".

.. |device_family| replace:: MyProductDeviceFamily

.. The |device_family| definition above defines a substitution string for
   the name for the device/board/system family (if any) within the product
   family to which the system belongs to be used when introducing the system
   in the Overview section and in other locations as necessary. Replace
   "MyProductDeviceFamily" with the system's product device family name.
   Examples: "All Programmable (AP)", "UltraScale+", "E3xx Series",
   "Advanced Learning Module".

.. Note that vendors frequently change the names of products, product families,
   series, etc. When describing the given system, use the naming convention
   that appears in the vendor product brief that corresponds to the system
   you're describing.

OpenCPI |vendor_name| |system_name| Getting Started Guide
=========================================================

.. This is the main RST file for a getting started guide (GSG) for
   an OpenCPI system. An OpenCPI system consists of platforms.
   The platforms used in a given system can be platforms that are
   re-usable in other systems or they can be platforms that are used
   only in the given system.

.. Reusable platforms generally have their own Getting Started Guides to
   describe their installation and setup. Examples of reusable platforms
   (using their OpenCPI platform names) are the xilinx19_2_aarch32 and
   xilinx19_2_aarch64 RCC platforms (Xilinx Linux 2019.2 32-bit and Xilinx
   Linux 2019.2 64-bit RCC platforms) and the picoevb PCI Express-based HDL
   platform (RHS Research PicoEVB, described in the PicoEVB Getting Started Guide).
   For reusable platforms, the system GSG should refer to the platform's
   GSG and only describe those differences (if any) in how the platform
   is used in the given system.
   Note that the reusable RCC platforms do not currently have their own GSGs.
   Installation information about these RCC platforms is provided in the
   OpenCPI Installation Guide.

.. Platforms that are truly specific to a given system should be documented
   in a separate section in this system GSG. The section should follow the
   outline/organization used in the OpenCPI platform getting started guide template.
   Examples are the adi_plutosdr0_32 RCC platform and the plutosdr HDL platform
   (specific to the ADALM-PLUTO/PlutoSDR system and documented in the PlutoSDR
   Getting Started Guide), the zed HDL platform (specific to the ZedBoard system
   and described in the Zedboard Getting Started Guide), the e31x HDL platform
   (specific to the E31X system and described in the E31x Getting Started Guide),
   and the adrv9361 HDL platform (specific to the ADRV9361-Z7035 system and described
   in the ADRV9361-Z7035 Getting Started Guide).

.. A system GSG should also describe any setup issues that are separate from
   the underlying platforms.
   
.. Each system should have its own GSG. The main RST file for a GSG should
   be located in the systems/<system-name>/ directory in the project (usually
   an OSP) along with the other assets specific to the given system.
   Images used in the system GSG should also be located in this directory
   unless you are using "include" files as described below.

Document Revision History
-------------------------

.. In the table below, supply the document's revision number,
   a brief description of the update, and the date at which the
   update was made. The revision number can be any sequential
   numbering scheme or it can be the same as the
   OpenCPI version in which the document is released.

.. csv-table:: OpenCPI |vendor_name| |system_name| Getting Started Guide: Revision History
   :header: "Revision", "Description of Change", "Date"
   :widths: 10,30,10
   :class: tight-table

   "v1.0", "Initial Release", "date"

How to Use This Document
------------------------
  
.. To start this section, give a 1-sentence description of this OpenCPI system.
   Use the proper name of the system and apply the appropriate
   trademarks. Below is an example that uses substitution strings and
   the copyright and trademark symbols defined at the top of this file.

This document provides information that is specific to setting up the
OpenCPI |vendor_name|\ |reg| |product_family|\ |reg| |device_family|\ |trade| |system_name|
for use with OpenCPI. It describes system-specific details, if any, about setting up:

* The platforms that comprise the system

* The system as a whole

Use this document in conjunction with the following OpenCPI documents:

.. Replace the first bullet below with the titles and links to the
   getting started guides for the platforms used in this OpenCPI system.

* The OpenCPI Getting Started Guide (if any) provided for each platform in the system

* The `OpenCPI Installation Guide <https://opencpi.gitlab.io/releases/latest/docs/OpenCPI_Installation_Guide.pdf>`_

The following OpenCPI documents can also be used as references for the information in this document:

* `OpenCPI User Guide <https://opencpi.gitlab.io/releases/latest/docs/OpenCPI_User_Guide.pdf>`_
  
* `OpenCPI Glossary <https://opencpi.gitlab.io/releases/latest/docs/OpenCPI_Glossary.pdf>`_

Note that the *OpenCPI Glossary* is also contained in both the *OpenCPI Installation Guide* and the
*OpenCPI User Guide*.

This document assumes a basic understanding of the Linux command line (or "shell") environment.

Overview
--------

.. Provide a brief overview of the system that describes how it can be used for OpenCPI.
   Features that are irrelevant to its use as an OpenCPI system do not need to be mentioned.
   Provide a link to the vendor product brief and give the OpenCPI name for the system
   (e.g., e31x, zed, zcu102, microzed,...)

.. Next, identify the platforms used in the system and how they are interconnected (fabric, bus, ...).

Installing Platform A for the |system_name|
-------------------------------------------

.. Create a section like this one for each platform in the system. The example
   headings here show two platforms, A and B.

.. If the platform to be installed is one that is re-usable in different systems:

   - Describe the differences (if any) in how the platform is used in this system.
     
   - Provide a reference/hyperlink to the platform's Getting Started Guide on the
     OpenCPI website opencpi.gitlab.io.

.. Do NOT duplicate the information found in the platform's getting started guide
   or the generic installation information about the platform found in the OpenCPI
   Installation Guide.

.. If the platform to be installed is specific to this system and therefore does
   not have its own getting started guide, provide the getting started guide
   information in this section by following the template for a platform GSG.

Installing Platform B for the |system_name|
-------------------------------------------

.. Follow the same instructions as for "Platform A" above.

Setting up the |system_name| After its Platforms are Installed
--------------------------------------------------------------

.. In this section, describe any steps to enable the OpenCPI development
   and execution environment that need to be performed on the system as
   a whole (and NOT on the platforms in the system). Examples:

   - How to set up the system to boot from an SD card: location of
     relevant jumpers or switches (include images or link to product
     vendor documentation) and steps to configure them.

   - How to connect the system to an Ethernet network: location of
     relevant Ethernet ports, hardware items required for connection,
     process to connect.

   - Any system-specific details that are necessary for following the
     procedures described in the OpenCPI Installation Guide section
     "Installation Steps for Systems after their Platforms are Installed".
     Examples:

     - SD card setup details needed when following the procedures in the
       sections "Using SD Card Reader/Writer Devices", "Preparing the SD
       Card Contents", "Writing the SD Card", SD Card OpenCPI Startup Script Setup"
       for this system.

     - Serial console setup details needed when following the serial
       console-related procedures described in "Preparing the Development
       Host to Support Embedded Systems" and "Establishing a Serial Console
       Connection" for this system.

     - Details about setting up the modes of OpenCPI operation (server, network,
       or standalone) needed when following the procedures in the section
       "Configuring the Runtime Environment" for this system.

     - Details about running the standard installation test applications in
       the different modes of operation (server, network, standalone) needed
       when following the procedures in the section "Running the Test Application"
       for this system.

.. If possible, supply images for the locations of ports, switches, and jumpers
   and for switch and jumper settings. Otherwise, refer to the vendor hardware
   user manual.

.. The standard OpenCPI installation process described in "Installation Steps
   for Systems after their Platforms are Installed" must be used to enable
   OpenCPI for the given OpenCPI system unless there is a legitimate reason
   for providing something different.
   
.. Below is the introductory text for this section that is used in all system GSGs.

This section describes steps to enable the OpenCPI development and execution environment
that must be performed on the |system_name| after its platforms have been
installed. It also contains setup information specific to the |system_name| system
that is needed when performing the tasks described in the section
"Installation Steps for Systems After their Platforms are Installed"
in the
`OpenCPI Installation Guide <https://opencpi.gitlab.io/releases/latest/docs/OpenCPI_Installation_Guide.pdf>`_.

.. Below is an example of how to provide a "details" section be used in a procedure
   described in "Installation Steps for Systems after their Platforms are Installed"
   in the OpenCPI Installation Guide.
   
Details for Establishing a Serial Console Connection for the |system_name|
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This section contains details about the |system_name| that pertain to the
instructions for setting up a serial I/O console described in the section
"Establishing a Serial Console Connection" in the
`OpenCPI Installation Guide <https://opencpi.gitlab.io/releases/latest/docs/OpenCPI_Installation_Guide.pdf>`_:

* Detail 1

* Perform this step before performing step X

* Perform this step after performing step Y

