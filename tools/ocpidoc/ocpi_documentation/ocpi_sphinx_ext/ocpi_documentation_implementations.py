#!/usr/bin/env python3

# Property summary directive
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
import os

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

        implementations = [] # actual paths of worker doc primary rst files
        source_path = pathlib.Path(self.state.document.attributes["source"])
        source_dir = source_path.parent
        for argument in self.arguments:
            if argument.startswith("../"):
                link = "gen/" + argument[2:]
                if source_dir.joinpath(link).exists():
                    argument = link
            worker_directory = source_dir.joinpath(argument)
            worker_name = worker_directory.stem
            found = None
            # try {worker_name}-worker.rst for legacy, {worker_name}.rst, then index.rst
            # {worker_name}.rst for consistency with {worker_name}.xml, as doc'd
            for doc_name in [ f'{worker_name}-worker', worker_name, "index" ]:
                doc = worker_directory.joinpath(doc_name + ".rst")
                if doc.exists():
                    implementations.append(doc)
                    found = doc
                    break
            if not found:
                self.state_machine.reporter.warning(
                    f"Implementation argument {argument} gives directory "
                    + f"{worker_directory} which does not contain a "
                    + f"{worker_name}.rst (preferred) or {worker_name}-worker.rst or index.rst file",
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
                implementation.relative_to(source_dir).with_suffix(""),
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

        # A ViewList is used to parse a ReST toctree and insert it beneath
        # this directive. The toctree links to worker documentation files,
        # which enables, for example, figure and equation numbering to be
        # displayed in the generated worker documentation pages.
        toctree_rst = docutils.statemachine.ViewList()
        toctree_rst.append(".. toctree::", source_path, self.lineno + 1)
        toctree_rst.append("   :hidden:", source_path, self.lineno + 2)
        toctree_rst.append("   :glob:", source_path, self.lineno + 3)
        toctree_rst.append("", source_path, self.lineno + 4)

        line_number_rst = self.lineno + 5
        for implementation in implementations:
            # prepare a path acceptable to toctree, eliminating any ".." and making it
            # relative to the top level "project"" directory, with leading /
            # (called "absolute" in the toctree documentation)
            toctree_docname = "/" + str(
                implementation.
                relative_to(pathlib.Path(self.state.document.settings.env.project.srcdir)).
                with_suffix(""))
            toctree_rst.append(f"   {toctree_docname}", source_path, line_number_rst)
            line_number_rst = line_number_rst + 1

        self.state.nested_parse(toctree_rst, 0, implementation_list)

        content.append(implementation_list)

        return content
