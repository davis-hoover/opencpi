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
# if os.path.isfile(os.getcwd() + '/platform.py'):
#     # collision with uuid's 'import platform' and this directory's
#     # platform.py
#     raise Exception('do not run this from the assets directory!')
import uuid
from _opencpi.assets.abstract2 import *
from _opencpi.assets.abstract2 import AssetBase


class Worker(AssetBase):
    """ Reference RCC/HDL Development Guide section 3. A Worker is
        represented by a xml file (OWD) and knows nothing about the project it
        is in or its package ID. """

    def __init__(self, xml_abs_path):
        self.root_tags = ['HdlWorker', 'HdlDevice']  # PDG section 5.4.4
        self.root_tags += ['HdlPlatform', 'RccWorker']
        # start pre-2.0 opencpi
        self.root_tags += ['HdlImplementation', 'RccImplementation']
        # end pre-2.0 opencpi
        AssetBase.__init__(self, xml_abs_path)
        self.authoring_model = ''
        directory_name = self.abs_path.split('/', -2)[-2]
        if directory_name.endswith('.hdl'):
            self.authoring_model = 'hdl'
        elif directory_name.endswith('.rcc'):
            self.authoring_model = 'rcc'
        else:
            # is a hdl platform worker case
            self.authoring_model = 'hdl'
        self.supports = [] # PDG section 5.5.4
        self.parse()

    def get_paths_to_parse(self):
        paths = []
        # start pre-2.0 opencpi
        paths += [self.get_dir_abs_path() + '/Makefile']
        # intentionally put xml last so that its attributes take precedence
        # end pre-2.0 opencpi
        paths.append(self.get_xml_abs_path())
        paths = self.get_list_of_existing_abs_paths_to_parse(paths)
        return paths

    def get_attr_infos(self):
        ret = []
        ret.append(AttributeInfo('Name'))
        ret.append(AttributeInfo('Spec'))  # CDG section 8.1.2
        ret.append(AttributeInfo('Language'))  # CDG section 8.1.3
        ret.append(AttributeInfo('Version', is_int=True))  # CDG secion 8.1.4
        is_list = True
        ret.append(AttributeInfo('SourceFiles', is_list))  # CDG section 8.1.10
        ret.append(AttributeInfo('Libraries', is_list))  # CDG section 8.1.11
        # control_operations  # RDG section 3.1.3
        # slave  # RDG section 3.1.5
        return ret

    def parse(self):
        AssetBase.parse(self)
        if self.attrs['Name'] != '':
            self.name = self.attrs['Name']
        spec = self.attrs['Spec']
        self.attrs['Spec'] = spec.replace('-spec', '').replace('_spec', '')
        # TODO replace ocpi.core. delete according to CDG 8.1.11
        self.attrs['Libraries'] = \
            [str(lib).replace('ocpi.core.', '')
             for lib in self.attrs['Libraries']]
        if self.authoring_model == 'hdl':
            for elem in self.get_parsed().iter():
                if elem.tag.lower() == 'supports':
                    for key, val in elem.attrib.items():
                        if key.lower() == 'worker':
                            self.supports.append(val)

    def get_type(self):
        return self.authoring_model + ' worker'

    def create_templates(self):
        pass

    def create(self):
        pass


class RccAssembly(AssetBase):

    def __init__(self, dir_abs_path):
        AssetBase.__init__(self, dir_abs_path)
        # below line is undocumented edge case (testzc.rcc/Makefile Workers)
        self.workers = []
        self.parse()
        self.discover()

    def get_root_tags(self):
        # TODO replace get_root_tags() with self.root_tags
        return ['RccWorker']

    def get_attr_infos(self):
        ret = []
        ret.append(AttributeInfo('Workers', is_list=True))
        return ret

    def get_paths_to_parse(self):
        paths = []
        paths.append(self.get_dir_abs_path() + '/Makefile')
        return paths

    def discover(self):
        self.discover_workers()

    def discover_workers(self):
        for entry in AssetBase.listdir_assets(self.get_dir_abs_path()):
            workers_attr = self.attrs['Workers']
            if (entry.split('.')[0] in workers_attr or (workers_attr == [])):
                owd_path = self.get_dir_abs_path() + '/' + entry
                if entry.endswith('.xml'):
                    try:
                        self.workers.append(Worker(owd_path))
                    except InvalidAssetError as err:
                        pass

    def get_type(self):
        return 'rcc assembly'


def test_Worker(ret):
    fs = TemporaryFilesystem()
    for test in range(8):
        passed = True
        ext = 'rcc'
        dir_abs_path = fs.abs_path + '/' + 'worker.' + ext
        xml_abs_path = dir_abs_path + '/' + 'worker.xml'
        try:
            os.system('mkdir -p ' + dir_abs_path)
            ff = open(xml_abs_path, 'w')
            if test == 0:
                ff.write('<HdlWorker/>\n')
            elif test == 1:
                ff.write('<HdlWorker Name=\'worker\'/>\n')
            elif test == 2:
                ff.write('<HdlWorker Spec=\'comp\'/>\n')
            elif test == 3:
                ff.write('<HdlWorker SourceFiles=\'1.cc 2.cc\'/>\n')
            elif test == 4:
                ff.write('<HdlWorker Libraries=\'foo\'/>\n')
            elif test == 5:
                ff.write('<HdlWorker/>\n')
            elif test == 6:
                ff.write('<HdlWorker Language=\'lang\'/>\n')
            elif test == 7:
                ff.write('<HdlWorker Version=\'2\'/>\n')
            ff.close()
            uut = Worker(xml_abs_path)
            if Environment().ocpi_log_level >= 10:
                print(uut.__dict__.keys())
                os.system('cat ' + xml_abs_path)
            if test == 0:
                if uut.abs_path != xml_abs_path:
                    passed = False
            elif test == 1:
                if uut.name != 'worker':
                    passed = False
            elif test == 2:
                if uut.attrs['Spec'] != 'comp':
                    passed = False
            elif test == 3:
                if uut.attrs['SourceFiles'] != ['1.cc', '2.cc']:
                    passed = False
            elif test == 4:
                if uut.attrs['Libraries'] != ['foo']:
                    passed = False
            elif test == 5:
                if uut.authoring_model != 'rcc':
                    passed = False
            elif test == 6:
                if uut.attrs['Language'] != 'lang':
                    passed = False
            elif test == 7:
                if uut.attrs['Version'] != 2:
                    passed = False
        except InvalidAssetError:
            passed = False
        if test == 0:
            log_pass_fail('testing Worker abs_path', passed)
        elif test == 1:
            log_pass_fail('testing Worker name', passed)
        elif test == 2:
            log_pass_fail('testing Worker spec', passed)
        elif test == 3:
            log_pass_fail('testing Worker source_files', passed)
        elif test == 4:
            log_pass_fail('testing Worker libraries', passed)
        elif test == 5:
            log_pass_fail('testing Worker authoring_model', passed)
        elif test == 6:
            log_pass_fail('testing Worker Language', passed)
        elif test == 7:
            log_pass_fail('testing Worker Version', passed)
        if passed is False:
            ret = False
    return ret


def test_RccAssembly(ret):
    fs = TemporaryFilesystem()
    passed = True
    try:
        dir_abs_path = fs.abs_path + '/' + 'components/foo.rcc'
        os.system('mkdir -p ' + dir_abs_path)
        for name in ['foo1', 'foo2']:
            xml_abs_path = dir_abs_path + '/' + name + '.xml'
            ff = open(xml_abs_path, 'w')
            ff.write('<RccWorker/>\n')
            ff.close()
        uut = RccAssembly(dir_abs_path)
        if Environment().ocpi_log_level >= 10:
            print(uut.__dict__.keys())
            os.system('cat ' + xml_abs_path)
        passed = len(uut.workers) == 2
    except InvalidAssetError:
        passed = False
    log_pass_fail('testing RccAssembly workers', passed)
    if passed is False:
        ret = False
    return ret
