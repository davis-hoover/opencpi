import logging
import sys
from pathlib import PosixPath, Path

from tools.python._opencpi.util import OCPIException


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


def need_name(*args):
    """Ensure a name argument is present"""
    if len(args[1]) == 0:
        bad(f"A name argument is required after the command {args[0]}")
    elif args[1] == "*":
        bad(f"You cannot use '*' as a name")


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