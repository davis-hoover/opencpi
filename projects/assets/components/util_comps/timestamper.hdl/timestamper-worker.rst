.. timestamper HDL worker


:orphan:

.. _timestamper-HDL-worker:


``timestamper`` HDL worker
==========================
Application worker HDL implementation with a settable runtime configuration parameter for the ``enable`` property.

Detail
------
.. ocpi_documentation_worker::

Worker ports
~~~~~~~~~~~~

Inputs:

* ``in``: Signed complex samples.
  
  * Type: ``StreamInterface``
    
  * Data width: ``32``
    
  * Number of opcodes: ``256``

Outputs:

* ``out``: Signed complex samples.
  
  * Type: ``StreamInterface``
    
  * Data width: ``32``
    
  * Number of opcodes: ``256``

Time:

* ``time``: Time interface provided by OpenCPI time server.
  
  * Type: ``TimeInterface``
    
  * Seconds width: ``32``
    
  * Fraction width: ``32``


Control Timing and Signals
~~~~~~~~~~~~~~~~~~~~~~~~~~
The timestamper HDL worker uses the clock from the control plane and standard
control signals.

Data presented on the input appears on the output clock three cycles later
(latency=3).  Two of the three clock cycles consist of a time message.

Utilisation
-----------
.. ocpi_documentation_utilisation::
