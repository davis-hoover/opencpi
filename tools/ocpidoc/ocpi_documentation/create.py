#!/usr/bin/env python3

# Copy a documentation template file to the set path
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


import datetime
import pathlib
import re
import sys

import _opencpi.util as ocpiutil

AUTHORING_MODELS = [".rcc", ".hdl", ".ocl"]


def _template_to_specific(template, name, authoring_model=None,
                          project_prefix=None, project=None, library=None, toc=None):
    """ Replace template placeholder text with specific instance text

    Args:
        template (``str``): The template text to be updated.
        name (``str``): The specific element name to be used.
        authoring_model (``str``, optional): The specific authoring model to be
            used. If not set (or set to ``None``) will not be added to specific
            instance.
        project_prefix (``str``, optional): The specific project prefix to be
            used. If not set (or set to ``None``) will not be added to specific
            instance.
        project (``str``, optional): The project name to be used. If not set
            (or set to ``None``) will not be added to specific instance.
        library (``str``, optional): Specific library name to be swapped in. If
            not set (or set to ``None``) will ne be swapped.

    Returns:
        Template text with placeholders replaced with specific instance text.
    """
    # Different formats for the name text
    if name is not None:
        name_proper = name.replace("_", " ").capitalize()
        name_code = name.replace(" ", "_").lower()
        template = template.replace("%%NAME-PROPER%%", name_proper)
        template = template.replace("%%NAME-CODE%%", name_code)

    template = template.replace("%%YEAR%%", str(datetime.datetime.now().year))

    if project_prefix is not None:
        template = template.replace("%%PROJECT_PREFIX%%", project_prefix)

    if project is not None:
        template = template.replace("%%PROJECT%%", project)

    if authoring_model is not None:
        template = template.replace("%%AUTHORING_MODEL%%",
                                    authoring_model.upper())

    if library is not None:
        template = template.replace("%%LIBRARY%%", library.lower())

    if toc is not None:
        template = template.replace("%%TOC%%", toc)

    # Regex finds all underlined titles and replaces underline to allign
    # the number of characters to the title
    regex = ".+\n(=+|-+|~+)\n"
    for match in re.finditer(regex, template):
        titles = match.group().split("\n")
        if len(titles[0]) != len(titles[1]):
            template = template.replace(match.group(), titles[0] + "\n"
                                        + titles[1][0] * len(titles[0])
                                        + "\n")

    return template


# for now map asset types to doc types, but templates could be make
# consistent with asset types and make this simpler
asset_type_to_doc_type = {
    '.*-worker' : 'worker',
    'applications' : 'applications-directory',
    'library' : 'component-library',
    'hdl-library' : 'primitive-library',
    'hdl-core' : 'primitive-core',
    'libraries' : 'components-directory',
    'hdl-primitives' : 'primitives-directory',
}

def create(directory, documentation_type=None, asset_type=None, file_name=None, name=None,
           verbose=None, file_only=None, **kwargs):
    """ Copy template documentation files into place

    Args:
        directory (``str``): Directory documentation template is to be save in.
        documentation_type (``str``): Documentation type, set based on the
            available types in the ``rst_templates`` directory.
            If None, it will be determined from asset_type
        name (``str``, optional): Name of the new documentation item. Must be
            provided when ``documentation_type`` is ``component``,
            ``primitive``, ``protocol``, ``worker``, ``component-library`` or
            ``primitive-library``. Will override default is used for anything
            else.
        file_name:  The name to be used for the primary RST file, if supplied
        kwargs (optional): Other keyword arguments, provided for compatibility
            interfacing. Values not used.
    """

    if asset_type:
        if documentation_type:
            raise ValueError(f"Only one of asset_type and documentation_type is allowed")
        documentation_type = asset_type
        for key, type in asset_type_to_doc_type.items():
            if re.match(key, asset_type):
                documentation_type = type
    directory = pathlib.Path(directory) # allow str or path
    directory_templates = []
    for path in pathlib.Path(__file__).parent.joinpath("rst_templates").glob(
            "*"):
        if path.is_dir():
            directory_templates.append(path.name)

    if directory.suffix.lower() in AUTHORING_MODELS:
        authoring_model = directory.suffix[1:].lower()
    else:
        authoring_model = None

    # Determine if within an OpenCPI project and if so get the project name and
    # prefix so can be used to replace placeholder in template.
    project_path = ocpiutil.is_path_in_project(directory)
    if project_path:
        attrs = ocpiutil.get_project_attributes(project_path)
        package_id = ocpiutil.get_project_package_id(project_path, attrs)
        parts = package_id.split('.')
        project = parts[-1]
        project_prefix = '.'.join(parts[:-1])
    else:
        raise ValueError(f"Directory {directory} for {documentation_type} documentation, "+
                         f"is not in a project")
    # Determine if within a library and if so get the library name so can be
    # used to replace placeholder in template. For loop limited to 2 to allow
    # documentation directory is a worker or component directory
    library_search_directory = directory
    library = None
    for _ in range(2):
        if ocpiutil.get_dirtype(library_search_directory) == 'library':
            library = library_search_directory.name
            break
        else:
            library_search_directory = library_search_directory.parent

    # Directory templates - use them if the asset itself has/is a directory
    if not file_only and documentation_type in directory_templates:
        if name is None:
            raise ValueError(f"For {documentation_type} a name must be given")
        # This is a hack. The templates should *always* be placed in the provided
        # directory whether the template is a directory or not
        if asset_type: # if we were called with the true path of the asset...
            destination_path = directory
        else:
            destination_path = pathlib.Path(
                directory).resolve().absolute().joinpath(
                    f"{name}.{documentation_type[0:4]}")
        if not destination_path.exists():
            destination_path.mkdir()
        templates = list(pathlib.Path(__file__).parent.joinpath(
            "rst_templates").joinpath(f"{documentation_type}").glob("*"))
        for file in templates:
            if file.suffix == ".rst":
                file_name = f"{name}-{file.stem}.rst"
            else:
                file_name = file.name
            file_path = destination_path.joinpath(file_name)
            if file_name.endswith('.rst') and file.stem == destination_path.name.split('.')[-1]:
                primary_path = file_path
            if file_path.is_file():
                print(f'File "{file_path}" already exists')
            else:
                with open(file, "r") as template_file:
                    template = template_file.read()

                with open(file_path, "w+") as documentation_file:
                    documentation_file.write(_template_to_specific(
                        template, name, authoring_model, project_prefix,
                        project, library))

    # Single page templates
    else:
        destination_path = directory.resolve().absolute()
        primary_path = destination_path
        if file_name:
            destination_path = destination_path.joinpath(f"{file_name}.rst")
        elif documentation_type[-8:] == "-library":
            if name is None:
                raise ValueError(
                    f"For {documentation_type} a name must be given")
            destination_path = destination_path.joinpath(f"{name}-library.rst")
        elif documentation_type[-10:] == "-directory":
            if name is None:
                if documentation_type[:7] == "project":
                    destination_path = destination_path.joinpath("index.rst")
                else:
                    destination_path = destination_path.joinpath(
                        f"{documentation_type[:-10]}.rst")
            else:
                destination_path = destination_path.joinpath(f"{name}.rst")
        else:
            if name is None:
                raise ValueError(
                    f"For {documentation_type} a name must be given")
            destination_path = destination_path.joinpath(
                f"{name}-{documentation_type}.rst")

        if destination_path.exists():
            print(f"Documentation file {destination_path} already exists")
            return

        template_path = pathlib.Path(__file__).parent.joinpath(
            "rst_templates").joinpath(f"{documentation_type}.rst")
        if not template_path.exists():
            print(f'Warning: no documentation template for asset type "{documentation_type}" so '+
                  f'no documentation files are generated')
            return
        with open(template_path, "r") as template_file:
            template = template_file.read()
        with open(destination_path, "w+") as documentation_file:
            documentation_file.write(_template_to_specific(
                template, name, authoring_model, project_prefix,
                project, library))
    if verbose:
        print("Documentation template initialized at:", primary_path, file=sys.stderr)
