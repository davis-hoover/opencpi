#!/usr/bin/env python3

# Dependency directive
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


class OcpiDocumentationDependencies(docutils.parsers.rst.Directive):
    """ ocpi_documentation_dependency directive
    """
    has_context = True

    # Arguments is list of file paths that dependencies are to be tracked for
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True

    def run(self):
        """ Action when ocpi_documentation_dependencies directive called

        Lists the dependencies for the files passed.

        Returns:
            List with the docutils tree map to replace the directive in the
                source text with.
        """
        # Variable to add the resulting output to
        content = []

        content.append(docutils.nodes.paragraph(
            text="Automatic dependency tracking not yet implemented."))

        return [content]
