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

from pathlib import Path
import _opencpi.util as ocpiutil
from .abstract import RunnableAsset, HDLBuildableAsset, RCCBuildableAsset

class Test(RunnableAsset, HDLBuildableAsset, RCCBuildableAsset):
    """
    This class represents an OpenCPI Component Unit test.  Contains build/run settings that are
    specific to Tests.
    """
    valid_settings = ["keep_sims", "acc_errors", "cases", "verbose", "remote_test_sys", "view"]
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
        if not directory.endswith(".test") and not directory.endswith(".test/"):
            directory = directory + ".test"
        self.check_dirtype("test", directory)
        super().__init__(directory, name, **kwargs)

        self.keep_sims = kwargs.get("keep_sims", False)
        self.view = kwargs.get("view", False)
        self.acc_errors = kwargs.get("acc_errors", False)
        self.cases = kwargs.get("cases", None)
        self.mode = kwargs.get("mode", "all")
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
        return ocpiutil.execute_cmd(self.get_settings(),
                                    self.directory,
                                    self.mode_dict[self.mode],
                                    file=ocpiutil.get_makefile(self.directory, "test")[0])

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
        if len(list(filter(None, [library, hdl_library, platform]))) > 1:
            ocpiutil.throw_invalid_libs_e()
        if cur_dirtype not in valid_dirtypes:
            ocpiutil.throw_not_valid_dirtype_e(valid_dirtypes)
        if not name:
            ocpiutil.throw_not_blank_e("test", "name", True)

        #add on the .test to the test name if its not already there
        if not Path(name).suffix == '.test':
            name += '.test'
        project_path = Path(ocpiutil.get_path_to_project_top())
        if library:
            if not library.startswith("components"):
                library = "components/" + library
            working_path = Path(project_path, library)
        elif hdl_library:
            working_path = Path(project_path, hdl_library)
        elif platform:
            working_path = Path(
                project_path, 'hdl', 'platforms', platform, 'devices')
        elif cur_dirtype == "hdl-platform":
            working_path = Path(working_path, 'devices')
        elif cur_dirtype == "project":
            if ocpiutil.get_dirtype("components") == "libraries":
                ocpiutil.throw_specify_lib_e()
            working_path = Path(working_path, 'components')
        
        working_path = Path(working_path, name)

        return str(working_path)
