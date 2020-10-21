from pathlib import PosixPath

from tools.ocpidev.check_components import check_components
from tools.ocpidev.ocpidev import parse_makefile, make_library
from tools.ocpidev.ocpidev_errors import bad


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
