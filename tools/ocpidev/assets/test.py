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

import os
from pathlib import Path
import _opencpi.util as ocpiutil
import jinja2
import _opencpi.assets.template as ocpitemplate
from .abstract import RunnableAsset, HDLBuildableAsset, RCCBuildableAsset
from .library import Library

class Test(RunnableAsset, HDLBuildableAsset, RCCBuildableAsset):
    """
    This class represents an OpenCPI Component Unit test.  Contains build/run settings that are
    specific to Tests.
    """
    valid_settings = ["keep_sims", "acc_errors", "cases", "verbose", "remote_test_sys", "view", "phase"]
    def __init__(self, directory, name=None, **kwargs):
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
        if not name:
            name = Path(directory).name
            directory = str(Path(directory).parent)
        elif Path(name).suffix != '.test':
            name += '.test'
        path = Path(directory, name)
        if path.suffix == '.test':
            self.check_dirtype("test", str(path))
        else:
            dir_type = ocpiutil.get_dirtype(str(path))
            if dir_type is None:
                err_msg = ' '.join([
                    'cannot operate within directory of type "None".',
                    'Try returning to the top level of your project.'
                ])
                raise ocpiutil.OCPIException(err_msg)
        super().__init__(directory, name, **kwargs)
        
        self.keep_sims = kwargs.get("keep_sims", False)
        self.view = kwargs.get("view", False)
        self.acc_errors = kwargs.get("acc_errors", False)
        self.cases = kwargs.get("cases", None)
        self.mode = kwargs.get("mode", "all")
        self.phases = kwargs.get("phases", [])
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
        self.remote_test_sys = kwargs.get("remote_test_sys", None)

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

    def run(self):
        """
        Runs the Test with the settings specified in the object
        """
        goal=self.mode_dict[self.mode]
        if self.mode != "view" and (self.view or "view" in self.phases):
            goal.append("view")
        directory = str(Path(self.directory, self.name))
        make_file = ocpiutil.get_makefile(directory, "test")[0]
        make_file = str(Path(directory, make_file).resolve())
        return ocpiutil.execute_cmd(self.get_settings(),
                                    directory,
                                    goal,
                                    file=make_file)

    def build(self):
        """
        This is a placeholder function will be the function that builds this Asset
        """
        raise NotImplementedError("Test.build() is not implemented")

    @staticmethod
    def get_working_dir(name, ensure_exists=True, **kwargs):
        """
        return the directory of a Test given the name (name) and
        library specifiers (library, hdl_library, hdl_platform)
        """
        # if more then one of the library location variable are not None it is an error
        cur_dirtype = ocpiutil.get_dirtype()
        valid_dirtypes = ["project", "libraries", "library", "test"]
        library = kwargs.get('library', '')
        hdl_library = kwargs.get('hdl_library', '')
        platform = kwargs.get('platform', '')
        working_path = Path.cwd()
        name = name if name else ''
        if len(list(filter(None, [library, hdl_library, platform]))) > 1:
            ocpiutil.throw_invalid_libs_e()
        if cur_dirtype not in valid_dirtypes:
            ocpiutil.throw_not_valid_dirtype_e(valid_dirtypes)

        #add on the .test to the test name if its not already there
        if name and not Path(name).suffix == '.test':
            name += '.test'
        project_path = Path(ocpiutil.get_path_to_project_top())
        if library:
            if not library.startswith("components"):
                library = "components/" + library
            working_path = Path(project_path, library)
        elif hdl_library:
            hdldir = "hdl/" + hdl_library
            working_path = Path(project_path, hdldir)
        elif platform:
            working_path = Path(
                project_path, 'hdl', 'platforms', platform, 'devices')
        elif cur_dirtype == "hdl-platform":
            working_path = Path(working_path, 'devices')

        working_path = Path(working_path, name)
        return str(working_path)


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
    def create(name, directory, **kwargs):
        """
        Create test assets
        """
        verbose = kwargs.get("verbose", None)
        library = kwargs.get("library", None)
        hdl_lib = kwargs.get("hdl_library", None)
        platform = kwargs.get("platform", None)
        testname = name.replace(".test", "")
        testdir = Path(directory, name)
        projdir = ocpiutil.get_path_to_project_top()
        projname = os.path.basename(projdir)
 
        if projdir == os.path.dirname(testdir) and \
          not library and not hdl_lib and not platform:
            raise ocpiutil.OCPIException("Must specify library (not components)," +
                                             " HDL library, or HDL platform" )
        if testdir.is_dir():
            raise ocpiutil.OCPIException(name + " already exists at " + directory)
        if platform:
            platdir = os.path.dirname(directory)
            if not os.path.exists(platdir):
                raise ocpiutil.OCPIException("Cannot find platform " + platdir)
            if not os.path.exists(directory):
                os.mkdir(directory)
        elif not os.path.exists(directory):
            missing = " library " if library else "HDL library "
            raise ocpiutil.OCPIException("Cannot find " + missing + directory)

        testdir.mkdir()
        os.chdir(testdir)
        template_dict = Test._get_template_dict(testname, testdir, **kwargs)
        template = jinja2.Template(ocpitemplate.TEST_GENERATE_PY, trim_blocks=True)
        ocpiutil.write_file_from_string("generate.py", template.render(**template_dict))
        template = jinja2.Template(ocpitemplate.TEST_VERIFY_PY, trim_blocks=True)
        ocpiutil.write_file_from_string("verify.py", template.render(**template_dict))
        template = jinja2.Template(ocpitemplate.TEST_VIEW_SH, trim_blocks=True)
        ocpiutil.write_file_from_string("view.sh", template.render(**template_dict))
        template = jinja2.Template(ocpitemplate.TEST_NAME_TEST_XML, trim_blocks=True)
        ocpiutil.write_file_from_string(testname + "-test.xml", template.render(**template_dict))
        Library.get_package_id(directory)
        if verbose == True:
            print("Created test '" + name + "' at " + str(testdir))
