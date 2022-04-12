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

import os,sys
import logging
import _opencpi.util as ocpiutil
import jinja2
import json
from pathlib import Path
import _opencpi.assets.template as ocpitemplate
import _opencpi.util as ocpiutil
import shutil
from .abstract import RunnableAsset, RCCBuildableAsset, HDLBuildableAsset, ReportableAsset, Asset
from .factory import AssetFactory
from .worker import Worker, HdlWorker
from .component import Component


class Library(RunnableAsset, RCCBuildableAsset, HDLBuildableAsset, ReportableAsset):
    """
    This class represents an OpenCPI Library.  Contains a list of the tests that are in this
    library and can be initialized or left as None if not needed
    """
    valid_settings = []
    def __init__(self, directory, name=None, verb=None, **kwargs):
        """
        Initializes Library member data  and calls the super class __init__.  Throws an
        exception if the directory passed in is not a valid library directory.
        """
        super().__init__(directory, name, **kwargs)
        self.check_dirtype("library", self.directory)
        self.test_list = None
        self.tests_names = None
        self.wkr_names = None
        self.package_id, self.tests_names, self.wkr_names = (
            self.get_package_id_wkrs_tests(self.directory))
        self.make_type = 'library'

        kwargs["package_id"] = self.package_id
        if verb in ['show', 'run']:
            self.test_list = []
            logging.debug("Library constructor creating Test Objects")
            for test_directory in self.tests_names:
                kwargs['name'] = None
                kwargs['child_path'] = None
                self.test_list.append(AssetFactory.factory("test", test_directory, **kwargs))
        self.worker_list = None
        self.comp_list = None
        kwargs.pop('name', None)
        kwargs.pop('child_path', None)
        if verb in ['show', 'utilization']:
            # Collect the list of workers and initialize Worker objects for each worker
            # of a supported authoring model
            self.worker_list = []
            logging.debug("Library constructor creating Worker Objects")
            for worker_directory in self.wkr_names:
                worker_path = Path(worker_directory)
                auth = Worker.get_authoring_model(worker_directory)
                if auth not in Asset.valid_authoring_models:
                    logging.debug("Skipping worker \"" + directory +
                                  "\" with unsupported authoring model \"" + auth + "\"")
                else:
                    asset_type = ocpiutil.get_dir_info(worker_path)[1]
                    self.worker_list.append(AssetFactory.factory(asset_type,
                                                                 str(worker_path.parent),
                                                                 name=worker_path.name, **kwargs))
            self.comp_list = []
            for comp_directory in self.get_valid_components():
                comp_name = ocpiutil.rchop(os.path.basename(comp_directory), "spec.xml")[:-1]
                self.comp_list.append(AssetFactory.factory("component", comp_directory, **kwargs))


    @classmethod
    def resolve_child(cls, parent_path, asset_type, args):
        """
        Resolve the actual relative path and name for a child asset as needed
        Here is the knowledge of where various assets live inside a library
        """
        assert asset_type.endswith('worker') or asset_type in ['component', 'protocol', 'hdl-slot',
                                                               'hdl-card', 'hdl-device', 'test']
        name = args.name
        args.child_path = Path(name) # default is asset name is dir name
        if asset_type in ['component', 'protocol', 'hdl-slot', 'hdl-card']: # file-based assets
            if name.endswith(".xml"):
                name = name[:-4]
            suffixes = {'component':['_spec','-spec'],
                        'protocol': ['_prot', '-prot']}.get(asset_type)
            if suffixes and name[-5:] in suffixes:
                args.child_path = Path("specs", name + ".xml")
                name = name[:-5]
            elif asset_type == 'component':
                if Path(parent_path, 'specs', name + '_spec.xml').exists():
                    args.child_path = Path('specs', name + '_spec.xml')
                elif Path(parent_path, 'specs', name + '-spec.xml').exists() or args.file_only:
                    args.child_path = Path("specs", name + '-spec.xml')
                else:
                    args.child_path = Path(name + '.comp')
            elif asset_type == 'protocol':
                if Path(parent_path, 'specs', name + '_prot.xml').exists():
                    args.child_path = Path('specs', name + '_prot.xml')
                else:
                    args.child_path = Path('specs', name + '-prot.xml')
            else: # slots and cards have no suffix
                args.child_path = Path('specs', name + '.xml')
        elif asset_type.endswith('worker') or asset_type == 'hdl-device':
            pass
        elif asset_type == 'test':
            if name.endswith('.test'):
                name = name[:-5]
            args.child_path = Path(name + '.test')
        args.name = name

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

    def run(self, **kwargs):
        """
        Runs the Library with the settings specified in the object.  Throws an exception if the
        tests were not initialized at initialization.  Running a
        Library will run all the component unit tests that are contained in the Library
        """
        ret_val = 0
        if self.test_list is None:
            raise ocpiutil.OCPIException('For a Library to be run it must use the "run" verb ' +
                                         'when the object is constructed')
        for test in self.test_list:
            run_val = test.run(**kwargs)
            ret_val = ret_val + run_val
        return ret_val

    def show_utilization(self):
        """
        Show utilization separately for each HdlWorker in this library
        """
        for worker in self.worker_list:
            if isinstance(worker, HdlWorker):
                worker.show_utilization()

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
                        "determined_package_id" :
                          ocpiutil.get_package_id_from_vars(package_id, package_prefix,
                                                            package_name, name)
                        }
        return template_dict

    @staticmethod
    def create(name, directory, verbose=None, **kwargs):
        """
        Create library asset
        """
        lib_path, name, parent_path = Asset.start_creation(directory, name, 'library', kwargs)
        if name != 'components' and not lib_path.parent.exists():
            libs_path = lib_path.parent
            libs_path.mkdir(parents=True)
            template = jinja2.Template(ocpitemplate.LIBRARIES_XML, trim_blocks=True)
            ocpiutil.write_file_from_string(libs_path.joinpath(libs_path.name + '.xml'),
                                                               template.render({}))
        lib_path.mkdir(parents=True)
        template_dict = Library._get_template_dict(name, directory, **kwargs)
        template = jinja2.Template(ocpitemplate.LIB_DIR_XML, trim_blocks=True)
        ocpiutil.write_file_from_string(lib_path.joinpath(name + ".xml"),
                                        template.render(**template_dict))
        subdir_path = lib_path.joinpath('lib')
        subdir_path.mkdir()
        ocpiutil.write_file_from_string(subdir_path.joinpath('package-id'),
                                        __class__.get_package_id(lib_path))
        ocpiutil.write_file_from_string(subdir_path.joinpath("workers"), '\n')
        Asset.finish_creation('library', name, lib_path, verbose)

    def add_assets(self, asset_type, assets, **kwargs):
        """
        Add to the "assets" list for assets in this library
        """
        my_path = Path(self.directory)
        if asset_type == 'components':
            specs_path = my_path.joinpath("specs")
            if specs_path.exists():
                for spec in specs_path.iterdir():
                    name = Component.get_component_spec_file(str(spec))
                    if name:
                        assets.append((self.directory, name, 'specs/' + spec.name))
            for comp in my_path.glob('*.comp'):
                spec_path = comp.joinpath(comp.stem + '-spec.xml')
                if spec_path.exists():
                    assets.append((self.directory, comp.name.split('.')[0], comp.name))
        elif asset_type == 'workers':
            for wkr in self.wkr_names:
                assets.append((wkr,self.package_id))
        elif asset_type == 'tests':
            for test in self.tests_names:
                assets.append((test, self.package_id)) # test directory and library package_id

class LibrariesCollection(RunnableAsset, RCCBuildableAsset, HDLBuildableAsset, ReportableAsset):
    """
    This class represents an OpenCPI Library Collection.  Contains a list of the libraries that
    are in this library collection and can be initialized or left as None if not needed
    """
    def __init__(self, directory, name=None, orig_noun=None, verb=None, verbose=None,
                 assets=None, **kwargs):
        if assets != None:
            self.out_of_project = True
        super().__init__(directory, name, **kwargs)
        self.make_type = 'libraries'
        self.orig_noun = orig_noun
        self.libraries = None
        if assets:
            self.libraries = []
            for library in assets:
                self.libraries.append(Library(library, verb=verb, verbose=verbose))
        else:
            self.check_dirtype("libraries", self.directory)
            if verb in ['run', 'utilization', 'show']:
                self.libraries = []
                logging.debug("LibrariesCollection constructor creating Library Objects")
                for subdir in Path(self.directory).iterdir():
                    if subdir.is_dir() and ocpiutil.get_dirtype(subdir) == 'library':
                        self.libraries.append(Library(str(subdir), verb=verb,
                                                      verbose=verbose, **kwargs))

    @staticmethod
    def create(name, directory, verbose=None, **kwargs):
        """
        Create library collection (directory of libraries)
        """
        libs_path, name, parent_path = Asset.start_creation(directory, name, 'libraries', kwargs)
        libs_path.mkdir()
        template = jinja2.Template(ocpitemplate.LIBRARIES_XML, trim_blocks=True)
        ocpiutil.write_file_from_string(libs_path.joinpath(libs_path.name + '.xml'),
                                        template.render({}))
        Asset.finish_creation('libraries', name, libs_path, verbose)

    def add_assets(self, asset_type, assets, **kwargs):
        """
        Add to the "assets" list for the given asset type
        For assets in libraries, add the assets for all libraries in the collection.
        """
        assert asset_type in ['library','components', 'workers', 'tests']
        for lib in self.libraries:
            if asset_type == 'library':
                assets.append(Path(lib.directory))
            else:
                lib.add_assets(asset_type, assets, **kwargs)

    def run(self, **kwargs):
        """
        Runs the Library with the settings specified in the object.  Throws an exception if the
        tests were not initialized by using the init_tests variable at initialization.  Running a
        Library will run all the component unit tests that are contained in the Library
        """
        ret_val = 0
        for lib in self.libraries:
            run_val = lib.run(**kwargs)
            ret_val = ret_val + run_val
        return ret_val

    def show_utilization(self):
        """
        Show utilization separately for each library
        """
        for lib in self.libraries:
            lib.show_utilization()

    def show(self, format=None, **kwargs):
        """
        Show all of the libraries in the collection
        """
        """
        Print out all the libraries that are in this project in the format specified by format
        (simple, table, or json)
        """
        json_dict = {}
        project_dict = {}
        libraries_dict = {}
        if ocpiutil.get_dirtype(self.directory) == 'library':
            lib_directories = [ self.directory ]
        else:
            lib_directories = []
            my_path = Path(self.directory)
            for entry in my_path.iterdir():
                if entry.is_dir() and ocpiutil.get_dirtype(str(entry)) == 'library':
                    lib_directories.append(str(entry))
        for lib_directory in lib_directories:
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

        if format == "simple":
            for lib,dict in libraries_dict.items():
                print("Library: " + dict["directory"])
        elif format == "table":
            rows = [["Library Directories"]]
            for lib,dict in libraries_dict.items():
                rows.append([dict["directory"]])
            ocpiutil.print_table(rows, underline="-")
        else:
            json.dump(libraries_dict, sys.stdout)
            print()

    def delete_all(self):
        projdir = Path(ocpiutil.get_path_to_project_top())
        os.chdir(projdir)
        shutil.rmtree(self.directory)
        print("Successfully deleted all libraries and directory:", self.directory)

    def delete(self, force=False, **kwargs):
        if self.orig_noun == "libraries":
            for lib in self.libraries:
               lib.delete(self, force)
            if not force:
                prompt = 'Delete {} at: {}'.format(self.name, str(self.directory))
                force = ocpiutil.get_ok(prompt=prompt)
            if force:
                LibrariesCollection.delete_all(self)
            return

        libs = []
        for lib in self.libraries:
            libs.append(lib.name.strip())
        tense = "library exists:" if len(libs) == 1 else "libraries exist:"
        if self.orig_noun == "library" and self.libraries and not force:
            print("OCPI:ERROR: cannot delete 'components' because the following ", end="")
            print(tense, str(libs)[1:-1])
            exit(1)
        if not os.path.isdir(self.directory):
            print("OCPI:ERROR: no such directory:", self.directory)
            exit(1)
        LibrariesCollection.delete_all(self)
