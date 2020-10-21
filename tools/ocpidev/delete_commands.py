from tools.ocpidev.dirtypes import get_dirtype
from tools.ocpidev.ocpidev_errors import bad


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