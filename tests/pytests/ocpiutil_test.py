#!/usr/bin/env python3

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
Unit test the utility functions in the ocpiutil module.
Some of the simpler functions in ocpiutil only have doctests
(which live inside the ocpiutil file).

Run from this directory as follows:
    $ coverage3 run ocpiutil_test.py -v

To view the code coverage report:
    $ coverage3 report
To view the line-by-line code coverage report:
    $ coverage3 annotate ../../tools/scripts/ocpiutil.py
    $ vim ../../tools/scripts/ocpiutil.py,cover
"""
import unittest
import os
import sys
import re
import subprocess
import logging
sys.path.append(os.getenv('OCPI_CDK_DIR') + '/' + os.getenv('OCPI_TOOL_PLATFORM') + '/lib/')
import _opencpi.util as ocpiutil
from  _opencpi.assets.factory import *
from  _opencpi.assets.registry import *
from  _opencpi.assets.project import Project
import io
from contextlib import redirect_stdout

# The following globals are used within the test cases for
# setting up and verifying projects and paths
DIR_PATH = os.path.dirname(os.path.realpath(__file__)) + "/"

PROJECT0 = "ocpiutil_test_project0"

PROJECT0_DIRTYPES = {
    "components": "libraries",
    "components/mylibrary": "library",
    "components/mylibrary/myworker0.rcc": "worker",
    "components/mylibrary/myworker1.hdl": "worker",
    "components/mylibrary/myspec.test": "test",
    "hdl/primitives": "hdl-primitives",
    "hdl/primitives/mycore": "hdl-core",
    "hdl/primitives/mylib": "hdl-library",
    "hdl/platforms": "hdl-platforms",
    "hdl/platforms/myplat": "hdl-platform",
    "hdl/assemblies": "hdl-assemblies",
    "hdl/assemblies/myassemb": "hdl-assembly"
}

PROJECT_PACKAGES = {
    PROJECT0: "local." + PROJECT0,
    "mypj0": "pkg0",
    "mypj1": "pkg1",
    "mypj2": "pref0.mypj2",
    "mypj3": "pref1.myname0",
    "mypj4": "pref2.myname1",
    "mypj5": "local.myname2",
    "mypj6": "pkg2",
    "mypj7": "local.mypj7",
    "mypj8_exported": "prefexports.nm8"
}

OCPI_LOG_LEVEL = os.environ.get('OCPI_LOG_LEVEL')
OCPI_CDK_DIR = os.environ.get('OCPI_CDK_DIR')
OCPI_TOOL_PLATFORM = os.environ.get('OCPI_TOOL_PLATFORM')

# Determine path to ocpidev based on CDK so that we avoid accidentally
# using the one installed by RPMs
OCPIDEV_PATH = OCPI_CDK_DIR + '/' + OCPI_TOOL_PLATFORM + '/bin/ocpidev'
if OCPI_LOG_LEVEL and int(OCPI_LOG_LEVEL) > 8:
    SET_X = " set -x; "
    OCPIDEV_CMD = OCPIDEV_PATH + " -v"
else:
    SET_X = " "
    OCPIDEV_CMD = OCPIDEV_PATH

#TODO: test get_ok

class TestPrintTable(unittest.TestCase):
    def test_simple_print(self):
        f = io.StringIO()
        with redirect_stdout(f):
            ocpiutil.print_table([["Col1","Col2"], ["foo", "bar"]])
        actual = f.getvalue()

        expected =  "---------------\n"
        expected += "| Col1 | Col2 |\n"
        expected += "| foo  | bar  |\n"
        expected += "---------------\n"
        
        self.assertEqual(actual, expected)

    def test_simple_print_ints(self):
        f = io.StringIO()
        with redirect_stdout(f):
            ocpiutil.print_table([["Col1","Col2"], [3, 4]])
        actual = f.getvalue()

        expected =  "---------------\n"
        expected += "| Col1 | Col2 |\n"
        expected += "| 3    | 4    |\n"
        expected += "---------------\n"
        
        self.assertEqual(actual, expected)

    def test_print_with_header(self):
        f = io.StringIO()
        with redirect_stdout(f):
            ocpiutil.print_table([["Col1","Col2"], ["foo", "bar"]], underline="-")
        actual = f.getvalue()

        expected =  "---------------\n"
        expected += "| Col1 | Col2 |\n"
        expected += "| ---- | ---- |\n"
        expected += "| foo  | bar  |\n"
        expected += "---------------\n"
        
        self.assertEqual(actual, expected)

    def test_print_with_footnote(self):
        f = io.StringIO()
        c = ocpiutil.TableCell("Col1", "hello")
        with redirect_stdout(f):
            ocpiutil.print_table([[c,"Col2"], ["foo", "bar"]])
        actual = f.getvalue()

        expected =  "----------------\n"
        expected += "| Col1* | Col2 |\n"
        expected += "| foo   | bar  |\n"
        expected += "----------------\n"
        expected += "*) hello\n"

        self.assertEqual(actual, expected)

    def test_print_with_footnotes_with_marker(self):
        f = io.StringIO()
        c = ocpiutil.TableCell("Col1", "hello")
        c2 = ocpiutil.TableCell("bar", "hello again")
        with redirect_stdout(f):
            ocpiutil.print_table([[c,"Col2"], ["foo", c2]], footnote_marker="!")
        actual = f.getvalue()

        expected =  "-----------------\n"
        expected += "| Col1! | Col2  |\n"
        expected += "| foo   | bar!! |\n"
        expected += "-----------------\n"
        expected += "!) hello\n"
        expected += "!!) hello again\n"

        self.assertEqual(actual, expected)
    def test_print_with_footnotes(self):
        f = io.StringIO()
        c = ocpiutil.TableCell("Col1", "hello")
        c2 = ocpiutil.TableCell("bar", "hello again")
        with redirect_stdout(f):
            ocpiutil.print_table([[c,"Col2"], ["foo", c2]])
        actual = f.getvalue()

        expected =  "-----------------\n"
        expected += "| Col1* | Col2  |\n"
        expected += "| foo   | bar** |\n"
        expected += "-----------------\n"
        expected += "*) hello\n"
        expected += "**) hello again\n"

        self.assertEqual(actual, expected)

    def test_print_with_footnotes_reduced_footnote_marker(self):
        f = io.StringIO()
        c = ocpiutil.TableCell("Col1", "hello")
        c2 = ocpiutil.TableCell("bar", "hello")
        with redirect_stdout(f):
            ocpiutil.print_table([[c,"Col2"], ["foo", c2]], footnote_marker="!")
        actual = f.getvalue()

        expected =  "----------------\n"
        expected += "| Col1! | Col2 |\n"
        expected += "| foo   | bar! |\n"
        expected += "----------------\n"
        expected += "!) hello\n"

        self.assertEqual(actual, expected)
    def test_print_with_footnotes_reduced(self):
        f = io.StringIO()
        c = ocpiutil.TableCell("Col1", "hello")
        c2 = ocpiutil.TableCell("bar", "hello")
        with redirect_stdout(f):
            ocpiutil.print_table([[c,"Col2"], ["foo", c2]])
        actual = f.getvalue()

        expected =  "----------------\n"
        expected += "| Col1* | Col2 |\n"
        expected += "| foo   | bar* |\n"
        expected += "----------------\n"
        expected += "*) hello\n"

        self.assertEqual(actual, expected)

    def test_print_with_footnotes_reduced_surr_col_delim(self):
        f = io.StringIO()
        c = ocpiutil.TableCell("Col1", "hello")
        c2 = ocpiutil.TableCell("bar", "hello")
        with redirect_stdout(f):
            ocpiutil.print_table([[c,"Col2"], ["foo", c2]], surr_cols_delim="!")
        actual = f.getvalue()

        expected =  "----------------\n"
        expected += "! Col1* | Col2 !\n"
        expected += "! foo   | bar* !\n"
        expected += "----------------\n"
        expected += "*) hello\n"

        self.assertEqual(actual, expected)
    def test_print_with_footnotes_reduced_surr_rows_delim(self):
        f = io.StringIO()
        c = ocpiutil.TableCell("Col1", "hello")
        c2 = ocpiutil.TableCell("bar", "hello")
        with redirect_stdout(f):
            ocpiutil.print_table([[c,"Col2"], ["foo", c2]], surr_rows_delim="!")
        actual = f.getvalue()

        expected =  "!!!!!!!!!!!!!!!!\n"
        expected += "| Col1* | Col2 |\n"
        expected += "| foo   | bar* |\n"
        expected += "!!!!!!!!!!!!!!!!\n"
        expected += "*) hello\n"

        self.assertEqual(actual, expected)

    def test_print_with_footnotes_reduced_col_delim(self):
        f = io.StringIO()
        c = ocpiutil.TableCell("Col1", "hello")
        c2 = ocpiutil.TableCell("bar", "hello")
        with redirect_stdout(f):
            ocpiutil.print_table([[c,"Col2"], ["foo", c2]], col_delim="!")
        actual = f.getvalue()

        expected =  "----------------\n"
        expected += "| Col1* ! Col2 |\n"
        expected += "| foo   ! bar* |\n"
        expected += "----------------\n"
        expected += "*) hello\n"

        self.assertEqual(actual, expected)

    def test_print_with_footnotes_reduced_row_delim(self):
        f = io.StringIO()
        c = ocpiutil.TableCell("Col1", "hello")
        c2 = ocpiutil.TableCell("bar", "hello")
        with redirect_stdout(f):
            ocpiutil.print_table([[c,"Col2"], ["foo", c2]], row_delim="!")
        actual = f.getvalue()

        expected =  "----------------\n"
        expected += "| Col1* | Col2 |\n"
        expected += "!!!!!!!!!!!!!!!!\n"
        expected += "| foo   | bar* |\n"
        expected += "!!!!!!!!!!!!!!!!\n"
        expected += "----------------\n"
        expected += "*) hello\n"

        self.assertEqual(actual, expected)


class TestPathFunctions(unittest.TestCase):
    """
    Test the path finding/manipulating functions in ocpiutil (e.g. get_path(s)_...)
    as well as the project package functions (e.g. get_project_package)
    """
    @classmethod
    def setUpClass(cls):
        logging.info("Setting up test projects...")
        logging.info("...")
        # Set the registry, (export the variable in bash), register core in the new location
        os.environ['OCPI_PROJECT_REGISTRY_DIR'] = os.path.realpath('./project-registry')
        ocpidev_command = "set -e; set -o pipefail && rm -r -f project-registry; " + SET_X
        ocpidev_command += OCPIDEV_CMD + " create registry project-registry; "
        ocpidev_command += ("export OCPI_PROJECT_REGISTRY_DIR=" +
                            os.path.realpath('./project-registry') + " ; ")
        # Create PROJECT0 and fill it with assets of many types
        ocpidev_command += ("ln -s " + OCPI_CDK_DIR +
                            "/../project-registry/ocpi.core project-registry/ocpi.core; ")
        ocpidev_command += OCPIDEV_CMD + " --register create project " + PROJECT0 + "; "
        ocpidev_command += OCPIDEV_CMD + " -d " + PROJECT0 + " create library mylibrary; "
        ocpidev_command += OCPIDEV_CMD + " -d " + PROJECT0 + " create -l mylibrary spec myspec; "
        ocpidev_command += OCPIDEV_CMD + " -d " + PROJECT0 + " create -l mylibrary test myspec; "
        ocpidev_command += (OCPIDEV_CMD + " -d " + PROJECT0 +
                            " create -l mylibrary worker myworker0.rcc -S myspec-spec.xml; ")
        ocpidev_command += (OCPIDEV_CMD + " -d " + PROJECT0 +
                            " create -l mylibrary worker myworker1.hdl -S myspec-spec.xml; ")
        ocpidev_command += OCPIDEV_CMD + " -d " + PROJECT0 + " create hdl primitive core mycore; "
        ocpidev_command += OCPIDEV_CMD + " -d " + PROJECT0 + " create hdl primitive library mylib; "
        ocpidev_command += OCPIDEV_CMD + " -d " + PROJECT0 + " create hdl platform myplat; "
        ocpidev_command += OCPIDEV_CMD + " -d " + PROJECT0 + " create hdl assembly myassemb; "
        ocpidev_command += OCPIDEV_CMD + " -d " + PROJECT0 + " create application myapp; "
        # Create a handful of proje " + OCPIDEV_VERBOSE + "cts with different names and packages
        ocpidev_command += OCPIDEV_CMD + " --register -K pkg0               create project mypj0; "
        ocpidev_command += OCPIDEV_CMD + " --register -K pkg1   -N whocares create project mypj1; "
        ocpidev_command += OCPIDEV_CMD + " --register -F pref0              create project mypj2; "
        ocpidev_command += OCPIDEV_CMD + " --register -F pref1  -N myname0  create project mypj3; "
        ocpidev_command += OCPIDEV_CMD + " --register -F pref2. -N myname1  create project mypj4; "
        ocpidev_command += OCPIDEV_CMD + " --register           -N myname2  create project mypj5; "
        ocpidev_command += OCPIDEV_CMD + " --register -K pkg2   -N wc -F wc create project mypj6; "
        ocpidev_command += OCPIDEV_CMD + " --register                       create project mypj7; "
        ocpidev_command += OCPIDEV_CMD + "            -F prefexports -N nm8 create project mypj8; "
        # Create a components library in each
        ocpidev_command += OCPIDEV_CMD + " -d mypj0 create library components; "
        ocpidev_command += OCPIDEV_CMD + " -d mypj1 create library components; "
        ocpidev_command += OCPIDEV_CMD + " -d mypj2 create library components; "
        ocpidev_command += OCPIDEV_CMD + " -d mypj3 create library components; "
        ocpidev_command += OCPIDEV_CMD + " -d mypj4 create library components; "
        ocpidev_command += OCPIDEV_CMD + " -d mypj5 create library components; "
        ocpidev_command += OCPIDEV_CMD + " -d mypj6 create library components; "
        ocpidev_command += OCPIDEV_CMD + " -d mypj7 create library components; "
        ocpidev_command += OCPIDEV_CMD + " -d mypj8 create library components; "
        # Export mypj8
        ocpidev_command += "make -f $OCPI_CDK_DIR/include/project.mk exports -C mypj8;"
        # Copy the exported pj8 to a new dir, but omit the imports
        ocpidev_command += "mkdir mypj8_exported;"
        ocpidev_command += "rm mypj8/exports/imports; "
        # Note use -R, not -r, for POSIX/BSD portability
        ocpidev_command += "cp -RfL mypj8/exports/* mypj8_exported 2>/dev/null; "
        # Rebuild pj8's imports
        ocpidev_command += "make imports -C mypj8; "
        # Get imports by setting registry for the new exported non-source project
        ocpidev_command += OCPIDEV_CMD + " -d mypj8_exported set registry; "
        # Register the exported project
        ocpidev_command += OCPIDEV_CMD + " register project mypj8_exported; "

        logging.debug("OCPIDEV CMD: '" + ocpidev_command.replace('; ', ';\n'))
        process = subprocess.Popen(ocpidev_command, shell=True, executable='/bin/bash')
        results = process.communicate()
        if results[1] or process.returncode != 0:
            raise ocpiutil.OCPIException("'ocpidev create project' failed in ocpiutil test\n" +
                                         "process.returncode: " +  str(process.returncode) +
                                         ":" + str(results[1]))

    @classmethod
    def tearDownClass(cls):
        """
        Remove the projects created by setUp
        """
        if not os.environ.get('OCPI_KEEP_TEST'):
            ocpidev_command = ""
            for prj in PROJECT_PACKAGES:
                ocpidev_command += OCPIDEV_CMD + " -f delete project " + prj + "; "
            # Manually remove mypj8 because it is not in PROJECT_PACKAGES since only
            # its exported version is used
            ocpidev_command += OCPIDEV_CMD + " -f delete project mypj8; "
            ocpidev_command += "rm project-registry/ocpi.core;" # it is here because we hacked the link
            ocpidev_command += OCPIDEV_CMD + " -f delete registry project-registry; "
            process = subprocess.Popen(ocpidev_command, stdout=subprocess.PIPE, shell=True)
            if process.communicate()[1] or process.returncode != 0:
                logging.info("'ocpidev delete project' failed in ocpiutil test")
                logging.info("process.returncode: " +  str(process.returncode))
                raise RuntimeError("Failed to delete the projects via 'ocpidev delete' commands")

    def test_get_project_registry_dir(self):
        """
        Test the value extracted for project-registry dir
        given different states:
            With OCPI_PROJECT_REGISTRY_DIR set
            With it unset, but OCPI_CDK_DIR set
            With both unset
        """
        logging.info("==================================" +
                     "===================================")
        logging.info("Asserting that 'project-registry directory' " +
                     "defaults to correct values\n")
        reg_dir = Registry.get_default_registry_dir()
        self.assertEqual(reg_dir, os.environ.get('OCPI_PROJECT_REGISTRY_DIR'))

        # Collect all of the projects except for core
        # TODO: test get_all_project cases where OCPI_PROJECT_PATH exists,
        #       and also where registry does not
        all_pjs = [pj for pj in ocpiutil.get_all_projects() if not re.search(r".*/ocpi\.core$", pj)]
        pj_paths = [os.path.realpath('.') + '/project-registry/'
                    + pj for pj in list(PROJECT_PACKAGES.values())]
        golden_all_pjs = pj_paths
        project_path = os.environ.get('OCPI_PROJECT_PATH')
        if project_path:
           golden_all_pjs += project_path.split(':')
        logging.info("Verifying that get_all_projects correctly collects CDK, Project path, " +
                     "and registry contents: " + str(golden_all_pjs))
        self.assertEqual(set(all_pjs), set(golden_all_pjs))
        orig_gprd = os.environ['OCPI_PROJECT_REGISTRY_DIR']


        logging.info("Ensuring that invalid registry environment variable results in error")
        os.environ['OCPI_PROJECT_REGISTRY_DIR'] = "INVALID"
        self.assertRaises(ocpiutil.OCPIException, Registry.get_default_registry_dir)

        logging.info("Verify that a project's imports takes precedence over the environment's " +
                     "registry settings.")
        for proj in PROJECT_PACKAGES:
            with ocpiutil.cd(proj):
                reg_dir = str(Project.get_registry_path_from_project_path(Path('.')))
                if re.search(r".*exported$", proj):
                    logging.debug("Verify that deep-copied/exported project (" + proj + ") uses " +
                                  "its imports dir as the registry.")
                    self.assertEqual(os.path.realpath("imports"), reg_dir)
                else:
                    logging.debug("Verify that the project (" + proj + ") uses its " +
                                  "imports link as the registry.")
                    self.assertEqual(os.path.realpath("../project-registry"), reg_dir)

        # Test for 'bad' registry results
        os.environ['OCPI_PROJECT_REGISTRY_DIR'] = __file__
        logging.info("Verify that the default registry is correct even for a bad registry.")
        #get_default_registry_dir is stricter and fails here for good reasons
        #self.assertEqual(__file__, Registry.get_default_registry_dir())
        self.assertRaises(ocpiutil.OCPIException, Registry.get_default_registry_dir)

        del os.environ['OCPI_PROJECT_REGISTRY_DIR']
        logging.info("Verify that the registry is correct when OCPI_PROJECT_REGISTRY_DIR is unset.")
        reg_dir = Registry.get_default_registry_dir()
        self.assertEqual(reg_dir, os.path.realpath(os.environ.get('OCPI_CDK_DIR') + "/../project-registry"))
        logging.info("Verify that the default registry is correct when the env var is unset.")
        self.assertEqual(reg_dir, Registry.get_default_registry_dir())
        if os.path.isdir("/opt/opencpi/project-registry"):
            orig_cdk = os.environ['OCPI_CDK_DIR']
            del os.environ['OCPI_CDK_DIR']
            reg_dir = Registry.get_default_registry_dir()
            self.assertEqual(reg_dir, "/opt/opencpi/project-registry")
            logging.info("Verify that the default registry is correct when no env vars are set.")
            self.assertEqual(reg_dir, Registry.get_default_registry_dir())
            os.environ['OCPI_CDK_DIR'] = orig_cdk
        else:
            logging.warning("Skipping default registry check because " +
                            "/opt/opencpi/project-registry does not exist")

        os.environ['OCPI_PROJECT_REGISTRY_DIR'] = orig_gprd

    def test_get_dirtype(self):
        """
        Iterate through the PROJECT0_DIRTYPES dictionary and confirm that
        each directory in PROJECT0 is recognized by the correct dirtype.
        """
        logging.info("===========================\nTesting 'get_dirtype'")
        for path, dirtype in list(PROJECT0_DIRTYPES.items()):
            logging.info("\nDirtype for path '" + path + "' should be: " + dirtype + "\n")
            self.assertEqual(ocpiutil.get_dirtype(PROJECT0 + "/" + path), dirtype)
        logging.info("---------------------------")
        logging.info("Dirtype for path '.' should be: None")
        self.assertEqual(ocpiutil.get_dirtype(), None)

    def test_get_subdirs_of_type(self):
        """
        When get_subdirs... is called, every directory in PROJECT0
        with the given type should be returned.
        """
        logging.info("===========================\nTesting 'get_subdirs_of_type'")
        for path, dirtype in list(PROJECT0_DIRTYPES.items()):
            expected_path = PROJECT0 + "/" + path
            logging.info("\nSubdirs of type '" + dirtype +
                         "' should contain path: " + expected_path)
            subdirs = ocpiutil.get_subdirs_of_type(dirtype, PROJECT0)
            logging.info("Subdirs collected are: " + str(subdirs))
            self.assertTrue(expected_path in subdirs)
        logging.info("---------------------------")
        logging.info("Subdirs of invalid type should be: None")
        self.assertEqual(ocpiutil.get_subdirs_of_type("INVALID_TYPE"), [])
        self.assertEqual(ocpiutil.get_subdirs_of_type(None), [])

    def test_is_path_in_project(self):
        """
        Every path in PROJECT0_DIRTYPES is within PROJECT0,
        so they should all result in True here. Invalid paths
        or those outside the project should return false.
        """
        logging.info("===========================\nTesting 'is_path_in_project'")
        logging.info("All paths corresponding to project-assets " +
                     "show up as True for in-project.")
        logging.info("---------------------------")
        for path, _ in list(PROJECT0_DIRTYPES.items()):
            self.assertTrue(ocpiutil.is_path_in_project(PROJECT0 + "/" + path))
        self.assertTrue(ocpiutil.is_path_in_project(PROJECT0))
        logging.info("Invalid paths and directories outside projects " +
                     "should return False.")
        self.assertFalse(ocpiutil.is_path_in_project("/"))
        self.assertFalse(ocpiutil.is_path_in_project("NOT A PATH"))

    def test_is_path_in_exported_project(self):
        logging.info("===========================\nTesting 'is_path_in_exported_project'")
        logging.info("Confirm mypj8_exported is in an exported project")
        self.assertTrue(ocpiutil.is_path_in_exported_project("mypj8_exported"))
        logging.info("Confirm mypj8 is NOT in an exported project")
        self.assertFalse(ocpiutil.is_path_in_exported_project("mypj8"))

    def test_get_project_imports(self):
        pass

    def test_get_project_package(self):
        """
        A handful of projects were created by ocpidev in setUp and listed in
        PROJECT_PACKAGES. Each one has different project name and package settings.
        Verify that each is correct from different CWDs.
        """
        logging.info("===========================\nTesting 'get_project_package'")
        for proj, pkg in list(PROJECT_PACKAGES.items()):
            logging.info("Project \"" + proj + "\" should have full-package: " + pkg)
            self.assertEqual(ocpiutil.get_project_package(proj), pkg)
        logging.info("---------------------------")
        logging.info("Rerunning full-package name tests from " +
                     "within subdirs in each project.")
        for proj, pkg in list(PROJECT_PACKAGES.items()):
            with ocpiutil.cd(proj):
                logging.info("Project \"" + proj + "\" should have full-package: " + pkg)
                self.assertEqual(ocpiutil.get_project_package(), pkg)
                self.assertEqual(ocpiutil.get_project_package("."), pkg)
                components_dir = "components"
                if not os.path.exists("components"):
                    components_dir = "lib/components"
                if os.path.exists(components_dir):
                    with ocpiutil.cd(components_dir):
                        self.assertEqual(ocpiutil.get_project_package(), pkg)
                        self.assertEqual(ocpiutil.get_project_package("."), pkg)
                        self.assertEqual(ocpiutil.get_project_package(".."), pkg)
        logging.info("---------------------------")
        logging.info("Project package for a directory outside a project " +
                     "or invalid should be None.")
        self.assertEqual(ocpiutil.get_project_package("/"), None)
        self.assertEqual(ocpiutil.get_project_package(None), None)

    def test_pj_with_pkg_exist(self):
        """
        Verify that each known package is recognized as existing from different CWDs.
        Invalid ones of course should result in False for 'project with pkg DNE'
        """
        logging.info("===========================\n" +
                     "Testing 'does_project_with_package_exist'")
        # TODO: test case where registry does not exist, should return false
        for proj, pkg in list(PROJECT_PACKAGES.items()):
            logging.info("A project (\"" + proj + "\") with package \"" +
                         pkg + "\" should exist.")
            self.assertTrue(ocpiutil.does_project_with_package_exist(package=pkg))
            with ocpiutil.cd(proj):
                logging.info("Trying from within project '" + proj + "'.")
                # Exclude deep-copied/exported projects because they cannot import themselves
                #   or the risk infinite recursive imports
                if not re.search(r".*exported$", proj):
                    self.assertTrue(ocpiutil.does_project_with_package_exist(package=pkg))
                    logging.info("Should not have to specify package name " +
                                 "from within project name.")
                    self.assertTrue(ocpiutil.does_project_with_package_exist())
                    self.assertFalse(ocpiutil.does_project_with_package_exist(package="INVALID"))
                    components_dir = "components"
                    if not os.path.exists("components"):
                        components_dir = "lib/components"
                    if os.path.exists(components_dir):
                        with ocpiutil.cd(components_dir):
                            logging.info("Trying from within project components library.")
                            self.assertTrue(ocpiutil.does_project_with_package_exist(package=pkg))
                            self.assertTrue(ocpiutil.does_project_with_package_exist())
                            self.assertTrue(ocpiutil.does_project_with_package_exist(".."))
                            self.assertFalse(ocpiutil.does_project_with_package_exist(package="INVALID"))
        logging.info("---------------------------")
        logging.info("If project package is invalid," +
                     "does_project_with_package_exist should return False.\n" +
                     "If project package is blank" +
                     "and the specified or current directory is not within a\n" +
                     "project, does_project_with_package_exist should return False.")
        self.assertFalse(ocpiutil.does_project_with_package_exist(package="INVALID"))
        self.assertFalse(ocpiutil.does_project_with_package_exist("/"))
        self.assertFalse(ocpiutil.does_project_with_package_exist(package="INVALID"))

    def test_set_unset_registry(self):
        """
        Set and unset the registry for a project in various ways. Confirm that
        the resulting imports link is correct.
        """
        # TODO/FIXME: set and unset registry are no longer in ocpiutil and should be tested in
        #             a separate unit test
        logging.info("===========================\nTesting 'set/unset_project_registry'")
        #TODO: test set case where imports exists and is not a link
        #TODO: test set for warning when setting to a registry that does not include CDK

        with ocpiutil.cd(PROJECT0):
            proj = AssetFactory.factory("project", ".", verbose=0)
            logging.info("Make sure you can set a project's registry to the default via no args.")
            proj.set_registry()
            self.assertEqual(os.path.realpath("../project-registry"),
                             os.path.realpath(os.readlink("imports")))
            # Cannot set/unset the registry for a project when it is registered
            self.assertRaises(ocpiutil.OCPIException, proj.set_registry, "../../../project-registry")
            self.assertRaises(ocpiutil.OCPIException, proj.unset_registry)
            self.assertTrue(os.path.exists("imports"))

            reg = AssetFactory.get_instance("registry", Project.get_registry_path_from_project_path("."), verbose=0)
            # Remove the project from the registry and proceed with unsetting
            reg.remove(package_id=proj.package_id)
            proj.unset_registry(verbose=True)
            self.assertFalse(os.path.exists("imports"))
            reg.add(proj.package_id, proj.directory)

            logging.info("Make sure you can set a project's registry to a given directory.")
            if os.path.isdir("../../../project-registry"):
                # Cannot set/unset the registry for a project when it is registered
                self.assertRaises(ocpiutil.OCPIException, proj.set_registry,
                                  "../../../project-registry")
                # Remove the project from the registry and proceed with (un)setting
                reg.remove(package_id=proj.package_id)
                proj.set_registry("../../../project-registry")
                self.assertEqual(os.path.realpath("../../../project-registry"),
                                 os.path.realpath(os.readlink("imports")))
                proj.unset_registry()
                self.assertFalse(os.path.exists("imports"))
                reg.add(proj.package_id, proj.directory)
            else:
                logging.warning("Skipping this registry test because ../../../project-registry " +
                                "does not exist (not run from repo?).")

            reg.remove(package_id=proj.package_id)
            logging.info("Make sure you cannot set a project's registry to a non-dir file. " +
                         "Expect an ERROR:")
            self.assertRaises(ocpiutil.OCPIException, proj.set_registry, "Project.mk")
            self.assertFalse(os.path.exists("imports"))

            # Test unset when imports is a plain file and when it does not exist
            logging.info("Make sure you cannot unset/rm an 'imports' file that is not a link. " +
                         "Expect an ERROR:")
            open("imports", 'a').close()
            #self.assertFalse(ocpiutil.unset_project_registry())
            self.assertRaises(ocpiutil.OCPIException, proj.unset_registry)
            self.assertTrue(os.path.isfile("imports"))
            os.remove("imports")
            logging.info("Make sure unsetting a project's registry succeeds and does nothing " +
                         "when it was already unset.")
            proj.unset_registry()
            self.assertFalse(os.path.exists("imports"))

            # Reset project registry to default
            proj.set_registry()
            reg.add(proj.package_id, proj.directory)


    def test_reg_unreg_project(self):
        """
        Unregister and re-register each project in PROJECT_PACKAGES and
        confirm that the project-link is successfully removed from the
        registry and then recreated.
        """
        logging.info("===========================\nTesting 'register_project'")
        # TODO/FIXME: Register and unregister are no longer in ocpiutil and should be tested in
        #             a separate unit test
        # TODO: test reg cases where package is 'local', and where registry does not exist
        # TODO: test reg case where project with the package already exists
        # TODO: test reg case where a link conflicting with the package package exists
        # TODO: test unreg case where user tries to unregister a project, but the registered
        #       project with that package is actually a different project
        reg = AssetFactory.factory("registry", Registry.get_default_registry_dir(), verbose=0)
        gprd = reg.directory
        for proj_dir, pkg in list(PROJECT_PACKAGES.items()):
            logging.info("Unregistering and re-registering project \"" + proj_dir +
                         "\" with package \"" + pkg + "\"")
            reg.remove(directory=proj_dir)
            self.assertFalse(os.path.lexists(gprd + "/" + pkg))
            reg.add(pkg, proj_dir)
            self.assertTrue(os.path.lexists(gprd + "/" + pkg))

            logging.info("Should be able to unregister via project package instead.")
            reg.remove(pkg)
            self.assertFalse(os.path.lexists(gprd + "/" + pkg))
            reg.add(pkg, proj_dir)
            self.assertTrue(os.path.lexists(gprd + "/" + pkg))
            with ocpiutil.cd(proj_dir):
                # Exclude deep-copied/exported projects because they cannot import themselves
                #   or the risk infinite recursive imports
                if not re.search(r".*exported$", proj_dir):
                    logging.info("Confirming this all works from within " +
                                 "the project using path='.'")
                    reg.remove(directory=".")
                    self.assertFalse(os.path.lexists(gprd + "/" + pkg))
                    reg.add(pkg, ".")
                    self.assertTrue(os.path.lexists(gprd + "/" + pkg))
        # If log level is low, disable logging to prevent the expected scary ERROR
        if not OCPI_LOG_LEVEL or int(OCPI_LOG_LEVEL) < 8:
            ocpiutil.OCPIUTIL_LOGGER.disabled = True
        logging.info("Should print an ERROR and return false for invalid project_paths:")
        self.assertRaises(ocpiutil.OCPIException, reg.remove, "INVALID")
        if OCPI_LOG_LEVEL and int(OCPI_LOG_LEVEL) < 8:
            ocpiutil.OCPIUTIL_LOGGER.disabled = False

    def test_get_path_to_project_top(self):
        """
        Given a few paths within (or not within) PROJECT0, verify that
        the calculated path to the project top matches the known correct path.
        Do this for both relative and absolute mode.
        """
        logging.info("===========================\nTesting 'get_path_to_project_top'")
        golden_rel_paths = [".", "./..", "./../../..", None]
        golden_path_to_pj = DIR_PATH + PROJECT0
        golden_paths = [golden_path_to_pj, golden_path_to_pj, golden_path_to_pj, None]
        test_paths = [PROJECT0, PROJECT0 + "/components",
                      PROJECT0 + "/components/mylibrary/specs", "/"]
        for test_path, gold_path, gold_rel in zip(test_paths, golden_paths, golden_rel_paths):
            logging.info("\nGetting path_to_project_top for: " + str(test_path))
            logging.info("Project top should be: " + str(gold_path))
            path = ocpiutil.get_path_to_project_top(test_path)
            self.assertEqual(path, gold_path)
            logging.info("Relative project top should be: " + str(gold_rel))
            rel = ocpiutil.get_path_to_project_top(test_path, relative_mode=True)
            self.assertEqual(rel, gold_rel)
        logging.info("Path to '" + PROJECT0 + "'s project top should be: " +
                     DIR_PATH + PROJECT0)
        self.assertEqual(ocpiutil.get_path_to_project_top(PROJECT0), DIR_PATH + PROJECT0)
        logging.info("Path to '" + DIR_PATH + "'s project top should be: None")
        self.assertEqual(ocpiutil.get_path_to_project_top("/"), None)
        logging.info("Path to 'INVALID's project top should be: None")
        self.assertEqual(ocpiutil.get_path_to_project_top("INVALID"), None)

    def test_get_path_from_project_top(self):
        """
        Given a few paths within (or not within) PROJECT0, verify that
        the calculated path from the project top matches the known correct path.
        """
        logging.info("===========================\nTesting 'get_path_from_project_top'")
        for path, _ in list(PROJECT0_DIRTYPES.items()):
            full_path = DIR_PATH + PROJECT0 + "/" + path
            logging.info("\nPath to '" + full_path +
                         "' from project top should be: " + path)
            self.assertEqual(ocpiutil.get_path_from_project_top(full_path), path)
            rel_path = PROJECT0 + "/" + path
            logging.info("Path to '" + rel_path + "' from project top should be: " + path)
            self.assertEqual(ocpiutil.get_path_from_project_top(rel_path), path)

        logging.info("---------------------------")
        logging.info("Path to '" + PROJECT0 + "' from project top should be: ''")
        self.assertEqual(ocpiutil.get_path_from_project_top(PROJECT0), '')
        logging.info("Path to '" + DIR_PATH + "' from project top should be: None")
        self.assertEqual(ocpiutil.get_path_from_project_top("/"), None)
        logging.info("Path to 'INVALID' from project top should be: None")
        self.assertEqual(ocpiutil.get_path_from_project_top("INVALID"), None)

if __name__ == '__main__':
    unittest.main()
