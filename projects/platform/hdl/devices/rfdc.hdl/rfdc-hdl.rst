.. rfdc.hdl HDL worker


.. _rfdc.hdl-HDL-worker:


``rfdc.hdl`` HDL Worker
======================
Xilinx RF Data Converter Device Worker.

Detail
------
.. ocpi_documentation_worker::

.. figure:: rfdc_block.svg

The Xilinx RF Data Converter (RFDC) has 3 generations (https://www.xilinx.com/products/intellectual-property/rf-data-converter.html). The non-comprehensize list of relevant capabilities are as follows:
#. Number of RF ADCs range from 0 to 16 (generation-dependent)
#. Number of RF DACs range from 0 to 16 (generation-dependent)
#. ADC number of sample bits ranges from 12 bits to 14 bits (generation-dependent)
#. DAC number of sample bits is 14
#. ADC RF direction conversion sampling rates vary and are up to 5.9 Gsps (generation-dependent) and are specified at build-time by the IP generator GUI
#. DAC RF direction conversion sampling rates vary and are up to 10 Gsps (generation-dependent) and are specified at build-time by the IP generator GUI
#. Digital decimation/interpolation rates range from 1x to 40x (generation-dependent)
#. Clock source/routing is complicated and the Xilinx IP generator GUI indicates valid/invalid configurations
#. ADCs and DACs are organized by tiles, often confusingly

This worker and its underlying rfdc primitive only support the following RFDC configuration(s):
#. Generation 3 ZU48DR (xczu48dr-ffvg1517-2-e)
#. 2 ADCs (Tiles 224, 226)
#. 2 DACs (Tile 231)
#. 14-bit ADC
#. 14-bit DAC
#. ADC RF direction conversion sampling rate of 4 Gsps
#. DAC RF direction conversion sampling rate of 4 Gsps
#. Digital decimation/interpolation rate of 40x (4 Gsps / 40 = 100 Msps at AXI-Stream ports)
#. Digital complex mixer (fine frequency control) enabled for every converter

This worker was designed with the following ordered design priorities:
#. Enable the RF Data Converter (RFDC) HiTechGlobal ZU48DR variant with J3, J13, J18, J20 (Tiles 224, 226, 231) RF connectors
#. Instance as few RFDC Xilinx IP RF ports as possible
#. Instance as few RFDC clocks as possible
