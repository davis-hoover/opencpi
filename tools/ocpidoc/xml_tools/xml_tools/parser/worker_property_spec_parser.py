#!/usr/bin/env python3

# Class for parsing properties in OWD XML files.
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


class WorkerPropertySpecParser(property_spec_parser.PropertySpecParser):
    """ Class for parsing <property> elements in OWD XML files
    """

    def __init__(self, filename, include_filepaths=["."]):
        """ Initialise property specification parser class.

        Handles parsing an OWD XML file with <property> elements. Properties
        in OWD files can have additional attributes compared to those in
        OCS files.

        Args:
            filename (``string``): File path and name of the XML file to parse.
            include_filepaths (``list``): List of strings containing the
                filepaths to search for a file specified in an XML include
                statement.

        Returns:
            An initialised WorkerPropertySpecParser instance.
        """
        super().__init__(filename=filename,
                         include_filepaths=include_filepaths)

        # Override access values for properties as
        self._access_values = [
            "readback", "readable", "readsync", "writable", "volatile",
            "writesync", "initial", "parameter", "readerror", "writeerror",
            "padding"]

        self._spec_property_access_values = [
            "writable", "writesync", "readsync", "readback", "parameter",
            "readerror", "writeerror"]

    def get_properties(self):
        """ Get list of properties and associated arguments from the OWD XML.

        Stores the properties as a list of dictionaries. Supports property
        elements that are children of other property elements.

        Returns:
            Dictionary containing property name and associated
            arguments. Within the dict Boolean values are of type bool. All
            others are strings. The values of "default" and "value" are always
            strings when present and None when not specified. E.g.
            ``{"<property_name>": {
              "type": {"data_type": "ulong"}
              "access": {"initial":  False, "parameter": False,
                      "readable": False, "readback":  False,
                      "readsync": False, "volatile":  False,
                      "writable": True,  "writesync": False,
                      "readerror": False, "writeerror": False,
                      "padding": False},
              "description": "<description>,
              "default": "<property_default_value>",
              "value": "<property_default_value>"},
            "<property_name2>": {etc.}"}``

            The type dictionary has two optional keys when the type is a
            sequence or an array. When both are present it is a sequence of
            arrays. E.g.
            ``"type": {"data_type": "ulong",
                     "arraydimensions": ["64","2"],
                     "sequencelength": "4"}``

            If "data_type" is "enum" then an addition enum key lists the enums:
            ``"type": {"data_type": "enum",
                     "enum": ["enum_val1","enum_val2"]}``

            If "data_type" is "struct" then an additional "members" key is used
            with a dict containing the name and type of each field in the
            struct. OpenCPI struct members cannot have type struct. E.g:
            ``"type": {"data_type": "struct",
                     "members": {"<member_name>: {
                                  "type": {"data_type": "ulong"}}}}``
        """
        # Run method from parent function.
        # Method was overloaded purely to allow a different docstring.
        return super().get_properties()

    def _get_property(self, property_element):
        """ Get property attributes from a property XML element.

        Args:
            property_element (``xml.etree.ElementTree.Element``):
                Object containing the XML property element from which to
                extract the property arguments from.
        Returns:
            None if a name attribute is not found, else returns a dictionary
            containing property name and associated arguments. Within the dict
            Boolean values are of type bool. All others are strings. The values
            of "default" and "value" are always strings when present and None
            when not specified. E.g.
            ``{"<property_name>": {
              "type": {"data_type": "ulong"}
              "access": {"initial":  False, "parameter": False,
                      "readable": False, "readback":  False,
                      "readsync": False, "volatile":  False,
                      "writable": True,  "writesync": False,
                      "readerror": False, "writeerror": False,
                      "padding": False},
              "description": "<description>,
              "default": "<property_default_value>",
              "value": "<property_default_value>"}}``

            The type dictionary has two optional keys when the type is a
            sequence or an array. When both are present it is a sequence of
            arrays. E.g.
            ``"type": {"data_type": "ulong",
                     "arraydimensions": ["64","2"],
                     "sequencelength": "4"}``

            If "data_type" is "enum" then an addition enum key lists the enums:
            ``"type": {"data_type": "enum",
                     "enum": ["enum_val1","enum_val2"]}``

            If "data_type" is "struct" then an additional "members" key is used
            with a dict containing the name and type of each field in the
            struct. OpenCPI struct members cannot have type struct. E.g:
            ``"type": {"data_type": "struct",
                     "members": {"<member_name>: {
                                  "type": {"data_type": "ulong"}}}}``
        """
        # Run method from parent function.
        # Method was overloaded purely to allow a different docstring.
        return super()._get_property(property_element)

    def get_spec_properties(self):
        """ Get dict of all specproperty elements and associated arguments.

        Parses an OpenCPI worker description (OWD) XML file.
        Stores the spec properties as a list of dictionaries.

        Returns:
            Dictionary containing all spec property names and associated
            arguments. Within the dict Boolean values are of type bool. All
            others are strings. The values of "default" and "value" are always
            strings when present and None when not specified. Access values are
            None when not specified. E.g.
            ``{"<spec_property_name>": {
              "access": {"writable": None, "writesync":  None,
                         "readsync": None, "readback": True,
                         "parameter": None, "readerror": None,
                         "writeerror": None},
              "default": "<property_default_value>",
              "value": "<property_default_value>"},
            "<spec_property_name2>": {etc.}"}``
        """
        spec_property_list = {}
        for spec_property_element in self._xml_root.iter("specproperty"):
            spec_property_ = self._get_spec_property(spec_property_element)
            if spec_property_ is not None:
                spec_property_list.update(spec_property_)
        return spec_property_list

    def _get_spec_property(self, spec_property_element):
        """ Get property attributes from a specproperty XML element.

        Args:
            spec_property_element (``xml.etree.ElementTree.Element``):
                Object containing the XML specproperty element from which to
                extract the property arguments from.
        Returns:
            None if a name attribute is not found, else returns a dictionary
            containing property name and associated arguments. Within the dict
            Boolean values are of type bool. All others are strings. The values
            of "default" and "value" are always strings when present and None
            when not specified. Access values are None when not specified. E.g.
            ``{"<spec_property_name>": {
              "access": {"writable": None, "writesync":  None,
                         "readsync": None, "readback": True,
                         "parameter": None, "readerror": None,
                         "writeerror": None},
              "default": "<property_default_value>",
              "value": "<property_default_value>"}}``
        """
        # Check not just a blank specproperty element
        if spec_property_element.attrib:
            # Check property has a name
            name = self._get_attribute(
                element=spec_property_element,
                attribute="name", optional=False)
            spec_property_ = {name: {}}
            # Get all other attributes
            spec_property_[name]["access"] = self._get_boolean_attributes(
                element=spec_property_element,
                attribute_list=self._spec_property_access_values,
                default=None, optional=True)
            spec_property_[name]["value"] = self._get_attribute(
                element=spec_property_element, attribute="value",
                default=None, optional=True)
            spec_property_[name]["default"] = self._get_attribute(
                element=spec_property_element, attribute="default",
                default=None, optional=True)
            return spec_property_
        else:
            return None
