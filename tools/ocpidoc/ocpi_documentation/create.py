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


AUTHORING_MODELS = [".rcc", ".hdl", ".ocl"]


def _template_to_specific(template, name, authoring_model=None,
                          project_prefix=None, project=None, library=None):
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

    return template


def create(directory, documentation_type, name=None, **kwargs):
    """ Copy template documentation files into place

    Args:
        directory (``str``): Path documentation template is to be save to.
        documentation_type (``str``): Documentation type, set based on the
            available types in the ``rst_templates`` directory.
        name (``str``, optional): Name of the new documentation item. Must be
            provided when ``documentation_type`` is ``component``,
            ``primitive``, ``protocol``, ``worker``, ``component-library`` or
            ``primitive-library``. Will override default is used for anything
            else.
        kwargs (optional): Other keyword arguments, provided for compatibility
            interfacing. Values not used.
    """
    directory = pathlib.Path(directory)
    documentation_type = documentation_type

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
    # prefix so can be used to replace placeholder in template. For loop
    # limited to 5 to allow documentation directory in a primitive's directory
    # to still reach project directory - likely maximum path depth
    project_search_directory = directory
    project = None
    project_prefix = None
    for _ in range(5):
        if project_search_directory.joinpath("Project.mk").is_file():
            with open(project_search_directory.joinpath("Project.mk"),
                      "r") as project_file:
                for line in project_file:
                    if line.startswith("PackagePrefix="):
                        project_prefix = line[14:].strip()
                    if line.startswith("PackageName="):
                        project = line[12:].strip()
            break
        else:
            project_search_directory = project_search_directory.parent
        if project_search_directory == pathlib.Path("/"):
            break

    # Determine if within a library and if so get the library name so can be
    # used to replace placeholder in template. For loop limited to 2 to allow
    # documentation directory is a worker or component directory
    library_search_directory = directory
    library = None
    for _ in range(2):
        if library_search_directory.joinpath("Library.mk").is_file():
            library = library_search_directory.name
            break
        else:
            library_search_directory = library_search_directory.parent

    # Directory templates
    if documentation_type in directory_templates:
        if name is None:
            raise ValueError(f"For {documentation_type} a name must be given")
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
            if destination_path.joinpath(file_name).is_file():
                print(
                    f"File {destination_path.joinpath(file_name)} already "
                    + "exists")
            else:
                with open(file, "r") as template_file:
                    template = template_file.read()

                with open(destination_path.joinpath(file_name),
                          "w+") as documentation_file:
                    documentation_file.write(_template_to_specific(
                        template, name, authoring_model, project_prefix,
                        project, library))

    # Single page templates
    else:
        destination_path = pathlib.Path(directory).resolve().absolute()
        if documentation_type[-8:] == "-library":
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
        with open(template_path, "r") as template_file:
            template = template_file.read()
        with open(destination_path, "w+") as documentation_file:
            documentation_file.write(_template_to_specific(
                template, name, authoring_model, project_prefix,
                project, library))

    print("Template initialized at:", destination_path)
