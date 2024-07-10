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
from _opencpi.assets.primitive2 import HdlLibrary
from _opencpi.assets.assembly2 import HdlAssembly
from _opencpi.assets.platform2 import HdlCard, HdlPlatform


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
            self.discover_hdl_cards()
            self.discover_hdl_platforms()
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
                # try:
                #     ComponentLibraries(dir_abs_path)
                #     is_libs = True
                # except InvalidAssetError as err:
                #     pass
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
        self.hdl_platforms.extend(self.hdl_platforms)

    def get_built_in_hdl_libraries(self):
        """ HDG section 5 "The built-in ocpi.core project includes several HDL
            primitive libraries, and some are always available for use by all
            workers" - here are the implied "some" """
        # these are intentionally in build dependency order
        tmp = ['bsv', 'fixed_float', 'ocpi', 'util', 'protocol', 'cdc']
        return tmp + ['platform', 'sdp', 'axi']

    def get_hdl_primitive_dependent_libraries(self, hdl_primitive=None):
        ret = []
        # 1. built-in (core) libraries (every project except ocpi.core)
        if str(self.get_package_id()) != 'ocpi.core':
            ret = self.get_built_in_hdl_libraries()
        # 2. project's own libraries
        if len(self.hdl_libraries) > 0:
            if str(self.get_package_id()) != 'ocpi.core':
                for lib in self.hdl_libraries:
                    ret.append(lib)
        # 3. library's dependent libraries
        if len(hdl_primitive.attrs['Libraries']) > 0:
            for lib in hdl_primitive.attrs['Libraries']:
                # split necessary because some Libraries are specified w/
                # package id, e.g., ocpi.core.bsv
                ret.append(lib.split('.')[-1])
        return ret

    def get_hdl_worker_dependent_libraries(self, comp_library, worker):
        ret = []
        if worker.authoring_model == 'hdl':
            ret.extend(self.get_built_in_hdl_libraries())
        # TODO investigate whether HdlLibraries is even allowed?
        for lib in comp_library.attrs['HdlLibraries']:
            ret.append(lib)
        for lib in comp_library.attrs['Libraries']:
            ret.append(lib)
        for lib in worker.attrs['Libraries']:
            ret.append(lib)
        return ret

    def get_hdl_worker_dependent_workers(self, project_registry, worker,
                                         hdl_platform):
        ret = []
        if worker.authoring_model == 'hdl':
            for project in project_registry.projects:
                for comp_library in project.component_libraries:
                    for potential_subdevice in comp_library.workers:
                        for support in potential_subdevice.supports:
                            if support == worker.name:
                                ret.append(potential_subdevice)
        if worker.name == hdl_platform:
            # TODO retrieve from registry, don't re-construct HdlPlatform
            _hdl_platform = HdlPlatform(worker.get_dir_abs_path())
            for cfg in _hdl_platform.configurations.values():
                for dev in cfg.devices:
                    _worker = None
                    project = project_registry.get_worker_project(dev.name)
                    for clib in project.component_libraries:
                        for device in clib.workers:
                            if device.name == dev.name:
                                ret.append(device)
                                break
        return ret

    def get_hdl_assembly_dependent_workers(
            self, project_registry, hdl_assembly, hdl_platform):
        ret = []
        for instance in hdl_assembly.instances:
            ret.append(instance.worker)
        # TODO optimize the below 2 lines per container requirements
        ret += project_registry.get_core_project_assets('hdl adapters')
        ret += project_registry.get_core_project_assets('hdl devices')
        ret.append(hdl_platform)
        for container in hdl_assembly.containers:
            # tmp = (container.platform == hdl_platform)
            # tmp = tmp or (hdl_platform in container.only_platforms)
            # if tmp and (hdl_platform not in container.exclude_platforms):
            for devname, dev in container.devices.items():
                # use the card or platform to disambiguate zero-based ordinal
                # described in PDG section 5.4.4.4
                for project in project_registry.projects:
                    search_list = None
                    if dev.card is None:
                        search_list = project.hdl_platforms
                    else:
                        search_list = project.hdl_cards
                    for entry in search_list:
                        for key, val in entry.devices.items():
                            if key == devname:
                                ret.append(val)
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
