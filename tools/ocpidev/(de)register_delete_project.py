import os
import subprocess
import sys

import cdk.ubuntu18_04.lib._opencpi as ocpi_module
from cdk.ubuntu18_04.lib._opencpi.assets import factory as asset_factory
from cdk.ubuntu18_04.lib._opencpi.assets import registry as asset_registry
from tools.ocpidev.ocpidev_errors import try_return_bool


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