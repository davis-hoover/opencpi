#!/usr/bin/env python3

# Test platforms directive
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

import docutils
import docutils.parsers.rst


class OcpiDocumentationTestPlatforms(docutils.parsers.rst.Directive):
    """ ocpi_documentation_test_platforms
    """
    has_content = False
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True
    # Allow overriding of the automatically determined file paths.
    option_spec = {}

    def run(self):
        """ Action when ocpi_documentation_test_platforms directive called

        Generates a page with a list of platforms that tests have been ran on.

        Returns:
            List with the docutils tree map to replace the directive in the
                source text with.
        """
        # Variable to add the resulting output to
        content = []

        # Determine path to <asset_name>.test/
        asset_name = os.path.splitext(pathlib.Path(
            self.state.document.attributes["source"]).resolve(
        ).parent.name)[0]

        current_directory = pathlib.Path(
            self.state.document.attributes["source"]).resolve().parent

        test_directory = current_directory.joinpath(
            f"../{asset_name}.test/run").resolve()

        # Get the names of all folders in <asset_name>.test/run/
        # These are the names of the platforms tested
        directories = []
        if test_directory.is_dir():
            directories = [directory.name for directory in os.scandir(
                test_directory) if directory.is_dir()]

        if(len(directories) > 0):
            paragraph = docutils.nodes.paragraph(
                "", "Tested platforms:")
            item_list = docutils.nodes.bullet_list()
            for directory in directories:
                item = docutils.nodes.list_item()
                item.append(docutils.nodes.literal(text=directory))
                item_list.append(item)
            paragraph.append(item_list)
            content.append(paragraph)
        else:
            content.append(docutils.nodes.paragraph(
                "", "Tested platforms: None"))

        return content
