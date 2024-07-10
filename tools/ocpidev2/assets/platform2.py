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
from _opencpi.assets.abstract2 import *
from _opencpi.assets.abstract2 import AssetBase
from _opencpi.assets.worker2 import Worker


class HdlCardPlatformBase(AssetBase):

    def __init__(self, abs_path):
        AssetBase.__init__(self, abs_path)
        self.devices = dict()  # key = unique instance name, val = worker name

    def parse_devices(self):
        for elem in self.get_parsed().iter():
            if elem.tag.lower() == 'device':
                for attrib in elem.attrib:
                    if attrib.lower() == 'worker':
                        device = elem.attrib[attrib]
                        # PDG section 5.5.8
                        num_inst = 0
                        done = False
                        while not done:
                            done = True
                            for key, val in self.devices.items():
                                if key == device:
                                    del self.devices[val]
                                    self.devices[val + '0'] = val
                                    done = False
                                    break
                                if val == device:
                                    num_inst = num_inst + 1
                        if num_inst == 0:
                            self.devices[device] = device
                        else:
                            self.devices[device + str(num_inst)] = device


class HdlPlatform(HdlCardPlatformBase):
    """ Platform Development Guide section 5.4 """

    def __init__(self, dir_abs_path):
        self.root_tags = ['HdlPlatform']
        HdlCardPlatformBase.__init__(self, dir_abs_path)
        if not os.path.isfile(self.get_xml_abs_path()):
            self.raise_abs_path_does_not_exist()
        self.configurations = dict()
        try:
            self.configurations['base'] = HdlPlatformConfiguration(None)
        except InvalidAssetError:
            pass
        self.parse()

    def parse(self):
        self.parse_devices()
        owd_path = self.abs_path + '/' + self.name + '.xml'
        if self.name != Worker(owd_path).name:
            msg = ('platform directory ' + owd_path + ' , ' +
                   self.name + '.xml' + ' file does not contain equivalent '
                   'platform worker XML Name attiribute: ' + self.name)
            Logger().warn(msg)
        for cfg in self.get_attr_list('Configurations'):
            path = self.abs_path + '/' + cfg + '.xml'
            try:
                config = HdlPlatformConfiguration(path)
                self.configurations[cfg] = config
            except InvalidAssetError as err:
                if cfg != 'base':
                    raise err

    def get_type(self):
        return 'hdl platform'


class HdlPlatformConfigurationDevice(AttributeBase):

    def __init__(self, elem):
        self.name = ''
        AttributeBase.__init__(self, elem)
        self.parse(elem)

    def get_root_tags(self):
        return ['Device']

    def parse(self, elem):
        self.name = self.get_attr('Name', elem)


class HdlPlatformConfiguration(AssetBase):
    """ Platform Development Guide section 5.4.8 """

    def __init__(self, xml_abs_path):
        """ xml_abs_path is None for 'base' configuration """
        self.devices = []
        AssetBase.__init__(self, xml_abs_path)
        if (self.name != 'base') or (xml_abs_path is not None):
            self.parse()

    def get_root_tags(self):
        return ['HdlConfig']

    def parse(self):
        for elem in self.get_parsed().iter():
            try:
                device = HdlPlatformConfigurationDevice(elem)
                self.devices.append(device)
            except InvalidAttributeError:
                pass


class HdlCard(HdlCardPlatformBase):
    """ Platform Development Guide section 5.6 """

    def __init__(self, xml_abs_path):
        self.root_tags = ['Card']
        HdlCardPlatformBase.__init__(self, xml_abs_path)
        self.parse()

    def get_attr_infos(self):
        ret = []
        ret.append(AttributeInfo('Type'))
        return ret

    def parse(self):
        AssetBase.parse(self)
        self.parse_devices()

    def get_type(self):
        return 'hdl card'


class HdlCardPlatformBaseTester(HdlCardPlatformBase):
    """ Platform Development Guide section 5.4 """

    def __init__(self, dir_abs_path):
        HdlCardPlatformBase.__init__(self, dir_abs_path)

    def get_root_tags(self):
        return ['Test']


def test_HdlCardPlatformBase(ret):
    fs = TemporaryFilesystem()
    for test in [0, 1, 2]:
        passed = True
        try:
            dir_abs_path = fs.abs_path + '/' + 'foo'
            xml_abs_path = dir_abs_path + '/' + 'foo.xml'
            os.system('mkdir -p ' + dir_abs_path)
            ff = open(xml_abs_path, 'w')
            ff.write('<Test>\n')
            ff.write('  <Device Worker=\'foo\'/>\n')
            ff.write('</Test>\n')
            ff.close()
            uut = HdlCardPlatformBaseTester(dir_abs_path)
            # if Environment().ocpi_log_level >= 10:
            #     print(str([a for a in dir(uut) if not
            #           callable(getattr(uut, a))]))
            #     os.system('cat ' + xml_abs_path)
            if test == 0:
                passed = uut.abs_path == dir_abs_path
            if test == 1:
                passed = uut.name == 'foo'
            # if test == 2:
            #     passed = (uut.devices.keys() == ['foo']) and
            #              (uut.devices.values() == ['foo'])
        except InvalidAssetError:
            passed = False
        if test == 0:
            log_pass_fail('testing HdlCardPlatformBase abs_path', passed)
        if test == 1:
            log_pass_fail('testing HdlCardPlatformBase name', passed)
        # if test == 2:
        #     log_pass_fail('testing HdlCardPlatformBase devices', passed)
        if passed is False:
            ret = False
    return ret


def test_HdlPlatform(ret):
    passed = True
    fs = TemporaryFilesystem()
    dir_abs_path = fs.abs_path + '/' + 'platform'
    xml_abs_path = dir_abs_path + '/' + 'platform.xml'
    try:
        os.system('mkdir -p ' + dir_abs_path)
        ff = open(xml_abs_path, 'w')
        ff.write('<HdlPlatform/>\n')
        ff.close()
        uut = HdlPlatform(dir_abs_path)
        if Environment().ocpi_log_level >= 10:
            print(str([a for a in dir(uut) if not
                  callable(getattr(uut, a))]))
            os.system('cat ' + xml_abs_path)
    except InvalidAssetError:
        passed = False
    log_pass_fail('testing HdlPlatform', passed)
    if passed is False:
        ret = False
    return ret


def test_HdlPlatformConfiguration(ret):
    passed = True
    fs = TemporaryFilesystem()
    dir_abs_path = fs.abs_path + '/' + 'platform'
    xml_abs_path = dir_abs_path + '/' + 'config.xml'
    try:
        os.system('mkdir -p ' + dir_abs_path)
        ff = open(xml_abs_path, 'w')
        ff.write('<HdlConfig/>\n')
        ff.close()
        if Environment().ocpi_log_level >= 10:
            os.system('cat ' + xml_abs_path)
        platform = HdlPlatformConfiguration(xml_abs_path)
    except InvalidAssetError:
        passed = False
    log_pass_fail('testing HdlPlatformConfiguration', passed)
    if passed is False:
        ret = False
    return ret


def test_HdlCard(ret):
    passed = True
    fs = TemporaryFilesystem()
    dir_abs_path = fs.abs_path + '/' + 'cards/specs'
    xml_abs_path = dir_abs_path + '/' + 'card.xml'
    try:
        os.system('mkdir -p ' + dir_abs_path)
        ff = open(xml_abs_path, 'w')
        ff.write('<Card Type=\'a_slot\'>\n')
        ff.write('  <Device Worker=\'foo\'/>\n')
        ff.write('</Card>\n')
        ff.close()
        uut = HdlCard(xml_abs_path)
        if Environment().ocpi_log_level >= 10:
            print(str([a for a in dir(uut) if not callable(getattr(uut, a))]))
            os.system('cat ' + xml_abs_path)
        if uut.abs_path != xml_abs_path:
            passed = False
        log_pass_fail('testing HdlCard abs_path', passed)
        if uut.name != 'card':
            passed = False
        log_pass_fail('testing HdlCard name', passed)
        if len(uut.devices) != 1:
            passed = False
        else:
            if (uut.devices['foo'] != 'foo'):
                passed = False
        log_pass_fail('testing HdlCard devices', passed)
        if uut.attrs['Type'] != 'a_slot':
            passed = False
    except InvalidAssetError:
        passed = False
    log_pass_fail('testing HdlCard type', passed)
    if passed is False:
        ret = False
    return ret
