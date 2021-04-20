#!/usr/bin/env python3

# Test code in build_parser.py
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


class TestBuildParser(unittest.TestCase):
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
            ["<build></build>"])[0]
        self.assertIsInstance(
            xml_tools.parser.build_parser.BuildParser(filename), xml_tools.parser.build_parser.BuildParser)

    def test_constructor_wrong_xml(self):
        filename = self.write_test_files(
            ["<property></property>"])[0]
        with self.assertRaises(ValueError):
            parser = xml_tools.parser.build_parser.BuildParser(filename)

    def test_context_manager(self):
        filename = self.write_test_files(
            ["<build></build>"])[0]
        with xml_tools.parser.build_parser.BuildParser(filename) as parser:
            self.assertIsInstance(
                parser, xml_tools.parser.build_parser.BuildParser)

    def test_get_parameters(self):
        filename = self.write_test_files(["<build></build>"])[0]
        parser = xml_tools.parser.build_parser.BuildParser(filename)

        xml_string = "".join([
            "<build>\n",
            "  <parameter name='param_a' value='1'/>\n",
            "  <parameter name='param_b' values='1,2'/>\n",
            "  <configuration>\n",
            "    <parameter name='param_c' value='10'/>\n",
            "  </configuration>\n",
            "</build>"])

        xml_element = ET.fromstring(xml_string)

        expected_value = {"param_a": ["1"], "param_b": ["1", "2"]}

        self.assertEqual(parser._get_parameters(xml_element), expected_value)

    def test_get_configurations_with_no_id(self):
        filename = self.write_test_files(["<build></build>"])[0]
        parser = xml_tools.parser.build_parser.BuildParser(filename)

        xml_string = "".join([
            "<build>\n",
            "  <parameter name='param_a' value='1'/>\n",
            "  <configuration>\n",
            "    <parameter name='param_b' value='10'/>\n",
            "    <parameter name='param_c' values='100,101'/>\n",
            "  </configuration>\n",
            "  <configuration>\n",
            "    <parameter name='param_c' values='1,10,1000'/>\n",
            "  </configuration>\n",
            "  <configuration id='0'>\n",
            "    <parameter name='param_c' value='10000'/>\n",
            "  </configuration>\n",
            "</build>"])

        xml_element = ET.fromstring(xml_string)

        expected_value = [{"param_b": ["10"], "param_c": ["100", "101"]},
                          {"param_c": ["1", "10", "1000"]}]

        self.assertEqual(
            parser._get_configurations_with_no_id(xml_element), expected_value)

    def test_get_configurations_with_id(self):
        filename = self.write_test_files(["<build></build>"])[0]
        parser = xml_tools.parser.build_parser.BuildParser(filename)

        xml_string = "".join([
            "<build>\n",
            "  <parameter name='param_a' value='1'/>\n",
            "  <configuration id='1'>\n",
            "    <parameter name='param_b' value='10'/>\n",
            "    <parameter name='param_c' value='100'/>\n",
            "  </configuration>\n",
            "  <configuration>\n",
            "    <parameter name='param_c' values='1,10,1000'/>\n",
            "  </configuration>\n",
            "  <configuration id='0'>\n",
            "    <parameter name='param_c' value='10000'/>\n",
            "  </configuration>\n",
            "</build>"])

        xml_element = ET.fromstring(xml_string)

        expected_value = {"1":
                          {"param_b": "10", "param_c": "100"},
                          "0":
                          {"param_c": "10000"}}

        self.assertEqual(
            parser._get_configurations_with_id(xml_element), expected_value)

    def test_get_dictionary(self):

        xml_string = "\n".join([
            "<build>",
            "  <parameter name='param_a' value='1'/>",
            "  <parameter name='param_b' values='10,11'/>",
            "  <configuration id='0'>",
            "    <parameter name='param_a' value='20'/>",
            "    <parameter name='param_b' value='30'/>",
            "    <parameter name='param_c' value='60'/>",
            "  </configuration>",
            "  <configuration id='1'>",
            "    <parameter name='param_a' value='2'/>",
            "    <parameter name='param_b' value='3'/>",
            "    <parameter name='param_c' value='6'/>",
            "  </configuration>",
            "  <configuration>",
            "    <parameter name='param_c' value='200'/>",
            "  </configuration>",
            "  <configuration>",
            "    <parameter name='param_c' values='300,400,500'/>",
            "  </configuration>",
            "</build>"])

        filename = self.write_test_files([xml_string])[0]
        parser = xml_tools.parser.build_parser.BuildParser(filename)

        expected_value = {
            "global_parameters": {
                "param_a": ["1"],
                "param_b": ["10", "11"]},
            "configurations_no_id": [
                {"param_c": ["200"]},
                {"param_c": ["300", "400", "500"]}],
            "configurations": {
                "0": {
                    "param_a": "20",
                    "param_b": "30",
                    "param_c": "60"},
                "1": {
                    "param_a": "2",
                    "param_b": "3",
                    "param_c": "6"}}}

        self.assertEqual(
            parser.get_dictionary(), expected_value)

    def test_get_dictionary_with_ocs(self):

        build_xml_string = "\n".join([
            "<build>",
            "  <parameter name='param_a' value='1'/>",
            "  <parameter name='param_b' values='10,11'/>",
            "  <configuration id='0'>",
            "    <parameter name='param_a' value='20'/>",
            "    <parameter name='param_b' value='30'/>",
            "    <parameter name='param_c' value='60'/>",
            "  </configuration>",
            "  <configuration id='1'>",
            "    <parameter name='param_a' value='2'/>",
            "    <parameter name='param_b' value='3'/>",
            "    <parameter name='param_c' value='6'/>",
            "  </configuration>",
            "  <configuration>",
            "    <parameter name='param_c' value='200'/>",
            "  </configuration>",
            "  <configuration>",
            "    <parameter name='param_c' values='300,400,500'/>",
            "  </configuration>",
            "</build>"])

        ocs_xml_string = "\n".join([
            "<componentspec>",
            "  <property name='param_a' parameter='true' default='9832'/>",
            "  <property name='param_b' parameter='true' default='8347'/>",
            "  <property name='ocs_prop' parameter='true' value='47'/>",
            "</componentspec>"])

        build_file, ocs_file = self.write_test_files(
            [build_xml_string, ocs_xml_string])
        parser = xml_tools.parser.build_parser.BuildParser(build_file)

        expected_value = {
            "global_parameters": {
                "param_a": ["1"],
                "param_b": ["10", "11"],
                "ocs_prop": ["47"]},
            "configurations_no_id": [
                {"param_c": ["200"]},
                {"param_c": ["300", "400", "500"]}],
            "configurations": {
                "0": {
                    "param_a": "20",
                    "param_b": "30",
                    "param_c": "60",
                    "ocs_prop": "47"},
                "1": {
                    "param_a": "2",
                    "param_b": "3",
                    "param_c": "6",
                    "ocs_prop": "47"}}}

        self.assertEqual(parser.get_dictionary(
            owd_file=None, ocs_file=ocs_file), expected_value)

    def test_get_dictionary_with_owd(self):

        build_xml_string = "\n".join([
            "<build>",
            "  <parameter name='param_a' value='1'/>",
            "  <parameter name='param_b' values='10,11'/>",
            "  <configuration id='0'>",
            "    <parameter name='param_a' value='20'/>",
            "    <parameter name='param_b' value='30'/>",
            "    <parameter name='param_c' value='60'/>",
            "  </configuration>",
            "  <configuration id='1'>",
            "    <parameter name='param_a' value='2'/>",
            "    <parameter name='param_b' value='3'/>",
            "    <parameter name='param_c' value='6'/>",
            "  </configuration>",
            "  <configuration>",
            "    <parameter name='param_c' value='200'/>",
            "  </configuration>",
            "  <configuration>",
            "    <parameter name='param_c' values='300,400,500'/>",
            "  </configuration>",
            "</build>"])

        ocs_xml_string = "\n".join([
            "<componentspec>",
            "  <property name='param_a' parameter='true' default='9832'/>",
            "  <property name='param_b' parameter='true' default='8347'/>",
            "  <property name='ocs_prop1' parameter='true' value='47'/>",
            "  <property name='ocs_prop2' parameter='true' default='76'/>",
            "</componentspec>"])

        owd_xml_string = "\n".join([
            "<rccworker>",
            "  <property name='param_b' default='321'/>",
            "  <property name='param_c' parameter='true' default='76590'/>",
            "  <property name='owd_prop' parameter='true' default='54'/>",
            "</rccworker>"])

        build_file, ocs_file, owd_file = self.write_test_files(
            [build_xml_string, ocs_xml_string, owd_xml_string])
        parser = xml_tools.parser.build_parser.BuildParser(build_file)

        expected_value = {
            "global_parameters": {
                "param_a": ["1"],
                "param_b": ["10", "11"],
                "param_c": ["76590"],
                "ocs_prop1": ["47"],
                "ocs_prop2": ["76"],
                "owd_prop": ["54"]},
            "configurations_no_id": [
                {"param_c": ["200"]},
                {"param_c": ["300", "400", "500"]}],
            "configurations": {
                "0": {
                    "param_a": "20",
                    "param_b": "30",
                    "param_c": "60",
                    "ocs_prop1": "47",
                    "ocs_prop2": "76",
                    "owd_prop": "54"},
                "1": {
                    "param_a": "2",
                    "param_b": "3",
                    "param_c": "6",
                    "ocs_prop1": "47",
                    "ocs_prop2": "76",
                    "owd_prop": "54"}}}
        self.maxDiff = None
        self.assertEqual(parser.get_dictionary(
            owd_file=owd_file, ocs_file=ocs_file), expected_value)

    def test_get_all_configurations_no_non_id_config(self):

        build_xml_string = "\n".join([
            "<build>",
            "  <parameter name='param_a' value='1'/>",
            "  <parameter name='param_b' values='10,11'/>",
            "  <configuration id='0'>",
            "    <parameter name='param_a' value='20'/>",
            "    <parameter name='param_b' value='30'/>",
            "  </configuration>",
            "  <configuration id='1'>",
            "    <parameter name='param_a' value='2'/>",
            "    <parameter name='param_b' value='3'/>",
            "  </configuration>",
            "</build>"])

        expected_value = [{"param_a": "20", "param_b": "30"},
                          {"param_a": "2", "param_b": "3"},
                          {"param_a": "1", "param_b": "10"},
                          {"param_a": "1", "param_b": "11"}]

        build_file = self.write_test_files([build_xml_string])[0]
        parser = xml_tools.parser.build_parser.BuildParser(build_file)

        self.assertEqual(parser.get_all_configurations(), expected_value)

    def test_get_all_configurations_non_id_config(self):

        build_xml_string = "\n".join([
            "<build>",
            "  <parameter name='param_a' value='1'/>",
            "  <parameter name='param_b' values='10,11'/>",
            "  <parameter name='param_c' values='100,101'/>",
            "  <configuration>",
            "    <parameter name='param_a' value='2'/>",
            "  </configuration>",
            "  <configuration>",
            "    <parameter name='param_c' values='200,201,202'/>",
            "  </configuration>",
            "  <configuration>",
            "    <parameter name='param_b' values='20'/>",
            "    <parameter name='param_c' values='300'/>",
            "  </configuration>",
            "  <configuration>",
            "    <parameter name='param_a' value='2'/>",
            "  </configuration>",
            "</build>"])

        expected_value = [{"param_a": "2", "param_b": "10", "param_c": "100"},
                          {"param_a": "2", "param_b": "10", "param_c": "101"},
                          {"param_a": "2", "param_b": "11", "param_c": "100"},
                          {"param_a": "2", "param_b": "11", "param_c": "101"},
                          {"param_a": "1", "param_b": "10", "param_c": "200"},
                          {"param_a": "1", "param_b": "10", "param_c": "201"},
                          {"param_a": "1", "param_b": "10", "param_c": "202"},
                          {"param_a": "1", "param_b": "11", "param_c": "200"},
                          {"param_a": "1", "param_b": "11", "param_c": "201"},
                          {"param_a": "1", "param_b": "11", "param_c": "202"},
                          {"param_a": "1", "param_b": "20", "param_c": "300"}]

        build_file = self.write_test_files([build_xml_string])[0]
        parser = xml_tools.parser.build_parser.BuildParser(build_file)
        self.assertEqual(parser.get_all_configurations(), expected_value)
