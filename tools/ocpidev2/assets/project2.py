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
from _opencpi.assets.component2 import Component, Protocol
from _opencpi.assets.worker2 import Worker
from _opencpi.assets.application2 import Application, ApplicationsDirectory
from _opencpi.assets.library2 import SpecsDirectory, Discoverer
from _opencpi.assets.library2 import ComponentLibrary, ComponentLibrariesDirectory
from _opencpi.assets.library2 import test_ComponentLibrary
from _opencpi.assets.primitive2 import HdlLibrary
from _opencpi.assets.assembly2 import HdlAssembly
from _opencpi.assets.platform2 import HdlSlot, HdlCard
from _opencpi.assets.platform2 import HdlPlatform, RccPlatform
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


class Project(AssetBase, SpecsDirectory, Discoverer):
    """ Component Development Guide section 14 """

    def __init__(self, dir_abs_path, enable_path_existence_check=True,
                 cli_dict=None):
        self.root_tags = ['Project']
        if enable_path_existence_check:
            if not os.path.exists(dir_abs_path + '/Project.xml'):
                if not os.path.exists(dir_abs_path + '/Project.mk'):
                    raise InvalidAssetError('neither Project.mk or Project.xml exists')
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
                   is_list=True, cli=('-D', '--depends')))
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
        for hdl_platform in self.hdl_platforms:
            if hdl_platform.worker.name == name:
                am = authoring_model
                if (am == '') or (hdl_platform.worker.authoring_model == am):
                    ret = hdl_platform.worker
                    break
        return ret

    def get_asset_within(self, abs_path):
        """ get asset whose abs_path is within the abs_path and return None
            if not found """
        ret = None
        for component_library in self.component_libraries:
            for asset in component_library.workers:
                if (asset.get_xml_abs_path() + '/') in (abs_path + '/'):
                    ret = asset
                elif asset.get_dir_abs_path() == abs_path:
                    ret = asset
        for asset in self.applications:
            if (asset.get_dir_abs_path() + '/') in (abs_path + '/'):
                ret = asset
        for asset in self.hdl_primitives:
            if (asset.get_dir_abs_path() + '/') in (abs_path + '/'):
                ret = asset
        for asset in self.hdl_assemblies:
            if (asset.get_dir_abs_path() + '/') in (abs_path + '/'):
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

    def get_adapter_object_from_cli(self, cli_dict, _dir):
        if _dir != self.get_dir_abs_path() + '/hdl/adapters':
            msg = cli_dict['noun'] + ' \'' + cli_dict['name']
            msg += '\' can not exist within ' + _dir
            msg += ' (' + cli_dict['noun'] + ' can only be created within <project>/hdl/adapter, set -d, or the working directory, to <project>/hdl/adapters)'
            raise Exception(msg)
        xml_abs_path = _dir + '/' + cli_dict['name'] + '.hdl/'
        xml_abs_path += cli_dict['name'] + '.xml'
        return Worker(xml_abs_path, False, cli_dict)

    def get_application_object_from_cli(self, cli_dict, _dir):
        abs_path = self.get_dir_abs_path() + '/applications/'
        if cli_dict['xmlapp']:
            abs_path += cli_dict['name'] + '.xml'  # xml type
        else:
            if _dir != self.get_dir_abs_path() + '/applications':
                    msg = cli_dict['noun'] + ' \'' + cli_dict['name']
                    msg += '\' can not exist within ' + _dir
                    msg += ' (' + cli_dict['noun'] + ' can only be created within <project>/applications, set -d, or the working directory, to <project>/applications)'
                    raise Exception(msg)
            abs_path += cli_dict['name']  # dir type
        return Application(abs_path, False, cli_dict)

    def get_assembly_object_from_cli(self, cli_dict, _dir):
        if _dir != self.get_dir_abs_path() + '/hdl/assemblies':
            msg = cli_dict['noun'] + ' \'' + cli_dict['name']
            msg += '\' can not exist within ' + _dir
            msg += ' (' + cli_dict['noun'] + ' can only be created within <project>/hdl/assemblies, set -d, or the working directory, to <project>/hdl/assemblies)'
            raise Exception(msg)
        dir_abs_path = self.get_dir_abs_path() + '/hdl/assemblies/' + cli_dict['name']
        return HdlAssembly(dir_abs_path, False, cli_dict)

    def get_card_object_from_cli(self, cli_dict, _dir):
        if _dir != self.get_dir_abs_path() + '/hdl/cards/specs':
            msg = cli_dict['noun'] + ' \'' + cli_dict['name']
            msg += '\' can not exist within ' + _dir
            msg += ' (' + cli_dict['noun'] + ' can only be created within <project>/hdl/cards/specs, set -d, or the working directory, to <project>/hdl/cards/specs)'
            raise Exception(msg)
        xml_abs_path = self.get_dir_abs_path() + '/hdl/cards/'
        xml_abs_path += cli_dict['name'] + '.xml'
        return HdlCard(xml_abs_path, False, cli_dict)

    def get_component_object_from_cli(self, cli_dict, _dir):
        xml_abs_path = _dir + '/'
        if _dir != (self.get_dir_abs_path() + '/specs'):
            found = False
            for component_library in self.component_libraries:
                if _dir == component_library.get_dir_abs_path():
                    xml_abs_path += cli_dict['name'] + '.comp/'
                    found = True
                    break
                elif _dir == (component_library.get_dir_abs_path() + '/specs'):
                    Logger().warn('for component library creation, the working directory (or, if specified, the -d option) is recommended to be the component library location <library>, and not <library>/specs')
                    found = True
                    break
            if not found:
                msg = 'component \'' + cli_dict['name']
                msg += '\' can not exist within ' + _dir
                msg += ' (it is recommend to set the working directory or -d to a <project>/specs or a component <library> directory)'
                raise Exception(msg)
        xml_abs_path += cli_dict['name'] + '-comp.xml'
        return Component(xml_abs_path, False, cli_dict)

    def get_device_object_from_cli(self, cli_dict, _dir):
        xml_abs_path = _dir + '/' + cli_dict['name'] + '.hdl/'
        xml_abs_path += cli_dict['name'] + '.xml'
        return Worker(xml_abs_path, False, cli_dict)

    def get_library_object_from_cli(self, cli_dict, _dir):
        dir_abs_path = _dir
        if cli_dict['name'] == 'components':
            dir_abs_path += '/' + cli_dict['name']
            is_existing_component_libraries = False
            try:
                ComponentLibrariesDirectory(dir_abs_path, True, cli_dict)
                is_existing_component_libraries = True
            except InvalidAssetError:
                pass
            if (is_existing_component_libraries ) or (dir_abs_path != self.get_dir_abs_path() + '/components'):
                msg = 'component library \'' + cli_dict['name']
                msg += '\' can not exist within ' + _dir
                if is_existing_component_libraries:
                    msg += ' (\'components\' directory already exists and is not a component library - it already has a components.xml with a Libraries root tag)'
                else:
                    msg += ' (\'components\' library can only be created within the top level of a project, set -d, or the working directory, to the top level of a project)'
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
                    msg += ' (\'' + cli_dict['name'] + '\' library can only exist within <project>/hdl directory or <project>/hdl/platforms/<platform> directory, set -d, or the working directory, to <project>/hdl or <project>/hdl/platforms/<platform>)'
                    raise Exception(msg)
        elif (cli_dict['name'] == 'adapters') or (cli_dict['name'] == 'cards'):
            dir_abs_path = self.get_dir_abs_path() + '/hdl/' + cli_dict['name']
            if _dir != self.get_dir_abs_path() + '/hdl':
                msg = 'component library \'' + cli_dict['name']
                msg += '\' can not exist within ' + _dir
                msg += ' (\'' + cli_dict['name'] + '\' library can not exist within <project>/hdl directory, set -d, or the working directory, to <project>/hdl)'
                raise Exception(msg)
        else:
            dir_abs_path = _dir
            if dir_abs_path != self.get_dir_abs_path() + '/components':
                msg = 'component library ' + cli_dict['name']
                msg += ' can not exist within ' + _dir
                msg += ' (\'' + cli_dict['name'] + '\' library can not exist within <project>/components directory, set -d, or the working directory, to <project>/components)'
                raise Exception(msg)
            dir_abs_path += '/' + cli_dict['name']
        return ComponentLibrary(dir_abs_path, False, cli_dict)

    def get_platform_object_from_cli(self, cli_dict, _dir):
        if _dir != (self.get_dir_abs_path() + '/' + cli_dict['authoringmodel'] + '/platforms'):
            msg = cli_dict['authoringmodel'] + ' ' + cli_dict['noun'] + ' ' + cli_dict['name']
            msg += ' can not exist within ' + _dir
            msg += ' (must exist within <project>/hdl/platforms directory, set -d, or the working directory, to <project>/hdl/platforms)'
            raise Exception(msg)

        if cli_dict['authoringmodel'] == 'hdl':
            dir_abs_path = self.get_dir_abs_path() + '/hdl/platforms/' + cli_dict['name']
            asset = HdlPlatform(dir_abs_path, False, cli_dict)
        if cli_dict['authoringmodel'] == 'rcc':
            dir_abs_path = self.get_dir_abs_path() + '/rcc/platforms/' + cli_dict['name']
            asset = RccPlatform(dir_abs_path, False, cli_dict)
        return asset

    def get_primitive_object_from_cli(self, cli_dict, _dir):
        # TODO self.handle_hdl_library()
        dir_abs_path = self.get_dir_abs_path() + '/hdl/primitives/' + cli_dict['name']
        return HdlLibrary(dir_abs_path, False, cli_dict)

    def get_protocol_object_from_cli(self, cli_dict, _dir):
        # TODO self.handle_library()
        # TODO self.handle_cli_library()
        # TODO self.handle_cli_protocol()
        if _dir != (self.get_dir_abs_path() + '/specs'):
            found = False
            for component_library in self.component_libraries:
                if _dir == (component_library.get_dir_abs_path() + '/specs'):
                    found = True
                    break
            if not found:
                msg = cli_dict['noun'] + ' \'' + cli_dict['name']
                msg += '\' can not exist within ' + _dir
                msg += ' (' + cli_dict['noun'] + ' can only be created within <project>/specs or a component library specs directory, set -d, or the working directory, to <project>/specs or a component library specs directory)'
                raise Exception(msg)
        xml_abs_path = _dir + '/' + cli_dict['name'] + '-prot.xml'
        return Protocol(xml_abs_path, False, cli_dict)

    def get_slot_object_from_cli(self, cli_dict, _dir):
        xml_abs_path = self.get_dir_abs_path() + '/hdl/cards/specs/' + cli_dict['name'] + '.xml'
        return HdlSlot(xml_abs_path , False, cli_dict)

    def get_worker_object_from_cli(self, cli_dict, _dir):
        # TODO self.handle_hdl_library()
        xml_abs_path = _dir + '/' + cli_dict['name'] + '.'
        xml_abs_path += cli_dict['authoringmodel'] + '/' + cli_dict['name'] + '.xml'
        return Worker(xml_abs_path, False, cli_dict)

    def get_test_object_from_cli(self, cli_dict, _dir):
        dir_abs_path = _dir + '/' + cli_dict['name'] + '.test'
        return Test(dir_abs_path, False, cli_dict)

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
                msg = 'performing \'' + cli_dict['verb'] + '\' for an applications directory '
                msg = 'performing \'' + cli_dict['verb'] + '\' for an applications directory '
                Logger().log(3, msg + ' within directory ' + self.get_dir_abs_path())
                ApplicationsDirectory(self.get_dir_abs_path() + '/applications', False, cli_dict).create()
        elif cli_dict['noun'] == 'library':
            if cli_dict['name'] == 'components':
                pass
            elif cli_dict['name'] == 'devices':
                pass
            elif (cli_dict['name'] == 'adapters') or (cli_dict['name'] == 'cards'):
                pass
            else:
                if not os.path.exists(dir_abs_path):
                    msg = 'performing \'' + cli_dict['verb'] + '\' for a components directory '
                    Logger().log(3, msg + ' within directory ' + self.get_dir_abs_path())
                    ComponentLibrariesDirectory(dir_abs_path, False, cli_dict).create()
        asset = self.get_asset_object_from_cli(cli_dict, _dir)
        if (cli_dict['noun'] == 'component') or (cli_dict['noun'] == 'protocol'):
            if not os.path.exists(asset.get_dir_abs_path()):
                System('mkdir -p ' + asset.get_dir_abs_path())
        if os.path.exists(asset.abs_path):
            msg = cli_dict['noun'] + ' ' + cli_dict['name'] + ' already exists'
            msg += ' within directory ' + asset.get_dir_abs_path().rsplit('/', 1)[0]
            raise Exception(msg)
        if (asset.get_type() == 'hdl worker') or \
           (asset.get_type() == 'rcc worker'):
            if (asset.version != 2):
                Logger().warn('default version of 0 is being used, but --version 2 is highly recommended')
        asset.create()
        # if cli_dict['createtest']:
        #     self.get_test_object_from_cli(cli_dict, _dir).create()

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
                    ComponentLibrariesDirectory(dir_abs_path, True, {})
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
                # split necessary because some Libraries are specified w/ package id, e.g., ocpi.core.bsv
                ret.append(lib.split('.')[-1])
        return ret

    def get_hdl_worker_dependent_libraries(self, comp_library, worker):
        # TODO should some of this move to ComponentLibrary class?
        ret = []
        if worker.authoring_model == 'hdl':
            ret.extend(Project.get_built_in_hdl_libraries())
        # TODO investigate whether HdlLibraries is even allowed?
        for lib in comp_library.attrs['HdlLibraries']:
            ret.append(lib)
        for lib in comp_library.attrs['Libraries']:
            ret.append(lib)
        for lib in worker.attrs['Libraries']:
            ret.append(lib)
        return ret

    def get_assets_of_type(self, _type):
        assets = []
        if _type == Application:
            assets.extend(self.applications)
        if _type == HdlAssembly:
            assets.extend(self.hdl_assemblies)
        if _type == HdlCard:
            assets.extend(self.hdl_cards)
        if _type == Component:
            assets.extend(self.components)  # project specs directory
            for component_library in self.component_libraries:
                assets.extend(component_library.components)
        if _type == HdlLibrary:
            assets.extend(self.hdl_primitives)
        if _type == ComponentLibrary:
            assets.extend(self.component_libraries)
        if _type == HdlSlot:
            assets.extend(self.hdl_slots)
        if _type == HdlPlatform:
            assets.extend(self.hdl_platforms)
        if _type == RccPlatform:
            assets.extend(self.rcc_platforms)
        if _type == Project:
            assets.extend([self])
        for component_library in self.component_libraries:
            if _type == Worker:
                assets.extend(component_library.workers)
            if _type == Test:
                assets.extend(component_library.tests)
        if _type == Worker:
            for hdl_platform in self.hdl_platforms:
                assets.append(hdl_platform.worker)
        return assets

    def get_types_from_cli_dict(self, cli_dict):
        """ get list of types (asset classes) that correspond to cli_dict noun
            and authoring_model entries """
        types = []
        if cli_dict['noun'].startswith('application'):
            types.append(Application)
        if cli_dict['noun'].startswith('assembl'):
            types.append(HdlAssembly)
        if cli_dict['noun'].startswith('card'):
            types.append(HdlCard)
        if cli_dict['noun'].startswith('component'):
            types.append(Component)
        if cli_dict['noun'].startswith('core'):
            types.append(HdlLibrary)
        if cli_dict['noun'].startswith('librar'):
            types.append(ComponentLibrary)
        if cli_dict['noun'].startswith('slot'):
            types.append(HdlSlot)
        if cli_dict['noun'].startswith('platform'):
            if (cli_dict['authoringmodel'] == '') or \
               (cli_dict['authoringmodel'] == 'hdl'):
                types.append(HdlPlatform)
            if (cli_dict['authoringmodel'] == '') or \
               (cli_dict['authoringmodel'] == 'rcc'):
                types.append(RccPlatform)
        if cli_dict['noun'].startswith('primitive'):
            types.append(HdlLibrary)
        if cli_dict['noun'].startswith('project'):
            types.append(Project)
        if cli_dict['noun'].startswith('worker'):
            types.append(Worker)
        if cli_dict['noun'].startswith('test'):
            types.append(Test)
        return types

    def show(self, cli_dict, json_dict={}):
        if cli_dict['globalscope']:
            msg = '--global-scope does not change behavior, '
            msg += 'see man ocpidev2-show'
            Logger().warn(msg)
        first = True
        assets = []
        for _type in self.get_types_from_cli_dict(cli_dict):
            assets.extend(self.get_assets_of_type(_type))
        list_to_show = []
        for asset in assets:
            if (cli_dict['name'] is None) or \
               (cli_dict['name'] == asset.name):
                if (cli_dict['d'] == []) or \
                   any([(_dir + '/') in (asset.abs_path + '/') for _dir in cli_dict['d']]):
                    do_hdl_check = (cli_dict['authoringmodel'] != '') and \
                                   (cli_dict['noun'].startswith('primitive') or \
                                   cli_dict['noun'].startswith('librar'))
                    containing_path = asset.get_dir_abs_path().rsplit('/', 1)[0]
                    if cli_dict['noun'].startswith('librar'):
                        is_hdl = containing_path.endswith('hdl') or \
                                 containing_path.split('/')[-3] == 'hdl'
                    else:
                        is_hdl = containing_path.endswith('hdl/adapters') or \
                                 containing_path.endswith('hdl/cards') or \
                                 containing_path.endswith('hdl/devices') or \
                                 containing_path.endswith('hdl/primitives') or \
                                 containing_path.endswith('hdl/platforms')
                    if (not do_hdl_check) or (do_hdl_check and is_hdl):
                        if cli_dict['noun'].startswith('primitive'):
                            if cli_dict['adjective'].startswith('core'):
                                if not asset.is_core:
                                    continue
                            elif cli_dict['adjective'].startswith('librar'):
                                if asset.is_core:
                                    continue
                        pid = str(self.get_package_id())
                        if (_type == Component) or (_type == Worker) or (_type == ComponentLibrary):
                            for component_library in self.component_libraries:
                                if (asset in component_library.components) or \
                                   (asset in component_library.workers) or \
                                   (asset in self.component_libraries):
                                    if (asset in self.component_libraries):
                                        pid = asset.get_package_id(pid)
                                    else:
                                        pid = component_library.get_package_id(pid)
                                    break
                        pid_and_name = pid
                        if not cli_dict['noun'].startswith('project'):
                            if not (asset in self.component_libraries):
                                pid_and_name += '.' + asset.name
                        msg = ''
                        if first and cli_dict['simple']:
                            msg += ' '
                        msg += pid_and_name
                        if cli_dict['noun'].startswith('worker'):
                            msg += '.' + asset.authoring_model
                        if cli_dict['noun'].startswith('platform'):
                            if type(asset) == HdlPlatform:
                                msg += '.hdl'
                            if type(asset) == RccPlatform:
                                msg += '.rcc'
                        if cli_dict['verbose'] or cli_dict['table']:
                            msg += ' '
                            for idx in range(60-len(msg)):
                                msg += ' '
                            msg += asset.abs_path
                        if cli_dict['json']:
                            json_dict[pid_and_name] = \
                                    {'package_id': pid,
                                     'directory': asset.get_dir_abs_path()}
                        else:
                            list_to_show.append(msg)
                        first = False
        if not cli_dict['json']:
            # the list is sorted so that assets are generally printed in order
            # of project...component library... etc
            if len(list_to_show) > 0:
                sep = ' ' if cli_dict['simple'] else '\n'
                end = '' if cli_dict['simple'] else '\n'
                print(*sorted(list_to_show), sep=sep, end=end)
        return json_dict

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
        os.system(
                'rm -rf $(find ' + _dir + ' -type d -name config-\*)')
        os.system(
                'rm -rf $(find ' + _dir +
                ' -type d -name simulations)')
        os.system(
                'rm -rf $(find ' + _dir + ' -type d -name target-\*)')
        os.system(
                'rm -rf $(find ' + _dir +
                ' -type d -name container-\*)')
        os.system('rm -rf $(find ' + _dir + " -type f -name '.*lock')")
        os.system(
                'rm -rf $(find ' + _dir + " -type f -name '.*build')")
        os.system(
                'rm -rf $(find ' + _dir + " -type d -name artifacts)")

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
