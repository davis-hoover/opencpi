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

import os,sys
from pathlib import Path
import _opencpi.util as ocpiutil
import jinja2
import json
import _opencpi.assets.template as ocpitemplate
from .abstract import RunnableAsset, HDLBuildableAsset, RCCBuildableAsset,Asset
from .factory import AssetFactory
from .library import Library

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
                raise ocpiutil.OCPIException("Invalid phases: " + " ".join(phases))
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

    def run(self, verbose=False, **kwargs):
        """
        Runs the Test with the settings specified in the object
        """
        goal=self.mode_dict[self.mode]
        if self.mode != "view" and (self.view or "view" in self.phases):
            goal.append("view")
        directory = str(Path(self.directory))
        make_file = ocpiutil.get_makefile(directory, "test")[0]
        make_file = str(Path(directory, make_file).resolve())
        return ocpiutil.execute_cmd(self.get_settings(),
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

class TestsCollection(RunnableAsset, HDLBuildableAsset, RCCBuildableAsset):
    """
    This class represents an OpenCPI Component Unit test. Contains build/run settings that are
    specific to Tests.
    """
    valid_settings = []
    def __init__(self, directory, name=None, assets=None, **kwargs):
        if assets != None:
            self.out_of_project = True
        super().__init__(directory, name, **kwargs)
        self.tests = []
        if assets != None:
            for test_dir,parent_package_id in assets:
                test_name = Path(test_dir).stem
                self.tests.append(Test(test_dir, None,
                                       package_id=parent_package_id + ".tests." + test_name))
        else:
            self.check_dirtype('library', self.directory)
            for subdir in Path(self.directory).iterdir():
                if subdir.is_dir() and subdir.name != 'specs':
                    dirtype = ocpiutil.get_dirtype(subdir)
                    if dirtype == 'test':
                        self.tests.append(Test(str(subdir), None, **kwargs))

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
              optimize=False, dynamic=False, hdl_target=None, hdl_platform=None,
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

    def show(self, format=None, **kwargs):
        """
        Show all the tests
        """
        if format == "simple":
            for test in self.tests:
                print(test.name + " ", end="")
            print()
        elif format == "table":
            rows = [['Test', 'Package ID', 'Directory']]
            for test in self.tests:
                rows.append([test.name, test.package_id, test.directory])
            ocpiutil.print_table(rows, underline="-")
        elif format == "json":
            test_dict = {}
            for test in self.tests:
                test_dict[test.package_id] = { 'name' : test.name, 'package_id' : test.package_id,
                                               'path' : test.directory }
            json.dump(test_dict, sys.stdout)
            print()
