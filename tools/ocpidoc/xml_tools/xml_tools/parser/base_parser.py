#!/usr/bin/env python3

# Class for all XML parser types to inherit from.
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

import re
import xml.etree.ElementTree as ET
import os.path
import textwrap


class BaseParser():
    """ Class for all XML parsers to inherit from.
    """

    def __init__(
            self, filename, include_filepaths=["."], force_lowercase=True):
        """ Initialize base parser class.

        Args:
            filename (``string``): File path and name of the XML file to parse.
            include_filepaths (``list``): List of strings containing the
                filepaths to search for a file specified in an XML include
                statement.
            force_lowercase (``bool``): When true all XML tags and attribute
                names are converted to lowercase to allow for case insensitive
                XML parsing. When false the case of XML tags and attributes is
                preserved.

        Returns:
            An initialized BaseParser instance.
        """
        # Store path / filename of XML file and store a list of all the
        # directories to search if the specified XML specifies another XML file
        # via an XML include element.
        self._filename = filename
        self._include_filepaths = include_filepaths
        # Stores if XML element and attribute case should be preserved.
        self._force_lowercase = force_lowercase
        # Read the specified XML file. Resolve xi:include elements.
        # When specified, force tags and attribute names to lower case.
        # Use ElementTree to parse XML and store the root element.
        self._load_xml_file(force_lowercase)

    def __enter__(self):
        """ Allows usage as a context manager.

        Returns:
            Self as context manager.
        """
        return self

    def __exit__(self, *_):
        """ Exit context manager.

        Sets internal variables that are normally used to access data to None.

        Args:
            _ (optional): Input arguments are allowed to support the context
                manager standard format, and support shutdown signals, however
                not used here so just interface formatting.
        """
        pass

    def getroot(self):
        """ Gets the root element in the parsed XML file.

        Returns:
            Root element of the parsed XML file.
        """
        return self._xml_root

    def _load_xml_file(self, force_lowercase):
        """ Load XML file.

        Opens an XML file and reads contents as a string. Resolves any XML
        include statements. Optionally forces XML tags and attribute names to
        lower case. Stores processed string in self._xml_string. Parses the XML
        string using the xml.etree.ElementTree library and stores an object
        containing the root XML element as self._xml_root.

        Args:
            force_lowercase (``bool``): When true all XML tags and attribute
                names are converted to lowercase to allow for case insensitive
                XML parsing. When false the case of XML tags and attributes is
                preserved.
        """
        # Read XML file into a string
        with open(self._filename, "r") as open_file:
            file_xml_string = open_file.read()

        # Locate any <xi:include href="<file>"/> statements. Search for the
        # specified file within self._include_filepaths, and if found insert
        # the file's contents into the file_xml_string string.
        file_xml_string = self._process_xml_includes(file_xml_string)

        # Parse string containing original XML file and generate new string
        # with only lowercase element and attribute tags.
        # This is because tag capitalization can vary across files.
        if force_lowercase:
            file_xml_string = self._get_lower_case_xml(file_xml_string)

        # Parse the XML file from the new string
        self._xml_string = file_xml_string
        self._xml_root = ET.fromstring(self._xml_string)

    def _get_root_tag(self):
        """ Gets the tag of the root element in the parsed XML file.

        Returns:
            String containing the tag of the root XML element.
        """
        return self._xml_root.tag

    def _get_elements_tag_list(self, xml_element):
        """ Gets a list containing all unique tags within an XML element.

        Tags within child elements are also included.

        Args:
            xml_element (``xml.etree.ElementTree.Element``): Object containing
                the top level XML element in which to list tags within.

        Returns:
            List containing the name of each unique tag as a string.
        """
        element_tag_list = []
        # Step through all elements in the XML (including child elements)
        for element in xml_element.iter():
            # Get every element name
            element_tag_list.append(element.tag)
        # Remove duplicates
        element_tag_list = list(dict.fromkeys(element_tag_list))
        return element_tag_list

    def _get_attribute_tag_list(self, xml_element):
        """ Gets a list containing all unique attribute names.

        Searches within the provided XML element and all child elements.

        Args:
            xml_element (``xml.etree.ElementTree.Element``): Object containing
                the top level XML element in which to list attributes within.

        Returns:
            List containing the name of each unique attribute as a string.
        """
        attribute_tag_list = []
        # Step through all elements in XML (including child elements)
        for element in xml_element.iter():
            # Get every attribute name
            attribute_tag_list += list(element.attrib.keys())
        # Remove duplicates
        attribute_tag_list = list(dict.fromkeys(attribute_tag_list))
        return attribute_tag_list

    def _remove_lower_case(self, string_list):
        """ Removes lower case strings from a list.

        Args:
            string_list (``list``): List containing strings.

        Returns:
            List containing only strings where at least one upper case
            character is present.
        """
        return [value for value in string_list if not value.islower()]

    def _get_lower_case_xml(self, xml_string):
        """ Forces all tags and attribute names to be lower case.

        Upper case letters are preserved in attribute values and text
        sections of the XML file.

        Args:
            xml_string (``string``): String containing data in XML format.

        Returns:
            String containing data in XML format where all tags and attribute
            names are lower case.
        """
        xml_root = ET.fromstring(xml_string)
        # Extract any element tags that are not all lower case.
        element_tag_list = self._remove_lower_case(
            self._get_elements_tag_list(xml_root))
        # Replace all element tags with lower case versions using regex.
        for element in element_tag_list:
            # Replace '<element>'
            xml_string = re.sub("<" + element + " *>",
                                "<" + element.lower() + ">",
                                xml_string)
            # Replace </element>'
            xml_string = re.sub("</" + element + " *>",
                                "</" + element.lower() + ">",
                                xml_string)
            # Replace '<element '
            xml_string = re.sub("<" + element + " ",
                                "<" + element.lower() + " ",
                                xml_string)
        # Extract any attribute tags that are not all lower case.
        attribute_tag_list = self._remove_lower_case(
            self._get_attribute_tag_list(xml_root))
        # Replace all attribute tags with lower case versions using regex.
        for attribute in attribute_tag_list:
            # Replace 'attribute = "'
            xml_string = re.sub(" " + attribute + " *= *\"",
                                " " + attribute.lower() + "=\"",
                                xml_string)
            # Replace 'attribute = ''
            xml_string = re.sub(" " + attribute + " *= *'",
                                " " + attribute.lower() + "='",
                                xml_string)

        return xml_string

    def _is_true(self, element, attribute, default=False, optional=True):
        """ Determines if an attribute within an XML element is true.

        Values accepted as True are "true" [any case] or "1". All other values
        return False.

        Args:
            element (``xml.etree.ElementTree.Element``): Object containing the
                XML element.
            attribute (``string``): The name of the boolean attribute.
            default (``bool``): The value to return if the attribute is not
                present in the element.
            optional (``bool``): Determines behaviour when an attribute is not
                present. When True the method will return the default value.
                When False a ValueError exception is raised.

        Returns:
            True when attribute value is True, False when attribute value is
            False.
        """
        if attribute in element.attrib.keys():
            return (element.attrib[attribute].lower() in ["true", "1"])
        else:
            if optional:
                return default
            else:
                tag = element.tag
                raise ValueError(
                    f"Attribute {attribute} must be present in {tag} element.")

    def _get_boolean_attributes(self, element, attribute_list,
                                default=None, optional=True):
        """ Creates a dictionary of boolean attributes and their values.

        Args:
            element (``xml.etree.ElementTree.Element``): Object containing the
                XML element.
            attribute_list (``list``): A list of strings containing the names
                of the boolean attributes to get.
            default: The value to return if an attribute is not
                present in the element.
            optional (``bool``): Determines behaviour when an attribute is not
                present. When True the method will return the default value.
                When False a ValueError exception is raised.

        Returns:
            Python dictionary containing with name of each attribute as the key
            and the value as a bool. E.g. {"enable": True, "error": False}
        """
        attributes = {}
        for attribute in attribute_list:
            attributes[attribute] = self._is_true(
                element, attribute, default, optional)
        return attributes

    def _get_attribute(self, element, attribute, default=None, optional=True):
        """ Gets the value of an attribute from an XML element.

        Args:
            element (``xml.etree.ElementTree.Element``): Object containing the
                XML element.
            attribute (``string``): The name of the attribute to fetch.
            default (``string``): The value to return if the attribute is not
                present in the element.
            optional (``bool``): Determines behaviour when an attribute is not
                present. When True the method will return the default value.
                When False a ValueError exception is raised.

        Returns:
            String containing the value of the attribute.
        """
        if attribute in element.attrib.keys():
            return element.attrib[attribute]
        else:
            if optional:
                return default
            else:
                tag = element.tag
                raise ValueError(
                    f"Attribute {attribute} must be present in {tag} element.")

    def _get_list_attribute(self, element, attribute,
                            default=None, optional=True):
        """ Gets a list of values of an attribute from an XML element.

        Separates by comma, and removes whitespace. Not suitable for
        lists of string values when a string has a "," or whitespace characters
        as part of the string.

        Args:
            element (``xml.etree.ElementTree.Element``): Object containing the
                XML element.
            attribute (``string``): The name of the attribute to fetch.
            default (``string``): The value to return if the attribute is not
                present in the element.
            optional (``bool``): Determines behaviour when an attribute is not
                present. When True the method will return the default value.
                When False a ValueError exception is raised.

        Returns:
            List of strings containing the values of the attribute.
        """
        if attribute in element.attrib.keys():
            values = element.attrib[attribute]
            return [value.strip() for value in values.split(",")]
        else:
            if optional:
                return default
            else:
                tag = element.tag
                raise ValueError(
                    f"Attribute {attribute} must be present in {tag} element.")

    def _process_xml_includes(self, xml_string):
        """ Resolves xi:include elements with specified file

        The file name specified by the xi:include element is parsed and each
        path specified in self._include_filepaths is checked to see if the file
        exists. The first file with a matching file name is used. File paths
        are searched in the order that they are specified in the
        self._include_filepaths list.

        The xi:include element is directly replaced with the contents of the
        specified file. Included XML files are recursively checked for
        additional xi:included elements.

        If the specified file is not found the xi:include element is removed
        and a warning is displayed.

        NB. the xi:include element used within OpenCPI files does not fully
        follow the XML format, and must handled before parsing the XML file
        with a regular XML parser.

        Args:
            xml_string (``string``): String containing data in XML format.

        Returns:
            String containing data in XML format where all xi:include elements
            have been either resolved or removed.
        """
        # Loop through all xi:include elements in the XML string
        for include in self._get_xml_includes(xml_string):
            # Extract the filename specified by the XML include statement
            filename = self._get_xml_include_filename(include)
            if filename is None:
                # Failed to extract a filename from the xi:include.
                raise ValueError(
                    f"Failed to extract filename from \"{include}\"")
            xml_include_string = ""
            file_not_found = False
            # Step through all search directories until the file is found
            for file_path in self._include_filepaths:
                full_path = os.path.join(file_path, filename)
                # Open the file and store the contents
                if os.path.isfile(full_path):
                    with open(full_path, "r") as xml_include_file:
                        xml_include_string = xml_include_file.read()
                    break
            else:
                file_not_found = True
            # If the included file has an XML version tag, remove it.
            version_pattern = r"<\? *xml *version *= *[\"']1.0[\"'].*\?>"
            xml_include_string = re.sub(
                version_pattern, "", xml_include_string)
            # Use a regex to repace the full xi:include element with the
            # contents of the specified file (minus the XML version tag).
            indent = include.split("<xi")[0]
            xml_include_string = textwrap.indent(xml_include_string, indent)
            xml_string = re.sub(include, xml_include_string, xml_string)
            # If no file could be found in the search path, then just remove
            # the XML include statement and show a warning.
            if file_not_found:
                print(f"Warning: The file {filename} specified for inclusion "
                      + f"in {self._filename} could not be found "
                      + "and was ignored.")
            # Recursively replace any XML include statements that were in the
            # newly included files.
            if self._get_xml_includes(xml_string):
                xml_string = self._process_xml_includes(xml_string)

        return xml_string

    def _get_xml_includes(self, xml_string):
        """ Gets a list of all xi:include elements found within a string.

        Args:
            xml_string (``string``): String containing data in XML format.

        Returns:
            List containing a string for all xi:include elements found within
            the input XML data, including indentation.
        """
        # NB. includes arguments other than just href.
        include_files = re.findall(
            r".*<xi:include +href *= *[\"'][^>]*[\"'] */>", xml_string)
        return include_files

    def _get_xml_include_filename(self, xi_include_string):
        """ Extracts the value of the href attribute in an xi:include string.

        Args:
            xi_include_string (``string``): String containing an single
                xi:include element.

        Returns:
            String containing the file name specified in the xi:include
            element.
        """
        # Use a regex group to extract just the filename
        result = re.findall(
            r"<xi:include +href *= *[\"']([^>]*)[\"'] */>$",
            xi_include_string)
        if result:
            # Remove other arguments if they exist
            include_file = result[0].replace("'", "\"").split("\"")[0]
            if not include_file.endswith(".xml"):
                include_file += ".xml"
            return include_file
        else:
            return None
