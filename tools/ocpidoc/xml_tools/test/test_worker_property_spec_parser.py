#!/usr/bin/env python3

# Test code in worker_property_spec_parser.py
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


import unittest
import os
import sys
import xml.etree.ElementTree as ET

import xml_tools


class TestWorkerPropertySpecParser(unittest.TestCase):
    def setUp(self):
        self.file_prefix = "test_worker_property_spec_parser_"

    def tearDown(self):
        counter = 0
        while True:
            filename = self.file_prefix + str(counter) + ".xml"
            if os.path.exists(filename):
                os.remove(filename)
                counter += 1
            else:
                break

    def write_test_files(self, strings):
        files = []
        for counter, string_ in enumerate(strings):
            filename = self.file_prefix + str(counter) + ".xml"
            with open(filename, "w") as open_file:
                open_file.write(string_)
            files.append(filename)
        return files

    def test_constructor(self):
        filename = self.write_test_files(["<property></property>"])[0]
        self.assertIsInstance(
            xml_tools.parser.worker_property_spec_parser.WorkerPropertySpecParser(filename), xml_tools.parser.worker_property_spec_parser.WorkerPropertySpecParser)

    def test_context_manager(self):
        filename = self.write_test_files(["<property></property>"])[0]
        with xml_tools.parser.worker_property_spec_parser.WorkerPropertySpecParser(filename) as parser:
            self.assertIsInstance(
                parser, xml_tools.parser.worker_property_spec_parser.WorkerPropertySpecParser)

    def test_get_property_access(self):
        filename = self.write_test_files(["<property></property>"])[0]
        parser = xml_tools.parser.worker_property_spec_parser.WorkerPropertySpecParser(
            filename)

        access_values = [
            "".join([
                "initial='false' parameter='false' ",
                "readable='false' readback='false' ",
                "readsync='false' volatile='true' ",
                "writable='false' writesync='false' ",
                "readerror='false' writeerror='false' ",
                "padding='false'"]),
            "".join([
                "readable='False' writable='true'"])]

        expected_values = [
            {"initial":  False, "parameter": False,
             "readable": False, "readback":  False,
             "readsync": False, "volatile":  True,
             "writable": False,  "writesync": False,
             "readerror": False, "writeerror": False,
             "padding": False},
            {"initial":  False, "parameter": False,
             "readable": False, "readback":  False,
             "readsync": False, "volatile":  False,
             "writable": True,  "writesync": False,
             "readerror": False, "writeerror": False,
             "padding": False}
        ]
        for expected, access_value in zip(expected_values, access_values):

            xml_string = "".join([
                "<property name='test' type='ulong' ",
                access_value,
                "/>"])
            expected_dict = {"test": {"type": {"data_type": "ulong"},
                                      "access": expected,
                                      "description": None,
                                      "default": None,
                                      "value": None}}

            xml_element = ET.fromstring(xml_string)
            self.assertEqual(
                parser._get_property(xml_element), expected_dict)

    def test_get_property(self):
        filename = self.write_test_files(["<property></property>"])[0]
        parser = xml_tools.parser.worker_property_spec_parser.WorkerPropertySpecParser(
            filename)

        xml_string = " ".join([
            "<property name='test' type='ulong'",
            "readable='False' writable='true'",
            "description='Test property'",
            "default='85'",
            "value='439875'",
            "/>"])

        expected_access = {
            "initial": False, "parameter": False,
            "readable": False, "readback":  False,
            "readsync": False, "volatile":  False,
            "writable": True,  "writesync": False,
            "readerror": False, "writeerror": False,
            "padding": False}

        expected_dict = {"test": {"type": {"data_type": "ulong"},
                                  "access": expected_access,
                                  "description": "Test property",
                                  "default": "85",
                                  "value": "439875"}}

        xml_element = ET.fromstring(xml_string)
        self.assertEqual(
            parser._get_property(xml_element), expected_dict)

    def test_get_properties(self):

        xml_string = "".join([
            "<property>\n",
            "<property name='test' type='ulong' ",
            "readable='False' writable='true' ",
            "description='Test property' ",
            "value='457'/>\n",
            "<property name='test2' type='double' ",
            "readable='true' writable='false' ",
            "description='Test property2' ",
            "default='90'/>\n",
            "</property>"])

        filename = self.write_test_files([xml_string])[0]
        parser = xml_tools.parser.worker_property_spec_parser.WorkerPropertySpecParser(
            filename)

        expected_access = {
            "initial": False, "parameter": False,
            "readable": False, "readback":  False,
            "readsync": False, "volatile":  False,
            "writable": True,  "writesync": False,
            "readerror": False, "writeerror": False,
            "padding": False}
        expected_access2 = {
            "initial": False, "parameter": False,
            "readable": True, "readback":  False,
            "readsync": False, "volatile":  False,
            "writable": False,  "writesync": False,
            "readerror": False, "writeerror": False,
            "padding": False}

        expected_dict = {"test": {
            "type": {"data_type": "ulong"},
            "access": expected_access,
            "description": "Test property",
            "default": None,
            "value": "457"},
            "test2": {
            "type": {"data_type": "double"},
            "access": expected_access2,
            "description": "Test property2",
            "default": "90",
            "value": None},

        }

        xml_element = ET.fromstring(xml_string)
        self.assertEqual(
            parser.get_properties(), expected_dict)

    def test_get_spec_property(self):
        filename = self.write_test_files(["<property></property>"])[0]
        parser = xml_tools.parser.worker_property_spec_parser.WorkerPropertySpecParser(
            filename)

        xml_string = " ".join([
            "<specproperty name='test' ",
            "writesync='true' writable='true' ",
            "readerror='false' ",
            "value='1234'",
            "/>"])

        expected_access = {
            "parameter": None, "readback":  None,
            "readsync": None, "writable": True,
            "writesync": True, "readerror": False,
            "writeerror": None}

        expected_dict = {"test": {"access": expected_access,
                                  "default": None,
                                  "value": "1234"}}

        xml_element = ET.fromstring(xml_string)
        self.assertEqual(
            parser._get_spec_property(xml_element), expected_dict)

    def test_get_spec_properties(self):

        xml_string = "".join([
            "<rccworker>\n",
            "<specproperty name='test' ",
            "writeerror='True' readback='true' ",
            "value='4575'/>\n",
            "<specproperty name='test2' ",
            "parameter='true' readsync='false' ",
            "default='89.07'/>\n",
            "</rccworker>"])

        filename = self.write_test_files([xml_string])[0]
        parser = xml_tools.parser.worker_property_spec_parser.WorkerPropertySpecParser(
            filename)

        expected_access = {
            "parameter": None, "readback": True,
            "readsync": None, "writable": None,
            "writesync": None, "readerror": None,
            "writeerror": True}
        expected_access2 = {
            "parameter": True, "readback":  None,
            "readsync": False, "writable": None,
            "writesync": None, "readerror": None,
            "writeerror": None}

        expected_dict = {"test": {
            "access": expected_access,
            "default": None,
            "value": "4575"},
            "test2": {
            "access": expected_access2,
            "default": "89.07",
            "value": None}
        }

        xml_element = ET.fromstring(xml_string)
        self.assertEqual(
            parser.get_spec_properties(), expected_dict)
