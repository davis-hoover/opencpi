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
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


import os
# below line is for testing only
import xml.etree.ElementTree as ET
from _opencpi.assets.abstract2 import *
from _opencpi.assets.abstract2 import AssetBase


class OperationArgumentMember(AttributeBase):

    def __init__(self, elem):
        AttributeBase.__init__(self, elem)

    def get_root_tags(self):
        # TODO replace get_root_tags() with self.root_tags
        return ['Member']

    def get_attr_infos(self):
        ret = []
        for key in ['Name', 'Type']:
            ret.append(AttributeInfo(key))
        return ret


class OperationArgument(AttributeBase):
    """ Component Development Guide section 5.1.3.2 """

    def __init__(self, elem):
        self.array_length = -1
        self.sequence_length = -1
        self.members = []
        AttributeBase.__init__(self, elem)
        self.parse(elem)

    def get_root_tags(self):
        # TODO replace get_root_tags() with self.root_tags
        return ['Argument']

    def get_attr_infos(self):
        ret = []
        for key in ['Name', 'Type']:
            ret.append(AttributeInfo(key))
        for key in ['ArrayLength', 'SequenceLength']:
            ret.append(AttributeInfo(key, is_list=True))
        return ret

    def parse(self, elem):
        AttributeBase.parse(self, elem)
        for child in elem.iter():
            try:
                member = OperationArgumentMember(child)
                self.members.append(member)
            except InvalidAttributeError:
                pass


class Operation(AttributeBase):
    """ Component Development Guide section 5.1.3 """

    def __init__(self, elem):
        self.name = ''
        self.arguments = []
        AttributeBase.__init__(self, elem)
        self.parse(elem)

    def get_root_tags(self):
        # TODO replace get_root_tags() with self.root_tags
        return ['Operation']

    def get_attr_infos(self):
        ret = []
        ret.append(AttributeInfo('Name'))
        return ret

    def parse(self, elem):
        AttributeBase.parse(self, elem)
        for child in elem.iter():
            try:
                argument = OperationArgument(child)
                self.arguments.append(argument)
            except InvalidAttributeError:
                pass


class Protocol(AssetBase):
    """ Reference Component Development Guide section 5. A Protocol is
        represented by a xml file (OPS) and knows nothing about the project it
        is in or its package ID. """

    def __init__(self, xml_abs_path):
        AssetBase.__init__(self, xml_abs_path)
        self.operations = []
        self.parse()

    def get_root_tags(self):
        # TODO replace get_root_tags() with self.root_tags
        return ['Protocol']

    def parse(self):
        AttributeBase.parse(self)
        for elem in self.get_parsed().iter():
            for key, value in elem.attrib.items():
                if key.lower() == 'href':
                    href_abs_path = self.abs_path.rsplit('/', 1)[0] + '/'
                    href_abs_path += value
                    href_protocol = Protocol(href_abs_path)
                    self.operations.extend(href_protocol.operations)
            try:
                operation = Operation(elem)
                self.operations.append(operation)
            except InvalidAttributeError:
                pass


class Component(AssetBase):
    """ Reference Component Development Guide section 6. A Component is
        represented by a xml file (OCS) and knows nothing about the project it
        is in or its package ID. """

    def __init__(self, xml_abs_path, cli_dict=None):
        """ xml_abs_path is None for ComponentSpec embedded in OWD """
        self.root_tags = ['ComponentSpec']
        AssetBase.__init__(self, xml_abs_path)
        Logger().debug('parsing ' + self.get_xml_abs_path())
        self.parse(cli_dict)

    def get_attr_infos(self):
        ret = []
        ret.append(AttributeInfo('Name'))
        return ret

    def parse(self, cli_dict=None):
        AssetBase.parse(self, cli_dict)
        if self.attrs['Name'] != '':
            self.name = self.attrs['Name']
        #    for elem in AttributeBase.get_parsed(self.abs_path).iter():
        #        if elem.tag.lower() == self.get_root().lower():
        #            pass
        #        elif elem.tag.lower() == 'property':
        #            pass
        #        elif elem.tag.lower() == 'properties':
        #            pass
        #        elif elem.tag.lower() == 'description':
        #            pass
        #        elif elem.tag.lower() == 'member':
        #            pass
        #        elif elem.tag.lower() == 'port':
        #            pass
        #        elif elem.tag.lower() == 'protocol':
        #            pass
        #        elif elem.tag.lower() == 'operation':
        #            pass
        #        elif elem.tag.lower() == 'argument':
        #            pass
        #        else:
        #            # start pre-2.0 opencpi
        #            if elem.tag.lower() == 'datainterfacespec':
        #                pass
        #            elif elem.tag.lower() == 'protocolsummary':
        #                pass
        #            # end pre-2.0 opencpi
        #            else:
        #                tag = elem.tag
        #                self.throw_invalid_element_error(self.abs_path, tag)

    def get_type(self):
        return 'component'


# TODO iherit from, and consolidate functionality from, AttributeBase
class Property(AttributeBase):
    """ CDG Development Guide section 6.3 """

    def __init__(self, elem):
        AttributeBase.__init__(self)

    def get_root_tags(self):
        # TODO replace get_root_tags() with self.root_tags
        return ['Property']

    def get_attr_infos(self):
        ret = []
        ret.append(AttributeInfo('Name'))  # CDG section 6.3.1
        ret.append(AttributeInfo('Value'))  # CDG section 6.4.11
        return ret


def test_Property(ret):
    fs = TemporaryFilesystem()
    for test in range(6):
        passed = True
        try:
            xml_abs_path = fs.abs_path + '/' + 'foo.xml'
            os.system('mkdir -p ' + fs.abs_path)
            ff = open(xml_abs_path, 'w')
            ff.write('<Foo>\n')
            ff.write('  <Property name=\'myprop\' value=\'abc\'/>\n')
            ff.write('</Foo>\n')
            ff.close()
            tree = ET.parse(xml_abs_path)
            for elem in tree.iter():
                if elem == 'Property':
                    uut = Property(elem)
                    if Environment().ocpi_log_level >= 10:
                        print(uut.__dict__.keys())
                        os.system('cat ' + xml_abs_path)
                    if test == 0:
                        passed = uut.attrs['Name'] == 'myprop'
                    if test == 1:
                        passed = uut.attrs['Value'] == 'abc'
                    break
        except InvalidAssetError:
            passed = False
        if test == 0:
            log_pass_fail('testing Property value', passed)
        if test == 1:
            log_pass_fail('testing Property name', passed)
        if passed is False:
            ret = False
    fs = TemporaryFilesystem()
    file_name = fs.abs_path + '/' + 'tmp.xml'
    prop_elems = 3
    prop_names = [("prop" + str(idx) + "_name") for idx in range(prop_elems)]
    prop_values = [("prop" + str(idx) + "_value") for idx in range(prop_elems)]
    prop_dict = {key: value for key, value in zip(prop_names, prop_values)}

    def create_xml(prop_dict):
        root = ET.Element("instance", elem1="elem1", elem2="elem2")
        for key, value in prop_dict.items():
            ET.SubElement(root, "property", name=key, value=value)
        # Create XML tree
        tree = ET.ElementTree(root)
        # Write the XML tree to a file with indentation
        tree.write(file_name, xml_declaration=True, method="xml")

    def test___init__(ret):
        passed = True
        names = []
        values = []
        tree = ET.parse(file_name)
        for elem in tree.iter():
            if elem == 'Property':
                try:
                    uut = Property(elem)
                    values.append(uut.attrs['Value'])
                    names.append(uut.attrs['Name'])
                except InvalidAttributeError:
                    pass
        for name in names:
            if name in prop_names:
                prop_names.remove(name)
            else:
                passed = False
        for value in values:
            if value in prop_values:
                prop_values.remove(value)
            else:
                passed = False
        if len(prop_values) != 0 or len(prop_names) != 0:
            passed = False
        log_pass_fail('testing Property __init__()', passed)
        if passed is False:
            ret = False
        return ret
    # TODO investigate test coverage of below 4 lines
    # create_xml(prop_dict)
    # passed = test___init__(ret)
    # if passed is False:
    #     ret = False
    return ret


def test_Component(ret):
    fs = TemporaryFilesystem()
    for test in [0, 1]:
        passed = True
        try:
            dir_abs_path = fs.abs_path + '/' + 'components/specs'
            os.system('mkdir -p ' + dir_abs_path)
            xml_abs_path = dir_abs_path + '/' + 'component.xml'
            ff = open(xml_abs_path, 'w')
            ff.write('<ComponentSpec/>\n')
            ff.close()
            uut = Component(xml_abs_path)
            if Environment().ocpi_log_level >= 10:
                print(uut.__dict__.keys())
                os.system('cat ' + xml_abs_path)
            if test == 0:
                passed = uut.abs_path == xml_abs_path
            if test == 1:
                passed = uut.name == 'component'
        except InvalidAssetError:
            passed = False
        if test == 0:
            log_pass_fail('testing Component abs_path', passed)
        if test == 1:
            log_pass_fail('testing Component name', passed)
        if passed is False:
            ret = False
    return ret
