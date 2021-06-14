#!/usr/bin/env python3

# Test code in property_spec_parser.py
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


class TestPropertySpecParser(unittest.TestCase):
    def setUp(self):
        self.file_prefix = "test_property_spec_parser_"

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
        self.assertIsInstance(xml_tools.parser.property_spec_parser.PropertySpecParser(
            filename), xml_tools.parser.property_spec_parser.PropertySpecParser)

    def test_context_manager(self):
        filename = self.write_test_files(["<property></property>"])[0]
        with xml_tools.parser.property_spec_parser.PropertySpecParser(filename) as parser:
            self.assertIsInstance(
                parser, xml_tools.parser.property_spec_parser.PropertySpecParser)

    def test_clean_description_text_no_whitespace(self):
        filename = self.write_test_files(["<property></property>"])[0]
        parser = xml_tools.parser.property_spec_parser.PropertySpecParser(
            filename)

        test_string = "".join([
            "This is a test1.",
            "This is a test2.",
            "This is a test3."])

        self.assertEqual(parser._clean_description_text(test_string),
                         test_string)

    def test_clean_description_text_whitespace(self):
        filename = self.write_test_files(["<property></property>"])[0]
        parser = xml_tools.parser.property_spec_parser.PropertySpecParser(
            filename)

        expected_string = "\n".join([
            "This is a test1.",
            "This is a test2.",
            "This is a test3."])

        test_strings = [
            "\n".join([
                "   This is a test1.",
                "   This is a test2.",
                "   This is a test3."]),
            "\n".join([
                "",
                "   This is a test1.",
                "   This is a test2.",
                "   This is a test3."]),
            "\n".join([
                "     ",
                "   This is a test1.",
                "   This is a test2.",
                "   This is a test3."]),
            "\n".join([
                "   This is a test1.",
                "   This is a test2.",
                "   This is a test3.",
                ""]),
            "\n".join([
                "   This is a test1.",
                "   This is a test2.",
                "   This is a test3.",
                "      "])]

        for test_string in test_strings:
            self.assertEqual(parser._clean_description_text(test_string),
                             expected_string)

    def test_clean_description_text_whitespace2(self):
        filename = self.write_test_files(["<property></property>"])[0]
        parser = xml_tools.parser.property_spec_parser.PropertySpecParser(
            filename)

        expected_string = "\n".join([
            "This is a test1.",
            " This is a test2.",
            "    This is a test3."])

        test_strings = [
            "\n".join([
                "     This is a test1.",
                "      This is a test2.",
                "         This is a test3."]),
            "\n".join([
                "                            ",
                "     This is a test1. ",
                "      This is a test2.",
                "         This is a test3.    "])]

        for test_string in test_strings:
            self.assertEqual(parser._clean_description_text(test_string),
                             expected_string)

    def test_get_description(self):
        filename = self.write_test_files(["<property></property>"])[0]
        parser = xml_tools.parser.property_spec_parser.PropertySpecParser(
            filename)

        description = "This is a description test."

        xml_string = "".join([
            "<property name=\"test\" value=\"12\" ",
            "description=\"",
            description,
            "\"/>\n"])

        xml_element = ET.fromstring(xml_string)

        self.assertEqual(parser._get_description(xml_element), description)

    def test_get_struct_property_type(self):
        filename = self.write_test_files(["<property></property>"])[0]
        parser = xml_tools.parser.property_spec_parser.PropertySpecParser(
            filename)

        expected_result = {"test_member1": {"type": {"data_type": "ulong"}},
                           "test_member2": {
                               "type": {
                                   "data_type": "enum",
                                   "enums": ["test1", "test2"]}},
                           "test_member3": {"type": {"data_type": "float"}}}

        xml_string = "\n".join([
            "<property name='test' type='struct'>",
            "  <member name='test_member1' type='ulong'/>",
            "  <member name='test_member2' type='enum' enums='test1,test2'/>",
            "  <member name='test_member3' type='float'/>",
            "</property>"])

        xml_element = ET.fromstring(xml_string)

        self.assertEqual(parser._get_struct_property_type(xml_element),
                         expected_result)

    def test_get_struct_property_type_nested_member(self):
        filename = self.write_test_files(["<property></property>"])[0]
        parser = xml_tools.parser.property_spec_parser.PropertySpecParser(
            filename)

        xml_string = "\n".join([
            "<property name='test' type='struct'>",
            "  <member name='test_member1' type='ulong'/>",
            "  <member name='test_member2' type='struct'>"
            "    <member name='nested_test_member1' type='ulong'/>",
            "  </member>",
            "  <member name='test_member3' type='float'/>",
            "</property>"])

        xml_element = ET.fromstring(xml_string)
        with self.assertRaises(ValueError):
            test = parser._get_struct_property_type(xml_element)

    def test_get_property_type_struct(self):
        filename = self.write_test_files(["<property></property>"])[0]
        parser = xml_tools.parser.property_spec_parser.PropertySpecParser(
            filename)

        expected_result = {
            "data_type": "struct",
            "members": {
                "test_member1": {"type": {"data_type": "ulong"}},
                "test_member2": {"type": {"data_type": "float"}}}}

        xml_string = "\n".join([
            "<property name='test' type='struct'>",
            "  <member name='test_member1' type='ulong'/>",
            "  <member name='test_member2' type='float'/>",
            "</property>"])

        xml_element = ET.fromstring(xml_string)

        self.assertEqual(parser._get_property_type(xml_element),
                         expected_result)

    def test_get_property_type_enum(self):
        filename = self.write_test_files(["<property></property>"])[0]
        parser = xml_tools.parser.property_spec_parser.PropertySpecParser(
            filename)

        expected_result = {
            "data_type": "enum",
            "enums": ["Test1", "test2", "tesT3"]}

        xml_string = "".join([
            "<property name='test' type='enum' enums=' Test1,test2, tesT3 '>",
            "</property>"])

        xml_element = ET.fromstring(xml_string)

        self.assertEqual(parser._get_property_type(xml_element),
                         expected_result)

    def test_get_property_type_enum_no_enums(self):
        filename = self.write_test_files(["<property></property>"])[0]
        parser = xml_tools.parser.property_spec_parser.PropertySpecParser(
            filename)

        xml_string = "".join([
            "<property name='test' type='enum'>",
            "</property>"])

        xml_element = ET.fromstring(xml_string)

        with self.assertRaises(ValueError):
            test = parser._get_property_type(xml_element)

    def test_get_property_type_string(self):
        filename = self.write_test_files(["<property></property>"])[0]
        parser = xml_tools.parser.property_spec_parser.PropertySpecParser(
            filename)

        expected_result = {
            "data_type": "string",
            "stringlength": "874"}

        xml_string = "".join([
            "<property name='test' type='string' stringlength=' 874'>",
            "</property>"])

        xml_element = ET.fromstring(xml_string)

        self.assertEqual(parser._get_property_type(xml_element),
                         expected_result)

    def test_get_property_type_string_no_length(self):
        filename = self.write_test_files(["<property></property>"])[0]
        parser = xml_tools.parser.property_spec_parser.PropertySpecParser(
            filename)

        xml_string = "".join([
            "<property name='test' type='string'>",
            "</property>"])

        xml_element = ET.fromstring(xml_string)

        with self.assertRaises(ValueError):
            test = parser._get_property_type(xml_element)

    def test_get_property_type_array_1d(self):
        filename = self.write_test_files(["<property></property>"])[0]
        parser = xml_tools.parser.property_spec_parser.PropertySpecParser(
            filename)

        expected_result = {
            "data_type": "short",
            "arraydimensions": ["67"]}

        xml_strings = [
            "".join([
                "<property name='test' type='short' arraydimensions=' 67 '>",
                "</property>"]),
            "".join([
                "<property name='test' type='short' arraylength='67'>",
                "</property>"])]

        for xml_string in xml_strings:
            xml_element = ET.fromstring(xml_string)
            self.assertEqual(parser._get_property_type(xml_element),
                             expected_result)

    def test_get_property_type_array_multi_dimension(self):
        filename = self.write_test_files(["<property></property>"])[0]
        parser = xml_tools.parser.property_spec_parser.PropertySpecParser(
            filename)

        expected_result = {
            "data_type": "long",
            "arraydimensions": ["1", "3", "89"]}

        xml_string = "".join([
            "<property name='test' type='long' arraydimensions=' 1, 3 ,89 '>",
            "</property>"])

        xml_element = ET.fromstring(xml_string)
        self.assertEqual(parser._get_property_type(xml_element),
                         expected_result)

    def test_get_property_type_sequence(self):
        filename = self.write_test_files(["<property></property>"])[0]
        parser = xml_tools.parser.property_spec_parser.PropertySpecParser(
            filename)

        expected_result = {
            "data_type": "double",
            "sequencelength": "1254"}

        xml_string = "".join([
            "<property name='test' type='double' sequencelength='1254 '>",
            "</property>"])

        xml_element = ET.fromstring(xml_string)

        self.assertEqual(parser._get_property_type(xml_element),
                         expected_result)

    def test_get_property_type_sequence_of_array(self):
        filename = self.write_test_files(["<property></property>"])[0]
        parser = xml_tools.parser.property_spec_parser.PropertySpecParser(
            filename)

        expected_result = {
            "data_type": "double",
            "sequencelength": "10",
            "arraydimensions": ["1", "2", "3"]}

        xml_string = "".join([
            "<property name='test' type='double' ",
            "sequencelength='10' ",
            "arraydimensions='1,2,3'>",
            "</property>"])

        xml_element = ET.fromstring(xml_string)

        self.assertEqual(parser._get_property_type(xml_element),
                         expected_result)

    def test_get_property_type(self):
        filename = self.write_test_files(["<property></property>"])[0]
        parser = xml_tools.parser.property_spec_parser.PropertySpecParser(
            filename)

        types = ["ulong", "LONG", "short   ", "  Float", "uLongLong"]
        expected_values = ["ulong", "long", "short", "float", "ulonglong"]
        for expected, type_ in zip(expected_values, types):

            xml_string = "".join([
                "<property name='test' type='",
                type_,
                "'/>"])
            expected_dict = {"data_type": expected}

            xml_element = ET.fromstring(xml_string)
            self.assertEqual(
                parser._get_property_type(xml_element, "test"), expected_dict)

    def test_get_property_access(self):
        filename = self.write_test_files(["<property></property>"])[0]
        parser = xml_tools.parser.property_spec_parser.PropertySpecParser(
            filename)

        access_values = [
            "".join([
                "initial='false' parameter='false' ",
                "readable='false' volatile='true' ",
                "writable='false'"]),
            "".join([
                "readable='False' writable='true'"])]

        expected_values = [
            {"initial":  False, "parameter": False,
             "readable": False, "volatile":  True,
             "writable": False},
            {"initial":  False, "parameter": False,
             "readable": False, "volatile":  False,
             "writable": True}
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
        parser = xml_tools.parser.property_spec_parser.PropertySpecParser(
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
            "readable": False, "volatile":  False,
            "writable": True}

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
        parser = xml_tools.parser.property_spec_parser.PropertySpecParser(
            filename)

        expected_access = {
            "initial": False, "parameter": False,
            "readable": False, "volatile":  False,
            "writable": True}
        expected_access2 = {
            "initial": False, "parameter": False,
            "readable": True, "volatile":  False,
            "writable": False}

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
