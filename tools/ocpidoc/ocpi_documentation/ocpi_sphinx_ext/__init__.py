#!/usr/bin/env python3

# Register directives with Sphinx
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


from .ocpi_documentation_dependencies import OcpiDocumentationDependencies
from .ocpi_documentation_implementations import \
    OcpiDocumentationImplementations
from .ocpi_documentation_ports import OcpiDocumentationPorts
from .ocpi_documentation_properties import OcpiDocumentationProperties
from .ocpi_documentation_test_detail import OcpiDocumentationTestDetail
from .ocpi_documentation_test_result_summary import \
    OcpiDocumentationTestResultSummary
from .ocpi_documentation_utilization import OcpiDocumentationUtilization
from .ocpi_documentation_worker import OcpiDocumentationWorker


def setup(app):
    """ Sphinx setup phase

    Adds directives in the extension to running Sphinx instance.

    Args:
        app: The Sphinx instance to add the directives to.
    """
    app.add_directive("ocpi_documentation_dependencies",
                      OcpiDocumentationDependencies)
    app.add_directive("ocpi_documentation_implementations",
                      OcpiDocumentationImplementations)
    app.add_directive("ocpi_documentation_ports", OcpiDocumentationPorts)
    app.add_directive("ocpi_documentation_properties",
                      OcpiDocumentationProperties)
    app.add_directive("ocpi_documentation_test_detail",
                      OcpiDocumentationTestDetail)
    app.add_directive("ocpi_documentation_test_result_summary",
                      OcpiDocumentationTestResultSummary)
    app.add_directive("ocpi_documentation_utilization",
                      OcpiDocumentationUtilization)
    app.add_directive("ocpi_documentation_worker", OcpiDocumentationWorker)
