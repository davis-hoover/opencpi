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
# A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.
"""
definitions for utility functions that have to do with opencpi project layout
"""

import os
import sys
import os.path
import fnmatch
import logging
import collections
from glob import glob
from pathlib import Path
import re
import xml.etree.ElementTree as xt
from _opencpi.util import cd, set_vars_from_make, OCPIException, logging
import subprocess

def get_make_vars_rcc_targets():
    """
    Get make variables from rcc-targets.mk
    Dictionary key examples are:
        RccAllPlatforms, RccPlatforms, RccAllTargets, RccTargets
    """
    if not get_make_vars_rcc_targets.dict:
        get_make_vars_rcc_targets.dict = {}
        for key,value in get_platform_make_dictionary().items():
            if key.startswith("Rcc"):
                get_make_vars_rcc_targets.dict[key] = value
    return get_make_vars_rcc_targets.dict
get_make_vars_rcc_targets.dict=None

#    return set_vars_from_make(os.environ["OCPI_CDK_DIR"] +
#                              "/include/rcc/rcc-targets.mk",
#                              "ShellRccTargetsVars=1", "verbose")

###############################################################################
# Utility functions for collecting information about the directories
# in a project
###############################################################################

def get_makefile(directory, type=None):
    """
    Return a tuple consisting of the appropriate makefile as well as the directory
    to call "make" in
    """
    directory = str(directory) # allow paths as input
    if not type:
        type = get_dirtype(directory)
    if os.path.exists(directory + "/Makefile"):
        mkf="Makefile"
    else:
        hdl = "hdl/" if type and type.startswith("hdl-") else ""
        mkf = os.environ["OCPI_CDK_DIR"] + "/include/" + hdl + type + ".mk"
    return mkf,directory

def get_dirtype(directory="."):
    """
    Return the make-type of the directory or None if it has no make-type
    """
    info = get_dir_info(directory)
    return info[0] if info else None

def get_maketype(directory):
    """
    Return the make-type extracted from the Makefile in a diretory
    """
    match = None
    file = directory + "/Makefile"
    if os.path.isfile(file):
        with open(file) as mk_file:
            for line in mk_file:
                result = re.match(r"^\s*include\s*.*OCPI_CDK_DIR.*/include/(hdl/)?(.*)\.mk.*", line)
                if result:
                    match = result.group(2)
                    if match == "lib":
                        match = "library"
    return match

def get_dir_info(directory=".", careful=False):
    """
    Determine a directory's attributes in a tuple:  make-type, asset-type, directory, xml_file
    The primary technique is to look at an XML file that is the same name as the directory name with
    a matching/appropriate top-level xml element
    """
    directory = str(directory) # allow pathlib arg
    # print("GETDIRINFO:"+directory+":"+os.getcwd(),file=sys.stderr)
    # print("ENV:"+repr(os.environ.get("OCPI_XML_INCLUDE_PATH")), file=sys.stderr)
    models = ["hdl", "rcc", "ocl"] # should be static elsewhere
    in_lib  = models + [ "test", "comp" ]
    directory = directory.rstrip('/')
    base = os.path.basename(directory)
    # avoid absolutizing if it is not necessary since it is expensive
    if base in ['', '.', '..']:
        directory = os.path.realpath(directory)
        base = os.path.basename(directory)
    if not os.path.isdir(directory):
        print("Warning:  no directory type when requesting it for a non-directory:  " + directory,
              file=sys.stderr)
        return None # be relaxed about non-dirs so callers can use them from "make"
    parts = base.split('.') # perhaps there is an authoring model suffix
    name = parts[0]
    make_type = None
    asset_type = None # will be set to make_type if not set
    top_xml_elements = None
    xml_name = directory + "/" + name
    xml_file = xml_name + ".xml"
    has_project_file = (os.path.isfile(directory + "/Project.mk") or
                        os.path.isfile(directory + "/Project.xml"))
    if has_project_file or os.path.isfile(directory + "/project-package-id"):
        # Do we need to check for project-package-id file in exports?
        make_type = asset_type = "project"
        xml_name = directory + "/Project" if has_project_file else None
    elif len(parts) > 1:
        if parts[-1] == "test":
            xml_name += "-test"
            make_type = asset_type = "test"
        elif parts[-1] == "comp":
            xml_name += "-spec"
            make_type = asset_type = "component"
        elif parts[-1] in [ "hdl", "rcc", "ocl" ]:
            make_type = "worker"
            asset_type = parts[-1] + '-worker'
            xml_path = Path(xml_file)
            if not xml_path.exists():
                xml_path = xml_path.parent.joinpath(name + '-' + parts[-1] + '.xml')
            if parts[-1] == "hdl":
                xml = xml_path.read_text().lower()
                for tag in ['device', 'implementation']:
                    if re.search(f'< *hdl{tag}[^a-z_]', xml):
                        asset_type = 'hdl-device'
                        break
    elif name == "components":
        # ambiguous: if there are worker dirs
        make_type = asset_type = get_maketype(directory);
        if make_type:
            pass # library or libraries
        elif os.path.exists(xml_file):
            make_type = asset_type = xt.parse(xml_file).getroot().tag.lower()
        else: # no Makefile, no xml file
            make_type = 'libraries'
            # does not work with python3 < 3.6.0
            # with os.scandir(directory) as it:
            # it = os.scandir(directory)
            for entry in os.scandir(directory):
                if entry.is_dir():
                    dparts = entry.name.split('.')
                    if entry.name == "specs" or (len(dparts) > 1 and dparts[-1] in in_lib):
                        make_type = asset_type = 'library'
                        break
    elif name in ["platforms", "primitives", "cards", "devices", "adapters", "assemblies" ]:
        # plurals that are usually make types but not actual assets
        if directory.startswith(name): # incur absolutizing penalty
            directory = os.path.realpath(directory)
        parent = os.path.basename(os.path.dirname(directory))
        if parent == "rcc" and name == "platforms":
            make_type = parent + '-platforms'
        elif parent in ["hdl"]: # someday models, at least for primitives (e.g. rcc primitives)
            if name in ["cards", "devices", "adapters"]:
                make_type = asset_type = "library"
            else:
                make_type = "hdl-" + name
        elif name == "devices" and get_dirtype(os.path.dirname(directory)) == "hdl-platform":
            make_type = asset_type = "library"
        elif name == "assemblies" and parent == "gen":
            make_type = "hdl-assemblies"
    elif name == "applications":
        # what is left: specs (not a thing), cards, devices, adapters
        make_type = "applications"
    elif name == "assemblies":
        # what is left: specs (not a thing), cards, devices, adapters
        make_type = "hdl-assemblies"
    elif name == "specs":
        make_type = None
        asset_type = "specs"
        xml_name = None
    elif os.path.isfile(xml_name + "-app.xml"):
        make_type = asset_type = "application"
        xml_name += "-app"
    elif os.path.isfile(xml_file):
        # a platform, an assembly, a library, a primitive
        tag = xt.parse(xml_file).getroot().tag.lower()
        if tag.startswith("hdl"):
            make_type = asset_type = "hdl-" + tag[3:]
        elif tag == "library":
            make_type = asset_type = "library"
        elif tag == "application":
            make_type = asset_type = "application"
    else: # could be library or platform or assembly or application
        if directory.startswith(name): # incur absolutizing penalty
            directory = os.path.realpath(directory)
        parent_path = Path(directory).parent
        parent = parent_path.name
        if parent == "components":
            if os.path.isfile(directory + "/Library.xml") or get_maketype(directory) == "library":
                make_type = asset_type = "library"
        elif parent == "assemblies":
            make_type = asset_type = "hdl-assembly"
        elif parent == "platforms":
            model = parent_path.parent.name
            make_type = asset_type = model + "-platform"
        elif parent == "applications":
            make_type = asset_type = "application"
        elif parent == "primitives":
            mt = get_maketype(directory)
            if mt == "hdl-library" or mt == "hdl-lib":
                make_type = asset_type = "hdl-library"
            elif mt == "hdl-core":
                make_type = asset_type = "hdl-core"
    if careful and make_type:
        match = get_maketype(directory)
        if match and match != make_type:
            raise OCPIException("When determining the directory type of \"" + str(directory) + "\", "\
                                "apparent type is \"" + make_type + "\" but Makefile has \"" + match + "\"")
    r = make_type, asset_type, directory, xml_name + ".xml" if xml_name else None, name
    # if make_type:
    #     print("GETDIRINFOr:"+repr(r),file=sys.stderr)
    return r

def get_dir_info_for_make(directory="."):
    info = list(get_dir_info(directory));
    for i in range(0, len(info)):
        if not info[i]:
            info[i] = ""
    return ":".join(info)

def get_subdirs_of_type(dirtype, directory="."):
    """
    Return a list of directories underneath the given directory
    that have a certain type (library, worker, hdl-assembly...)
    """
    subdir_list = []
    if dirtype:
        for subdir, _, _ in os.walk(directory):
            if get_dirtype(subdir) == dirtype:
                subdir_list.append(subdir)
    return subdir_list

###############################################################################
# Utility function for exporting libraries in a project
###############################################################################
# def export_libraries():
#     """
#     Build the lib directory and links to specs in each library in a project.
#     This will allow specs to be exported before workers in a library are built.
#     """
#     for lib_dir in get_subdirs_of_type("library"):
#         logging.debug("Library found at \"" + lib_dir + "\", running \"make speclinks\" there.")
#         proc = subprocess.Popen(["make", "-C", lib_dir, "speclinks"],
#                                 stdout=subprocess.PIPE,
#                                 stderr=subprocess.PIPE)
#         my_out = proc.communicate()
#         if proc.returncode != 0:
#             logging.warning("Failed to export library at " + lib_dir + " because of error : \n" +
#                             str(my_out[1]))

###############################################################################
# Utility functions for determining paths to/from the top level of a project
# or a project's imports directory.
###############################################################################

def is_path_in_project(origin_path=".",):
    """
    Determine whether a path is inside a project
    """
    try:
        dir_path = Path(origin_path).resolve()
        while dir_path.name != '':
            for file in ['Project.xml', 'Project.mk', 'project-package-id']:
                if dir_path.joinpath(file).exists():
                    return dir_path
            dir_path = dir_path.parent
    except:
        pass
    return None

# Get the path to the project containing 'origin_path'
# relative_mode : default=False
# If relative_mode is False,
#     an absolute path to the containing project is returned
# If relative_mode is True,
#     a relative path from origin_path is returned
# accum_path is an internal argument that accumulates the path to
#    return across recursive calls
def __get_path_to_project_top(origin_path, relative_mode, accum_path):
    if origin_path and os.path.exists(origin_path):
        abs_path = os.path.abspath(origin_path)
        if get_dirtype(origin_path) == "project":
            return abs_path if relative_mode is False else accum_path
        elif abs_path != "/":
            return __get_path_to_project_top(os.path.dirname(abs_path),
                                             relative_mode, accum_path + "/..")
    return None
def get_path_to_project_top(origin_path=".", relative_mode=False):
    """
    Get the path to the top of the project containing 'origin_path'.
    Optionally enable relative_mode for relative paths.
    Note: call aux function to set accum_path internal arg
    """
    path_to_top = __get_path_to_project_top(origin_path, relative_mode, ".")
    if path_to_top is None:
        if origin_path is None:
            logging.debug("Cannot get path to project for origin_path=None.")
        else:
            logging.debug("Path \"" + os.path.realpath(origin_path) + "\" is not in a project")
    return path_to_top

# Go to the project top and check if the project-package-id file is present.
def is_path_in_exported_project(origin_path):
    """
    Given a path, determine whether it is inside an exported project.
    """
    project_top = get_path_to_project_top(origin_path)
    if project_top is not None:
        if os.path.isfile(project_top + "/project-package-id"):
            logging.debug("Path \"" + os.path.realpath(origin_path) +
                          "\" is in an exported project.")
            return True
    return False


# Get the path from 'to_path's project top to 'to_path'.
# accum_path is an internal argument that accumulates the path to
#    return across recursive calls
def __get_path_from_project_top(to_path, accum_path):
    if os.path.exists(to_path):
        abs_path = os.path.abspath(to_path)
        if get_dirtype(to_path) == "project":
            return accum_path
        elif abs_path != "/":
            appended_accum = os.path.basename(abs_path)
            if accum_path != "":
                appended_accum = appended_accum + "/" + accum_path
            return __get_path_from_project_top(os.path.dirname(abs_path), appended_accum)
    return None
def get_path_from_project_top(to_path="."):
    """
    Get the path to a location from the top of the project containing it.
    The returned path STARTS AT THE PROJECT TOP and therefore does not include
    the path TO the project top.
    Note: call aux function to set accum_path internal arg
    """
    path_from_top = __get_path_from_project_top(to_path, "")
    if path_from_top is None:
        if to_path is None:
            logging.debug("Cannot get path from project for to_path=None.")
        else:
            logging.debug("Path \"" + os.path.realpath(to_path) + "\" is not in a project")
    return path_from_top

def get_project_imports(origin_path="."):
    """
    Get the contents of a project's imports directory.
    The current project is determined based on 'origin_path'
    """
    project_top = get_path_to_project_top(origin_path, False)
    return os.listdir(project_top + "/imports") if project_top is not None else None

# NOTE: This function is not thoroughly tested
def get_path_from_given_project_top(origin_top, dest_path, path_to_origin_top=""):
    """
    Determine the path from the top level of a project (origin_top) to the
    destination path (dest_path). Whenever possible, try to stay internal to
    the project or go through the project's imports directory. If that is not
    possible, return destination path as handed to this function.

    Optionally, a path TO the origin-path's top directory can be provided
    and prepended to the return value whenever possible (when the function
    determined a path inside the project or its imports.
    """
    dest_top = get_path_to_project_top(dest_path, False)
    if dest_top:
        path_from_dest_top = get_path_from_project_top(dest_path)
        prepend_path = path_to_origin_top + "/" if path_to_origin_top != "" else ""
        if os.path.samefile(origin_top, dest_top):
            return prepend_path + path_from_dest_top
        else:
            to_import = "imports/" + os.path.basename(dest_top)
            if os.path.isdir(origin_top + "/" + to_import):
                return prepend_path + to_import + "/" + path_from_dest_top
    return dest_path

# NOTE: This function is not thoroughly tested
def get_paths_from_project_top(origin_path, dest_paths):
    """
    Given an origin and a list of destination paths, return a list of paths
    from origin's project top to each destination (potentially through imports).
    If a destination path is not in the current or an imported project,
    return an absolute path.
    """
    origin_top = get_path_to_project_top(origin_path, False)
    if origin_top is None:
        # pylint:disable=undefined-variable
        raise OCPIException("origin_path \"" + str(origin_path) + "\" is not in a project")
        # pylint:enable=undefined-variable
    paths_from_top = []
    for dest_p in dest_paths:
        paths_from_top.append(get_path_from_given_project_top(origin_top, dest_p))
    return paths_from_top

# NOTE: This function does is not thoroughly tested
def get_paths_through_project_top(origin_path, dest_paths):
    """
    origin to each destination going through the project top (and potentially
    imports) when possible.
    """
    origin_top = get_path_to_project_top(origin_path, False)
    origin_top_rel = get_path_to_project_top(origin_path, True)
    if origin_top is None:
        # pylint:disable=undefined-variable
        raise OCPIException("origin_path \"" + str(origin_path) + "\" is not in a project")
        # pylint:enable=undefined-variable
    paths_through_top = []
    for dest_p in dest_paths:
        paths_through_top.append(
            get_path_from_given_project_top(origin_top, dest_p, origin_top_rel))
    return paths_through_top

###############################################################################
# Functions for determining project package information
###############################################################################
def get_project_package(origin_path="."):
    """
    Get the Package Name of the project containing 'origin_path'.
    """
    path_to_project = get_path_to_project_top(origin_path)
    if path_to_project is None:
        logging.debug("Path \"" + str(origin_path) + "\" is not inside a project")
        return None

    # From the project top, probe the Makefile for the projectpackage
    # which is printed in cdk/include/project.mk in the projectpackage rule
    # if ShellProjectVars is defined
    with cd(path_to_project):
        project_package = None
        # If the project-package-id file exists, set package-id to its contents
        if os.path.isfile(path_to_project + "/project-package-id"):
            with open(path_to_project + "/project-package-id", "r") as package_id_file:
                project_package = package_id_file.read().strip()
                logging.debug("Read Project-ID '" + project_package + "' from file: " +
                              path_to_project + "/project-package-id")

        # Otherwise, ask Makefile at the project top for the ProjectPackage
        if project_package is None or project_package == "":
            project_vars = set_vars_from_make("Makefile" if os.path.exists("Makefile") else
                                              os.environ["OCPI_CDK_DIR"] + "/include/project.mk",
                                              "projectpackage ShellProjectVars=1", "verbose")
            if (not project_vars is None and 'ProjectPackage' in project_vars and
                    len(project_vars['ProjectPackage']) > 0):
                # There is only one value associated with ProjectPackage, so get element 0
                project_package = project_vars['ProjectPackage'][0]
            else:
                logging.error("Could not determine Package-ID of project.")
                return None
    return project_package

def does_project_with_package_exist(origin_path=".", package=None, return_project_dir=False):
    """
    Determine if a project with the given package exists and is registered. If origin_path is not
    specified, assume we are interested in the current project. If no package is given, determine
    the current project's package.
    """
    project_registry_dir_exists, project_registry_dir = get_project_registry_dir()
    if not project_registry_dir_exists:
        logging.debug("Registry does not exist, so project with any package cannot be found.")
        return False
    if package is None:
        package = get_project_package(origin_path)
        if package is None:
            logging.debug("No package was provided to the does_project_with_package_exist " +
                          "function, and the path provided does not have a package.")
            return False
    for project in glob(project_registry_dir + "/*"):
        if get_project_package(project) == package or os.path.basename(project) == package:
            if return_project_dir:
                return project
            return True
    return False

def is_path_in_registry(origin_path="."):
    """
    Is the path provided one of the projects in the registry?
    """
    project_registry_dir_exists, project_registry_dir = get_project_registry_dir()
    if not project_registry_dir_exists:
        # If registry does not exist, origin path cannot be a project in it
        return False
    origin_realpath = os.path.realpath(origin_path)
    # For each project in the registry, check equivalence to origin_path
    for project in glob(project_registry_dir + "/*"):
        if origin_realpath == os.path.realpath(project):
            # A project was found that matches origin path!
            return True
    # No matching project found. Project/path is not in registry
    return False

###############################################################################
# Functions for and accessing/modifying the project registry and collecting
# existing projects
###############################################################################

# Could not think of better/shorted function name, so we disable the pylint checker
# that was erroring due to name length
# pylint:disable=invalid-name
def get_default_project_registry_dir():
    """
    Get the default registry from the environment setup. Check in the following order:
    OCPI_PROJECT_REGISTRY_DIR, OCPI_ROOT_DIR/project-registry or /opt/opencpi/project-registry
    """
    project_registry_dir = os.environ.get('OCPI_PROJECT_REGISTRY_DIR')
    if project_registry_dir is None:
        cdkdir = os.environ.get('OCPI_CDK_DIR')
        if cdkdir:
            project_registry_dir = cdkdir + "/../project-registry"
        else:
            project_registry_dir = "/opt/opencpi/project-registry"
    return project_registry_dir
# pylint:enable=invalid-name

def get_project_registry_dir(directory="."):
    """
    Determine the project registry directory. If in a project, check for the imports link.
    Otherwise, get the default registry from the environment setup:
        OCPI_PROJECT_REGISTRY_DIR, OCPI_ROOT_DIR/project-registry or /opt/opencpi/project-registry

    Determine whether the resulting path exists.

    Return the exists boolean and the path to the project registry directory.
    """
    if (is_path_in_project(directory) and
            os.path.isdir(get_path_to_project_top(directory) + "/imports")):
        # allow imports to be a link OR a directory (needed for deep copies of exported projects)
        project_registry_dir = os.path.realpath(get_path_to_project_top(directory) + "/imports")
    else:
        project_registry_dir = get_default_project_registry_dir()

    exists = os.path.exists(project_registry_dir)
    if not exists:
        logging.warning("The project registry directory '" + project_registry_dir +
                        "' does not exist.\nCorrect " + "'OCPI_PROJECT_REGISTRY_DIR' or run: " +
                        "'ocpidev create registry " + project_registry_dir + "'")
    elif not os.path.isdir(project_registry_dir):
        raise OSError("The current project registry '" + project_registry_dir +
                      "' exists but is not a directory.\nCorrect " +
                      "'OCPI_PROJECT_REGISTRY_DIR'")
    return exists, project_registry_dir

def get_all_projects():
    """
    Iterate through the project path and project registry.
    If the registry does not exist, manually locate the CDK.
    Return the list of all projects.
    """
    projects = []
    project_path = os.environ.get('OCPI_PROJECT_PATH')
    if project_path:
        projects += project_path.split(':')
    exists, project_registry_dir = get_project_registry_dir()
    if exists:
        projects += glob(project_registry_dir + '/*')
    else:
        cdkdir = os.environ.get('OCPI_CDK_DIR')
        if cdkdir:
            projects.append(cdkdir)
    logging.debug("All projects: " + str(projects))
    return projects

###############################################################################
# Utility functions for use by ocpidev code close to the CLI
###############################################################################

def throw_not_valid_dirtype_e(valid_loc):
    """
    throws an exception and forms a error message if not in a valid directory
    """
    raise OCPIException("The directory of type " + str(get_dirtype()) + " is not a " +
                        "valid directory type to run this command in. Valid directory types are: " +
                        ' '.join(valid_loc))

def check_no_libs(dir_type, library, hdl_library, hdl_platform):
    if library: throw_not_blank_e(dir_type, "--library option", False)
    if hdl_library: throw_not_blank_e(dir_type, "--hdl-library option", False)
    if hdl_platform: throw_not_blank_e(dir_type, "-P option", False)

def throw_not_blank_e(noun, var, always):
    """
    throws an exception and forms a error message if a variable is blank and shouldn't be or
    if a variable is not bank ans should be blank
    """
    always_dict = {True: "not", False : "always"}
    raise OCPIException(var + " should " +  always_dict[always] + " be blank for " + noun +
                        " operations.  Command is invalid.")

def throw_invalid_libs_e():
    """
    throws an exception and forms a error message if too many library locations are specified
    """
    raise OCPIException("only one of hdl_libary, library, and hdl_platform can be used.  Invalid " +
                        "Command, Choose only one.")

def throw_specify_lib_e():
    """
    throws an exception and forms a error message if no library is specified
    """
    raise OCPIException("No library specified, Invalid Command.")

def get_component_filename(library, name):
    """
    >>> open("/tmp/my_file-spec.xml",'w').close()
    >>> get_component_filename("/tmp", "my_file-spec.xml")
    '/tmp/my_file-spec.xml'
    >>> get_component_filename("/tmp", "my_file-spec")
    '/tmp/my_file-spec.xml'
    >>> get_component_filename("/tmp", "my_file")
    '/tmp/my_file-spec.xml'
    >>> os.remove("/tmp/my_file-spec.xml")
    >>> open("/tmp/my_file_spec.xml",'w').close()
    >>> get_component_filename("/tmp", "my_file")
    '/tmp/my_file_spec.xml'
    >>> os.remove("/tmp/my_file_spec.xml")
    """
    basename = library + "/" + name
    end_list = ["", ".xml", "_spec.xml", "-spec.xml"]
    for ending in end_list:
        if os.path.exists(basename + ending):
            return basename + ending
    return basename

def get_package_id_from_vars(package_id, package_prefix, package_name, name):
    """
    >>> get_package_id_from_vars("package_id", "package_prefix", "package_name", None)
    'package_id'
    >>> get_package_id_from_vars(None, "package_prefix", "package_name",None)
    'package_prefix.package_name'
    >>> get_package_id_from_vars(None, None, "package_name",None)
    'local.package_name'
    >>> get_package_id_from_vars(None, None, None, "etc")
    'local.etc'
    """
    if package_id:
        return package_id
    if package_prefix:
        package_prefix = package_prefix.rstrip('.')
    else:
        package_prefix = "local"
    if not package_name:
        package_name = name
    return package_prefix + "." + package_name


def get_env_dir(env):
    """
    Gets the given environment variable and verifies that it has
    been set correctly to a path
    """
    err_msg = None
    if env not in os.environ:
        err_msg = env + ' environment setting not found'
    path = Path(os.environ[env])
    if not path.is_dir():
        err_msg = env + ' environment setting invalid'
    if err_msg:
        raise OCPIException(err_msg)
    return str(path)

def get_cdk_dir():
    """
    Gets the OCPI_CDK_DIR environment variable and verifies that it has
    been set correctly.
    """
    return get_env_dir('OCPI_CDK_DIR')

def get_root_dir():
    """
    Gets the OCPI_ROOT_DIR environment variable and verifies that it has
    been set correctly.
    """
    return get_env_dir('OCPI_ROOT_DIR')

def get_project_package_id(realpath, dict):
    """
    Returns the full package id based on variables or attributes
    """
    package_id = dict.get('package_id')
    if not package_id:
        package_id = dict.get('package')
    if package_id:
        return package_id
    package_name = dict.get('packagename')
    if not package_name:
        package_name = os.path.basename(realpath)
    return get_package_id_from_vars(package_id, dict.get('packageprefix'), dict.get('packagename'),
                                    os.path.basename(realpath))

def get_project_attributes(directory, xml_file = None, mk_file = None):
    """
    Return a dictionary of a project's attributes
    """
    directory = str(directory) # Allow path args
    if not xml_file and not mk_file:
        xml_file = directory + "/Project.xml"
        if not os.path.exists(xml_file):
            xml_file = None
            mk_file = directory + "/Project.mk"
            if not os.path.exists(mk_file):
                mk_file = None
    attrs={}
    if xml_file:
        root = xt.parse(xml_file).getroot()
        assert root.tag.lower() == "project"
        for key,value in root.attrib.items():
            attrs[key.lower()] = value
    elif mk_file:
        with open(mk_file) as mk:
            prog = re.compile('^\s*(\w+):?=\s*([^#\n]*).*$', re.ASCII)
            for line in mk:
                match = prog.match(line)
                if match:
                    attrs[match.group(1).lower()] = match.group(2)
    else:
        raise OCPIException('The project in directory "' + directory +
                            '" has no Project.xml (or old Project.mk) file')
    return attrs

hdl_builtins=None
hdl_families={} # map from family to dict for family
hdl_parts={} # map from part to family
hdl_vendors={}
hdl_tools={}
hdl_fake_platforms={} # for test purposes only since it violates dropin
def get_hdl_builtins():
  """
  Return an XML root for the builtin HDL targets database
   """
  global hdl_builtins
  if not hdl_builtins:
      builtins = xt.parse(get_cdk_dir() + "/include/hdl/hdl-targets.xml").getroot()
      # Some families are not used by any platform so we get them here
      for e in builtins.iter('family'):
          family = e.get('name')
          family_dict={}
          parts_list = e.get('parts')
          family_dict['parts'] = \
              dict(map(lambda x:(x,None),parts_list.split())) if parts_list else dict()
          toolset = e.get('toolset')
          if toolset:
              family_dict['toolset'] = toolset
          default_part = e.get('default')
          if default_part:
              family_dict['default'] = default_part
          hdl_families[family] = family_dict
          if parts_list:
              for part in parts_list.split():
                  hdl_parts[part] = family
          else:
              hdl_parts[family] = family
      for v in builtins.iter('vendor'):
          families=[]
          vendor = v.get('name')
          for f in v.iter('family'):
              family = f.get('name')
              families.append(family)
              hdl_families[family]['vendor'] = vendor
          hdl_vendors[vendor] = families
      for t in builtins.iter('toolset'):
          hdl_tools[t.get('name')] = { 'simulator': t.get('simulator') == 'true',
                                       'tool' : t.get('tool') }
      for p in builtins.iter('platform'):
          hdl_fake_platforms[p.get('name')] = p.attrib
      hdl_builtins=hdl_vendors,hdl_families,hdl_tools,hdl_parts
  return hdl_builtins

def get_platform_attributes(project_package_id, directory, name, model):
    """
    Return a dictionary of a platforms's attributes
    Prefer a "lib" (exported) subdirectory of the platform's directory if present
    The directory argument may be the xml exports directory
    """
    get_hdl_builtins()
    attrs={}
    if model == "hdl":
        xml_file = directory + "/hdl/" + name + ".xml" # try for a built or declared file
        if not os.path.exists(xml_file):
            xml_file = directory + "/" + name + ".xml" # try the source file
        try:
            root = xt.parse(xml_file).getroot()
            assert root.tag.lower() == "hdlplatform"
        except:
            print("Error parsing XML file:  " + xml_file, file=sys.stderr)
            return None
        for key,value in root.attrib.items():
            attrs[key.lower()] = value
            attrs["rccplatforms"] = ""
        part = attrs.get('part')
        # Backward compatibility:  if there is no part attribute look in <plat>.mk
        if not part:
            prog = re.compile('^\s*(\w+):?=\s*([^#\n]*).*$', re.ASCII)
            for mkfile in [directory + "/" + name + ".mk", directory + "/hdl/" + name + ".mk"]:
                if os.path.exists(mkfile):
                    with open(mkfile) as mk:
                        for line in mk:
                            match = prog.match(line)
                            if match:
                                if match.group(1) == "HdlPart_" + name:
                                    part = attrs["part"] = match.group(2)
                                elif match.group(1) == "HdlRccPlatforms_" + name:
                                    attrs["rccplatforms"] = match.group(2).split()
                    break
            mkfile = directory + "/" + "Makefile"
            if os.path.exists(mkfile):
                with open(mkfile) as mk:
                    for line in mk:
                        match = prog.match(line)
                        if match:
                            if match.group(1) == "Configurations":
                                attrs['configurations'] = match.group(2).split()
        if attrs.get('configurations') == None: # not empty string is ok
            attrs['configurations'] = ['base']
        if not part:
            print("Error: no part variable or attribute when parsing platform:  ", name, file=sys.stderr)
            return None
        family = attrs.get('family')
        if not family:
            family = hdl_parts.get(part.split('-')[0])
            if not family:
                family = name;
            attrs['family'] = family
        vendor = attrs.get('vendor')
        if not vendor:
            for vendor,families in hdl_vendors.items():
                if family in families:
                    attrs['vendor'] = vendor
                    break
        toolset = attrs.get('toolset')
        if not toolset:
            toolset = hdl_families[family]['toolset']
            attrs['toolset'] = toolset
            attrs['tool'] = hdl_tools[toolset]['tool']
        # attrs['target'] = family
        # Update global database from this platform
        family_dict = hdl_families.get(family)
        if not family_dict:
            family_dict = {}
            family_dict['parts'] = set()
            hdl_families[family] = family_dict
        family_dict['parts'][part.split('-')[0]] = None

        if directory.endswith("/xml"):
            directory = os.path.normpath(directory + "/../" + name) # may not exist
        attrs['built'] = (os.path.isdir(directory + "/hdl/" + family) or
                          os.path.isdir(directory + "/lib/hdl/" + family))
        attrs['target'] = attrs['family'] # "target" is generic, family is an HDL thing
    elif model == "rcc":
        file = directory + "/" + name + ".mk"
        try:
            with open(file) as mk:
                prog = re.compile('^\s*(\w+):?=\s*([^#\n]*).*$', re.ASCII)
                for line in mk:
                    match = prog.match(line)
                    if match:
                        var = match.group(1).lower()
                        if var.startswith("ocpiplatform"):
                            var = var[len("ocpiplatform"):]
                            if var in [ 'os', 'osversion', 'arch']:
                                attrs[var] = match.group(2)
            attrs['target'] = attrs['os'] + '-' + attrs['osversion'] + '-' + attrs['arch']
            attrs['built'] = os.path.isdir(os.environ["OCPI_CDK_DIR"] + '/' + name)
        except:
            print("Failed to process RCC file: " + file, file=sys.stderr)
            return None
        if len(attrs) == 0:
            print("No attributes found in RCC file: " + file, file=sys.stderr)
            return None
    else:
        print("Invalid model: " + model, file=sys.stderr)
        return None
    attrs['model'] = model
    attrs['directory'] = directory
    attrs['package_id'] = project_package_id + "." + name
    return attrs


def find_all_projects(directory=None, project_package_id=None):
    """Find all projects (packageids and realpaths).
    
    Returns an ORDERED dict of package-id->realpath.
    This function does not navigate into the exports subdir of a project
    Optional argument is simply a directory that we think might be *in* 
    a project and thus should be used to find the registry.
    If the package_id argument is supplied it means we know the 
    directory is a project and we know its package_id/
    OCPI_PROJECT_PATH is also used as a source of projects.
    The ordered dict returned is suitable for project searching: 
        *this* project, projectpath, registry
    Note a small amount of extra effort is done to always have the 
    package_id even though in some contexts it is not needed.
    Minimize file system touches
    """
    xml_file = None
    mk_file = None
    project_dir = os.getenv('OCPI_PROJECT_DIR')
    if project_package_id:
        project_dir = directory
    elif directory:
        while not project_dir:
            # We just test for existence (as opposed to opening file)
            # Since if it is registered we won't need it, and it 
            # probably is registered
            xml_file = str(Path(directory, "Project.xml"))
            mk_file = str(Path(directory, "Project.mk"))
            if Path(xml_file).exists():
                project_dir = directory
                mk_file = None
            elif Path(mk_file).exists():
                project_dir = directory
                xml_file = None
            else:
                parent = Path(directory).resolve().parent
                if parent.samefile(directory): # root
                    break
                directory = str(parent)
    if project_dir and Path(project_dir, "imports").is_dir():
        registry_dir = str(Path(project_dir, "imports"))
    else:
        # either no OCPI_PROJECT_DIR, directory arg not in a project,
        # or project_dir has no imports
        registry_dir = os.getenv('OCPI_PROJECT_REGISTRY_DIR')
        if not registry_dir:
            registry_dir = str(Path(get_root_dir(), "project-registry"))
    projects = collections.OrderedDict()
    # check for the directory we are in, that might *not* be registered
    if project_dir: # from environment or from cwd: add it if not there
        realpath = Path(project_dir).resolve()
        if project_package_id:
            projects[project_package_id] = str(realpath)
        else:
        # no project ID handy, so use realpath
            if realpath not in projects.values():
                attrs = get_project_attributes(realpath, xml_file, mk_file)
                project_package_id = get_project_package_id(realpath, attrs)
                projects[project_package_id] = str(realpath)
    dirs = [dir for dir in os.getenv('OCPI_PROJECT_PATH', '').split(':') if dir]
    for dir in dirs:
        realpath = str(Path(dir).resolve())
        if realpath not in projects.values():
            attrs = get_project_attributes(realpath)
            pid = get_project_package_id(realpath, attrs)
            projects[pid] = str(realpath)
    # Now process the registry
    if not Path(registry_dir).is_dir():
        raise OCPIException(f'The specified project registry directory "{registry_dir}" is '+
                            f'not a directory.')
    for path in Path(registry_dir).iterdir():
        if path.is_symlink() and path.exists():
            if not projects.get(path.name):
                projects[path.name] = str(Path(registry_dir, path.name))
        else:
            print(f'Warning: the registry at "{registry_dir}" contains an invalid file/link: '+
                  f'"{path.name}"', file=sys.stderr)
            continue
    return projects


def get_platforms():
    """
    Find platforms in this environment, based on find_all_projects.
    return a dictionary of all platforms, with the key being its name, and the
    value being its attributes including model and packageid
    """
    if get_platforms.dict:
        return get_platforms.dict
    get_hdl_builtins()
    if len(hdl_fake_platforms) > 0:
        return hdl_fake_platforms
    get_platforms.dict={}
    dir = os.getenv("OCPI_PROJECT_DIR")
    if dir:
        package_id = os.getenv('OCPI_PROJECT_PACKAGE')
    else:
        dir = os.getcwd()
        package_id = None
    for package_id, realpath in find_all_projects(dir, package_id).items():
        for model in [ 'rcc', 'hdl' ]:
            for dir in [ realpath + "/exports/" + model + "/platforms",
                         realpath + "/" + model + "/platforms"]:
                if os.path.exists(dir):
                    platforms_dir = dir + "/xml"
                    if os.path.isdir(platforms_dir):
                        # Use <platforms>/xml/*.{xml,mk}
                        with os.scandir(platforms_dir) as it:
                            for entry in it:
                                if fnmatch.fnmatch(entry.name, '*.xml'):
                                    name = entry.name[0:-4]
                                    if get_platforms.dict.get(name):
                                        continue # already defined earlier
                                    attrs = get_platform_attributes(package_id, platforms_dir, name,
                                                                    model)
                                    if attrs:
                                        get_platforms.dict[name] = attrs
                    else:
                        with os.scandir(dir) as it:
                            for entry in it:
                                if entry.name == 'lib' or get_platforms.dict.get(entry.name):
                                    continue # already defined earlier
                                if entry.is_dir():
                                    platform_dir = dir + "/" + entry.name
                                    if ('/exports/' not in dir and os.path.isdir(platform_dir + "/lib") and
                                        os.path.exists(platform_dir + "/lib/" + entry.name + ".xml")):
                                        platform_dir += "/lib"
                                    attrs = get_platform_attributes(package_id, platform_dir, entry.name, model)
                                    if attrs:
                                        get_platforms.dict[entry.name] = attrs
    return get_platforms.dict
get_platforms.dict=None

# Exceptions to the simply mapping of attributes to variables (capitalized)
# And empty string means do not include them in the output for make
makeVariables={ "directory": "PlatformDir",
                "osversion" : "",
                "package_id" : "PlatformPackageID",
                "rccplatforms" : "AllRccPlatforms",
                "part" : "Part",
                "family":"Target",
                "model":"", "spec":"", "libraries":"","language":"", "version":"",
                "configurations":""}

def get_platform_variables(shell, only_model=None):
    """
    Output on standard output the information about platforms in the format and variable names
    that the current make code wants.
    """
    model_platforms={}
    quote='"' if shell else ''
    end=quote + ('\n')
    blist={}
    rcctlist=[]
    out=""
    for name, dict in get_platforms().items():
        model = dict['model']
        if only_model and model != only_model:
            continue
        if not blist.get(model):
            blist[model]=[]
        if not model_platforms.get(model):
            model_platforms[model] = [ name ]
        else:
            model_platforms[model].append(name)
        for attribute, value in dict.items():
            var = makeVariables.get(attribute)
            if var and var != "":
                out+=(model.capitalize() + 
                      (var if var else "Platform" + attribute.capitalize()) + "_" + name + "=" +
                      quote + value + end)
            if attribute == 'built' and value:
                blist[model].append(name)
        if model == 'rcc':
            target = dict['target']
            out+=("RccTarget_" + name + "=" + quote + target + end)
            rcctlist.append(target)
    for model, platforms in model_platforms.items():
        platforms.sort()
        blist[model].sort()
        out+=(model.capitalize() + "AllPlatforms=" + quote + ' '.join(platforms) + end)
        out+=(model.capitalize() + "BuiltPlatforms=" + quote + ' '.join(blist[model]) + end)
    if not only_model or only_model == 'rcc':
        rcctlist.sort()
        out+=("RccAllTargets=" + quote + ' '.join(rcctlist) + end)
    if not only_model or only_model == 'hdl':
        families=set(hdl_families.keys())
        flist=list(families)
        flist.sort()
        out+=("HdlAllFamilies=" + quote + ' '.join(flist) + end)
        families |= hdl_vendors.keys()
        flist=list(families)
        flist.sort()
        out+=("HdlAllTargets=" + quote + ' '.join(flist) + end)
        simlist=[]
        for key,value in hdl_tools.items():
            if value.get('simulator'):
                simlist.append(key)
            out+=("HdlToolName_" + key + "=" + quote + value.get('tool') + end)
        simlist.sort()
        out+=("HdlSimTools=" + quote + ' '.join(simlist) + end)
        for key,value in hdl_families.items():
            parts=value.get('parts')
            if parts:
                parts=list(parts.keys())
                parts.sort()
                out+=("HdlTargets_" + key + "=" + quote + ' '.join(parts) + end)
            out+=("HdlToolSet_" + key + "=" + quote + value.get('toolset') + end)
            default_part = value.get('default')
            if default_part:
                out+=("HdlDefaultTarget_" + key + "=" + quote + default_part + end)
        for key,value in hdl_vendors.items():
            value.sort()
            out+=("HdlTargets_" + key + "=" + quote + ' '.join(value) + end)
        out+=("HdlTopTargets=" + quote + ' '.join(hdl_vendors.keys()) + end)
    return out.strip()

def get_platform_make_dictionary():
   """
   Return a dictionary of make  variable settings compatible withe set_vars_from_make
   """
   if not get_platform_make_dictionary.dict:
       get_platform_make_dictionary.dict={}
       for assignment in get_platform_variables(False).strip().split('\n'):
           var,value = assignment.split('=')
           get_platform_make_dictionary.dict[var] = value.split(' ')
   return get_platform_make_dictionary.dict
get_platform_make_dictionary.dict=None

# Note this was moved from tools/ocpidev/assets/component.py
# It is assumed to be called in a project context, which means if it is not
# at the project level, higher level attributes are in the environment, which will be
# used by ocpigen
# Note also that the directory is "resolved" to make sure that it is under a project
# at the correct level regardless of any permament or temporary symlinks
# (like when sphinx has to find worker dirs UNDERNEATH comp dirs and so symlinks are used)
def get_xml_string(directory='.'):
    """
    Ask ocpigen (the code generator) to parse the worker(OWD) or component(OCS) xml file and
    spit out an artifact xml that this function parses into class variables.
      property_list - list of every property, each property in this list will be a dictionary of
                      all the xml attributes associated with it from the artifact xml
      port_list     - list of every port each port in this list will be a dictionary of
                      all the xml attributes associated with it from the artifact xml some of
                      which are unused
      slave_list    - list of every slave worker's name expected to be blank for an OCS

    Function attributes:
      xml_file - the file to have ocpigen parse
    """
    make_type, asset_type, directory, xml_name,_ = get_dir_info(str(Path(directory).resolve(True)))
    return get_xml_string_from_file(make_type, directory, xml_name)

def get_xml_string_from_file(make_type, directory, xml_file):
    """
    Caller knows where to execute the request, the make type, and the xml file name, which can be None
    The "make" machinery knows how to do the correct search rules.
    """
    directory = str(directory)
    cmd = ["make", "-r", "--no-print-directory", "-C", directory,
           "-f", get_makefile(directory, make_type)[0],
           "XmlFile="+(str(xml_file) if xml_file else ''), "xml" ]
    logging.info("running command: " + str(cmd))
    old_log_level = os.environ.get("OCPI_LOG_LEVEL", "0")
    os.environ["OCPI_LOG_LEVEL"] = "0"
    env = os.environ
    # Force the recomputation of the project dir and cause "make" to think it is the top level invocation
    env.pop("OCPI_PROJECT_REL_DIR",None)
    env.pop("MAKEFLAGS",None)
    env.pop("MAKELEVEL",None)
    env.pop("MAKEOVERRIDES",None)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, env=env)
    if p.returncode:
        logging.bad("XML parsing failure in directory: " + directory)
        sys.exit(p.returncode)
    xml = p.communicate()[0]
    os.environ["OCPI_LOG_LEVEL"] = old_log_level
    logging.debug("Asset XML from ocpigen: \n" + str(xml))
    return xml.decode()

if __name__ == "__main__":
    import doctest
    import sys
    __LOG_LEVEL = os.environ.get('OCPI_LOG_LEVEL')
    __VERBOSITY = False
    if __LOG_LEVEL:
        try:
            if int(__LOG_LEVEL) >= 8:
                __VERBOSITY = True
        except ValueError:
            pass
    doctest.testmod(verbose=__VERBOSITY, optionflags=doctest.ELLIPSIS)
    sys.exit(doctest.testmod()[0])
