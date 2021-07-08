#!/usr/bin/env python3

# Testing of code in build.py
#
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
# A PARTICULAR PURPOSE. See the GNU Lesser General Public License for
# more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


import pathlib
import shutil
import unittest
import uuid

from ocpi_documentation.build import build
from ocpi_documentation.create import create


class TestBuild(unittest.TestCase):
    def setUp(self):
        self.test_directory = pathlib.Path(
            f"/tmp/ocpi_doc_testing-{uuid.uuid4()}")
        self.test_directory.mkdir()
        self.test_directory.joinpath("components").joinpath(
            "a_library").joinpath("abc_xyz_component.hdl").mkdir(parents=True)
        self.test_directory.joinpath("hdl").joinpath("primitives").joinpath(
            "a_library").joinpath("abc_xyz_primitive").mkdir(parents=True)
        self.test_directory.joinpath("specs").mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.test_directory)

    def test_build(self):
        # Allow use of create as tested without using build
        create(
            self.test_directory.joinpath("components").joinpath("a_library"),
            "component", "abc_xyz_component")

        build(self.test_directory.joinpath("components").joinpath(
            "a_library").joinpath("abc_xyz_component.comp"))

        self.assertTrue(
            self.test_directory.joinpath("components").joinpath(
                "a_library").joinpath("abc_xyz_component.comp").joinpath(
                "gen/doc").is_dir())

        self.assertTrue(
            self.test_directory.joinpath("components").joinpath(
                "a_library").joinpath("abc_xyz_component.comp").joinpath(
                "gen/doc").joinpath("abc_xyz_component-index.html").is_file(
            ))
