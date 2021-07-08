.. timestamper HDL worker


:orphan:

.. _timestamper-HDL-worker:


``timestamper`` HDL Worker
==========================
Application worker HDL implementation with a settable runtime configuration parameter for the ``enable`` property.

Detail
------
.. ocpi_documentation_worker::

  in: Signed complex samples.

  out: Signed complex samples.

  time: Time interface provided by OpenCPI time server.

Control Timing and Signals
~~~~~~~~~~~~~~~~~~~~~~~~~~
The timestamper HDL worker uses the clock from the control plane and standard
control signals.

Data presented on the input appears on the output clock three cycles later
(latency=3).  Two of the three clock cycles consist of a time message.

Utilization
-----------
.. ocpi_documentation_utilization::
