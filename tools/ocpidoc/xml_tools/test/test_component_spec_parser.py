#!/usr/bin/env python3

# Test code in component_spec_parser.py
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


class TestComponentSpecParser(unittest.TestCase):
    def setUp(self):
        self.file_prefix = "test_component_spec_parser_"

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
        filename = self.write_test_files(
            ["<componentspec></componentspec>"])[0]
        self.assertIsInstance(
            xml_tools.parser.component_spec_parser.ComponentSpecParser(filename), xml_tools.parser.component_spec_parser.ComponentSpecParser)

    def test_constructor_wrong_xml(self):
        filename = self.write_test_files(
            ["<property></property>"])[0]
        with self.assertRaises(ValueError):
            parser = xml_tools.parser.component_spec_parser.ComponentSpecParser(
                filename)

    def test_context_manager(self):
        filename = self.write_test_files(
            ["<componentspec></componentspec>"])[0]
        with xml_tools.parser.component_spec_parser.ComponentSpecParser(filename) as parser:
            self.assertIsInstance(
                parser, xml_tools.parser.component_spec_parser.ComponentSpecParser)

    def test_get_port(self):
        filename = self.write_test_files(
            ["<componentspec></componentspec>"])[0]
        parser = xml_tools.parser.component_spec_parser.ComponentSpecParser(
            filename)

        xml_strings = [
            "<port name='input'/>",
            "<port name='input2' protocol='stream-protocol.xml'/>",
            "<port name='Test' ></port>",
            "<port name='input3 ' producer='false' optional='true'></port>",
            "<port name='INPUT' producer='false' optional='false'></port>",
            "<port name='in' producer='false' numberofopcodes='8'></port>"]

        expected_values = [
            {"input": {"protocol": None, "optional": False}},
            {"input2": {"protocol": "stream-protocol.xml", "optional": False}},
            {"Test": {"protocol": None, "optional": False}},
            {"input3": {"protocol": None, "optional": True}},
            {"INPUT": {"protocol": None, "optional": False}},
            {"in":
                {"protocol": None, "optional": False, "numberofopcodes": "8"}}]

        for expected, xml_string in zip(expected_values, xml_strings):
            xml_element = ET.fromstring(xml_string)
            self.assertEqual(parser._get_port(xml_element), expected)

    def test_get_output_ports(self):

        xml_string = "\n".join([
            "<componentspec>",
            "<datainterfacespec name='input' protocol='stream_in-prot'/>",
            "<datainterfacespec name='out' producer='true' optional='false'/>",
            "<port name='out2' producer='True' protocol='stream-prot'/>",
            "<port name='in' producer='false' optional='true' ></port>",
            "</componentspec>"])

        filename = self.write_test_files([xml_string])[0]
        parser = xml_tools.parser.component_spec_parser.ComponentSpecParser(
            filename)

        expected_value = {
            "out": {"protocol": None, "optional": False},
            "out2": {"protocol": "stream-prot", "optional": False}}

        self.assertEqual(parser.get_output_ports(), expected_value)

    def test_get_input_ports(self):

        xml_string = "\n".join([
            "<componentspec>",
            "<datainterfacespec name='input' protocol='stream_in-prot'/>",
            "<datainterfacespec name='out' producer='true' optional='false'/>",
            "<port name='out2' producer='True' protocol='stream-prot'/>",
            "<port name='in' producer='false' optional='true' ></port>",
            "</componentspec>"])

        filename = self.write_test_files([xml_string])[0]
        parser = xml_tools.parser.component_spec_parser.ComponentSpecParser(
            filename)

        expected_value = {
            "input": {"protocol": "stream_in-prot", "optional": False},
            "in": {"protocol": None, "optional": True}}

        self.assertEqual(parser.get_input_ports(), expected_value)

    def test_get_dictionary(self):

        xml_string = "".join([
            "<componentspec>\n",
            "<Property name='test_prop' type='ushort' default='1' ",
            "description='This is a test property' arraydimensions='10,2'/>\n",
            "<property name='test_prop2' type='enum' default='test' ",
            " enums='test , test2' writable='true'/>\n",
            "<port name='input' producer='false' protocol='test-prot'/>\n",
            "<port name='input2' producer='false' optional='true' />\n",
            "<port name='output' producer='True' protocol='stream-prot'/>\n",
            "</componentspec>"])

        filename = self.write_test_files([xml_string])[0]
        parser = xml_tools.parser.component_spec_parser.ComponentSpecParser(
            filename)

        expected_value = {
            "inputs": {
                "input": {"protocol": "test-prot", "optional": False},
                "input2": {"protocol": None, "optional": True}},
            "outputs": {
                "output": {"protocol": "stream-prot", "optional": False}},
            "properties": {
                "test_prop": {
                    "type": {"data_type": "ushort",
                             "arraydimensions": ["10", "2"]},
                    "access": {"initial":  False, "parameter": False,
                               "volatile":  False, "writable": False},
                    "description": "This is a test property",
                    "default": "1",
                    "value": None},
                "test_prop2": {
                    "type": {"data_type": "enum", "enums": ["test", "test2"]},
                    "access": {"initial":  False, "parameter": False,
                               "volatile":  False, "writable": True},
                    "description": None,
                    "default": "test",
                    "value": None}}}

        self.assertEqual(parser.get_dictionary(), expected_value)
