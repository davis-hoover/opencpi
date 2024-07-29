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


""" This file connects the collection of projects above with all possible
    project constituents (Component, ComponentLibrary, Worker, HdlAssembly,
    HdlPlatform, etc) below. interfaces with projects and not individual asset
    classes. """


import os
import hashlib
import itertools
from _opencpi.assets.abstract2 import *
# here we interface with all the typical asset types
from _opencpi.assets.abstract2 import AssetBase
from _opencpi.assets.component2 import Component, Protocol
from _opencpi.assets.worker2 import Worker
from _opencpi.assets.application2 import Application, ApplicationsDirectory
from _opencpi.assets.library2 import SpecsDirectory
from _opencpi.assets.library2 import ComponentLibrary
from _opencpi.assets.library2 import ComponentLibrariesDirectory
from _opencpi.assets.library2 import test_ComponentLibrary
from _opencpi.assets.primitive2 import HdlLibrary, HdlCore
from _opencpi.assets.assembly2 import HdlAssembly, test_HdlAssembly
from _opencpi.assets.platform2 import HdlSlot, HdlCard
from _opencpi.assets.platform2 import HdlPlatform, RccPlatform
from _opencpi.assets.platform2 import test_HdlPlatform, test_HdlCard
from _opencpi.assets.test2 import Test


proj_exports_template = """
# This file specifies aspects of this project that are made available to users,
# by adding or subtracting from what is automatically exported based on the
# documented rules.
# Lines starting with + add to the exports
# Lines starting with - subtract from the exports
all

\n\n\n"""

proj_git_ignore_template = """
# Lines starting with '#' are considered comments.
# Ignore (generated) html files,
#*.html
# except foo.html which is maintained by hand.
#!foo.html
# Ignore objects and archives.
*.rpm
*.obj
*.so
*~
*.o
target-*/
*.deps
gen/
*.old
*.hold
*.orig
*.log
lib/
#Texmaker artifacts
*.aux
*.synctex.gz
*.out
**/doc*/*.pdf
**/doc*/*.toc
**/doc*/*.lof
**/doc*/*.lot
run/
exports/
imports
*.pyc
simulations/
\n\n"""

proj_git_attributes_template = """
*.ngc -diff
*.edf -diff
*.bit -diff
\n\n"""

proj_rst_template = """
.. {{asset.name}} top level project documentation


{{asset.name|capitalize}}
===============
Skeleton outline: Description of project.

.. toctree::
   :maxdepth: 2

   components/components
   hdl/primitives/primitives
   specs/specs
\n"""

comp_example_app_rst_template = """<?xml version="1.0"?>
<Application Done='file_write'>
  <Instance Component='ocpi.core.file_read' Connect='{{asset.name}}'>
    <Ptoperty Name='filename' Value='input.bin'/>
  </Instance>
  <Instance Component='{{extra}}.{{asset.name}}' Connect='file_write'>
  </Instance>
  <Instance Component='ocpi.core.file_write'>
    <Ptoperty Name='filename' Value='output.bin'/>
  </Instance>
</Application>
"""  # nopep8


class Project(AssetBase, ComponentLibraryProjectBase,
              ComponentLibraryWorkerProjectAssemblyBase, SpecsDirectory):
    """ Component Development Guide section 14 """

    def __init__(self, dir_abs_path, cli_dict=None):
        self.root_tags = ['Project']
        if cli_dict is None:
            if not os.path.exists(dir_abs_path + '/Project.xml'):
                if not os.path.exists(dir_abs_path + '/Project.mk'):
                    msg = 'neither Project.mk or Project.xml exists'
                    raise InvalidAssetError(msg)
        AssetBase.__init__(self, dir_abs_path, cli_dict, bad_name_action=0)
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

    @staticmethod
    def is_worker(noun):
        worker_strs = ['worker', 'device', 'adapter']
        return any([noun.startswith(_str) for _str in worker_strs])

    @staticmethod
    def is_hdl(noun):
        hdl_strs = ['adapter', 'assembl', 'card', 'device', 'librar',
                    'primitive', 'platform', 'slot', 'target', 'worker']
        return any([noun.startswith(_str) for _str in hdl_strs])

    @staticmethod
    def is_rcc(noun):
        rcc_strs = ['worker', 'target', 'platform']
        return any([noun.startswith(_str) for _str in rcc_strs])

    @staticmethod
    def get_asset_for_create(noun, authoring_model=''):
        asset = None
        dummy_dict = {}  # TODO remove this mess
        dummy_dict['component'] = ''
        dummy_dict['componentlibrary'] = ''
        dummy_dict['depends'] = ''
        dummy_dict['excludeplatform'] = []
        dummy_dict['excludetarget'] = []
        dummy_dict['includedir'] = ''
        dummy_dict['language'] = 'vhdl'
        dummy_dict['libraries'] = ''
        dummy_dict['nocontrol'] = False
        dummy_dict['onlytarget'] = []
        dummy_dict['onlyplatform'] = []
        dummy_dict['packageid'] = ''
        dummy_dict['packagename'] = ''
        dummy_dict['packageprefix'] = ''
        dummy_dict['primitivelibrary'] = ''
        dummy_dict['type'] = 'foo'
        dummy_dict['usehdlfileio'] = ''
        dummy_dict['version'] = 2
        dummy_dict['xmlinclude'] = ''
        if noun == 'application':
            asset = Application('', dummy_dict)
        if noun == 'assembly':
            asset = HdlAssembly('', dummy_dict)
        if noun == 'card':
            asset = HdlCard('', dummy_dict)
        if noun == 'component':
            asset = Component('', dummy_dict)
        if noun == 'library':
            asset = ComponentLibrary('', dummy_dict)
        if noun == 'test':
            asset = Test('', dummy_dict)
        if noun == 'project':
            asset = Project('', dummy_dict)
        if noun == 'protocol':
            asset = Protocol('', dummy_dict)
        if noun == 'primitive':
            asset = HdlLibrary('', dummy_dict)
        if noun == 'platform':
            asset = HdlPlatform('', dummy_dict)
        if Project.is_worker(noun):
            asset = Worker('', dummy_dict)
        return asset

    def get_type(self):
        return 'project'

    def get_attr_infos(self):
        ret = []
        ret.extend(ComponentLibraryProjectBase.get_attr_infos(self))
        tmp = ComponentLibraryWorkerProjectAssemblyBase.get_attr_infos(self)
        ret.extend(tmp)
        # Attributes provided (partially) in CDG 10.1 Table 7
        ret.append(AttributeInfo('ProjectDependencies',
                   is_list=True, cli=('-D', '--depends')))
        ret.append(AttributeInfo('PackagePrefix',
                   cli=('-F', '--package-prefix')))
        ret.append(AttributeInfo('PackageID',
                   cli=('-K', '--package-id')))
        ret.append(AttributeInfo('PackageName',
                   cli=('-N', '--package-name')))
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

    def get_component_library_package_id(self, component_library):
        ret = self.get_package_id()
        abs_path_split = component_library.abs_path.split('/')
        if len(abs_path_split) >= 3:
            if abs_path_split[-3] == 'platforms':
                ret += '.platforms.' + abs_path_split[-2]
        # use e.g. ocpi.core instead of ocpi.core.components (same as OAS)
        if component_library.name != 'components':
            ret += '.' + component_library.name
        return ret

    def get_list_of_component_strings_by_name(self, name):
        """ get list of package id-qualified name per component found in this
            project, or an empty list if not found """
        ret = []
        project_pid = self.get_package_id()
        for component in self.components:
            if name == component.name:
                ret.append(project_pid + '.' + component.name)
        for comp_library in self.component_libraries:
            for component in comp_library.components:
                if name == component.name:
                    pid = self.get_component_library_package_id(comp_library)
                    ret.append(pid + '.' + component.name)
        return ret

    def get_worker_by_name(self, name, authoring_model=''):
        ret = None
        for component_library in self.component_libraries:
            for worker in component_library.workers:
                if worker.name == name:
                    am = authoring_model
                    if (am == '') or (worker.authoring_model == am):
                        ret = worker
        for hdl_platform in self.hdl_platforms:
            if hdl_platform.worker.name == name:
                am = authoring_model
                if (am == '') or (hdl_platform.worker.authoring_model == am):
                    ret = hdl_platform.worker
                    break
        return ret

    def get_assets_within(self, abs_path):
        """ get list of assets whose abs_path is within the abs_path """
        ret = []
        buildables = [self.applications, self.hdl_primitives,
                      self.hdl_assemblies]
        for component_library in self.component_libraries:
            buildables.append(component_library.workers)
        for asset_list in buildables:
            for asset in asset_list:
                if (abs_path + '/') in (asset.abs_path + '/'):
                    ret.append(asset)
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

    def get_templates(self):
        templates = {}
        templates['Project.exports'] = proj_exports_template
        templates['.gitignore'] = proj_git_ignore_template
        templates['.gitattributes'] = proj_git_attributes_template
        templates['Project.rst'] = proj_rst_template
        templates['Project.xml'] = g_asset_template
        return templates

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

    def discover(self, do_component_libraries=True, do_hdl_primitives=True,
                 do_hdl_assemblies=True):
        # start of bullets at top of CDG section 14
        if do_component_libraries:
            tmp = self.abs_path.split('/')[-1]
            Logger().info('discovering project ' + tmp)
            SpecsDirectory.discover(self)
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

    def append_discovered_asset(self, asset):
        if asset.get_type() == 'component':
            self.components.append(asset)
        if asset.get_type() == 'component library':
            self.component_libraries.append(asset)
        if asset.get_type() == 'application':
            self.applications.append(asset)
        if asset.get_type() == 'hdl primitive':
            self.hdl_primitives.append(asset)
        if asset.get_type() == 'hdl primitive core':
            self.hdl_primitives.append(asset)
        if asset.get_type() == 'hdl assembly':
            self.hdl_assemblies.append(asset)
        if asset.get_type() == 'hdl slot':
            self.hdl_slots.append(asset)
        if asset.get_type() == 'hdl card':
            self.hdl_cards.append(asset)
        if asset.get_type() == 'hdl platform':
            self.hdl_platforms.append(asset)
        if asset.get_type() == 'protocol':
            self.protocols.append(asset)
        if asset.get_type() == 'rcc platform':
            self.rcc_platforms.append(asset)
        _type = asset.get_type()
        if (_type == 'hdl worker') or (_type == 'rcc worker'):
            self.workers.append(asset)
        if asset.get_type() == 'test':
            self.tests.append(asset)
        Logger().log(9, 'discovered ' + _type + ' ' + asset.abs_path)

    def get_potential_asset_dir_abs_paths(self, parent):
        ret = []
        discovery_path = self.abs_path + '/' + parent
        if os.path.isdir(discovery_path):
            for _dir in AssetBase.listdir_assets(discovery_path):
                dir_abs_path = discovery_path + '/' + _dir
                allowable_dir = (_dir != 'specs') and (_dir != 'gen')
                if os.path.isdir(dir_abs_path) and allowable_dir:
                    ret.append(dir_abs_path)
        return ret

    def discover_dir_assets(self, parent, allowlist=None, platform=False):
        for dir_abs_path in self.get_potential_asset_dir_abs_paths(parent):
            try:
                assets = []
                if parent == 'hdl/primitives':
                    assets.append(HdlCore(dir_abs_path))
                for asset in assets:
                    if allowlist is not None:
                        # TODO is this pre-2.0???
                        allowlist = [name.split('.')[0] for name in allowlist]
                    if (allowlist is None) or (asset.name in allowlist):
                        self.append_discovered_asset(asset)
            except InvalidAssetError as err:
                if (parent != 'applications') and \
                   (not dir_abs_path.endswith('.test')):
                    if parent != 'hdl/primitives':
                        Logger().warn('skipping ' + str(err))
                pass
        for dir_abs_path in self.get_potential_asset_dir_abs_paths(parent):
            try:
                assets = []
                tmp = dir_abs_path
                if parent == 'rcc/platforms':
                    assets.append(RccPlatform(dir_abs_path))
                elif parent == 'hdl/platforms':
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
                    else:
                        tmp = dir_abs_path + '/' + name + '.xml'
                        assets.append(Worker(tmp))
                elif tmp.endswith('.test'):
                    assets.append(Test(dir_abs_path))
                for asset in assets:
                    if allowlist is not None:
                        # TODO is this pre-2.0???
                        allowlist = [name.split('.')[0] for name in allowlist]
                    if (allowlist is None) or (asset.name in allowlist):
                        self.append_discovered_asset(asset)
            except InvalidAssetError as err:
                if (parent != 'applications') and \
                   (not dir_abs_path.endswith('.test')):
                    Logger().warn('skipping ' + str(err))
                pass

    def raise_if_devices_name_collision(self, cli_dict, _dir):
        """ Checks to see if more than one 'devices' Component Library name
            exists """
        if 'devices' in (cli_dict.get('hdllibrary'),
                         cli_dict.get('library'),
                         cli_dict.get('platform')):
            devices_paths = [comp_lib.abs_path for comp_lib in
                             self.component_libraries if
                             comp_lib.abs_path.endswith('/devices')]
            devices_in_path = [dev_path for dev_path in devices_paths if
                               _dir + '/' in dev_path]
            if len(devices_in_path) > 1:
                msg = 'Path: \'' + _dir + '\' contains more than'
                msg += ' one \'devices\' component libraries: '
                msg += ', '.join(map(str, list(devices_in_path))) + '. '
                msg += 'Use \'-d\' instead.'
                raise Exception(msg)

    def raise_if_not_in_hdl_cards_specs(self, cli_dict, _dir):
        if _dir != self.get_dir_abs_path() + '/hdl/cards/specs':
            msg = cli_dict['noun'] + ' \'' + cli_dict['name']
            msg += '\' can not exist within ' + _dir
            msg += ' (' + cli_dict['noun'] + ' can only be created within '
            msg += '<project>/hdl/cards/specs, set -d, or the working '
            msg += 'directory, to <project>/hdl/cards/specs)'
            raise Exception(msg)

    def get_and_validate_cli_dir_abs_path(self, cli_dict, _dir,
                                          libs_to_consider, dict_key):
        """ considers the combination of _dir (which is already verified to
            exist in self (this project) and cli_dict[dict_key], where dict_key
            is one of 'library', 'hdllibrary', or 'platform', and retrieves the
            absolute path to the directory of the component library that was
            requested, throwing an exception if _dir/cli_dict request is
            invalid for any reason """
        lib_valid = False
        for lib in libs_to_consider:
            if (_dir + '/') in (lib.get_dir_abs_path() + '/'):
                if cli_dict[dict_key] == lib.name:
                    lib_valid = True
                    lib_path = lib.get_dir_abs_path()
                    break
        if not lib_valid:
            msg = 'The ' + dict_key.replace('hdl', 'hdl ') + ' \''
            msg += cli_dict[dict_key] + '\' does not exist in the directory: '
            msg += '\'' + _dir + '\', which is in the project ' + self.name
            msg += ', which only contains the ' + dict_key + ' entries: '
            first = True
            for lib in libs_to_consider:
                if not first:
                    msg += ', '
                first = False
                msg += '\'' + str(lib.name) + '\''
            raise Exception(msg)
        return lib_path

    def get_component_library_dir_abs_path_from_cli(self, cli_dict, _dir):
        if cli_dict.get('library'):
            clibs = self.component_libraries
            dd = self.get_and_validate_cli_dir_abs_path(cli_dict, _dir,
                                                        clibs, 'library')
            dir_abs_path = dd
        elif cli_dict.get('hdllibrary'):
            hdl_libs = []
            for lib in self.component_libraries:
                if (self.get_dir_abs_path() + '/hdl/') in \
                   (lib.get_dir_abs_path() + '/'):
                    hdl_libs.append(lib)
            dd = self.get_and_validate_cli_dir_abs_path(cli_dict, _dir,
                                                        hdl_libs, 'hdllibrary')
            dir_abs_path = dd
        elif cli_dict.get('platform'):
            pf_libs = []
            found = False
            for hdl_platform in self.hdl_platforms:
                if hdl_platform.name == cli_dict['platform']:
                    for lib in self.component_libraries:
                        if (hdl_platform.get_dir_abs_path() + '/devices') == \
                           (lib.get_dir_abs_path()):
                            dir_abs_path = lib.get_dir_abs_path()
                            found = True
            if not found:
                msg = 'the component library \'devices\' does not exist in '
                msg += 'the \'' + cli_dict['platform'] + '\' hdl platform'
                raise Exception(msg)
        return dir_abs_path

    def get_component_library_type_object_from_cli(self, cli_dict, _dir):
        """ returns a protocol, component, worker, or test object as requested
            from CLI """
        self.raise_if_devices_name_collision(cli_dict, _dir)
        if cli_dict.get('project'):
            dir_abs_path = self.get_dir_abs_path() + '/specs'
        elif cli_dict.get('library') or cli_dict.get('hdllibrary') or \
                cli_dict.get('platform'):
            dir_abs_path = self.get_component_library_dir_abs_path_from_cli(
                cli_dict, _dir)
            if cli_dict['noun'].startswith('protocol'):
                dir_abs_path += '/specs'
        else:
            valid_dirs = []
            if cli_dict['noun'].startswith('protocol') or \
               cli_dict['noun'].startswith('component'):
                # for the individial prot/comp xml files in project
                # specs directory
                valid_dirs.append(self.get_dir_abs_path() + '/specs')
                # for the individial prot/comp xml files in project/complib
                # specs directory
                valid_dirs.extend(comp_lib.get_dir_abs_path() + '/specs' for
                                  comp_lib in self.component_libraries)
            if not cli_dict['noun'].startswith('protocol'):
                # all worker/test/.comp directories are allowed directly
                # within complib directory
                valid_dirs.extend(comp_lib.get_dir_abs_path() for
                                  comp_lib in self.component_libraries)
            if (_dir + '/') not in [vd + '/' for vd in valid_dirs]:
                msg = cli_dict['noun'] + ' \'' + cli_dict['name']
                msg += '\' can not exist within ' + _dir
                msg += ' (' + cli_dict['noun'] + ' can only be created within '
                msg += '<project>/specs or a component library '
                if cli_dict['noun'].startswith('protocol'):
                    msg += 'specs '
                msg += 'directory, set -d, or the working directory, to '
                if cli_dict['noun'].startswith('protocol'):
                    msg += '<project>/specs or a component library specs '
                else:
                    msg += '<project>/specs or a component library <library>'
                msg += ' directory)'
                raise Exception(msg)
            dir_abs_path = _dir
        if cli_dict['noun'].startswith('component'):
            if dir_abs_path.endswith('specs'):
                Logger().warn('for component library creation, the '
                              'working directory (or, if specified, '
                              'the -d option) is recommended to be '
                              'the component library location '
                              '<library>, and not <library>/specs')
                xml_abs_path = dir_abs_path + '/' + cli_dict['name'] + \
                    '-comp.xml'
            else:
                dir_abs_path += '/' + cli_dict['name'] + '.comp'
                xml_abs_path = dir_abs_path + '/' + cli_dict['name'] + \
                    '-comp.xml'
            ret = Component(xml_abs_path, cli_dict)
        if cli_dict['noun'].startswith('protocol'):
            dir_abs_path += '/' + cli_dict['name']
            xml_abs_path = dir_abs_path + '-prot.xml'
            ret = Protocol(xml_abs_path, cli_dict)
        if cli_dict['noun'].startswith('worker'):
            dir_abs_path += '/' + cli_dict['name']
            dir_abs_path += '.' + cli_dict['authoringmodel']
            xml_abs_path = dir_abs_path + '/' + cli_dict['name'] + '.xml'
            ret = Worker(xml_abs_path, cli_dict)
        if cli_dict['noun'].startswith('test'):
            dir_abs_path += '/' + cli_dict['name'] + '.test'
            ret = Test(dir_abs_path, cli_dict)
        return ret

    def get_adapter_object_from_cli(self, cli_dict, _dir):
        if _dir != self.get_dir_abs_path() + '/hdl/adapters':
            msg = cli_dict['noun'] + ' \'' + cli_dict['name']
            msg += '\' can not exist within ' + _dir
            msg += ' (' + cli_dict['noun'] + ' can only be created within '
            msg += '<project>/hdl/adapter, set -d, or the working directory, '
            msg += 'to <project>/hdl/adapters)'
            raise Exception(msg)
        xml_abs_path = _dir + '/' + cli_dict['name'] + '.hdl/'
        xml_abs_path += cli_dict['name'] + '.xml'
        return Worker(xml_abs_path, cli_dict)

    def get_application_object_from_cli(self, cli_dict, _dir):
        abs_path = self.get_dir_abs_path() + '/applications/'
        if cli_dict['xmlapp']:
            abs_path += cli_dict['name'] + '.xml'  # xml type
        else:
            if _dir != self.get_dir_abs_path() + '/applications':
                msg = cli_dict['noun'] + ' \'' + cli_dict['name']
                msg += '\' can not exist within ' + _dir
                msg += ' (' + cli_dict['noun'] + ' can only be created '
                msg += 'within <project>/applications, set -d, or the '
                msg += 'working directory, to <project>/applications)'
                raise Exception(msg)
            abs_path += cli_dict['name']  # dir type
        return Application(abs_path, cli_dict)

    def get_assembly_object_from_cli(self, cli_dict, _dir):
        if _dir != self.get_dir_abs_path() + '/hdl/assemblies':
            msg = cli_dict['noun'] + ' \'' + cli_dict['name']
            msg += '\' can not exist within ' + _dir
            msg += ' (' + cli_dict['noun'] + ' can only be created within '
            msg += '<project>/hdl/assemblies, set -d, or the working '
            msg += 'directory, to <project>/hdl/assemblies)'
            raise Exception(msg)
        dir_abs_path = self.get_dir_abs_path() + '/hdl/assemblies/' + \
            cli_dict['name']
        return HdlAssembly(dir_abs_path, cli_dict)

    def get_card_object_from_cli(self, cli_dict, _dir):
        self.raise_if_not_in_hdl_cards_specs(cli_dict, _dir)
        xml_abs_path = self.get_dir_abs_path() + '/hdl/cards/specs/'
        xml_abs_path += cli_dict['name'] + '.xml'
        return HdlCard(xml_abs_path, cli_dict)

    def get_component_object_from_cli(self, cli_dict, _dir):
        return self.get_component_library_type_object_from_cli(cli_dict, _dir)

    def get_device_object_from_cli(self, cli_dict, _dir):
        found = False
        for component_library in self.component_libraries:
            if component_library.name in ['devices', 'cards']:
                if _dir == component_library.get_dir_abs_path():
                    found = True
                    break
        if not found:
            msg = cli_dict['noun'] + ' \'' + cli_dict['name']
            msg += '\' can not exist within ' + _dir
            msg += ' (must set the working directory, or '
            msg += '-d <dir>, to a devices or cards component <library> '
            msg += 'directory'
            raise Exception(msg)
        xml_abs_path = _dir + '/' + cli_dict['name'] + '.hdl/'
        xml_abs_path += cli_dict['name'] + '.xml'
        return Worker(xml_abs_path, cli_dict)

    def get_library_object_from_cli(self, cli_dict, _dir):
        dir_abs_path = _dir
        if cli_dict['name'] == 'components':
            dir_abs_path += '/' + cli_dict['name']
            is_existing_component_libraries = False
            try:
                ComponentLibrariesDirectory(dir_abs_path, None)
                is_existing_component_libraries = True
            except InvalidAssetError:
                pass
            if (is_existing_component_libraries) or \
               (dir_abs_path != self.get_dir_abs_path() + '/components'):
                msg = 'component library \'' + cli_dict['name']
                msg += '\' can not exist within ' + _dir
                if is_existing_component_libraries:
                    msg += ' (\'components\' directory already exists and is '
                    msg += 'not a component library - it already has a '
                    msg += 'components.xml with a Libraries root tag)'
                else:
                    msg += ' (\'components\' library can only be created '
                    msg += 'within the top level of a project, set -d, or the '
                    msg += 'working directory, to the top level of a project)'
                raise Exception(msg)
        elif cli_dict['name'] == 'devices':
            dir_abs_path = _dir + '/' + cli_dict['name']
            if _dir != (self.get_dir_abs_path() + '/hdl'):
                found = False
                for hdl_platform in self.hdl_platforms:
                    if _dir == hdl_platform.get_dir_abs_path():
                        found = True
                if not found:
                    msg = 'component library ' + cli_dict['name']
                    msg += ' can not exist within ' + _dir
                    msg += ' (\'' + cli_dict['name'] + '\' library can only '
                    msg += 'exist within <project>/hdl directory or '
                    msg += '<project>/hdl/platforms/<platform> directory, set '
                    msg += '-d, or the working directory, to <project>/hdl or '
                    msg += '<project>/hdl/platforms/<platform>)'
                    raise Exception(msg)
        elif (cli_dict['name'] == 'adapters') or (cli_dict['name'] == 'cards'):
            dir_abs_path = self.get_dir_abs_path() + '/hdl/' + cli_dict['name']
            if _dir != self.get_dir_abs_path() + '/hdl':
                msg = 'component library \'' + cli_dict['name']
                msg += '\' can not exist within ' + _dir
                msg += ' (\'' + cli_dict['name'] + '\' library can not exist '
                msg += 'within <project>/hdl directory, set -d, or the '
                msg += 'working directory, to <project>/hdl)'
                raise Exception(msg)
        else:
            dir_abs_path = _dir
            if dir_abs_path != self.get_dir_abs_path() + '/components':
                msg = 'component library ' + cli_dict['name']
                msg += ' can not exist within ' + _dir
                msg += ' (\'' + cli_dict['name'] + '\' library can not exist '
                msg += 'within <project>/components directory, set -d, or the '
                msg += 'working directory, to <project>/components)'
                raise Exception(msg)
            dir_abs_path += '/' + cli_dict['name']
        return ComponentLibrary(dir_abs_path, cli_dict)

    def get_platform_object_from_cli(self, cli_dict, _dir):
        if _dir != (self.get_dir_abs_path() + '/' +
                    cli_dict['authoringmodel'] + '/platforms'):
            msg = cli_dict['authoringmodel'] + ' ' + cli_dict['noun'] + ' '
            msg += cli_dict['name']
            msg += ' can not exist within ' + _dir
            msg += ' (must exist within <project>/hdl/platforms directory, '
            msg += 'set -d, or the working directory, to '
            msg += '<project>/hdl/platforms)'
            raise Exception(msg)
        if cli_dict['authoringmodel'] == 'hdl':
            dir_abs_path = self.get_dir_abs_path() + '/hdl/platforms/' + \
                           cli_dict['name']
            asset = HdlPlatform(dir_abs_path, cli_dict)
        if cli_dict['authoringmodel'] == 'rcc':
            dir_abs_path = self.get_dir_abs_path() + '/rcc/platforms/' + \
                           cli_dict['name']
            asset = RccPlatform(dir_abs_path, cli_dict)
        return asset

    def get_primitive_object_from_cli(self, cli_dict, _dir):
        if _dir != self.get_dir_abs_path() + '/hdl/primitives':
            msg = cli_dict['noun'] + ' ' + cli_dict['name']
            msg += ' can not exist within ' + _dir
            msg += ' (\'' + cli_dict['name'] + '\' can only exist '
            msg += 'within <project>/hdl/primitives directory, set -d, or the '
            msg += 'working directory, to <project>/hdl/primitives)'
            raise Exception(msg)
        dir_abs_path = self.get_dir_abs_path() + '/hdl/primitives/'
        dir_abs_path += cli_dict['name']
        if cli_dict['librarytype'] == 'core':
            asset = HdlCore(dir_abs_path, cli_dict)
        else:
            asset = HdlLibrary(dir_abs_path, cli_dict)
        return asset

    def get_protocol_object_from_cli(self, cli_dict, _dir):
        return self.get_component_library_type_object_from_cli(cli_dict, _dir)

    def get_slot_object_from_cli(self, cli_dict, _dir):
        self.raise_if_not_in_hdl_cards_specs(cli_dict, _dir)
        xml_abs_path = self.get_dir_abs_path() + '/hdl/cards/specs/'
        xml_abs_path += cli_dict['name'] + '.xml'
        return HdlSlot(xml_abs_path, cli_dict)

    def get_worker_object_from_cli(self, cli_dict, _dir):
        return self.get_component_library_type_object_from_cli(cli_dict, _dir)

    def get_test_object_from_cli(self, cli_dict, _dir):
        return self.get_component_library_type_object_from_cli(cli_dict, _dir)

    def handle_hdl_library(self, cli_dict, _dir):
        # TODO handle common args somwhere(e.g. --hdl-library --library)
        pass

    def get_asset_object_from_cli(self, cli_dict, _dir):
        """ _dir is THE directory within which to do the action corresponding
            to cli_dict['verb'] (do NOT use cli_dict['d']"""
        if cli_dict['noun'] == 'adapter':
            asset = self.get_adapter_object_from_cli(cli_dict, _dir)
        elif cli_dict['noun'] == 'application':
            asset = self.get_application_object_from_cli(cli_dict, _dir)
        elif cli_dict['noun'] == 'assembly':
            asset = self.get_assembly_object_from_cli(cli_dict, _dir)
        elif cli_dict['noun'] == 'card':
            asset = self.get_card_object_from_cli(cli_dict, _dir)
        elif cli_dict['noun'] == 'component':
            asset = self.get_component_object_from_cli(cli_dict, _dir)
        elif cli_dict['noun'] == 'device':
            asset = self.get_device_object_from_cli(cli_dict, _dir)
        elif cli_dict['noun'] == 'library':
            asset = self.get_library_object_from_cli(cli_dict, _dir)
        elif cli_dict['noun'] == 'platform':
            asset = self.get_platform_object_from_cli(cli_dict, _dir)
        elif cli_dict['noun'] == 'primitive':
            asset = self.get_primitive_object_from_cli(cli_dict, _dir)
        elif cli_dict['noun'] == 'protocol':
            asset = self.get_protocol_object_from_cli(cli_dict, _dir)
        elif cli_dict['noun'] == 'slot':
            asset = self.get_slot_object_from_cli(cli_dict, _dir)
        elif cli_dict['noun'] == 'test':
            asset = self.get_test_object_from_cli(cli_dict, _dir)
        elif cli_dict['noun'] == 'worker':
            asset = self.get_worker_object_from_cli(cli_dict, _dir)
        return asset

    def create_asset(self, cli_dict, _dir):
        dir_abs_path = _dir
        if cli_dict['noun'] == 'application':
            if not os.path.exists(self.get_dir_abs_path() + '/applications'):
                msg = 'performing \'' + cli_dict['verb']
                msg += '\' for an applications directory '
                msg = 'performing \'' + cli_dict['verb'] + '\' for an '
                msg += 'applications directory '
                Logger().log(3, msg + ' within directory ' +
                             self.get_dir_abs_path())
                ApplicationsDirectory(self.get_dir_abs_path() +
                                      '/applications', False,
                                      cli_dict).create()
        elif cli_dict['noun'] == 'library':
            if cli_dict['name'] == 'components':
                pass
            elif cli_dict['name'] == 'devices':
                pass
            elif (cli_dict['name'] == 'adapters') or \
                 (cli_dict['name'] == 'cards'):
                pass
            else:
                if not os.path.exists(dir_abs_path):
                    msg = 'performing \'' + cli_dict['verb'] + '\' for a '
                    msg += 'components directory '
                    Logger().log(3, msg + ' within directory ' +
                                 self.get_dir_abs_path())
                    dd = cli_dict
                    cld = ComponentLibrariesDirectory(dir_abs_path, dd)
                    cld.create()
        asset = self.get_asset_object_from_cli(cli_dict, _dir)
        if (cli_dict['noun'] == 'component') or \
           (cli_dict['noun'] == 'protocol'):
            if not os.path.exists(asset.get_dir_abs_path()):
                System('mkdir -p ' + asset.get_dir_abs_path())
        if os.path.exists(asset.abs_path):
            msg = cli_dict['noun'] + ' ' + cli_dict['name'] + ' already exists'
            msg += ' within directory '
            msg += asset.get_dir_abs_path().rsplit('/', 1)[0]
            raise Exception(msg)
        if (asset.get_type() == 'hdl worker') or \
           (asset.get_type() == 'rcc worker'):
            if (asset.version != 2):
                msg = 'default version of 0 is being used, but --version 2 is '
                msg += 'highly recommended'
                Logger().warn(msg)
        asset.create()
        if ('createtest' in cli_dict.keys()) and cli_dict['createtest']:
            test_dict = {'noun': 'test', 'name': asset.name,
                         'component': asset.name, 'usehdlfileio': False}
            self.get_test_object_from_cli(test_dict, _dir).create()
        if cli_dict['noun'] == 'component':
            pid = self.get_package_id()
            if _dir != (self.get_dir_abs_path() + '/specs'):
                if not cli_dict['project']:
                    found = False
                    for component_library in self.component_libraries:
                        if _dir == component_library.get_dir_abs_path():
                            cl = component_library
                            pid = self.get_component_library_package_id(cl)
            if not _dir.endswith('specs'):
                file_abs_path = asset.get_dir_abs_path() + '/'
                file_abs_path += 'example_app.xml'
                self.create_file(file_abs_path, comp_example_app_rst_template,
                                 asset, extra=pid)

    def delete_asset(self, cli_dict, _dir):
        self.get_asset_object_from_cli(cli_dict, _dir).delete()

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
                # components/<library>, exists (note hdl/platforms is not a
                # component library and therefore not added):
                #   - components/
                #   - hdl/devices/
                #   - hdl/cards/
                #   - hdl/adapters/
                if _dir != 'hdl/platforms':
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
                    ComponentLibrariesDirectory(dir_abs_path)
                    is_libs = True
                except InvalidAssetError as err:
                    pass
                asset = ComponentLibrary(dir_abs_path)
                if not is_libs:
                    self.append_discovered_asset(asset)
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

    @staticmethod
    def get_built_in_hdl_libraries():
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
        # TODO should some of this move to ComponentLibrary class?
        ret = []
        if worker.authoring_model == 'hdl':
            ret.extend(Project.get_built_in_hdl_libraries())
        # --- IMPORTANT --- BELOW LINE IS NOT MENTIONED IN DEV GUIDE BUT
        #                   EXISTS IN misc_comps/Library.mk
        for lib in comp_library.attrs['HdlLibraries']:
            ret.append(lib)
        for lib in comp_library.attrs['Libraries']:
            ret.append(lib)
        for lib in worker.attrs['Libraries']:
            ret.append(lib)
        return ret

    def get_assets_of_type(self, _type):
        assets = []
        if _type == 'application':
            assets.extend(self.applications)
        if _type == 'hdl assembly':
            assets.extend(self.hdl_assemblies)
        if _type == 'hdl card':
            assets.extend(self.hdl_cards)
        if _type == 'component':
            assets.extend(self.components)  # project specs directory
            for component_library in self.component_libraries:
                assets.extend(component_library.components)
        if _type == 'hdl primitive':
            for prim in self.hdl_primitives:
                # TODO change to 'hdl primitive library'
                if prim.get_type() == 'hdl primitive':
                    assets.append(prim)
        if _type == 'hdl primitive core':
            for prim in self.hdl_primitives:
                if prim.get_type() == 'hdl primitive core':
                    assets.append(prim)
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
        if _type == 'protocol':
            assets.extend(self.protocols)
        for component_library in self.component_libraries:
            if _type.endswith('worker'):
                assets.extend(component_library.workers)
            if _type == 'test':
                assets.extend(component_library.tests)
        if _type == 'hdl worker':
            for hdl_platform in self.hdl_platforms:
                assets.append(hdl_platform.worker)
        # TODO define HdlTarget, RccTarget class
        return assets

    def get_types_from_cli_dict(self, cli_dict):
        """ get list of types (asset classes) that correspond to cli_dict noun
            and authoring_model entries """
        types = []
        if cli_dict['noun'].startswith('adapter'):
            types.append('hdl worker')
        if cli_dict['noun'].startswith('application'):
            types.append('application')
        if cli_dict['noun'].startswith('assembl'):
            types.append('hdl assembly')
        if cli_dict['noun'].startswith('card'):
            types.append('hdl card')
        if cli_dict['noun'].startswith('component'):
            types.append('component')
        if cli_dict['noun'].startswith('device'):
            types.append('hdl worker')
        if cli_dict['noun'].startswith('librar'):
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
        if cli_dict['noun'].startswith('primitive'):
            if cli_dict['adjective'].startswith('core'):
                types.append('hdl primitive core')
            elif cli_dict['adjective'].startswith('librar'):
                types.append('hdl primitive')
            else:
                types.append('hdl primitive core')
                types.append('hdl primitive')
        if cli_dict['noun'].startswith('project'):
            types.append('project')
        if cli_dict['noun'].startswith('protocol'):
            types.append('protocol')
        if cli_dict['noun'].startswith('worker'):
            if cli_dict['authoringmodel'] != 'rcc':
                types.append('hdl worker')
            if cli_dict['authoringmodel'] != 'hdl':
                types.append('rcc worker')
        if cli_dict['noun'].startswith('test'):
            types.append('test')
        if cli_dict['noun'].startswith('target'):
            if (cli_dict['authoringmodel'] == '') or \
               (cli_dict['authoringmodel'] == 'hdl'):
                types.append('hdl platform')  # TODO fix
            if (cli_dict['authoringmodel'] == '') or \
               (cli_dict['authoringmodel'] == 'rcc'):
                types.append('rcc platform')
        return types

    def clean(self, _dir):
        os.system('rm -rf $(find ' + _dir + ' -type d -name gen)')
        os.system('rm -rf $(find ' + _dir + ' -type d -name lib)')
        os.system('rm -rf $(find ' + _dir + ' -type d -name run)')
        # below 4 lines account for corrupted imports/exports
        os.system('rm -rf $(find ' + _dir + ' -type f -name imports)')
        os.system('rm -rf $(find ' + _dir + ' -type f -name exports)')
        os.system('rm -rf $(find ' + _dir + ' -type d -name imports)')
        os.system('rm -rf $(find ' + _dir + ' -type d -name exports)')
        os.system('rm -rf $(find ' + _dir + ' -type l -name imports)')
        os.system('rm -rf $(find ' + _dir + ' -type l -name exports)')
        os.system('rm -rf $(find ' + _dir +
                  ' -type d -name config-\*)')  # nopep8
        os.system('rm -rf $(find ' + _dir + ' -type d -name simulations)')
        os.system('rm -rf $(find ' + _dir +
                  ' -type d -name target-\*)')  # nopep8
        os.system('rm -rf $(find ' + _dir +
                  ' -type d -name container-\*)')  # nopep8
        os.system('rm -rf $(find ' + _dir + ' -type f -name \'.*lock\')')
        os.system('rm -rf $(find ' + _dir + ' -type f -name \'.*build\')')
        os.system('rm -rf $(find ' + _dir + ' -type d -name artifacts)')


def test_Project(ret):
    # ret = test_GNUMakefile(ret)
    ret = test_ComponentLibrary(ret)
    # ret = test_Project_discover_component_libraries(ret)
    ret = test_HdlPlatform(ret)
    ret = test_HdlCard(ret)
    # ret = test_HdlAssemblyInstance(ret)
    ret = test_HdlAssembly(ret)
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
            'components': libraries[0],
            'hdl/adapters': libraries[1],
            'hdl/cards': libraries[2],
            'hdl/devices': libraries[3],
            'hdl/platforms': libraries[4],
            'components/clib': libraries[5],
            'hdl/platforms/plat/devices': libraries[6]
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


def test_ComponentLibrary_create(ret):
    passed = True
    fs = TemporaryFilesystem()
    cli_dict = 'empty'
    # Create a project
    project_path = fs.abs_path + '/foo'
    project = Project(project_path, False, None)
    project.create()
    test_name = 'test_ComponentLibrary_create: '
    for test in range(6):
        valid_libs = ['components', 'devices', 'adapters', 'cards',
                      'platforms']
        # Create valid component libraries (Pass)
        if test == 0:
            for lib in valid_libs:
                try:
                    if lib == 'components':
                        component_path = project_path + '/' + lib
                        component = ComponentLibrary(
                            component_path, False, cli_dict
                        )
                        component.create(project, project_path)
                        if not os.path.exists(
                            component_path + '/' + lib + '.xml'
                        ):
                            passed = False
                    else:
                        component_path = project_path + '/hdl/' + lib
                        component = ComponentLibrary(
                            component_path, False, cli_dict
                        )
                        component.create(project, project_path)
                        if not os.path.exists(
                            component_path + '/' + lib + '.rst'
                        ):
                            passed = False
                    os.system('rm -rf ' + project_path + '/components')
                    os.system('rm -rf ' + project_path + '/hdl')
                except Exception as e:
                    Logger().debug(test_name + str(e))
                    passed = False
        # Create a valid component library within components directory (Pass)
        if test == 1:
            try:
                component_path = project_path + '/components/cmp'
                component = ComponentLibrary(component_path, False, cli_dict)
                component.create(project, project_path + '/components')
                if not os.path.exists(project_path + '/components'):
                    passed = False
                if not os.path.exists(component_path + '/' + 'cmp.rst'):
                    passed = False
                if not os.path.exists(component_path + '/' + 'cmp.xml'):
                    passed = False
                os.system('rm -rf ' + project_path + '/components')
            except Exception as e:
                Logger().debug(test_name + str(e))
                passed = False
        # Create a valid hdl/platform/<platform> device library (Pass)
        if test == 2:
            try:
                plat_dir = project_path + '/hdl/platforms/test_plat'
                os.makedirs(plat_dir)
                with open(plat_dir + '/test_plat.xml', 'w') as file:
                    file.write('<HdlPlatform/>')
                    file.close()
                component_path = plat_dir + '/devices'
                component = ComponentLibrary(component_path, False, cli_dict)
                component.create(project, plat_dir)
                if not os.path.exists(component_path + '/devices.rst'):
                    passed = False
                if not os.path.exists(component_path + '/devices.xml'):
                    passed = False
                os.system('rm -rf ' + project_path + '/hdl')
            except Exception as e:
                Logger().debug(test_name + str(e))
                passed = False
        # Test ComponentLibrary.valid_library_name()
        if test == 3:
            # Create invalid library names (Fail)
            try:
                component_path = project_path + '/invalid_library'
                component = ComponentLibrary(component_path, False, cli_dict)
                component.create(project, project_path)
                passed = False
            except Exception as e:
                Logger().debug(test_name + str(e))
                passed = True
            # Create invalid comp lib  within components directory (Fail)
            try:
                component_path = project_path + '/devices'
                component = ComponentLibrary(component_path, False, cli_dict)
                component.create(project, project_path + '/components')
                passed = False
            except Exception as e:
                Logger().debug(test_name + str(e))
                passed = True
        # Test ComponentLibrary.library_exists()
        if test == 4:
            # Create duplicate valid component libraries (Fail)
            for lib in valid_libs:
                try:
                    if lib == 'components':
                        component_path = project_path + '/' + lib
                    else:
                        component_path = project_path + '/hdl/' + lib
                    component = ComponentLibrary(
                        component_path, False, cli_dict
                    )
                    component.create(project, project_path)
                    component.create(project, project_path)
                    passed = False
                except Exception as e:
                    Logger().debug(test_name + str(e))
                    os.system('rm -rf ' + project_path + '/components')
                    os.system('rm -rf ' + project_path + '/hdl')
                    passed = True
            # Create duplicate comp lib within components directory (Fail)
            try:
                component_path = project_path + '/components/cmp'
                component = ComponentLibrary(component_path, False, cli_dict)
                component.create(project, project_path + '/components')
                component.create(project, project_path + '/components')
                passed = False
            except Exception as e:
                Logger().debug(test_name + str(e))
                os.system('rm -rf ' + project_path + '/components')
                passed = True
            # Create a duplicate platform device library (Fail)
            try:
                plat_dir = project_path + '/hdl/platforms/test_plat'
                os.makedirs(plat_dir)
                with open(plat_dir + '/test_plat.xml', 'w') as file:
                    file.write('<HdlPlatform/>')
                    file.close()
                component_path = plat_dir + '/devices'
                component = ComponentLibrary(component_path, False, cli_dict)
                component.create(project, plat_dir)
                component.create(project, plat_dir)
                passed = False
            except Exception as e:
                Logger().debug(test_name + str(e))
                os.system('rm -rf ' + project_path + '/hdl')
                passed = True
        # Tests ComponentLibrary.valid_path()
        if test == 5:
            # Create an invalid library path (Fail)
            valid_libs.extend(['', 'comp_lib_within_components_directory'])
            for lib in valid_libs:
                component_path = project_path + '/' + lib
                if lib == '':
                    component_path = project_path + '/components'
                try:
                    project_path = project_path + '/invalid'
                    component = ComponentLibrary(
                        component_path, False, cli_dict
                    )
                    component.create(project, project_path)
                    passed = False
                except Exception as e:
                    Logger().debug(test_name + str(e))
                    passed = True
    log_pass_fail('testing ComponentLibrary create()', passed)
