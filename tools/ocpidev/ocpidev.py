#!/usr/bin/env python3
import importlib.util
import logging
import os
from pathlib import Path, PosixPath
import shutil
import subprocess
import sys

import cdk as cdk_dir
import cdk.ubuntu18_04.lib._opencpi as ocpi_module
from cdk.ubuntu18_04.lib._opencpi.util import OCPIException
from cdk.ubuntu18_04.lib._opencpi.assets import factory as asset_factory
from cdk.ubuntu18_04.lib._opencpi.assets import registry as asset_registry

# TODO: Get the expected directories
library = Path("")
lib = Path("")

# TODO: Figure out what to do with these
# Database of models, languages and suffixes, redundant with util.mk
# Models=(rcc hdl ocl)
# Language_rcc=c++
# Languages_rcc=(c:c c++:cc)
# Language_hdl=vhdl
# Languages_hdl=(vhdl:vhd)
# Language_ocl=cl

# TODO: Could combine these two blocks into a single function call
# Get CDK directory path from environment variable
try:
    cdk_dir = Path(os.environ["OCPI_CDK_DIR"])
    platform_dir = Path(os.environ["OCPI_TOOL_PLATFORM"])
except KeyError:
    print("You need to source the OpenCPI CDK directory first.")
    sys.exit(1)

# Verify that the CDK directory exists
try:
    if not cdk_dir:
        raise OSError
except OSError:
    print(f"Error: OCPI_CDK_DIR environment setting not valid: {cdk_dir}")
    sys.exit(1)

subprocess.run(["/bin/bash", "-c", f"source {cdk_dir}/scripts/util.sh"])
check_cdk = f"$(if $(realpath $({cdk_dir}),,$(error The OCPI_CDK_DIR environment variable is not set correctly.))"


# Error messages
def bad(err_mess):
    """Error messages that cause program to exit"""
    sys.stderr.write(f"Error: {err_mess}")
    sys.exit(1)


def warn(warn_mess):
    """Warning messages that don't cause program exit"""
    sys.stderr.write(f"Warning: {warn_mess}")
    return


def no_slash(path_dir):
    """Notify user that slashes aren't allowed in the path"""
    try:
        if not isinstance(path_dir, PosixPath):  # Argument is not a Path object
            raise TypeError
        if path_dir.parent != Path.cwd():
            raise SyntaxError
    except TypeError:
        bad(f"{path_dir} is not a Path object")
    except SyntaxError:
        bad(f"No slashes allowed in {path_dir}; perhaps use the -d option?")


def no_exist(path_dir):
    """Directory argument already exists"""
    try:
        if not isinstance(path_dir, PosixPath):  # Argument is not a Path object
            raise TypeError
        if path_dir.exists:
            raise FileExistsError
    except TypeError:
        bad(f"{path_dir} is not a Path object")
    except FileExistsError:
        bad(f"The file/directory {path_dir} already exists")


def lib_exist(lib_dir):
    """Check if library exists"""
    try:
        if not isinstance(lib_dir, PosixPath):  # Argument is not a Path object
            raise TypeError
        if not lib_dir.exists:  # Is the path present?
            raise OSError
    except TypeError:
        bad(f"{lib_dir} is not a Path object")
    except OSError:
        bad(f"The specified library {lib_dir} does not exist")


# TODO: the arguments will have to be passed in correctly
def check_components(*args):
    """Check that the component's directory is a usable library from the project level"""
    dir_type = ""
    global library
    global lib

    if args[2]:  # check for third value in command-line arguments
        component_dir = Path(args[2])
    else:
        component_dir = "components"

    try:
        if not isinstance(component_dir, PosixPath):  # Argument is not a Path object
            raise TypeError
        if not component_dir.exists:  # Is the path present?
            raise OSError
        else:
            dir_type = get_dirtype(component_dir)
    except TypeError:
        bad(f"{component_dir} is not a Path object")
    except OSError:
        bad(f"The specified library {component_dir} does not exist")

    if dir_type in library or dir_type in lib:
        if component_dir == "":
            bad(f"The directory {component_dir} is empty. There are component libraries under {component_dir} in this"
                f"project, so the {component_dir} library cannot be {args[1]}")
        elif dir_type == "libraries":  # TODO: verify this check
            bad(f"Must specify a library, not {component_dir}, when there are libraries under the {component_dir} "
                f"directory")
        elif dir_type == "*":  # TODO: verify this check
            bad(f"The {component_dir} directory appears to have the wrong type of Makefile {dir_type}")


def need_name(*args):
    """Ensure a name argument is present"""
    if len(args[1]) == 0:
        bad(f"A name argument is required after the command {args[0]}")
    elif args[1] == "*":
        bad(f"You cannot use '*' as a name")


def get_dirtype(*args):
    """Determine the type of Makefile based on directory type.

    If there is no Makefile or no appropriate line in the Makefile, dirtype is an emtpy string.
    """
    dirtype = ""
    makefile_dir = args[1]

    try:
        if not isinstance(makefile_dir, PosixPath):  # Argument is not a Path object
            raise TypeError
        if not makefile_dir.is_dir():  # Requested directory is not actually a directory
            raise NotADirectoryError
        if not makefile_dir:  # Requested directory does not exist
            raise OSError
        else:
            if makefile_dir / "Makefile":
                dirtype = parse_makefile(makefile_dir / "Makefile")
            elif makefile_dir / "project-package-id" and not dirtype:
                dirtype = "project"
    except TypeError:
        bad(f"{makefile_dir} is not a Path object")
    except NotADirectoryError:
        bad(f"{makefile_dir} should be a directory but is not")
    except OSError:
        bad(f"Directory {makefile_dir} should exist and does not")

    return dirtype


def parse_makefile(file):
    """Get the make file type from Makefile.

    Per the original sed command, it should return the last match in the file.
    """
    required = ("include", "$(OCPI_CDK_DIR)", "/include/", ".mk")

    with open(file) as make_file:
        for line in make_file:
            if all(string in line for string in required):  # Identify necessary lines
                line_path = Path(line)  # Convert line to Path type for parsing
                file_name = line_path.stem  # Get just the name of the file
                if "rcc" in file_name:
                    file_type = "rcc"
                elif "hdl" in file_name:
                    file_type = "hdl"
                else:
                    file_type = ""

    return file_type


def check_dirtype(*args):
    """Look in a directory and determine type of Makefile, then set the dirtype"""
    makefile_dir = args[1]
    dirtype = get_dirtype(makefile_dir)
    try:
        if not dirtype:
            raise FileNotFoundError
        if dirtype != args[2]:
            raise TypeError
    except FileNotFoundError:
        bad(f"{makefile_dir / 'Makefile'} is not correctly formatted. No 'include *.mk' lines.")
    except TypeError:
        bad(f"{makefile_dir / 'Makefile'} has an unexpected dirtype {dirtype}; expected {args[2]}")


def get_project_top():
    """Get the path to the top of the project.

    This uses pathlib.Path to build the path to the opencpi/util/project.py file. Then importlib is used to generate
    a module spec from the source file. The spec file then generates a custom Python module, which is loaded with the
    spec file data. Finally, the desired function in the project.py module is called.
    """
    # ocpi_util_path = platform_dir / "lib" / "_opencpi" / "util" / "project.py"
    # util_spec = importlib.util.spec_from_file_location(name="project", location=ocpi_util_path)
    # util_module = importlib.util.module_from_spec(util_spec)
    # util_spec.loader.exec_module(util_module)
    # project_top = util_module.get_path_to_project_top()
    project_top = ocpi_module.util.project.get_path_to_project_top()
    try:
        if not project_top:
            raise OSError
        else:
            return project_top
    except OSError:
        bad(f"Failure to find project containing path {Path.cwd()}")


def get_project_package():
    """Determine the package ID of the current project."""
    # ocpi_asset_path = platform_dir / "lib" / "_opencpi" / "assets" / "project.py"
    # asset_spec = importlib.util.spec_from_file_location("project", ocpi_asset_path)
    # asset_module = importlib.util.module_from_spec(asset_spec)
    # asset_spec.loader.exec_module(asset_module)
    # project_pkg = asset_module.Project(directory=".").package
    project_pkg = ocpi_module.assets.project.Project(directory=".").package_id
    try:
        if not project_pkg:
            raise OSError
        else:
            return project_pkg
    except OSError:
        bad(f"Failure to find project package for path {Path.cwd()}")


def try_return_bool(*args):
    """Test a command argument for success or failure."""
    # ocpi_util_path = platform_dir / "lib" / "_opencpi" / "util"
    # util_spec = importlib.util.spec_from_file_location("util", ocpi_util_path)
    # util_module = importlib.util.module_from_spec(util_spec)
    # util_spec.loader.exec_module(util_module)
    # OCPIException = util_module.OCPIException()
    try:
        if args[1]:
            return sys.exit()
    except OCPIException as e:
        logging.error(e)
        return sys.exit(1)


def register_project(*args):
    """Register project to program"""
    if args[1]:
        project = args[1]
    else:
        project = "."

    if force:  # TODO: What is this compared to the Bash file ($force)
        py_force = True
    else:
        py_force = False

    factory_input = asset_factory.AssetFactory.factory("registry", asset_registry.Registry.get_registry_dir(project)). \
        add(project, force=py_force)
    sys.stderr.write(try_return_bool(factory_input))

    # Export a project on register, but only if it is not an exported project itself
    is_exported = ocpi_module.util.is_path_in_exported_project(project)
    if not is_exported:
        try:
            subprocess.run(["make", "-C", f"{project}", "${verbose:+AT=}", "exports", "1>&2"])
        except OSError:
            print(f"Could not export project {project}. You may not have write permissions on this project."
                  f"Proceeding...")
    else:
        if not verbose:  # TODO: Is this like the '-v' CLI argument?
            sys.stderr.write("Skipped making exports because this is an exported, standalone project")


def unregister_project(*args):
    """De-link a project in the installation registry.

    The project's link should be named based on the project's package name. If a project does not exist as specified
    by args[1], assume args[1] is the package/link name itself.
    """
    if args[1]:
        project = args[1]
    else:
        project = "."

    if os.path.exists(project) or "/" in project:  # Registry instance from project dir and remove project by dir
        sys.stderr.write(try_return_bool(
            asset_factory.AssetFactory.factory("registry", asset_registry.Registry.
                                               get_registry_dir(project)).remove(directory=project)))
    else:  # Registry instance from current dir and remove project by package ID
        sys.stderr.write(try_return_bool(
            asset_factory.AssetFactory.factory("registry", asset_registry.Registry.
                                               get_registry_dir(project)).remove(project)))


def delete_project(*args):
    """Delete project from installation registry."""
    if args[1]:
        project = args[1]
    else:
        project = "."

    if force:
        py_force = True
    else:
        py_force = False

    if os.path.exists(project) and os.path.isdir(project):
        my_proj = asset_factory.AssetFactory.factory("project", project)
        my_proj.delete(py_force)
    else:
        my_reg = asset_factory.AssetFactory.factory("registry", asset_registry.Registry.get_registry_dir("."))
        my_proj = my_reg.get_project(project)
        my_proj.delete(py_force)


def get_subdir():
    """This function sets the subdir variable based on the current directory and whether the library/platform options
    are set.

    This is for use only when creating assets meant to reside inside libraries. This is NOT for use when
    creating platforms, assemblies, primitives, libraries, apps, projects, or primitives.

    This function essentially does nothing except call get_dirtype "." when one of those nouns is being operated on.
    """
    if noun in ("worker", "device", "spec", "component", "protocol", "properties", "signals", "test", "card", "slot"):
        libasset = 1
    elif noun in ("library", "assembly", "assemblies", "platform", "platforms", "primitive", "primitives",
                  "application", "applications", "project", "registry"):
        libasset = ""
    else:
        bad(f"Invalid noun {noun}")

    dirtype = get_dirtype(".")
    subdir = "."

    if not libasset or (not standalone and dirtype in project):
        if not libbase != "hdl" or libbase == hdl.is_dir() or verb != "create":
            make_hdl_dir()
        if library:
            if library in components:
                subdir = library
            elif library in ("hdl/cards" or "hdl/devices" or "hdl/adapters"):
                autocreate = 1
                subdir = library
            elif library in "hdl/*":
                subdir = library
            else:
                subdir = f"components/{library}"
        elif platform:
            if f"{hdlorrcc}/platforms/{platform}".is_dir():
                autocreate = 1
                subdir = f"{hdlorrcc}/platforms/{platform}/devices"
            else:
                bad(f"The platform {platform} does not exist in /{hdlorrcc}/platforms/{platform}/")
        elif libbase == "hdl":
            autocreate = 1
            subdir = "hdl/devices"
        elif project:
            subdir = "."
        else:
            check_components(used)
            subdir = components
    elif not libasset or (not standalone and dirtype in library):
        if library:
            if platform or card or project:
                bad(f"Cannot specify -P or -p (platform/project) within a libraries collection")
            else:
                subdir = basename(library)
        else:
            bad(f"Must specifiy a library when operating from a libraries collection")
    elif not libasset or (not standalone and dirtype in hdl-platform):
        if library or platform or card or project:
            bad(f"Cannot specify '-l, -h, -P, or -p' (library/platform/project) within a platform.")
        else:
            autocreate = 1
            subdir = devices
    elif not libasset or (not standalone and dirtype in hdl-platforms):
        if platform:
            if library or card or project:
                bad(f"Cannot specify '-l, -h, -P, or -p' (library/platform) within a platform.")
            if not platform.is_dir():
                bad(f"The platform {platform} does not exist (in hdl/platforms/{platform})")
            else:
                autocreate = 1
                subdir = platform/devices
        else:
            bad(f"Must choose a platform (-P) when operating from the platforms directory.")
    else:
        if not dirtype:
            bad(f"Cannot operate within unknown directory type. Try returning to the top level of your project.")
        else:
            bad(f"Cannot operate within directory of type {dirtype}. Try returning to the top level of your project.")

    if subdir.is_dir() or verb != "create" or autocreate == 1:
        make_library(subdir)
        subdir
    if not subdir.is_dir():
        bad(f"The library for '{library}' '{subdir}' does not exist.")

    subdir_library = get_dirtype(subdir)
    if standalone or dirtype == library or project:  # Confirm targeted subdirectory is actually a library
        bad(f"The directory for '{library}' '({libdir})' is not a library but type '{dirtype}'.")

    get_dirtype(".")  # Restore current directory (desired dirtype) for use after this function call


def get_deletecmd():
    """Recommend delete command for use when a worker/device creation fails.

    Assumes the -k option is used so the partial results remain in the new worker/device directory.
    """
    get_dirtype(".")

    if libbase != hdl:
        del_cmd = f"-l {library} delete {noun}"
    else:
        if noun == worker:
            del_cmd = f"delete {noun}"
        else:
            del_cmd = f"delete hdl {noun}"

        if dirtype in project or dirtype in libraries:
            if platform:
                del_cmd = f"-P {platform} {del_cmd}"
            elif library:
                del_cmd = f"-h {basename(library)} {del_cmd}"
        if dirtype in platforms:
            if platform:
                del_cmd = f"-P {platform} {del_cmd}"
            else:
                bad(f"Need to specify platform '-P' when operating from the /platforms directory.")
        else:
            bad(f"A device can only be created from a project, library, or platform directory")


def ask(*args):  # TODO: Verify whether the ${*} from the Bash file is the same as *args
    """Confirm with the user about performing an action"""
    if JENKINS_HOME:  # TODO: figure out where this directory should be found
        print(f"OCPI:WARNING: Running under Jenkins: auto-answered 'yes' to '{args}?'")
        ans = True
    if not force:
        while not (ans is True or ans is False):
            ans = input(f"Are you sure you want to {args}? (y or n)")
            if ans is "n" or ans is "N":
                ans = False
            elif ans is "y" or ans is "Y":
                ans = True
        if ans is False:
            sys.exit(1)


def do_registry(*args):
    """If not already present, create a registry directory."""
    if verb == "create":
        if not args[1]:
            bad(f"Provide a registry directory to create")
            sys.exit(1)
        elif args[1]:
            bad(f"The registry to create {args[1]} already exists. Use that one or remove it and try again.")
        else:
            if verbose:
                print(f"The project registry {args[1]} has been ")
            else:
                args[1] = Path.mkdir()
                print(f"OCPI:WARNING:To use this registry, run the following command and add it to your ~/.bashrc:\n"
                      f"export OCPI_PROJECT_REGISTRY_DIR={ocpiReadLinkE({args[1]})")
    elif verb == "delete":
        if not args[1]:
            del_registry = OCPI_PROJECT_REGISTRY_DIR
        else:
            del_registry = args[1]
        try:
            if not del_registry:
                raise OSError
            else:
                if ocpiReadLinkE(del_registry) == ocpiReadLinkE(cdk_dir / ".." / "project-registry") \
                        or ocpiReadLinkE(del_registry) == "/opt/opencpi/project-registry":
                    bad(f"Cannot delete the default project registry {del_registry}")
                ask(f"Delete the registry at {del_registry}?")
                shutil.rmtree(args[1])
        except OSError:
            bad(f"Registry to delete ({del_registry}) does not exist")
    elif verb == "set":
        py_cmd = asset_factory.AssetFactory.factory("project", ".").unset_registry()
        if try_return_bool(py_cmd) == 1:  # TODO: Verify whether this block corresponds to Bash script
            sys.stderr.write(try_return_bool(py_cmd))
            sys.exit(1)
        else:
            bad(f"The registry noun is only valid after the create/delete or set/unset verbs.")


def do_project(*args):
    """Handle all aspects of project creation, registration, deregistration, etc."""
    input_arg = args[1]
    if verb == "register":
        try:
            register_project(input_arg)
            if verbose:
                print(f"Successfully registered project {input_arg} in project registry.")
                return
        except OSError:
            sys.exit(1)
    elif verb == "unregister":
        pj_title = str(input_arg)  # TODO: Seems like this and the following if statement could be combined
        if not input_arg:
            pj_title = current

        ask(f"unregister the {pj_title} project/package from its project registry")

        try:
            unregister_project(input_arg)
            if verbose:
                print(f"Successfully unregistered project '{input_arg}' in project registry.")
                return
        except OSError:
            sys.exit(1)
    elif verb == "delete":
        return delete_project(input_arg)  # Return the sys.exit code from delete_project()
    elif verb == "refresh":
        gpmd = cdk_dir / "scripts" / "genProjMetaData.py"
        try:
            if shutil.which(gpmd) is None: # Check if file exists and is executable
                raise OSError
            else:
                gpmd = Path.cwd()  # Set gpmd variable to current working directory
        except OSError:
            return
    elif verb == "build":
        if not buildRcc and not buildHdl and buildClean:
            clean_target = "clean"
        if buildRcc and buildClean:
            buildRcc = ""
            clean_target = " cleanrcc"
        if buildHdl and buildClean:
            buildHdl = ""
            clean_target = " cleanhdl"
        # TODO: Verify the functionality of these make calls; just a copy/paste for now
        subprocess.run(["make -C $subdir/$1 ${verbose:+AT=} imports"])
        subprocess.run(["make -C $subdir/$1 ${verbose:+AT=} ${cleanTarget:+$cleanTarget} ${buildRcc:+rcc}"
                        "${buildHdl:+hdl} ${buildNoAssemblies:+Assemblies=} ${assys:+Assemblies=\" ${assys[@]}\"} "
                        "${hdlplats:+HdlPlatforms=\" ${hdlplats[@]}\"} ${hdltargets:+HdlTargets=\" ${hdltargets[@]}\"} "
                        "${swplats:+RccPlatforms=\" ${swplats[@]}\"} ${hwswplats:+RccHdlPlatforms=\"${hwswplats[@]}\"}"
                        "$OCPI_MAKE_OPTS"])
        if buildClean and not hardClean:
            subprocess.run(["make -C $subdir/$1 ${verbose:+AT=} imports"])
            subprocess.run(["make -C $subdir/$1 ${verbose:+AT=} exports"])
        return
    if dirtype:
        bad(f"The directory '{directory}' where the project directory would be created is inside an OpenCPI project")
    if top or platform or prebuilt or library:
        bad(f"Illegal options present for creating project.")

    no_slash(input_arg)
    no_exist(input_arg)

    arg_dir = Path(input_arg)
    try:  # This is not part of the Bash script but isn't a bad idea
        arg_dir.mkdir()
        os.chdir(arg_dir)
    except FileExistsError:
        bad(f"Directory {arg_dir} already exists.")
    except FileNotFoundError:
        bad(f"Cannot change directories. Directory {arg_dir} does not exist")

    if not packagename:
        packagename = input_arg

    with open("Project.exports", "w") as exports_file:
        text = "# This file specifies aspects of this project that are made available to users,\n" \
               "# by adding or subtracting from what is automatically exported based on the\n" \
               "# documented rules.\n" \
               "# Lines starting with + add to the exports\n" \
               "# Lines starting with - subtract from the exports"
        exports_file.write(text)

    # TODO: Check whether the variables at the end need to be Pythonized or as-is
    with open("Project.mk", "w") as mk_file:
        text = f"# This Makefile fragment is for the '{input_arg} project\n\n" \
               f"# Package identifier is used in a hierarchical fashion from Project to Libraries....\n" \
               f"# The PackageName, PackagePrefix and Package variables can optionally be set here:\n" \
               f"# PackageName defaults to the name of the directory\n" \
               f"# PackagePrefix defaults to local\n" \
               f"# Package defaults to PackagePrefix.PackageName\n" \
               f"#\n" \
               f"# ***************** WARNING ********************\n" \
               f"# When changing the PackageName or PackagePrefix of an existing project the\n" \
               f"# project needs to be both unregistered and re-registered then cleaned and\n" \
               f"# rebuilt. This also includes cleaning and rebuilding any projects that\n" \
               f"# depend on this project.\n" \
               f"# ***************** WARNING ********************\n" \
               f"#\n" \
               f"${packagename:+PackageName=$packagename}\n" \   
               f"${packageprefix:+PackagePrefix=$packageprefix}\n" \
               f"${package:+Package=$package}\n" \
               f"ProjectDependencies=${dependencies[@]}\n" \
               f"${liblibs:+Libraries=${liblibs[@]}}\n" \
               f"${includes:+IncludeDirs=${includes[@]}}\n" \
               f"${xmlincludes:+XmlIncludeDirs=${xmlincludes[@]}}\n" \
               f"${complibs:+ComponentLibraries=${complibs[@]}}"
        mk_file.write(text)

    with open("Makefile", "w") as Makefile:
        text = f"$CheckCDK\n" \
               f"# This is the Makefile for the '{input_arg} project.\n" \
               f"include \$(OCPI_CDK_DIR)/include/project.mk"

    package_id = ocpi_module.util.get_project_package()

    with open(".project", "w") as proj_file:
        text = "<?xml version="1.0" encoding="UTF-8"?>\n" \
                "<projectDescription>\n" \
                    "<name>$package_id</name>\n" \
                    "<comment></comment>\n" \
                    "<projects></projects>\n" \
                    "<buildSpec></buildSpec>\n" \
                    "<natures></natures>\n" \
                "</projectDescription>"
        proj_file.write(text)

    with open(".gitignore", "w") as gitignore:
        text = "# Lines starting with '#' are considered comments.\n" \
               "# Ignore (generated) html files,\n" \
               "#*.html\n" \
               "# except foo.html which is maintained by hand.\n" \
               "#!foo.html\n" \
               "# Ignore objects and archives.\n" \
               "*.rpm\n" \
               "*.obj\n" \
               "*.so\n" \
               "*~\n" \
               "*.o\n" \
               "target-*/\n" \
               "*.deps\n" \
               "gen/\n" \
               "*.old\n" \
               "*.hold\n" \
               "*.orig\n" \
               "*.log\n" \
               "lib/\n" \
               "#Texmaker artifacts\n" \
               "*.aux\n" \
               "*.synctex.gz\n" \
               "*.out\n" \
               "**/doc*/*.pdf\n" \
               "**/doc*/*.toc\n" \
               "**/doc*/*.lof\n" \
               "**/doc*/*.lot\n" \
               "run/\n" \
               "exports/\n" \
               "imports\n" \
               "*.pyc"
        gitignore.write(text)

    with open(".gitattributes", "w") as git_attribs:
        text = "*.ngc -diff\n" \
               "*.edf -diff\n" \
               "*.bit -diff"
        git_attribs.write(text)

    # Register project link in project registry
    if register_enable:
        try:
            register_project(input_arg)
            if keep:
                print(f"The project directory has been created, but not registered \(which may be fine\). If the "
                      f"project must be registered, resolve the conflict and run: ocpidev register project {input_arg}")
            else:
                print(f"Removing the project directory '{input_arg}' due to errors.")
                os.chdir("..")
                shutil.rmtree({input_arg})
        except OSError:
            sys.exit(1)

    subprocess.run(["make", f"{exports}"])
    subprocess.run(["make", f"{imports}"])

    if verbose:
        print(f"A new project named '{input_arg}' has been created in {Path.cwd()}")

