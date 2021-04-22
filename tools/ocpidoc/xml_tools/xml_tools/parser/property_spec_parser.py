#!/usr/bin/env python3

# Class for parsing properties in OCS and OWD XML files.
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

from . import base_parser


class PropertySpecParser(base_parser.BaseParser):
    """ Class for parsing <property> elements in XML files
    """

    def __init__(self, filename, include_filepaths=["."]):
        """ Initialise property specification parser class.

        Handles parsing an XML file with <property> elements.

        Args:
            filename (``string``): File path and name of the XML file to parse.
            include_filepaths (``list``): List of strings containing the
                filepaths to search for a file specified in an XML include
                statement.

        Returns:
            An initialised PropertySpecParser instance.
        """
        super().__init__(filename=filename,
                         include_filepaths=include_filepaths,
                         force_lowercase=True)

        self._access_values = ["writable", "volatile", "initial", "parameter",
                               "readable"]

    def get_properties(self):
        """ Get list of properties and associated arguments.

        Parses an OpenCPI component specification (OCS) or worker description
        (OWD) XML file.
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
                         "writable": False, "volatile":  False,
                         "readable": False},
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
        property_list = {}
        for property_element in self._xml_root.iter("property"):
            property_ = self._get_property(property_element)
            if property_ is not None:
                property_list.update(property_)
        return property_list

    def _get_property(self, property_element):
        """ Get property attributes from a property XML element.

        Args:
            property_element (``xml.etree.ElementTree.Element``): Object
                containing the XML property element from which to extract the
                property arguments from.
        Returns:
            None if a name attribute is not found, else returns a dictionary
            containing property name and associated arguments. Within the dict
            Boolean values are of type bool. All others are strings. The values
            of "default" and "value" are always strings when present and None
            when not specified. E.g.
            ``{"<property_name>": {
              "type": {"data_type": "ulong"}
              "access": {"initial":  False, "parameter": False,
                         "writable": False, "volatile":  False,
                         "readable": False},
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
                     "enums": ["enum_val1","enum_val2"]}``

            If "data_type" is "struct" then an additional "members" key is used
            with a dict containing the name and type of each field in the
            struct. OpenCPI struct members cannot have type struct. E.g:
            ``"type": {"data_type": "struct",
                     "members": {"<member_name>: {
                                  "type": {"data_type": "ulong"}}}}``
        """
        # Check not just a blank property element
        if property_element.attrib:
            # Check property has a name
            name = self._get_attribute(
                element=property_element, attribute="name", optional=False)
            property_ = {name: {}}
            # Get all other attributes
            property_[name]["type"] = self._get_property_type(property_element)
            property_[name]["access"] = self._get_boolean_attributes(
                element=property_element, attribute_list=self._access_values,
                default=False, optional=True)
            property_[name]["description"] = self._get_description(
                property_element)
            property_[name]["value"] = self._get_attribute(
                element=property_element, attribute="value",
                default=None, optional=True)
            property_[name]["default"] = self._get_attribute(
                element=property_element, attribute="default",
                default=None, optional=True)
            return property_
        else:
            return None

    def _get_property_type(self, property_element, member_element=False):
        """ Get property type attributes from a property or member XML element.

        Args:
            property_element (``xml.etree.ElementTree.Element``): Object
                containing the XML property or member element from which
                to extract the property/member arguments from.
            member_element (``bool``): When True element is <member>. When
                False element is <property>. Member elements cannot have type
                "struct", otherwise the type attributes of <property> and
                <member> elements are parse in the same way.

        Returns:
            Returns a dictionary containing property type arguments. Within the
            dict Boolean values are of type bool. All others are strings. The
            values of "default" and "value" are always strings when present and
            None when not specified. E.g.
            ``{"data_type": "ulong"}``

            The type dictionary has two optional keys when the type is a
            sequence or an array. When both are present it is a sequence of
            arrays. E.g.
            ``{"data_type": "ulong",
             "arraydimensions": ["64","2"],
             "sequencelength": "4"}``

            If "data_type" is "enum" then an additional enum key lists the
            enums:
            ``{"data_type": "enum",
             "enums": ["enum_val1","enum_val2"]}``

            If "data_type" is "struct" then an additional "members" key is used
            with a list value containing the name and type of each field in the
            struct. OpenCPI struct members cannot have type struct. E.g:
            ``{"data_type": "struct",
             "members": [{"name": "<member_name>,
                          "type": {"data_type": "ulong"}]}``
        """
        # Get type attribute. If not present default to ulong
        type_ = self._get_attribute(
            element=property_element, attribute="type",
            default="ulong", optional=True)
        type_dict = {"data_type": type_.lower().strip()}

        # Handle special property types
        if type_ == "struct":
            if not member_element:
                type_dict["members"] = self._get_struct_property_type(
                    property_element)
            else:
                raise ValueError(
                    "Member child elements cannot have type struct.")
        elif type_ == "enum":
            # "enum" attribte must be present when type is "enum".
            type_dict["enums"] = self._get_list_attribute(
                element=property_element, attribute="enums", optional=False)
        elif type_ == "string":
            # "stringlength" must be present when type is "string".
            type_dict["stringlength"] = self._get_attribute(
                element=property_element, attribute="stringlength",
                optional=False).strip()

        # Handle arrays dimensions / length
        # Only include "arraydimensions" key in dictionary if "arraydimensions"
        # or "arraylength" is an attribute in the property / member element.
        if "arraydimensions" in property_element.attrib.keys():
            type_dict["arraydimensions"] = self._get_list_attribute(
                element=property_element, attribute="arraydimensions",
                optional=False)
            # Check for double declaration of array size.
            if "arraylength" in property_element.attrib.keys():
                raise ValueError(
                    "ArrayLength attribute cannot coexist with " +
                    "ArrayDimensions attribute.")
        elif "arraylength" in property_element.attrib.keys():
            type_dict["arraydimensions"] = self._get_list_attribute(
                element=property_element, attribute="arraylength",
                optional=False)

        # If sequencelength and arraylength are both set then the result is a
        # sequence of arrays and not an array of sequences.
        if "sequencelength" in property_element.attrib.keys():
            type_dict["sequencelength"] = self._get_attribute(
                element=property_element, attribute="sequencelength",
                optional=False).strip()

        return type_dict

    def _get_struct_property_type(self, property_element):
        """ Get name and type attributes from a member XML element.

        Args:
            property_element (``xml.etree.ElementTree.Element``): Object
                containing the XML property or member element from which to
                extract the property/member arguments from.

        Returns:
            Dictionary with member name as the key and member type as the
            value. Within the dict all values are strings (or a list of stings)
            E.g.
            ``{"<member_name>": {
             "type": {"data_type": "ulonglong"}},
             "<member_name2>": {etc}}``

            The type dictionary has two optional keys when the type is a
            sequence or an array. When both are present it is a sequence of
            arrays. E.g.
            ``"type": {"data_type": "ulong",
                     "arraydimensions": ["64","2"],
                     "sequencelength": "4"}``

            If "data_type" is "enum" then an addition enum key lists the enums:
            ``"type": {"data_type": "enum",
                     "enums": ["enum_val1","enum_val2"]}``

            OpenCPI struct members cannot have type struct.
        """
        members = {}
        for member in property_element.iter("member"):
            if "name" not in property_element.attrib.keys():
                raise ValueError("Member value must have 'name' attribute.")
            name = member.attrib["name"]
            member_dict = {name: {}}

            member_dict[name]["type"] = self._get_property_type(
                property_element=member, member_element=True)

            members.update(member_dict)
        return members

    def _get_description(self, property_element):
        """ Gets the description of a property XML element.

        Supports the description supplied as either an argument of the
        <property> element, or the text of a <description> element as a child
        of the <property> element.

        Args:
            property_element (``xml.etree.ElementTree.Element``): Object
            containing the XML property or member element from which to extract
            the property/member arguments from.

        Returns:
            A string containing the property description or None if there is no
            description.
        """
        description = self._get_attribute(
            element=property_element, attribute="description",
            default=None, optional=True)
        # If there is no description attribute, check for description element
        if not description:
            description_element = list(property_element.iter("description"))
            # If there is a description element then process and store it
            if description_element:
                description = self._clean_description_text(
                    description_element[0].text)
        return description

    def _clean_description_text(self, description):
        """ Removes unwanted whitespace from a property description string.

        Removes leading whitespace to the extent that is common to all lines of
        the description.

        Args:
            description (``string``): Property description string directly
                from XML file.

        Returns:
            Property description string with all common leading whitespace
            characters removed from each line.
        """
        # Check for blank description or description only containing whitespace
        if not description:
            return None
        elif description.isspace():
            return None

        lines = description.split("\n")
        # Remove blank starting / ending lines
        if lines[0].isspace() or lines[0] == "":
            del lines[0]
        if lines[-1].isspace() or lines[-1] == "":
            del lines[-1]

        # Remove leading whitespace to the extent that is common to all lines
        # (Except whitespace only lines)
        min_whitespace = len(description)
        for line in lines:
            if not line.isspace() and not line == "":
                line_starts = len(line) - len(line.lstrip())
                if line_starts < min_whitespace:
                    min_whitespace = line_starts

        # Truncate each line and form a string
        stripped_description = ""
        for line in lines:
            if len(line) > min_whitespace:
                stripped_line = line[min_whitespace:]
                stripped_description += stripped_line.rstrip() + "\n"
            else:
                stripped_description += line.rstrip() + "\n"
        # Remove final '\n' char
        stripped_description = stripped_description[:-1]
        return stripped_description
