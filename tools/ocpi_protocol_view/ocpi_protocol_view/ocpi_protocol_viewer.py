#!/usr/bin/env python3

# Display messages-in-file files which use timed sample protocols
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


import itertools
import pathlib

from opencpi.ocpi_protocols import ParseMessagesFile


class OcpiProtocolViewer:
    """ Display message-in-file files that use timed sample protocols
    """

    def __init__(self, protocol, files):
        """ Initialise OcpiProtocolViewer

        Args:
            protocol (``str``): Name of the protocol type to be used when
                displaying the files.
            files (``list``): A list of all files to be displayed. When two
                file paths are provided, these will be displayed within 80
                characters on the terminal.

        Returns:
            Initialised OcpiProtocolViewer instance.
        """
        self._protocol = protocol
        default_sample_formats = {
            "bool_timed_sample": "{sample!s:>27}",
            "uchar_timed_sample": "{sample: 27}",
            "char_timed_sample": "{sample: 27}",
            "complex_char_timed_sample":
                " {sample.real: 11} + {sample.imag: 11}j",
            "ushort_timed_sample": "{sample: 27}",
            "short_timed_sample": "{sample: 27}",
            "complex_short_timed_sample":
                " {sample.real: 11} + {sample.imag: 11}j",
            "ulong_timed_sample": "{sample: 27}",
            "long_timed_sample": "{sample: 27}",
            "complex_long_timed_sample":
                " {sample.real: 11} + {sample.imag: 11}j",
            "ulonglong_timed_sample": "{sample: 27}",
            "longlong_timed_sample": "{sample: 27}",
            "complex_longlong_timed_sample":
                " {sample.real: 11} + {sample.imag: 11}j",
            "float_timed_sample": "{sample: 27}",
            "complex_float_timed_sample":
                " {sample.real: 11} + {sample.imag: 11}j",
            "double_timed_sample": "{sample: 27}",
            "complex_double_timed_sample":
                " {sample.real: 11} + {sample.imag: 11}j"}
        self._sample_format = default_sample_formats[protocol]
        self._time_format = "{sample: 34}"
        self._metadata_format = " ID: {id: 4}. Value: {value: 16}"

        # As large files may result in a lot being printed to the terminal any
        # warning messages are likely easily missed when printed at the top, so
        # add here for echoing after the messages and samples have been printed
        # to the terminal.
        self._end_of_print_messages = []

        self._files = []
        for file in files:
            file = pathlib.Path(file).resolve()
            if file.is_file():
                self._files.append(file)
            else:
                self._end_of_print_messages.append(
                    f"{file} does not exist, file has not been displayed")

    def show_headers(self):
        """ Display headers

        Headers contain the opcode type and size of message in bytes.

        Headers of all messages in self._files will be displayed.
        """
        headers = []

        for file in self._files:
            with ParseMessagesFile(file, self._protocol) as messages_file:
                headers.append(messages_file.headers)

        # Print intro row
        column_heading = "            Opcode         (size)"
        top_row = "  # : " + column_heading + (
            f" | {column_heading}") * (len(self._files) - 1)
        print(top_row)

        # Print main text
        for index, messages_header in enumerate(
                itertools.zip_longest(*headers)):
            print_text = (
                f"{index: 3} : {self._get_header_summary(messages_header[0])}")
            for header in messages_header[1:]:
                print_text = (
                    f"{print_text} | {self._get_header_summary(header)}")
            print(print_text)

        self._print_warning_messages()

    def show_messages(self, first_message, message_count=1, first_sample=None,
                      sample_count=None, custom_format=None):
        """ Display a set of messages

        Args:
            first_message (``int``): Index of the first message to be shown.
                Zero indexed.
            message_count (``int``, optional): Number of messages to be shown.
                If not set one message will be shown. If more messages are
                requested than in the file, messages until the end of the file
                will be shown.
            first_sample (``int``, optional): First sample in a sample message
                to show. If not set, or set to None, will show all samples in a
                message.
            sample_count (``int``, optional): Number of samples to show. If not
                set, or set to None, will show samples until the end of a
                message.
            custom_format (``str``, optional): Sample formatting string. Format
                as a Python formatting string, with the variable ``sample``
                contains the value to be printed so needs to be included in the
                format string (e.g. ``{sample:027}``).
        """
        file_handlers = []
        for file in self._files:
            file_handlers.append(ParseMessagesFile(file, self._protocol))

        if custom_format is not None:
            self._sample_format = custom_format
            self._time_format = custom_format
            self._metadata_format = custom_format

        # Print intro row
        column_heading = "Opcode / Sample index             "
        top_row = "  # : " + column_heading + (
            f" | {column_heading}") * (len(self._files) - 1)
        print(top_row)

        # Add a list with a single item of zero to stop an error when there are
        # no valid file handlers.
        last_message_to_show = max(
            [len(handler.headers) for handler in file_handlers] + [0])
        last_message_to_show = min(last_message_to_show,
                                   first_message + message_count)
        for message_index in range(first_message, last_message_to_show):
            # The message description row
            print_text = f"{message_index: 3} : " + self._get_opcode_name(
                file_handlers[0].headers, message_index)
            for handler in file_handlers[1:]:
                print_text = print_text + " | " + self._get_opcode_name(
                    handler.headers, message_index)
            print(print_text)

            messages_opcodes = []
            current_messages = []
            for handler in file_handlers:
                if message_index < len(handler.headers):
                    messages_opcodes.append(
                        handler.headers[message_index]["opcode"])
                    if handler.headers[message_index]["opcode"] == "sample":
                        current_messages.append(
                            handler.messages_data[message_index])
                    else:
                        # Put non-sample data in lists to allow non-steam data
                        # to be handled by iterators like sample data.
                        current_messages.append(
                            [handler.messages_data[message_index]])
                else:
                    messages_opcodes.append(None)
                    current_messages.append([None])

            # If sample index and sample count set, limit the data to be shown
            # to the range described by these variables.
            if first_sample is not None:
                for file_index in range(len(self._files)):
                    if messages_opcodes[file_index] == "sample":
                        if first_sample < len(current_messages[file_index]):
                            current_messages[file_index] = current_messages[
                                file_index][first_sample:]
                        else:
                            current_messages[file_index] = [None]
                    # Only limit number of messages if the first sample index
                    # is set
                    if sample_count is not None:
                        current_messages[file_index] = current_messages[
                            file_index][0:sample_count]
                index_printing = first_sample
            else:
                # Otherwise show all samples
                index_printing = 0

            # Display message
            for sample_index, samples in enumerate(
                    itertools.zip_longest(*current_messages),
                    start=index_printing):
                print_text = "    : " + self._get_sample_entry(
                    messages_opcodes[0], sample_index, samples[0])
                for opcode, sample in zip(messages_opcodes[1:],
                                          samples[1:]):
                    print_text = print_text + " | " + self._get_sample_entry(
                        opcode, sample_index, sample)
                print(print_text)

        for handler in file_handlers:
            handler.close()

        self._print_warning_messages()

    def _get_header_summary(self, header):
        """ Format header summary string

        Args:
            header (``dict``): The header to be summarised.

        Returns:
            String of formatted header.
        """
        if header is not None:
            size_outline = f"({header['size']} bytes)"
            return f"{header['opcode']:>18} {size_outline:>14}"
        else:
            return "                [Out of messages]"

    def _get_opcode_name(self, headers, index):
        """ Format opcode name string

        Args:
            headers (``list``): List of all headers in a file.
            index (``int)``: Index of header in headers to be returned as a
                formatted string.

        Returns:
            String of formatted opcode name.
        """
        if index < len(headers):
            return f"{headers[index]['opcode']: <34}"
        else:
            return "[Out of messages]                 "

    def _get_sample_entry(self, opcode, index, sample):
        """ Format sample entry

        Args:
            sample_message (``str``): Opcode of message sample is from.
            index (``int``): Sample index in message.
            sample (``various``): Sample to be used in formatted string.

        Returns:
            String with formatted sample entry.
        """
        if opcode == "sample":
            sample_entry = f"{index: 5}:"
            if sample is not None:
                sample_entry = sample_entry + " " + self._sample_format.format(
                    sample=sample)
            else:
                sample_entry = sample_entry + "            [Out of samples]"
            return sample_entry

        elif opcode in ["time", "sample_interval"]:
            if sample is not None:
                return self._time_format.format(sample=sample)
            else:
                return "           [No samples to display]"

        # Opcode with no data
        elif opcode in ["flush", "discontinuity"]:
            return "              [Opcode has no data]"

        elif opcode == "metadata":
            if sample is not None:
                return self._metadata_format.format(
                    id=sample["id"], value=sample["value"])
            else:
                return "           [No samples to display]"

        elif opcode is None:
            return "                 [Out of messages]"

        else:
            raise ValueError(f"Unsupported opcode of {opcode}")

    def _print_warning_messages(self):
        """ Print any stored warning messages to terminal
        """
        for message in self._end_of_print_messages:
            print(message)
