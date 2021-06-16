.. include this file in Operating Modes section of file_read and file_write component index rst files.

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


Messaging Mode
^^^^^^^^^^^^^^
In messaging mode, the component interprets the file content
as a sequence of defined messages with an 8-byte header in
the file itself preceding the payload for each message.
This header contains the
message length and opcode, with the message data contents following
the header. The length can be zero, which means that a message
will be sent with the indicated opcode and the length of the
message will be zero.

The component interprets the first 32-bit word of the header
as the message length in bytes, little endian. The next 8-bit
byte is the opcode for the message, followed by three
padding bytes. If the component encounters the end of
the file while reading a message header or while reading the
header-specified length of the message payload, it
reports an error and terminates. The messaging file
field layout is shown in the following figure:

.. figure:: ../file_read.test/doc/figures/MessageMode.png
   :alt: Messaging File Field Layout
   :align: center

   Layout of messaging file fields.
