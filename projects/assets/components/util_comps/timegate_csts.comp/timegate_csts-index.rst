.. timegate_csts documentation

.. _timegate_csts:


Timegate (``timegate``)
=============================

Timed transmit of complex IQ data using complex time sampled protocol. 
``timegate_csts`` is an asset in the ``ocpi.assets.util_comps`` component library.
Implementations include the :ref:`timegate_csts-HDL-worker` (``timegate_csts.hdl``). 
Tested platforms include
``xsim``, ``modelsim``, ``zed``, ``e3xx``. 

Design
------
Inputs complex short time sampled data and outputs complex short time sample data when the current time 
exceed the gated time.

Current time is provided as an input to the component on the time interface.
The time gated timestamp is a 96-bit number with the first 32 bits corresponding to seconds
and the last 40 bits corresponding to fractional seconds. The default state of the the timegate
is open which means data samples flows between the input and the output ports. 

When a timestamp opcode is received on the input port that is greater then the current time, the timegate
stops consuming data from the input port. When the current time exceeds the timestamp the 
gate is open and starts passing samples through the component. 

The time interface from which the current time is derived from originates from the
OpenCPI time server, which is instanced as part of the platform worker.
Furthermore, an additional component (time client) is dynamically instanced
by the framework for all components that declare time interfaces.
The time client communicates with the time server and produces the

Interface
---------
.. literalinclude:: ../specs/timegate_csts-spec.xml
   :language: xml

Properties
~~~~~~~~~~
.. ocpi_documentation_properties::

Ports
~~~~~
.. ocpi_documentation_ports::

   in: Signed complex samples with timestamps.
   out: Signed complex samples.

Implementations
---------------
.. ocpi_documentation_implementations:: ../timegate_csts.hdl

Example Application
-------------------
.. literalinclude:: example_app.xml
   :language: xml

Dependencies
------------
The dependencies to other elements in OpenCPI are:

 * None.

Limitations
-----------
Limitations of ``timegate_csts`` are:

 * The time client only provides a 64-bit interface thus some of the fractional time (40-bits) from
   the timestamp gets truncated. 

Testing
-------
One test case is implemented to validate the timegate_csts component:

The input file contains one timestamp and 8 notional complex data samples. The timestamp is zero 
seconds and fractional second is set to max value (0xFFFFFFFFFF). For verification, the timegate_csts
passes the complex data samples through the gate. 

.. ocpi_documentation_test_platforms::

.. ocpi_documentation_test_result_summary::
