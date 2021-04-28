.. platform_ad9361_config HDL worker

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

.. _platform_ad9361_config-HDL-worker:


``platform_ad9361_config`` HDL worker
=====================================

Detail
------
The AD9361 config HDL subdevice worker's OpenCPI Worker Description (OWD) defines the
`AD9361 device registers <https://usermanual.wiki/Document/AD9361RegisterMapReferenceManualUG671.1082447504/view>`_
as properties.  The ``rawprops`` worker port accesses the device registers
and forwards them to the AD9361 SPI HDL subdevice worker.

The AD9361 config HDL subdevice worker also operates itself as a subdevice that conveys:

* Build-time information from the ``ad9361_adc_sub.hdl`` and ``ad9361_dac_sub.hdl`` HDL subdevice workers (see ``ocpi.assets.devices``) up to the processor via properties

* Processor-known assumptions about the AD9361 multichannel configuration to the ``ad9361_adc_sub.hdl`` and ``ad9361_dac_sub.hdl`` HDL subdevice workers.
  
.. comment out ocpi_documentation_worker directive for now. It doesn't work with HdlDevice yet.

Worker ports
~~~~~~~~~~~~

.. this is hand-entered for now to suggest a format that the XML parser might use to automatically generate it.

Outputs:

* ``rawprops``: Communicates the AD9361 register map to AD9361 SPI subdevice worker.

  * Type: ``RawProp``

  * Master: ``true``

* ``dev_force_spi_reset``: Forces the RESETB pin, which is active low, to logic 0.

  * Type: ``DevSignal``

  * Count: 1

  * Optional: ``false``

  * Master: ``true``

  * Signal: ``force_reset``

* ``dev_cfg_data``:

  * Type: ``DevSignal``

  * Count: 1

  * Optional: ``true``

  * Master: ``false``

  * Signals (expected to be hard-coded at build time):

    * ``ch0_handler_is_present``: Set to ``1`` if the ``dev_data_ch0`` signal is connected to a worker that handles the data; set to ``0`` otherwise.

    * ``ch1_handler_is_present``: Set to ``1`` if the ``dev_data_ch1`` signal is connected to a worker that handles the data; set to ``0`` otherwise.

    * ``data_bus_index_direction``: Set to ``1`` if the bus indexing the P0_D and P1_D was reversed before processing.

    * ``data_clock_is_inverted``: Set to ``1`` if the clock in via ``dev_data_clk`` was inverted inside the worker before used as an active-edge rising clock.

    * ``islvds``: Set to ``1`` if the ``DIFFERENTIAL_p`` parameter is ``true`` and to ``0`` if the ``PORT_CONFIG_p`` parameter is ``single``.

    * ``isdualport``: Set to ``1`` if the ``PORT_CONFIG_p`` parameter is ``dual`` and to ``0`` if it is ``single``.

    * ``isfullduplex``: Set to ``1`` if the ``DIFFERENTIAL_p`` parameter is ``true`` and to ``0`` if the ``PORT_CONFIG_p`` parameter is ``single``.

    * ``isDDR``: Set to ``1`` if the ``DATA_RATE_CONFIG_p`` parameter is ``DDR`` and to ``0`` if it is ``SDR``.

    * ``present``: Set to ``1`` to indicate that this worker should validate the ``islvds``, ``isdualport``, ``isfullduplex`` and ``isddr`` signals against similar signals in the AD9361 ADC sub and AD9361 data sub HDL subdevice workers if they are present in the FPGA bitstream.

* ``dev_cfg_data_rx``:

  * Type: ``DevSignal``

  * Count: 1

  * Optional: ``true``

  * Master: ``false``

  * Signals (expected to be hard-coded at build time):

    * ``rx_frame_usage``: Set to ``1`` to indicate that this worker was built with the assumption that the RX frame operates in its toggle setting and set to ``0`` if this worker was built with the assumption that the RX frame has a rising edge on the first sample and then stays high.  The value is intended to match the AD9361 register 0x010 BIT D3.

    * ``rx_frame_is_inverted``: RX path-specific data port configuration.  Used to tell other workers about the configuration that was enforced when this worker was compiled.

Inputs:

* ``dev_cfg_data_port``: 

  * Type: ``DevSignal``

  * Count: ``1``

  * Optional: ``false``

  * Master: ``true``

  * Signals (expected to be hard-coded at build time):

    * ``ios_standard_is_lvds``: Set to ``1`` if the build-time configuration was for LVDS mode; set to ``0`` otherwise.

    * ``p0_p1_are_swapped``: Set to ``1`` if the build-time configuration inverted the P0 and P1 data port roles; set to ``0`` otherwise.

* ``dev_cfg_data``: Some data port configurations, like LVDS, require the TX bus to use 2R2T timing if either 2 TX or 2 RX channels are used.  FOr example, if using LVDS and this has a value of 1, 2R2T timing will be forced.

  * Type: ``DevSignal``

  * Count: ``1``

  * Optional: ``true``

  * Master: ``false``

  * Signal: ``config_is_two_r``

* ``dev_cfg_data_tx``: 

  * Type: ``DevSignal``

  * Count: ``1``

  * Optional: ``true``

  * Master: ``false``

  * Signals:

    * ``config_is_two_t``: Some data port configurations, like LVDS, require the TX bus to use 2R2T timing if either 2 TX or 2 RX channels are used.  FOr example, if using LVDS and this has a value of 1, 2R2T timing will be forced.

    * ``force_two_r_two_t_timing``: Expected to match AD9361 register 0x010 bit D2.

* ``dev_rxen_data_sub``:

  * Type: ``DevSignal``

  * Count: 1

  * Optional: ``false``

  * Master: ``true``

  * Signal: ``rxen``

* ``dev_txen_data_sub``:

  * Type: ``DevSignal``

  * Count: 1

  * Optional: ``false``

  * Master: ``true``

  * Signal: ``txen``


SubDevice connections
~~~~~~~~~~~~~~~~~~~~~

* Worker port ``dev_cfg_data``:

  * Port index: 0

  * Worker supported: ``ad9361_adc_sub``

  * Worker port supported: ``dev_cfg_data``

* Worker port ``dev_cfg_data_rx``:

  * Port index: 0

  * Worker supported: ``ad9361_adc_sub``

  * Worker port supported: ``dev_cfg_data_rx``

* Worker port ``dev_cfg_data``:

  * Port index: 1

  * Worker supported: ``ad9361_dac_sub``

  * Worker port supported: ``dev_cfg_data``

* Worker port ``dev_cfg_data_tx``:

  * Port index: 0

  * Worker supported: ``ad9361_dac_sub``

    Worker port supported: ``dev_cfg_data_tx``


Worker configuration parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Resource utilization for this worker for the ``zynq`` target platform:

  * Configuration: 0
  
  * Tool: Vivado
  
  * Version: 2017.1
  
  * Device: xc72020clg484-1
  
  * Registers (Typ): 77
  
  * LUTS (Typ): 123
  
  * ``Fmax`` (MHz) (Typ): 318

* Resource utilization for this worker for the ``stratix`` target platform:

  * Configuration: 0
  
  * Tool: Quartus
  
  * Version: 17.1.0
  
  * Device: EP4SGX230KF40C2
  
  * Registers (Typ): 80
  
  * LUTS (Typ): 167
  
  * ``Fmax`` (MHz) (Typ): N/A

* Resource utilization for this worker for the ``virtex6`` target platform:

  * Configuration: 0
  
  * Tool: ISE
  
  * Version: 14.7
  
  * Device: 6v1x240tff1 156-1
  
  * Registers (Typ): 86
  
  * LUTS (Typ): 217
  
  * ``Fmax`` (MHz) (Typ): 331.126


``Fmax`` refers to the maximum allowable clock rate for any registered signal paths within a given clock domain
for an FPGA design. ``Fmax`` is specific only to this worker and represents the maximum
possible Fmax for any OpenCPI bitstream built with this worker included.
Note that the ``Fmax`` value for a given clock domain for the final bitstream is often worse
than the Fmax specific to this worker, even if this worker is the only one included in the bitstream.

Control timing and signals
--------------------------

The AD9361 config HDL subdevice worker operates in the
control plane clock domain. Note that this worker is essentially
the central worker that command/control passes through, and that no RX or TX data paths flow through this worker.

Vivado timing analysis
----------------------

The Vivado timing report that OpenCPI runs for HDL device workers may erroneously report
a max delay for a clocking path which should have been ignored. Custom Vivado ``tcl`` commands
had to be run for this HDL subdevice worker to extract pertinent information from Vivado timing analysis.
After building the worker, the following commands were run from the ``assets`` project directory
(after the Vivado ``settings64.sh`` was sourced):

.. code-block::
   
   cd hdl/devices/
   vivado -mode tcl

Then the following commands were run inside the Vivado ``tcl`` terminal:

.. code-block::
   
   open_project ad9361_config.hdl/target-zynq/ad9361_config_rv.xpr
   synth_design -part xc7z020clg484-1 -top ad9361_config_rv -mode out_of_context
   create_clock -name clk1 -period 0.001 [get_nets {ctl_in[Clk]}]
   report_timing -delay_type min_max -sort_by slack -input_pins -group clk1

The following is the output of the timing report. The ``Fmax`` for the control plane clock
for this worker is computed as the maximum magnitude slack with a control plane clock
of 1 ps plus 2 times the assumed 1 ps control plane
clock period (3.135 ns + 0.002 ns = 3.137 ns, 1/3.137 ns = 318.78 MHz).

.. code-block::
   
   Vivado% report_timing -delay_type min_max -sort_by slack -input_pins -group clk1

   Timing Report

   Slack (VIOLATED) : -3.135ns (required time - arrival time)

   Source:             wci/wci_decode/my_state_r_reg[2]/C
   
                         (rising edge-triggered cell FDRE clocked by clk1 {rise@0.000ns fall@0.001ns period=0.001ns})

   Destination:        wci/wci_decode/FSM_oneshot_my_access_r_reg[0]/CE

                         (rising edge-triggered cell FDSE clocked by clk1 {rise@0.000ns fall@0.001ns period=0.001ns}) clk1
      
   Path Group:         clk1
   
   Path Type:          Setup (Max at Slow Process Corner)

   Requirement:        0.002ns (clk1 rise@0.002ns - clk1 rise@0.000ns)

   Data Path Delay:    2.884ns (logic 0.937ns (32.490%) route 1.947ns (67.510%))

   Logic Levels:       2 (LUT6=2)

   Clock Path Skew:   -0.049ns (DCD - SCD + CPR)
   
      Destination Clock Delay (DCD): 0.924ns = ( 0.926 - 0.002 )
      
      Source Clock Delay (SCD):      0.973ns
   
      Clock Pessimism Removal (CPR): 0.000ns
   
   Clock Uncertainty:  0.035ns ((TSJ^2 + TIJ^2)^1/2 + DJ) / 2 + PE

      Total System Jitter (TSJ):     0.071ns

      Total Input Jitter  (TIJ):     0.000ns

      Discrete Jitter      (DJ):     0.000ns 

      Phase Error          (PE):     0.000ns
   

   Location    Delay type             Incr(ns)  Path(ns)   Netlist Resource(s)
   ------------------------------------------------------------------- ------------

               (clock clk1 rise edge) 0.000     0.000 r
	       
	                              0.000     0.000 r    ct1_in[Clk] (IN)
                       
               net (fo=66, unset)     0.973     0.973      wci/wci_decode/ctl_in[Clk]

               FDRE                                   r    wci/wci_decode/my_state_r_reg[2]/C
	       
   ------------------------------------------------------------------- -------------

               FDRE (Prop_fdre_C_Q)   0.518     1.491 r    wci/wci_decode/my_state_r_reg[2]/Q

               net (fo=5, unplaced)   0.993     2.484      wci/wci_decode/wci_state[2]

	                                              r    wci/wci_decode/ctl_out[SResp][1]_INST_0_i_2/I0

               LUT6 (Prop_lut6_I0_O)  0.295     2.779 r    wci/wci_decode/ctl_out[SResp][1]_INST_0_i_2/O
	       
	       net (fo=4, unplaced)   0.443     3.222      wci/wci_decode/ctl_out[SResp][1]_INST_0_i_2_n_0

	                                                   wci/wci_decode/FSM_oneshot_my_access_r[4]_i_1/I2

               LUT6 (Prop_lut6_I2_O)  0.124     3.346 r    wci/wci_decode/FSM_oneshot_my_access_r[4]_i_1/O

	       net (fo=8, unplaced)   0.511     3.857      wci/wci_decode/my_access_r

	       FDSE                                   r    wci/wci_decode/FSM_oneshot_my_access_r_reg[0]/CE

   ------------------------------------------------------------------- --------------

               (clock clk1 rise edge) 0.002     0.002 r

	                              0.002     0.002 r    ctl_in[Clk] (IN)

               net (fo=66, unset)     0.924     0.926      wci/wci_decode/ctl_in[Clk]

	       FDSE                                   r    wci/wci_decode/FSM_oneshot_my_access_r_reg[0]/C
	       
               clock pessimism        0.000     0.926
	       
               clock uncertainty     -0.035     0.891

	       FDSE (Setup_fdse_C_CE)-0.169     0.722      wci/wci/decode/FSM_oneshot_my_access_r_reg[0]
	       	       
   --------------------------------------------------------------

               required time                    0.722
	       
               arrival time                    -3.857
	       
   --------------------------------------------------------------	       

               slack                           -3.135
	       

   report_timing: Time (s): cpu = 00:00:07 ; elapsed = 00:00:08 . Memory (MB): peak = 2093.707 ; gain = 496.523 ; free physical = 13626 ; free virtual = 87791

Utilisation
-----------
.. ocpi_documentation_utilisation::
