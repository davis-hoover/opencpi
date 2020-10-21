import shutil
import sys
from pathlib import Path

from tools.ocpidev.ask import ask
from tools.ocpidev.ocpidev_errors import bad, try_return_bool
from cdk.ubuntu18_04.lib._opencpi.assets import factory as asset_factory



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