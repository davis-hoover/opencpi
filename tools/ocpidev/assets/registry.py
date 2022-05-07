# This file is protected by Copyright. Please refer to the COPYRIGHT file
# distributed with this source distribution.
#
# This file is part of OpenCPI <http://www.opencpi.org>
#
# OpenCPI is free software: you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# OpenCPI is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.
"""
Definition of Registry class
"""

import os
import sys
import json
from glob import glob
import logging
import shutil
from pathlib import Path
import _opencpi.util as ocpiutil
from .abstract import ShowableAsset
from .factory import AssetFactory

# TODO: Should also extend CreatableAsset, ShowableAsset
class Registry(ShowableAsset):
    """
    The Registry class represents an OpenCPI project registry. As an OpenCPI
    registry contains project-package-ID named symlinks to project directories,
    registry instances contain dictionaries mapping package-ID to project instances.
    Projects can be added or removed from a registry
    """
    instances_should_be_cached = True
    def __init__(self, directory, name=None, **kwargs):
        self.out_of_project = True
        self.asset_type = 'registry'
        super().__init__(directory, name, **kwargs)

        # Each registry instance has a list of projects registered within it.
        # Initialize this list by probing the file-system for links that exist
        # in the registry directory.
        # __projects maps package-ID --> project instance
        self.__projects = {}
        # use global scope for now
        #for path in Path(self.directory).iterdir():
        for pid,dir in ocpiutil.find_all_projects().items():
            path = Path(dir)
            if not path.exists() or not path.is_symlink(): # might be dead symlink
                print(f'Warning:  the registry at "{self.directory}" contains an invalid file/link: '+
                      f'{path}',file=sys.stderr)
                continue
            pid = path.name
            project_dir = str(path.resolve())
            self.__projects[pid] = AssetFactory.get_instance("project", project_dir, None, **kwargs)

    def add_assets(self, asset_type, assets, **kwargs):
        """
        Add to the "assets" list the assets from projects in the project path and this registry
        I.e. the registry is virtually extended by the project path
        """
        projects = []

        if asset_type == 'hdl-targets':
            # Since hdl-targets are not really assets they have no pathname
            # so the returned list is not a path, but a triple of
            # name, vendor, toolset, and part list
            _,families,_,_ = ocpiutil.get_hdl_builtins()
            assets.extend(list(families.items()))
        for _,project in self.__projects.items():
            if asset_type == 'projects':
                assets.append(project.directory)
            else:
                # Pass in assets to allow the project to see what is already there
                project.add_assets(asset_type, assets, **kwargs)

    def contains(self, package_id=None, directory=None):
        """
        Given a project's package-ID or directory, determine if the project is present
        in this registry.
        """
        # If neither package_id nor directory are provided, exception
        if package_id is None:
            if directory is None:
                raise ocpiutil.OCPIException("Could determine whether project exists because " +
                                             "the package_id and directory provided were both " +
                                             "None.\nProvide one or both of these arguments.")
            # Project's package-ID is determined from its directory if not provided
            package_id = ocpiutil.get_project_package(directory)
            if package_id is None:
                raise ocpiutil.OCPIException("Could not determine package-ID of project located " +
                                             "at \"" + directory + "\".\nDouble check this " +
                                             "configurations.")

        # If the project is registered here by package-ID, return True.
        # If not, or if a different project is registered here with that package-ID, return False
        if package_id in self.__projects:
            # pylint:disable=bad-continuation
            if (directory is not None and
                os.path.realpath(directory) != self.__projects[package_id].directory):
                logging.warning("Registry at \"" + self.directory + "\" contains a project with " +
                                "package-ID \"" + package_id + "\", but it is not the same " +
                                "project as \"" + directory + "\".")
                return False
            # pylint:enable=bad-continuation
            return True
        return False

    def add(self, package_id, path, force=None, creating=None, verbose=None):
        """
        Given a package ID and project path, create the corresponding link in the project registry,
        and add it to this Registry instance's __projects dictionary.
        If a project with the same package-ID already exists in the registry, fail.
        """
        if not ocpiutil.is_path_in_project(path):
            raise ocpiutil.OCPIException(f'Failure to register project. The pathname "{path}" '+
                                         f'is not in a project or does not exist.')
        if package_id == "local":
            if creating:
                raise ocpiutil.OCPIException(f'Failure to register a new project at "{path}".  '+
                                             f'Cannot register a project with the (default) '+
                                             f'package ID of "local".  Either specify a '+
                                             f'non-local package ID as a "create" option or do '+
                                             f'not request this new project to be registered')
            else:
                raise ocpiutil.OCPIException(f'Failure to register a project at "{path}".  '+
                                             f'Cannot register a project with the (default) '+
                                             f'package ID of "local".  Either specify a '+
                                             f'non-local package ID in the Project.xml file or '+
                                             f'do not request this project to be registered')
        project = self.__projects.get(package_id, None)
        if project:
            # If the project is already registered and is the same
            if project.directory == str(path):
                logging.debug('Project link is already in the registry. Proceeding...')
                print(f'Successfully registered the "{package_id}" project at ' +
                      f'"{path}" in the registry at "{self.directory}".')
                return
            if not force:
                raise ocpiutil.OCPIException(f'Failure to register the project with package id '+
                                             f'"{package_id}", since a project/link with that '+
                                             f'package ID is already registered in '+
                                             f'the registry (at "{self.directory}").\n'+
                                             f'The old registration is not being overwritten.\n'+
                                             f'You can unregister the original project by using '+
                                             f'"ocpidev unregister project {project.directory}"\n' +
                                             f'Then, run the command: "ocpidev -d {path} register" '+
                                             f'or use the "--force" option')
            else:
                self.remove(package_id=package_id)

        # link will be created at <registry>/<package-ID>
        project_link = self.directory + "/" + package_id

        # if this statement is reached and the link exists, it is a broken link
        if os.path.lexists(project_link):
            # remove the broken link that would conflict
            self.remove_link(package_id)

        # Perform the actual registration: create the symlink to the project in this registry
        # directory
        self.create_link(package_id, path)
        # Add the project to this registry's projects dictionary if we are not creating the project
        if not creating:
            self.__projects[package_id] = AssetFactory.get_instance("project", path, verbose=verbose)

        if verbose:
            print(f'Successfully registered the project at "{path}" under the package ID '+
                  f'"{package_id}",\ninto the registry at "{self.directory}".',
                  file=sys.stderr)

    def remove(self, package_id=None, directory=None):
        """
        Given a project's package-ID or directory, determine if the project is present
        in this registry. If so, remove it from this registry's __projects dictionary
        and remove the registered symlink.
        """
        logging.debug("package_id=" + str(package_id)+ " directory=" + str(directory))
        if package_id is None:
            package_id = ocpiutil.get_project_package(directory)
            if package_id is None:
                raise ocpiutil.OCPIException("Could not unregister project located at \"" +
                                             directory + "\" because the project's package-ID " +
                                             "could not be determined.\nIs it really a project?")

        if package_id not in self.__projects:
            link_path = self.directory + "/" + package_id
            if os.path.exists(link_path) and not os.path.exists(os.readlink(link_path)):
                logging.debug("Removing the following broken link from the registry:\n" +
                              link_path + " -> " + os.readlink(link_path))
                self.remove_link(package_id)
                print("Successfully unregistered the " + package_id + " project: " +
                      os.path.realpath(directory) + "\nFrom the registry: " +
                      os.path.realpath(self.directory) + "\n")
                return
            raise ocpiutil.OCPIException("Could not unregister project with package-ID \"" +
                                         package_id + "\" because the project is not in the " +
                                         "registry.\n Run 'ocpidev show registry --table' for " +
                                         "information about the currently registered projects.\n")

        # if a project is deleted from disk underneath our feet this could be None (AV-4483)
        if self.__projects[package_id] is not None:
            project_link = self.__projects[package_id].directory
            if directory is not None and os.path.realpath(directory) != project_link:
                raise ocpiutil.OCPIException("Failure to unregister project with package '" +
                                             package_id + "'.\nThe registered project with link '" +
                                             package_id + " --> " + project_link + "' does not " +
                                             "point to the specified project '" +
                                             os.path.realpath(directory) + "'." + "\nThis " +
                                             "project does not appear to be registered.")

        if directory is None:
            directory = str(self.__projects[package_id].directory)
        # Remove the symlink registry/package-ID --> project
        self.remove_link(package_id)
        # Remove the project from this registry's dict
        self.__projects.pop(package_id)
        print("Successfully unregistered the " + package_id + " project: " +
              os.path.realpath(directory) + "\nFrom the registry: " +
              os.path.realpath(self.directory) + "\n" + str(self.__projects))

    def create_link(self, package_id, path):
        """
        Create a link to the provided project in this registry
        """
        registry_path = Path(self.directory).resolve()
        # rel_path = path.resolve().relative_to(registry_path)
        rel_path = Path(os.path.relpath(path, registry_path))
        registration_path = registry_path.joinpath(package_id)
        try:
            registration_path.symlink_to(rel_path)
        except Exception as e:
            raise ocpiutil.OCPIException(f'Failure to register project at directory "{path}".'+
                                         f'with package ID "{package_id}".  Error was "{e}".\n'+
                                         f'The registry is at "{self.directory}".')

    def remove_link(self, package_id):
        """
        Remove link with name=package-ID from this registry
        """
        link_path = self.directory + "/" + package_id
        try:
            os.unlink(link_path)
        except OSError:
            raise ocpiutil.OCPIException("Failure to unregister link to project: " + package_id +
                                         " --> " + os.readlink(link_path) + "\nCommand " +
                                         "attempted: 'unlink " + link_path + "'\nTo " +
                                         "(un)register projects in " +
                                         "/opt/opencpi/project-registry, you need to be a " +
                                         "member of the opencpi group.")

    def get_project(self, package_id):
        """
        Return the project with the specified package-id that is registered in this registry
        """
        if package_id not in self.__projects:
            raise ocpiutil.OCPIException("\"" + package_id + "\" is not a valid package-id or " +
                                         "project directory")
        return self.__projects[package_id]

    @staticmethod
    def create(name=None, directory=None, **kwargs):
        """
        Create a registry (which is essentially a folder) at the location specified by asset_dir
        """
        asset_dir = directory + "/" + name
        print("making: " + asset_dir)
        os.mkdir(asset_dir)

    @staticmethod
    def get_default_registry_dir():
        """
        Get the default registry from the environment setup. Check in the following order:
        OCPI_PROJECT_REGISTRY_DIR, OCPI_ROOT_DIR/project-registry or /opt/opencpi/project-registry
        """
        project_registry_dir = os.environ.get('OCPI_PROJECT_REGISTRY_DIR')
        if project_registry_dir is None:
            cdkdir = os.environ.get('OCPI_CDK_DIR')
            if cdkdir:
                project_registry_dir = cdkdir + "/../project-registry"
                project_registry_dir = os.path.realpath(project_registry_dir)
            else:
                project_registry_dir = "/opt/opencpi/project-registry"
        path = Path(project_registry_dir)
        if not path.is_dir():
            raise ocpiutil.OCPIException(f'The default registry directory is "{path}", but it is '+
                                         f'not a directory')
        return project_registry_dir

    @staticmethod
    def get_default_registry_path():
        return Path(__class__.get_default_registry_dir())

    def _collect_workers_dict(self):
        """
        return a dictionary with all the workers in all the projects in the registry
        """
        ret_dict = {}
        proj_dict = {}
        for proj in self.__projects:
            lib_dict = {}
            for lib in self.__projects[proj].lib_list:
                wkr_dict = {}
                # pylint:disable=unused-variable
                tests, wkrs = lib.get_valid_tests_workers()
                # pylint:enable=unused-variable
                for wkr in wkrs:
                    wkr_dict[os.path.basename(wkr)] = wkr
                if wkr_dict:
                    wkrs_dict = {"workers":wkr_dict,
                                 "directory":lib.directory,
                                 "package_id": lib.package_id}
                    lib_package = lib.package_id
                    # in case two or more libraries have the same package id we update the key to
                    # end with a number
                    i = 1
                    while lib_package in lib_dict:
                        lib_package += ":" + str(i)
                        i += 1
                    lib_dict[lib_package] = wkrs_dict
            if lib_dict:
                libs_dict = {"libraries":lib_dict,
                             "directory":self.__projects[proj].directory,
                             "package_id": self.__projects[proj].package_id}
                proj_dict[self.__projects[proj].package_id] = libs_dict

        ret_dict["projects"] = proj_dict
        return ret_dict

    def _collect_components_dict(self):
        """
        return a dictionary with all the components in all the projects in the registry
        """
        ret_dict = {}
        proj_dict = {}
        for proj in self.__projects:
            top_comp_dict = {}
            for comp in self.__projects[proj].get_valid_components():
                comp_name = ocpiutil.rchop(os.path.basename(comp), "spec.xml")[:-1]
                top_comp_dict[comp_name] = comp
            lib_dict = {}
            for lib in self.__projects[proj].lib_list:
                comp_dict = {}
                for comp in lib.get_valid_components():
                    comp_name = ocpiutil.rchop(os.path.basename(comp), "spec.xml")[:-1]
                    comp_dict[comp_name] = comp
                if comp_dict:
                    comps_dict = {"components":comp_dict,
                                  "directory":lib.directory,
                                  "package_id": lib.package_id}
                    lib_package = lib.package_id
                    # in case two or more  libraries have the same package id we update the key to
                    # end with a number
                    i = 1
                    while lib_package in lib_dict:
                        lib_package += ":" + str(i)
                        i += 1
                    lib_dict[lib_package] = comps_dict
            if lib_dict:
                libs_dict = {"libraries":lib_dict,
                             "directory":self.__projects[proj].directory,
                             "package_id": self.__projects[proj].package_id}
                if top_comp_dict:
                    libs_dict["components"] = top_comp_dict
                proj_dict[self.__projects[proj].package_id] = libs_dict

        ret_dict["projects"] = proj_dict
        return ret_dict

    # pylint:disable=unused-argument
    def show_workers(self, format, verbose, **kwargs):
        """
        Show all the workers in all the projects in the registry
        """
        reg_dict = self._collect_workers_dict()
        if format == "simple":
            for proj in reg_dict["projects"]:
                for lib in reg_dict["projects"][proj]["libraries"]:
                    for wkr in reg_dict["projects"][proj]["libraries"][lib]["workers"]:
                        print(wkr + " ", end="")
            print()
        elif format == "table":
            rows = [["Project", "Library Directory", "Worker"]]
            for proj in reg_dict["projects"]:
                for lib in reg_dict["projects"][proj]["libraries"]:
                    for wkr in reg_dict["projects"][proj]["libraries"][lib]["workers"]:
                        lib_dict = reg_dict["projects"][proj]["libraries"][lib]
                        rows.append([proj, lib_dict["directory"], wkr])
            ocpiutil.print_table(rows, underline="-")
        elif format == "json":
            json.dump(reg_dict, sys.stdout)
            print()
    # pylint:enable=unused-argument

    # pylint:disable=unused-argument
    def show_components(self, format, verbose, **kwargs):
        """
        Show all the components in all the projects in the registry
        """
        reg_dict = self._collect_components_dict()
        if format == "simple":
            for proj in reg_dict["projects"]:
                for comp in reg_dict["projects"][proj].get("components", []):
                    print(comp + " ", end="")
                for lib in reg_dict["projects"][proj]["libraries"]:
                    for comp in reg_dict["projects"][proj]["libraries"][lib]["components"]:
                        print(comp + " ", end="")
            print()
        elif format == "table":
            rows = [["Project", "Component Spec Directory", "Component"]]
            for proj in reg_dict["projects"]:
                for comp in reg_dict["projects"][proj].get("components", []):
                    rows.append([proj, reg_dict["projects"][proj]["directory"] + "/specs", comp])
                for lib in reg_dict["projects"][proj]["libraries"]:
                    for comp in reg_dict["projects"][proj]["libraries"][lib]["components"]:
                        lib_dict = reg_dict["projects"][proj]["libraries"][lib]
                        rows.append([proj, lib_dict["directory"] + "/specs", comp])
            ocpiutil.print_table(rows, underline="-")
        elif format == "json":
            json.dump(reg_dict, sys.stdout)
            print()
    # pylint:enable=unused-argument

    def get_dict(self, get_package):
        """
        return a dictionary with with information about the registry
        """
        proj_dict = {}
        for proj in self.__projects:
            if self.__projects[proj]:
                if get_package:
                    package_id = self.__projects[proj].package_id
                else:
                    package_id = proj
                proj_dict[package_id] = {
                    "real_path":self.__projects[proj].directory,
                    "exists":(os.path.exists(self.__projects[proj].directory) and
                              os.path.isdir(self.__projects[proj].directory))}

        json_dict = {"registry_location": self.directory}
        json_dict["projects"] = proj_dict
        return json_dict

    def show(self, format, verbose, **kwargs):
        """
        show information about the registry in the format specified by format
        (simple, table, or json)
        """
        reg_dict = self.get_dict(False)
        if format == "simple":
            print(" ".join(sorted(reg_dict["projects"])))
        elif format == "table":
            print("Project registry is located at: " + reg_dict["registry_location"])
            # Table header
            row_1 = ["Project Package-ID", "Path to Project", "Valid/Exists"]
            rows = [row_1]
            for proj in reg_dict["projects"]:
                rows.append([proj, reg_dict["projects"][proj]["real_path"],
                             reg_dict["projects"][proj]["exists"]])
            ocpiutil.print_table(rows, underline="-")
        elif format == "json":
            json.dump(reg_dict, sys.stdout)
            print()

    def delete(self, force=False, **kwargs):
        """
        Deletes the registry. Prompts the user to confirm if args.force
        is not True. Refuses to delete the default registry or registry
        set to OCPI_PROJECT_REGISTRY_DIR.
        """
        root_dir = os.getenv('OCPI_ROOT_DIR', '')
        default_registry_dir = str(Path(root_dir, 'project-registry'))
        err_msg = None
        registry_dir = os.getenv('OCPI_PROJECT_REGISTRY_DIR', None)
        if registry_dir:
            registry_dir = str(Path(registry_dir).resolve())
        if default_registry_dir == self.directory:
            err_msg = 'Cannot delete the default project registry'
        elif registry_dir and registry_dir == self.directory:
            if force: 
                os.environ.pop('OCPI_PROJECT_REGISTRY_DIR')
            else:
                err_msg = ' '.join([
                    'Cannot delete registry set in OCPI_PROJECT_REGISTRY_DIR',
                    'environment variable. Unset variable before attempting to delete'])
        if err_msg:
            raise ocpiutil.OCPIException(err_msg)
        super().delete(force=force, **kwargs)
