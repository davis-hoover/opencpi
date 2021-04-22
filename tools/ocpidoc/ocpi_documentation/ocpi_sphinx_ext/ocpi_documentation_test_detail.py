#!/usr/bin/env python3

# Test detail directive
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


import json
import pathlib

import docutils
import docutils.parsers.rst

from . import docutils_helpers


class OcpiDocumentationTestDetail(docutils.parsers.rst.Directive):
    """ ocpi_documentation_test_detail directive
    """
    has_context = False
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True
    # Allow overriding of the automatically determined testing summary log path
    option_spec = {"test_log": str}

    def run(self):
        """ Action when ocpi_documentation_test_detail directive called

        Generates a page with detail of all the test cases for a component.

        Returns:
            List with the docutils tree map to replace the directive in the
                source text with.
        """
        # Variable to add the resulting output to
        content = []

        # If lint log set as option use that value otherwise set automatic path
        if "test_log" in self.options:
            test_log_path = pathlib.Path(
                self.state.document.attributes["source"]).parent.joinpath(
                self.options["test_log"])
            # Give warning in this case as user has set log path manually, but
            # file does not exist. While file not existing is a valid event
            # when the user has manually set this likely they know the path
            # exists.
            if not test_log_path.is_file():
                self.state_machine.reporter.warning(
                    f"{test_log_path} is not a valid file path",
                    line=self.lineno)
        else:
            test_log_path = pathlib.Path(
                self.state.document.attributes["source"]).parent.joinpath(
                "test_log.json")

        if not test_log_path.is_file():
            return content

        with open(test_log_path, "r") as test_log_file:
            log = json.load(test_log_file)

        component_name = pathlib.Path(
            self.state.document.attributes["source"]).stem[0:-5]
        component_name = component_name.replace("_", "-")

        cases = list(log.keys())
        cases.sort()
        for case in cases:
            subcases = list(log[case].keys())
            subcases.sort()
            case_section = docutils.nodes.section(
                "", ids=[f"test-{case}"])
            case_section.append(docutils.nodes.title("", f"Test {case}"))

            # If not using rst_string_convert, likely link needs to be
            # registered with state, however rst_string_convert does this
            # already
            case_section.append(docutils_helpers.rst_string_convert(
                self.state, f".. _{component_name}-test{case}:\n"))

            for subcase in subcases:
                subcase_section = docutils.nodes.section(
                    "", ids=[f"test-{case}-{subcase}"])
                subcase_section.append(docutils.nodes.title(
                    "", f"Test {case}.{subcase}"))

                if "generator" in log[case][subcase]:
                    generator = docutils.nodes.paragraph(
                        "", "Input data generator: ")
                    generator.append(docutils.nodes.literal(text=log[case][
                        subcase]["generator"]["test"]))
                    generator.append(docutils.nodes.inline(text="."))
                    subcase_section.append(generator)
                else:
                    subcase_section.append(docutils.nodes.paragraph(
                        "", "No input generator."))

                if "comparison_method" in log[case][subcase]:
                    comparison_method = docutils.nodes.paragraph(
                        "",
                        "Comparison method used for verification is: ")
                    comparison_method.append(
                        docutils.nodes.literal(text=log[case][subcase][
                            "comparison_method"]["method"]))
                    if len(log[case][subcase]["comparison_method"][
                            "variables"]) > 0:
                        comparison_method.append(
                            docutils.nodes.inline(text=", with set variables:")
                        )
                        subcase_section.append(comparison_method)
                        variables_list = docutils.nodes.bullet_list()
                        for variable, value in log[case][subcase][
                                "comparison_method"]["variables"].items():
                            item = docutils.nodes.list_item()
                            item.append(docutils.nodes.literal(text=variable))
                            item.append(docutils.nodes.inline(text=": "))
                            item.append(
                                docutils.nodes.literal(text=f"{value}"))
                            variables_list.append(item)
                        subcase_section.append(variables_list)
                    else:
                        comparison_method.append(
                            docutils.nodes.inline(text="."))
                        subcase_section.append(comparison_method)

                else:
                    subcase_section.append(docutils.nodes.paragraph(
                        "",
                        "Comparison method unknown until tests have been run"))

                case_section.append(subcase_section)
            content.append(case_section)

        return content
