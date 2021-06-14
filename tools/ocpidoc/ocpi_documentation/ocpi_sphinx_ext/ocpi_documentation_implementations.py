#!/usr/bin/env python3

# Property and parameter summary directive
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
import sphinx

from . import docutils_helpers


class OcpiDocumentationImplementations(docutils.parsers.rst.Directive):
    """ ocpi_documentation_implementations directive
    """
    has_content = False
    required_arguments = 1
    optional_arguments = 10
    final_argument_whitespace = False

    def run(self):
        """ Action when ocpi_documentation_implementations directive called

        This directive draws in the documentation for the worker page directly.

        Returns:
            List with the docutils tree map to replace the directive in the
                source text with.
        """
        # Variable to add the resulting output to
        content = []

        implementations = []
        for argument in self.arguments:
            worker_directory = pathlib.Path(
                self.state.document.attributes["source"]).parent.joinpath(
                argument)
            if len(list(worker_directory.glob("*-worker.rst"))) == 1:
                implementations.append(
                    list(worker_directory.glob("*-worker.rst"))[0])
            elif len(list(worker_directory.glob("*-worker.rst"))) == 0:
                self.state_machine.reporter.warning(
                    f"Implementation argument {argument} gives directory "
                    + f"{worker_directory} which does not contain a "
                    + "*-worker.rst file",
                    line=self.lineno)
            else:
                self.state_machine.reporter.warning(
                    f"Implementation argument {argument} gives directory "
                    + f"{worker_directory} which does contain more than one "
                    + "*-worker.rst file, so cannot uniquely determine main "
                    + "worker documentation page",
                    line=self.lineno)

        if not implementations:
            self.state_machine.reporter.warning(
                "No valid worker documentation pages found", line=self.lineno)
            return content

        implementation_list = docutils.nodes.bullet_list()
        for implementation in implementations:
            list_item = docutils.nodes.list_item()
            name = implementation.parent.stem
            model = implementation.parent.suffix[1:]

            worker_link = sphinx.addnodes.pending_xref(
                "", refdoc=self.state.document.settings.env.docname,
                refdomain="std", refexplicit="True",
                reftarget=f"{name}-{model}-worker", reftype="ref",
                refwarn=True)
            link_text = docutils.nodes.inline(text=f" ({model.upper()})")
            worker_link.append(link_text)

            worker_name_link = docutils.nodes.paragraph()
            worker_name_link.append(docutils_helpers.rst_string_convert(
                self.state, f"``{name}``").children[0].children[0])
            worker_name_link.append(worker_link)

            list_item.append(worker_name_link)

            with open(implementation, "r") as implementation_file:
                implementation_text = implementation_file.read()
                # Directives that are met in this text can cause an error,
                # since we only want the first paragraph of text we can ignore
                # directives at this level, so remove the "::" that follow a
                # directive's label.
                implementation_text = implementation_text.replace(
                    "::", " [Directives disabled in implementation summary] ")
            parser_settings = docutils.frontend.OptionParser(
                components=(docutils.parsers.rst.Parser,)
            ).get_default_values()
            implementation_documentation = docutils.utils.new_document(
                implementation_file.name, parser_settings)
            try:
                docutils.parsers.rst.Parser().parse(
                    implementation_text, implementation_documentation)
            # A blank except is a bad thing since any error will be masked.
            # However the parser can return any error due to poor syntax
            # and the traceback looks to only report Exception so that is
            # all that can be captured.
            except Exception:
                self.state_machine.reporter.warning(
                    f"Worker documentation {implementation} includes a "
                    + "syntax error", line=self.lineno)

            # Take content from the "document" (page) wrapping and get only the
            # sections contained within. It is assumed - as all pages are
            # structured in the same format - on reaching the second title the
            # detail section is reached and so any summary text to include on
            # the component page has already been reached.
            title_found = False
            for section in implementation_documentation.traverse():
                if isinstance(section, docutils.nodes.title):
                    if title_found:
                        break
                    else:
                        title_found = True
                elif isinstance(section, docutils.nodes.paragraph):
                    if title_found:
                        list_item.append(section)
                        break

            implementation_list.append(list_item)

        content.append(implementation_list)

        return content
