.. platform_ad9361_spi_csts HDL worker

.. This file is protected by Copyright. Please refer to the COPYRIGHT file
   distributed with this source distribution.

   This file is part of OpenCPI <http://www.opencpi.org>

   OpenCPI is free software: you can redistribute it and/or modify it under the
   terms of the GNU Lesser General Public License as published by the Free
   Software Foundation, either version 3 of the License, or (at your option) any
   later version.

   OpenCPI is distributed in the hope that it will be useful, but WITHOUT ANY
   WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
   A PARTICULAR PURPOSE. See the GNU Lesser General Public License for
   more details.

   You should have received a copy of the GNU Lesser General Public License
   along with this program. If not, see <http://www.gnu.org/licenses/>.

:orphan:

.. _platform_ad9361_spi_csts-HDL-worker:


``platform_ad9361_spi_csts`` HDL Worker
=======================================

Detail
------
The AD9361 SPI HDL subdevice worker is intended for use in platforms and cards
with an SPI bus that addresses only the AD9361. SPI read/writes are
actuated by the ``rprops`` RawProperty port. A DevSignal is also sent which
can force the AD9361 RESETB pin, which is active-low, to logic 0.

.. ocpi_documentation_worker::

   rprops: Actuates SPI reads and writes to the AD9361 device.
   dev_force_reset: Forces the ``RESETB`` pin, which is active low, to logic 0.

Worker Configuration Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* Resource utilization for this worker for the ``zynq`` target platform, configuration 0:

  * Configuration: 0
  
  * Tool: Vivado
  
  * Version: 2017.1
  
  * Device: xc72020clg484-1
  
  * Registers (Typ): 67
  
  * LUTS (Typ): 94
  
  * ``Fmax`` (MHz) (Typ): 235

* Resource utilization for this worker for the ``zynq`` target platform, configuration 1:

  * Configuration: 1
  
  * Tool: Vivado
  
  * Version: 2017.1
  
  * Device: xc72020clg484-1
  
  * Registers (Typ): 68
  
  * LUTS (Typ): 101
  
  * ``Fmax`` (MHz) (Typ): 315

* Resource utilization for this worker for the ``stratix`` target platform, configuration 0:

  * Configuration: 1
  
  * Tool: Quartus
  
  * Version: 17.1.0
  
  * Device: EP4SGX230KF40C2
  
  * Registers (Typ): 70
  
  * LUTS (Typ): 139
  
  * ``Fmax`` (MHz) (Typ): N/A

* Resource utilization for this worker for the ``stratix`` target platform, configuration 1:

  * Configuration: 1
  
  * Tool: Quartus
  
  * Version: 17.1.0
  
  * Device: EP4SGX230KF40C2
  
  * Registers (Typ): 71
  
  * LUTS (Typ): 141
  
  * ``Fmax`` (MHz) (Typ): N/A

* Resource utilization for this worker for the ``virtex6`` target platform, configuration 0:

  * Configuration: 0
  
  * Tool: ISE
  
  * Version: 14.7
  
  * Device: 6v1x240tff1 156-1
  
  * Registers (Typ): 65
  
  * LUTS (Typ): 130
  
  * ``Fmax`` (MHz) (Typ): 437.445

* Resource utilization for this worker for the ``virtex6`` target platform, configuration 1:

  * Configuration: 1
  
  * Tool: ISE
  
  * Version: 14.7
  
  * Device: 6v1x240tff1 156-1
  
  * Registers (Typ): 65
  
  * LUTS (Typ): 134
  
  * ``Fmax`` (MHz) (Typ): 412.712

``Fmax`` refers to the maximum allowable clock rate for any registered signal paths within a given clock domain
for an FPGA design. ``Fmax`` is specific only to this worker and represents the maximum
possible Fmax for any OpenCPI bitstream built with this worker included.
Note that the ``Fmax`` value for a given clock domain for the final bitstream is often worse
than the Fmax specific to this worker, even if this worker is the only one included in the bitstream.

Note that the ``Fmax`` measurements given for the ``zynq`` target are the result of a Vivado timing analysis
that is different from the Vivado analysis performed by default for OpenCPI worker builds. See
the section "Vivado timing analysis" for details.


Control Timing and Signals
--------------------------
The AD9361 SPI HDL subdevice worker operates entirely in
the control plane clock domain. All SPI data and SPI
clock signals are generated in the control plane clock domain.
Note that SPI clock can only be a divided version of the control plane clock.

Vivado Timing Analysis
----------------------
The Vivado timing report that OpenCPI runs for HDL device workers may erroneously report
a max delay for a clocking path which should have been ignored. Custom Vivado ``tcl`` commands
had to be run for this HDL subdevice worker to extract pertinent information from Vivado timing analysis.
After building the worker, the following commands were run from the ``assets`` project directory
(after the Vivado ``settings64.sh`` was sourced):

.. code-block::

   cd hdl/devices/
   vivado -mode tcl

Then the following commands were run inside the Vivado ``tcl`` terminal for the
parameter property set:

* CP_CLK_FREQ_HZ_p=100e6
  
* SPI_CLK_FREQ_HZp=6.25e6

.. code-block::
   
   open_project ad9361_spi.hdl/target-zynq/ad9361_spi_rv.xpr
   synth_design -part xc7z020clg484-1 -top ad9361_spi_rv -mode out_of_context
   create_clock -name clk1 -period 0.001 [get_nets {ctl_in[Clk]}]
   report_timing -delay_type min_max -sort_by slack -input_pins -group clk1

The Fmax for the control plane clock for this worker is computed as
the maximum magnitude slack with a control plane clock of 1 ps plus 2 times
the assumed 1 ps control plane clock period (4.244 ns + 0.002 ns = 4.244 ns, 1/4.244 ns = 235.52 MHz).

Then the following commands were run inside the Vivado tcl terminal for the parameter property set:

* CP_CLK_FREQ_HZ_p=125e6

* SPI_CLK_FREQ_HZp=6.25e6

.. code-block::
   
   open_project ad9361_spi.hdl/target-zynq/ad9361_spi_rv.xpr
   synth_design -part xc7z020clg484-1 -top ad9361_spi_rv -mode out_of_context
   create_clock -name clk1 -period 0.001 [get_nets {ctl_in[Clk]}]
   report_timing -delay_type min_max -sort_by slack -input_pins -group clk1

The Fmax for the control plane clock for this worker is computed as
the maximum magnitude slack with a control plane clock of 1 ps plus 2 times
the assumed 1 ps control plane clock period (3.169 ns + 0.002 ns = 3.171 ns, 1/3.171 ns = 315.36 MHz).

Utilization
-----------
.. ocpi_documentation_utilization::
