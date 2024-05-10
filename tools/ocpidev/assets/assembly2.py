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
from .abstract2 import *
from _opencpi.assets.abstract2 import AssetBase
from .worker2 import Worker


class HdlAssemblyInstance(AttributeBase):

    def __init__(self, elem):
        self.name = ''
        self.worker = ''
        AttributeBase.__init__(self, elem)
        self.parse(elem)

    def get_root_tags(self):
        return ['Instance']

    def parse(self, elem):
        self.name = self.get_attr('Name', elem)
        self.worker = self.get_attr('Worker', elem)


class HdlAssembly(AssetBase):
    """ Reference HDL Development Guide section 6. A HdlAssembly is
        represented by a directory and knows nothing about the project it
        is in or its package ID. """

    def __init__(self, dir_abs_path):
        AssetBase.__init__(self, dir_abs_path)
        if not os.path.isfile(self.get_xml_abs_path()):
            self.raise_abs_path_does_not_exist()
        self.instances = []
        self.containers = []
        self.parse()

    def get_root_tags(self):
        return ['HdlAssembly']

    def parse(self):
        paths = []
        # start pre-2.0 opencpi
        paths += [self.abs_path + '/Makefile']
        # intentionally put xml path last so that its attributes take precedence
        # end pre-2.0 opencpi
        paths.append(self.get_xml_abs_path())
        paths = self.get_list_of_existing_abs_paths_to_parse(paths)
        containers = self.get_attr_list('Containers', None, paths)
        if len(containers) > 0:
            for cname in containers:
                # start pre-2.0 opencpi
                # interesting edge case for
                # assets/hdl/assemblies/empty/Makefile which has Makefiel
                # variable Containers with a value that is not just a
                # string (which is typical) but an .xml extension (atypical)
                # cnt_hsmc_loopback_card_hsmc_alst4_a_hsmc_alst4_b.xml
                cname = cname.split('.xml')[0]
                # end pre-2.0 opencpi
                path = self.abs_path + '/' + cname + '.xml'
                self.containers.append(HdlContainer(path))
        for elem in self.get_parsed().iter():
            try:
                instance = HdlAssemblyInstance(elem)
                self.instances.append(instance)
            except InvalidAttributeError:
                pass

    def get_type(self):
        return 'hdl assembly'


class HdlContainerDevice():

    def __init__(self, card, slot):
        self.card = card
        self.slot = slot


class HdlContainer(AssetBase):
    """ HDL Development Guide section 6.4 """

    def __init__(self, xml_abs_path):
        AssetBase.__init__(self, xml_abs_path)
        # start of HDL section 6.4.1
        self.platform = ''
        self.config = ''
        self.constraints = ''
        self.only_platforms = []
        self.exclude_platforms = []
        # end of HDL section 6.4.1
        self.devices = dict()
        self.parse()

    def get_root_tags(self):
        return ['HdlContainer']

    def parse(self):
        Logger().debug('parsing ' + self.get_xml_abs_path())
        self.platform = self.get_attr('Platform')
        self.config = self.get_attr('Config')
        self.constraints = self.get_attr('Constraints')
        self.only_platforms = self.get_attr_list('OnlyPlatforms')
        self.exclude_platforms = self.get_attr_list('ExcludePlatforms')
        # TODO consolidate below with AttributeBase/AssetBase methods
        for elem in self.get_parsed().iter():
            name = None
            card = None
            slot = None
            con = elem.tag.lower() == 'connection'
            dev = elem.tag.lower() == 'device'
            if con or dev:
                for attrib in elem.attrib:
                    name_con = con and (attrib.lower() == 'device')
                    name_dev = dev and (attrib.lower() == 'name')
                    name_dev = attrib.lower() == 'name'
                    if name_con or name_dev:
                        name = elem.attrib[attrib]
                    if attrib.lower() == 'card':
                        card = elem.attrib[attrib]
                    if attrib.lower() == 'slot':
                        slot = elem.attrib[attrib]
                if name is not None:
                    self.devices[name] = HdlContainerDevice(card, slot)


def create_test_ohad(
        instances, dir_abs_path, containers=[], filename='assembly.xml',
        tag='HdlAssembly', quote='\'', valid_xml=True):
    file_abs_path = dir_abs_path + '/' + filename
    os.system('mkdir -p ' + dir_abs_path)
    ff = open(file_abs_path, 'w')
    tmp = '<' + tag
    for idx, container in enumerate(containers):
        if idx == 0:
            tag += ' Containers=\''
        tag += container
        if idx == len(containers)-1:
            tag += quote
        else:
            tag += ' '
    ff.write(tmp + '>\n')
    for instance in instances:
        tmp = '  <Instance Worker=' + quote + instance[0] + quote
        if instance[1] is not None:
            tmp += ' Name=' + quote + instance[1] + quote
        tmp += '/>\n'
        ff.write(tmp)
    if valid_xml:
        ff.write('</' + tag + '>\n')
    ff.close()
    if Environment().ocpi_log_level >= 10:
        os.system('cat ' + file_abs_path)


def test_HdlAssembly___init___abs_path(ret):
    passed = True
    fs = TemporaryFilesystem()
    dir_abs_path = fs.abs_path + '/' + 'assembly'
    # try:
    #     create_test_ohad([('nothing', None)], dir_abs_path, valid_xml=False)
    #     hdl_assembly = HdlAssembly(dir_abs_path)
    #     passed = False
    # except:
    #     pass
    try:
        create_test_ohad([('nothing', None)], dir_abs_path)
        uut = HdlAssembly(dir_abs_path)
        for abs_path in [dir_abs_path, dir_abs_path + '/']:
            if uut.abs_path != dir_abs_path:
                passed = False
    except:
        passed = False
    log_pass_fail('testing HdlAssembly abs_path', passed)
    if passed is False:
        ret = False
    return ret


def test_HdlAssembly___init___name(ret):
    passed = True
    fs = TemporaryFilesystem()
    dir_abs_path = fs.abs_path + '/' + 'assembly'
    try:
        create_test_ohad([('nothing', None)], dir_abs_path)
        hdl_assembly = HdlAssembly(dir_abs_path)
        if hdl_assembly.name != 'assembly':
            passed = False
    except:
        passed = False
    log_pass_fail('testing HdlAssembly name', passed)
    if passed is False:
        ret = False
    return ret


def test_HdlAssembly___init__(ret):
    ret = test_HdlAssembly___init___abs_path(ret)
    ret = test_HdlAssembly___init___name(ret)
    return ret


def test_HdlAssembly_InvalidAssetError_exception(ret):
    passed = True
    fs = TemporaryFilesystem()
    dir_abs_path = fs.abs_path + '/' + 'assembly'
    try:
        create_test_ohad([('nothing', None)], dir_abs_path, tag='NotOHAD')
        uut = HdlAssembly(dir_abs_path)
        passed = False
    except InvalidAssetError:
        pass
    val = passed
    log_pass_fail(
          'testing HdlAssembly parse() for InvalidAssetError exception', val)
    if passed is False:
        ret = False
    return ret


def test_HdlAssembly_parse_instances(ret):
    passed = True
    fs = TemporaryFilesystem()
    dir_abs_path = fs.abs_path + '/' + 'assembly'
    for quote in ['\'', '\"']:
        try:
            create_test_ohad([], dir_abs_path, quote=quote)
            hdl_assembly = HdlAssembly(dir_abs_path)
            passed = False
        except:
            pass
        try:
            create_test_ohad([('nothing', None)], dir_abs_path, quote=quote)
            hdl_assembly = HdlAssembly(dir_abs_path)
            if len(hdl_assembly.instances) != 1:
                passed = False
            if hdl_assembly.instances['nothing'] != 'nothing':
                passed = False
            create_test_ohad([('nothing', 'myname')], dir_abs_path,
                             quote=quote)
            hdl_assembly = HdlAssembly(dir_abs_path)
            if len(hdl_assembly.instances) != 1:
                passed = False
            if hdl_assembly.instances['myname'] != 'nothing':
                passed = False
            create_test_ohad([('nothing', None), ('nothing', None)],
                             dir_abs_path, quote=quote)
            hdl_assembly = HdlAssembly(dir_abs_path)
            if len(hdl_assembly.instances) != 2:
                passed = False
            if hdl_assembly.instances['nothing0'] != 'nothing':
                passed = False
            if hdl_assembly.instances['nothing1'] != 'nothing':
                passed = False
            # create_test_ohad([('nothing', None), ('nothing', 'myname')],
            #                  dir_abs_path, quote=quote)
            # hdl_assembly = HdlAssembly(dir_abs_path)
            # if len(hdl_assembly.instances) != 2:
            #     passed = False
            # if hdl_assembly.instances['nothing'] != 'nothing':
            #     passed = False
            # if hdl_assembly.instances['myname'] != 'nothing':
            #     passed = False
            # create_test_ohad([('nothing', 'myname'), ('nothing', None)],
            #                  dir_abs_path, quote=quote)
            # hdl_assembly = HdlAssembly(dir_abs_path)
            # if len(hdl_assembly.instances) != 2:
            #     passed = False
            # if hdl_assembly.instances['myname'] != 'nothing':
            #     passed = False
            # if hdl_assembly.instances['nothing'] != 'nothing':
            #     passed = False
        except:
            passed = False
    instances = []
    # try:
    #     for count in range(128):
    #         instances.append(('nothing', None))
    #     create_test_ohad(instances, dir_abs_path, quote = quote)
    #     hdl_assembly = HdlAssembly(dir_abs_path)
    #     passed = False
    # except:
    #     pass
    log_pass_fail('testing HdlAssembly parse() self.instances', passed)
    if passed is False:
        ret = False
    return ret


def test_HdlAssembly_parse_containers(ret):
    passed = True
    log_pass_fail('testing HdlAssembly parse() self.containers', passed)
    return ret


def test_HdlAssembly_parse(ret):
    ret = test_HdlAssembly_InvalidAssetError_exception(ret)
    # ret = test_HdlAssembly_parse_instances(ret)
    ret = test_HdlAssembly_parse_containers(ret)
    return ret


def test_HdlAssembly_get_type(ret):
    passed = True
    fs = TemporaryFilesystem()
    dir_abs_path = fs.abs_path + '/' + 'assembly'
    try:
        create_test_ohad(['nothing'], dir_abs_path)
        passed = HdlAssembly(dir_abs_path).get_type() == 'hdl assembly'
    except:
        passed = False
    log_pass_fail('testing HdlAssembly get_type()', passed)
    if passed is False:
        ret = False
    return ret


def test_HdlAssembly(ret):
    ret = test_HdlAssembly___init__(ret)
    ret = test_HdlAssembly_parse(ret)
    ret = test_HdlAssembly_get_type(ret)
    return ret


def test_HdlContainerDevice(ret):
    passed = True
    try:
        hdl_container_device = HdlContainerDevice('mycard', 'myslot')
        if hdl_container_device.card != 'mycard':
            passed = False
        if hdl_container_device.slot != 'myslot':
            passed = False
    except:
        passed = False
    log_pass_fail('testing HdlContainerDevice', passed)
    if passed is False:
        ret = False
    return ret


def test_HdlContainer(ret):
    fs = TemporaryFilesystem()
    for test in [0, 1, 2, 3]:
        passed = True
        try:
            dir_abs_path = fs.abs_path + '/' + 'assembly'
            xml_abs_path = dir_abs_path + '/' + 'container.xml'
            os.system('mkdir -p ' + dir_abs_path)
            ff = open(xml_abs_path, 'w')
            ff.write('<HdlContainer Config=\'cfg\' Constraints=\'cst.xdc\' ')
            ff.write('OnlyPlatforms=\'zed alst4\' ExcludePlatforms=\'ml604\'/>\n')
            ff.close()
            uut = HdlContainer(xml_abs_path)
            if Environment().ocpi_log_level >= 10:
                print(uut.__dict__.keys())
                os.system('cat ' + xml_abs_path)
            if test == 0:
                passed = uut.config == 'cfg'
            if test == 1:
                passed = uut.constraints == 'cst.xdc'
            if test == 2:
                passed = uut.only_platforms == ['zed', 'alst4']
            if test == 3:
                passed = uut.exclude_platforms == ['ml604']
        except:
            passed = False
        if test == 0:
            log_pass_fail('testing HdlContainer config', passed)
        if test == 1:
            log_pass_fail('testing HdlContainer constraints', passed)
        if test == 2:
            log_pass_fail('testing HdlContainer only_platforms', passed)
        if test == 3:
            log_pass_fail('testing HdlContainer exclude_platforms', passed)
        if passed is False:
            ret = False
    return ret
