#!/usr/bin/env python3

# Read OpenCPI data files, when written as a data stream
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


import os
import struct

from .ocpi_protocols import OcpiProtocols
from .ocpi_protocols import OPCODES


class _DataReader:
    """ An iterator and indexable class to read stream data from file

    Implementation class - expected to be accessed by using a
    ``ParseStreamFile`` instance.
    """

    def __init__(self, file, protocol):
        """ Declare _DataReader instance.

        Args:
            file (file handler): An open file handler of the file which
                contains the stream data to be read.
            protocol (Protocol object): The protocol object with pack and
                unpack functions.

        Returns:
            Initialised _DataReader instance.
        """
        self._file = file
        self._protocol = protocol

        self._values_in_file = \
            os.path.getsize(self._file.name) // self._protocol.data_size

        # This stream read assumes always reading opcode 0 (the first opcode),
        # the name of this opcode is needed for the implementation
        self._opcode_name = OPCODES[0]

    def __iter__(self):
        """ Prepare for iterator to start

        Returns:
            Self as iterator.
        """
        self._file.seek(0)
        return self

    def __next__(self):
        """ Get each item when iterating

        Returns:
            Data values.
        """
        raw_data = self._file.read(self._protocol.data_size)
        if len(raw_data) == 0:
            raise StopIteration

        return self._protocol.unpack_data(self._opcode_name, raw_data)[0]

    def __getitem__(self, subscript):
        """ Get a specific data element from file

        Args:
            subscript (``int`` or slice): If an integer the index of the sample
                to be retrieved. If a slice the set of sample indexes to be
                retrieved.

        Returns:
            If subscript is an integer returns the data element. If subscript
                is a slice returns a list where the elements of the list are
                the data elements that match the slice indexes.
        """
        if isinstance(subscript, slice):
            if subscript.start is None:
                start_index = 0
            elif subscript.start < 0:
                start_index = self._values_in_file + subscript.start
            else:
                start_index = subscript.start
            if subscript.stop is None:
                stop_index = self._values_in_file
            elif subscript.stop < 0:
                stop_index = self._values_in_file + subscript.stop
            else:
                stop_index = subscript.stop
            if subscript.step is None:
                step_size = 1
            else:
                step_size = subscript.step

            return [self.__getitem__(index) for index in
                    range(start_index, stop_index, step_size)]
        else:
            # Allow negative indexing
            if subscript < 0:
                subscript = self._values_in_file + subscript

            self._file.seek(subscript * self._protocol.data_size)
            raw_data = self._file.read(self._protocol.data_size)
            return self._protocol.unpack_data(self._opcode_name, raw_data)[0]


class ParseStreamFile:
    """ Read data stream from file written as OpenCPI stream

    Always assumes the stream (first opcode in protocol) type was written to
    file.

    Intended to be used as a context manager (i.e. used with the ``with``
    keyword) and using the ``data`` variable to access the stream samples.
    """

    def __init__(self, file_path, protocol):
        """ Initialised a ``ParseStreamFile`` instance

        Args:
            file_path (``str``): Path of the file to be read. This will be a
                file that has been written to with a stream of data (not
                messages) and the protocol used for the file write was one of
                the timed sample protocols.
            protocol (``str``): Name of the protocol this file relates to.

        Returns:
            Initialised ``ParseStreamFile`` instance.
        """
        self._file_path = file_path
        self._protocol_type = protocol

        self._file = open(file_path, "rb")
        self._file.seek(0)
        self._protocol = OcpiProtocols(protocol)

        #: Indexable and iterable variable to access the samples of the file.
        self.data = _DataReader(self._file, self._protocol)

        self._data_read_index = 0

    def __enter__(self):
        """ Enter context manager

        Returns:
            Self as context manager.
        """
        return self

    def __exit__(self, *_):
        """ Exit context manager

        Sets internal variables that are normally used to access data to
        ``None``.

        Args:
            _ (optional): Input arguments are allowed to support the context
                manager standard format, and support shutdown signals, however
                not used here so just interface formatting.
        """
        self._protocol_type = None
        self._file_path = None
        self._protocol = None

        if self._file is not None:
            self._file.close()
            self._file = None

    def read(self, number_of_values=None):
        """ Read data from file

        Args:
            number_of_values (``int``, optional): If not set, or set to
                ``None`` (default), will read the whole file. Reading the whole
                file can have a performance impact if a large file. If the file
                is large it may be more appropriate to use ``self.data`` to
                access the file content as this can be indexed and iterated
                through.

        Returns:
            Data that has been read. If at the end of the file will return an
                empty list. If more data values are requested than available
                from the current file pointer location, will return all which
                is in file.
        """
        if number_of_values is None:
            data = self.data[self._data_read_index:]
        else:
            data = self.data[self._data_read_index: number_of_values]

        # Update read index (which is like a local file pointer)
        self._data_read_index = self._data_read_index + len(data)

        return data

    def seek(self, index):
        """ Set the read pointer so the next data element index to be read

        Args:
            index (``int``): The data element to start the next
                ``self.read()`` at.
        """
        self._data_read_index = index

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
        return (f"ocpi_protocols.ParseStreamFile({self._file_path}, " +
                f"{self._protocol_type})")

    def __str__(self):
        """ Informal string representation of object

        Returns:
            Informal string representation of object.
        """
        return (f"<ocpi_protocols.ParseStreamFile file={self._file_path} " +
                f"protocol={self._protocol_type}>")
