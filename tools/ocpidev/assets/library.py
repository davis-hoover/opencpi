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
from .abstract import RunnableAsset, RCCBuildableAsset, HDLBuildableAsset, ReportableAsset, Asset
from .factory import AssetFactory
from .worker import Worker, HdlWorker

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

    def build(self):
        """
        This is a placeholder function will be the function that builds this Asset
        """
        raise NotImplementedError("Library.build() is not implemented")

    @staticmethod
    def get_working_dir(name, library, hdl_library, hdl_platform):
        """
        return the directory of a Library given the name (name) and
        library specifiers (library, hdl_library, hdl_platform)
        """
        # if more then one of the library location variables are not None it is an error.
        # a length of 0 means that a name is required and a default location of components/
        if len(list(filter(None, [library, hdl_library, hdl_platform]))) > 1:
            ocpiutil.throw_invalid_libs_e()
        if name: ocpiutil.check_no_libs("library", library, hdl_library, hdl_platform)
        if library:
            return "components/" + library
        elif hdl_library:
            return "hdl/" + hdl_library
        elif hdl_platform:
            return "hdl/platforms/" + hdl_platform + "/devices"
        elif name:
            if name != "components" and ocpiutil.get_dirtype() != "libraries":
                name = "components/" + name
            return name
        else:
            ocpiutil.throw_specify_lib_e()

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
            "determined_package_id" : ocpiutil.get_package_id_from_vars(
                package_id, package_prefix, package_name, directory)
        }
        
        return template_dict

    @staticmethod
    def create(name, directory, **kwargs):
        """
        Create library assets
        """
        if not name:
           raise ocpiutil.OCPIException("Creating a library asset requires a name")
        dirtype = ocpiutil.get_dirtype(directory)
        if dirtype != "project" and dirtype != "libraries":
           raise ocpiutil.OCPIException(directory + " must be a project or components directory")

        if dirtype == "project":
            compdir = directory + "/components/"
            if not os.path.isdir(compdir):
                os.mkdir(compdir) 
            os.chdir(compdir)

        currdir = os.getcwd()
        currtype = ocpiutil.get_dirtype(currdir)
        if not currtype == "libraries":
            raise ocpiutil.OCPIException(currdir + " must be of type libraries")
        compdir = currdir
        libdir = currdir + "/" + name
        Library.make_library(libdir, name, **kwargs)


    @staticmethod
    def make_library(directory, name, **kwargs):
        directory_path = Path(directory)
        if not directory_path.exists():
            directory_path.mkdir()
        else:
            raise ocpiutil.OCPIException(str(directory_path) + " already exists.")
        template_dict = Library._get_template_dict(name, directory_path.parent, **kwargs)
        # if not os.path.exists(compdir + "/Makefile"):
        #     template = jinja2.Template(ocpitemplate.LIB_MAKEFILE, trim_blocks=True)
        #     ocpiutil.write_file_from_string("Makefile", template.render(**template_dict))
        os.chdir(str(directory))
        # template = jinja2.Template(ocpitemplate.LIB_DIR_MAKEFILE, trim_blocks=True)
        # ocpiutil.write_file_from_string("Makefile", template.render(**template_dict))
        template = jinja2.Template(ocpitemplate.LIB_DIR_XML, trim_blocks=True)
        ocpiutil.write_file_from_string(name + ".xml", template.render(**template_dict))
        # subprocess.check_call('make')
        cdkdir = os.environ.get('OCPI_CDK_DIR')
        metacmd = cdkdir + "/scripts/genProjMetaData.py " + directory
        os.system(metacmd)


class LibraryCollection(RunnableAsset, RCCBuildableAsset, HDLBuildableAsset, ReportableAsset):
    """
    This class represents an OpenCPI Library Collection.  Contains a list of the libraries that
    are in this library collection and can be initialized or left as None if not needed
    """
    def __init__(self, directory, name=None, **kwargs):
        self.check_dirtype("libraries", directory)
        super().__init__(directory, name, **kwargs)
        self.library_list = None
        if kwargs.get("init_libs_col", False):
            self.library_list = []
            logging.debug("LibraryCollection constructor creating Library Objects")
            for lib in next(os.walk(directory))[1]:
                lib_directory = directory + "/" + lib
                self.library_list.append(AssetFactory.factory("library", lib_directory, **kwargs))

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

    def build(self):
        """
        This is a placeholder function will be the function that builds this Asset
        """
        raise NotImplementedError("LibraryCollection.build() is not implemented")
