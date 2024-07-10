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
from _opencpi.assets.platform2 import HdlPlatform, RccPlatform
from _opencpi.assets.assembly2 import HdlAssembly
from _opencpi.assets.primitive2 import HdlLibrary
from _opencpi.assets.application2 import Application
from _opencpi.assets.test2 import Test

comp_lib_rst_template = """
.. {{asset.name|capitalize}} library index page


{{asset.name|capitalize}} Library
=================================
Skeleton outline: Component library description and outline of scope to go here.

.. toctree::
   :maxdepth: 1
   :glob:
   :caption: {{asset.name}}

   *.comp/*-index
   *.comp/*-comp

..
   "*.comp/*-index" is for backward compatibility with older component document naming schemes.

"""  # noqa: E501


def create_templates(name):
    """ Creates a <component_name>.rst skeleton document to populate the
        directory using instance variables"""
    comp_lib_templates = {}
    comp_lib_templates[name + '.rst'] = comp_lib_rst_template
    return comp_lib_templates


class SpecsDirectory():
    """ Class for discovering component assets in the specs directory """

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
                if parent != 'applications':
                    Logger().warn('skipping ' + str(err))
                pass


class ComponentLibraries(AssetBase):
    """ undocumented """

    def __init__(self, dir_abs_path):
        self.root_tags = ['Libraries']  # undocumented
        if not dir_abs_path.endswith('components'):
            self.raise_invalid_asset_error()
        AssetBase.__init__(self, dir_abs_path)
        # TODO investigate moving below 3 lines into AssetBase
        if os.path.exists(self.get_xml_abs_path()):
            self.raise_if_invalid_root_tag(self.get_parsed().getroot())
        found = True
        for entry in AssetBase.listdir_assets(self.get_dir_abs_path()):
            if entry == 'specs':
                found = False
        if not found:
            self.raise_invalid_location()
        self.parse()

    def get_paths_to_parse(self):
        return [self.get_xml_abs_path()]

    def get_type(self):
        return 'component libraries'


class ComponentLibrary(AssetBase, SpecsDirectory, Discoverer):
    """ Reference RCC/HDL Development Guide section 3. A ComponentLibrary is
        represented by a directory and knows nothing about the project it
        is in or its package ID. """
    # start of CDG section 14.2.3
    valid_locations = ['components', 'hdl/devices', 'hdl/cards']
    valid_locations += ['hdl/adapters', 'hdl/platforms', 'devices']
    # end of CDG section 14.2.3

    def __init__(self, dir_abs_path, enable_path_existence_check=True,
                 cli_dict=None):
        self.root_tags = ['Library']  # CDG section 10.1
        AssetBase.__init__(self, dir_abs_path, enable_path_existence_check)
        try:
            self.raise_if_invalid_location()
        except InvalidAssetError:
            tmp = dir_abs_path.split('components/')
            Logger().debug('tmp ' + str(tmp))
            if len(tmp) == 2:
                if tmp[1] == 'gen':
                    self.raise_invalid_location()
            else:
                self.raise_invalid_location()
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
        self.parse(cli_dict)
        workers = self.attrs['Workers']
        allowlist = None if workers == [] else workers
        if enable_path_existence_check:
            self.discover(allowlist, 'hdl/platforms' in dir_abs_path)

    def get_comp_dict(self, project):
        """ Update comp_dict with discovered project
            hdl/platform/<platform_name> libraries """
        comp_dict = ({lib.split('/')[-1]: lib for lib in
                     ComponentLibrary.valid_locations})
        platform_device_libs = []
        for proj_plat in project.hdl_platforms:
            plat_rel = proj_plat.abs_path.split('/')[-3:]
            plat_rel = '/'.join(plat_rel) + '/devices'
            platform_device_libs.append(plat_rel)
        comp_dict['devices'] = [comp_dict['devices']]
        comp_dict['devices'].extend(platform_device_libs)
        return comp_dict

    def create_components_dir(self, project):
        """ If no 'components' directory exists when creating a
            omponent library with a components directory, create one. """
        if not os.path.exists(project.abs_path + '/components'):
            # Create 'components' temporary variables
            abs_path = self.abs_path
            self.abs_path = project.abs_path + '/components'
            name = self.name
            self.name = 'components'
            # Create 'components' template
            comp_lib_templates = create_templates('components')
            comp_lib_templates['components.xml'] = g_asset_template
            AssetBase.create_files(self, comp_lib_templates, self.abs_path)
            # Reset self. variables to create the component library within the
            # components directory
            self.abs_path = abs_path
            self.name = name

    def valid_library_name(self, project, comp_dict,
                           is_component_library_within_components_dir=False):
        """ Check for a valid component library name """
        if is_component_library_within_components_dir:
            if self.name in comp_dict.keys():
                msg = ("Sub-component-library name '" + self.name +
                       "' invalid. Cannot share component library names: " +
                       (', '.join(map(str, list(comp_dict.keys()))))) + "."
                raise Exception(msg)
        if not is_component_library_within_components_dir:
            if self.name not in comp_dict:
                msg = ("Component Library name '" + self.name + "' invalid. "
                       "Not part of the valid component library names: " +
                       (', '.join(map(str, list(comp_dict.keys())))) + ". "
                       "To create a '" + self.name +
                       "' component library within a components directory" +
                       ", point (-d) to the 'components' library.")
                raise Exception(msg)

    def valid_path(self, project, comp_dict,
                   is_component_library_within_components_dir):
        """ Check that the user is providing a valid path to a component
            library. If not, provide path suggestions """
        valid_path = False
        if is_component_library_within_components_dir:
            valid_path = True
        elif self.name == 'devices':
            for lib in comp_dict[self.name]:
                path_to_check = project.abs_path + '/' + lib
                if path_to_check == self.abs_path:
                    valid_path = True
        else:
            path_to_check = project.abs_path + '/' + comp_dict[self.name]
            if path_to_check == self.abs_path:
                valid_path = True
        if not valid_path:
            if self.name == 'devices':
                valid_locations = (
                    '<project_name>/hdl/ , ' +
                    '<project_name>/hdl/platform/<platform_name>/'
                )
            elif self.name in ['cards', 'adapters', 'platforms']:
                valid_locations = '<project_name>/hdl/'
            else:  # 'components':
                valid_locations = '<project_name>/'
            msg = ("create library '" + self.name + "' must be in (CWD) or "
                   "point to (-d) a valid component library location: " +
                   valid_locations)
            raise Exception(msg)

    def create(self, project, _dir):
        """ Creates a valid Component Library and associated skeleton files
            for a given path """
        comp_lib_templates = create_templates(self.name)
        comp_dict = self.get_comp_dict(project)
        is_comp_lib_within_components_dir = _dir.endswith(
                project.name + '/components')
        if is_comp_lib_within_components_dir and (self.name not in
                                                  comp_dict.keys()):
            self.create_components_dir(project)
        self.valid_library_name(project, comp_dict,
                                is_comp_lib_within_components_dir)
        self.valid_path(project, comp_dict, is_comp_lib_within_components_dir)
        comp_lib_xml_name = self.name + '.xml'
        comp_lib_templates[comp_lib_xml_name] = g_asset_template
        AssetBase.create_files(self, comp_lib_templates, self.abs_path)

    @staticmethod
    def get_dir_abs_path_is_worker(dir_abs_path):
        ret = False
        # TODO remove 'comp' from list
        for ext in ['rcc', 'hdl', 'ocl', 'comp']:
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

    def get_attr_infos(self):
        ret = []
        ret.append(AttributeInfo('ComponentLibraries', is_list=True))
        # TODO investigate whether HdlLibraries is even allowed?
        ret.append(AttributeInfo('HdlLibraries', is_list=True))
        ret.append(AttributeInfo('Libraries', is_list=True))
        ret.append(AttributeInfo('Workers', is_list=True))
        ret.append(AttributeInfo('PackagePrefix',
                                 cli=('-F', '--package-prefix')))
        ret.append(AttributeInfo('PackageID', cli=('-K', '--package-id')))
        ret.append(AttributeInfo('PackageName', cli=('-N', '--package-name')))
        return ret

    def get_paths_to_parse(self):
        paths = []
        # start pre-2.0 opencpi
        # TODO address library.mk vs libraries.mk behavior in Makefile
        paths += [self.abs_path + '/Library.mk', self.abs_path + '/Makefile']
        # intentionally put xml last so that its attributes take precedence
        # end pre-2.0 opencpi
        paths.append(self.get_xml_abs_path())
        paths = self.get_list_of_existing_abs_paths_to_parse(paths)
        return paths

    def parse(self, cli_dict=None):
        AssetBase.parse(self, cli_dict)
        global g_libraries_mk
        if g_libraries_mk:
            g_libraries_mk = False

    def discover(self, allowlist, platform=False):
        self.discover_components()
        self.discover_workers(allowlist, platform)
        self.discover_tests()

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
        # Logger().debug(str(allowlist))
        # '' in below line indicates worker discovery
        self.discover_dir_assets('', allowlist, platform)

    def discover_tests(self):
        self.discover_dir_assets('', None, False)

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
                test_str = 'ocpi.core.platforms.mypf.devices'
                if uut.get_package_id('ocpi.core') != test_str:
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
            tmp = passed
            log_pass_fail('testing ComponentLibrary component_libraries', tmp)
        if test == 6:
            log_pass_fail('testing ComponentLibrary get_package_id()', passed)
        if passed is False:
            ret = False
    return ret


def test_ComponentLibrary_create(ret):
    from _opencpi.assets.project2 import Project
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
