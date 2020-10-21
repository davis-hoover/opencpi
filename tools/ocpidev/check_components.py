# TODO: the arguments will have to be passed in correctly
from pathlib import Path, PosixPath

from tools.ocpidev.ocpidev import get_dirtype
from tools.ocpidev.ocpidev_errors import bad


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