.. %%NAME-CODE%% documentation


.. Skeleton comment (to be deleted): Alternative names should be listed as
   keywords. If none are to be included delete the meta directive below.

.. meta::
   :keywords: skeleton example


.. _%%NAME-CODE%%-primitive:


SKELETON NAME (``%%NAME-CODE%%``)
=================================
Skeleton outline: Single line description.

Design
------
Skeleton outline: Functional description of **what** the primitive achieves.

The mathematical representation of the implementation is given in :eq:`%%NAME-CODE%%-equation`.

.. math::
   :label: %%NAME-CODE%%-equation

   y[n] = \alpha * x[n]

In :eq:`%%NAME-CODE%%-equation`:

 * :math:`y[n]` is the output values.

 * etc.,

A block diagram representation of the implementation is given in :numref:`%%NAME-CODE%%-diagram`.

.. _%%NAME-CODE%%-diagram:

.. figure:: %%NAME-CODE%%.svg
   :alt: Skeleton alternative text.
   :align: center

   Caption text.

Implementation
--------------
Skeleton outline: Description of **how** the primitive is implemented.

Interface
---------

Generics
~~~~~~~~

 * ``GENERIC_NAME`` (``GENERIC_TYPE``): Skeleton outline, put generic outline here.

Ports
~~~~~

 * ``PORT_NAME`` (``PORT_TYPE``), in / out: Skeleton outline, put port outline here.

Dependencies
------------
The dependencies to other elements in OpenCPI are:

 * Skeleton outline: List primitives or other files within OpenCPI that are used, or state "None." if there are none.

There is also a dependency on:

 * ``ieee.std_logic_1164``

 * ``ieee.numeric_std``

 * Skeleton outline: Any other HDL packages.

Limitations
-----------
Limitations of ``%%NAME-CODE%%`` are:

 * Skeleton outline: List any limitations, or state "None." if there are none.
