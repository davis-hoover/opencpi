#!/usr/bin/env python3

# Class for parsing component specification XML files.
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

import xml.etree.ElementTree as ET

from . import property_spec_parser


class ComponentSpecParser(property_spec_parser.PropertySpecParser):
    """ Class for parsing component specification XML files.
    """

    def __init__(self, filename, include_filepaths=["."]):
        """ Initialize component spec parser class.

        Handles parsing an XML file with the componentspec root tag.

        Args:
            filename (``string``): File path and name of the XML file to parse.
            include_filepaths (``list``): List of strings containing the
                filepaths to search for a file specified in an XML include
                statement.

        Returns:
            An initialized ComponentSpecParser instance.
        """
        super().__init__(filename=filename,
                         include_filepaths=include_filepaths)

        # Check root tag
        root_tag = "componentspec"
        file_root_tag = self._get_root_tag()
        if not file_root_tag == root_tag:
            raise ValueError(
                f"Root XML tag must be {root_tag}, not {file_root_tag}")

    def get_dictionary(self):
        """ Gets a dictionary containing OpenCPI component information.

        Parses an OpenCPI component specification (OCS) XML file.
        Stores the information within a dictionary.

        Returns:
            Python dictionary containing information about the inputs, outputs,
            and properties specified in the parsed XML file. Within the dict
            Boolean values are of type bool. All others are strings. The values
            of "default" and "value" are always strings when present and None
            when not specified. E.g.

            .. code-block:: python

               {"inputs": {"<input_name>": {
                             "protocol": "<protocol_name>",
                             "optional": False},
                           "<input_name2>": {
                             "protocol": "<protocol_name>",
                             "optional": False}},
                "outputs": {"<output_name>": {
                              "protocol": "<protocol_name>",
                              "optional": False}},
                "properties": {"<property_name": {
                                "type": {"data_type": "ulong"}
                                "access": {"initial":  False, "parameter": False,
                                           "volatile":  False, "writable": True},
                                "description": "<description>,
                                "default": "<property_default_value>",
                                "value": "<property_default_value>"}}}

            The type dictionary has two optional keys when the type is a
            sequence or an array. When both are present it is a sequence of
            arrays. E.g.

            .. code-block:: python

               "type": {"data_type": "ulong",
                        "arraydimensions": ["64","2"],
                        "sequencelength": "4"}

            If ``data_type`` is ``enum`` then an addition ``enums`` key lists
            the ``enums``:

            .. code-block:: python

               "type": {"data_type": "enum",
                        "enums": ["enum_val1","enum_val2"]}

            If ``data_type`` is ``struct`` then an additional "members" key is
            used with a dictionary containing the name and type of each field
            in the ``struct``. OpenCPI ``struct`` members cannot have type
            ``struct``. E.g:

            .. code-block:: python

               "type": {"data_type": "struct",
                        "members": {"<member_name>: {
                                     "type": {"data_type": "ulong"}}}}
        """
        dictionary = {}
        dictionary["inputs"] = self.get_input_ports()
        dictionary["outputs"] = self.get_output_ports()
        dictionary["properties"] = self.get_properties()
        return dictionary

    def get_input_ports(self):
        """ Gets a dict of all input ports and associated arguments from the
        parsed XML file.

        Extracts value of the 'name', 'protocol', and 'optional' arguments of
        each input port in the parsed XML file.

        Returns:
            Python dict containing input port names and associated
            attributes. E.g.

            .. code-block:: python

               {"input": {"protocol": "long_protocol", "optional": False},
                "debug": {"protocol": "short_protocol", "optional": True}}
        """
        input_list = {}
        for tag in ["port", "datainterfacespec"]:
            for port in self._xml_root.iter(tag):
                # If producer attribute is not present then port is an input
                if self._is_true(port, "producer"):
                    # Skip output ports
                    continue
                else:
                    # Add to list of inputs
                    input_list.update(self._get_port(port))

        return input_list

    def get_output_ports(self):
        """ Gets a dictionary of all output ports and associated arguments.

        Extracts value of the 'name', 'protocol', and 'optional' arguments of
        each output port in the parsed XML file.

        Returns:
            Python dict containing output port names and associated
            attributes. E.g.

            .. code-block:: python

               {"out": {"protocol": "long_protocol", "optional": False},
               {"debug": {"protocol": "short_protocol", "optional": True}}
        """
        output_list = {}
        for tag in ["port", "datainterfacespec"]:
            for port in self._xml_root.iter(tag):
                # When producer=false skip
                if not self._is_true(port, "producer"):
                    continue
                else:
                    # Add to list of outputs
                    output_list.update(self._get_port(port))

        return output_list

    def _get_port(self, port):
        """ Gets attributes of an XML element with a tag of <port>.

        Extracts value of the 'name', 'protocol', and 'optional' arguments from
        the port element.

        Args:
            port (``xml.etree.ElementTree.Element``): Object containing an XML
                element with a port tag.

        Returns:
            Python dicts containing port attributes. E.g.

            .. code-block:: python

               {"<port_name>": {"protocol": "long_protocol",
                                "optional": False}}
        """
        # Get port name. Raise exception if attribute not found
        name = self._get_attribute(
            element=port, attribute="name", optional=False).strip()
        port_data = {name: {}}
        # Store protocol. If no attribute then store as None
        port_data[name]["protocol"] = self._get_attribute(port, "protocol")
        # Store optional. If no attribute then store as false
        port_data[name]["optional"] = self._is_true(
            element=port, attribute="optional", default=False, optional=True)

        # Get all other port attributes. These are only added to the dict
        # when they are present
        for key, value in port.items():
            if key in ["name", "protocol", "optional", "producer"]:
                continue
            else:
                port_data[name][key] = value

        return port_data
