#!/usr/bin/env python3

# Write OpenCPI data stream file
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


from .ocpi_protocols import OcpiProtocols
from .ocpi_protocols import OPCODES


class WriteStreamFile:
    """ Write stream to an OpenCPI stream file

    Intended to be used as a context manager (i.e. used with the ``with``
    keyword).
    """

    def __init__(self, file_path, protocol):
        """ Initialise a ``WriteStreamFile`` instance

        Args:
            file_path (``str``): File path that is to be written to with a
                stream of data (not messages).
            protocol (``str``): Name of the protocol this file relates to.

        Returns:
            Initialised ``WriteStreamFile`` instance.
        """
        self._file_path = file_path
        self._protocol_type = protocol

        self._file = open(file_path, "wb")
        self._protocol = OcpiProtocols(protocol)

        # This stream write assumes writing opcode 0 (the first opcode), the
        # name of this opcode is needed for the implementation
        self._opcode_name = OPCODES[0]

    def __enter__(self):
        """ Enter context manager

        Returns:
            Self as context manager.
        """
        return self

    def __exit__(self, *_):
        """ Exit context manager

        Sets internal variables that are normally used to access data to None.

        Args:
            _ (optional): Input arguments are allowed to support the context
                manager standard format, and support shutdown signals, however
                not used here - just interface formatting.
        """
        self._file_path = None
        self._protocol_type = None
        self._protocol = None

        if self._file is not None:
            self._file.close()
            self._file = None

    def write(self, data, raw_data=False):
        """ Write data to file as stream

        Args:
            data (various): The data to be written to file. If ``raw_data`` is
                set to ``False`` (default), the data should be in its "native"
                Python type as will be converted to packed bytes before being
                written to file. If ``raw_data`` is set to ``True``, this
                should be bytes in the packed format.

            raw_data (``bool``, optional): Indicates if data is already packed
                and should be written to file in the current format.
        """
        if raw_data is False:
            self._file.write(self._protocol.pack_data(self._opcode_name, data))
        else:
            self._file.write(data)

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
        return (f"ocpi_protocols.WriteStreamFile({self._file_path}, " +
                f"{self._protocol_type})")

    def __str__(self):
        """ Informal string representation of object

        Returns:
            Informal string representation of object.
        """
        return (f"<ocpi_protocols.WriteStreamFile file={self._file_path} " +
                f"protocol={self._protocol_type}>")
