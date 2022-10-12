#!/usr/bin/env python3

# Class for parsing worker specification XML files.
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
import xml.etree.ElementTree as ET
import copy

from . import worker_property_spec_parser
from . import component_spec_parser


class WorkerSpecParser(worker_property_spec_parser.WorkerPropertySpecParser):
    """ Class for parsing worker specification XML files.
    """

    def __init__(self, filename, include_filepaths=["."]):
        """ Initialize worker spec parser class.

        Handles parsing an XML file with the XYZWorker root tag. e.g. RccWorker

        Args:
            filename (``string``): File path and name of the XML file to parse.
            include_filepaths (``list``): List of strings containing the
                file paths to search for a file specified in an XML include
                statement.
        Returns:
            An initialized WorkerSpecParser instance.
        """
        super().__init__(filename=filename, include_filepaths=include_filepaths)
        # Capture the name determined by the base class init
        self.name = os.path.splitext(os.path.basename(self._filename))[0]
        self.authoring_model = self._xml_root.attrib["model"]

    def get_dictionary(self):
        """ Gets a dictionary containing OpenCPI worker information.

        Parses an OpenCPI worker description (OWD) XML file.
        Stores the information within a dictionary.

        Returns:
            Python dictionary containing information about the ports and
            properties specified in the parsed OWD XML file. Within the dict
            Boolean values are of type bool. All others are strings. The values
            of "default" and "value" are always strings when present and None
            when not specified. E.g.

            .. code-block:: python

              {"name": "<worker_name>",
               "authoring_model": "hdl",
               "ports": {"<port_name>": {
                           "type": "streaminterface",
                           "datawidth": "16"}},
               "specproperties": {"<specproperty_name>": {
                                    "access": {
                                        "writable": None, "writesync": None,
                                        "readsync": None, "readback": True,
                                        "parameter": None, "readerror": None,
                                        "writeerror": None},
                                    "default": "<property_default_value>",
                                    "value": "<property_default_value>"}},
               "properties": {"<property_name>": {
                               "type": {"data_type": "ulong"}
                               "access": {
                                   "initial":  False, "parameter": False,
                                   "readback": False, "readsync": False,
                                   "volatile": False, "writable": True,
                                   "writesync": False, "readerror": False,
                                   "writeerror": False, "padding": False},
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

            If "data_type" is ``struct`` then an additional "members" key is
            used with a dictionary containing the name and type of each field
            in the ``struct``. OpenCPI ``struct`` members cannot have type
            ``struct``. E.g:

            .. code-block:: python

               "type": {"data_type": "struct",
                        "members": {"<member_name>: {
                                        "type": {"data_type": "ulong"}}}}

            In addition to the above structure all attributes of the XYZWorker
            element are saved in the root of the dictionary with the attribute
            name as the key and the attribute value as the string value.
        """
        dictionary = {}

        # Check for name attribute, otherwise set name to filename.
        name = self._get_attribute(
            element=self._xml_root, attribute="name",
            optional=True, default=None)
        if name:
            dictionary["name"] = name.strip()
        else:
            dictionary["name"] = self.name

        dictionary["authoring_model"] = self.authoring_model
        dictionary["path"] = self._filename
        # Get all worker attributes
        for key, value in self._xml_root.attrib.items():
            if key == "name":
                continue
            else:
                dictionary[key] = value
        # Get ports, and add to "inputs", "outputs" and other lists
        port_list = {}
        # The other sphinx extension code never tests for non-existent dictionary entries...
        dictionary["inputs"] = {}
        dictionary["outputs"] = {}
        dictionary["time"] = {}
        dictionary["signals"] = {}
        dictionary["interfaces"] = {}
        dictionary["other_interfaces"] = {}
        for port in self._xml_root.iter("port"):
            name = self._get_attribute(element=port, attribute="name", optional=False)
            type = port.get("type")
            port_list[name] = {"type": type}
            # Get all port attributes
            for key, value in port.items():
                if key != "name":
                    port_list[name][key] = value
            producer = self._is_true(port, "producer", None, True)
            if producer != None:
                protocol = port.find("protocol")
                if protocol:
                    protocol_name = protocol.get("name")
                else:
                    protocol_name = "None"
                dictionary["outputs" if producer else "inputs"][name] = {
                    "protocol" : protocol_name,
                    "optional" : self._is_true(port, "optional", False, True)
                }
            elif type in ["devsignal", "rawprop"]:
                dictionary["interfaces"][name] = port_list
        dictionary["ports"] = port_list
        dictionary["properties"] = self.get_properties()
        dictionary["specproperties"] = self.get_spec_properties()
        dictionary["supports"] = self.get_supports()
        return dictionary

    def get_combined_dictionary(self, component_spec_file=None):
        """ Gets a dictionary containing OpenCPI worker / component information

        Parses an OpenCPI worker description (OWD) XML file and an OpenCPI
        component specification (OCS) XML file.
        Combines the information and stores it within a dictionary.

        Args:
            component_spec_file (``string``): File path and name of the OCS
                XML file.

        Returns:
            Python dictionary containing information about the ports and
            properties specified in the parsed OWD XML and OCS file. Within the
            dict Boolean values are of type bool. All others are strings. The
            values of "default" and "value" are always strings when present and
            None when not specified. E.g.

            .. code-block:: python

               {"name": "<worker_name>",
               "authoring_model": "hdl",
               "inputs": {"<input_name>": {
                             "protocol": "<protocol_name>",
                             "optional": False},
                          "<input_name2>": {
                             "protocol": "<protocol_name>",
                             "optional": False}},
               "outputs": {"<output_name>": {
                             "protocol": "<protocol_name>",
                             "optional": False}},
               "time": {"<time_name>": {
                             "type": "timeinterface",
                             "fractionwidth": "16"}},
               "interfaces": {"<interface_name>": {
                             "type": "devsignal",
                             "master": True}},
               "other_interfaces": {"<interface_name>": {
                             "type": "otherinterface",
                             "default": True}},
               "properties": {"<property_name>": {
                               "type": {"data_type": "ulong"}
                               "access": {
                                   "initial":  False, "parameter": False,
                                   "readback": False, "readsync": False,
                                   "volatile": False, "writable": True,
                                   "writesync": False, "readerror": False,
                                   "writeerror": False, "padding": False},
                               "description": "<description>,
                               "default": "<property_default_value>",
                               "value": "<property_default_value>",
                               "worker_property": False}}}

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

            If ``data_type`` is ``struct``" then an additional "members" key is
            used with a dictionary containing the name and type of each field
            in the ``struct``. OpenCPI ``struct``` members cannot have type
            ``struct``. E.g:

            .. code-block:: python

               "type": {"data_type": "struct",
                        "members": {"<member_name>: {
                                        "type": {"data_type": "ulong"}}}}

            In addition to the above structure all attributes of the XYZWorker
            element are saved in the root of the dictionary with the attribute
            name as the key and the attribute value as the string value.

            In addition to the above structure all attributes of port elements
            are saved (within each named port dictionary) with the attribute
            name as the key and the attribute value as the string value.
        """
        # Get dictionary from the OWD, which contains the spec information too
        worker = self.get_dictionary()
        return worker

    def get_component_dictionary(self, component_spec_file=None):
        """ Get dictionary containing component specification.

        If a component specification file is specified then it is parsed
        using ComponentSpecParser. If a component specification is not
        specified then an empty OCS dictionary is returned.

        Args:
            component_spec_file (``string``): File path and name of the OCS
                XML file.

        Returns:
            An dictionary containing the result of the
            ```ComponentSpecParser(file).get_dictionary()`` method.
        """
        if component_spec_file:
            # If component spec file is specified then try and open it
            component = component_spec_parser.ComponentSpecParser(
                filename=component_spec_file,
                include_filepaths=self._include_filepaths)
            return component.get_dictionary()
        else:
            print("WARNING: Worker component specification file was not found")
            empty_spec = {"properties": {},
                          "inputs": {},
                          "outputs": {}}
            return empty_spec

    def get_ports(self, port_types=None):
        """ Gets a dictionary of all ports and associated arguments.

        Args:
            port_types (``list``): List of strings containing the types of
                the port elements to search for in the XML file.  If None,
                take all ports
        Returns:
            Python dict containing port names, types and associated
            attributes. E.g.

            .. code-block:: python

               {'input': {'type': 'streaminterface', "datawidth": "32"},
                {'time':{'type': 'timeinterface', "secondswidth": "32"}}
        """
        port_list = {}
        for port in self._xml_root.iter("port"):
            name = self._get_attribute(element=port, attribute="name", optional=False)
            port_list[name] = {"type": tag}
            # Get all port attributes
            for key, value in port.items():
                if key != "name":
                    port_list[name][key] = value


        for tag in port_type:
            for port in self._xml_root.iter(tag):
                name = self._get_attribute(
                    element=port, attribute="name", optional=True)
                # Signal definitions do not require a name attribute
                if name is None:
                    name = "None"
                else:
                    name.strip()
                port_list[name] = {"type": tag}
                # Get all port attributes
                for key, value in port.items():
                    if key == "name":
                        continue
                    else:
                        port_list[name][key] = value

        return port_list

    def get_supports(self):
        """ Gets a dictionary of all supports relationships.
        The key is the worker, and the value is a dictionary of connections
        The connection dictionary's key is the worker's port, and the value is
        a tuple of supported worker port and index
        """
        supports_list = {}
        for supports in self._xml_root.iter("supports"):
            connections = {}
            for connect in supports.iter("connect"):
                connections[connect.attrib["port"]] = connect.attrib["to"], connect.attrib.get("index")
            supports_list[supports.attrib["worker"]] = connections
        return supports_list
