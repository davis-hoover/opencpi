.. %%NAME-CODE%% documentation

.. Skeleton comment (to be deleted): Alternative names should be listed as
   keywords. If none are to be included delete the meta directive.

.. meta::
   :keywords: skeleton example


.. _%%NAME-CODE%%:


SKELETON NAME (``%%NAME-CODE%%``)
=================================
Skeleton outline: Single line description.

Design
------
Skeleton outline: Functional description of **what** the component achieves (not **how** it is implemented, as that belongs in primitive documentation).

The mathematical representation of the implementation is given in :eq:`%%NAME-CODE%%-equation`.

.. math::
   :label: %%NAME-CODE%%-equation

   y[n] = \alpha * x[n]


In :eq:`%%NAME-CODE%%-equation`:

 * :math:`x[n]` is the input values.

 * :math:`y[n]` is the output values.

 * Skeleton, etc.,

A block diagram representation of the implementation is given in :numref:`%%NAME-CODE%%-diagram`.

.. _%%NAME-CODE%%-diagram:

.. figure:: %%NAME-CODE%%.svg
   :alt: Skeleton alternative text.
   :align: center

   Caption text.

Interface
---------
.. literalinclude:: ../specs/%%NAME-CODE%%-spec.xml
   :language: xml

Opcode handling
~~~~~~~~~~~~~~~
Skeleton outline: Description of how the non-stream opcodes are handled.

Properties
~~~~~~~~~~
.. ocpi_documentation_properties::

   property_name: Skeleton outline: List any additional text for properties, which will be included in addition to the description field in the component specification XML.

Ports
~~~~~
.. ocpi_documentation_ports::

   input: Primary input samples port.
   output: Primary output samples port.

Implementations
---------------
.. ocpi_documentation_implementations:: ../%%NAME-CODE%%.hdl ../%%NAME-CODE%%.rcc

Example Application
-------------------
.. literalinclude:: example_app.xml
   :language: xml

Dependencies
------------
The dependencies to other elements in OpenCPI are:

 * Skeleton outline: List primitives or other files within OpenCPI that are used (no need to list protocols).

There is also a dependency on:

 * ``ieee.std_logic_1164``

 * ``ieee.numeric_std``

 * Skeleton outline: Any other standard C++ or HDL packages.

Limitations
-----------
Limitations of ``%%NAME-CODE%%`` are:

 * Skeleton outline: List any limitations, or state "None." if there are none.

Testing
-------
.. ocpi_documentation_test_result_summary::
