from tools.ocpidev.get_dirtype import get_dirtype
from tools.ocpidev.ocpidev_errors import bad


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