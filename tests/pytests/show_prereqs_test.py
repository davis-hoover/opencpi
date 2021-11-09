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
import unittest
import json
import uuid
import sys
import os
import shutil
from pathlib import Path
sys.path.append(os.getenv('OCPI_CDK_DIR') + '/' + os.getenv('OCPI_TOOL_PLATFORM') + '/lib/')
import _opencpi.util as ocpiutil
from  _opencpi.assets import factory
from _opencpi.assets import prerequisite

"""
This file contains the unit tests for the prerequisites classes
"""
class PrereqTest(unittest.TestCase):
    def test_addPlatform(self):
        uut = prerequisite.Prerequisite(Path("."))
        uut.add_platform("Hello")
        uut.add_platform("World")

        expected=["Hello", "World"]
        actual=uut.get_platforms()

        self.assertCountEqual(expected, actual)

    def test_location(self):
        uut = prerequisite.Prerequisite(Path("."))
    
        expected="."
        actual=uut.get_location()

        self.assertEqual(expected, actual)

    def test_getDict(self):
        uut = prerequisite.Prerequisite(Path("."))
        uut.add_platform("Hello")
    
        expected={"path":".", "platforms":["Hello"]}
        actual=uut.get_dict()

        self.assertDictEqual(expected, actual)

class PrereqDirTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._old_prereq_dir = os.environ.get("OCPI_PREREQUISITES_DIR")
        cls._old_cdk_dir = os.environ.get("OCPI_CDK_DIR")
        cls._oldcwd = Path(os.getcwd())

        # Must ensure that the WD is 2 deep for the CDK_DIR test
        cls._newwd = Path(os.getcwd()).joinpath(cls.generate_unused_name(), cls.generate_unused_name())

    @classmethod
    def tearDownClass(cls):
        if cls._old_prereq_dir:
            cls.set_prereq_dir(cls._old_prereq_dir)
        if cls._old_cdk_dir:
            cls.set_cdk_dir(cls._old_cdk_dir)
        os.chdir(cls._oldcwd)
        cls.ensure_removed(cls._newwd.parent)

    @classmethod
    def set_cdk_dir(cls, newdir):
        os.environ["OCPI_CDK_DIR"] = newdir

    @classmethod
    def set_prereq_dir(cls, newdir):
        os.environ["OCPI_PREREQUISITES_DIR"] = newdir

    def test_location(self):
        uut = prerequisite.Prerequisites(Path("."))
        expected = "."
        actual = uut.get_location()
        self.assertEqual(expected,actual)

    def test_addPrerequisite(self):
        uut = prerequisite.Prerequisites(Path("."))
        uut.add_prerequisite("Hello", "World")
        expected = {"Hello": "World"}
        actual = uut.get_prerequisites()
        self.assertDictEqual(expected,actual)

    def test_getDict(self):
        uut = prerequisite.Prerequisites(Path("."))
        uut.add_prerequisite("Hello", "World")
        uut.add_prerequisite("Goodbye", "World")

        expected={"prereqs":{"Hello":"World", "Goodbye":"World"},"location":"."}
        actual = uut.get_dict()
        self.assertDictEqual(expected, actual)

    @classmethod
    def generate_unused_name(cls):
        return str(uuid.uuid1())
    
    @classmethod
    def ensure_removed(cls, path: Path):
        shutil.rmtree(path, ignore_errors=True)
        try:
            path.unlink()
        except Exception as e:
            pass

    def test_get_default_location_and_dict_created(self):
        #I want these to be run in sequence because I am messing around with the env
        fallback = Path(os.path.join("/","opt", "opencpi", "prerequisites"))

        # Happy path, where OCPI_PREREQS_DIR is set and exists
        self.set_prereq_dir(os.getcwd())
        expected = Path(os.getcwd())
        actual = prerequisite.Prerequisites.get_default_location()
        self.assertEqual(expected, actual)

        # PREREQS_DIR doesn't exist 
        del os.environ["OCPI_CDK_DIR"]
        newdir = Path(os.path.join(os.getcwd(), self.generate_unused_name()))
        self.ensure_removed(newdir)
        self.set_prereq_dir(str(newdir))
        if not fallback.exists():
            self.assertRaises(ocpiutil.OCPIException, prerequisite.Prerequisites.get_default_location)
        else:
            self.assertEqual(prerequisite.Prerequisites.get_default_location(), fallback)
       
        # Happy path where OCPI_CDK_DIR is set
        del os.environ["OCPI_PREREQUISITES_DIR"]
        self.set_cdk_dir(str(newdir))
        expected = newdir.parent.joinpath("prerequisites")
        Path.mkdir(expected, parents=True)
        actual = prerequisite.Prerequisites.get_default_location()
        self.assertEqual(expected, actual)

        #CDK_DIR doesn't exist
        self.ensure_removed(expected)
        if not fallback.exists():
            self.assertRaises(ocpiutil.OCPIException, prerequisite.Prerequisites.get_default_location)
        else:
            self.assertEqual(prerequisite.Prerequisites.get_default_location(), fallback)

        # At this point I am confident that the prereqs loc can be found so I can actually use the env
        self.set_prereq_dir(str(self._newwd))
        self.set_cdk_dir(str(self._old_cdk_dir))

        # Create a prereq with two platforms
        prereq1 = self._newwd.joinpath("prereq1")
        Path.mkdir(prereq1, parents=True)
        platform1 = prereq1.joinpath("centos7")
        platform2 = prereq1.joinpath("xilinx13_4")
        Path.mkdir(platform1)
        Path.mkdir(platform2)
        prereq1 = prerequisite.Prerequisite(prereq1)
        prereq1.add_platform("centos7")
        prereq1.add_platform("xilinx13_4")

        # Create a prereq with an invalid platform name
        prereq2 = self._newwd.joinpath("prereq2")
        platform3 = prereq2.joinpath("MSDOS")
        Path.mkdir(platform3, parents=True)
        prereq2 = prerequisite.Prerequisite(prereq2)

        uut = prerequisite.Prerequisites.create()
        actual = uut.get_dict()
        self.assertDictEqual(actual["prereqs"]["prereq1"].get_dict(), prereq1.get_dict())
        self.assertDictEqual(actual["prereqs"]["prereq2"].get_dict(), prereq2.get_dict())
        self.assertEqual(actual["location"], str(self._newwd))



if __name__ == '__main__':
    unittest.main()
