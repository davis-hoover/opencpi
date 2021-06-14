#!/usr/bin/env python3

# Test code in base_parser.py
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
# from xml_tools import xml_tools.parser.base_parser.xml_tools.parser.base_parser.BaseParser


class TestBaseParser(unittest.TestCase):
    def setUp(self):
        self.file_prefix = "test_base_parser_"

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

    def xml_compare(self, xml1, xml2):
        if xml1.tag != xml2.tag:
            return False
        if xml1.text != xml2.text:
            return False
        if xml1.tail != xml2.tail:
            return False
        if xml1.attrib != xml2.attrib:
            return False
        if len(xml1) != len(xml2):
            return False
        return all(
            self.xml_compare(xml1a, xml2a) for xml1a, xml2a in zip(xml1, xml2))

    def test_constructor(self):
        filename = self.write_test_files(["<example></example>"])[0]
        self.assertIsInstance(xml_tools.parser.base_parser.BaseParser(
            filename), xml_tools.parser.base_parser.BaseParser)

    def test_context_manager(self):
        filename = self.write_test_files(["<example></example>"])[0]
        with xml_tools.parser.base_parser.BaseParser(filename) as parser:
            self.assertIsInstance(
                parser, xml_tools.parser.base_parser.BaseParser)

    def test_load_xml_file(self):
        xml_string = \
            "<LEVEL1  >\n" +\
            "<xi:include href=\"test_base_parser_1.xml\"/>\n" +\
            "<lEvEl1A test=\"Hello, world\" Version=\"2.0\"/>\n" +\
            "  <level2  ATTRIB=\"ImPoRtAnT TEXT\" Version = \"2A\">\n" +\
            "    <leveL2a></leveL2a>" +\
            "    <Level3>\n" +\
            "      <level4>\n" +\
            "        <level5 href=\"WWW.example.com\" aRef=\"test\">\n" +\
            "          <level6>\n" +\
            "          </level6>\n" +\
            "        </level5>\n" +\
            "      </level4>\n" +\
            "    </Level3>\n" +\
            "  </level2>\n" +\
            "</LEVEL1  >\n"

        include_xml = \
            "<?xml version=\"1.0\"?>\n" +\
            "<example test123=\"this_is_a_test\"/>"

        expected = \
            "<level1>\n\n" +\
            "<example test123=\"this_is_a_test\"/>\n" +\
            "<level1a test=\"Hello, world\" version=\"2.0\"/>\n" +\
            "  <level2  attrib=\"ImPoRtAnT TEXT\" version=\"2A\">\n" +\
            "    <level2a></level2a>" +\
            "    <level3>\n" +\
            "      <level4>\n" +\
            "        <level5 href=\"WWW.example.com\" aref=\"test\">\n" +\
            "          <level6>\n" +\
            "          </level6>\n" +\
            "        </level5>\n" +\
            "      </level4>\n" +\
            "    </level3>\n" +\
            "  </level2>\n" +\
            "</level1>\n"

        filename, _ = self.write_test_files([xml_string, include_xml])
        parser = xml_tools.parser.base_parser.BaseParser(filename)
        expected_xml_element = ET.fromstring(expected)

        self.assertTrue(
            self.xml_compare(parser._xml_root, expected_xml_element))

    def test_load_xml_file_retain_tag_case(self):
        xml_string = \
            "<LEVEL1  >\n" +\
            "<lEvEl1A test=\"Hello, world\" Version=\"2.0\"/>\n" +\
            "  <level2  ATTRIB=\"ImPoRtAnT TEXT\" Version = \"2A\">\n" +\
            "    <leveL2a></leveL2a>" +\
            "    <Level3>\n" +\
            "      <level4>\n" +\
            "        <level5 href=\"WWW.example.com\" aRef=\"test\">\n" +\
            "          <level6>\n" +\
            "          </level6>\n" +\
            "        </level5>\n" +\
            "      </level4>\n" +\
            "    </Level3>\n" +\
            "  </level2>\n" +\
            "</LEVEL1  >\n"

        filename = self.write_test_files([xml_string])[0]
        parser = xml_tools.parser.base_parser.BaseParser(
            filename, force_lowercase=False)
        expected_xml_element = ET.fromstring(xml_string)

        self.assertTrue(
            self.xml_compare(parser._xml_root, expected_xml_element))

    def test_get_root_tag(self):
        root_tags = ["Example", "test", "hello_world", "helloWorld"]

        for tag in root_tags:
            filename = self.write_test_files(
                ["<" + tag + "></" + tag + ">"])[0]

            self.assertEqual(xml_tools.parser.base_parser.BaseParser(
                filename, force_lowercase=False)._get_root_tag(), tag)

    def test_get_elements_tag_list(self):
        filename = self.write_test_files(["<example></example>"])[0]
        parser = xml_tools.parser.base_parser.BaseParser(filename)
        xml_string = \
            "<level1>\n" +\
            "<level1a test=\"Hello, world\"/>\n" +\
            "  <level2>\n" +\
            "    <level2a></level2a>" +\
            "    <Level3>\n" +\
            "      <level4>\n" +\
            "        <level5>\n" +\
            "          <level6>\n" +\
            "          </level6>\n" +\
            "        </level5>\n" +\
            "      </level4>\n" +\
            "    </Level3>\n" +\
            "  </level2>\n" +\
            "</level1>\n"
        expected = ["level1", "level1a", "level2", "level2a",
                    "Level3", "level4", "level5", "level6"]
        xml_element = ET.fromstring(xml_string)
        self.assertEqual(parser._get_elements_tag_list(xml_element), expected)

    def test_get_attribute_tag_list(self):
        filename = self.write_test_files(["<example></example>"])[0]
        parser = xml_tools.parser.base_parser.BaseParser(filename)
        xml_string = \
            "<level1>\n" +\
            "<level1a test=\"Hello, world\" Version=\"2.0\"/>\n" +\
            "  <level2>\n" +\
            "    <level2a></level2a>" +\
            "    <Level3>\n" +\
            "      <level4>\n" +\
            "        <level5 href=\"www.example.com\" aref=\"test\">\n" +\
            "          <level6>\n" +\
            "          </level6>\n" +\
            "        </level5>\n" +\
            "      </level4>\n" +\
            "    </Level3>\n" +\
            "  </level2>\n" +\
            "</level1>\n"
        expected = ["test", "Version", "href", "aref"]
        xml_element = ET.fromstring(xml_string)
        self.assertEqual(parser._get_attribute_tag_list(xml_element), expected)

    def test_remove_lower_case(self):
        filename = self.write_test_files(["<example></example>"])[0]
        parser = xml_tools.parser.base_parser.BaseParser(filename)
        list_ = ["test", "tEst", "test_test", "test_TEST1", "test2"]
        expected = ["tEst", "test_TEST1"]
        self.assertEqual(parser._remove_lower_case(list_), expected)

    def test_get_lower_case_xml(self):
        filename = self.write_test_files(["<example></example>"])[0]
        parser = xml_tools.parser.base_parser.BaseParser(filename)
        xml_string = \
            "<LEVEL1  >\n" +\
            "<lEvEl1A test=\"Hello, world\" Version=\"2.0\"/>\n" +\
            "  <level2  ATTRIB=\"ImPoRtAnT TEXT\" Version = \"2A\">\n" +\
            "    <leveL2a></leveL2a>" +\
            "    <Level3>\n" +\
            "      <level4>\n" +\
            "        <level5 href=\"WWW.example.com\" aRef=\"test\">\n" +\
            "          <level6>\n" +\
            "          </level6>\n" +\
            "        </level5>\n" +\
            "      </level4>\n" +\
            "    </Level3>\n" +\
            "  </level2>\n" +\
            "</LEVEL1  >\n"
        expected = \
            "<level1>\n" +\
            "<level1a test=\"Hello, world\" version=\"2.0\"/>\n" +\
            "  <level2  attrib=\"ImPoRtAnT TEXT\" version=\"2A\">\n" +\
            "    <level2a></level2a>" +\
            "    <level3>\n" +\
            "      <level4>\n" +\
            "        <level5 href=\"WWW.example.com\" aref=\"test\">\n" +\
            "          <level6>\n" +\
            "          </level6>\n" +\
            "        </level5>\n" +\
            "      </level4>\n" +\
            "    </level3>\n" +\
            "  </level2>\n" +\
            "</level1>\n"
        self.assertEqual(parser._get_lower_case_xml(xml_string), expected)

    def test_is_true(self):
        filename = self.write_test_files(["<example></example>"])[0]
        parser = xml_tools.parser.base_parser.BaseParser(filename)

        bool_attributes = ["testattrib=\"true\"",
                           "testattrib=\"false\"",
                           "testattrib=\"True\"",
                           "testattrib=\"False\"",
                           "testattrib=\"1\"",
                           "testattrib=\"0\""]

        expected_values = [True, False, True, False, True, False]
        for expected, bool_attribute in zip(expected_values, bool_attributes):
            xml_string = \
                "<level1 " + bool_attribute + ">\n" +\
                "  <level2 test2=\"false\">\n" +\
                "  </level2>\n" +\
                "</level1>\n"
            xml_element = ET.fromstring(xml_string)
            self.assertEqual(
                parser._is_true(xml_element, "testattrib"), expected)

    def test_is_true_exception(self):
        filename = self.write_test_files(["<example></example>"])[0]
        parser = xml_tools.parser.base_parser.BaseParser(filename)

        xml_string = \
            "<level1>\n" +\
            "  <level2 test_val=\"false\">\n" +\
            "  </level2>\n" +\
            "</level1>\n"
        xml_element = ET.fromstring(xml_string)
        with self.assertRaises(ValueError):
            test = parser._is_true(xml_element, "testattrib", optional=False)
        # Attribute in child element should not be detected
        with self.assertRaises(ValueError):
            test = parser._is_true(xml_element, "test_val", optional=False)

    def test_is_true_default(self):
        filename = self.write_test_files(["<example></example>"])[0]
        parser = xml_tools.parser.base_parser.BaseParser(filename)

        test_values = [True, False, None]

        for test_value in test_values:
            xml_string = \
                "<level1>\n" +\
                "  <level2 test2=\"false\">\n" +\
                "  </level2>\n" +\
                "</level1>\n"
            xml_element = ET.fromstring(xml_string)
            self.assertEqual(
                parser._is_true(xml_element, "testattrib", default=test_value,
                                optional=True), test_value)

    def test_get_boolean_attributes(self):
        filename = self.write_test_files(["<example></example>"])[0]
        parser = xml_tools.parser.base_parser.BaseParser(filename)

        xml_attributes = ["testattribute1=\"true\" testattribute2=\"false\"",
                          "a1=\"false\" a2=\"true\" a4=\"True\""]
        results = [{"testattribute1": True, "testattribute2": False},
                   {"a1": False, "a2": True, "a3": None, "a4": True}]

        names = [["testattribute1", "testattribute2"],
                 ["a1", "a2", "a3", "a4"]]

        for name, result, attribute in zip(names, results, xml_attributes):
            xml_string = \
                "<level1 " + attribute + ">\n" +\
                "  <level2 test2=\"false\">\n" +\
                "  </level2>\n" +\
                "</level1>\n"
            xml_element = ET.fromstring(xml_string)
            self.assertEqual(
                parser._get_boolean_attributes(
                    xml_element, name, default=None, optional=True), result)

    def test_get_attribute(self):
        filename = self.write_test_files(["<example></example>"])[0]
        parser = xml_tools.parser.base_parser.BaseParser(filename)

        bool_attributes = ["test=\"test_string\"",
                           "test='testString'",
                           "test=\"6236.944\"",
                           "test=\"{5,6,7},{'test','a','b'}\"",
                           "test=\"67 &amp; nVal \""]

        expected_values = ["test_string", "testString", "6236.944",
                           "{5,6,7},{'test','a','b'}", "67 & nVal "]
        for expected, bool_attribute in zip(expected_values, bool_attributes):
            xml_string = \
                "<level1 " + bool_attribute + ">\n" +\
                "  <level2 test2=\"false\">\n" +\
                "  </level2>\n" +\
                "</level1>\n"
            xml_element = ET.fromstring(xml_string)
            self.assertEqual(
                parser._get_attribute(xml_element, "test"), expected)

    def test_get_attribute_exception(self):
        filename = self.write_test_files(["<example></example>"])[0]
        parser = xml_tools.parser.base_parser.BaseParser(filename)

        xml_string = \
            "<level1>\n" +\
            "  <level2 test_val=\"false\">\n" +\
            "  </level2>\n" +\
            "</level1>\n"
        xml_element = ET.fromstring(xml_string)
        with self.assertRaises(ValueError):
            test = parser._get_attribute(
                xml_element, "testattrib", optional=False)
        # Attribute in child element should not be detected
        with self.assertRaises(ValueError):
            test = parser._get_attribute(
                xml_element, "test_val", optional=False)

    def test_get_attribute_default(self):
        filename = self.write_test_files(["<example></example>"])[0]
        parser = xml_tools.parser.base_parser.BaseParser(filename)

        test_values = ["test1", "678", None]

        for test_value in test_values:
            xml_string = \
                "<level1>\n" +\
                "  <level2 test2=\"false\">\n" +\
                "  </level2>\n" +\
                "</level1>\n"
            xml_element = ET.fromstring(xml_string)
            self.assertEqual(
                parser._get_attribute(
                    xml_element, "testattrib",
                    default=test_value, optional=True),
                test_value)

    def test_get_list_attribute(self):
        filename = self.write_test_files(["<example></example>"])[0]
        parser = xml_tools.parser.base_parser.BaseParser(filename)

        bool_attributes = ["test=\"test_string\"",
                           "test='a,b,c,d,e'",
                           "test=\"  Test1  ,test2 ,Test3  , test4\"",
                           "test=\"4,5,6, 78.9, 80\""]

        expected_values = [["test_string"], ["a", "b", "c", "d", "e"],
                           ["Test1", "test2", "Test3", "test4"],
                           ["4", "5", "6", "78.9", "80"]]
        for expected, bool_attribute in zip(expected_values, bool_attributes):
            xml_string = \
                "<level1 " + bool_attribute + ">\n" +\
                "  <level2 test2=\"false\">\n" +\
                "  </level2>\n" +\
                "</level1>\n"
            xml_element = ET.fromstring(xml_string)
            self.assertEqual(
                parser._get_list_attribute(xml_element, "test"), expected)

    def test_get_list_attribute_exception(self):
        filename = self.write_test_files(["<example></example>"])[0]
        parser = xml_tools.parser.base_parser.BaseParser(filename)

        xml_string = \
            "<level1>\n" +\
            "  <level2 test_val=\"false\">\n" +\
            "  </level2>\n" +\
            "</level1>\n"
        xml_element = ET.fromstring(xml_string)
        with self.assertRaises(ValueError):
            test = parser._get_list_attribute(
                xml_element, "testattrib", optional=False)
        # Attribute in child element should not be detected
        with self.assertRaises(ValueError):
            test = parser._get_list_attribute(
                xml_element, "test_val", optional=False)

    def test_get_list_attribute_default(self):
        filename = self.write_test_files(["<example></example>"])[0]
        parser = xml_tools.parser.base_parser.BaseParser(filename)

        test_values = [["0"], ["1", "1"], [None], None]

        for test_value in test_values:
            xml_string = \
                "<level1>\n" +\
                "  <level2 test2=\"false\">\n" +\
                "  </level2>\n" +\
                "</level1>\n"
            xml_element = ET.fromstring(xml_string)
            self.assertEqual(
                parser._get_list_attribute(
                    xml_element, "testattrib",
                    default=test_value, optional=True),
                test_value)

    def test_process_xml_includes(self):
        include_variants = ["<xi:include href=\"test_base_parser_1.xml\"/>",
                            "<xi:include href='test_base_parser_1.xml'/>",
                            "<xi:include href = \"test_base_parser_1.xml\" />",
                            "<xi:include   href= \"test_base_parser_1.xml\"/>",
                            "<xi:include href ='test_base_parser_1.xml'  />"]
        file_to_include = \
            "<example_child name=\"child1\" value=\"Hello, World!\"/>"
        expected = \
            "<example>\n" +\
            "  <example_child name=\"child1\" value=\"Hello, World!\"/>\n" +\
            "</example>\n"

        for variant in include_variants:
            main_xml = \
                "<example>\n" +\
                "  " + variant + "\n" +\
                "</example>\n"

            main_xml_filename, _ = self.write_test_files(
                [main_xml, file_to_include])
            parser = xml_tools.parser.base_parser.BaseParser(
                main_xml_filename, force_lowercase=False)
            self.assertEqual(parser._xml_string, expected)

    def test_process_xml_includes_with_xml_version(self):
        version_variants = ["<?xml version=\"1.0\"?>",
                            "<?xml version='1.0'?>",
                            "<?xml version = \"1.0\"?>",
                            "<?xml  version=\"1.0\" ?>",
                            "<?xml version=\"1.0\" encoding=\"character\"?>"]

        main_xml = \
            "<example>\n" +\
            "  <xi:include href=\"test_base_parser_1.xml\"/>\n" +\
            "</example>\n"

        expected = \
            "<example>\n" +\
            "  \n" + \
            "<example_child name=\"child1\" value=\"Hello, World!\"/>\n" +\
            "</example>\n"

        for variant in version_variants:
            file_to_include = \
                variant + "\n" +\
                "<example_child name=\"child1\" value=\"Hello, World!\"/>"

            main_xml_filename, _ = self.write_test_files(
                [main_xml, file_to_include])
            parser = xml_tools.parser.base_parser.BaseParser(
                main_xml_filename, force_lowercase=False)
            self.assertEqual(parser._xml_string, expected)

    def test_get_xml_includes(self):
        filename = self.write_test_files(["<example></example>"])[0]

        include_variants = ["<xi:include href=\"file1.xml\"/>",
                            "<xi:include href='file2.xml'/>",
                            "<xi:include href = \"file3.xml\" />",
                            "<xi:include   href= \"file4\"/>",
                            "<xi:include href ='file5'  />"]

        test_xml_string = \
            f"<example>\n" +\
            f"  {include_variants[0]}\n" +\
            f"  <ex1>{include_variants[1]}</ex1>\n" +\
            f"  <ex2 attr=\"xi:include\"/>\n" +\
            f"  {include_variants[2]}{include_variants[3]}\n" +\
            f"{include_variants[4]}<example>"
        parser = xml_tools.parser.base_parser.BaseParser(filename)
        result = parser._get_xml_includes(test_xml_string)
        self.assertEqual(result, include_variants)

    def test_get_xml_include_filename(self):
        filename = self.write_test_files(["<example></example>"])[0]

        include_variants = ["<xi:include href=\"test_base_parser_1.xml\"/>",
                            "<xi:include href='test_base_parser_1.xml'/>",
                            "<xi:include href = \"test_base_parser_1.xml\" />",
                            "<xi:include   href= \"test_base_parser_1.xml\"/>",
                            "<xi:include href ='test_base_parser_1.xml'  />"]

        for variant in include_variants:
            parser = xml_tools.parser.base_parser.BaseParser(filename)
            result = parser._get_xml_include_filename(variant)
            self.assertEqual(result, "test_base_parser_1.xml")
