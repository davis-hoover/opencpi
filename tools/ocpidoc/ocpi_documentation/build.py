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

import sphinx.cmd.build

from .conf import BUILD_FOLDER


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

    build_options = [str(source_directory), str(build_directory),
                     "-c", str(conf_directory)]

    # As the name of the main / top level documentation file will depend on the
    # type of source documentation this needs to be set at build time. Due to
    # how conf.py is called this cannot be set in conf.py, so pass as a build
    # option
    if source_directory.suffix == ".comp":
        master_doc = f"{source_directory.stem}-index"
    elif source_directory.suffix in [".hdl", ".rcc", ".ocl"]:
        master_doc = f"{source_directory.stem}-worker"
    elif len(list(source_directory.glob("*-library.rst"))) == 1:
        master_doc = list(source_directory.glob("*-library.rst"))[0].stem
    elif len(list(source_directory.glob("specs.rst"))) == 1:
        master_doc = list(source_directory.glob("specs.rst"))[0].stem
    elif len(list(source_directory.glob("*.rst"))) == 1:
        # If nothing else matches and there is a single rst file in the
        # directory use that
        master_doc = list(source_directory.glob("*.rst"))[0].stem
    else:
        # Use Sphinx default, as best case guess in this case
        master_doc = "index"
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
        print(f"Home page at: {home_page}")
    # No error message as Sphinx will have printed this
    return return_value
