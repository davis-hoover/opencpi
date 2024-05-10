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
from _opencpi.assets.abstract2 import _AssetBase


class Worker(_AssetBase):
    """ Reference RCC/HDL Development Guide section 3. A Worker is
        represented by a xml file (OWD) and knows nothing about the project it
        is in or its package ID. """

    def __init__(self, xml_abs_path):
        _AssetBase.__init__(self, xml_abs_path)
        self.spec = ''  # CDG section 8.1.2
        # self.language = ''  # CDG section 8.1.3
        # self.version = ''  # CDG secion 8.1.4
        self.source_files = []  # CDG section 8.1.10
        self.libraries = []  # CDG section 8.1.11
        # self.control_operations = ''  # RDG section 3.1.3
        # self.slave = ''  # RDG section 3.1.5
        self.authoring_model = ''
        directory_name = self.abs_path.split('/', -2)[-2]
        if directory_name.endswith('.hdl'):
            self.authoring_model = 'hdl'
        elif directory_name.endswith('.rcc'):
            self.authoring_model = 'rcc'
        else:
            # is a hdl platform worker case
            self.authoring_model = 'hdl'
        self.parse()

    def get_root_tags(self):
        ret = ['HdlWorker', 'HdlDevice']  # PDG section 5.4.4
        ret += ['HdlPlatform', 'RccWorker']
        # start pre-2.0 opencpi
        ret += ['HdlImplementation', 'RccImplementation']
        # end pre-2.0 opencpi
        return ret

    def parse(self):
        Logger().debug('parsing ' + self.get_xml_abs_path())
        paths = []
        # start pre-2.0 opencpi
        paths += [self.abs_path + '/Makefile']
        # intentionally put xml last so that its attributes take precedence
        # end pre-2.0 opencpi
        paths.append(self.get_xml_abs_path())
        for path in self.get_list_of_existing_abs_paths_to_parse(paths):
            name = self.get_attr('Name', None, path)
            if name != '':
                self.name = name
            spec = self.get_attr('Spec', None, path)
            if spec != '':
                self.spec = spec.replace('-spec', '').replace('_spec', '')
            # self.language = self.get_attr('Language', None, path)
            # self.version = self.get_attr('Version', None, path)
            files = self.get_attr_list('SourceFiles', None, path)
            if files != '':
                self.source_files = files
            libraries = self.get_attr_list('Libraries', None, path)
            if len(libraries) > 0:
                # TODO replace ocpi.core. delete according to CDG 8.1.11
                self.libraries = [str(lib).replace('ocpi.core.', '')
                                  for lib in libraries]

    def get_type(self):
        return self.authoring_model + ' worker'


# TODO iherit from, and consolidate functionality from, _AssetBase
class RccAssembly(_AssetBase):

    def __init__(self, dir_abs_path):
        _AssetBase.__init__(self, dir_abs_path)
        # below line is undocumented edge case (testzc.rcc/Makefile Workers)
        self.workers = []
        workers = self.parse()
        self.discover(workers)

    def get_root_tags(self):
        return ['RccWorker']

    def parse(self):
        workers = []
        paths = []
        paths.append(self.get_dir_abs_path() + '/Makefile')
        for path in self.get_list_of_existing_abs_paths_to_parse(paths):
            workers = self.get_variable_val_list_from_gnu_makefile(
                    'Workers', path)
        return workers

    def discover(self, workers):
        self.discover_workers(workers)

    def discover_workers(self, workers):
        for entry in _AssetBase.listdir_assets(self.get_dir_abs_path()):
            if (entry.split('.')[0] in workers) or (workers == []):
                owd_path = self.get_dir_abs_path() + '/' + entry
                if entry.endswith('.xml'):
                    try:
                        self.workers.append(Worker(owd_path))
                    except InvalidAssetError as err:
                        pass

    def get_type(self):
        return 'rcc assembly'


def test_Worker___init___common(ret, test):
    passed = True
    fs = TemporaryFilesystem()
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
        ff.close()
        uut = Worker(xml_abs_path)
        if Environment().ocpi_log_level >= 10:
            print(str([a for a in dir(uut) if not callable(getattr(uut, a))]))
            os.system('cat ' + xml_abs_path)
        if test == 0:
            if uut.abs_path != xml_abs_path:
                passed = False
        elif test == 1:
            if uut.name != 'worker':
                passed = False
        elif test == 2:
            if uut.spec != 'comp':
                passed = False
        elif test == 3:
            if uut.source_files != ['1.cc', '2.cc']:
                passed = False
        elif test == 4:
            if uut.libraries != ['foo']:
                passed = False
        elif test == 5:
            if uut.authoring_model != 'rcc':
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
    if passed is False:
        ret = False
    return ret


def test_Worker___init___abs_path(ret):
    return test_Worker___init___common(ret, 0)


def test_Worker___init___name(ret):
    return test_Worker___init___common(ret, 1)


def test_Worker___init___spec(ret):
    return test_Worker___init___common(ret, 2)


def test_Worker___init___source_files(ret):
    return test_Worker___init___common(ret, 3)


def test_Worker___init___libraries(ret):
    return test_Worker___init___common(ret, 4)


def test_Worker___init___authoring_model(ret):
    return test_Worker___init___common(ret, 5)


def test_Worker(ret):
    ret = test_Worker___init___abs_path(ret)
    ret = test_Worker___init___name(ret)
    ret = test_Worker___init___spec(ret)
    ret = test_Worker___init___source_files(ret)
    ret = test_Worker___init___libraries(ret)
    ret = test_Worker___init___authoring_model(ret)
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
            if Environment().ocpi_log_level >= 10:
                print(str([a for a in dir(uut) if not
                      callable(getattr(uut, a))]))
                os.system('cat ' + xml_abs_path)
                os.system('cat ' + xml_abs_path)
        uut = RccAssembly(dir_abs_path)
        passed = len(uut.workers) == 2
    except InvalidAssetError:
        passed = False
    log_pass_fail('testing RccAssembly workers', passed)
    if passed is False:
        ret = False
    return ret
