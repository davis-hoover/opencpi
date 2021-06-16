.. complex_mixer RCC worker


:orphan:

.. _complex_mixer-RCC-worker:


``complex_mixer`` RCC Worker
============================
Application worker RCC implementation with a numerically-controlled oscillator (NCO)
that uses the ``nco`` module from liquid-dsp to generate the digital
sine wave for the complex multiply operation.

Detail
------

The RCC worker implements the NCO using the ``nco`` module from liquid-dsp, which is a free
and open-source signal processing library for software-defined radios written in C
that is included in the OpenCPI installation. For details on liquid-dsp
and the ``nco`` module, see the `liquid-dsp website  <https://liquidsdr.org/doc/nco>`_.

The RCC worker converts the samples from fixed-point to floating-point
numbers in order to perform the math on a general-purpose processor (GPP).
The conversion equations are:

.. math::
	   
   iq\_float = \frac{iq\_fixed}{2^{15} -1}


.. math::
	   
   iq\_fixed = {iq\_float}*(2^{15} -1)


This conversion introduces a small
amount of error in the output data that should be accounted for when
using the RCC worker in an application.

The RCC worker also performs a conversion on the phase increment (`phs_inc`) property
to adhere to the the way it is implemented in HDL.  The conversion is done in the RCC implementation
for the component because the division operation is very resource-intensive in HDL.
The conversion equation from the component property to the input property in the liquid-dsp
interface is given below:

.. math::
	   
   liquid\_phs\_inc = phs\_inc*\frac{2\pi}{0x7FFF*2}


.. ocpi_documentation_worker::


Utilization
-----------
.. ocpi_documentation_utilization::
