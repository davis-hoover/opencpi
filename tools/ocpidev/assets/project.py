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
Definition of Project class
"""

import os
import sys
import logging
import json
import jinja2
from pathlib import Path
import _opencpi.util as ocpiutil
from _opencpi.util import OCPIException
import _opencpi.assets.template as ocpitemplate
from .abstract import (RunnableAsset, RCCBuildableAsset, HDLBuildableAsset, ShowableAsset,
                       ReportableAsset, Asset)
from .factory import AssetFactory
from .library import Library
import _opencpi.assets.registry as ocpiregistry
from .component import Component


# TODO: Should also extend CreatableAsset, ShowableAsset
# pylint:disable=too-many-instance-attributes
# pylint:disable=too-many-ancestors
class Project(RunnableAsset, RCCBuildableAsset, HDLBuildableAsset, ShowableAsset, ReportableAsset):
    """
    The Project class represents an OpenCPI project. Only one Project class should
    exist per OpenCPI project. Projects can be built, run, registered, shown....
    """
    valid_settings = []
    instances_should_be_cached = True
    def __init__(self, directory, name=None, verb=None, **kwargs):
        """
        Initializes Project member data  and calls the super class __init__.  Throws an
        exception if the directory passed in is not a valid project directory.
        """
        self.asset_type = 'project'
        # This next line is saying that that there is no resolution from a parent.
        # FIXME: stop callers using name==None ever
        kwargs['child_path'] = name if name else Path(directory).name
        super().__init__(directory, name, **kwargs)
        kwargs.pop('child_path', None) # ugh.
        self.check_dirtype("project", self.directory)
        self.lib_list = None
        self.apps_col_list = None

        # Boolean for whether or the current directory is within this project
        # TODO: is current_project needed as a field, or can it be a function?
        #self.current_project = ocpiutil.get_path_to_project_top() == self.directory
        self.__registry = None
        self.package_id = self.get_package_id(self.directory)

        # NOTE: imports link to registry is NOT initialized in this constructor.
        #       Neither is the __registry Registry object.
        if verb in ['run','utilization'] or (verb == 'show' and self.verbose > 1):
            self.lib_list = []
            logging.debug("Project constructor creating Library Objects")
            for lib_directory in self.get_valid_libraries():
                self.lib_list.append(AssetFactory.factory("library", lib_directory,
                                                          verb=verb, **kwargs))
        if verb == 'run' or (verb == 'show' and self.verbose):
            self.apps_col_list = []
            logging.debug("Project constructor creating ApplicationCollection Objects")
            for app_directory in self.get_valid_apps_col():
                self.apps_col_list.append(AssetFactory.factory("applications", app_directory,
                                                               verb=verb, **kwargs))
        if verb == 'show' and self.verbose:
            self.comp_list = []
            package_id = None
            for comp_directory in self.get_valid_components():
                if package_id:
                    kwargs["package_id"] = package_id
                #comp_name = ocpiutil.rchop(os.path.basename(comp_directory), "spec.xml")[:-1]
                self.comp_list.append(Component(comp_directory, name=None, verb=verb, **kwargs))
                package_id = self.comp_list[0].package_id
        self.hdlplatforms = None
        self.rccplatforms = None
        self.hdlassemblies = None
        self._initialize_platforms(**kwargs)

    @classmethod
    def resolve_child(cls, path, asset_type, args):
        """
        Resolve the actual relative path and name for a child asset as needed
        Here is the knowledge of where various assets live inside a project
        """
        assert asset_type in ['library', 'component', 'protocol', 'hdl-slot', 'hdl-assemblies', 'applications', 'libraries']
        name = args.name
        if asset_type == 'library':
            if name == 'components':
                args.child_path = Path("components")
            else:
                args.child_path = Path("components", name)
        elif asset_type in ['component', 'protocol', 'hdl-slot']:
            args.name, args.child_path = Library.resolve_file_child(asset_type, path, args)
        elif asset_type == 'applications':
            args.child_path = 'applications'
        elif asset_type == 'libraries':
            args.child_path = 'components'

    def _initialize_platforms(self, verb=None, verbose=None, **kwargs):
        """
        initialize the variables self.hdlplatforms, self.rccplatforms, and self.hdlassemblies with
        lists of these asset types if the init variable associated with them
        (init_rccplats, init_hdlplats, and init_hdlassembs) are set to True
        """
        if verb == 'utilization' or (self.verbose > 0 and verb == 'show'):
            logging.debug("Project constructor creating RccPlatformsCollection Object")
            plats_directory = self.directory + "/rcc/platforms"
            # If hdl/platforms exists for this project, construct the HdlPlatformsCollection
            # instance
            if os.path.exists(plats_directory):
                self.rccplatforms = [AssetFactory.factory("rcc-platforms", plats_directory,
                                                          **kwargs)]
            else:
                self.rccplatforms = []
            logging.debug("Project constructor creating HdlPlatformsCollection Object")
            plats_directory = self.directory + "/hdl/platforms"
            # If hdl/platforms exists for this project, construct the HdlPlatformsCollection
            # instance
            if os.path.exists(plats_directory):
                self.hdlplatforms = [AssetFactory.factory("hdl-platforms", plats_directory,
                                                          **kwargs)]
            else:
                self.hdlplatforms = []
        if (verb == 'show' and verbose > 1) or verb == 'utilization':
            logging.debug("Project constructor creating HdlAssembliesCollection Object")
            assemb_directory = self.directory + "/hdl/assemblies"
            # If hdl/assemblies exists for this project, construct the HdlAssembliesCollection
            # instance
            if os.path.exists(assemb_directory):
                self.hdlassemblies = AssetFactory.factory("hdl-assemblies", assemb_directory,
                                                          **kwargs)

    def __eq__(self, other):
        """
        Two projects are equivalent if their directories match
        """
        #TODO: do we need realpath too? remove the abs/realpaths if we instead call
        # them in the Asset constructor
        return (other is not None and
                os.path.realpath(self.directory) == os.path.realpath(other.directory))

    def delete(self, **kwargs):
        """
        Remove the project from the registry if it is registered anywhere and remove the project
        from disk
        """
        registry = self.registry()
        if super().delete(**kwargs) and registry:
            try:
                registry.remove(package_id=self.package_id)
            except ocpiutil.OCPIException:
                # do nothing it's ok if the unregistering fails
                pass

    @staticmethod
    def get_package_id(directory):
        """ Get the package id from a project given a project directory path """
        # If the project-package-id file exists, set package-id to its contents
        dir_path = Path(directory)
        try:
            exported_package_id_file = dir_path.joinpath("project-package-id")
            with open(exported_package_id_file, "r") as package_id_file:
                project_package_id = package_id_file.read().strip()
                logging.debug("Read Project-ID '" + project_package_id + "' from file: " +
                              str(exported_package_id_file))
                return project_package_id
        except:
            pass
        # If not an exported project, use "make" to get it
        project_vars = ocpiutil.set_vars_from_make(ocpiutil.get_makefile(str(dir_path), "project"),
                                                   mk_arg="projectpackage ShellProjectVars=1",
                                                   verbose=True)
        if (project_vars and 'ProjectPackage' in project_vars and
            len(project_vars['ProjectPackage']) > 0):
            return project_vars['ProjectPackage'][0]
        raise ocpiutil.OCPIException("Could not determine PackageID of project \"" +
                                     str(dir_path) + "\".")

    def get_valid_apps_col(self):
        """
        Gets a list of all directories of type applications in the project and puts that
        applications directory and the basename of that directory into a list to return
        """
        apps=self.directory + "/applications"
        return [ apps ] if os.path.isdir(apps) and ocpiutil.get_dirtype(apps) == "applications" else [];

    def get_valid_libraries(self, **kwargs):
        """
        Gets a list of all directories for libraries in the project, subject to the
        various filtering options
        library directory and the basename of that directory into a list to return
        """
        library = kwargs.get('library', False)
        hdl_library = kwargs.get('hdl_library', False)
        platform = kwargs.get('platform', False)
        if library:
            return [ 'components' + ("/" + library) if library != 'components' else '' ]
        if platform:
            return [ 'hdl/platforms/' + platform + '/devices' ]
        if hdl_library:
            return [ 'hdl/' + hdl_library ]
        # The places where component libraries might exist
        libs=[]
        for pattern in [ 'components', 'components/*', 'hdl/[cards|devices|adapters]',
                        'hdl/platforms/*/devices']:
            for match in Path(self.directory).glob(pattern):
                if match.is_dir() and ocpiutil.get_dirtype(str(match)) == 'library':
                    libs.append(str(match))
        return libs

    def run(self, **kwargs):
        """
        Runs the Project with the settings specified in the object Throws an exception if no
        applications or libraries are initialized using the init_apps or init_libs variables at
        initialization time
        """
        ret_val = 0
        if (self.apps_col_list is None) and (self.lib_list is None):
            raise ocpiutil.OCPIException("For a Project to be run \"init_libs\" and " +
                                         "\"init_tests\" or \"init_apps_col\" must be set to " +
                                         "True when the object is constructed")
        if self.apps_col_list is not None:
            for apps in self.apps_col_list:
                run_val = apps.run(**kwargs)
                ret_val = ret_val + run_val
        if self.lib_list is not None:
            for lib in self.lib_list:
                run_val = lib.run(**kwargs)
                ret_val = ret_val + run_val
        return ret_val

    def clean(self, verbose=False, hdl=False, rcc=False, clean_all=False,
        worker=None, no_assemblies=False, hdl_assembly=None, hdl_platform=None,
              hdl_target=None, rcc_platform=None, hdl_rcc_platform=None, **kwargs):
        """
        Cleans the project by handing over the user specifications
        to execute command.
        """
        #Specify what to clean
        action=[]
        if not rcc and not hdl:
            action.append('clean')
        else:
            if rcc:
                action.append('cleanrcc')
            if hdl:
                action.append('cleanhdl')
        if no_assemblies:
            action.append('Assemblies=')
        settings = {}
        if hdl_assembly:
            settings['hdl_assembly'] = hdl_assembly
        if hdl_platform:
            settings['hdl_plat_strs'] = hdl_platform
        if hdl_target:
            settings['hdl_target'] = hdl_target
        if rcc_platform:
            settings['rcc_platform'] = rcc_platform
        if hdl_rcc_platform:
            settings['hdl_rcc_platform'] = hdl_rcc_platform
        if worker:
            settings['worker'] = worker
        make_file = ocpiutil.get_makefile(self.directory, "project")[0]
        #Clean
        ocpiutil.execute_cmd(settings,
                             self.directory,
                             action=action,
                             file=make_file,
                             verbose=verbose)
        if not clean_all:
            ocpiutil.execute_cmd({},
                                 self.directory,
                                 action=['imports'],
                                 file=make_file,
                                 verbose=verbose)
            ocpiutil.execute_cmd({},
                                 self.directory,
                                 action=['exports'],
                                 file=make_file,
                                 verbose=verbose)

    def build(self, **kwargs):
        """
        Builds the project by handing over the user specifications to execute command. 
        Performing the "imports" step is done prior to using the generic build method
        """
        make_file = ocpiutil.get_makefile(self.directory, "project")[0]
        ocpiutil.execute_cmd({},
                             self.directory,
                             action=['imports'],
                             file=make_file,
                             verbose=kwargs.get('verbose'))
        super().build(export=True, **kwargs)

    def get_show_test_dict(self):
        """
        Generate the dictionary that is used to show all the tests in this project
        """
        json_dict = {}
        project_dict = {}
        libraries_dict = {}
        for lib in self.lib_list:
            # pylint:disable=unused-variable
            valid_tests, valid_workers = lib.get_valid_tests_workers()
            # pylint:disable=unused-variable
            if  valid_tests:
                lib_dict = {}
                lib_package = lib.package_id
                lib_dict["package"] = lib_package
                lib_dict["directory"] = lib.directory
                lib_dict["tests"] = {os.path.basename(test.rstrip('/')):test
                                     for test in valid_tests}
                # in case two or more  libraries have the same package id we update the key to end
                # with a number
                i = 1
                while lib_package in libraries_dict:
                    lib_package += ":" + str(i)
                    i += 1
                libraries_dict[lib_package] = lib_dict
        project_vars = ocpiutil.set_vars_from_make(ocpiutil.get_makefile(self.directory, "project"),
                                                   mk_arg="projectdeps ShellProjectVars=1",
                                                   verbose=True)
        project_dict["dependencies"] = project_vars['ProjectDependencies']
        project_dict["directory"] = self.directory
        project_dict["libraries"] = libraries_dict
        project_dict["package"] = self.package_id
        json_dict["project"] = project_dict
        return json_dict

    # pylint:disable=unused-argument
    def show_tests(self, format, verbose, **kwargs):
        """
        Print out all the tests in a project in the format given by format
        (simple, verbose, or json)

        JSON format:
        {project:{
          name: proj_name
          directory: proj_directory
          libraries:{
            lib_name:{
              name: lib_name
              directory:lib_directory
              tests:{
                test_name : test_directory
                ...
              }
            }
          }
        }
        """
        if self.lib_list is None:
            raise ocpiutil.OCPIException("For a Project to show tests \"init_libs\" "
                                         "must be set to True when the object is constructed")
        json_dict = self.get_show_test_dict()
        if format == "simple":
            for lib in json_dict["project"]["libraries"]:
                print("Library: " + json_dict["project"]["libraries"][lib]["directory"])
                tests_dict = json_dict["project"]["libraries"][lib]["tests"]
                for test in tests_dict:
                    print("    Test: " + tests_dict[test])
        elif format == "table":
            rows = [["Library Directory", "Test"]]
            for lib in json_dict["project"]["libraries"]:
                tests_dict = json_dict["project"]["libraries"][lib]["tests"]
                for test in tests_dict:
                    rows.append([json_dict["project"]["libraries"][lib]["directory"], test])
            ocpiutil.print_table(rows, underline="-")
        else:
            json.dump(json_dict, sys.stdout)
            print()
    # pylint:enable=unused-argument

    # pylint:disable=unused-argument
    def show_libraries(self, format, verbose, **kwargs):
        """
        Print out all the libraries that are in this project in the format specified by format
        (simple, table, or json)
        """
        json_dict = {}
        project_dict = {}
        libraries_dict = {}
        for lib_directory in self.get_valid_libraries():
            lib_dict = {}
            lib_package = Library.get_package_id(lib_directory)
            lib_dict["package"] = lib_package
            lib_dict["directory"] = lib_directory
            # in case two or more  libraries have the same package id we update the key to end
            # with a number
            i = 1
            while lib_package in libraries_dict:
                lib_package += ":" + str(i)
                i += 1
            libraries_dict[lib_package] = lib_dict
        project_vars = ocpiutil.set_vars_from_make(ocpiutil.get_makefile(self.directory, "project"),
                                                   mk_arg="projectdeps ShellProjectVars=1",
                                                   verbose=True)
        project_dict["dependencies"] = project_vars['ProjectDependencies']
        project_dict["directory"] = self.directory
        project_dict["libraries"] = libraries_dict
        project_dict["package"] = self.package_id
        json_dict["project"] = project_dict

        if format == "simple":
            lib_dict = json_dict["project"]["libraries"]
            for lib in lib_dict:
                print("Library: " + lib_dict[lib]["directory"])
        elif format == "table":
            rows = [["Library Directories"]]
            lib_dict = json_dict["project"]["libraries"]
            for lib in lib_dict:
                rows.append([lib_dict[lib]["directory"]])
            ocpiutil.print_table(rows, underline="-")
        else:
            json.dump(json_dict, sys.stdout)
            print()
    # pylint:enable=unused-argument

    def _collect_components_dict(self):
        """
        return a dictionary with all the components in the project
        """
        top_comp_dict = {}
        for comp in self.get_valid_components():
            comp_name = ocpiutil.rchop(os.path.basename(comp), "spec.xml")[:-1]
            top_comp_dict[comp_name] = comp
        lib_dict = {}
        if top_comp_dict:
            lib_dict[self.directory + "/specs"] = { "components" : top_comp_dict,
                                                    "package_id" : self.package_id }
        for lib in self.lib_list:
            comp_dict = {}
            for comp in lib.get_valid_components():
                comp_name = ocpiutil.rchop(os.path.basename(comp), "spec.xml")[:-1]
                comp_dict[comp_name] = comp
            if comp_dict:
                comps_dict = {"components":comp_dict,
                              "package_id": lib.package_id}
                lib_dict[lib.directory + "/specs"] = comps_dict
        return lib_dict

    # pylint:disable=unused-argument
    def show_components(self, format, verbose, **kwargs):
        """
        Show all the components in all the projects in the registry
        """
        lib_dict = self._collect_components_dict()
        if format == "simple":
            for dir, comps_dict in lib_dict.items():
                for comp in comps_dict["components"]:
                    print(comp + " ", end="")
            print()
        elif format == "table":
            rows = [["Library Package ID", "Component Spec Directory", "Component"]]
            for dir, comps_dict in lib_dict.items():
                for comp in sorted(comps_dict["components"]):
                    rows.append([comps_dict["package_id"], dir[len(self.directory)+1:], comp])
            ocpiutil.print_table(rows, underline="-")
        elif format == "json":
            json.dump(lib_dict, sys.stdout)
            print()
    # pylint:enable=unused-argument

    def _collect_workers_dict(self):
        """
        return a dictionary with all the workers in the projects
        """
        lib_dict = {}
        for lib in self.lib_list:
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
        return lib_dict

    # pylint:disable=unused-argument

    def show_workers(self, format, verbose, **kwargs):
        """
        Show all the workers in the projects
        """
        lib_dict = self._collect_workers_dict()
        if format == "simple":
            for id,lib in lib_dict.items():
                print(self.directory)
                for wkr in lib["workers"]:
                    print(wkr + " ", end="")
            print()
        elif format == "table":
            rows = [["Library Package ID", "Library Directory", "Worker"]]
            for id,lib in lib_dict.items():
                for wkr in sorted(lib["workers"]):
                    rows.append([lib["package_id"], lib["directory"][len(self.directory)+1:], wkr])
            ocpiutil.print_table(rows, underline="-")
        elif format == "json":
            json.dump(lib_dict, sys.stdout)
            print()
    # pylint:enable=unused-argument

    # pylint:disable=unused-argument
    def _show_non_verbose(self, format, **kwargs):
        """
        show all the information about a project with level 1 of verbosity in the format specified
        by format (simple, table, or json)
        """
        project_vars = ocpiutil.set_vars_from_make(ocpiutil.get_makefile(self.directory, "project"),
                                                   mk_arg="projectdeps ShellProjectVars=1",
                                                   verbose=True)
        #TODO output the project's registry here too
        proj_depends = project_vars['ProjectDependencies']
        if not proj_depends:
            proj_depends.append("None")
        proj_dict = {'project': {'directory': self.directory,
                                 'package': self.package_id,
                                 'dependencies': proj_depends}}

        if format == "simple":
            print("Project Directory: " + proj_dict["project"]["directory"])
            print("Package-ID: " + proj_dict["project"]["package"])
            print("Project Dependencies: " + ", ".join(proj_dict["project"]["dependencies"]))
        elif format == "table":
            rows = [["Project Directory", "Package-ID", "Project Dependencies"]]
            rows.append([proj_dict["project"]["directory"],
                         proj_dict["project"]["package"],
                         ", ".join(proj_dict["project"]["dependencies"])])
            ocpiutil.print_table(rows, underline="-")
        else:
            json.dump(proj_dict, sys.stdout)
            print()

    def _collect_plats_dict(self):
        """
        Generate a dictionary that contains all the rcc and hdl platforms within this project
        """
        rcc_plats_dict = {}
        for rcc_plats_col in self.rccplatforms:
            for rcc_plat in rcc_plats_col.platform_list:
                rcc_plats_dict[rcc_plat.name] = rcc_plat.directory
        hdl_plats_dict = {}
        for hdl_plats_col in self.hdlplatforms:
            for hdl_plat in hdl_plats_col.platform_list:
                hdl_plats_dict[hdl_plat.name] = hdl_plat.directory
        plats_dict = {"rcc": rcc_plats_dict, "hdl": hdl_plats_dict}
        return plats_dict

    def _collect_verbose_dict(self):
        """
        Generate a dictionary that contains all the information about a project with verbosity
        level 1
        """
        proj_dict = {}
        top_dict = {}
        libraries_dict = {}
        top_comp_dict = {}
        for comp in self.comp_list:
            top_comp_dict[comp.name] = comp.directory
        top_dict["components"] = top_comp_dict
        for lib in self.get_valid_libraries():
            lib_package = Library.get_package_id(lib)
            i = 1
            while lib_package in libraries_dict:
                lib_package += ":" + str(i)
                i += 1
            libraries_dict[lib_package] = lib
        if os.path.isdir(self.directory + "/applications"):
            apps_dict = {}
            for app_col in self.apps_col_list:
                for app in app_col.apps_list:
                    apps_dict[app.name] = app.directory
            top_dict["applications"] = apps_dict
        project_vars = ocpiutil.set_vars_from_make(ocpiutil.get_makefile(self.directory, "project"),
                                                   mk_arg="projectdeps ShellProjectVars=1",
                                                   verbose=True)
        proj_depends = project_vars['ProjectDependencies']
        if not proj_depends:
            proj_depends.append("None")
        top_dict["dependencies"] = proj_depends
        top_dict["directory"] = self.directory
        top_dict["libraries"] = libraries_dict
        top_dict["platforms"] = self._collect_plats_dict()
        top_dict["package"] = self.package_id
        proj_dict["project"] = top_dict
        return proj_dict

    def _get_very_verbose_assemblies_dict(self):
        """
        Generate the dictionary of assemblies within a project that is used with verbosity level 2
        """
        assys_dict = {}
        if self.hdlassemblies:
            for assy in self.hdlassemblies.assembly_list:
                assys_dict[assy.name] = assy.directory
        return assys_dict

    def _get_very_verbose_prims_dict(self):
        """
        Generate the dictionary of primitives within a project that is used with verbosity level 2
        """
        prims_dict = {}
        prim_dir = self.directory + "/hdl/primitives"
        if os.path.isdir(prim_dir):
            prims = [dir for dir in os.listdir(prim_dir)
                     if not os.path.isfile(os.path.join(prim_dir, dir))]
            prims = [x for x in prims if x != "lib"]
            for prim in prims:
                prims_dict[prim] = prim_dir + "/" + prim
        return prims_dict

    def _get_very_verbose_libs_dict(self):
        """
        Generate the dictionary of libraries within a project that is used with verbosity level 2
        """
        libraries_dict = {}
        for lib in self.lib_list:
            lib_dict = {}
            lib_package = lib.package_id
            lib_dict["package"] = lib_package
            lib_dict["directory"] = lib.directory
            valid_tests, valid_workers = lib.get_valid_tests_workers()
            if  valid_tests:
                have_any_tests = True
                lib_dict["tests"] = {os.path.basename(test.rstrip('/')):test
                                     for test in valid_tests}
            if valid_workers:
                have_any_wkrs = True
                lib_dict["workers"] = {os.path.basename(wkr.rstrip('/')):wkr
                                       for wkr in valid_workers}
            valid_comps = lib.get_valid_components()
            if valid_comps:
                have_any_comps = True
                lib_dict["components"] = {ocpiutil.rchop(os.path.basename(comp), "spec.xml")[:-1]:
                                          comp for comp in valid_comps}
            # in case two or more  libraries have the same package id we update the key to end
            # with a number
            i = 1
            while lib_package in libraries_dict:
                lib_package += ":" + str(i)
                i += 1
            libraries_dict[lib_package] = lib_dict
        return libraries_dict, have_any_tests, have_any_wkrs, have_any_comps

    def _collect_very_verbose_dict(self):
        """
        Generate a dictionary with all the information about a project with verbosity level 2
        """
        have_any_tests = False
        have_any_wkrs = False
        have_any_comps = False
        proj_dict = {}
        top_dict = {}
        top_comp_dict = {}
        libraries_dict, have_any_tests, have_any_wkrs, have_any_comps = (
            self._get_very_verbose_libs_dict())
        for comp in self.comp_list:
            top_comp_dict[comp.name] = comp.directory
        top_dict["components"] = top_comp_dict
        if os.path.isdir(self.directory + "/applications"):
            apps_dict = {}
            for app_col in self.apps_col_list:
                for app in app_col.apps_list:
                    apps_dict[app.name] = app.directory
            top_dict["applications"] = apps_dict

        project_vars = ocpiutil.set_vars_from_make(ocpiutil.get_makefile(self.directory, "project"),
                                                   mk_arg="projectdeps ShellProjectVars=1",
                                                   verbose=True)
        prims_dict = self._get_very_verbose_prims_dict()
        if prims_dict:
            top_dict["primitives"] = prims_dict
        assys_dict = self._get_very_verbose_assemblies_dict()
        if assys_dict:
            top_dict["assemblies"] = assys_dict
        proj_depends = project_vars['ProjectDependencies']
        if not proj_depends:
            proj_depends.append("None")
        top_dict["dependencies"] = proj_depends
        top_dict["directory"] = self.directory
        top_dict["libraries"] = libraries_dict
        top_dict["platforms"] = self._collect_plats_dict()
        top_dict["package"] = self.package_id
        proj_dict["project"] = top_dict
        return proj_dict, have_any_tests, have_any_wkrs, have_any_comps

    def _show_verbose(self, format, **kwargs):
        """
        print out information about the project with verbosity level 1 in the format specified by
        format (simple, table, or json)
        """
        proj_dict = self._collect_verbose_dict()

        if format == "simple":
            print("Project Directory: " + proj_dict["project"]["directory"])
            print("Package-ID: " + proj_dict["project"]["package"])
            print("Project Dependencies: " + ", ".join(proj_dict["project"]["dependencies"]))
            comp_dict = proj_dict["project"].get("components", [])
            comps = []
            for comp in comp_dict:
                comps.append(comp)
            if comp_dict:
                print("Top Level Components: " + ", ".join(comps))
            lib_dict = proj_dict["project"].get("libraries", [])
            for lib in lib_dict:
                print("  Library: " + lib_dict[lib])
        elif format == "table":
            print("Overview:")
            rows = [["Project Directory", "Package-ID", "Project Dependencies"]]
            rows.append([proj_dict["project"]["directory"],
                         proj_dict["project"]["package"],
                         ", ".join(proj_dict["project"]["dependencies"])])
            ocpiutil.print_table(rows, underline="-")
            comp_dict = proj_dict["project"].get("components", [])
            if comp_dict:
                print("Top Level Components:")
                rows = [["Component Name"]]
                for comp in comp_dict:
                    rows.append([comp])
                ocpiutil.print_table(rows, underline="-")
            lib_dict = proj_dict["project"].get("libraries", [])
            if lib_dict:
                print("Libraries:")
                rows = [["Library Directories"]]
                for lib in lib_dict:
                    rows.append([lib_dict[lib]])
                ocpiutil.print_table(rows, underline="-")
        else:
            json.dump(proj_dict, sys.stdout)
            print()

    def _show_very_verbose_simple(self, proj_dict):
        print("Project Directory: " + proj_dict["project"]["directory"])
        print("Package-ID: " + proj_dict["project"]["package"])
        print("Project Dependencies: " + ", ".join(proj_dict["project"]["dependencies"]))
        comp_dict = proj_dict["project"].get("components", [])
        comps = []
        for comp in comp_dict:
            comps.append(comp)
        if comp_dict:
            print("Top Level Components: " + ", ".join(comps))
        prim_dict = proj_dict["project"].get("primitives", [])
        if prim_dict:
            print("  HDL Primitives: " + self.directory + "/hdl/primitives")
        for prim in prim_dict:
            print("    Primitive: " + prim)
        assembly_dict = proj_dict["project"].get("assemblies", [])
        if assembly_dict:
            print("  HDL Assemblies: " + self.directory + "/hdl/assemblies")
        for assy in assembly_dict:
            print("    Assembly: " + assy)
        lib_dict = proj_dict["project"].get("libraries", [])
        for lib in lib_dict:
            print("  Library: " + lib_dict[lib]["directory"])
            test_dict = lib_dict[lib].get("tests", [])
            for test in test_dict:
                print("    Test: " + test)
            wkr_dict = lib_dict[lib].get("workers", [])
            for wkr in wkr_dict:
                print("    Worker: " + wkr)
            comp_dict = lib_dict[lib].get("components", [])
            for comp in comp_dict:
                print("    Component: " + comp)

    def _show_very_verbose_table(self, proj_dict, have_any_tests, have_any_wkrs, have_any_comps):
        """
        Prints out information about a project with verbosity level 2 in table format

        Arguments:
          proj_dict      - dictionary with all the project information
          have_any_tests - Boolean flag denoting if this project has any tests
          have_any_wkrs  - Boolean flag denoting if this project has any workers
          have_any_comps - Boolean flag denoting if this project has any components
        """
        print("Overview:")
        rows = [["Project Directory", "Package-ID", "Project Dependencies"]]
        rows.append([proj_dict["project"]["directory"],
                     proj_dict["project"]["package"],
                     ", ".join(proj_dict["project"]["dependencies"])])
        ocpiutil.print_table(rows, underline="-")
        comp_dict = proj_dict["project"].get("components", [])
        if comp_dict:
            print("Top Level Components:")
            rows = [["Compenent Name"]]
            for comp in comp_dict:
                rows.append([comp])
        ocpiutil.print_table(rows, underline="-")
        prim_dict = proj_dict["project"].get("primitives", [])
        if prim_dict:
            print("Primitives:")
            rows = [["Primitive Directory", "Primitive"]]
            for prim in prim_dict:
                rows.append([self.directory + "/hdl/primitives", prim])
            ocpiutil.print_table(rows, underline="-")
        assembly_dict = proj_dict["project"].get("assemblies", [])
        if assembly_dict:
            print("Assemblies:")
            rows = [["Assembly Directory", "Assembly"]]
            for assy in assembly_dict:
                rows.append([self.directory + "/hdl/assemblies", assy])
            ocpiutil.print_table(rows, underline="-")
        lib_dict = proj_dict["project"].get("libraries", [])
        if lib_dict:
            print("Libraries:")
            rows = [["Library Directories"]]
            for lib in lib_dict:
                rows.append([lib_dict[lib]["directory"]])
            ocpiutil.print_table(rows, underline="-")
        if have_any_tests:
            print("Tests:")
            rows = [["Library Directory", "Test"]]
            lib_dict = proj_dict["project"].get("libraries", [])
            for lib in lib_dict:
                test_dict = lib_dict[lib].get("tests", [])
                for test in test_dict:
                    rows.append([os.path.dirname(ocpiutil.rchop(test_dict[test], "/")), test])
            ocpiutil.print_table(rows, underline="-")
        if have_any_wkrs:
            self._show_libary_workers_table(proj_dict)
        if have_any_comps:
            self._show_libary_comps_table(proj_dict)


    @staticmethod
    def _show_libary_workers_table(proj_dict):
        """
        Prints out the table for any workers that are located in a project
        """
        print("Workers:")
        rows = [["Library Directory", "Worker"]]
        lib_dict = proj_dict["project"].get("libraries", [])
        for lib in lib_dict:
            wkr_dict = lib_dict[lib].get("workers", [])
            for wkr in wkr_dict:
                rows.append([os.path.dirname(ocpiutil.rchop(wkr_dict[wkr], "/")), wkr])
        ocpiutil.print_table(rows, underline="-")

    @staticmethod
    def _show_libary_comps_table(proj_dict):
        """
        Prints out the table for any components that are located in a project
        """
        print("Components:")
        rows = [["Library Directory", "Component"]]
        lib_dict = proj_dict["project"].get("libraries", [])
        for lib in lib_dict:
            comp_dict = lib_dict[lib].get("components", [])
            for comp in comp_dict:
                rows.append([os.path.dirname(ocpiutil.rchop(comp_dict[comp], "/")), comp])
        ocpiutil.print_table(rows, underline="-")

    def _show_very_verbose(self, format, **kwargs):
        """
        Prints out information about a project verbosity level 2 in the format specified by format
        (simple, table, json)
        """
        proj_dict, have_any_tests, have_any_wkrs, have_any_comps = self._collect_very_verbose_dict()

        if format == "simple":
            self._show_very_verbose_simple(proj_dict)
        elif format == "table":
            self._show_very_verbose_table(proj_dict, have_any_tests, have_any_wkrs, have_any_comps)

        else:
            json.dump(proj_dict, sys.stdout)
            print()

    def show(self, format, verbose, **kwargs):
        """
        This method prints out information about the project based on the options passed in as
        kwargs
        valid kwargs handled by this method are:
            json (T/F) - Instructs the method whether to output information in json format or
                         human readable format
            tests (T/F) - Instructs the method whether print out the tests that that exist in
                          this project
        """
        if verbose == 0:
            self._show_non_verbose(format, **kwargs)
        elif verbose == 1:
            self._show_verbose(format, **kwargs)
        elif verbose == 2:
            self._show_very_verbose(format, **kwargs)

    def show_utilization(self):
        """
        Show utilization separately for each library in this project and for all assemblies
        """
        for library in self.lib_list:
            library.show_utilization()

        # if this project has an hdl/platforms directory, show its utilization
        if self.hdlplatforms:
            for hdlplatforms in self.hdlplatforms:
                hdlplatforms.show_utilization()

        # if this project has an hdl/assemblies directory, show its utilization
        if self.hdlassemblies:
            self.hdlassemblies.show_utilization()

    def initialize_registry_link(self):
        """
        If the imports link for the project does not exist, set it to the default project registry.
        Basically, make sure the imports link exists for this project.
        """
        imports_link = self.directory + "/imports"
        if os.path.exists(imports_link):
            logging.info("Imports link exists for project " + self.directory +
                         ". No registry initialization needed")
        else:
            import _opencpi.assets.registry
            # Get the default project registry set by the environment state
            self.set_registry(ocpiregistry.Registry.get_default_registry_dir())

    def set_registry(self, registry=None, verbose=None, **kwargs):
        """
        Set the project registry link for this project. If a registry path is provided,
        set the link to that path. Otherwise, set it to the default registry based on the
        current environment.
        I.e. Create the 'imports' link at the top-level of the project to point to the project
             registry
        """
        import _opencpi.assets.registry
        registry_path = (self.path.joinpath(registry) if registry else
                         ocpiregistry.Registry.get_default_registry_path())
        if not registry_path.is_dir():
            raise OCPIException(f'The specified new registry, "{registry}", is not a directory')

        old_registry = self.registry()
        verbose=True
        if old_registry: # if this project is already associated with a registry
            if str(old_registry.path.resolve()) == str(registry_path.resolve()):
                if verbose:
                    print(f'Warning:  setting the registry for this project to the registry it '+
                          f'is already associated with, "{old_registry.path}", so nothing will '+
                          f'happen.', file=sys.stderr)
                return
            elif old_registry.contains(package_id=self.package_id, directory=self.directory):
                raise OCPIException(f'Since this project is currently registered with the '+
                                    f'registry at "{old_registry.path}", you must first '+
                                    f'unregister the project.\n'+
                                    f'This can be done by running '+
                                    f'"ocpidev unregister project".')
            else:
                if verbose:
                    print(f'Disassociating the project from its current registry at '+
                          f'"{old_registry.path}"', file=sys.stderr)
                self.unset_registry(verbose=verbose, **kwargs)
        else:
            registry = ocpiregistry.Registry(registry_path, verbose=verbose)
            if registry.contains(package_id=self.package_id, directory=self.directory):
                raise OCPIException(f'Since this project is currently registered with the '+
                                    f'registry at "{registry.path}", you must first unregister '+
                                    f'the project.\n'+
                                    f'This can be done by running '+
                                    f'"ocpidev unregister project".')

        imports_link = self.path.joinpath('imports')
        assert not imports_link.exists()
        imports_link.symlink_to(Path(os.path.relpath(registry_path, self.path)))
        if verbose:
            print(f'The registry of the project at "{self.path}" '+
                  f'has been set to the registry at "{registry_path}"', file=sys.stderr)

    def unset_registry(self, verbose=None, **kwargs):
        """
        Unset the project registry link for this project.
        I.e. remove the 'imports' link at the top-level of the project.
        """
        registry = self.registry()
        if not registry:
            if verbose:
                print(f'The project at "{self.path}" is not associated with any registry so '+
                      f'nothing has happened')
            return
        if registry.contains(package_id=self.package_id, directory=self.directory):
            raise OCPIException(f'Since this project is currently registered with the '+
                                f'registry at "{registry.path}", you must first unregister '+
                                f'the project.\n'+
                                f'This can be done by running '+
                                f'"ocpidev unregister project".')
        imports_link = self.path.joinpath('imports')
        imports_link.unlink()
        self.__registry = None
        if verbose:
            print(f'The project at "{self.path}" has been disassociated from its current '+
                  f'registry at "{registry.path}"', file=sys.stderr)

    def refresh(self, **kwargs):
        """
        Generate a new copy of project metadata
        """
        self.check_dirtype("project", self.directory)
        sys.path.append(os.getenv('OCPI_CDK_DIR') + '/scripts/')
        import genProjMetaData

        genProjMetaData.main(self.directory)

    def registry(self):
        """
        This function will return the registry object for this Project instance.
        If the registry is None, it will try to find/construct it first
        """
        if self.__registry is None and self.path.joinpath('imports').exists():
            self.__registry = AssetFactory.get_instance("registry",
                                                        self.get_registry_dir(),
                                                        verbose = self.verbose)
        return self.__registry

    @classmethod
    def collect_projects_from_path(cls):
        """
        Finds all projects in the OCPI_PROJECT_PATH environment variable and in the registry
        """
        project_path = os.environ.get('OCPI_PROJECT_PATH')
        projects_from_env = {}
        if not project_path is None and not project_path.strip() == "":
            projects_from_path = project_path.split(':')
            for proj in projects_from_path:
                proj_package = ocpiutil.get_project_package(proj)
                if proj_package is None:
                    proj_package = os.path.basename(proj.rstrip("/"))
                    proj_exists = False
                else:
                    proj_exists = True
                projects_from_env[proj_package] = {}
                projects_from_env[proj_package]["exists"] = proj_exists
                projects_from_env[proj_package]["registered"] = False
                projects_from_env[proj_package]["real_path"] = os.path.realpath(proj)
        return projects_from_env

    @staticmethod
    def _get_template_dict(name, directory, **kwargs):
        """
        used by the create function/verb to generate the dictionary of viabales to send to the
        jinja2 template.
        valid kwargs handled at this level are:
            package_id     (string)      - Package ID for a project  (used instead of package_prefix
                                           and package_name usually)
            package_prefix (string)      - Package prefix for a project (used instead of package_id
                                           usually)
            package_name   (string)      - Package name for a project  (used instead of package_id
                                           usually)
            comp_lib       (list of str) - Specify ComponentLibraries in Makefile
            xml_include    (list of str) - Specify XmlIncludeDirs in Makefile
            include_dir    (list of str) - Specify IncludeDirs in Makefile
            prim_lib       (list of str) - Specify Libraries in Makefile
            depend         (list of str) - Specify ProjectDependencies in Makefile
        """
        package_id = kwargs.get("package_id", None)
        package_prefix =kwargs.get("package_prefix", None)
        package_name =  kwargs.get("package_name", name)
        comp_lib = kwargs.get("comp_lib", None)
        if comp_lib:
            comp_lib = " ".join(comp_lib)
        xml_include = kwargs.get("xml_include", None)
        if xml_include:
            xml_include = " ".join(xml_include)
        include_dir = kwargs.get("include_dir", None)
        if include_dir:
            include_dir = " ".join(include_dir)
        prim_lib = kwargs.get("prim_lib", None)
        if prim_lib:
            prim_lib = " ".join(prim_lib)
        depend = kwargs.get("depend", None)
        if depend:
            depend = " ".join(depend)

        template_dict = {
            "name" : name,
            "comp_lib" : comp_lib,
            "xml_include" :xml_include,
            "include_dir" : include_dir,
            "prim_lib" : prim_lib,
            "package_id" : package_id,
            "package_name" : package_name,
            "package_prefix" : package_prefix,
            "depend" : depend,
            "determined_package_id" : ocpiutil.get_package_id_from_vars(
                package_id, package_prefix, package_name, name)
        }
        return template_dict

    @staticmethod
    def create(name, directory, register=None, verbose=None, **kwargs):
        """
        Static method that will create a new Project given a name and directory kwargs that are
        handled at this level:
            register (T/F) - if set to true this project is also registered after it is created
        """
        path, name, parent_path = Asset.start_creation(directory, name, 'project', kwargs)
        path.mkdir()
        template_dict = __class__._get_template_dict(name, directory, **kwargs)
        # Generate all the project files using templates
        ocpiutil.write_file_from_string(path.joinpath("Project.exports"), ocpitemplate.PROJ_EXPORTS)
        ocpiutil.write_file_from_string(path.joinpath(".gitignore"), ocpitemplate.PROJ_GIT_IGNORE)
        ocpiutil.write_file_from_string(path.joinpath(".gitattributes"), ocpitemplate.PROJ_GIT_ATTR)
        template = jinja2.Template(ocpitemplate.PROJ_PROJECT_XML, trim_blocks=True)
        ocpiutil.write_file_from_string(path.joinpath("Project.xml"), template.render(**template_dict))
        template = jinja2.Template(ocpitemplate.PROJ_GUI_PROJECT, trim_blocks=True)
        ocpiutil.write_file_from_string(path.joinpath(".project"), template.render(**template_dict))

        if register:
            # To register during creation means you are both associating the project with the
            # default registry and also registering the project in that registry.
            # If you do not register the project during creation, the project remains
            # disassociated from any registry.
            registry_path = ocpiregistry.Registry.get_default_registry_path()
            registry = AssetFactory.get_instance("registry", registry_path, verbose=verbose)
            imports_link = path.joinpath('imports')
            imports_link.symlink_to(Path(os.path.relpath(registry_path, path)))
            registry.add(template_dict['determined_package_id'], path, verbose=verbose,
                         creating=True)
        Asset.finish_creation("project", name, path, verbose)

    def register(self, force=False, verbose=False, **kwargs):
        """
        Register project to registry. Export project if possible.
        """
        registry_dir = ocpiregistry.Registry.get_default_registry_dir()
        AssetFactory.get_instance('registry', registry_dir, verbose=verbose).\
            add(self.package_id, Path(self.directory), force=force, verbose=verbose)

        # Attempt to export project
        is_exported = ocpiutil.is_path_in_exported_project(self.directory)
        if not is_exported:
            make_file = ocpiutil.get_makefile(self.directory, "project")[0]
            rc = ocpiutil.execute_cmd({},
                                      self.directory,
                                      action=['exports'],
                                      file=make_file,
                                      verbose=verbose)
            if rc:
                msg = ' '.join(['Could not export project "{}".'.format(self.name), 
                                'You may not have write permissions on this project.',
                                'Proceeding...'])
                logging.warning(msg)
        elif verbose:
            msg = 'Skipped making exports because this is an exported standalone project'
            logging.warning(msg)

    def unregister(self, force=False, verbose=None, **kwargs):
        """
        Unregister project from registry. If not force, prompts the user first.
        """
        if not force:
            prompt = ' '.join(['Are you sure you want to',
                               'unregister the "{}"'.format(self.name), 
                               'project/package from its project registry?'])
            force = ocpiutil.get_ok(prompt)
        if force:
            registry = self.registry()
            if not registry:
                registry = ocpiregistry.Registry(ocpiregistry.Registry.get_default_registry_dir())
            registry.remove(package_id=self.package_id, directory=self.directory)

    def add_assets(self, asset_type, assets, **kwargs):
        """
        Add to the "assets" list,  the information about child assets of a particular asset type
        """
        assert asset_type in ['hdl-platforms', 'platforms', 'rcc-platforms', 'platforms',
                              'components', 'hdl-targets', 'workers', 'tests', 'libraries']
        if asset_type in ['hdl-platforms', 'platforms']:
            plats = Path(self.directory,"hdl","platforms")
            if plats.is_dir():
                for path in plats.iterdir():
                    if path.is_dir() and ocpiutil.get_dirtype(path) == 'hdl-platform' and \
                       path.joinpath(path.name + ".xml").exists():
                        assets.append(path)
        if asset_type in ['rcc-platforms', 'platforms']:
            plats = Path(self.directory,"rcc","platforms")
            if plats.is_dir():
                for path in plats.iterdir():
                    if path.is_dir() and ocpiutil.get_dirtype(path) == 'rcc-platform' and \
                       path.joinpath(path.name + ".mk").exists():
                        assets.append(path)
        if asset_type == 'components':
            comp_dicts = {}
            lib_options = kwargs.get('library') or kwargs.get('hdl_library') or kwargs.get('platform')
            if kwargs.get('project') or not lib_options: # only those at the project level
                # include top-level specs if asking for them specifically or
                # asking for all components in the project
                specs = Path(self.directory, "specs")
                if specs.is_dir():
                    for entry in specs.iterdir():
                        name = Component.get_component_spec_file(str(entry.name))
                        if name:
                            assets.append((self.directory, name, 'specs/' + entry.name))
            args = kwargs
            args['name'] = None
            args.pop('directory')
            for lib in self.get_valid_libraries(**kwargs):
                library = Library(lib, **args) # use get_instance?
                library.add_assets("components", assets)
        if asset_type in ['workers', 'tests']:
            args = kwargs
            args['name'] = None
            args.pop('directory')
            for lib in self.get_valid_libraries(**kwargs):
                library = Library(lib, **args) # use get_instance?
                library.add_assets(asset_type, assets)
        if asset_type == 'libraries':
            for lib in self.get_valid_libraries(**kwargs):
                assets.append(lib)
        if asset_type == 'hdl-targets':
            _,families,_,_ = ocpiutil.get_hdl_builtins()
            assets_dict=dict(assets)
            # look for platforms that add to the builtin families
            plats = Path(self.directory,"hdl","platforms")
            if plats.is_dir():
                for path in plats.iterdir():
                    if ocpiutil.get_dirtype(path) == 'hdl-platform' and \
                       path.joinpath(path.name + ".xml").exists():
                        attrs = ocpiutil.get_platform_attributes(self.package_id, str(path),
                                                                 path.name, 'hdl')
                        family = attrs['family']
                        part = attrs['part']
                        family_dict = assets_dict.get(family)
                        if not family_dict:
                            family_dict = families.get(family)
                        if not family_dict:
                            # Create a new family based on this platform's info
                            family_dict = { 'name' : family, 'vendor' : attrs['vendor'],
                                            'toolset' : attrs['toolset'],
                                            'parts' : { attrs['part'] : attrs['package_id']},
                                            'platform' : attrs['package_id'] }
                            assets_dict[family] = family_dict; # to avoid dups within this project
                            assets.append((family,family_dict))
                        elif part not in family_dict['parts']:
                            parts = family_dict['parts']
                            if part not in parts:
                                # this platform adds a new part
                                family_dict['parts'][part] = attrs['package_id']

    def get_registry_dir(self):
        return __class__.get_registry_path_from_project_path(self.path)

    @staticmethod
    def get_registry_path_from_project_path(path):

        """
        Determine the project's registry directory. Check for the imports link.
        Otherwise, get the default registry
        Return the exists Boolean and the path to the project registry directory.
        """
        path = Path(path)
        imports_path = path.joinpath('imports')
        if imports_path.is_symlink():
            if imports_path.exists():
                return imports_path.resolve()
            raise OCPIException(f'There is an invalid "imports" symbolic link in this project\'s '+
                                f'directory at "{path}/imports".  It must be removed.  Use '+
                                f'the "set registry" command if you need this project to be '+
                                f'associated with a non-default registry.')
        elif imports_path.exists():
            raise OCPIException(f'There is an invalid "imports" file or directory in this '+
                                f'project\'s directory at "{path}/imports".  It must be '+
                                f'removed.  Use the "set registry" command if you need this '+
                                f'project to be associated with a non-default registry.')
        default_path = Path(ocpiregistry.Registry.get_default_registry_dir())
        if default_path.exists():
            return default_path
        raise OCPIException(f'The default registry directory as determined by the current '+
                            f'environment is "{default_path}", which does not exist.  This '+
                            f'must be fixed by changing or unsetting the '+
                            f'OCPI_PROJECT_REGISTRY_DIR environment variable.')

# pylint:enable=too-many-instance-attributes
# pylint:enable=too-many-ancestors
class ProjectsCollection(ShowableAsset):
    """
    Collection of projects - which is sort of like a registry
    """
    valid_settings = []

    def __init__(self, directory, name=None, verb=None, assets=None, **kwargs):
        self.out_of_project = True
        self.asset_type = 'projects'
        super().__init__(directory, name, **kwargs)
        assert assets != None
        self.projects = []
        for project in assets:
            self.projects.append(Project(project, **kwargs))

    def show(self, format, verbose, **kwargs):
        """
        Show all of the platforms in this collection
        """
        if format == "simple":
            projects = []
            for project in self.projects:
                projects.append(project.package_id)
            print(' '.join(sorted(projects)))
        elif format == "table":
            rows = [["Project Package-ID", "Path to Project"]]
            for project in self.projects:
                rows.append([project.package_id, project.directory])
            ocpiutil.print_table(rows, underline="-")
        elif format == "json":
            projects = {}
            for project in self.projects:
                projects[project.package_id] = { 'real_path' : project.directory, 'exists': True }
            json.dump({ 'registry_location' : self.directory, 'projects' : projects },
                      sys.stdout)
            print()
