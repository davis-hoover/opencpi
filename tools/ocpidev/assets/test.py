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
Definition of Test class
"""

from fnmatch import fnmatch
from itertools import product
import jinja2
import json
import os
from pathlib import Path
import sys
from typing import List
import xml.etree.ElementTree as ET
import _opencpi.util as ocpiutil
import _opencpi.assets.template as ocpitemplate
from .abstract import RunnableAsset, HDLBuildableAsset, RCCBuildableAsset,Asset
from .factory import AssetFactory

class Test(RunnableAsset, HDLBuildableAsset, RCCBuildableAsset):
    """
    This class represents an OpenCPI Component Unit test.  Contains build/run settings that are
    specific to Tests.
    """
    valid_settings = ["keep_sims", "acc_errors", "cases", "verbose", "remote_test_sys", "view", "phase"]
    def __init__(self, directory, name=None, keep_simulations=None, view=None, accumulate_errors=None,
                 case=None, mode=None, phase=None, remote_test_sys=None, package_id=None, **kwargs):
        """
        Initializes Test member data  and calls the super class __init__. Throws an exception if
        the directory passed in is not a valid test directory.
        valid kwargs handled at this level are:
            keep_sims (T/F) - Keep HDL simulation files for any simulation platforms
            acc_errors (T/F) - Causes errors to accumulate and tests to continue on
            cases (list) - Specify Which test cases that will be run/verified
            mode (list) - Specify which phases of the unit test to run
            remote_test_sys (list) - Specify remote systems to run the test(s)
        """
        self.asset_type = 'test'
        super().__init__(directory, name, **kwargs)
        if not kwargs.get('child_path') and not self.directory.endswith('.test'):
            self.directory += '.test'
        self.name = self.name.split('.')[0] # test names do not include the .test
        if not self.directory.endswith(".test"):
            raise ocpiutil.OCPIException("Invalid location for test asset:  " + self.directory)
        self.package_id = package_id
        self.keep_sims = keep_simulations
        self.view = view
        self.acc_errors = accumulate_errors
        self.cases = case
        self.mode = mode if mode else 'all'
        self.phases = phase if phase else []
        if self.mode == "all":
            # convert user-friendly phase into "modes" if --mode is default
            prepare = "prepare" in self.phases
            run = "run" in self.phases
            verify = "verify" in self.phases
            view = "view" in self.phases
            if not prepare and not run and not verify:
                if view:
                    self.mode = "view"
                else:
                    self.mode = "prep_run_verify"
            elif prepare and not run and not verify:
                self.mode = "prep"
            elif not prepare and run and not verify:
                self.mode = "run"
            elif not prepare and not run and verify:
                self.mode = "verify"
            elif prepare and run and not verify:
                self.mode = "prep_run"
            elif not prepare and run and verify:
                self.mode = "run_verify"
            elif prepare and run and verify:
                self.mode = "prep_run_verify"
            else:
                raise ocpiutil.OCPIException("Invalid phases: " + " ".join(self.phases))
        self.remote_test_sys = remote_test_sys
    
        # using the make target "all" instead of "build" so that old style unit tests wont blow up
        # "all" and "build" will evaluate to the functionality
        self.mode_dict = {}
        # pylint:disable=bad-whitespace
        #TODO this should probably be a single statement to create the dictionary
        #     in place (this is slightly faster)
        self.mode_dict['gen_build']       = ["all"]
        self.mode_dict['prep_run_verify'] = ["run"]
        self.mode_dict['clean_all']       = ["clean"]
        self.mode_dict['prep']            = ["prepare"]
        self.mode_dict['run']             = ["runnoprepare"]
        self.mode_dict['prep_run']        = ["runonly"]
        self.mode_dict['run_verify']      = ["runverify"]
        self.mode_dict['verify']          = ["verify"]
        self.mode_dict['view']            = ["view"]
        self.mode_dict['gen']             = ["generate"]
        self.mode_dict['clean_run']       = ["cleanrun"]
        self.mode_dict['clean_sim']       = ["cleansim"]
        self.mode_dict['all']             = ["all", "run"]
        # pylint:enable=bad-whitespace
        xml_path = Path(self.directory, f'{Path(self.directory).stem}-test.xml')
        makefile = Path(self.directory, 'Makefile')
        self.exclude_platforms = []
        self.only_platforms = []
        self.exclude_workers = []
        self.only_workers = []
        if xml_path.exists():
            root = ET.parse(str(xml_path)).getroot()
            attribs = {key.lower(): val for key, val in root.attrib.items()}
            # spec name is spec attribute if exists; else test name
            self.spec_name = attribs.get('spec', self.name).split('.')[-1]
            self.exclude_platforms += attribs.get('excludeplatforms', '').split()
            self.only_platforms += attribs.get('onlyplatforms', '').split()
            self.exclude_workers += attribs.get('excludeworkers', '').split()
            self.only_workers += attribs.get('onlyworkers', '').split()
        else:
            self.spec_name = self.name.split('.')[-1]
        if makefile.exists():
            self.only_platforms += ocpiutil.get_val_from_make(
                makefile, 'OnlyPlatforms', delim=' ') or []
            self.exclude_platforms += ocpiutil.get_val_from_make(
                makefile, 'ExcludePlatforms', delim=' ') or []
            self.only_workers += ocpiutil.get_val_from_make(
                makefile, 'OnlyWorkers', delim=' ') or []
            self.exclude_workers += ocpiutil.get_val_from_make(
                makefile, 'ExcludeWorkers', delim=' ') or []

    def run(self, verbose=False, **kwargs):
        """
        Runs the Test with the settings specified in the object
        """
        goal = self.mode_dict[self.mode]
        if self.mode != "view" and (self.view or "view" in self.phases):
            goal.append("view")
        directory = str(Path(self.directory))
        make_file = ocpiutil.get_makefile(directory, "test")[0]
        make_file = str(Path(directory, make_file).resolve())
        settings = self.get_settings()
        settings['nothing_error'] = kwargs.get('nothing_error', False)
        return ocpiutil.execute_cmd(settings,
                                    directory,
                                    goal,
                                    file=make_file,
                                    verbose=verbose)

    def _get_template_dict(name, directory, **kwargs):
        """
        used by the create function/verb to generate the dictionary of viabales to send to the
        jinja2 template.
        valid kwargs handled at this level are:
            test            (string)      - Test name
        """
        template_dict = {
                        "test" : name,
                        }
        return template_dict

    @staticmethod
    def create(name, directory, verbose=None, **kwargs):
        """
        Create a test in the given parent directory with the given name
        """
        assert '.' not in name # check against legacy callers
        test_path = Path(directory, name + '.test')
        test_path.mkdir()
        for template,file in [[ocpitemplate.TEST_GENERATE_PY, 'generate.py'],
                              [ocpitemplate.TEST_VERIFY_PY, 'verify.py'],
                              [ocpitemplate.TEST_VIEW_SH, 'view.sh'],
                              [ocpitemplate.TEST_NAME_TEST_XML, name + '-test.xml']]:
            template = jinja2.Template(template, trim_blocks=True)
            ocpiutil.write_file_from_string(test_path.joinpath(file), template.render(test=name))
        Asset.finish_creation('test', name, test_path, verbose)

    def _is_valid_platform(self, platform) -> bool:
        """Determines whether a platform is valid for the test.

        Validity is determined by both ensuring the specified platform 
        is not in the test's list of platforms to exclude as well as 
        ensuring that, if the test has a list of platforms to include,
        that the specified platform is contained within said list. Uses
        fnmatch to compare the platform to the test's inclusion and
        exclusion lists since they can contain patterns such as 
        wildcards.

        Args:
            platform: The Platform to validate.
        Returns:
            Bool indicating whether the platform is valid for the test.
        """
        if any([fnmatch(platform.name, exclude) for exclude in self.exclude_platforms]):
            ocpiutil.logging.debug(f'Platform "{platform.name}" excluded by test "{self.name}"')
            return False
        elif self.only_platforms and not any([fnmatch(platform.name, include) 
                                        for include in self.only_platforms]):
            ocpiutil.logging.debug(f'Platform "{platform.name}" not included by test "{self.name}"')
            return False
        return True
            
    def _is_valid_worker(self, worker) -> bool:
        """Determines whether a worker is valid for the test.

        Validity is determined by comparing the worker's spec to the
        test's spec, by ensuring the specified worker is not in the 
        test's list of workers to exclude, and by ensuring that, if the 
        test has a list of workers to include, that the specified worker 
        is contained within said list.

        Args:
            worker: The Worker to validate.
        Returns:
            Bool indicating whether the worker is valid for the test.
        """
        if not worker.spec_name == self.spec_name or not worker.parent == self.parent:
            return False
        if worker.name in self.exclude_workers:
            ocpiutil.logging.debug(f'Worker "{worker.name}" excluded by test "{self.name}"')
            return False
        if self.only_workers and worker.name not in self.only_workers:
            ocpiutil.logging.debug(f'Worker "{worker.name}" not included by test "{self.name}"')
            return False
        return True

class TestsCollection(RunnableAsset, HDLBuildableAsset, RCCBuildableAsset):
    """
    This class represents an OpenCPI Component Unit test. Contains build/run settings that are
    specific to Tests.
    """
    valid_settings = []
    def __init__(self, directory, name=None, assets=None, **kwargs):
        if assets != None:
            self.out_of_project = True
        self.asset_type = 'tests'
        super().__init__(directory, name, **kwargs)
        self.tests = []
        if assets != None:
            for test_dir, parent_package_id in assets:
                test_name = Path(test_dir).stem
                package_id = f'{parent_package_id}.tests.{test_name}'
                self.tests.append(Test(test_dir, None, package_id=package_id))
        else:
            path = Path(self.directory)
            project_package = ocpiutil.get_project_package(self.directory)
            package_id = f'{project_package}.{path.name}.tests.{{}}'
            for subdir in path.iterdir():
                if subdir.is_dir() and subdir.name != 'specs':
                    dirtype = ocpiutil.get_dirtype(subdir)
                    if dirtype == 'test' and subdir.joinpath(f'{subdir.stem}-test.xml').exists():
                        self.tests.append(Test(str(subdir), 
                                               None, 
                                               package_id=package_id.format(subdir.stem), 
                                               **kwargs))

    def get_valid_tests(self):
        """
        Gets a list of all directories of type tests in the library and puts that
        tests directory and the basename of that directory into a dictionary to return
        """
        return ocpiutil.get_subdirs_of_type("test", self.directory)

    def run(self, **kwargs):
        """
        Runs the tests by handing over the user specifications
        to run each test.
        """
        ret_val = 0
        for test in self.tests:
            run_val = test.run(**kwargs)
            ret_val = ret_val + run_val
        return ret_val

    def clean(self, verbose=False, simulation=False, execute=False, **kwargs):
        """
        Cleans the library by handing over the user specifications
        to execute command.
        """
        #Specify what to clean
        action=[]
        if simulation:
            action.append('cleansim')
        elif execute:
            action.append('cleanrun')
        else:
            action.append('cleantest')
        settings = {}
        make_file = ocpiutil.get_makefile(self.directory)[0]
        #Clean
        ocpiutil.execute_cmd(settings,
                             self.directory,
                             action=action,
                             file=make_file,
                             verbose=verbose)

    def build(self, verbose=False, no_assemblies=None, workers_as_needed=False,
              artifacts_only=False, optimize=False, dynamic=False, hdl_target=None, hdl_platform=None,
              rcc_platform=None, hdl_rcc_platform=None, generate=False, export=False, **kwargs):
        """
        Builds the tests by handing over the user specifications
        to execute command.
        """
        #Specify what to build
        action = ['test']
        if generate:
            action.append('generate')
        if no_assemblies:
            action.append('Assemblies=')
        if workers_as_needed:
            os.environ['OCPI_AUTO_BUILD_WORKERS'] = '1'
        if artifacts_only:
            os.environ['OCPI_ARTIFACTS_ONLY'] = '1'
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
        #Pass settings HdlPlatforms RccPlatforms RccHdlPlatforms
        settings = {}
        if hdl_platform:
            settings['hdl_plat_strs'] = hdl_platform
        if hdl_target:
            settings['hdl_target'] = hdl_target
        if rcc_platform:
            settings['rcc_platform'] = rcc_platform
        if hdl_rcc_platform:
            settings['hdl_rcc_platform'] = hdl_rcc_platform
        settings['nothing_error'] = kwargs.get('nothing_error', False)
        make_file = ocpiutil.get_makefile(self.directory)[0]
        #Build
        ocpiutil.execute_cmd(settings, 
                             self.directory,
                             action=action,
                             file=make_file,
                             verbose=verbose)
        if export:
            location=ocpiutil.get_path_to_project_top()
            make_file=ocpiutil.get_makefile(location, "project")[0]
            ocpiutil.execute_cmd({},
                             location,
                             action=['exports'],
                             file=make_file,
                             verbose=verbose)
            
    def _filter_on_platforms(self, platforms: List) -> List[Test]:
        """Filters tests by provided platforms.
        
        If multiple platforms  are provided, the returned tests will be 
        a union for all provided platforms. A test is filtered out if no 
        worker sharing the same spec as the test is found for any of the 
        provided platforms or if the test specifically excludes the 
        provided platforms or found workers.

        Args:
            platforms: List of platforms to filter by.
        Returns:
            List of tests filtered by provided platforms.
        """
        if not platforms:
            return self.tests
        platforms_str = ", ".join([platform.name for platform in platforms])
        library_dict = {}
        for test in self.tests:
        # Get libraries of tests
            library_dir = str(test.parent)
            if library_dir not in library_dict.keys():
                library_dict[library_dir] = AssetFactory.get_instance(
                    AssetFactory.get_class_from_asset_type('library', ''), 
                    library_dir, parse_workers=True, verb='show')
        tests = []
        for test in self.tests:
        # Find tests with an appropriate worker for a provided platform
            library = library_dict[str(test.parent)]
            for worker, platform in product(filter(test._is_valid_worker, library.worker_list), 
                                            filter(test._is_valid_platform, platforms)):
                if worker._is_valid_platform(platform):
                # Appropriate worker found; include test
                    ocpiutil.logging.debug(
                        f'Including "{test.name}": appropriate worker "{worker.name}"'
                        f' found for platform "{platform.name}"')
                    tests.append(test)
                    break
            else:
            # No appropriate worker found; exclude test
                ocpiutil.logging.debug(
                    f'Excluding test "{test.name}": no appropriate worker found for any'
                    f' of the following platforms: {platforms_str}')
        exclude_count = len(self.tests) - len(tests)
        include_count = len(tests)
        ocpiutil.logging.info(
            f'Filtered out {exclude_count} {"test" if exclude_count == 1 else "tests"}.')
        ocpiutil.logging.info(
            f'Found {include_count} {"test" if include_count == 1 else "tests"}'
            f' appropriate for the following platforms: {platforms_str}')
        return tests
                

    def show(self, format=None, **kwargs):
        """
        Show all the tests
        """
        platforms_dict = ocpiutil.get_platforms()
        platforms = []
        hdl_platform_names = kwargs.get('hdl_platform', None) or []
        rcc_platform_names = kwargs.get('rcc_platform', None) or []
        try:
            for platform_name in hdl_platform_names:
                platform_dir = str(Path(platforms_dict[platform_name]['directory']).parent)
                platform_class = AssetFactory.get_class_from_asset_type('hdl-platform', '')
                platform = AssetFactory.get_instance(platform_class, platform_dir, platform_name)
                platforms.append(platform)
            for platform_name in rcc_platform_names:
                platform_dir = platforms_dict[platform_name]['directory']
                platform_class = AssetFactory.get_class_from_asset_type('rcc-platform', '')
                platform = AssetFactory.get_instance(platform_class, platform_dir)
                platforms.append(platform)
        except KeyError:
            raise ocpiutil.OCPIException(f'Unknown platform "{platform_name}".')
        tests = self._filter_on_platforms(platforms)
        if format == "simple":
            for test in tests:
                print(test.name + " ", end="")
            print()
        elif format == "table":
            rows = [['Test', 'Package ID', 'Directory']]
            for test in tests:
                rows.append([test.name, test.package_id, test.directory])
            ocpiutil.print_table(rows, underline="-")
        elif format == "json":
            test_dict = {}
            for test in tests:
                test_dict[test.package_id] = { 
                    'name': test.name, 
                    'package_id': test.package_id,
                    'path': test.directory 
                }
            json.dump(test_dict, sys.stdout)
            print()
