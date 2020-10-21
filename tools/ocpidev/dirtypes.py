from pathlib import PosixPath

from tools.ocpidev.ocpidev import parse_makefile
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