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


import pathlib

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

        Generates page with worker parameter and property specific section, and
        worker build configuration section, when required.

        Returns:
            List with the docutils tree map to replace the directive in the
                source text with.
        """
        # Variable to add the resulting output to
        content = []

        # If worker description is not set, determine it
        if "worker_description" in self.options:
            worker_description_path = pathlib.Path(
                self.state.document.attributes["source"]).joinpath(
                self.options["worker_description"]).resolve()
        else:
            worker_name = pathlib.Path(
                self.state.document.attributes["source"]).resolve().parent.stem
            worker_description_path = pathlib.Path(
                self.state.document.attributes["source"]).resolve(
            ).parent.joinpath(f"{worker_name}.xml")

        if worker_description_path.is_file():
            with xml_tools.parser.WorkerSpecParser(
                    worker_description_path) as file_parser:
                worker_description = file_parser.get_dictionary()

        else:
            self.state_machine.reporter.warning(
                f"{worker_description_path} is not a valid file path. Worker "
                + "description cannot be read. Use directive option "
                + "'worker_description' to set non-default path.",
                line=self.lineno)
            worker_description = None

        self._parse_context_to_addition_text()
        for property_name in self.additional_text:
            if property_name not in worker_description["properties"]:
                self.state_machine.reporter.warning(
                    f"No property called {property_name} defined in worker "
                    + f"description, {worker_description_path}",
                    line=self.lineno)
                continue

        # Add any other detail from the worker description
        property_list = docutils.nodes.bullet_list()
        parameter_list = docutils.nodes.bullet_list()
        for name, detail in worker_description["properties"].items():
            list_item = self._property_summary(name, detail)
            if detail["access"]["parameter"]:
                parameter_list.append(list_item)
            else:
                property_list.append(list_item)

        if len(property_list) > 0:
            property_section = docutils.nodes.section(
                ids=["worker-properties"], names=["worker properties"])
            property_section.append(
                docutils.nodes.title(text="Worker properties"))
            property_section.append(property_list)
            content.append(property_section)

        if len(parameter_list) > 0:
            parameter_section = docutils.nodes.section(
                ids=["worker-parameters"], names=["worker parameters"])
            parameter_section.append(
                docutils.nodes.title(text="Worker parameters"))
            parameter_section.append(parameter_list)
            content.append(parameter_section)

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
                    docutils.nodes.title(text="Build configurations"))
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
