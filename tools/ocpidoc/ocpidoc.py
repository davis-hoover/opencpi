#!/usr/bin/env python3

# Command line script to manage and build documentation
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


import argparse
import pathlib
import sys

import _opencpi.util as ocpiutil
import ocpi_documentation


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Initialize and build documentation.")
    parser.add_argument("-d", "--directory", type=str,
                        default=pathlib.Path.cwd(),
                        help="Directory to run action in.")
    subparsers = parser.add_subparsers(help="Documentation action to take")

    create_parser = subparsers.add_parser(
        "create", help="Create documentation template files")
    create_parser.set_defaults(func=ocpi_documentation.create)
    template_types = [template.stem for template in pathlib.Path(
        ocpi_documentation.__file__).parent.joinpath("rst_templates").glob("*")
    ]
    create_parser.add_argument("documentation_type", type=str, choices=template_types,
                               help="Documentation type to be created")
    create_parser.add_argument("name", type=str, nargs="?", default=None,
                               help="Name of element")

    build_parser = subparsers.add_parser("build", help="Build documentation")
    build_parser.set_defaults(func=ocpi_documentation.build)
    build_parser.add_argument("-b", "--build_only", action="store_true",
                              help="Build only, do not spell check")
    build_parser.add_argument("-m", "--mathjax", type=str, default=None,
                              help="Use alternative MathJax source path")
    # Option flag is -D to match Sphinx
    build_parser.add_argument("-D", dest="config_options", action="append",
                              default=[],
                              help="Set Sphinx configuration option")

    clean_parser = subparsers.add_parser("clean",
                                         help="Remove built documentation")
    clean_parser.set_defaults(func=ocpi_documentation.clean)
    clean_parser.add_argument("-r", "--recursive", action="store_true",
                              help="Remove built documentation from all "
                                    + "subfolders")
    # For consistency vs. all other ocpi* commands
    # force non-zero exit code if argparse exits, even for help etc.
    # force help if no arguments
    try:
        arguments = parser.parse_args(args=None if sys.argv[1:] else ['--help'])
    except SystemExit:
        sys.exit(1)

    # Run only when the directory is in a project
    project_path = ocpiutil.get_path_to_project_top(str(arguments.directory))
    if project_path is not None:
        sys.exit(arguments.func(**vars(arguments)))
    else:
        print("Error: the directory " + str(arguments.directory) +
              " is not inside a OpenCPI project directory",
              file=sys.stderr)
        sys.exit(1)
