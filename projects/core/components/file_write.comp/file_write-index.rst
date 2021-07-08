.. file_write documentation

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

.. _file_write:


File Write (``file_write``)
===========================
Writes application data to a file.
``file_write`` is an asset in the ``ocpi.core`` component library.
Implementations include the
:ref:`file_write-HDL-worker` (``file_write.hdl``) and the :ref:`file_write-RCC-worker` (``file_write.rcc``).
Tested platforms include
``centos7``, ``isim``, ``modelsim``, ``xilinx13_3``, ``xilinx13_4``, and ``xsim``.


Design
------
The file write component writes application data to a file. To use it, specify
an instance of it and connect its input port to an output port of the component
that produces the data. Use the ``fileName property`` to specify the name of the file
to be written.

This component has one input port whose name is ``in``, which carries the
messages to be written to the file. There is no protocol associated
with the port, enabling it to be agnostic as to the protocol
of the file data and the connected output port.

Operating Modes
~~~~~~~~~~~~~~~
The file read component has two modes of operation: data-streaming mode and messaging mode.
These modes are similar, but not identical to the :ref:`file_read` component modes.

Data-Streaming Mode
^^^^^^^^^^^^^^^^^^^
In data-streaming mode, the contents of the file become the payloads of the stream
of messages arriving at the input port. No message lengths or opcodes are
recorded in the output file.

Messaging Mode
^^^^^^^^^^^^^^

In messaging mode, the contents of the output file are written as a sequence of defined
messages, with an 8-byte header in the file itself preceding the data for each message
written to the file. This header contains the length and opcode of the message, with the
data contents of the message following the header. The length can be zero, meaning
that a header will be written but no data will follow the header in the file.

The first 32-bit word of the header is written as the message length in bytes, little-endian.
The next 8-bit byte is the opcode of the message, followed by three padding bytes.
For example, in the C language (on a little-endian processor):

.. code-block:: C
		
   struct {
   uint32_t messageLength;
   uint8_t opcode;
   uint8_t padding[3];
   };

This format of messages in a file is the format consumed by the :ref:`file_read` component
when in messaging mode.


Implications for No Protocol on Port
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The component's input port has no protocol specified in order to support
interfacing with any protocol. This means that the created data file is
formatted to match the protocol of the output port of the connected component.

End-of-File Handling
~~~~~~~~~~~~~~~~~~~~
If the file write component receives an EOF indication, it will interpret it as the end
of data and will close the output file and declare itself “finished”, entering the
*finished* state. This is useful when this component is specified as the “finished”
component instance for applications, which is indicated by setting the ``finished``
top-level attribute in the application (OAS) to the instance name of a file write
component. Thus, when the file write component writes out all its data and
receives the EOF, the application is considered finished.

Nothing is written to the output file for the EOF indication.

Interface
---------
.. literalinclude:: ../specs/file_write_spec.xml
   :language: xml

Properties
~~~~~~~~~~
.. ocpi_documentation_properties::

      fileName: The name of the file that is written to disk from the input port.

      messagesInFile: The flag that turns messaging mode on and off.

      bytesWritten: The number of bytes written to the file. Useful when debugging data flow issues.

      messagesWritten: The number of messages written to the file. Useful when debugging data flow issues.

      stopOnEOF: No functionality; exists for backward compatibility.

Ports
~~~~~
.. ocpi_documentation_ports::

   in: Data streamed to file.

Implementations
---------------
.. ocpi_documentation_implementations:: ../file_write.hdl ../file_write.rcc

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
Limitations of ``file_write`` are:

 * None.

Testing
-------
All test benches use the worker implementation as part of the verification process. This component does not have a unit test suite.

.. ocpi_documentation_test_result_summary::
