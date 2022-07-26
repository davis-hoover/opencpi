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
import re
import xml.etree.ElementTree as xt
import tempfile
import _opencpi.util as ocpiutil
from .conf import BUILD_FOLDER
from .create import _template_to_specific

def _get_spelling_options(conf_directory, source_directory, build_directory):
    """ Look for ocpidoc.dict and Project.dict files in the config directory
        and project top directory, respectively, and if present use them as
        custom dictionaries. Also look for a project language and set sphinx
        to use that if present.

    Args:
        conf_directory (``pathlib.Path``): The configuration directory.
        source_directory (``pathlib.Path``): The documentation source directory.
        build_directory (``pathlib.Path``): The documentation build directory.

    Returns:
        List of Sphinx options, each item a string in name=value format.
    """

    language = "en_US"          # Default to US English
    project_language = None  # Project specific language
    dictionaries = []

    # Look for the common tools dictionary
    common_dictionary = conf_directory.joinpath("ocpidoc.dict").resolve()
    if not common_dictionary.is_file():
        print("OpenCPI common word list NOT FOUND:", common_dictionary)
    else:
        print(f"Using OpenCPI common word list: {common_dictionary}")
        dictionaries.append(str(common_dictionary))

    # Look for a Project.dict in project top dir
    project_path = ocpiutil.get_path_to_project_top(str(source_directory))
    project_dictionary = pathlib.Path(project_path).joinpath("Project.dict")
    if not project_dictionary.is_file():
        print("Project custom word list not found:", project_dictionary)
    else:
        print(f"Using project custom word list: {project_dictionary}")

        # Read in project dictionary, without newline chars
        with open(project_dictionary, "r") as d:
            dictionary_lines = d.read().splitlines()

        # Will read language from a comment line in the format "# lang: <project language>"
        expected_format="# lang: <project language>"
        project_language = None
        non_empty_dictionary_lines = []
        for line in dictionary_lines:

            if line.startswith("#"):
                # Line is a comment
                # Is this line defining the language to spell check in?
                tokens = line[1:].strip().split() # Get tokens after the first # character
                if len(tokens) > 1 and tokens[0] =="lang:":
                    if project_language is None:
                        project_language = tokens[1]
                    else:
                        raise RuntimeError(f"Project language defined one than once in file: {project_dictionary}")
            elif len(line) > 0:
                # Non-empty, non-comment line
                non_empty_dictionary_lines.append(line)

        if len(non_empty_dictionary_lines) == len(dictionary_lines):
            # No blank or comment lines, use file as is
            dictionaries.append(str(project_dictionary))
        else:
            # Create temporary file with only the words, no comments or spaces
            if not os.path.exists(build_directory):
                os.makedirs(build_directory)
            word_list = os.path.join(build_directory, 'project_wordlist.dict')

            with open(word_list, "w", encoding="UTF-8") as outfile:
                outfile.write("\n".join(non_empty_dictionary_lines))
            dictionaries.append(str(word_list))

        if project_language is None:
            print(f"Using default language ({language}) as project custom word list does not define language in format \"{expected_format}\".")
        else:
            # Validate language is acceptable.
            # Do this import at runtime so that external callers to this module (dir) do not
            # have to import enchant unless they are doing building with spellcheck
            import enchant
            if enchant.dict_exists(project_language):
                language = project_language
                print(f"Setting language ({language}) from lang: comment in project custom word list.")
            else:
                print(
                    f"WARNING: Failed to set language from lang: comment in project custom word list."
                    f" Language ({project_language}) not installed,"
                    f" falling back to default ({language}) instead.")

    # Override language and dictionary settings via build options
    spelling_options = [f"spelling_lang={language}"]
    if len(dictionaries) > 0:
        dictionaries = ",".join(dictionaries)
        spelling_options.append(f"spelling_word_list_filename={dictionaries}")
    print("GCS: spelling_options",spelling_options)
    return spelling_options

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
        kwargs (optional): Other keyword arguments, provided for compatibility
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
    if not asset_type:
        return
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
        source_directory = source_directory.joinpath("gen")
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
        if not master_doc or not source_directory.joinpath(master_doc + ".rst").is_file():
            # Try using the default template in the gen/ subdir
            default_template_path = pathlib.Path(__file__).parent.joinpath("rst_templates",
                                                                           "default-" + asset_type + ".rst")
            xml_path = pathlib.Path(xml_file)
            if default_template_path.is_file(): # note xml_file does not have to exist
                with open(default_template_path, "r") as default_template_file:
                    template = default_template_file.read()
                    # source_directory = source_directory.joinpath("gen")
                    generated_rst_file = source_directory.joinpath('gen', xml_path.stem + ".rst")
                    generated_rst_file.parent.mkdir(parents=True,exist_ok=True)
                    toc = None
                    if asset_type == 'library': # put this elsewhere of course for recursion etc.
                        toc = ('   ../*.comp/*-comp\n'+
                               '   ../*.comp/*-index\n')
                        for dir in source_directory.iterdir():
                            if dir.is_dir() and dir.suffix != '' and dir.suffix != '.test':
                                xml = dir.joinpath(dir.stem + ".xml")
                                if not xml.exists():
                                    xml = dir.joinpath(dir.name.replace('.','-') + ".xml")
                                    if not xml.exists():
                                        continue
                                worker_xml = xt.fromstring(xml.read_text().replace('xi:include','xiinclude'))
                                for child in list(worker_xml):
                                    if child.tag.lower() == 'componentspec':
                                        rst = dir.joinpath(dir.stem + ".rst")
                                        if not rst.exists():
                                            rst = dir.joinpath(dir.stem + "-worker.rst")
                                            if not rst.exists():
                                                rst = dir.joinpath(dir.name.replace('.','-') + ".rst")
                                                if not rst.exists():
                                                    continue
                                        toc += f'   ../{dir.name}/{rst.stem}\n'
                                        break
                    with open(generated_rst_file,"w") as rst_file:
                        model = source_directory.suffix.lstrip('.')
                        if model == '':
                            model = None
                        rst_file.write(_template_to_specific(template, asset_name,
                                                             authoring_model=model,
                                                             toc=toc))
                        master_doc = 'gen/'+generated_rst_file.stem
        if not master_doc:
            print("Warning:  when building docs in directory " + str(directory) +
                  f" there is no \"{default_rst_file_name}\" or \"{xml_path.name}\" or " +
                  "\"index.rst\" file present.",
                  file=sys.stderr)
            return 0
    source_path = source_directory.joinpath(master_doc + ".rst")
    if not source_path.exists():
        print("Error:  In directory " + str(directory) +
              " there is no file " + master_doc + ".rst, use: ocpidoc create?", file=sys.stderr)
        return 1
    links=[]
    if asset_type in ['component', 'worker', 'test']:
        # Due to sphinx toctree limitations (no ../ paths supported, many requests to fix it),
        # create symlinks to other directories or files in the same library if we are using them
        # in some known directives.
        # We must remove the links after the sphinx build runs, otherwise they will be seen as duplicates
        # when docs are built higher up the directory structure (e.g. at the library or project level).
        # Please someone figure out a better way to do this!
        source_directory.joinpath("gen").mkdir(exist_ok=True)
        with open(source_path) as file:
            for line in file:
                for directive in ['ocpi_documentation_implementations', 'figure']:
                    result = re.match(f"^\\.\\.\\s{directive}::(.*)", line)
                    if result:
                        words = result.group(1).split()
                        for word in words:
                            components = word.split('/')
                            if components[0] == '..':
                                target = components[1]
                                link = source_directory.joinpath("gen/", target)
                                if not link.exists():
                                    link.symlink_to(pathlib.Path("../../" + target))
                                    links.append(link)

    build_options = [str(source_directory), str(build_directory),
                     "-c", str(conf_directory)]
    build_options = build_options + ["-D", f"master_doc={master_doc}"]

    if not build_only:
        # Build up spelling options
        for option in _get_spelling_options(conf_directory, source_directory, build_directory):
            build_options = build_options + ["-D", option]

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

    # Do this import at runtime so that external callers to this module (dir) do not have to import
    # sphinx unless they are doing building
    import sphinx.cmd.build
    return_value = sphinx.cmd.build.main(build_options)

    if build_only is False:
        sphinx.cmd.build.main(build_options + ["-b", "spelling"])

    # remove the links we created temporarily for component docs
    for link in links: link.unlink()

    if return_value == 0:
        home_page = build_directory.joinpath(f"{master_doc}.html")
        print(f'The primary HTML file for this "{asset_type}" asset is: {home_page}')
    # No error message as Sphinx will have printed this
    return return_value
