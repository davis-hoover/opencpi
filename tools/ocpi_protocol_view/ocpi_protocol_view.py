#!/usr/bin/env python3

# Command line script to view messages in file
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


import argparse
import sys

from ocpi_protocol_view import ocpi_protocol_viewer
from opencpi.ocpi_protocols import PROTOCOLS


assert sys.version_info >= (3, 6), \
    "ocpi_protocol_viewer must be run with Python 3.6."


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
            description="View and compare 'messages-in-file file that use "
            + "timed sample protocols.",
        usage="%(prog)s [-h] [-m index [-n count] [-s sample] [-p points]] "
              + "protocol file [files ...]")

    parser.add_argument("protocol", type=str, choices=PROTOCOLS.keys(),
                        help="Protocol of file(s) to be inspected.")
    parser.add_argument("files", type=str, nargs="+",
                        help="Path of file(s) to be viewed.")
    parser.add_argument(
        "-m", "--message", type=int, dest="index",
        help="Display specific message, zero indexed. If not set headers will "
             + "be reported.")
    parser.add_argument(
        "-n", "--number", type=int, required=False, dest="count", default=1,
        help="Display n messages. Can only be used when -m / --message set.")
    parser.add_argument(
        "-s", "--sample", type=int, required=False,
        help="Show particular sample from message. Can only be used when -m / "
             + "--message set and -n / --number not set.")
    parser.add_argument(
        "-p", "--points", type=int, required=False, default=1,
        help="Show the number of sample points. Can only be used when -s / "
             + "--sample set.")
    parser.add_argument(
        "-f", "--format", type=str, required=False, default=None,
        help="Set the sample print format. Uses Python 3 formatting syntax "
             + "with value to be displayed called sample (e.g. {sample:027})")

    arguments = parser.parse_args()

    viewer = ocpi_protocol_viewer.OcpiProtocolViewer(arguments.protocol,
                                                     arguments.files)
    if arguments.index is None:
        viewer.show_headers()
    else:
        viewer.show_messages(arguments.index, arguments.count,
                             arguments.sample, arguments.points,
                             arguments.format)
