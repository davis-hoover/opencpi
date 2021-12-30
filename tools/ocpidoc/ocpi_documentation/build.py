#!/usr/bin/env python3

# Build documentation
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
import sys
import sphinx.cmd.build
import _opencpi.util as ocpiutil
from .conf import BUILD_FOLDER
from ocpi_documentation.create import _template_to_specific

def build(directory, build_only=False, mathjax=None, config_options=[],
          **kwargs):
    """ Build documentation for set directory

    Args:
        directory (``str``): Directory containing source documentation files.
        build_only (``bool``, optional): Options to build only, so do not run
            spell checker.
        mathjax (``str``): Path to MathJax to be included. If not set, or set
            to ``None``, Sphinx default is used.
        config_options (``list``): Sphinx options to override those set in
            ``conf.py``, each item in the list should be a string in name=value
            format.
        kwards (optional): Other keyword arguments, provided for compatibility
            interfacing. Values not used.

    Returns:
        Return value of Sphinx build action.
    """
    source_directory = pathlib.Path(directory).resolve().absolute()
    build_directory = source_directory.joinpath("gen/" + BUILD_FOLDER)
    conf_directory = pathlib.Path(__file__).resolve().absolute().parent

    # As the name of the main / top level documentation file will depend on the
    # type of source documentation this needs to be set at build time. Due to
    # how conf.py is called this cannot be set in conf.py, so pass as a build
    # option

    # Let the generic "dir_info" function determine the default name for the
    # primary RST file, but also look for some backward compatible names
    # and sphinx defaults

    _,asset_type,_,xml_file,asset_name = ocpiutil.get_dir_info(str(source_directory))
    stem = source_directory.stem
    # If there is no possible primary XML file, use the stem, e.g. "specs".
    default_rst_file_name = (pathlib.PurePath(xml_file).stem if xml_file
                             else stem) + ".rst"
    default_rst_path = source_directory.joinpath(default_rst_file_name)
    master_doc = None
    if default_rst_path.is_file():
        master_doc = default_rst_path.stem # leave it local relative to source dir w/o .rst
    elif source_directory.joinpath("gen", default_rst_file_name).is_file():
        master_doc = default_rst_path.stem
        # Note that the default files will not need to access any other files
        source_directory = source_directory.joinpath("gen");
    else:
        # Non-default names for legacy (names that do not match the primary XML file)
        if asset_type == "component":
            master_doc = f"{stem}-index"
        elif asset_type == "worker":
            master_doc = f"{stem}-worker"
        elif asset_type == "library":
            master_doc = f"{stem}-library"
        else:
            rst_files = list(source_directory.glob("*.rst"))
            if len(rst_files) == 1:
                # If nothing else matches and there is a single rst file in the
                # directory use that
                master_doc = rst_files[0].stem
            elif "index" in map(lambda f: f.stem, rst_files):
                # Use Sphinx default, as best case guess in this case
                master_doc = "index"
        if not master_doc or not source_directory.joinpath(master_doc).is_file():
            # Try using the default template in the gen/ subdir
            empty_template_path = pathlib.Path(__file__).parent.joinpath("rst_templates",
                                                                         "default-" + asset_type + ".rst")
            xml_path = pathlib.Path(xml_file)
            if empty_template_path.is_file(): # note xml_file does not have to exist
                with open(empty_template_path, "r") as empty_template_file:
                    template = empty_template_file.read()
                    source_directory = source_directory.joinpath("gen")
                    generated_rst_file = source_directory.joinpath(xml_path.stem + ".rst")
                    generated_rst_file.parent.mkdir(parents=True,exist_ok=True)
                    with open(generated_rst_file,"w") as rst_file:
                        rst_file.write(_template_to_specific(template, asset_name,
                                                             source_directory.suffix,
                                                             None,
                                                             None))
                        master_doc = generated_rst_file.stem
        if not master_doc:
            print("Warning:  when building docs in directory " + str(directory) +
                  f" there is no \"{default_rst_file_name}\" or \"{xml_path.name}\" or " +
                  "\"index.rst\" file present.",
                  file=sys.stderr)
            return 0
    if not os.path.isfile(str(source_directory) + "/" + master_doc + ".rst"):
        print("Error:  In directory " + str(directory) +
              " there is no file " + master_doc + ".rst, use: ocpidoc create?", file=sys.stderr)
        return 1
    build_options = [str(source_directory), str(build_directory),
                     "-c", str(conf_directory)]
    build_options = build_options + ["-D", f"master_doc={master_doc}"]

    for option in config_options:
        build_options = build_options + ["-D", option]

    if mathjax is not None:
        mathjax = pathlib.Path(mathjax)
        if mathjax.is_dir():
            build_options = build_options + [
                "-D", "mathjax_path=mathjax/es5/tex-chtml-full.js",
                "-D", "html_static_path=" +
                      f"static,{str(mathjax.absolute())}"]
        else:
            raise NotADirectoryError(f"{mathjax} is not a directory")

    return_value = sphinx.cmd.build.main(build_options)

    if build_only is False:
        sphinx.cmd.build.main(build_options + ["-b", "spelling"])

    if return_value == 0:
        home_page = build_directory.joinpath(f"{master_doc}.html")
        print(f"Primary HTML file for this asset is: {home_page}")
    # No error message as Sphinx will have printed this
    return return_value
