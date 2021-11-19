#!/usr/bin/env python3

# Read OpenCPI data files, when written as messages (not sample)
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


HEADER_LENGTH = 8       # Header size of messages written to file, in bytes


class _MessageReader:
    """ Read messages (header and data) from file

    As protocol files could be large this does not read in the whole file at
    once, but reads just the headers initially, then when specific messages are
    requested, by indexing, seeks to that message in the file and reads it.

    Written as an iterator and indexable class.

    Implementation class - expected to be accessed by using a
    ``ParseMessagesFile`` instance.
    """

    def __init__(self, file, headers):
        """ Initialise a message reader

        Args:
            file (file handler): An open file handler of the file which
                contains the messages to be read.
            headers (list): List of dictionaries, where each element in the
                list is a dictionary with an opcode and size field which is
                from the header of the message written to file.

        Returns:
            An initialised MessageReader instance.
        """
        # Input argument checks
        if (not hasattr(file, "read")) or (not hasattr(file, "seek")):
            raise TypeError("file passed to MessageReader() must behave "
                            + "like a file pointer / file-like object, "
                            + f"{type(file).__name__} does not")
        if not all(
                ["opcode" in header and "size" in header
                 for header in headers]):
            raise ValueError("opcode and size must be in all header entries")

        self._file = file
        self._headers = headers

    def __iter__(self):
        """ Set up an iterator

        Returns:
            Self as iterator.
        """
        self._file.seek(0)
        self._index = 0
        return self

    def __next__(self):
        """ Get each item when iterating

        Returns:
            The raw message (both header and data) as bytes.
        """
        if self._index >= len(self._headers):
            raise StopIteration

        raw_message = self._file.read(HEADER_LENGTH +
                                      self._headers[self._index]["size"])
        self._index = self._index + 1
        return raw_message

    def __getitem__(self, subscript):
        """ Get a specific message from the file

        Args:
            subscript (``int`` or slice): If an integer, will be the index of
                the mesage to be retrieved. If a slice the set of message
                indexes to be retrieved from file.

        Returns:
            If subscript is an integer returns the raw message (header and
                data) bytes. If subscript is a slice returns a list where the
                elements of the list are the raw messages the slice indexed.
        """
        if isinstance(subscript, slice):
            if subscript.start is None:
                start_index = 0
            else:
                start_index = subscript.start
            if subscript.stop is None:
                stop_index = len(self._headers)
            else:
                stop_index = subscript.stop
            if subscript.step is None:
                step_size = 1
            else:
                step_size = subscript.step
            start_index = min(start_index, len(self._headers))
            stop_index = min(stop_index, len(self._headers))

            # Get sequential messages. Read will update seek position, so no
            # need to manually set the file pointer's position in the file in
            # this case.
            if step_size == 1:
                self._seek_to_message(start_index)
                return_list = [
                    self._file.read(HEADER_LENGTH +
                                    self._headers[index]["size"])
                    for index in range(start_index, stop_index)]
                return return_list

            else:
                get_message_indexes = range(start_index, stop_index, step_size)
                messages = []
                for index in get_message_indexes:
                    # Use the single element retrieval form of this function to
                    # get each element for the returned list
                    messages.append(self._get_single_message(index))
                return messages

        # Just get a single message from file
        else:
            if subscript < 0:
                subscript = len(self._headers) + subscript
            return self._get_single_message(subscript)

    def _seek_to_message(self, seek_index):
        """ Move file pointer to start of a particular message

        Args:
            seek_index (``int``): Index of the message in the file to move the
                pointer to the start of. Pointer will be at start of header
                (before the data). Indexing the same as used for
                ``self._headers``.
        """
        seek_position = 0
        for header in self._headers[:seek_index]:
            seek_position = seek_position + HEADER_LENGTH + header["size"]

        self._file.seek(seek_position, 0)

    def _get_single_message(self, index):
        """ Get a single message from the file

        Args:
            index (``int``): The message to be read from file.

        Returns:
            The bytes that make up the message on disk (as a message contains
            the header and data body).
        """
        # This method is included, rather than keeping as part of __getitem__()
        # as when classes which inherit this class do a __getitem__() call the
        # input argument could be a slice or a single integer, with these
        # different argument types leading to different expected behaviour.
        # Previously this had called the __getitem__() method from itself.
        # However, if a parent __getitem__() call was from a child call of
        # super().__getitem__(), where the parent uses self.__getitem__() as
        # part of its __getitem__() implementation, then this does not function
        # as intended. This method call from itself with same method name
        # existing in both the parent and child classes leads to the child's
        # method with the same name being called, at the parents
        # self.__getitem__() execution. This occurs since self will still be
        # the child class and the module resolution order (MRO) will be for
        # the child class. MRO is the Python concept that describes how
        # methods are searched for within the class inheritance structure. By
        # splitting this functionality into a separate method the call within
        # the parent __getitem__() no longer calls to the child implementation
        # (so long as this method name is not duplicated in any child classes).
        # This behaviour was seen with __getitem__() as the method name in
        # child and parent could not be made different as a special method
        # name.
        #
        # The result of this very long comment is to express that the
        # functionality here must be kept as a separate method, and not rely on
        # calling __getitem__() from itself, against self.
        self._seek_to_message(index)
        return self._file.read(HEADER_LENGTH + self._headers[index]["size"])


class _MessageRawDataReader(_MessageReader):
    """ An iterator and indexable class to read raw message data from file

    This class only returns raw data bytes from messages (i.e. not the header).
    Uses ``MessageReader`` as the class which interacts with the file.

    Implementation class - expected to be accessed by using a
    ``ParseMessagesFile`` instance.
    """

    def __next__(self):
        """ Get each item when iterating

        Returns:
            The raw data message (no header) as bytes.
        """
        # Drop the header and just return data portion of message
        return super().__next__()[HEADER_LENGTH:]

    def __getitem__(self, subscript):
        """ Get a specific message's raw data from file

        Args:
            subscript (``int`` or slice): If an integer is the index of the
                message for which the data is to be retrieved. If a slice then
                set of message indexes for the data of to be retrieved.

        Returns:
            If subscript is an integer returns the raw message data. If
                subscript is a slice returns a list where the elements of the
                list are the message's raw data the slice indexes.
        """
        # Drop the header and just return data portion of message
        if isinstance(subscript, slice):
            return [raw_message[HEADER_LENGTH:] for
                    raw_message in super().__getitem__(subscript)]

        else:
            return super().__getitem__(subscript)[HEADER_LENGTH:]


class _MessageDataReader(_MessageRawDataReader):
    """ An iterator and indexable class to read message data from file

    This class only returns the data from messages (i.e. not the header).
    Uses ``MessageReader``, inherited by ``MessageRawDataReader``, as the class
    which actually interacts with the file.

    Implementation class - expected to be accessed by using a
    ``ParseMessagesFile`` instance.
    """

    def __init__(self, file, protocol, headers):
        """ Declare MessageDataReader instance.

        Args:
            file (file handler): An open file handler of the file which
                contains the messages to be read.
            protocol (Protocol object): The protocol object with pack and
                unpack functions.
            headers (``list``): List of dictionaries, where each element in the
                list is a dictionary with an opcode and size field which is
                from the header of the message written to file.

        Returns:
            Initialised ``MessageDataReader`` instance.
        """
        self._protocol = protocol
        super().__init__(file, headers)

    def __next__(self):
        """ Get each item when iterating

        Returns:
            The data message.
        """
        # Header must be stored first as super().__next__ will update the
        # iterator index
        if self._index >= len(self._headers):
            raise StopIteration
        header = self._headers[self._index]
        raw_data = super().__next__()

        return self._protocol.unpack_data(header["opcode"], raw_data)

    def __getitem__(self, subscript):
        """ Get a specific message's data from file

        Args:
            subscript (``int`` or slice): If an integer is the index of the
                message for which the data is to be retrieved. If a slice then
                set of message indexes for the data of to be retrieved.

        Returns:
            If subscript is an integer returns the message data. If subscript
                is a slice returns a list where the elements of the list are
                the message's data the slice indexes.
        """
        raw_data = super().__getitem__(subscript)

        if isinstance(subscript, slice):
            return [self._protocol.unpack_data(header["opcode"], data) for
                    header, data in zip(self._headers[subscript], raw_data)]
        else:
            return self._protocol.unpack_data(
                self._headers[subscript]["opcode"], raw_data)


class ParseMessagesFile:
    """ Read message protocols from file written with OpenCPI messages

    Intended to be used as a context manager (i.e. used with the ``with``
    keyword) and then using the ``headers`` and ``messages_data`` variables of
    a class instance to interact with the data.
    """

    def __init__(self, file_path, protocol, number_of_messages=None):
        """ Initialised a ParseMessagesFile instance

        Args:
            file_path (str): Path of the file to be read. This will be a file
                that has been written to with messages (not a data sample) and
                the protocol used for the file write was one of the timed
                sample protocols.
            protocol (str): Name of the protocol this file relates to.
            number_of_messages (``int``, optional): If not set, or set to
                ``None`` (default), will parse the whole file. Otherwise the
                file is truncated in size to contain up to this many messages.

        Returns:
            Initialised ``ParseMessagesFile`` instance.
        """
        self._file_path = file_path
        self._protocol_type = protocol
        self._number_of_messages = number_of_messages

        self._file = open(file_path, "rb+")
        self._file.seek(0)
        self._protocol = OcpiProtocols(protocol)

        #: A list of the headers (opcode type and size in bytes) of the
        #: messages in the file being read
        self.headers = []

        # Import the headers
        if self._number_of_messages == 0:
            raw_header = b"";
        else:
            raw_header = self._file.read(HEADER_LENGTH)

        while raw_header != b"":
            (data_size, opcode_value) = struct.unpack("<IBxxx", raw_header)
            opcode_name = OPCODES[opcode_value]
            self.headers.append({"opcode": opcode_name, "size": data_size})
            # Move past the data body
            self._file.seek(data_size, 1)
            if self._number_of_messages is not None:
                # Limit number of messages in file
                if len(self.headers) >= self._number_of_messages:
                    self._file.truncate()
            raw_header = self._file.read(HEADER_LENGTH)

        #: Access the raw data (as the bytes are saved in the file) of the
        #: messages in the file. Is an iterator and can be accessed using an
        #: index which matches that of the message in ``self.headers``. Padding
        #: bytes are not removed, so are included in the output.
        self.messages_raw_data = _MessageRawDataReader(self._file,
                                                       self.headers)

        #: Access the data (as the bytes are saved in the file) of the messages
        #: in the file, with the data being in the most natural Python type for
        #: that data. Is an iterator and can be accessed using an index which
        #: matches that of the message in ``self.headers``.
        self.messages_data = _MessageDataReader(self._file, self._protocol,
                                                self.headers)

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
                not used here so just interface formatting.
        """
        self.headers = None
        self.messages_raw_data = None
        self.messages_data = None
        self._file_path = None
        self._protocol_type = None

        self._protocol = None

        if self._file is not None:
            self._file.close()
            self._file = None

    def get_all_messages(self, only_opcodes=["all"]):
        """ Read all messages from file

        Args:
            only_opcodes (``list``, optional): Only return the opcodes defined
                in this list when reading the file. "``all``" is a special case
                where all opcodes are returned, this is the default value.

        Returns:
            List which contains all messages in the file which have an opcode
                that matches one of the values in only_opcodes. Each element in
                the list is a dictionary which has the keys "``opcode``" and
                "``data``".
        """
        if "all" in only_opcodes:
            return [{"opcode": header["opcode"], "data": data} for
                    header, data in zip(self.headers, self.messages_data)]
        else:
            messages = []
            for header, data in zip(self.headers, self.messages_data):
                if header["opcode"] in only_opcodes:
                    messages.append({"opcode": header["opcode"], "data": data})
            return messages

    def get_sample_data(self, split_on=[], stop_on=[]):
        """ Read sample data from file.

        All data will be returned in a single list (i.e. consecutive sample
        message data will be concatenated). Unless ``split_on`` has any opcode
        types set, in which case a list of lists will be returned where the
        data will be split into a sub-list at every opcode type stated in
        ``split_on``.

        All sample messages in a file will be read until the first message with
        an opcode type stated in ``stop_on`` is reached. If ``stop_on`` is an
        empty list the whole file will be read.

        Args:
            split_on (``list``): A list of strings. Each string is the name of
                an opcode that the method should split into separate lists.
                If empty will return a single list of the sample data. If no
                messages with the opcode type which matches any of the
                ``split_on`` strings is found, will return a single list within
                a list. Consecutive messages in the file that have an opcode
                that matches a ``split_on`` value, but do not have sample data
                between them will result in an empty list being included in the
                parent list.
            stop_on (``list``): A list of strings. Each string is the
                name of an opcode that the method should stop reading the file
                upon detecting.

        Returns:
            A list of all the sample data, if ``split_on`` is empty. Or a list
                of lists of the sample data, is ``split_on`` is not empty.
        """
        sample_data = []
        if len(split_on) == 0:
            for header, data in zip(self.headers, self.messages_data):
                if header["opcode"] in stop_on:
                    break
                if header["opcode"] == "sample":
                    sample_data = sample_data + list(data)
        else:
            sample_data.append([])
            for header, data in zip(self.headers, self.messages_data):
                if header["opcode"] in stop_on:
                    break
                if header["opcode"] in split_on:
                    sample_data.append([])
                if header["opcode"] == "sample":
                    sample_data[-1] = sample_data[-1] + list(data)

        return sample_data

    def get_sample_data_length(self, length_in_samples=True):
        """ Report the sample data length

        Return the length of all sample messages in the file.

        It is significantly quicker to use this method than use
        ``len(self.get_sample_data())`` especially when the sample data file
        being read is large.

        Args:
            length_in_samples (``bool``, optional): When set to true (default)
                the length returned will be the number of samples in all sample
                messages. When set to false, will be the number of bytes the
                sample messages take up when saved to disk.

        Returns:
            Integer of the length of all sample data in the file, in either
                samples or bytes based on what ``length_in_samples`` is set to.
        """
        sample_data_length = 0
        for header in self.headers:
            if header["opcode"] == "sample":
                sample_data_length = sample_data_length + header["size"]

        if length_in_samples is True:
            return sample_data_length // self._protocol.data_size
        else:
            return sample_data_length

    def close(self, *other_arguments):
        """ Close file

        For use when not being used as a context manager.

        Args:
            other_arguments (optional): Provided to allow shutdown triggers to
                be passed. Not used.
        """
        self.__exit__(*other_arguments)

    def __repr__(self):
        """ Official string representation of object

        Returns:
            Official string representation of object.
        """
        return (f"ocpi_protocols.ParseMessagesFile({self._file_path}, "
                + f"{self._protocol_type})")

    def __str__(self):
        """ Informal string representation of object

        Returns:
            Informal string representation of object.
        """
        return (f"<ocpi_protocols.ParseMessagesFile file={self._file_path} "
                + f"protocol={self._protocol_type}>")
