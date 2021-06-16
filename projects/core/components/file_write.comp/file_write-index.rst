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
of the component connected to the input port.

Operating Modes
~~~~~~~~~~~~~~~
The file read component supports data-streaming mode and messaging mode.

Data-Streaming Mode
^^^^^^^^^^^^^^^^^^^
In data-streaming mode, the file contents become the payloads of the stream
of messages arriving at the input port. No message lengths or opcodes are
recorded in the output file.

.. include:: ../file_read.test/doc/snippets/messaging_snippet.rst

Implications for No Protocol on Port
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The component's input port has no protocol specified in order to support
interfacing with any protocol. This means that the created data file is
formatted to match the protocol of the output port of the connected component.

End-of-File Handling
~~~~~~~~~~~~~~~~~~~~
When the file write component receives an end-of-file notification, it
interprets this as the end of data, declares itself "done" and does
not write any further messages to the file.

Interface
---------
.. literalinclude:: ../specs/file_write_spec.xml
   :language: xml

Opcode Handling
~~~~~~~~~~~~~~~
To be supplied: Description of how the non-stream opcodes are handled.

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
