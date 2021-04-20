#!/usr/bin/env python3

# Property and parameter directive
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


import pathlib

import docutils
import docutils.parsers.rst

import xml_tools

from . import docutils_helpers


class PropertiesDirectiveHandler(docutils.parsers.rst.Directive):
    """ Parent class for directives that handle properties

    Gives standard way for properties to be formatted when being added to
    docutils tree.

    Class is expected to be inherited by class which is the directive.
    """

    def _parse_context_to_addition_text(self):
        """ Convert content to a dictionary

        Add the property text to ``self.additional_text`` as a dictionary.
        """
        self.additional_text = {}
        for line in self.content:
            if len(line) > 0:
                property_name = line[0:line.find(":")].strip()
                text = line[line.find(":")+1:].strip()

                # Add full stop at the end
                if text[-1] != ".":
                    text = f"{text}."

                self.additional_text[property_name] = text

    def _property_summary(self, name, detail):
        """ Generate a property summary

        Args:
            name (``str``): The property name.
            details (``dict``): Detail of the property in a dictionary.

        Returns:
            A ``docutils`` list item formatted with the properties details.
        """
        # Construct the list entry in ReStructuredText as the description and
        # additional text may be in ReStructuredText.
        property_rst = f"``{name}``: {detail['description']}".strip()
        if property_rst[-1] != ".":
            property_rst = f"{property_rst}."
        if name in self.additional_text:
            property_rst = f"{property_rst} {self.additional_text[name]}"
        if property_rst[-1] != ".":
            property_rst = f"{property_rst}."

        property_item = docutils.nodes.list_item()
        property_item_paragraph = docutils_helpers.rst_string_convert(
            self.state, property_rst)
        property_item.append(property_item_paragraph)

        # Add the expected values as a sublist
        property_detail_list = docutils.nodes.bullet_list()

        # Property / parameter type (e.g. char, short)
        data_type_item = docutils_helpers.list_item_name_code_value(
            "Variable type", detail["type"]["data_type"])
        data_type_detail_list = docutils.nodes.bullet_list()
        if "arraydimensions" in detail["type"]:
            array_details = docutils_helpers.list_item_name_code_value(
                "Array dimensions", detail["type"]["arraydimensions"])
            data_type_detail_list.append(array_details)
        if "sequencelength" in detail["type"]:
            sequence_details = docutils_helpers.list_item_name_code_value(
                "Sequence length", detail["type"]["sequencelength"])
            data_type_detail_list.append(sequence_details)
        if detail["type"]["data_type"] == "enum":
            enum_values = docutils_helpers.list_item_name_code_value(
                "Allowed values", str(detail["type"]["enums"]))
            data_type_detail_list.append(enum_values)
        if detail["type"]["data_type"] == "struct":
            struct_details = docutils_helpers.list_item_name_code_value(
                "Members", str(detail["type"]["memebers"]))
            data_type_detail_list.append(struct_details)
        if len(data_type_detail_list) > 0:
            data_type_item.append(data_type_detail_list)
        property_detail_list.append(data_type_item)

        # Access details
        access_item = docutils.nodes.list_item()
        access_item.append(docutils.nodes.paragraph(text="Access:"))
        access_details_list = docutils.nodes.bullet_list()
        if "readable" in detail["access"]:
            readable_details = docutils_helpers.list_item_name_code_value(
                "Readable", detail["access"]["readable"])
            access_details_list.append(readable_details)
        if "writable" in detail["access"]:
            writable_details = docutils_helpers.list_item_name_code_value(
                "Writable", detail["access"]["writable"])
            access_details_list.append(writable_details)
        if "initial" in detail["access"]:
            initial_details = docutils_helpers.list_item_name_code_value(
                "Initial", detail["access"]["initial"])
            access_details_list.append(initial_details)
        if "volatile" in detail["access"]:
            volatile_details = docutils_helpers.list_item_name_code_value(
                "Volatile", detail["access"]["volatile"])
            access_details_list.append(volatile_details)
        if "readsync" in detail["access"]:
            readsync_details = docutils_helpers.list_item_name_code_value(
                "Read synchronisation", detail["access"]["readsync"])
            access_details_list.append(readsync_details)
        if "writesync" in detail["access"]:
            writesync_details = docutils_helpers.list_item_name_code_value(
                "Write synchronisation", detail["access"]["writesync"])
            access_details_list.append(writesync_details)
        if "readback" in detail["access"]:
            readback_details = docutils_helpers.list_item_name_code_value(
                "Read back", detail["access"]["readback"])
            access_details_list.append(readback_details)
        if len(access_details_list) > 0:
            access_item.append(access_details_list)
            property_detail_list.append(access_item)

        # Default value
        default_item = docutils_helpers.list_item_name_code_value(
            "Default value", str(detail["default"]))
        property_detail_list.append(default_item)

        property_item.append(property_detail_list)

        return property_item


class OcpiDocumentationProperties(PropertiesDirectiveHandler):
    """ ocpi_documentation_properties directive
    """
    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True
    # component_spec allows optional manual setting of the path the component
    # specification is at. parameters is a flag which indicates parameters
    # rather than properties are to be documented.
    option_spec = {"component_spec": str,
                   "parameters": docutils.parsers.rst.directives.flag}

    def run(self):
        """ Action when ocpi_documentation_properties directive called

        Generates list of the properties or parameters for the component. If a
        properties or parameter list is generates is controlled based on the
        ``parameters`` option.

        Returns:
            List with the docutils tree map to replace the directive in the
                source text with.
        """
        # Variable to add the resulting output to
        content = []

        # If component specification path is set as option use this, otherwise
        # automatically determine likely path based on standard file structure
        if "component_spec" in self.options:
            component_specification_path = pathlib.Path(
                self.state.document.attributes["source"]).joinpath(
                self.options["component_spec"]).resolve()
        else:
            component_name = pathlib.Path(
                self.state.document.attributes["source"]).resolve(
            ).parent.name.replace(".comp", "")

            component_specification_path = pathlib.Path(
                self.state.document.attributes["source"]).resolve(
            ).parent.parent.joinpath("specs").joinpath(
                f"{component_name}-spec.xml")

            # Added to handle _spec.xml naming
            if not component_specification_path.is_file():
                component_specification_path = pathlib.Path(
                    self.state.document.attributes["source"]).resolve(
                ).parent.parent.joinpath("specs").joinpath(
                    f"{component_name}_spec.xml")

        if not component_specification_path.is_file():
            self.state_machine.reporter.warning(
                "Properties / parameters listing cannot find component "
                + f"specification, {component_specification_path}",
                line=self.lineno)
            return content

        with xml_tools.parser.ComponentSpecParser(
                component_specification_path) as file_parser:
            component_specification = file_parser.get_dictionary()

        # Determine if summarising parameters, otherwise will summarise
        # properties
        parameter_report = "parameters" in self.options

        self._parse_context_to_addition_text()
        for property_name in self.additional_text:
            # Check a valid name
            if property_name not in component_specification["properties"]:
                self.state_machine.reporter.warning(
                    f"No property called {property_name} defined in component "
                    + f"specification, {component_specification_path}",
                    line=self.lineno)
                continue

            # If additional text is added then give warning if not correct
            # property or parameter as the additional text will not be
            # shown.
            if component_specification["properties"][property_name]["access"][
                    "parameter"] != parameter_report:
                if parameter_report:
                    self.state_machine.reporter.warning(
                        f"{property_name} is a property while this directive "
                        + "is set to only report parameters",
                        line=self.lineno)
                else:
                    self.state_machine.reporter.warning(
                        f"{property_name} is a parameter while this directive "
                        + "is set to only report properties",
                        line=self.lineno)

        bullet_point_list = docutils.nodes.bullet_list()
        for name, detail in component_specification["properties"].items():
            # Skip entries that are parameters when only listing properties,
            # and vice-versa.
            if not (detail["access"]["parameter"] == parameter_report):
                continue

            bullet_point_list.append(self._property_summary(name, detail))

        if len(bullet_point_list) > 0:
            return [bullet_point_list]
        else:
            return [docutils.nodes.paragraph(text="None.")]
