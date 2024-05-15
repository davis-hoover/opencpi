.. test_drc documentation


.. _test_drc-application:


SKELETON NAME (``test_drc``)
=============================
OAS-only application which verifies Digital Radio Controller (DRC) core class unit test within test_drc.rcc

Hardware Portability
--------------------
Nothing in this application is specific to any hardware.

Execution
---------

   ``OCPI_LOG_LEVEL=8 ocpirun -t 5 test_drc.xml``

The pass indication string "ALL PASS" can also be searched for via grep with the following command:
OCPI_LOG_LEVEL=8 ocpirun -t 5 test_drc.xml

   ``OCPI_LOG_LEVEL=8 ocpirun -t 5 test_drc.xml 2>&1 | grep "ALL PASS"``


Prerequisites
~~~~~~~~~~~~~

   * RCC Worker: ``test_drc.rcc`` (ocpi.platform) built for any RCC platform

Verification
------------
Run the application and observe a "ALL PASS" printed to the screen. For example:

   ``OCPI( 8:453.0339): drc: ==================== ALL PASSED``
