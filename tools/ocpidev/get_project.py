from pathlib import Path

import cdk.ubuntu18_04.lib._opencpi as ocpi_module
from tools.ocpidev.ocpidev_errors import bad


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