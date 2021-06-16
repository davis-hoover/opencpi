.. file_read documentation

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

.. _file_read:


File read (``file_read``)
=========================
Injects file-based data into an application.
``file_read`` is an asset in the ``ocpi.core`` component library.
Implementations include the
:ref:`file_read-HDL-worker` (``file_read.hdl``) and the :ref:`file_read-RCC-worker` (``file_read.rcc``).
Tested platforms include
``centos7``, ``isim``, ``modelsim``, ``xilinx13_3``, ``xilinx13_4``, and ``xsim``.


Design
------
The file read component injects file-based data into an application. To use it, specify
a ``file_read`` component instance and connect its output port to an input port of the
component that is to process the data first. Use the ``fileName`` property to specify
the name of the file to be read. This component has one output port whose name is ``out``,
which carries the messages to be input. There is no protocol associated with the port,
enabling it to be agnostic as to the protocol of the component connected to the output port.

Operating modes
~~~~~~~~~~~~~~~
The file read component supports data-streaming mode and messaging mode.

Data-streaming mode
^^^^^^^^^^^^^^^^^^^
In data-streaming mode, the file content becomes the payload of a stream of messages,
each carrying a fixed number of bytes of file data and all with the same opcode.
The component properties ``messageSize`` and ``opcode`` specify the length
and opcode of all output messages, respectively, which means that this operating
mode lends itself to protocols that have a single opcode of where the intent is
only to send data on one of the opcodes of a multi-opcode protocol.

If the number of bytes in the file is not an even multiple of the message size,
the component sends the remaining bytes in a final, shorter message. The
``granularity`` property can be used to force the message size to be a
multiple of the specified value and to force truncation of the final message
to be a multiple of the specified value.

.. include:: ../file_read.test/doc/snippets/messaging_snippet.rst

Implications for no protocol on port
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The output port on the file read component has no protocol. This means that
the data file must be formatted to match the protocol of the connected component's
input port. In data-streaming mode, the file structure needs to correspond
to the opcode specified by the ``opcode`` property. In messaging mode, it means
only using opcodes and payloads in the file that correspond to the protocol
of the connected component.

Message size/buffers
~~~~~~~~~~~~~~~~~~~~
The system normally determines buffer sizes based on protocol. Since file read's
output port has no protocol, the protocol used is the protocol in use by the port
to which the output port is connected. If this port also has no protocol,
the system's default of 2KB is selected. This selection can always be overridden
in the application's OAS or with ACI Pvalues for *any* connection in the application.

When the ``messageSize`` property is zero (the default), the system's
(or application's) chosen buffer size is used. A non-zero value for this property
overrides the system/application value, which risks trying to write messages
larger than the system is prepared for, resulting in an error.

When the ``messagesInFile`` property is set to ``true`` (the component is operating in messaging
mode), the buffer size must be large enough to accommodate the largest message found in
the input file. It is always better to set the buffer size on connections in the OAS
(or using PValues in the ACI) than to use the ``messageSize`` property, since the former
method is universal for specifying buffer sizes for all connections in the application.
For example, the ``iqstream`` protocol uses a sequence of 2048 16-bit I/Q pairs,
which means that any message over 8192 (2048 * 4 bytes per pair) is invalid.

End-of-file handling
~~~~~~~~~~~~~~~~~~~~
When the file read component reaches the end of its input file, it does one of three things:

* Sends an end-of-file notification

* Enters the ``done`` state with no further action, when the ``suppressEOF`` property is ``true``

* Restarts reading at the beginning of the file, when the ``repeat`` property is ``true``

Interface
---------
.. literalinclude:: ../specs/file_read_spec.xml
   :language: xml

Opcode handling
~~~~~~~~~~~~~~~

To be supplied: Description of how the non-stream opcodes are handled.

Properties
~~~~~~~~~~
.. ocpi_documentation_properties::

   fileName: The name of the file whose contents are sent out as raw data to the output port.

   messagesInFile: The flag used to turn messaging mode on and off.

   opcode: In data-streaming mode, the opcode in which all the data in the file is sent. In messaging mode, the opcode of the ZLM at the end of the file.

      messageSize: The size of the messages in bytes that are created on the output port. The connected component buffer needs to be big enough to take the data buffer that is being passed to this worker.

      granularity: The value to use to calculate the final message size at the end of a file. The final message will be truncated to be a multiple of the specified value in bytes.

      repeat: The flag used to repeat reading the data file over and over.

      bytesRead: The number of bytes read from the file. Useful when debugging data flow issues.

      messagesWritten: The number of messages read from the file. Useful when debugging data flow issues.

      suppressEOF: The flag used to enable/disable the ZLM that is propagated at the end of the file.

      badMessage: The flag set by a worker when it has a problem getting data from the file; for example, when the file name is bad.

Ports
~~~~~
.. ocpi_documentation_ports::

   out: Data streamed from file.

Implementations
---------------
.. ocpi_documentation_implementations:: ../file_read.hdl ../file_read.rcc

Example application
-------------------
.. literalinclude:: example_app.xml
   :language: xml

Dependencies
------------
The dependencies on other elements in OpenCPI are:

 * None.

Limitations
-----------
Limitations of ``file_read`` are:

 * None.

Testing
-------
All test benches use the worker implementation as part of the verification process.
This component does not have a unit test suite.
 
.. ocpi_documentation_test_result_summary::
