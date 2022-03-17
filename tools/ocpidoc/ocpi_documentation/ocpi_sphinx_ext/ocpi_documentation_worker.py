#!/usr/bin/env python3

# Worker directive
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
import pathlib
import glob
import itertools
import docutils

import xml_tools

from . import docutils_helpers
from .ocpi_documentation_properties import PropertiesDirectiveHandler


class OcpiDocumentationWorker(PropertiesDirectiveHandler):
    """ ocpi_documentation_worker directive
    """
    has_content = True
    required_arguments = 0
    optional_arguments = 0
    # Allow overriding of the automatically determined file paths.
    option_spec = {"worker_description": str,
                   "build_file": str}

    def run(self):
        """ Action when ocpi_documentation_worker directive called

        Generates page with worker property specific section, and work
        build configuration section, when required.

        Returns:
            List with the docutils tree map to replace the directive in the
                source text with.
        """
        # Variable to add the resulting output to
        content = []

        rst_path = pathlib.Path(self.state.document.attributes["source"])
        worker_dir = rst_path.parent
        if worker_dir.name == "gen":
            worker_dir = worker_dir.parent
        with xml_tools.parser.WorkerSpecParser(None, include_filepaths=[str(worker_dir)]) as file_parser:
            worker_description = file_parser.get_combined_dictionary()

        self._parse_context_to_addition_text()

        for name in self.additional_text:
            if name not in itertools.chain(
                    worker_description.get("properties"),
                    worker_description.get("inputs"),
                    worker_description.get("outputs"),
                    worker_description.get("time"),
                    worker_description.get("signals"),
                    worker_description.get("interfaces"),
                    worker_description.get("other_interfaces")):
                self.state_machine.reporter.warning(
                    f"No property or port called {name} defined in worker "
                    + f"description, {worker_description.get('path')}",
                    line=self.lineno)
                continue

        # Add property detail from the worker description
        property_list = docutils.nodes.bullet_list()
        for name, detail in worker_description["properties"].items():
            if detail["worker_property"] is True:
                list_item = self._property_summary(name, detail)
                property_list.append(list_item)

        if len(property_list) > 0:
            property_section = docutils.nodes.section(
                ids=["worker-properties"], names=["worker properties"])
            property_section.append(
                docutils.nodes.title(text="Worker Properties"))
            property_section.append(property_list)
            content.append(property_section)

        # Add port detail from the worker description
        port_list = docutils.nodes.bullet_list()

        # Port options
        port_options = [("inputs", "Inputs:"),
                        ("outputs", "Outputs:"),
                        ("time", "Time:"),
                        ("signals", "Signals:"),
                        ("interfaces", "Interfaces:"),
                        ("other_interfaces", "Other interfaces:")]

        for port_type, port_type_header in port_options:
            if worker_description.get(port_type):
                port_name = list(worker_description[port_type].keys())[0]
                port_type_rst = port_type_header
                port_type_doc = docutils_helpers.rst_string_convert(
                    self.state, f"**{port_type_rst}**")
                port_list.append(port_type_doc)
                for name, detail in worker_description[port_type].items():
                    list_item = self._port_summary(name, detail)
                    port_list.append(list_item)

        # Get subdevice connections from OWD, if available
        subdevice_list = docutils.nodes.bullet_list()
        for worker,connections in worker_description["supports"].items():
            supported_item = docutils_helpers.list_item_name_code_value(
                "Supported device worker", worker)
            supported_item.append(docutils.nodes.line())
            supported_item.append(
                docutils.nodes.paragraph(text="Connections:"))
            supported_item.append(docutils.nodes.line())
            connection_list = docutils.nodes.bullet_list()
            for port,connect in connections:
                connection_list = docutils.nodes.bullet_list()
                connection_list.append(
                    docutils_helpers.list_item_name_code_value(
                        "Subdevice port", port))
                worker_port_item = \
                    docutils_helpers.list_item_name_code_value(
                        "Supported worker port", connect[0])
                supported_port_list = docutils.nodes.bullet_list()
                port_index = connect[1]
                supported_port_list.append(
                    docutils_helpers.list_item_name_code_value(
                        "Index", port_index))
                worker_port_item.append(supported_port_list)
                connection_list.append(worker_port_item)
                supported_item.append(connection_list)
                supported_item.append(docutils.nodes.line())
            subdevice_list.append(supported_item)

        if len(subdevice_list) > 0:
            subdevice_connections_doc = docutils_helpers.rst_string_convert(
                self.state, "**Subdevice Connections:**")
            subdevice_connections_doc.append(subdevice_list)
            port_list.append(subdevice_connections_doc)

        if len(port_list) > 0:
            port_section = docutils.nodes.section(
                ids=["worker-ports"], names=["worker ports"])
            port_section.append(
                docutils.nodes.title(text="Worker Ports"))
            port_section.append(port_list)
            content.append(port_section)

        # If build file path not set determine, otherwise use set value
        if "build_file" in self.options:
            build_file_path = pathlib.Path(
                self.state.document.attributes["source"]).joinpath(
                self.options["build_file"]).resolve()
            # Not having a build file is valid, however give a warning in the
            # case that the build file is set as a option as would likely only
            # be done when there is a build file to be included.
            if not build_file_path.is_file():
                self.state_machine.reporter.warning(
                    f"{build_file_path} is not a valid file path. Build file "
                    + "cannot be read.",
                    line=self.lineno)
        else:
            worker_name = pathlib.Path(
                self.state.document.attributes["source"]).resolve().parent.stem
            build_file_path = pathlib.Path(
                self.state.document.attributes["source"]).resolve(
            ).parent.joinpath(f"{worker_name}.build")

        if build_file_path.is_file():
            with xml_tools.parser.BuildParser(build_file_path) as file_parser:
                build_configurations = file_parser.get_all_configurations()

            if len(build_configurations) > 0:
                build_configuration_section = docutils.nodes.section(
                    ids=["build-configurations"],
                    names=["build configurations"])
                build_configuration_section.append(
                    docutils.nodes.title(text="Build Configurations"))
                parameter_build_list = docutils.nodes.bullet_list()
                for configuration in build_configurations:
                    build_list_item = docutils.nodes.list_item()
                    build_list_item.append(
                        self._format_configuration_item(configuration))
                    parameter_build_list.append(build_list_item)
                build_configuration_section.append(parameter_build_list)
                content.append(build_configuration_section)

        return content

    def _format_configuration_item(self, configuration):
        """ Format build configuration for including in documentation

        Args:
            configuration (``dict``): Build configuration dictionary to be
                formatted.

        Returns:
            Docutils paragraph to include in documentation output.
        """
        parameters = list(configuration.keys())
        parameters.sort()
        rst_text = (f"``{parameters[0].lower()}``: "
                    + f"``{configuration[parameters[0]]}``")
        for parameter in parameters[1:]:
            rst_text = (f"{rst_text}, ``{parameter.lower()}``: " +
                        f"``{configuration[parameter]}``")

        return docutils_helpers.rst_string_convert(self.state, rst_text)

    def _port_summary(self, name, detail):
        """ Generate a port summary

        Args:
            name (``str``): The port name.
            details (``dict``): Detail of the port in a dictionary.

        Returns:
            A ``docutils`` list item formatted with the port details.
        """
        # Add description of port, if available
        if "description" not in detail.keys():
            port_rst = f"``{name}``"
        else:
            port_rst = f"``{name}``: {detail['description']}".strip()
            if port_rst[-1] != ".":
                port_rst = f"{port_rst}."

        if name in self.additional_text:
            if "description" not in detail.keys():
                port_rst = f"{port_rst}: {self.additional_text[name]}"
            else:
                port_rst = f"{port_rst} {self.additional_text[name]}"
            if port_rst[-1] != ".":
                port_rst = f"{port_rst}."

        port_item = docutils.nodes.list_item()
        port_item_paragraph = docutils_helpers.rst_string_convert(
            self.state, port_rst)
        port_item.append(port_item_paragraph)

        # Add the expected values as a sublist
        port_detail_list = docutils.nodes.bullet_list()

        # Port attributes to display if available
        port_attributes = [("type", "Type"),
                           ("datawidth", "Data width"),
                           ("numberofopcodes", "Number of opcodes"),
                           ("secondswidth", "Seconds width"),
                           ("fractionwidth", "Fraction width"),
                           ("protocol", "Protocol"),
                           ("zerolengthmessages", "Zero length messages"),
                           ("master", "Master"),
                           ("count", "Count"),
                           ("optional", "Optional"),
                           ("signals", "Signals"),
                           ("input", "Input"),
                           ("output", "Output")]

        for attribute, text in port_attributes:
            if attribute in detail:
                # Include "devsignal" information contained in another xml
                if attribute == "signals":
                    signal_filename = detail["signals"]
                    if not signal_filename.endswith(".xml"):
                        signal_filename += ".xml"
                    current_directory = pathlib.Path(
                        self.state.document.attributes["source"]).resolve(
                    ).parent
                    specs_directory = current_directory.joinpath("../specs")
                    for directory in [current_directory, specs_directory]:
                        signal_file_path = directory.joinpath(signal_filename)
                        if signal_file_path.is_file():
                            break

                    signal_list = []
                    with xml_tools.parser.BaseParser(
                        signal_file_path,
                        include_filepaths=[current_directory, specs_directory]
                    ) as file_parser:
                        signals_xml_root = file_parser.getroot()
                        for signal_name in signals_xml_root.findall("signal"):
                            signal_list += [signal_name.get("name")]

                    signals_item = docutils.nodes.list_item()
                    signals_item.append(docutils.nodes.paragraph(
                        text="Signals:"))
                    signals_details_list = docutils.nodes.bullet_list()

                    for signal in signal_list:
                        item = docutils.nodes.list_item()
                        signal_rst = f"``{signal}``"
                        if signal in self.additional_text:
                            signal_rst += \
                                f": {self.additional_text[signal]}"
                            if signal_rst[-1] != ".":
                                signal_rst = f"{signal_rst}."
                        self.state.nested_parse(
                            docutils.statemachine.StringList(
                                signal_rst.split("\n")
                            ), 0, item)
                        signals_details_list.append(item)

                    signals_item.append(signals_details_list)
                    port_detail_list.append(signals_item)

                else:
                    attribute_detail = \
                        docutils_helpers.list_item_name_code_value(
                            text, detail[attribute])
                    port_detail_list.append(attribute_detail)

        if len(port_detail_list) > 0:
            port_item.append(port_detail_list)

        return port_item
