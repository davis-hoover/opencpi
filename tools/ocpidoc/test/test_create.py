#!/usr/bin/env python3.6

# Testing of code in create.py
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


import datetime
import pathlib
import shutil
import unittest
import uuid

from ocpi_documentation.create import _template_to_specific, create


class TestTemplateToSpecific(unittest.TestCase):
    def test_no_change(self):
        some_string = (
            "This is a line of text.\n" +
            "This is another line of text.\n" +
            "Word in 'escape' characters but not an expected item:\n" +
            "  Something and %%SOMETHING%% should be unchanged.\n")

        self.assertEqual(some_string,
                         _template_to_specific(some_string, "a_name",
                                               "an_authoring_model",
                                               "a_library"))

    def test_name_change(self):
        some_string = (
            "Name to change (proper): %%NAME-PROPER%%.\n" +
            "Name to change (code): %%NAME-CODE%%.\n" +
            "Word in 'escape' characters but not an expected item:\n" +
            "  Something and %%SOMETHING%% should be unchanged.\n")
        expected_string = (
            "Name to change (proper): A name.\n" +
            "Name to change (code): a_name.\n" +
            "Word in 'escape' characters but not an expected item:\n" +
            "  Something and %%SOMETHING%% should be unchanged.\n")

        self.assertEqual(expected_string, _template_to_specific(
            some_string, "a_name", "an_authoring_model", "a_project_prefix",
            "a_project", "a_library"))

    def test_year_change(self):
        some_string = (
            "Year to change: %%YEAR%%.\n" +
            "Word in 'escape' characters but not an expected item:\n" +
            "  Something and %%SOMETHING%% should be unchanged.\n")
        current_year = datetime.datetime.now().year
        expected_string = (
            f"Year to change: {current_year}.\n" +
            "Word in 'escape' characters but not an expected item:\n" +
            "  Something and %%SOMETHING%% should be unchanged.\n")

        self.assertEqual(expected_string, _template_to_specific(
            some_string, "a_name", "an_authoring_model", "a_project_prefix",
            "a_project", "a_library"))

    def test_project_prefix_changes(self):
        some_string = (
            "Project prefix to change: %%PROJECT_PREFIX%%.\n" +
            "Word in 'escape' characters but not an expected item:\n" +
            "  Something and %%SOMETHING%% should be unchanged.\n")
        expected_string = (
            "Project prefix to change: a_project_prefix.\n" +
            "Word in 'escape' characters but not an expected item:\n" +
            "  Something and %%SOMETHING%% should be unchanged.\n")

        self.assertEqual(expected_string, _template_to_specific(
            some_string, "a_name", "an_authoring_model", "a_project_prefix",
            "a_project", "a_library"))

    def test_project_changes(self):
        some_string = (
            "Project to change: %%PROJECT%%.\n" +
            "Word in 'escape' characters but not an expected item:\n" +
            "  Something and %%SOMETHING%% should be unchanged.\n")
        expected_string = (
            "Project to change: a_project.\n" +
            "Word in 'escape' characters but not an expected item:\n" +
            "  Something and %%SOMETHING%% should be unchanged.\n")

        self.assertEqual(expected_string, _template_to_specific(
            some_string, "a_name", "an_authoring_model", "a_project_prefix",
            "a_project", "a_library"))

    def test_authoring_model_changes(self):
        some_string = (
            "Authoring model to change: %%AUTHORING_MODEL%%.\n" +
            "Word in 'escape' characters but not an expected item:\n" +
            "  Something and %%SOMETHING%% should be unchanged.\n")
        expected_string = (
            "Authoring model to change: AN_AUTHORING_MODEL.\n" +
            "Word in 'escape' characters but not an expected item:\n" +
            "  Something and %%SOMETHING%% should be unchanged.\n")

        self.assertEqual(expected_string, _template_to_specific(
            some_string, "a_name", "an_authoring_model", "a_project_prefix",
            "a_project", "a_library"))

    def test_library_change(self):
        some_string = (
            "Library to change: %%LIBRARY%%.\n" +
            "Word in 'escape' characters but not an expected item:\n" +
            "  Something and %%SOMETHING%% should be unchanged.\n")
        expected_string = (
            "Library to change: a_library.\n" +
            "Word in 'escape' characters but not an expected item:\n" +
            "  Something and %%SOMETHING%% should be unchanged.\n")

        self.assertEqual(expected_string, _template_to_specific(
            some_string, "a_name", "an_authoring_model", "a_project_prefix",
            "a_project", "a_library"))


class TestCreate(unittest.TestCase):
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

    def test_create_component(self):
        create(
            self.test_directory.joinpath("components").joinpath("a_library"),
            "component",
            "abc_xyz_component")

        self.assertTrue(
            self.test_directory.joinpath("components").joinpath(
                "a_library").joinpath(f"abc_xyz_component.comp").is_dir())
        self.assertTrue(
            self.test_directory.joinpath("components").joinpath(
                "a_library").joinpath(f"abc_xyz_component.comp").joinpath(
                "abc_xyz_component-index.rst").is_file())
        self.assertTrue(
            self.test_directory.joinpath("components").joinpath(
                "a_library").joinpath(f"abc_xyz_component.comp").joinpath(
                "abc_xyz_component-test.rst").is_file())
        self.assertTrue(
            self.test_directory.joinpath("components").joinpath(
                "a_library").joinpath(f"abc_xyz_component.comp").joinpath(
                "example_app.xml").is_file())

    def test_create_worker(self):
        create(
            self.test_directory.joinpath("components").joinpath(
                "a_library").joinpath("abc_xyz_component.hdl"),
            "worker",
            "abc_xyz_worker")

        self.assertTrue(
            self.test_directory.joinpath("components").joinpath(
                "a_library").joinpath("abc_xyz_component.hdl").joinpath(
                "abc_xyz_worker-worker.rst").is_file())

    def test_create_primitive(self):
        create(
            self.test_directory.joinpath("hdl").joinpath("primitives").joinpath(
                "a_library").joinpath("abc_xyz_primitive"),
            "primitive", "abc_xyz_primitive")

        self.assertTrue(
            self.test_directory.joinpath("hdl").joinpath(
                "primitives").joinpath("a_library").joinpath(
                "abc_xyz_primitive").joinpath(
                "abc_xyz_primitive-primitive.rst").is_file())

    def test_create_protocol(self):
        create(self.test_directory.joinpath("specs"), "protocol", "a_protocol")

        self.assertTrue(
            self.test_directory.joinpath("specs").joinpath(
                "a_protocol-protocol.rst").is_file())

    def test_create_component_library(self):
        create(
            self.test_directory.joinpath("components").joinpath("a_library"),
            "component-library",
            "a_library")

        self.assertTrue(
            self.test_directory.joinpath("components").joinpath(
                "a_library").joinpath("a_library-library.rst").is_file())

    def test_create_primitive_library(self):
        create(
            self.test_directory.joinpath("hdl").joinpath(
                "primitives").joinpath("a_library"),
            "primitive-library", "a_library")

        self.assertTrue(
            self.test_directory.joinpath("hdl").joinpath(
                "primitives").joinpath("a_library").joinpath(
                "a_library-library.rst").is_file())

    def test_create_component_directory(self):
        create(self.test_directory.joinpath("components"),
               "components-directory")

        self.assertTrue(
            self.test_directory.joinpath("components").joinpath(
                "components.rst").is_file())

    def test_create_primitive_directory(self):
        create(self.test_directory.joinpath("hdl").joinpath("primitives"),
               "primitives-directory")

        self.assertTrue(
            self.test_directory.joinpath("hdl").joinpath(
                "primitives").joinpath("primitives.rst").is_file())

    def test_create_specs_directory(self):
        create(self.test_directory.joinpath("specs"), "specs-directory")

        self.assertTrue(
            self.test_directory.joinpath("specs").joinpath(
                "specs.rst").is_file())

    def test_create_project_directory(self):
        create(self.test_directory, "project-directory")
        self.assertTrue(
            self.test_directory.joinpath("index.rst").is_file())
