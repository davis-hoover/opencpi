#!/usr/bin/env python3

# Port summary directive
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


class OcpiDocumentationPorts(docutils.parsers.rst.Directive):
    """ ocpi_documentation_ports directive
    """
    has_content = True
    required_arguments = 0
    optional_arguments = 0
    # Allow overriding of the automatically determined component specification
    # file path.
    option_spec = {"component_spec": str}

    def run(self):
        """ Action when ocpi_documentation_ports directive called

        Generates list of input and output ports the component has.

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
                "Port listing cannot find component specification, "
                + f"{component_specification_path}",
                line=self.lineno)
            return content

        with xml_tools.parser.ComponentSpecParser(
                component_specification_path) as file_parser:
            component_specification = file_parser.get_dictionary()

        # Get any additional text for any ports
        additional_text = {}
        for line in self.content:
            if len(line) > 0:
                port_name = line[0:line.find(":")].strip()
                text = line[line.find(":")+1:].strip()

                # Check a valid name
                if (port_name not in component_specification["inputs"]) and (
                        port_name not in component_specification["outputs"]):
                    self.state_machine.reporter.warning(
                        f"No port called {port_name} defined in component "
                        + f"specification, {component_specification_path}",
                        line=self.lineno)
                    continue

                # Add full stop at end
                if text[-1] != ".":
                    text = f"{text}."

                additional_text[port_name] = text

        input_list = self._get_port_list(component_specification["inputs"],
                                         additional_text)
        content.append(docutils.nodes.paragraph(text="Inputs:"))
        if len(input_list) > 0:
            content.append(input_list)
        else:
            content.append(docutils.nodes.paragraph(text="None."))

        output_list = self._get_port_list(component_specification["outputs"],
                                          additional_text)
        content.append(docutils.nodes.paragraph(text="Outputs:"))
        if len(output_list) > 0:
            content.append(output_list)
        else:
            content.append(docutils.nodes.paragraph(text="None."))

        return content

    def _get_port_list(self, ports, additional_text={}):
        """ Create a bullet point list to describe a set of ports

        Args:
            ports (dict): A set of ports the list is to be generated for. Keys
                should be the port names.
            additional_text (dict, optional): Any additional (rst formatted)
                text for the ports. Keys should be port names.

        Returns:
            docutils.nodes.bullet_list instance which outlines all the ports
                from the input lists.
        """
        port_list = docutils.nodes.bullet_list()
        for name, port_detail in ports.items():
            list_item = docutils.nodes.list_item()

            # Construct the list entry in ReStructuredText as the additional
            # text may be in ReStructuredText
            list_item_rst = f"``{name}``"
            if name in additional_text:
                list_item_rst = (
                    f"{list_item_rst}: {additional_text[name]}")
            list_item.append(docutils_helpers.rst_string_convert(
                self.state, list_item_rst))

            detail_sub_list = docutils.nodes.bullet_list()

            protocol_item = docutils_helpers.list_item_name_code_value(
                "Protocol", port_detail["protocol"])
            detail_sub_list.append(protocol_item)

            optional_item = docutils_helpers.list_item_name_code_value(
                "Optional", port_detail["optional"])
            detail_sub_list.append(optional_item)

            list_item.append(detail_sub_list)
            port_list.append(list_item)

        return port_list
