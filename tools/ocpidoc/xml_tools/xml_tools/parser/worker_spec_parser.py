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
        super().__init__(filename=filename,
                         include_filepaths=include_filepaths)
        self.name = os.path.splitext(os.path.basename(filename))[0]

        # Check root tag
        file_root_tag = self._get_root_tag()
        if file_root_tag == "rccworker":
            self.authoring_model = "rcc"
        elif file_root_tag == "hdlworker" or file_root_tag == "hdldevice":
            self.authoring_model = "hdl"
        elif file_root_tag == "oclworker":
            self.authoring_model = "ocl"
        else:
            raise ValueError(
                f"Invalid root XML tag: {file_root_tag}")

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

        # Get all worker attributes
        for key, value in self._xml_root.attrib.items():
            if key == "name":
                continue
            else:
                dictionary[key] = value

        if self.authoring_model == "hdl":
            dictionary["ports"] = self.get_ports(
                port_type=["streaminterface",
                           "timeinterface",
                           "rawprop",
                           "signal",
                           "devsignal"])
        else:
            dictionary["ports"] = self.get_ports()

        dictionary["properties"] = self.get_properties()
        dictionary["specproperties"] = self.get_spec_properties()

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
        # Get dictionary of just the information from the OWD file.
        worker = self.get_dictionary()

        # Add a flag to all properties just declared in the OWD
        for property_name, property_ in worker["properties"].items():
            worker["properties"][property_name]["worker_property"] = True

        # Get dictionary of just the information from the OCS file.
        component = self.get_component_dictionary(component_spec_file)

        # Add a flag to all properties declared in the OCS.
        for name, property_ in component["properties"].items():
            component["properties"][name]["worker_property"] = False
            # Add all OWD access flags to OCS properties. This means all
            # access attributes will always exist, stopping the user from
            # having to test for existence first.
            for attrib in self._access_values:
                if attrib not in \
                        component["properties"][name]["access"].keys():
                    component["properties"][name]["access"][attrib] = False

        # Copy the component dict as a starting point for the combined dict.
        combined_dictionary = copy.deepcopy(component)
        combined_dictionary["time"] = {}
        combined_dictionary["interfaces"] = {}
        combined_dictionary["other_interfaces"] = {}
        # Copy all basic attributes from worker into combined dict
        for name, property_ in worker.items():
            if name not in ["ports", "properties", "specproperties"]:
                combined_dictionary[name] = property_

        # Add all worker properties into the combined dict
        combined_dictionary["properties"].update(worker["properties"])

        # Apply specproperties to properties
        for name, property_ in worker["specproperties"].items():
            if name not in combined_dictionary["properties"].keys():
                # Ignore specproperties that refer to properties that are not
                # in the OCS.
                continue

            # Update  access values from the specproperty element.
            for value in self._spec_property_access_values:
                # This will override both access properties with both a
                # true or a false value set in a specproperty element.
                # Typically OpenCPI only allows changing a false to a true
                # value, but this is not enforced here.
                if property_["access"][value] is not None:
                    combined_dictionary["properties"][name]["access"][value] =\
                        property_["access"][value]

            # Set the value/default attributes.
            if combined_dictionary["properties"][name]["value"] is None:
                if property_["value"] is not None:
                    combined_dictionary["properties"][name]["value"] =\
                        property_["value"]
                    combined_dictionary["properties"][name]["default"] = None
                elif property_["default"] is not None:
                    combined_dictionary["properties"][name]["default"] =\
                        property_["default"]

        # Apply worker port settings to component ports
        for name, property_ in worker["ports"].items():
            if name in combined_dictionary["inputs"].keys():
                combined_dictionary["inputs"][name].update(property_)
            elif name in combined_dictionary["outputs"].keys():
                combined_dictionary["outputs"][name].update(property_)
            else:
                # Store other interfaces like the time interface that are not
                # specified in the OCS file.
                if property_["type"] == "timeinterface":
                    combined_dictionary["time"][name] = property_
                elif property_["type"] == "rawprop" or \
                        property_["type"] == "signal" or \
                        property_["type"] == "devsignal":
                    combined_dictionary["interfaces"][name] = property_
                else:
                    combined_dictionary["other_interfaces"][name] = property_

        return combined_dictionary

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

    def get_ports(self, port_type=["port"]):
        """ Gets a dictionary of all ports and associated arguments.

        Args:
            port_type (``list``): List of strings containing the names of
                the port elements to search for in the XML file.
        Returns:
            Python dict containing port names, types and associated
            attributes. E.g.

            .. code-block:: python

               {'input': {'type': 'streaminterface', "datawidth": "32"},
                {'time':{'type': 'timeinterface', "secondswidth": "32"}}
        """
        port_list = {}
        for tag in port_type:
            for port in self._xml_root.iter(tag):
                name = self._get_attribute(
                    element=port, attribute="name", optional=False).strip()
                port_list[name] = {"type": tag}

                # Add attributes and their default values here to ensure
                # they are displayed in the generated documentation if
                # they are left unspecified
                if port.tag == "rawprop":
                    port_list[name].update({"master": "false"})
                if port.tag == "devsignal":
                    port_list[name].update({"count": "1",
                                            "optional": "false",
                                            "master": "false",
                                            "signals": "unspecified"})

                # Get all port attributes
                for key, value in port.items():
                    if key == "name":
                        continue
                    else:
                        port_list[name][key] = value

        return port_list
