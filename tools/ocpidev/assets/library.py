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
Definition of Library and Library collection classes
"""

import os
import logging
import _opencpi.util as ocpiutil
import jinja2
from pathlib import Path
import _opencpi.assets.template as ocpitemplate
import subprocess
import _opencpi.util as ocpiutil
import shutil
from .abstract import RunnableAsset, RCCBuildableAsset, HDLBuildableAsset, ReportableAsset, Asset
from .factory import AssetFactory
from .worker import Worker, HdlWorker

def do_build(asset_type, directory, kwargs):
    """
    Function common to build libraries and library collections
    """
    action=[]
    if kwargs.get('rcc'):
        action.append('rcc')
    if kwargs.get('hdl'):
        action.append('hdl')
    if kwargs.get('workers_as_needed'):
        os.environ['OCPI_AUTO_BUILD_WORKERS'] = '1'

    dynamic = kwargs.get('dynamic')
    optimize = kwargs.get('optimize')
    hdl_platform = kwargs.get('hdl_platform')
    hdl_rcc_platform = kwargs.get('hdl_rcc_platform')
    hdl_target = kwargs.get('hdl_target')
    rcc_platform = kwargs.get('rcc_platform')
    worker = kwargs.get('worker')

    build_suffix = '-'
    if dynamic:
        build_suffix += 'd'
    if optimize:
        build_suffix += 'o'
    if optimize or dynamic:
        if rcc_platform:
            if any("-" in s for s in rcc_platform):
                raise ocpiutil.OCPIException("You cannot use the --optimize build option and "
                + "also specify build options in a platform name (in this case: ",
                rcc_platform, ")")
            else:
                new_list = [s + build_suffix for s in rcc_platform]
                rcc_platform = new_list
        else:
            rcc_platform = [os.environ['OCPI_TOOL_PLATFORM'] + build_suffix]
    #Pass settings
    settings = {}
    if hdl_platform:
        settings['hdl_plat_strs'] = hdl_platform
    if hdl_target:
        settings['hdl_target'] = hdl_target
    if rcc_platform:
        settings['rcc_platform'] = rcc_platform
    if hdl_rcc_platform:
        settings['hdl_rcc_platform'] = hdl_rcc_platform
    if asset_type == 'library' and worker:
        settings['worker'] = worker
    make_file = ocpiutil.get_makefile(directory, asset_type)[0]
    #Build
    ocpiutil.file.execute_cmd(settings, directory, action="", file=make_file,
                              verbose=kwargs.get('verbose'))

def do_clean(asset_type, directory, kwargs):
    """
    Function common to clean libraries and library collections
    """
    #Specify what to clean
    action=[]
    rcc = kwargs.get('rcc')
    hdl = kwargs.get('hdl')
    hdl_platform = kwargs.get('hdl_platform')
    hdl_target = kwargs.get('hdl_target')
    worker = kwargs.get('worker')
    if not rcc and not hdl:
        action.append('clean')
    else:
        if rcc:
            action.append('cleanrcc')
        if hdl:
            action.append('cleanhdl')
    settings = {}
    if hdl_platform:
        settings['hdl_plat_strs'] = hdl_platform
    if hdl_target:
        settings['hdl_target'] = hdl_target
    if worker:
        settings['worker'] = worker
    make_file = ocpiutil.get_makefile(directory, asset_type)[0]
    #Clean
    ocpiutil.file.execute_cmd(settings, directory, action=action, file=make_file,
                              verbose=kwargs.get('verbose'))

class Library(RunnableAsset, RCCBuildableAsset, HDLBuildableAsset, ReportableAsset):
    """
    This class represents an OpenCPI Library.  Contains a list of the tests that are in this
    library and can be initialized or left as None if not needed
    """
    valid_settings = []
    def __init__(self, directory, name=None, **kwargs):
        """
        Initializes Library member data  and calls the super class __init__.  Throws an
        exception if the directory passed in is not a valid library directory.
        valid kwargs handled at this level are:
            init_tests   (T/F) - Instructs the method whether to construct all test objects
                                 contained in the library
            init_workers (T/F) - Instructs the method whether to construct all worker objects
                                 contained in the library
        """
        self.check_dirtype("library", directory)
        if not name:
            name = str(Path(directory).name)
        super().__init__(directory, name, **kwargs)
        self.test_list = None
        self.tests_names = None
        self.wkr_names = None
        self.package_id, self.tests_names, self.wkr_names = (
            self.get_package_id_wkrs_tests(self.directory))
        if kwargs.get("init_tests", False):
            self.test_list = []
            logging.debug("Library constructor creating Test Objects")
            for test_directory in self.tests_names:
                self.test_list.append(AssetFactory.factory("test", test_directory, **kwargs))

        kwargs["package_id"] = self.package_id
        self.worker_list = None
        if kwargs.get("init_workers", False):
            # Collect the list of workers and initialize Worker objects for each worker
            # of a supported authoring model
            self.worker_list = []
            logging.debug("Library constructor creating Worker Objects")
            for worker_directory in self.wkr_names:
                auth = Worker.get_authoring_model(worker_directory)
                if auth not in Asset.valid_authoring_models:
                    logging.debug("Skipping worker \"" + directory +
                                  "\" with unsupported authoring model \"" + auth + "\"")
                else:
                    wkr_name = os.path.splitext(os.path.basename(worker_directory))[0]
                    self.worker_list.append(AssetFactory.factory("worker", worker_directory,
                                                                 name=wkr_name,
                                                                 **kwargs))
        self.comp_list = None
        if kwargs.get("init_comps", False):
            self.comp_list = []
            for comp_directory in self.get_valid_components():
                comp_name = ocpiutil.rchop(os.path.basename(comp_directory), "spec.xml")[:-1]
                self.comp_list.append(AssetFactory.factory("component", comp_directory,
                                                           name=comp_name, **kwargs))

    @staticmethod
    def get_package_id(directory='.'):
        """
        return the package id of the library.  This information is determined from the make build
        system in order to be accurate.
        """
        lib_vars = ocpiutil.set_vars_from_make(ocpiutil.get_makefile(directory, "library"),
                                               mk_arg="ShellLibraryVars=1 showlib",
                                               verbose=True)
        return "".join(lib_vars['Package'])

    def get_package_id_wkrs_tests(self, directory='.'):
        """
        Return the package id of the Library from the make variable that is returned
        """
        lib_vars = ocpiutil.set_vars_from_make(ocpiutil.get_makefile(directory, "library"),
                                               mk_arg="ShellLibraryVars=1 showlib",
                                               verbose=True)
        ret_package = "".join(lib_vars['Package'])
        make_wkrs = lib_vars['Workers'] if lib_vars['Workers'] != [''] else []
        make_tests = lib_vars['Tests'] if lib_vars['Tests'] != [''] else []
        ret_tests = []
        ret_wkrs = []
        for name in make_tests:
            if name != "":
                ret_tests.append(self.directory + "/" + name)
        for name in make_wkrs:
            if name.endswith((".rcc", ".rcc/", ".hdl", ".hdl/")):
                ret_wkrs.append(self.directory + "/" + name)
        return ret_package, ret_tests, ret_wkrs

    def get_valid_tests_workers(self):
        """
        Probe make in order to determine the list of active tests in the library
        """
        # If this function has already been called don't call make again because its very expensive
        if self.tests_names is not None and self.wkr_names is not None:
            return (self.tests_names, self.wkr_names)
        ret_tests = []
        ret_wkrs = []
        mkf=ocpiutil.get_makefile(self.directory,"library")
        ocpiutil.logging.debug("Getting valid tests from: " + mkf)
        make_dict = ocpiutil.set_vars_from_make(mkf,
                                                mk_arg="ShellLibraryVars=1 showlib",
                                                verbose=True)
        make_tests = make_dict["Tests"]
        make_wkrs = make_dict["Workers"]

        for name in make_tests:
            if name != "":
                ret_tests.append(self.directory + "/" + name)
        for name in make_wkrs:
            if name.endswith((".rcc", ".rcc/", ".hdl", ".hdl/")):
                ret_wkrs.append(self.directory + "/" + name)
        self.tests_names = ret_tests
        self.wkr_names = ret_wkrs
        return (ret_tests, ret_wkrs)

    @staticmethod
    def get_workers(directory="."):
        workers = []
        mkf=ocpiutil.get_makefile(directory,"library")
        make_dict = ocpiutil.set_vars_from_make(mkf,
          mk_arg="ShellLibraryVars=1 showlib", verbose=True)
        wkrs = make_dict["Workers"]
        for name in wkrs:
            if name.endswith((".rcc", ".rcc/", ".hdl", ".hdl/")):
                workers.append(name + " ")
        return (workers)

    def run(self):
        """
        Runs the Library with the settings specified in the object.  Throws an exception if the
        tests were not initialized by using the init_tests variable at initialization.  Running a
        Library will run all the component unit tests that are contained in the Library
        """
        ret_val = 0
        if self.test_list is None:
            raise ocpiutil.OCPIException("For a Library to be run \"init_tests\" must be set to " +
                                         "True when the object is constructed")
        for test in self.test_list:
            run_val = test.run()
            ret_val = ret_val + run_val
        return ret_val

    def show_utilization(self):
        """
        Show utilization separately for each HdlWorker in this library
        """
        for worker in self.worker_list:
            if isinstance(worker, HdlWorker):
                worker.show_utilization()

    def clean(self, verbose=False, hdl=False, rcc=False,
        worker=None, hdl_platform=None, hdl_target=None):
        """
        Cleans the library by handing over the user specifications
        to execute command.
        """
        do_clean("library", self.directory, locals())

    def build(self, verbose=False, rcc=False, hdl=False, optimize=False,
        dynamic=False, worker=None, hdl_platform=None, workers_as_needed=False, 
        hdl_target=None, rcc_platform=None, hdl_rcc_platform=None):
        """
        Builds the library by using the common build function for libraries or library collections
        """
        do_build('library', self.directory, locals())

    @staticmethod
    def get_working_dir(name, ensure_exists=True, **kwargs):
        """
        return the directory of a Library given the name (name) and
        library specifiers (library, hdl_library, hdl_platform)
        """
        # if more then one of the library location variables are not None it is an error.
        # a length of 0 means that a name is required and a default location of components/
        library = kwargs.get('library', '')
        hdl_library = kwargs.get('hdl_library', '')
        platform = kwargs.get('platform', '')
        if len(list(filter(None, [library, hdl_library, platform]))) > 1:
            ocpiutil.throw_invalid_libs_e()
        ocpiutil.check_no_libs('library', library, hdl_library, platform)
        if not name:
            ocpiutil.throw_not_blank_e("library", "name", True)

        working_path = Path(ocpiutil.get_path_to_project_top())
        comp_path = Path(working_path, 'components')
        if name != 'components':
            if not comp_path.exists() and not ensure_exists:
                comp_path.mkdir()
            working_path = Path(comp_path, name)
        else:
            working_path = comp_path

        return str(working_path)

    def _get_template_dict(name, directory, **kwargs):
        """
        used by the create function/verb to generate the dictionary of viabales to send to the
        jinja2 template.
        valid kwargs handled at this level are:
            package_id     (string)      - Package for a project  (used instead of package_prefix
                                           and package_name usually)
            package_prefix (string)      - Package prefix for a project (used instead of package_id
                                           usually)
            package_name   (string)      - Package name for a project  (used instead of package_id
                                           usually)
            comp_lib       (list of str) - Specify ComponentLibraries in Makefile
            xml_include    (list of str) - Specify XmlIncludeDirs in Makefile
            include_dir    (list of str) - Specify IncludeDirs in Makefile
            prim_lib       (list of str) - Specify Libraries in Makefile
        """
        package_id = kwargs.get("package_id", None)
        package_prefix =kwargs.get("package_prefix", None)
        package_name =  kwargs.get("package_name", None)
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
        template_dict = {
                        "name" : name,
                        "comp_lib" : comp_lib,
                        "xml_include" :xml_include,
                        "include_dir" : include_dir,
                        "prim_lib" : prim_lib,
                        "package_id" : package_id,
                        "package_name" : package_name,
                        "package_prefix" : package_prefix,
                        "determined_package_id" : ocpiutil.get_package_id_from_vars(package_id,
                                                                                    package_prefix,
                                                                                    package_name, directory)
                        }
        return template_dict

    @staticmethod
    def create(name, directory, **kwargs):
        """
        Create library asset
        """
        verbose = kwargs.get("verbose", None)
        lib_path = Path(directory, name)
        if lib_path.exists():
            err_msg = 'library "{}" already exists at "{}"'.format(name, str(lib_path))
            raise ocpiutil.OCPIException(err_msg)

        template_dict = Library._get_template_dict(name, directory, **kwargs)
        compdir = Path(ocpiutil.get_path_to_project_top(), "components")
        if not compdir.exists():
            compdir.mkdir()
        os.chdir(str(compdir))
        template = jinja2.Template(ocpitemplate.LIBRARIES_XML, trim_blocks=True)
        ocpiutil.write_file_from_string("components.xml", template.render(**template_dict))

        if not lib_path.exists():
            lib_path.mkdir()
        os.chdir(str(lib_path))
        template = jinja2.Template(ocpitemplate.LIB_DIR_XML, trim_blocks=True)
        ocpiutil.write_file_from_string(name + ".xml", template.render(**template_dict))
        workers = str(Library.get_workers())[1:-1] + "\n"
        package_id = Library.get_package_id() + "." + name
        logging.debug("Workers: " + workers + "Package_ID: " + package_id)
        if verbose:
            print("Created library '" + name + "' at " + str(lib_path))


class LibraryCollection(RunnableAsset, RCCBuildableAsset, HDLBuildableAsset, ReportableAsset):
    """
    This class represents an OpenCPI Library Collection.  Contains a list of the libraries that
    are in this library collection and can be initialized or left as None if not needed
    """
    def __init__(self, directory, name=None, **kwargs):
        self.check_dirtype("libraries", directory)
        super().__init__(directory, name, **kwargs)
        self.verbose = kwargs.get("verbose", None)
        self.orig_noun = kwargs.get("orig_noun", None)
        self.library_list = None
        if kwargs.get("init_libs_col", False):
            self.library_list = []
            logging.debug("LibraryCollection constructor creating Library Objects")
            for lib in next(os.walk(directory))[1]:
                lib_directory = directory + "/" + lib
                self.library_list.append(AssetFactory.factory("library", lib_directory, **kwargs))

    @staticmethod
    def get_working_dir(name, ensure_exists=True, **kwargs):
        """
        return the directory of the Libraries given the name (name) and
        libraries specifiers (library, hdl_library, hdl_platform)
        """
        # if more then one of the library location variables are not None it is an error.
        # a length of 0 means that a name is required and a default location of components/
        libraries = kwargs.get('library', '')
        hdl_library = kwargs.get('hdl_library', '')
        platform = kwargs.get('platform', '')
        if len(list(filter(None, [libraries, hdl_library, platform]))) > 1:
            ocpiutil.throw_invalid_libs_e()
        ocpiutil.check_no_libs('libraries', libraries, hdl_library, platform)
        if not name:
            ocpiutil.throw_not_blank_e('libraries', 'name', True)

        working_path = Path(ocpiutil.get_path_to_project_top())
        comp_path = Path(working_path, 'components')
        if name != 'components':
            if not comp_path.exists() and not ensure_exists:
                comp_path.mkdir()
            working_path = Path(comp_path, name)
        else:
            working_path = comp_path

        return str(working_path)

    def run(self):
        """
        Runs the Library with the settings specified in the object.  Throws an exception if the
        tests were not initialized by using the init_tests variable at initialization.  Running a
        Library will run all the component unit tests that are contained in the Library
        """
        ret_val = 0
        for lib in self.library_list:
            run_val = lib.run()
            ret_val = ret_val + run_val
        return ret_val

    def show_utilization(self):
        """
        Show utilization separately for each library
        """
        for lib in self.library_list:
            lib.show_utilization()

    def clean(self, verbose=False, hdl=False, rcc=False,
        worker=None, hdl_platform=None, hdl_target=None):
        """
        Cleans the libraries
        """
        do_clean("libraries", self.directory, locals())

    def build(self, verbose=False, rcc=False, hdl=False, optimize=False,
        dynamic=False, worker=None, hdl_platform=None, workers_as_needed=False, 
        hdl_target=None, rcc_platform=None, hdl_rcc_platform=None):
        """
        Builds the library by using the common build function for libraries or library collections
        """
        do_build('libraries', self.directory, locals())

    def delete_all(self):
        projdir = Path(ocpiutil.get_path_to_project_top())
        os.chdir(projdir)
        shutil.rmtree(self.directory)
        print("Successfully deleted all libraries and directory:", self.directory)

    def delete(self, force=False):
        if self.orig_noun == "libraries":
            for lib in self.library_list:
               lib.delete(self, force)
            if not force:
                prompt = 'Delete {} at: {}'.format(self.name, str(self.directory))
                force = ocpiutil.get_ok(prompt=prompt)
            if force:
                LibraryCollection.delete_all(self)
            return

        libs = []
        for lib in self.library_list:
            libs.append(lib.name.strip())
        tense = "library exists:" if len(libs) == 1 else "libraries exist:"
        if self.orig_noun == "library" and self.library_list and not force:
            print("OCPI:ERROR: cannot delete 'components' because the following ", end="")
            print(tense, str(libs)[1:-1])
            exit(1)
        if not os.path.isdir(self.directory):
            print("OCPI:ERROR: no such directory:", self.directory)
            exit(1)
        LibraryCollection.delete_all(self)
