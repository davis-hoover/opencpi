.. test_drc.rcc RCC worker


.. _test_drc.rcc-RCC-worker:


``test_drc.rcc`` RCC Worker
======================
Application worker intended to perform unit testing of the core framework DRC class.

Detail
------

This worker includes the DRC.hh header from the OpenCPI core framework
(runtime/drc). It has a TestDRC class which inherits from the core framework DRC
class and defines virtual methods. The TestDRC also provides examples of simple
constraint application via use of the OperatingPlan class. The worker run()
method performs the unit tests. Tests are as follows:
 - C++ construction
 - state transitions: setting of known good configuration
 - state transitions: double release of known good configuration
 - state transitions: prepare of known good configuration
 - state transitions: prepare -> release of known good configuration
 - state transitions: prepare -> release -> release of known good configuration
 - state transitions: prepare -> start -> stop of known good configuration
 - state transitions: prepare -> start -> stop -> release of known good configuration
 - state transitions: prepare -> start -> stop -> release -> release of known good configuration
 - state transitions: prepare -> start -> release of known good configuration
 - state transitions: prepare of known bad configuration
 - state transitions: start of known bad configuration
 - 1 or 2 configurations
 - 1 or 2 channels per configuration
 - request by rf_port_name and by direction only
 - recoverable true and false

Verification
------------

The pass indication string "ALL PASS" can also be searched for in stderr when the OCPI_LOG_LEVEL is set to 8 or higher

