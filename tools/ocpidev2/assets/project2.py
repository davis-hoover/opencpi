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
import hashlib
import itertools
from _opencpi.assets.abstract2 import *
from _opencpi.assets.abstract2 import AssetBase
from _opencpi.assets.worker2 import Worker
from _opencpi.assets.application2 import Application
from _opencpi.assets.library2 import SpecsDirectory, Discoverer
from _opencpi.assets.library2 import ComponentLibrary, ComponentLibraries
from _opencpi.assets.library2 import test_ComponentLibrary
from _opencpi.assets.primitive2 import HdlLibrary
from _opencpi.assets.assembly2 import HdlAssembly
from _opencpi.assets.platform2 import HdlSlot, HdlCard
from _opencpi.assets.platform2 import HdlPlatform, RccPlatform


class Project(AssetBase, SpecsDirectory, Discoverer):
    """ Component Development Guide section 14 """

    def __init__(self, dir_abs_path, enable_path_existence_check=True,
                 cli_dict=None):
        self.root_tags = ['Project']
        AssetBase.__init__(self, dir_abs_path, enable_path_existence_check)
        SpecsDirectory.__init__(self)
        # start of bullets at top of CDG section 14 (XML, project INTERNAL)
        self.component_libraries = []
        self.applications = []
        self.hdl_primitives = []
        self.hdl_assemblies = []
        self.hdl_devices = []
        self.hdl_cards = []
        self.hdl_slots = []
        self.hdl_platforms = []
        # end of bullets at top of CDG section 14
        self.rcc_platforms = []
        self.assets = []  # TODO replaces above bullets with self.assets
        # start of CDG section 14.5 (EXTERNAL-to-project, i.e., DEPENDENCY)
        # HDG section 5 "The built-in ocpi.core project includes several HDL
        # primitive libraries, and some are always available for use by all
        # workers" - here are the implied "some"
        self.hdl_libraries = ['bsv', 'fixed_float', 'ocpi', 'util', 'protocol']
        self.hdl_libraries += ['cdc', 'sdp', 'axi']
        # initialize below line according to CDG Table 8
        self.project_dependencies = ['ocpi.core']
        # end of CDG section 14.5
        self.parse(cli_dict)
        self.first = True

    def get_type(self):
        return 'project'

    def get_attr_infos(self):
        ret = []
        # Attributes provided (partially) in CDG 10.1 Table 7
        ret.append(AttributeInfo('ProjectDependencies',
                   is_list=True, cli=('-D', '--depend')))
        ret.append(AttributeInfo('PackagePrefix',
                   cli=('-F', '--package-prefix')))
        ret.append(AttributeInfo('PackageID',
                   cli=('-K', '--package-id')))
        ret.append(AttributeInfo('PackageName',
                   cli=('-N', '--package-name')))
        ret.append(AttributeInfo('XmlIncludeDirs',
                   is_list=True, cli=('-A', '--xml-include')))
        ret.append(AttributeInfo('IncludeDirs',
                   is_list=True, cli=('-I', '--include-dir')))
        ret.append(AttributeInfo('HdlLibraries',
                   is_list=True, cli=('-Y', '--primitive-library')))
        ret.append(AttributeInfo('Libraries',
                   is_list=True, cli=('-y', '--component-library')))
        for attr_key in ['HdlTargets', 'HdlPlatforms', 'RccPlatforms',
                         'RccHdlPlatforms', 'ComponentLibraries',
                         'OnlyTargets', 'OnlyPlatforms',
                         'ExcludeTargets', 'ExcludePlatforms']:
            ret.append(AttributeInfo(attr_key, is_list=True))
        return ret

    def get_xml_abs_path(self):
        return self.abs_path + '/Project.xml'

    def get_buildable_paths(self):
        return [self.abs_path + '/hdl', self.abs_path + '/hdl/assemblies']

    def get_package_id(self):
        ret = ''
        if self.attrs['PackagePrefix'] == '':
            ret += 'local'
        else:
            ret += self.attrs['PackagePrefix']
        ret += '.'
        if self.attrs['PackageName'] == '':
            ret += self.name
        else:
            ret += self.attrs['PackageName']
        return ret

    def get_worker_by_name(self, name, authoring_model=''):
        ret = None
        for component_library in self.component_libraries:
            for worker in component_library.workers:
                if worker.name == name:
                    am = authoring_model
                    if (am == '') or (worker.authoring_model == am):
                        ret = worker
        return ret

    def get_asset(self, abs_path):
        """ returns None if asset not found """
        ret = None
        for component_library in self.component_libraries:
            for asset in component_library.workers:
                if asset.get_xml_abs_path() == abs_path:
                    ret = asset
                elif asset.get_dir_abs_path() == abs_path:
                    ret = asset
        for asset in self.applications:
            if asset.get_dir_abs_path() == abs_path:
                ret = asset
        for asset in self.hdl_primitives:
            if asset.get_dir_abs_path() == abs_path:
                ret = asset
        for asset in self.hdl_assemblies:
            if asset.get_dir_abs_path() == abs_path:
                ret = asset
        return ret

    def get_paths_to_parse(self):
        paths = []
        # start pre-2.0 opencpi
        paths += [self.abs_path + '/Project.mk']
        # intentionally put xml last so that its attributes take precedence
        # TODO consolidate with get_asset2() from AttributeBase
        paths.append(self.get_xml_abs_path())
        # end pre-2.0 opencpi
        paths = self.get_list_of_existing_abs_paths_to_parse(paths)
        return paths

    def parse(self, cli_dict):
        AssetBase.parse(self, cli_dict)
        self.hdl_libraries.extend(self.attrs['HdlLibraries'])
        self.project_dependencies.extend(self.attrs['ProjectDependencies'])
        # TODO: Include these checks in other parse() get_attr_list logic
        if self.attrs['PackagePrefix'] != '':
            if not self.attrs['PackagePrefix'].isidentifier():
                msg = 'PackagePrefix must contain only alphanumeric '
                msg += 'characters and not start with a number'
                raise InvalidAssetError(msg)

    def discover(
            self, do_component_libraries=True, do_hdl_primitives=True,
            do_hdl_assemblies=True):
        # start of bullets at top of CDG section 14
        if do_component_libraries:
            tmp = self.abs_path.split('/')[-1]
            Logger().info('discovering project ' + tmp)
            self.discover_components()
            self.discover_component_libraries()
            for component_library in self.component_libraries:
                for asset in component_library.workers:
                    # todo replace self.component_libraries with self.assets
                    self.assets.append(asset)
        # TODO fix below optimization line
        if do_hdl_primitives:
            self.discover_applications()
        if do_hdl_primitives:
            self.discover_hdl_primitives()
        if do_hdl_assemblies:
            self.discover_hdl_assemblies()
        # TODO fix below optimization line
        if do_hdl_primitives:
            self.discover_hdl_slots()
            self.discover_hdl_cards()
            self.discover_hdl_platforms()
            self.discover_rcc_platforms()
        # end of bullets at top of CDG section 14

    def get_existing_dir_abs_paths_for_clib_consideration(self):
        """ returns a list of absolute paths to directories in standard
            component libraries locations that are guaranteed to exist """
        # CDG section 14.2.3
        dir_abs_paths = []
        for _dir in ComponentLibrary.valid_locations:
            dir_abs_path = self.get_dir_abs_path() + '/' + _dir
            if os.path.isdir(dir_abs_path):
                # add to dir_abs_path the absolute path to the directories
                # of the following form from CDG section 14.2.3., if they
                # exist, regardless of whether a "sub"-library directory, e.g.
                # components/<library>, exists:
                #   - components/
                #   - hdl/devices/
                #   - hdl/cards/
                #   - hdl/adapters/
                #   - hdl/platforms/
                dir_abs_paths.append(dir_abs_path)
                a = dir_abs_path
                b = AssetBase.get_existing_abs_dir_paths_for_asset_consid(a)
                subdir_abs_paths = b
                if _dir == 'components':
                    for subdir_abs_path in subdir_abs_paths:
                        a = subdir_abs_path
                        if not ComponentLibrary.get_dir_abs_path_is_worker(a):
                            # add to dir_abs_path the absolute path to the
                            # directories of the following parents from CDG
                            # section 14.2.3., if they exist:
                            #   - hdl/platforms/<platform>/devices
                            #   - components/<library>
                            dir_abs_paths.append(subdir_abs_path)
                elif _dir == 'hdl/platforms':
                    for platform in subdir_abs_paths:
                        subdir_abs_path = platform + '/devices'
                        if os.path.isdir(subdir_abs_path):
                            # add to dir_abs_path the absolute path to the
                            # directories of the following parents from CDG
                            # section 14.2.3., if they exist:
                            #   - hdl/platforms/<platform>/devices
                            dir_abs_paths.append(subdir_abs_path)
        return dir_abs_paths

    def discover_component_libraries(self):
        tmp = self.get_existing_dir_abs_paths_for_clib_consideration()
        for dir_abs_path in tmp:
            try:
                is_libs = False
                try:
                    ComponentLibraries(dir_abs_path)
                    is_libs = True
                except InvalidAssetError as err:
                    pass
                # try:
                asset = ComponentLibrary(dir_abs_path)
                if not is_libs:
                    self.append_discovered_asset(asset)
                # except InvalidAssetError:
                #     pass
            except InvalidAssetError as err:
                path = dir_abs_path
                test = ComponentLibrary.get_dir_abs_path_is_test(path)
                worker = ComponentLibrary.get_dir_abs_path_is_worker(path)
                if (not test) and (not worker):
                    Logger().warn('skipping ' + path + ': ' + str(err))
                pass

    def discover_applications(self):
        # TODO check if there is an allowlist, and if so, pass to below call
        self.discover_dir_assets('applications')
        # TODO move from self.applications to generic self.assets
        self.assets.extend(self.applications)

    def discover_hdl_primitives(self):
        self.discover_dir_assets('hdl/primitives')
        # TODO move from self.hdl_primitives to generic self.assets
        self.assets.extend(self.hdl_primitives)

    def discover_hdl_assemblies(self):
        # TODO check if there is an allowlist, and if so, pass to below call
        self.discover_dir_assets('hdl/assemblies')
        # TODO move from self.hdl_assemblies to generic self.assets
        self.assets.extend(self.hdl_assemblies)

    def discover_hdl_slots(self):
        discovery_path = self.abs_path + '/hdl/cards/specs'
        if os.path.isdir(discovery_path):
            for _dir in AssetBase.listdir_assets(discovery_path):
                # TODO catch InvalidAssetError instead of all exceptions
                try:
                    asset = HdlSlot(discovery_path + '/' + _dir)
                    self.append_discovered_asset(asset)
                    # TODO move from self.hdl_cards to generic self.assets
                    # self.assets.extend(asset)
                except InvalidAssetError:
                    pass

    def discover_hdl_cards(self):
        discovery_path = self.abs_path + '/hdl/cards/specs'
        if os.path.isdir(discovery_path):
            for _dir in AssetBase.listdir_assets(discovery_path):
                # TODO catch InvalidAssetError instead of all exceptions
                try:
                    asset = HdlCard(discovery_path + '/' + _dir)
                    self.append_discovered_asset(asset)
                    # TODO move from self.hdl_cards to generic self.assets
                    # self.assets.extend(asset)
                except InvalidAssetError:
                    pass

    def discover_hdl_platforms(self):
        # TODO check if there is an allowlist, and if so, pass to below call
        self.discover_dir_assets('hdl/platforms')
        # TODO move from self.hdl_platforms to generic self.assets
        # self.hdl_platforms.extend(self.hdl_platforms)

    def discover_rcc_platforms(self):
        # TODO check if there is an allowlist, and if so, pass to below call
        self.discover_dir_assets('rcc/platforms')

    def get_assets_of_type(self, _type, authoring_model=''):
        assets = []
        if _type == 'application':
            assets.extend(self.applications)
        if _type == 'hdl assembly':
            assets.extend(self.hdl_assemblies)
        if _type == 'hdl card':
            assets.extend(self.hdl_cards)
        if _type == 'component':
            assets.extend(self.components)
            for component_library in self.component_libraries:
                assets.extend(component_library.components)
        if _type == 'hdl primitive':
            assets.extend(self.hdl_primitives)
        if _type == 'component library':
            assets.extend(self.component_libraries)
        if _type == 'hdl slot':
            assets.extend(self.hdl_slots)
        if _type == 'hdl platform':
            assets.extend(self.hdl_platforms)
        if _type == 'rcc platform':
            assets.extend(self.rcc_platforms)
        if _type == 'project':
            assets.extend([self])
        for component_library in self.component_libraries:
            if _type.startswith('worker'):
                for worker in component_library.workers:
                    if (cli_dict['authoringmodel'] == '') or \
                       (cli_dict['authoringmodel'] == 'hdl'):
                        assets.append(worker)
                    if (cli_dict['authoringmodel'] == '') or \
                       (cli_dict['authoringmodel'] == 'rcc'):
                        assets.append(worker)
            if _type.startswith('test'):
                assets.extend(component_library.tests)
        return assets

    def get_types_from_cli_dict(self, cli_dict):
        """ get list of types whose entries will each equal one of the values
            returned by an asset class's get_type() """
        types = []
        if cli_dict['noun'].startswith('application'):
            types.append('application')
        if cli_dict['noun'].startswith('assembl'):
            types.append('hdl assembly')
        if cli_dict['noun'].startswith('card'):
            types.append('hdl card')
        if cli_dict['noun'].startswith('component'):
            types.append('component')
        if cli_dict['noun'].startswith('librar'):
            types.append('hdl primitive')
            types.append('component library')
        if cli_dict['noun'].startswith('slot'):
            types.append('hdl slot')
        if cli_dict['noun'].startswith('platform'):
            if (cli_dict['authoringmodel'] == '') or \
               (cli_dict['authoringmodel'] == 'hdl'):
                types.append('hdl platform')
            if (cli_dict['authoringmodel'] == '') or \
               (cli_dict['authoringmodel'] == 'rcc'):
                types.append('rcc platform')
        if cli_dict['noun'].startswith('project'):
            types.append('project')
        for component_library in self.component_libraries:
            if cli_dict['noun'].startswith('worker'):
                for worker in component_library.workers:
                    if (cli_dict['authoringmodel'] == '') or \
                       (cli_dict['authoringmodel'] == 'hdl'):
                        types.append('hdl worker')
                    if (cli_dict['authoringmodel'] == '') or \
                       (cli_dict['authoringmodel'] == 'rcc'):
                        types.append('rcc worker')
            if cli_dict['noun'].startswith('test'):
                types.append('test')
        return types

    def show(self, _dir, cli_dict, json_dict={}):
        if cli_dict['globalscope']:
            Logger().warn('--global-scope does not change the behavior, see man ocpidev2-show')
        first = True
        for _type in self.get_types_from_cli_dict(cli_dict):
            assets = []
            for asset in self.get_assets_of_type(_type):
                if (cli_dict['name'] is None) or \
                   (cli_dict['name'] == asset.name):
                    if (_dir == '') or (_dir in asset.abs_path):
                        pid = str(self.get_package_id())
                        if (_type == 'component') or (_type.endswith('worker')):
                            for component_library in self.component_libraries:
                                if (asset in component_library.components) or (asset in component_library.workers):
                                    pid = component_library.get_package_id(pid)
                                    break
                        pid_and_name = pid
                        if not cli_dict['noun'].startswith('project'):
                            pid_and_name += '.' + asset.name
                        msg = ('' if first else ' ') + pid_and_name
                        if cli_dict['verbose'] or cli_dict['table']:
                            msg += ' '
                            for idx in range(60-len(msg)):
                                msg += ' '
                            msg += asset.abs_path
                        if cli_dict['json']:
                            json_dict[pid_and_name] = {"package_id": pid, "directory": asset.get_dir_abs_path()}
                        else:
                            print(msg, end=('' if cli_dict['simple'] else '\n'))
                        first = False
        return json_dict


def test_Project(ret):
    # ret = test_GNUMakefile(ret)
    ret = test_ComponentLibrary(ret)
    # ret = test_Project_discover_component_libraries(ret)
    return ret


def test_Project_discover_component_libraries(ret):
    """ Test all possible combinations of component libraries and
        "sub-"component libraries therein including:
        all possible parents from CDG section 14.2.3 """
    passed = True
    fs = TemporaryFilesystem()
    project_abs_path = fs.abs_path + '/' + 'project'
    os.system('mkdir -p %s' % project_abs_path)
    libs_to_test = 7
    element = [0, 1]
    libraries_product = itertools.product(element, repeat=libs_to_test)
    for libraries in libraries_product:
        lib_dict = {
            "components": libraries[0],
            "hdl/adapters": libraries[1],
            "hdl/cards": libraries[2],
            "hdl/devices": libraries[3],
            "hdl/platforms": libraries[4],
            "components/clib": libraries[5],
            "hdl/platforms/plat/devices": libraries[6]
        }
        # TODO: Break this out into separate function
        # Create Project Component Library Directories
        num_expected_libs = 0
        components_parent = False
        platforms_parent = False
        for lib_key, lib_value in lib_dict.items():
            if '/' in lib_key:
                library_xml = lib_key.split('/')[-1]
            else:
                library_xml = lib_key
            if lib_value:
                if lib_key == 'components':
                    components_parent = True
                    num_expected_libs += 1
                    os.system('mkdir -p %s/%s' % (project_abs_path, lib_key))
                elif lib_key == 'components/clib':
                    if components_parent:
                        num_expected_libs += 1
                    else:
                        num_expected_libs += 2
                    os.system('mkdir -p %s/%s' % (project_abs_path, lib_key))
                elif lib_key == 'hdl/platforms':
                    platforms_parent = True
                    num_expected_libs += 1
                    os.system('mkdir -p %s/%s' % (project_abs_path, lib_key))
                elif lib_key == 'hdl/platforms/plat/devices':
                    if platforms_parent:
                        num_expected_libs += 1
                    else:
                        num_expected_libs += 2
                    os.system('mkdir -p %s/%s' % (project_abs_path, lib_key))
                    # Create required <platform>/<platform>.xml with
                    # <HdlPlatform> XML root-tag
                    platform_xml = project_abs_path + '/'
                    platform_xml += 'hdl/platforms/plat/plat.xml'
                    os.system('touch %s' % platform_xml)
                    platform_xml_file = open(platform_xml, 'w')
                    platform_xml_file.write('<HdlPlatform/>\n')
                    platform_xml_file.close()
                    # os.system('cat ' + platform_xml)
                else:
                    num_expected_libs += 1
                    os.system('mkdir -p %s/%s' % (project_abs_path, lib_key))
            project_xml = open(project_abs_path + '/' + 'Project.xml', 'w')
            project_xml.write(
                    '<Project PackagePrefix=\'ocpi\' PackageName=\'proj\'/>\n')
            project_xml.close()
            uut = Project(project_abs_path, False)
            uut.discover()
            if num_expected_libs != len(uut.component_libraries):
                passed = False
        os.system('rm -rf %s/*' % project_abs_path)
    os.system('mkdir -p %s' % project_abs_path)
    for ext in ['hdl', 'rcc', 'ocl', 'test']:
        lib_path = '%s/components/foo.%s' % (project_abs_path, ext)
        os.system('mkdir -p ' + lib_path)
        if ext != 'test':
            ff = open(lib_path + '/foo.xml', 'w')
            ff.write('<' + ext + 'Worker/>\n')
            ff.close()
    uut = Project(project_abs_path)
    uut.discover()
    if len(uut.component_libraries) == 1:
        if uut.component_libraries[0].name != 'components':
            passed = False
    else:
        passed = False
    log_pass_fail('testing Project discover_component_libraries()', passed)
    if passed is False:
        ret = False
    return ret
