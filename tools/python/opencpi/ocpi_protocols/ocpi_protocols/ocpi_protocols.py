#!/usr/bin/env python3

# Definition of timed sample protocol set, with sample data packer and unpacker
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


import collections
import decimal
import math
import struct


# Variables that describe the time sample protocol set, and form the "public"
# interface of this protocol set
protocol = collections.namedtuple(
    "protocol", ["complex", "sample_python_type", "max_sample_length"])
PROTOCOLS = {"bool_timed_sample": protocol(False, bool, 16384),
             "uchar_timed_sample": protocol(False, int, 16384),
             "char_timed_sample": protocol(False, int, 16384),
             "complex_char_timed_sample": protocol(True, int, 8192),
             "ushort_timed_sample": protocol(False, int, 8192),
             "short_timed_sample": protocol(False, int, 8192),
             "complex_short_timed_sample": protocol(True, int, 4096),
             "ulong_timed_sample": protocol(False, int, 4096),
             "long_timed_sample": protocol(False, int, 4096),
             "complex_long_timed_sample": protocol(True, int, 2048),
             "ulonglong_timed_sample": protocol(False, int, 2048),
             "longlong_timed_sample": protocol(False, int, 2048),
             "complex_longlong_timed_sample": protocol(True, int, 1024),
             "float_timed_sample": protocol(False, float, 4096),
             "complex_float_timed_sample": protocol(True, float, 2048),
             "double_timed_sample": protocol(False, float, 2048),
             "complex_double_timed_sample": protocol(True, float, 1024)}

# Dictionary values are the opcode values
OPCODES = {"sample": 0,
           "time": 1,
           "sample_interval": 2,
           "flush": 3,
           "discontinuity": 4,
           "metadata": 5}
# Add the reverse mapping to the dictionary, to allow opcodes to be looked up
# by value as well as name.
OPCODES.update(dict(reversed(entry) for entry in OPCODES.items()))


def _interleave_complex(complex_list, return_type=float):
    """ Interleave real and imaginary values from a list of complex values

    Args:
        complex_list (``list``): A list of complex values for the real and
            imaginary values to be taken from.
        return_type (``type``, optional): The type to be returned (e.g.
            ``int``). Default is ``float``.

    Returns:
        List with real and imaginary elements of complex values interleaved.
            First value is real, then second value is imaginary.
    """
    # Preallocating list size is faster than updating list to include length
    # on each iteration
    values = [0.0] * len(complex_list) * 2

    # If the return type is a float then no conversion is need, and for larger
    # data sets the return_type call roughly doubles the run time; so do a
    # single if statement to see if the repeated type conversion function call
    # is needed to save some time in the case of floats.
    if return_type == float:
        for index, value in enumerate(complex_list):
            values[2 * index] = value.real
            values[2 * index + 1] = value.imag
    else:
        for index, value in enumerate(complex_list):
            values[2 * index] = return_type(value.real)
            values[2 * index + 1] = return_type(value.imag)

    return values


class OcpiProtocols:
    """ Definition of values that describe the timed sample protocols
    """
    _SAMPLE_PACK_FORMATS = {
        "bool_timed_sample": "<{data_length}?",
        "uchar_timed_sample": "<{data_length}B",
        "char_timed_sample": "<{data_length}b",
        "complex_char_timed_sample": "<{data_length}b",
        "ushort_timed_sample": "<{data_length}H",
        "short_timed_sample": "<{data_length}h",
        "complex_short_timed_sample": "<{data_length}h",
        "ulong_timed_sample": "<{data_length}L",
        "long_timed_sample": "<{data_length}l",
        "complex_long_timed_sample": "<{data_length}l",
        "ulonglong_timed_sample": "<{data_length}Q",
        "longlong_timed_sample": "<{data_length}q",
        "complex_longlong_timed_sample": "<{data_length}q",
        "float_timed_sample": "<{data_length}f",
        "complex_float_timed_sample": "<{data_length}f",
        "double_timed_sample": "<{data_length}d",
        "complex_double_timed_sample": "<{data_length}d"}
    _SAMPLE_UNPACK_FORMATS = {
        "bool_timed_sample": "f'<{raw_data_length}?'",
        "uchar_timed_sample": "f'<{raw_data_length}B'",
        "char_timed_sample": "f'<{raw_data_length}b'",
        "complex_char_timed_sample": "f'<{raw_data_length}b'",
        "ushort_timed_sample": "f'<{raw_data_length//2}H'",
        "short_timed_sample": "f'<{raw_data_length//2}h'",
        "complex_short_timed_sample": "f'<{raw_data_length//2}h'",
        "ulong_timed_sample": "f'<{raw_data_length//4}L'",
        "long_timed_sample": "f'<{raw_data_length//4}l'",
        "complex_long_timed_sample": "f'<{raw_data_length//4}l'",
        "ulonglong_timed_sample": "f'<{raw_data_length//4}Q'",
        "longlong_timed_sample": "f'<{raw_data_length//4}q'",
        "complex_longlong_timed_sample": "f'<{raw_data_length//4}q'",
        "float_timed_sample": "f'<{raw_data_length//4}f'",
        "complex_float_timed_sample": "f'<{raw_data_length//4}f'",
        "double_timed_sample": "f'<{raw_data_length//8}d'",
        "complex_double_timed_sample": "f'<{raw_data_length//8}d'"}
    _SAMPLE_VALUE_SIZE = {"bool_timed_sample": 1,
                          "uchar_timed_sample": 1,
                          "char_timed_sample": 1,
                          "complex_char_timed_sample": 2,
                          "ushort_timed_sample": 2,
                          "short_timed_sample": 2,
                          "complex_short_timed_sample": 4,
                          "ulong_timed_sample": 4,
                          "long_timed_sample": 4,
                          "complex_long_timed_sample": 8,
                          "ulonglong_timed_sample": 8,
                          "longlong_timed_sample": 8,
                          "complex_longlong_timed_sample": 16,
                          "float_timed_sample": 4,
                          "complex_float_timed_sample": 8,
                          "double_timed_sample": 8,
                          "complex_double_timed_sample": 16}

    def __init__(self, protocol):
        """ Initialise OcpiProtocol instance

        Args:
            protocol (``str``): Name of the protocol to be handled.

        Returns:
            Initialised ``OcpiProtocols`` instance.
        """
        if protocol not in PROTOCOLS:
            raise ValueError(f"{protocol} is not a recognised protocol name")

        self._protocol_type = protocol

        self._pack_format = self._SAMPLE_PACK_FORMATS[protocol]
        self._unpack_format = self._SAMPLE_UNPACK_FORMATS[protocol]
        self.data_size = self._SAMPLE_VALUE_SIZE[protocol]

        # Increase the decimal precision, needed to handle time and sample
        # interval values to their maximum supported accuracy
        decimal.getcontext().prec = 50

    def pack_data(self, opcode, data):
        """ Convert data into raw bytes based on the opcode and protocol

        Args:
            opcode (``str``): Name of opcode for this data.
            data (various): Data to be packed into bytes. Sample data values
                are the most natural Python data types. Time and sample
                interval data values are returned as ``decimal.Decimal`` with
                precision to set to 50. The decimal type is used as time must
                be stored with a greater level of precision than possible with
                a standard Python float.

        Returns:
            Data as packed bytes.
        """
        if opcode == "sample":
            if PROTOCOLS[self._protocol_type].complex:
                data = _interleave_complex(
                    data, PROTOCOLS[self._protocol_type].sample_python_type)

            # Add the length to the format string
            data_format = self._pack_format.format(
                **{"data_length": len(data)})

            try:
                return struct.pack(data_format, *data)
            except struct.error as error_:
                raise ValueError(
                    "Incorrect sample data type for protocol type") from error_

        elif opcode == "time":
            # Converting data to a decimal increases the supported precision of
            # the value and also the precision of the packed data returned.
            data = decimal.Decimal(data)

            if data >= 0:
                units = int(data)
                scaled_fraction = round(
                    (data - units) / decimal.Decimal(2**-64))
                # Only 40 bits of precision are to be used / supported
                scaled_fraction = 0xFFFFFFFFFF000000 & scaled_fraction

            else:
                raise ValueError("Time opcode cannot store negative values")

            return struct.pack("<QL", scaled_fraction, units)

        elif opcode == "sample_interval":
            # Converting data to a decimal increases the supported precision of
            # the value and also the precision of the packed data returned.
            data = decimal.Decimal(data)

            if data >= 0:
                units = int(data)
                scaled_fraction = round(
                    (data - units) / decimal.Decimal(2**-64))
                # Only 40 bits of precision are to be used / supported
                scaled_fraction = 0xFFFFFFFFFF000000 & scaled_fraction

            else:
                raise ValueError(
                    "Sample interval opcode cannot store negative values")

            return struct.pack("<QL", scaled_fraction, units)

        elif opcode == "flush":
            return bytes()

        elif opcode == "discontinuity":
            return bytes()

        elif opcode == "metadata":
            try:
                # As the value field is 64 bit, this will be aligned with 64
                # bit boundary in this data field, so add 32 zero bits of
                # padding between the ID and value fields.
                return struct.pack("<LLQ", data["id"], 0, data["value"])
            except KeyError as error_:
                raise KeyError("Metadata must be a dictionary with keys 'id' "
                               + "and 'value'.") from error_
            except struct.error as error_:
                raise TypeError("Metadata id or value can only be a single" +
                                " integer.") from error_

        else:
            raise ValueError(f"opcode value {opcode} not supported")

        raise Exception("Should never reach this position in the code as " +
                        "all opcodes should return their packed data, or " +
                        "the else report unexpected opcode")

    def unpack_data(self, opcode, raw_data):
        """ Convert raw bytes to true data format based on opcode and protocol

        Args:
            opcode (``str``): Name of opcode of the data to be unpacked.
            raw_data (``bytes``): Data to be interpreted.

        Returns:
            Interpreted data. The type of the data will depend on the opcode
                (and protocol), however the type will be the most natural built
                in Python data type available (e.g. complex numbers will use
                the complex type). Time is returned as a float.
        """
        if opcode == "sample":
            # Add the length of data to the unpack format string, eval() treats
            # the string as an f-string, where raw_data_length is required
            raw_data_length = len(raw_data)
            data = struct.unpack(eval(self._unpack_format), raw_data)

            if PROTOCOLS[self._protocol_type].complex:
                return_format = [complex(0, 0)] * (len(data) // 2)
                for index, (real, imaginary) in enumerate(zip(data[0::2],
                                                              data[1::2])):
                    return_format[index] = complex(real, imaginary)
                return tuple(return_format)
            else:
                return data

        elif opcode == "time":
            # Second block of 32 bits will be zero padding which needs to be
            # ignored.
            data = struct.unpack("<QL", raw_data)
            return decimal.Decimal(data[1]) + (
                decimal.Decimal(data[0]) / decimal.Decimal(2**64))

        elif opcode == "sample_interval":
            # Second block of 32 bits will be zero padding which needs to be
            # ignored.
            data = struct.unpack("<QL", raw_data)
            return decimal.Decimal(data[1]) + (
                decimal.Decimal(data[0]) / decimal.Decimal(2**64))

        elif opcode == "flush":
            return None

        elif opcode == "discontinuity":
            return None

        elif opcode == "metadata":
            # Second block of 32 bits will be zero padding which needs to be
            # ignored.
            data = struct.unpack("<LLQ", raw_data)
            return {"id": data[0], "value": data[2]}

        else:
            raise ValueError(f"opcode value {opcode} not supported")

        raise Exception("Should never reach this position in the code as "
                        + "all opcode conditions should return their data")

    def __repr__(self):
        """ Official string representation of object
        """
        return(f"ocpi_protocols.OcpiProtocols(\"{self._protocol_type}\")")

    def __str__(self):
        """ Informal string representation of object
        """
        return("<ocpi_protocols.OcpiProtocols instance " +
               f"protocol={self._protocol_type}>")
