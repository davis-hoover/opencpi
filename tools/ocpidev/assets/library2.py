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
from _opencpi.assets.component2 import Component
from _opencpi.assets.worker2 import Worker, RccAssembly
# below 4 lines are a weird, unintended consequence of Discoverer
from _opencpi.assets.platform2 import HdlPlatform
from _opencpi.assets.assembly2 import HdlAssembly
from _opencpi.assets.primitive2 import HdlLibrary
from _opencpi.assets.application2 import Application


class SpecsDirectory():

    def __init__(self):
        self.components = []

    def discover(self):
        self.discover()

    def discover_components(self):
        for _dir in os.listdir(self.abs_path):
            if _dir == 'specs':
                discovery_path = self.abs_path + '/' + _dir
                for name in AssetBase.listdir_assets(discovery_path):
                    path = self.abs_path + '/' + _dir + '/' + name
                    try:
                        asset = Component(path)
                        self.append_discovered_asset(asset)
                    except InvalidAssetError:
                        pass


class Discoverer():

    def append_discovered_asset(self, asset):
        if asset.get_type() == 'component':
            self.components.append(asset)
        if asset.get_type() == 'component library':
            self.component_libraries.append(asset)
        if asset.get_type() == 'application':
            self.applications.append(asset)
        if asset.get_type() == 'hdl primitive':
            self.hdl_primitives.append(asset)
        if asset.get_type() == 'hdl assembly':
            self.hdl_assemblies.append(asset)
        if asset.get_type() == 'hdl card':
            self.hdl_cards.append(asset)
        if asset.get_type() == 'hdl platform':
            self.hdl_platforms.append(asset)
        _type = asset.get_type()
        if (_type == 'hdl worker') or (_type == 'rcc worker'):
            self.workers.append(asset)
        Logger().log(9, 'discovered ' + _type + ' ' + asset.abs_path)

    def get_potential_asset_dir_abs_paths(self, parent):
        ret = []
        discovery_path = self.abs_path + '/' + parent
        if os.path.isdir(discovery_path):
            for _dir in AssetBase.listdir_assets(discovery_path):
                dir_abs_path = discovery_path + '/' + _dir
                if os.path.isdir(dir_abs_path):
                    ret.append(dir_abs_path)
        return ret

    def discover_dir_assets(self, parent, allowlist=None, platform=False):
        for dir_abs_path in self.get_potential_asset_dir_abs_paths(parent):
            try:
                assets = []
                tmp = dir_abs_path
                if parent == 'hdl/platforms':
                    assets.append(HdlPlatform(dir_abs_path))
                elif parent == 'hdl/assemblies':
                    assets.append(HdlAssembly(dir_abs_path))
                elif parent == 'hdl/primitives':
                    assets.append(HdlLibrary(dir_abs_path))
                elif parent == 'applications':
                    assets.append(Application(dir_abs_path))
                elif tmp.endswith('.rcc') or tmp.endswith('.hdl') or platform:
                    name = AssetBase.get_name_from_abs_path(dir_abs_path)
                    if tmp.endswith('.rcc'):
                        # due to edge cases such as testzc.rcc, testmulti.rcc
                        assets = RccAssembly(dir_abs_path).workers
                    elif not tmp.endswith('.test'):
                        assets.append(Worker(dir_abs_path + '/' + name + '.xml'))
                for asset in assets:
                    if allowlist is not None:
                        # TODO is this pre-2.0???
                        allowlist = [name.split('.')[0] for name in allowlist]
                    if (allowlist is None) or (asset.name in allowlist):
                        self.append_discovered_asset(asset)
            except InvalidAssetError as err:
                if parent != 'applications':
                    Logger().warn('skipping ' + str(err))
                pass


class ComponentLibrary(AssetBase, SpecsDirectory, Discoverer):
    """ Reference RCC/HDL Development Guide section 3. A ComponentLibrary is
        represented by a directory and knows nothing about the project it
        is in or its package ID. """

    def __init__(self, dir_abs_path):
        AssetBase.__init__(self, dir_abs_path)
        is_test = self.get_dir_abs_path_is_test(dir_abs_path)
        if is_test or self.get_dir_abs_path_is_worker(dir_abs_path):
            self.raise_invalid_asset_error()
        SpecsDirectory.__init__(self)
        # start of bullets at top of CDG section 10
        self.components = []
        self.protocols = []
        self.workers = []
        self.tests = []
        # end of bullets at top of CDG section 10
        # start of CDG section 14.5 (XML)
        self.component_libraries = []
        self.hdl_libraries = []
        # end of CDG section 14.5
        workers = self.parse()
        allowlist = None if workers == [] else workers
        self.discover(allowlist, 'hdl/platforms' in dir_abs_path)

    def get_root_tags(self):
        ret = ['Library']  # CDG section 10.1
        return ret

    @staticmethod
    def get_dir_abs_path_is_worker(dir_abs_path):
        ret = False
        for ext in ['rcc', 'hdl', 'ocl']:
            if dir_abs_path.endswith('.' + ext):
                ret = True
        return ret

    @staticmethod
    def get_dir_abs_path_is_test(dir_abs_path):
        return dir_abs_path.endswith('.test')

    def get_package_id(self, project_package_id_str):
        """ the overarching project tells this method its
            project_package_id_str """
        ret = project_package_id_str
        abs_path_split = self.abs_path.split('/')
        if len(abs_path_split) >= 3:
            if abs_path_split[-3] == 'platforms':
                ret += '.platforms.' + abs_path_split[-2]
        # use e.g. ocpi.core instead of ocpi.core.components (same as OAS)
        if self.name != 'components':
            ret += '.' + self.name
        return ret

    def parse(self):
        paths = []
        # start pre-2.0 opencpi
        # TODO address library.mk vs libraries.mk behavior in Makefile
        paths += [self.abs_path + '/Library.mk', self.abs_path + '/Makefile']
        # intentionally put xml last so that its attributes take precedence
        # end pre-2.0 opencpi
        paths.append(self.get_xml_abs_path())
        workers = []
        paths = self.get_list_of_existing_abs_paths_to_parse(paths)
        clibs = self.get_attr_list('ComponentLibraries', None, paths)
        if len(clibs) > 0:
            self.component_libraries = clibs
        hlibs = self.get_attr_list('HdlLibraries', None, paths)
        if len(hlibs) > 0:
            self.hdl_libraries = hlibs
        workers = self.get_attr_list('Workers', None, paths)
        global g_libraries_mk
        if g_libraries_mk:
            g_libraries_mk = False
        return workers

    def discover(self, allowlist, platform=False):
        self.discover_components()
        self.discover_workers(allowlist, platform)

    def discover_components(self):
        SpecsDirectory.discover_components(self)
        for discovery_path in self.get_potential_asset_dir_abs_paths(''):
            if discovery_path.endswith('.comp'):  # undocumented
                for entry in AssetBase.listdir_assets(discovery_path):
                    try:
                        asset = Component(discovery_path + '/' + entry)
                        self.append_discovered_asset(asset)
                    except InvalidAssetError:
                        pass

    def discover_workers(self, allowlist, platform=False):
        """ workers is a list containing the attribute that serves as a
            discovery "allowlist" """
        # Logger().debug(str(allowlist))
        # '' in below line indicates worker discovery
        self.discover_dir_assets('', allowlist, platform)

    def get_type(self):
        return 'component library'


def test_ComponentLibrary(ret):
    fs = TemporaryFilesystem()
    for test in range(7):
        passed = True
        try:
            dir_abs_path = fs.abs_path + '/' + 'components'
            os.system('mkdir -p ' + dir_abs_path + '/' + 'foo.comp')
            ff = open(dir_abs_path + '/' + 'components.xml', 'w')
            ff.write('<Library/>\n')
            ff.close()
            ff = open(dir_abs_path + '/foo.comp' + '/' + 'mycomp.xml', 'w')
            ff.write('<ComponentSpec/>\n')
            ff.close()
            uut = ComponentLibrary(dir_abs_path)
            if test == 0:
                passed = uut.abs_path == dir_abs_path
            if test == 1:
                passed = uut.name == 'components'
            if test == 2:
                passed = len(uut.components) == 1
            if test == 3:
                passed = uut.workers == []
            if test == 4:
                passed = uut.tests == []
            if test == 5:
                passed = uut.component_libraries == []
            if test == 6:
                if uut.get_package_id('ocpi.core') != 'ocpi.core':
                    passed = False
                uut.name = 'devices'
                if uut.get_package_id('ocpi.core') != 'ocpi.core.devices':
                    passed = False
                uut.abs_path = '/tmp/myproj/hdl/platforms/mypf/devices'
                if uut.get_package_id('ocpi.core') != 'ocpi.core.platforms.mypf.devices':
                    passed = False
        except InvalidAssetError:
            passed = False
        if test == 0:
            log_pass_fail('testing ComponentLibrary abs_path', passed)
        if test == 1:
            log_pass_fail('testing ComponentLibrary name', passed)
        if test == 2:
            log_pass_fail('testing ComponentLibrary components', passed)
        if test == 3:
            log_pass_fail('testing ComponentLibrary workers', passed)
        if test == 4:
            log_pass_fail('testing ComponentLibrary tests', passed)
        if test == 5:
            log_pass_fail('testing ComponentLibrary component_libraries', passed)
        if test == 6:
            log_pass_fail('testing ComponentLibrary get_package_id()', passed)
        if passed is False:
            ret = False
    return ret
