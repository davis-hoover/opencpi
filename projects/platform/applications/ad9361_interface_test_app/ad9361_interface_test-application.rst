.. ad9361_interface_test_app documentation 

.. _ad9361_interface_test_app: 


AD9361 Interface Test App (``ad9361_interface_test_app``)
=========================================================
Analog Devices AD9361 RFIC digital interface test application. 

Description
-----------
This application tests both the transmit and receive paths of an AD9361 based platform. The AD9361 is placed in digital loopback mode which ensures the data transfer between the FPGA and the AD9361 Transceiver IC are valid at various sampling rates. 
The application is comprised of two components ad9361_prbs_gen and ad9361_prbs_test. The pseudo-random bit stream (prbs) generator and tester  ensure that all 12-bits sent out of the DAC (digital to analog converter) are received at the ADC (analog to digital converter) without data corruption. 
Both components are HDL components and an ACI application is used to command and control the workers through their properties. A script is used to cycle between various sampling rates and reports whether the tester received valid (pass) or invalid (fail) results. 

Hardware Portability
--------------------
This application can be run on any AD9361 based platform as long ad you have the appropriate HDL assembly built for that platform. The first platform to support this application is located in ocpi.osp.e3xx project. 


Execution
---------

Prerequisites
~~~~~~~~~~~~~
Prior to running the application the following prerequisites apply 

* platform needs to have been installed
* OpenCPI assets related to this application have been built and deployed on the platform (ACI application, hdl assembly, drc, script)
* execute the application on the embedded platform 

Commands(s)
~~~~~~~~~~~
The application can be run using the included script named "run_app_multiple_times.sh" 

.. code-block:: bash 

    $ cd /home/root/ad9361_interface_test_app
    $ ./run_app_multiple_times.sh 

Verification
------------
The script will printout results during execution, they will look something like this: 

.. code-block:: bash

    % ./run_app_multiple_times.sh 

    Running interface test at sample rates: 4.0 7.0 8.0 10.0 15.0 20.0 30.0
    Each test repeated 10 times
    Key: '+' = PASS, '-' = FAIL 

    Sample rate: 4.0 MHz [++++++++++]
    Results: 10 / 10 passed

    Sample rate: 7.0 MHz [++++++++++]
    Results: 10 / 10 passed

    Sample rate: 8.0 MHz [++++++++++]
    Results: 10 / 10 passed

    Sample rate: 10.0 MHz [++++++++++]
    Results: 10 / 10 passed

    Sample rate: 15.0 MHz [++++++++++]
    Results: 10 / 10 passed

    Sample rate: 20.0 MHz [++++++++++]
    Results: 10 / 10 passed

    Sample rate: 30.0 MHz [++++++++++]
    Results: 10 / 10 passed

    Overal results: 70 / 70 passed

You can modify the run_app_multiple_times script to adjust sample rates and number of times to repeat. 
