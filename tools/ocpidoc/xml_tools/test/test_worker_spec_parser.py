#!/usr/bin/env python3

# Test code in worker_spec_parser.py
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


class TestWorkerSpecParser(unittest.TestCase):
    def setUp(self):
        self.file_prefix = "test_worker_spec_parser_"

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
        filenames = self.write_test_files(
            ["<rccworker></rccworker>",
             "<hdlworker></hdlworker>",
             "<oclworker></oclworker>"])

        expected_authoring_model = ["rcc", "hdl", "ocl"]

        for file_, model in zip(filenames, expected_authoring_model):
            self.assertIsInstance(xml_tools.parser.worker_spec_parser.WorkerSpecParser(
                file_), xml_tools.parser.worker_spec_parser.WorkerSpecParser)
            self.assertEqual(xml_tools.parser.worker_spec_parser.WorkerSpecParser(
                file_).authoring_model, model)

    def test_constructor_wrong_xml(self):
        filename = self.write_test_files(["<property></property>"])[0]
        with self.assertRaises(ValueError):
            parser = xml_tools.parser.worker_spec_parser.WorkerSpecParser(
                filename)

    def test_context_manager(self):
        filename = self.write_test_files(["<rccworker></rccworker>"])[0]
        with xml_tools.parser.worker_spec_parser.WorkerSpecParser(filename) as parser:
            self.assertIsInstance(
                parser, xml_tools.parser.worker_spec_parser.WorkerSpecParser)

    def test_get_port(self):

        xml_strings = [
            "<port name='input' test0='test_value'/>",
            "<port name='output' test1='false'/>",
            "<port name='in' test2='32' test3='64'/>",
            "<port name='OUT' test4='1'/>\n<port name='output' test5='0'/>", ]

        file_strings = []
        for string_ in xml_strings:
            file_strings.append("<rccworker>\n" + string_ + "\n</rccworker>")

        files = self.write_test_files(file_strings)

        expected_values = [
            {"input": {"test0": "test_value", "type": "port"}},
            {"output": {"test1": "false", "type": "port"}},
            {"in": {"test2": "32", "test3": "64", "type": "port"}},
            {"OUT": {"test4": "1", "type": "port"},
             "output": {"test5": "0", "type": "port"}}]

        for expected, file_ in zip(expected_values, files):
            parser = xml_tools.parser.worker_spec_parser.WorkerSpecParser(
                file_)
            self.assertEqual(parser.get_ports(), expected)

    def test_get_port_other_port_element_names(self):

        xml_strings = [
            "<streaminterface name='input' test0='test_value'/>",
            "<streaminterface name='output' test1='false'/>",
            "<streaminterface name='in' test2='32' test3='64'/>",
            "<streaminterface name='OUT' test4='1'/>\n" +
            "<timeinterface name='output' test5='0'/>"]

        file_strings = []
        for string_ in xml_strings:
            file_strings.append("<hdlworker>\n" + string_ + "\n</hdlworker>")

        files = self.write_test_files(file_strings)

        expected_values = [
            {"input": {"test0": "test_value", "type": "streaminterface"}},
            {"output": {"test1": "false", "type": "streaminterface"}},
            {"in": {"test2": "32", "test3": "64", "type": "streaminterface"}},
            {"OUT": {"test4": "1", "type": "streaminterface"},
             "output": {"test5": "0", "type": "timeinterface"}}]

        for expected, file_ in zip(expected_values, files):
            parser = xml_tools.parser.worker_spec_parser.WorkerSpecParser(
                file_)
            self.assertEqual(
                parser.get_ports(
                    ["streaminterface", "timeinterface"]), expected)

    def test_get_dictionary(self):
        xml_string = "".join([
            "<hdlworker name='test_worker' >\n",
            "<Property name='test_prop' type='ushort' default='1' ",
            "description='This is a test property' arraydimensions='10,2'/>\n",
            "<property name='test_prop2' type='enum' default='test' ",
            " enums='test , test2' writable='true'/>\n",
            "<specproperty name='test_prop3' parameter='true' value='60'/> \n",
            "<specproperty name='test_prop4' writesync='true' readsync='true'",
            " default='value_string' />\n"
            "<streaminterface name='input' datawidth='32' />\n",
            "<streaminterface name='input2'  />\n",
            "<streaminterface name='output' t='1' t2='2'/>\n",
            "<timeinterface name='time' secondswidth='16'/>\n",
            "</hdlworker>"])

        filename = self.write_test_files([xml_string])[0]
        parser = xml_tools.parser.worker_spec_parser.WorkerSpecParser(filename)

        expected_value = {
            "name": "test_worker",
            "authoring_model": "hdl",
            "ports": {
                "input": {"type": "streaminterface", "datawidth": "32"},
                "input2": {"type": "streaminterface"},
                "output": {"type": "streaminterface", "t": "1", "t2": "2"},
                "time": {"type": "timeinterface", "secondswidth": "16"}},
            "properties": {
                "test_prop": {
                    "type": {"data_type": "ushort",
                             "arraydimensions": ["10", "2"]},
                    "access": {"initial": False, "parameter": False,
                               "readable": False, "readback":  False,
                               "readsync": False, "volatile":  False,
                               "writable": False,  "writesync": False,
                               "readerror": False, "writeerror": False,
                               "padding": False},
                    "description": "This is a test property",
                    "default": "1",
                    "value": None},
                "test_prop2": {
                    "type": {"data_type": "enum", "enums": ["test", "test2"]},
                    "access": {"initial": False, "parameter": False,
                               "readable": False, "readback":  False,
                               "readsync": False, "volatile":  False,
                               "writable": True,  "writesync": False,
                               "readerror": False, "writeerror": False,
                               "padding": False},
                    "description": None,
                    "default": "test",
                    "value": None}},
            "specproperties": {
                "test_prop3": {
                    "access": {"parameter": True, "readback": None,
                               "readsync": None, "writable": None,
                               "writesync": None, "readerror": None,
                               "writeerror": None},
                    "default": None,
                    "value": "60"},
                "test_prop4": {
                    "access": {"parameter": None, "readback": None,
                               "readsync": True, "writable": None,
                               "writesync": True, "readerror": None,
                               "writeerror": None},
                    "default": "value_string",
                    "value": None}}}

        self.assertEqual(parser.get_dictionary(), expected_value)

    def test_get_component_dictionary(self):
        owd_file, ocs_file = self.write_test_files(
            ["<rccworker></rccworker>",
             "<componentspec></componentspec>"])

        expected_ocs = {"inputs": {}, "outputs": {}, "properties": {}}

        parser = xml_tools.parser.worker_spec_parser.WorkerSpecParser(owd_file)
        ocs = parser.get_component_dictionary(ocs_file)

        self.assertEqual(ocs, expected_ocs)

    def test_get_component_dictionary_ocs_named_in_worker(self):
        owd_file, ocs_file = self.write_test_files(
            ["<rccworker spec='" + self.file_prefix + "1.xml'></rccworker>",
             "<componentspec></componentspec>"])

        expected_ocs = {"inputs": {}, "outputs": {}, "properties": {}}

        parser = xml_tools.parser.worker_spec_parser.WorkerSpecParser(owd_file)
        ocs = parser.get_component_dictionary()

        self.assertEqual(ocs, expected_ocs)

    def test_get_component_dictionary_ocs_not_found(self):
        owd_file, ocs_file = self.write_test_files(
            ["<rccworker spec='139483929382992.xml'></rccworker>",
             "<componentspec></componentspec>"])

        parser = xml_tools.parser.worker_spec_parser.WorkerSpecParser(owd_file)

        with self.assertRaises(ValueError):
            ocs = parser.get_component_dictionary()

    def test_get_component_dictionary_ocs_not_specified(self):
        owd_file, ocs_file = self.write_test_files(
            ["<rccworker></rccworker>",
             "<componentspec></componentspec>"])

        parser = xml_tools.parser.worker_spec_parser.WorkerSpecParser(owd_file)

        with self.assertRaises(ValueError):
            ocs = parser.get_component_dictionary()

    def test_get_combined_dictionary_properties(self):

        owd_string = "".join([
            "<hdlworker name='test_worker'>\n",
            "<property name='worker_prop' type='ushort' default='1' ",
            "description='This is a worker prop' arraydimensions='10,2'/>\n",
            "</hdlworker>"])
        ocs_string = "".join([
            "<componentspec>\n",
            "<property name='component_prop' type='ulong' default='1' ",
            "description='This is a component prop' writable='true' />\n",
            "</componentspec>"])

        owd_file, ocs_file = self.write_test_files([owd_string, ocs_string])

        expected_result = {
            "authoring_model": "hdl",
            "inputs": {},
            "name": "test_worker",
            "other_interfaces": {},
            "outputs": {},
            "properties": {
                "component_prop": {
                    "access": {"initial": False, "padding": False,
                               "parameter": False, "readable": False,
                               "readback": False, "readerror": False,
                               "readsync": False, "volatile": False,
                               "writable": True, "writeerror": False,
                               "writesync": False},
                    "default": "1",
                    "description": "This is a component prop",
                    "type": {"data_type": "ulong"},
                    "value": None,
                    "worker_property": False},
                "worker_prop": {
                    "access": {"initial": False, "padding": False,
                               "parameter": False, "readable": False,
                               "readback": False, "readerror": False,
                               "readsync": False, "volatile": False,
                               "writable": False, "writeerror": False,
                               "writesync": False},
                    "default": "1",
                    "description": "This is a worker prop",
                    "type": {"data_type": "ushort",
                             "arraydimensions": ["10", "2"]},
                    "value": None,
                    "worker_property": True}}}

        parser = xml_tools.parser.worker_spec_parser.WorkerSpecParser(owd_file)
        combined = parser.get_combined_dictionary(ocs_file)

        self.assertEqual(combined, expected_result)

    def test_get_combined_dictionary_specproperties_access(self):

        owd_string = "".join([
            "<hdlworker name='test_worker'>\n",
            "<specproperty name='component_prop' parameter='true' />\n",
            "</hdlworker>"])
        ocs_string = "".join([
            "<componentspec>\n",
            "<property name='component_prop' type='ulong' default='1' ",
            "initial='true' />\n",
            "</componentspec>"])

        owd_file, ocs_file = self.write_test_files([owd_string, ocs_string])

        expected_result = {
            "authoring_model": "hdl",
            "inputs": {},
            "name": "test_worker",
            "other_interfaces": {},
            "outputs": {},
            "properties": {
                "component_prop": {
                    "access": {"initial": True, "padding": False,
                               "parameter": True, "readable": False,
                               "readback": False, "readerror": False,
                               "readsync": False, "volatile": False,
                               "writable": False, "writeerror": False,
                               "writesync": False},
                    "default": "1",
                    "description": None,
                    "type": {"data_type": "ulong"},
                    "value": None,
                    "worker_property": False}}}

        parser = xml_tools.parser.worker_spec_parser.WorkerSpecParser(owd_file)
        combined = parser.get_combined_dictionary(ocs_file)

        self.assertEqual(combined, expected_result)

    def test_get_combined_dictionary_specproperties_value(self):

        owd_string = "".join([
            "<hdlworker name='test_worker'>\n",
            "<specproperty name='component_prop' value='2' />\n",
            "</hdlworker>"])
        ocs_string = "".join([
            "<componentspec>\n",
            "<property name='component_prop' type='ulong' default='1' />\n",
            "</componentspec>"])

        owd_file, ocs_file = self.write_test_files([owd_string, ocs_string])

        expected_result = {
            "authoring_model": "hdl",
            "inputs": {},
            "name": "test_worker",
            "other_interfaces": {},
            "outputs": {},
            "properties": {
                "component_prop": {
                    "access": {"initial": False, "padding": False,
                               "parameter": False, "readable": False,
                               "readback": False, "readerror": False,
                               "readsync": False, "volatile": False,
                               "writable": False, "writeerror": False,
                               "writesync": False},
                    "default": None,
                    "description": None,
                    "type": {"data_type": "ulong"},
                    "value": "2",
                    "worker_property": False}}}

        parser = xml_tools.parser.worker_spec_parser.WorkerSpecParser(owd_file)
        combined = parser.get_combined_dictionary(ocs_file)

        self.assertEqual(combined, expected_result)

    def test_get_combined_dictionary_specproperties_default(self):

        owd_string = "".join([
            "<hdlworker name='test_worker'>\n",
            "<specproperty name='component_prop' default='10' />\n",
            "</hdlworker>"])
        ocs_string = "".join([
            "<componentspec>\n",
            "<property name='component_prop' type='ulong' default='1' />\n",
            "</componentspec>"])

        owd_file, ocs_file = self.write_test_files([owd_string, ocs_string])

        expected_result = {
            "authoring_model": "hdl",
            "inputs": {},
            "name": "test_worker",
            "other_interfaces": {},
            "outputs": {},
            "properties": {
                "component_prop": {
                    "access": {"initial": False, "padding": False,
                               "parameter": False, "readable": False,
                               "readback": False, "readerror": False,
                               "readsync": False, "volatile": False,
                               "writable": False, "writeerror": False,
                               "writesync": False},
                    "default": "10",
                    "description": None,
                    "type": {"data_type": "ulong"},
                    "value": None,
                    "worker_property": False}}}

        parser = xml_tools.parser.worker_spec_parser.WorkerSpecParser(owd_file)
        combined = parser.get_combined_dictionary(ocs_file)

        self.assertEqual(combined, expected_result)

    def test_get_combined_dictionary_specproperties_default_incorrect(self):
        # Test when a specproperty tries to override a value attribute with a
        # default attribute.
        owd_string = "".join([
            "<hdlworker name='test_worker'>\n",
            "<specproperty name='component_prop' default='10' />\n",
            "</hdlworker>"])
        ocs_string = "".join([
            "<componentspec>\n",
            "<property name='component_prop' type='ulong' value='1' />\n",
            "</componentspec>"])

        owd_file, ocs_file = self.write_test_files([owd_string, ocs_string])

        expected_result = {
            "authoring_model": "hdl",
            "inputs": {},
            "name": "test_worker",
            "other_interfaces": {},
            "outputs": {},
            "properties": {
                "component_prop": {
                    "access": {"initial": False, "padding": False,
                               "parameter": False, "readable": False,
                               "readback": False, "readerror": False,
                               "readsync": False, "volatile": False,
                               "writable": False, "writeerror": False,
                               "writesync": False},
                    "default": None,
                    "description": None,
                    "type": {"data_type": "ulong"},
                    "value": "1",
                    "worker_property": False}}}

        parser = xml_tools.parser.worker_spec_parser.WorkerSpecParser(owd_file)
        combined = parser.get_combined_dictionary(ocs_file)

        self.assertEqual(combined, expected_result)

    def test_get_combined_dictionary_ports(self):

        owd_string = "".join([
            "<hdlworker name='test_worker'>\n",
            "<streaminterface name='input' datawidth='16' />\n",
            "<streaminterface name='output' numberofopcodes='8' />\n",
            "<timeinterface name='time_in' secondswidth='32' ",
            "fractionwidth='16' />\n",
            "</hdlworker>"])
        ocs_string = "".join([
            "<componentspec>\n",
            "<port name='input' producer='false' protocol='stream-prot' />\n",
            "<port name='output' producer='true' optional='true' />\n",
            "</componentspec>"])

        owd_file, ocs_file = self.write_test_files([owd_string, ocs_string])

        expected_result = {
            "authoring_model": "hdl",
            "inputs": {"input": {"optional": False,
                                 "datawidth": "16",
                                 "protocol": "stream-prot",
                                 "type": "streaminterface"}},
            "name": "test_worker",
            "other_interfaces": {"time_in": {"secondswidth": "32",
                                             "fractionwidth": "16",
                                             "type": "timeinterface"}},
            "outputs": {"output": {"optional": True,
                                   "numberofopcodes": "8",
                                   "protocol": None,
                                   "type": "streaminterface"}},
            "properties": {}}

        parser = xml_tools.parser.worker_spec_parser.WorkerSpecParser(owd_file)
        combined = parser.get_combined_dictionary(ocs_file)

        self.assertEqual(combined, expected_result)

    def test_get_combined_dictionary_ports_ocs(self):

        owd_string = "".join([
            "<hdlworker name='test_worker'>\n",
            "<streaminterface name='in' datawidth='16' />\n",
            "</hdlworker>"])
        ocs_string = "".join([
            "<componentspec>\n",
            "<port name='in' producer='false' numberofopcodes='8' />\n",
            "</componentspec>"])

        owd_file, ocs_file = self.write_test_files([owd_string, ocs_string])

        expected_result = {
            "authoring_model": "hdl",
            "inputs": {"in": {"optional": False,
                              "datawidth": "16",
                              "protocol": None,
                              "type": "streaminterface",
                              "numberofopcodes": "8"}},
            "name": "test_worker",
            "other_interfaces": {},
            "outputs": {},
            "properties": {}}

        parser = xml_tools.parser.worker_spec_parser.WorkerSpecParser(owd_file)
        combined = parser.get_combined_dictionary(ocs_file)

        self.assertEqual(combined, expected_result)
