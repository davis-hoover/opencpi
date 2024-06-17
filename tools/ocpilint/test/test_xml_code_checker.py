#!/usr/bin/env python3

# Test code in xml_code_checker.py
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


import os
import pathlib
import unittest
import unittest.mock

from ocpilint.ocpi_linter.xml_code_checker import XmlCodeChecker
from ocpilint.ocpi_linter.linter_settings import LinterSettings


component_spec_patch_string = (
    ".".join([XmlCodeChecker._component_spec.__module__,
              XmlCodeChecker._component_spec.__qualname__]))
worker_description_patch_string = (
    ".".join([XmlCodeChecker._worker_description.__module__,
              XmlCodeChecker._worker_description.__qualname__]))
build_file_patch_string = (
    ".".join([XmlCodeChecker._build_file.__module__,
              XmlCodeChecker._build_file.__qualname__]))


class TestXmlCodeChecker(unittest.TestCase):
    def setUp(self):
        self.test_file_path = pathlib.Path("test_file.xml")
        self.test_file_path.touch()
        self.test_settings = LinterSettings()

    def tearDown(self):
        if self.test_file_path.is_file():
            os.remove(self.test_file_path)

        # In case test file path is change during test
        if pathlib.Path("test_file.xml").is_file():
            os.remove("test_file.xml")

    expected_copyright = """<!-- This file is protected by Copyright. Please refer to the COPYRIGHT file
     distributed with this source distribution.

     This file is part of OpenCPI <http://www.opencpi.org>

     OpenCPI is free software: you can redistribute it and/or modify it under
     the terms of the GNU Lesser General Public License as published by the Free
     Software Foundation, either version 3 of the License, or (at your option)
     any later version.

     OpenCPI is distributed in the hope that it will be useful, but WITHOUT ANY
     WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
     FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for
     more details.

     You should have received a copy of the GNU Lesser General Public License
     along with this program. If not, see <http://www.gnu.org/licenses/>. -->
"""

    long_code_sample = """<?xml version="1.0"?>
<xml>
  <test description="Tests that long attribute values are wrapped as expected"
    mylongattribute="test1 test2 test3 test4 test5 test6 test7 test8 test9 test10 test11 test12 test13 test14 test15 test16 test17
      test18 test19 test20 test21 test22 test23 test24"/>
  <property name="bitmask"
    generate="generate_pattern.py --pattern='0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,1,1,1,
      1,1,1,1,1,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,1,1,
      1,1,1,1,1,1,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1'"/>
  <test att1="value" attr2="value2" attr3="'&quot; '" attr4="'&quot; '"
    attr5="1,1,1,1,1,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,
      0,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1" attr6="value #6"/>
</xml>
"""

    def test_xml_empty(self):
        code_sample = ""
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = XmlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        with unittest.mock.patch(component_spec_patch_string,
                                 return_value=True):
            results = code_checker.lint()

        # Check an empty file fails lint without raising an exception
        self.assertGreater(len(results), 0)

    # Functionality of linter test 000 is not tested here since this uses
    # an external code formatter and it is assumed this is tested separately.
    # Only reporting of errors is tested.

    def test_xml_000_pass(self):
        code_sample = self.long_code_sample
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = XmlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_xml_000()

        self.assertEqual([], issues)

    def test_xml_000_fail(self):
        # Get code in one extra-long line.
        code_sample = self.long_code_sample.replace("\n", "")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = XmlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_xml_000()

        print(issues)
        print(code_checker._code)
        self.assertGreater(len(issues), 0)
        self.assertEqual(issues[0]["line"], 1)
        self.assertEqual(issues[0]["message"],
                         "File was reformatted by xmllint.")

    def test_xml_001_pass(self):
        code_sample = (
            "<?xmlversion=1.0?>\n" +
            self.expected_copyright +
            "This would be the start of the main file.")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = XmlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_xml_001()

        self.assertEqual([], issues)

    def test_xml_001_fail_no_header(self):
        code_sample = "A single line of text"
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = XmlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_xml_001()

        self.assertEqual(1, len(issues))
        self.assertEqual(None, issues[0]["line"])

    def test_xml_001_fail_license_notice_typo(self):
        code_sample = (
            "<?xmlversion=1.0?>\n" +
            self.expected_copyright.replace("published by the Free",
                                            "published by the Frea") +
            "This would be the start of the main file.")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = XmlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_xml_001()

        self.assertEqual(1, len(issues))
        self.assertEqual(8, issues[0]["line"])

    def test_xml_002_pass(self):
        code_sample = ("<!-- 'Single quotes' are fine in comments -->\n" +
                       "<element value=\"something\"/>\n" +
                       "<!-- Single quotes within multi-line\n" +
                       "     comments shouldn't be a problem -->")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = XmlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_xml_002()

        self.assertEqual([], issues)

    def test_xml_002_fail(self):
        code_sample = ("<!-- 'Single quotes' are fine in comments -->\n" +
                       "<element value='something'/>\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = XmlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_xml_002()

        self.assertEqual(1, len(issues))
        self.assertEqual(2, issues[0]["line"])

    def test_xml_002_fail2(self):
        code_sample = (
            "<!-- Single quotes between comments -->" +
            "<element value='something'/>" +
            "<!-- are not ok -->\n" +
            "<!-- Aren't OK, even if between \n" +
            "multiline --><element value='some other thing'/><!-- \n" +
            "comments -->\n" +
            "<element value=\"but they aren't disallowed in strings\">")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = XmlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_xml_002()

        self.assertEqual(2, len(issues))
        self.assertEqual(1, issues[0]["line"])  # value='something'
        self.assertEqual(3, issues[1]["line"])  # value='some other thing'

    def test_xml_003_pass(self):
        code_sample = ("<!-- A short comment. -->\n" +
                       "<element value=\"something\"/>\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = XmlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_xml_003()

        self.assertEqual([], issues)

    def test_xml_003_fail(self):
        code_sample = (
            "<!-- Some very long comment line. This line will exceed " +
            "the 132 character line limit by just a few characters, and " +
            "so should fail. -->\n" +
            "<element value='something'/>\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = XmlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_xml_003()

        self.assertEqual(1, len(issues))
        self.assertEqual(1, issues[0]["line"])

    def test_xml_004_pass(self):
        code_sample = """<line1>
<!-- Upper Case Allowed In Comments. --><line2>
<element_1 value="something"/>
<element_2 description="Upper Case Allowed In Description"/>
<!-- Upper Case Allowed
Multiline In Comments. -->
<element_3 description="Upper
Case Allowed In
Multiline Description"/>
<!-- Upper Case Allowed
Multiline In Comments. -->
<!--
<element_4 description="COMMENTED OUT UNCLOSED DESCRIPTION
-->
<element_5><description>Upper Case Allowed In Description</description>
</element_5>
<element_6>
    <description>
        Upper Case Allowed In Description
    </description>
</element_6>
"""
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = XmlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_xml_004()

        self.assertEqual([], issues)

    def test_xml_004_fail(self):
        code_sample = """<line1>
<!-- Upper Case Allowed In Comments. --><line2>
<element_1 value="Something"/>
<element_2 description="Upper Case Allowed In Description" value/>
<element_3 description="Upper Case Allowed
In Multiline Description" BUT="not in other attributes"/>
<element_4 description="Upper Case Allowed
In Multiline Description" but="Not In other VALUES"/>
"""
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = XmlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_xml_004()

        self.assertEqual(3, len(issues))
        self.assertEqual(3, issues[0]["line"])  # value="Something"
        self.assertEqual(6, issues[1]["line"])  # "BUT" attribute
        self.assertEqual(8, issues[2]["line"])  # "VALUES" in "but" attribute

    def test_xml_005_pass(self):
        code_sample = """
<componentspec>
  <port name="input" producer="false" protocol="short_v1_protocol"/>
  <port name="output" producer="true" protocol="short_v1_protocol"/>
  <property type="uchar" name="a_parameter" parameter="true"/>
  <property type="uchar" name="an_initial" initial="true"/>
  <property type="uchar" name="write_property" writable="true"/>
  <property type="uchar" name="read_property" volatile="true"/>
  <property type="uchar" name="rw_property" volatile="true" writable="true"/>
</componentspec>
"""
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = XmlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        with unittest.mock.patch(component_spec_patch_string,
                                 return_value=True):
            _, issues = code_checker.test_xml_005()

        self.assertEqual([], issues)

    def test_xml_005_fail_writable_not_set(self):
        code_sample = """
<componentspec>
  <port name="input" producer="false" protocol="short_v1_protocol"/>
  <port name="output" producer="true" protocol="short_v1_protocol"/>
  <property type="uchar" name="none_set" />
  <property type="uchar" name="a_parameter" parameter="false"/>
  <property type="uchar" name="an_initial" initial="false"/>
  <property type="uchar" name="write_property" writable="false"/>
  <property type="uchar" name="read_property" volatile="false"/>
  <property type="uchar" name="rw_property" volatile="false" writable="false"/>
</componentspec>
"""
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = XmlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        with unittest.mock.patch(component_spec_patch_string,
                                 return_value=True):
            _, issues = code_checker.test_xml_005()

        print(issues)
        self.assertEqual(6, len(issues))
        self.assertEqual(5, issues[0]["line"])
        self.assertEqual(6, issues[1]["line"])
        self.assertEqual(7, issues[2]["line"])
        self.assertEqual(8, issues[3]["line"])
        self.assertEqual(9, issues[4]["line"])
        self.assertEqual(10, issues[5]["line"])

    def test_xml_006_pass(self):
        code_sample = (
            "<componentspec>\n" +
            "  <port name=\"input\" producer=\"false\" " +
            "protocol=\"short_v1_protocol\"/>\n" +
            " <port name=\"output\" producer=\"true\" " +
            "protocol=\"short_v1_protocol\"/>\n" +
            " <property name=\"a_property\" type=\"uchar\" " +
            "readable=\"true\" writable=\"true\" default=\"0\" " +
            "description=\"Describes the property.\"/>\n" +
            "</componentspec>\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = XmlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        with unittest.mock.patch(component_spec_patch_string,
                                 return_value=True):
            _, issues = code_checker.test_xml_006()

        self.assertEqual([], issues)

    def test_xml_006_fail(self):
        code_sample = (
            "<componentspec>\n" +
            "  <port name=\"input\" protocol=\"short_v1_protocol\"/>\n" +
            " <port name=\"output\" producer=\"true\" " +
            "protocol=\"short_v1_protocol\"/>\n" +
            " <property name=\"a_property\" type=\"uchar\" " +
            "writable=\"true\" default=\"0\" " +
            "description=\"Describes the property.\"/>\n" +
            "</componentspec>\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = XmlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        with unittest.mock.patch(component_spec_patch_string,
                                 return_value=True):
            _, issues = code_checker.test_xml_006()

        self.assertEqual(1, len(issues))
        self.assertEqual(2, issues[0]["line"])

    def test_xml_007_pass(self):
        code_sample = (
            "<hdlworker language=\"vhdl\" spec=\"component-spec\">\n" +
            "  <streaminterface name=\"input\" datawidth=\"8\"/>\n" +
            "  <streaminterface name=\"output\" datawidth=\"8\"/>\n" +
            "  <property name=\"a_worker_property\" parameter=\"true\" " +
            "initial=\"true\" default=\"2\"/>\n" +
            "</hdlworker>\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = XmlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        with unittest.mock.patch(worker_description_patch_string,
                                 return_value=True):
            _, issues = code_checker.test_xml_007()

        self.assertEqual([], issues)

    def test_xml_007_fail(self):
        code_sample = (
            "<hdlworker language=\"vhdl\" spec=\"component-spec\">\n" +
            "  <streaminterface name=\"input\" datawidth=\"8\"/>\n" +
            "  <streaminterface name=\"output\" datawidth=\"8\"/>\n" +
            "  <property name=\"a_worker_property\" parameter=\"true\" " +
            "initial=\"true\"/>\n" +
            "</hdlworker>\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = XmlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        with unittest.mock.patch(worker_description_patch_string,
                                 return_value=True):
            _, issues = code_checker.test_xml_007()

        self.assertEqual(1, len(issues))
        self.assertEqual(4, issues[0]["line"])

    def test_xml_008_pass(self):
        code_sample = (
            "<xml>\n" +
            "test_xml_008 has been removed and is a no-op\n" +
            "It will always pass\n" +
            "</xml>\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)
        code_checker = XmlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        _, issues = code_checker.test_xml_008()

        self.assertEqual([], issues)

    @unittest.skip("test_xml_008 has been removed and is a no-op")
    def test_xml_008_fail(self):
        # test_xml_008 has been removed and is a no-op
        # It will always pass, so can't check it fails
        pass

    def test_xml_009_pass(self):
        code_sample = (
            "<build>\n" +
            "  <parameter name=\"a_parameter\" value=\"5\"/>\n" +
            "</build>\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = XmlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        with unittest.mock.patch(build_file_patch_string,
                                 return_value=True):
            _, issues = code_checker.test_xml_009()

        self.assertEqual([], issues)

    def test_xml_009_fail1(self):
        code_sample = (
            "<build>\n" +
            "</build>\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)
        code_checker = XmlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        self.test_file_path = pathlib.Path("test_file.xml")
        self.test_file_path.touch()

        with unittest.mock.patch(build_file_patch_string,
                                 return_value=True):
            _, issues = code_checker.test_xml_009()

        self.assertEqual(1, len(issues))

    def test_xml_009_fail2(self):
        code_checker = XmlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        with unittest.mock.patch(build_file_patch_string,
                                 return_value=True):
            _, issues = code_checker.test_xml_009()

        self.assertEqual(1, len(issues))

    def test_xml_010_pass(self):
        code_sample = (
            "<componentspec>\n" +
            "  <port name=\"input\" producer=\"false\" " +
            "protocol=\"short_v1_protocol\"/>\n" +
            " <port name=\"output\" producer=\"true\" " +
            "protocol=\"short_v1_protocol\"/>\n" +
            " <property name=\"a_property\" type=\"uchar\" " +
            "writable=\"true\" default=\"0\" " +
            "description=\"Describes the property.\"/>\n" +
            "</componentspec>\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = XmlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        with unittest.mock.patch(component_spec_patch_string,
                                 return_value=True):
            _, issues = code_checker.test_xml_010()

        self.assertEqual([], issues)

    def test_xml_010_fail(self):
        code_sample = (
            "<componentspec name=\"some_different_name\">\n" +
            "  <port name=\"input\" producer=\"false\" " +
            "protocol=\"short_v1_protocol\"/>\n" +
            " <port name=\"output\" producer=\"true\" " +
            "protocol=\"short_v1_protocol\"/>\n" +
            " <property name=\"a_property\" type=\"uchar\" " +
            "writable=\"true\" default=\"0\" " +
            "description=\"Describes the property.\"/>\n" +
            "</componentspec>\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = XmlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        with unittest.mock.patch(component_spec_patch_string,
                                 return_value=True):
            _, issues = code_checker.test_xml_010()

        self.assertEqual(1, len(issues))
        self.assertEqual(1, issues[0]["line"])

    def test_xml_011_pass(self):
        code_sample = (
            "<componentspec>\n" +
            "  <property name=\"a_property\" type=\"uchar\" " +
            "            writable=\"true\" default=\"0\" " +
            "            description=\"Describes the property.\"/>\n" +
            "  <port name=\"input\" producer=\"false\" " +
            "        protocol=\"short_v1_protocol\"/>\n" +
            "  <port name=\"output\" producer=\"true\" " +
            "        protocol=\"short_v1_protocol\"/>\n" +
            "</componentspec>\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = XmlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        with unittest.mock.patch(component_spec_patch_string,
                                 return_value=True):
            _, issues = code_checker.test_xml_011()

        self.assertEqual([], issues)

    def test_xml_011_fail_outputs_first(self):
        code_sample = (
            "<componentspec>\n" +
            "  <port name=\"output\" producer=\"true\" " +
            "        protocol=\"short_v1_protocol\"/>\n" +
            "  <property name=\"a_property\" type=\"uchar\" " +
            "            writable=\"true\" default=\"0\" " +
            "            description=\"Describes the property.\"/>\n" +
            "  <port name=\"input\" producer=\"false\" " +
            "        protocol=\"short_v1_protocol\"/>\n" +
            "</componentspec>\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = XmlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        with unittest.mock.patch(component_spec_patch_string,
                                 return_value=True):
            _, issues = code_checker.test_xml_011()

        # Two issues are expected here, as output first places it both
        # before the input port and before the property tag
        self.assertEqual(2, len(issues))
        self.assertEqual(3, issues[0]["line"])
        self.assertEqual(4, issues[1]["line"])

    def test_xml_011_fail_inputs_first(self):
        code_sample = (
            "<componentspec>\n" +
            "  <port name=\"input\" producer=\"false\" " +
            "        protocol=\"short_v1_protocol\"/>\n" +
            "  <property name=\"a_property\" type=\"uchar\" " +
            "            writable=\"true\" default=\"0\" " +
            "            description=\"Describes the property.\"/>\n" +
            " <port name=\"output\" producer=\"true\" " +
            "       protocol=\"short_v1_protocol\"/>\n" +
            "</componentspec>\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = XmlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        with unittest.mock.patch(component_spec_patch_string,
                                 return_value=True):
            _, issues = code_checker.test_xml_011()

        self.assertEqual(1, len(issues))
        self.assertEqual(3, issues[0]["line"])

    def test_xml_011_fail_input_last(self):
        code_sample = (
            "<componentspec>\n" +
            "  <property name=\"a_property\" type=\"uchar\" " +
            "            writable=\"true\" default=\"0\" " +
            "            description=\"Describes the property.\"/>\n" +
            "  <port name=\"output\" producer=\"true\" " +
            "        protocol=\"short_v1_protocol\"/>\n" +
            "  <port name=\"input\" producer=\"false\" " +
            "        protocol=\"short_v1_protocol\"/>\n" +
            "</componentspec>\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = XmlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        with unittest.mock.patch(component_spec_patch_string,
                                 return_value=True):
            _, issues = code_checker.test_xml_011()

        self.assertEqual(1, len(issues))
        self.assertEqual(4, issues[0]["line"])

    def test_xml_012_pass(self):
        code_sample = (
            "<componentspec>\n" +
            "  <port name=\"input\" producer=\"false\" " +
            "protocol=\"short_v1_protocol\"/>\n" +
            " <port name=\"output\" producer=\"true\" " +
            "protocol=\"short_v1_protocol\"/>\n" +
            " <property name=\"a_property\" type=\"uchar\" " +
            "writable=\"true\" default=\"0\" " +
            "description=\"Describes the property.\"/>\n" +
            "</componentspec>\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = XmlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        with unittest.mock.patch(component_spec_patch_string,
                                 return_value=True):
            _, issues = code_checker.test_xml_012()

        self.assertEqual([], issues)

    def test_xml_012_fail(self):
        code_sample = (
            "<componentspec>\n" +
            "  <port name=\"input\" producer=\"false\" " +
            "protocol=\"short_v1_protocol\"/>\n" +
            " <port name=\"output\" producer=\"true\" " +
            "protocol=\"short_v1_protocol\"/>\n" +
            " <property name=\"a_property\" type=\"uchar\" " +
            "writable=\"true\" " +
            "description=\"Describes the property.\"/>\n" +
            "</componentspec>\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = XmlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        with unittest.mock.patch(component_spec_patch_string,
                                 return_value=True):
            _, issues = code_checker.test_xml_012()

        self.assertEqual(1, len(issues))
        self.assertEqual(4, issues[0]["line"])

    def test_xml_013_pass(self):
        code_sample = (
            "<componentspec>\n" +
            "  <port name=\"input\" producer=\"false\" " +
            "protocol=\"short_v1_protocol\"/>\n" +
            " <port name=\"output\" producer=\"true\" " +
            "protocol=\"short_v1_protocol\"/>\n" +
            " <property name=\"a_property\" type=\"uchar\" " +
            "writable=\"true\" default=\"0\" " +
            "description=\"Describes the property.\"/>\n" +
            "</componentspec>\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = XmlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        with unittest.mock.patch(component_spec_patch_string,
                                 return_value=True):
            _, issues = code_checker.test_xml_013()

        self.assertEqual([], issues)

    def test_xml_013_fail(self):
        code_sample = (
            "<componentspec>\n" +
            "  <port name=\"input\" producer=\"false\" " +
            "protocol=\"short_v1_protocol\"/>\n" +
            " <port name=\"output\" producer=\"true\" " +
            "protocol=\"short_v1_protocol\"/>\n" +
            " <property name=\"a_property\" type=\"uchar\" " +
            "writable=\"true\" default=\"0\" />" +
            "</componentspec>\n")
        with open(self.test_file_path, "w+") as source_code_file:
            source_code_file.write(code_sample)

        code_checker = XmlCodeChecker(self.test_file_path, self.test_settings)
        code_checker._read_in_code()

        with unittest.mock.patch(component_spec_patch_string,
                                 return_value=True):
            _, issues = code_checker.test_xml_013()

        self.assertEqual(1, len(issues))
        self.assertEqual(4, issues[0]["line"])
