.. %%NAME-CODE%% Getting Started Guide Documentation


.. _%%NAME-CODE%%-platform-gsg:

.. This is a template for creating an OpenCPI Getting Started Guide
   for an OpenCPI platform. Copy this template file, rename it, and
   edit the contents to your requirements.

.. Below are definitions for copyright and trademark symbols.

.. |trade| unicode:: U+2122
   :ltrim:

.. |reg| unicode:: U+00AE
   :ltrim:

.. Below are default substitution strings used in this template
   in headings and text as placeholders for the given platform
   name, its vendor, and the product and device families it belongs
   to, if any. Use any or all of these strings "as is" or customize
   them to your requirements.

.. Details on how to use substitution strings are given in the
   section "Using Include Files and Substitution Strings to
   Share Common Information" in the OpenCPI Documentation Writer Guide.

.. |platform_name| replace:: MyPlatformName


.. The |platform_name| definition above specifies a substitution
   string for the name for the platform to be used when referring
   to the platform in section headings and text. Replace "MyPlatformName"
   with the common/shorthand name used for the given platform in the
   product vendor's documentation. Examples: "PicoEVB" (for the RHS Research
   PicoEVB PCI Express-based HDL platform), "ZCU111" (for the Xilinx
   Zynq UltraScale+ ZCU111 RFSoC's HDL (FPGA) platform).

.. |vendor_name| replace:: MyPlatformVendor

.. The |vendor_name| definition above specifies a substitution
   string for the name for the platform's vendor to be used in
   section headings and text. Replace "MyPlatformVendor" with
   the platform vendor's name. Examples: "RHS Research", "Xilinx".

.. |product_family| replace:: MyPlatformProductFamily

.. The |product_family| definition above defines a substitution string
   for the name of the product family/product category/series/version to which
   the platform belongs (if any) to be used when introducing the platform
   in the Overview section and in other locations as necessary.
   Replace "MyPlatformProductFamily" with the platform's product family
   name. Examples: "Zynq".

.. |device_family| replace:: MyProductDeviceFamily

.. The |device_family| definition above defines a substitution string for
   the name for the device/board/software family (if any) within the product
   family to which the platform belongs to be used when introducing the platform
   in the Overview section and in other locations as necessary. Replace
   "MyProductDeviceFamily" with the platform's product device family name.
   Examples: "UltraScale+".

.. |ocpi_platform_name| replace:: MyOpenCPIplatformName

.. The |ocpi_platform_name| definition above defines a substitution string
   for the OpenCPI identifier for the platform to be used in command lines for
   OpenCPI tools like ocpiadmin and in directory paths to platform assets
   and files, for example, $OCPI_ROOT_DIR/projects/platform/hdl/platforms/picoevb.
   Replace "MyOpenCPIplatformName" with the platform's OpenCPI identifier.
   Examples: "picoevb", "zcu111".

.. Note that vendors frequently change the names of products, product families,
   series, etc. When describing the given platform, use the naming convention
   that appears in the vendor product brief that corresponds to the platform
   you're describing.


OpenCPI |vendor_name| |platform_name| Getting Started Guide
===========================================================

.. This is the main RST file for an OpenCPI platform getting started guide
   (GSG). If a given platform can be used in multiple systems and there
   are details about its setup for OpenCPI that are specific to the platform,
   it needs a GSG.
 
.. A platform GSG should contain hardware and software setup and installation
   information that is specific to enabling OpenCPI for the given
   OpenCPI-supported platform that an installer can use when following
   the standard, platform-generic procedures for enabling OpenCPI for
   platforms that are described in the OpenCPI Installation Guide.

.. A platform GSG provides key details and/or special steps for enabling
   OpenCPI for the given platform that are not mentioned in the
   platform-generic descriptions in the OpenCPI Installation Guide.
   The installer has both the GSG and the OpenCPI Installation Guide
   open in separate windows and uses the GSG to fill in any
   platform-specific information while following the standard setup
   and installation process described in the OpenCPI Installation Guide.

.. A platform GSG describes the steps to add a platform to a system.
   "Enabling OpenCPI" is separated into steps performed on the development host
   (enabling OpenCPI development) and steps performed on the runtime host
   (enabling OpenCPI runtime execution). Note that development host and
   runtime host can be the same system.

.. The standard OpenCPI installation process described in the OpenCPI
   Installation Guide must be used to enable OpenCPI on a given platform
   unless there is a legitimate reason for providing something different.

.. A platform GSG should NOT duplicate the generic installation information
   provided in the OpenCPI Installation Guide.

.. The RST file for a platform GSG should be co-located with the platform
   asset it describes.

Document Revision History
-------------------------

.. In the table below, supply the document's revision number,
   a brief description of the update, and the date at which the
   update was made. The revision number can be any sequential
   numbering scheme or it can be the same as the
   OpenCPI version in which the document is released.

.. csv-table:: OpenCPI |vendor_name| |platform_name| Getting Started Guide: Revision History
   :header: "Revision", "Description of Change", "Date"
   :widths: 10,30,10
   :class: tight-table

   "v1.0", "Initial Release", "date"

How to Use This Document
------------------------
  
.. To start this section, give a 1-sentence description of the target platform.
   Use the proper name of the platform and apply the appropriate
   trademarks. Below is an example that uses substitution strings and
   the copyright and trademark symbols defined at the top of this file.

This document provides installation information that is specific
to the OpenCPI |vendor_name|\ |reg| |product_family|\ |reg| |device_family|\ |trade| |platform_name|.

.. The rest of this section's text is the same for all getting started guides.
   Add the name of your platform (either directly to the text, as a value of
   the |platform_name| string at the top of this file, or as the value of
   a substitution string used in an include file and defined with the
   "ocpi_documentation_include" directive.
   
Use this document when configuring the |platform_name| hardware for OpenCPI and
when performing the tasks described
in the chapter "Enabling OpenCPI Development for Embedded Systems"
in the 
`OpenCPI Installation Guide <https://opencpi.gitlab.io/releases/latest/docs/OpenCPI_Installation_Guide.pdf>`_.
This document supplies details about enabling OpenCPI development for the |platform_name|
that can be applied to the procedures described in the referenced *OpenCPI Installation Guide* chapter.
The recommended method is to have the *OpenCPI Installation Guide* and this document
open in separate windows and refer to this document for any platform-specific details
while following the OpenCPI setup tasks described in the Installation Guide.

The following OpenCPI documents can also be used as references for the tasks described in this document:

* `OpenCPI User Guide <https://opencpi.gitlab.io/releases/latest/docs/OpenCPI_User_Guide.pdf>`_
  
* `OpenCPI Glossary <https://opencpi.gitlab.io/releases/latest/docs/OpenCPI_Glossary.pdf>`_

Note that the *OpenCPI Glossary* is also contained in both the *OpenCPI Installation Guide* and the
*OpenCPI User Guide*.

.. To the sentence below, add any platform-specific knowledge pre-requisites,
   for example, a basic understanding of PC motherboard connections if the
   platform is a PCI Express-based device.

This document assumes a basic understanding of the Linux command line (or "shell") environment.

Overview
--------

.. Provide a brief overview of the platform that describes how it can be used
   for OpenCPI. Features that are irrelevant to its use as an OpenCPI platform
   do not need to be mentioned. Provide a link to the vendor product brief
   and give the OpenCPI platform name for the platform (e.g., picoevb, alst4, ml605,...).

Installation Prerequisites
--------------------------

.. List the hardware items required for setting up the platform for OpenCPI:
   the platform itself, power supply, cables, adapters, SD cards. Then list
   any optional hardware items, like ethernet cable, and so on.
   See the getting started guides in the Avnet OSP or the Xilinx OSP for examples.
   Below is a skeleton list.

The following items are required for OpenCPI |platform_name| installation and setup:

* |vendor_name| |platform_name|

* 4x2 USB-to-JTAG cable

The following items are optional:

* xxx carrier card

Installation Summary
--------------------

.. List the installation/setup steps that need to be performed for this platform
   in the order in which they should be performed and provide links (Sphinx "refs")
   to the places in this GSG that provide the platform-specific details about the step.
   See the getting started guides in the Avnet OSP or the Xilinx OSP for examples.
   Below is a skeleton list.

To set up the |platform_name| for OpenCPI application development and execution,
perform the following steps:

* Install the vendor tools required for the |platform_name| on the development host. See XXX.

* Install and build the OpenCPI platform for the |platform_name| on the development host. See YYY.

* Configure the |platform_name| for OpenCPI and connect it to the runtime host. See ZZZ.

Enabling the OpenCPI Development Environment for |platform_name|
--------------------------------------------------------------

.. In this section, describe any key details or additional steps
   for the given platform that apply when following the steps described
   in the following places in the OpenCPI Installation Guide:

   - The section "Installation Steps for Platforms"

   - The chapter "Installing Third-party/Vendor Tools"

   - For a PCI Express-based platform, the section "Enabling
     the OpenCPI Development Environment for PCIe FPGA Cards".
     Note that this section simply points to the two places listed
     above.

   These steps enable OpenCPI development for platforms and are
   performed on a development host.

.. For example, the "Installation Steps for Platforms" section has a
   step to manually install the required third-party tools according
   to the chapter in the Installation Guide titled "Installing
   Third-party/Vendor Tools". If there are key details or additional
   steps for the given platform that apply to this section, supply
   them here like this:

This section provides details about the |platform_name| that pertain to
installing the XX tool as described in the chapter
"Installing Third-party Vendor Tools"
in the
`OpenCPI Installation Guide <https://opencpi.gitlab.io/releases/latest/docs/OpenCPI_Installation_Guide.pdf>`_:

* Detail 1

* Perform this step before performing step X

* Perform this step after performing step Y

.. Example 2: the "Installation Steps for Platform" section of the
   OpenCPI Installation Guide gives a generic description of the  step
   to install/build the platform with "ocpiadmin". Supply the specific
   "ocpiadmin install platform <platform>" command and any specific
   options to be used for this platform here.

Enabling the OpenCPI Execution Environment for |platform_name|
------------------------------------------------------------

.. In this section, describe any steps to enable the OpenCPI
   execution environment for this platform that should be
   performed no matter which system the platform is connected to.
   Examples:

   - How to connect this platform to a host

   - How to set any jumpers or switches on this platform that
     are required for OpenCPI operation

   - How to set up network connections for this platform

   Create subsections as necessary. Provide hyperlinks to the platform
   vendor's hardware user guide for the platform and/or other relevant
   documents as necessary.

.. If the given platform is a PCI Express-based FPGA platform, provide
   platform-specific key details to be applied to the generic instructions
   in the section "Enabling the OpenCPI Execution Environment for the
   PCIe FPGA Card" in the OpenCPI Installation Guide. Examples:
   
   - How to connect JTAG cables from the given platform to the host

   - How to use the loadFlash script for the given platform

   - The LEDs that indicate a successful system boot

   - How to set up the network connection, in the case of a
     PCI Express-based FPGA card with an Ethernet connection
     directly to an FPGA on that card
