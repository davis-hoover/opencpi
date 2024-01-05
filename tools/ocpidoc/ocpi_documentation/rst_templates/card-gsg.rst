.. %%NAME-CODE%% Getting Started Guide Documentation

.. _%%NAME-CODE%%-gsg:

.. This is a template for creating an OpenCPI Getting Started Guide
   for an OpenCPI HDL card. Copy this template file, rename it, and
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

.. |card_name| replace:: MyCardName

.. The |card_name| definition above specifies a substitution
   string for the name for the card to be used when referring
   to the card in section headings and text. Replace "MyCardName"
   with the common/shorthand name used for the given card in the
   product vendor's documentation.

.. |vendor_name| replace:: MyCardVendor

.. The |vendor_name| definition above specifies a substitution
   string for the name for the card's vendor to be used in
   section headings and text. Replace "MyCardVendor" with
   the card vendor's name. Examples: "Avnet", "Analog".

.. |product_family| replace:: MyCardProductFamily

.. The |product_family| definition above defines a substitution string
   for the name of the product family/product category/series/version to which
   the card belongs (if any) to be used when introducing the card
   in the Overview section and in other locations as necessary.
   Replace "MyCardProductFamily" with the card's product family
   name.

.. |device_family| replace:: MyProductDeviceFamily

.. The |device_family| definition above defines a substitution string for
   the name for the device/board family (if any) within the product
   family to which the card belongs to be used when introducing the card
   in the Overview section and in other locations as necessary. Replace
   "MyProductDeviceFamily" with the card's product device family name.

.. |ocpi_platform_name| replace:: MyOpenCPIplatformName

.. The |ocpi_platform_name| definition above defines a substitution string
   for the OpenCPI identifier for the platform to be used in command lines for
   OpenCPI tools like ocpiadmin and in directory paths to platform assets
   and files, for example, $OCPI_ROOT_DIR/projects/platform/hdl/platforms/zed_ether.
   Replace "MyOpenCPIplatformName" with the platform's OpenCPI identifier.
   Examples: "zed_ether".

.. Note that vendors frequently change the names of products, product families,
   series, etc. When describing the given card, use the naming convention
   that appears in the vendor product brief that corresponds to the platform
   you're describing.

OpenCPI |vendor_name| |card_name| Getting Started Guide
=======================================================

.. This is the main file for a getting started guide (GSG) for an
   OpenCPI HDL card. It should contain the information required to
   install the card on an OpenCPI HDL platform and enable it for
   OpenCPI.

.. An OpenCPI HDL card is an optional piece of hardware that contains
   extra devices. An HDL card is used to expand the scope of an HDL
   platform by adding more HDL devices to it. An HDL card contains one
   or more HDL devices and is plugged in to a slot on an OpenCPI platform.

.. An HDL card GSG should contain details (if any) about configuring the
   card before and/or after it is plugged into the HDL platform that applies
   to all relevant OpenCPI HDL platforms the card can be plugged in to. It
   should also provide configuration information that is specific to a
   particular platform(s).

.. The RST file for an HDL card GSG should be co-located with the HDL
   card asset it describes.

   
Document Revision History
-------------------------

.. In the table below, supply the document's revision number,
   a brief description of the update, and the date at which the
   update was made. The revision number can be any sequential
   numbering scheme or it can be the same as the
   OpenCPI version in which the document is released.

.. csv-table:: OpenCPI |vendor_name| |card_name| Getting Started Guide: Revision History
   :header: "Revision", "Description of Change", "Date"
   :widths: 10,30,10
   :class: tight-table

   "v1.0", "Initial Release", "date"

Overview
--------

.. Provide a brief overview of the HDL card that describes how it can be used
   for OpenCPI. Features that are irrelevant to its use as an OpenCPI HDL card
   do not need to be mentioned. Provide a link to the vendor product brief
   and give the OpenCPI platform name for the HDL card (e.g., zed_ether).


Installation Prerequisites
--------------------------

.. List any hardware items required (if any) for setting up the card
   on an OpenCPI platform.  Below is a skeleton list:

The following items are required for OpenCPI |card_name| installation and setup:

* |vendor_name| |card_name|

* 4x2 USB-to-JTAG cable

The following items are optional:

* xxx carrier card


Setting up the |card_name| for Installation on a Platform
---------------------------------------------------------

.. Describe any configuration/setup steps that should be performed
   before plugging in the HDL card to the HDL platform. These steps
   should apply to any platform to which the card is to be plugged
   in to.
 

Setting up the |card_name| After It is Installed on a Platform
--------------------------------------------------------------

.. Describe any configuration steps that should be performed
   after the HDL card has been plugged into the HDL platform.
   These steps should apply to any platform to which the card
   is to be plugged in to.
 
Setting up the |card_name| on a |platform_name| Platform
--------------------------------------------------------

.. Describe any modifications that need to be made to the card to get
   it to work with a particular HDL platform.  For example, any modifications
   to the card that need to be made in order for its host HDL platform to
   function properly.
      
