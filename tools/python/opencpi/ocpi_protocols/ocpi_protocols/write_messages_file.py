#!/usr/bin/env python3

# Write OpenCPI data files, when written as messages (not sample)
#
# This file is protected by Copyright. Please refer to the COPYRIGHT file
# distributed with this source distribution.
#
# This file is part of OpenCPI <http://www.opencpi.org>
#
# OpenCPI is free software: you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# OpenCPI is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU Lesser General Public License for
# more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


import struct

from .ocpi_protocols import OcpiProtocols
from .ocpi_protocols import OPCODES


class WriteMessagesFile:
    """ Write message protocols to file

    Intended to be used as a context manager (i.e. used with the ``with``
    keyword).
    """

    def __init__(self, file_path, protocol):
        """ Initialise a ``WriteMessagesFile`` instance

        Args:
            file_path (``str``): Path of the file to be written.
            protocol (``str``): Name of the protocol to use for writing.

        Returns:
            Initialised ``WriteMessagesFile`` instance.
        """
        self._file_path = file_path
        self._protocol_type = protocol
        self._file = open(file_path, "wb")
        self._file.seek(0)

        self._protocol = OcpiProtocols(protocol)

    def __enter__(self):
        """ Enter context manager

        Returns:
            Self as context manager.
        """
        return self

    def __exit__(self, *_):
        """ Exit context manager

        Args:
            _ (optional): Input arguments are allowed to support the context
                manager standard format, and support shutdown signals, however
                not used here - just interface formatting.
        """
        self._protocol = None
        self._protocol_type = None
        self._file_path = None

        if self._file is not None:
            self._file.close()
            self._file = None

    def write_message(self, opcode_name, data=[], raw_data=False):
        """ Write a message to file

        Args:
            opcode_name (``str``): Opcode name.
            data (various, optional): The data to be written to file. If the
                opcode type does not have any data then not required, will
                default to an empty list. If ``raw_data`` is ``False`` then
                this will be the "natural" Python type for this data (e.g. a
                list of complex values for a complex sample). If ``raw_data``
                is ``True`` then will be bytes to be written to file.
            raw_data (``bool``, optional): Indicates if data is raw data and so
                to be written to file without packing into bytes. Defaults to
                ``False``.
        """
        if raw_data is False:
            data = self._protocol.pack_data(opcode_name, data)

        header_opcode = bytes([OPCODES[opcode_name], 0, 0, 0])
        header_size = (len(data)).to_bytes(4, "little")
        self._file.write(header_size + header_opcode)
        self._file.write(data)

    def write_messages(self, headers, messages_data, use_headers_size=False,
                       raw_data=False):
        """ Write multiple messages to file

        Args:
            headers (``list``): A list of dictionaries with at least an
                "``opcode``" key which has the string of the timed sample
                protocol opcode name. If ``use_headers_size`` is set to
                ``True`` then must also include a "``size``" key.
            messages_data (``list``): A list of the messages data which relate
                to the headers provided.
            user_headers_size (``bool``, optional): When set to ``True`` means
                ``messages_data``` will be truncated or padded with zeros to
                ensure it is the size (in bytes) defined in the relevant
                header. Defaults to ``False``, in which case no truncation or
                padding is done.
            raw_data (``bool``, optional): Indicates if data is raw data and so
                to be written to file without packing into bytes. Defaults to
                ``False``.
        """
        if use_headers_size is False:
            for header, data in zip(headers, messages_data):
                self.write_message(header["opcode"], data, raw_data)
        else:
            for header, data in zip(headers, messages_data):
                data = self._protocol.pack_data(header["opcode"], data)
                if len(data) < header["size"]:
                    data = data + bytes([0] * (header["size"] - len(data)))
                elif len(data) > header["size"]:
                    data = data[0:header["size"]]
                else:
                    # Data is the expected length - no action
                    pass

                self.write_message(header["opcode"], data, raw_data=True)

    def write_dict_message(self, message):
        """ Write message currently in dictionary format to file

        Args:
            message (dict): Message to be written to file. Dictionary with the
                keys "``opcode``" and "``data``". "``opcode``" stores a string
                with the opcode name of this message. "``data``" stores the
                data for this message, if any.
        """
        data = self._protocol.pack_data(message["opcode"], message["data"])

        header_opcode = bytes([OPCODES[message["opcode"]], 0, 0, 0])
        header_size = (len(data)).to_bytes(4, "little")
        self._file.write(header_size + header_opcode)
        self._file.write(data)

    def write_dict_messages(self, messages):
        """ Write multiple message currently in dictionary format to file

        Args:
            messages (``list``): List of message to be written to file. Each
                message is a dictionary with the keys "``opcode``" and
                "``data``". "``opcode``" stores a string with the opcode name
                of this message. "``data``" stores the data for this message,
                if any.
        """
        for message in messages:
            self.write_dict_message(message)

    def close(self, *other_arguments):
        """ Close file

        For use when not being used as a context manager.

        Args:
            other_arguments (optional): This is provided to allow shutdown
                triggers to be passed. Not used.
        """
        self.__exit__(*other_arguments)

    def __repr__(self):
        """ Official string representation of object

        Returns:
            Official string representation of object.
        """
        return (f"ocpi_protocols.WriteMessagesFile({self._file_path}, "
                + f"{self._protocol_type})")

    def __str__(self):
        """ Informal string representation of object

        Returns:
            Informal string representation of object.
        """
        return (f"<ocpi_protocols.WriteMessagesFile file={self._file_path}"
                + f"protocol={self._protocol_type}>")
