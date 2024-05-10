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
import itertools
from _opencpi.assets.abstract2 import *
from _opencpi.assets.abstract2 import AssetBase
from _opencpi.assets.worker2 import Worker
from _opencpi.assets.application2 import Application
from _opencpi.assets.library2 import SpecsDirectory, Discoverer, ComponentLibrary
from _opencpi.assets.primitive2 import HdlLibrary
from _opencpi.assets.assembly2 import HdlAssembly
from _opencpi.assets.platform2 import HdlCard, HdlPlatform


class Project(SpecsDirectory, Discoverer, AssetBase):
    """ Component Development Guide section 14 """

    def __init__(
            self, dir_abs_path, do_discover_component_libraries=True,
            do_discover_hdl_primitives=True):
        AssetBase.__init__(self, dir_abs_path)
        #del self.name
        SpecsDirectory.__init__(self)
        self.package_prefix = ''
        self.package_name = ''
        self.package_id = ''
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
        # start of CDG section 14.5 (EXTERNAL-to-project, i.e., DEPENDENCY)
        self._component_libraries = []
        # HDG section 5 "The built-in ocpi.core project includes several HDL
        # primitive libraries, and some are always available for use by all
        # workers" - here are the implied "some"
        self.hdl_libraries = ['bsv', 'fixed_float', 'ocpi', 'util', 'protocol']
        self.hdl_libraries += ['cdc', 'sdp', 'axi']
        # initialize below line according to CDG Table 8
        self.project_dependencies = ['ocpi.core']
        # end of CDG section 14.5
        self.parse()
        # TODO fix below optimization line
        self.discover(
                do_discover_component_libraries, do_discover_hdl_primitives, do_discover_hdl_primitives)
        self.first = True

    def get_root_tags(self):
        return ['Project']

    def get_xml_abs_path(self):
        return self.abs_path + '/Project.xml'

    def get_package_id(self):
        tmp = self.package_prefix + "." + self.package_name
        ret = tmp if self.package_id == '' else self.package_id
        return ret

    def get_asset(self, abs_path):
        """ returns None if asset not found """
        ret = None
        for component_library in self.component_libraries:
            for worker in component_library.workers:
                if worker.abs_path == abs_path:
                    ret = Worker(abs_path + '/' + worker.name + '.xml')
        for application in self.applications:
            if application.abs_path == abs_path:
                ret = Application(abs_path)
        for hdl_primitive in self.hdl_primitives:
            if hdl_primitive.abs_path == abs_path:
                ret = HdlLibrary(abs_path)
        for hdl_assembly in self.hdl_assemblies:
            if hdl_assembly.abs_path == abs_path:
                ret = HdlAssembly(abs_path)
        return ret

    # TODO consolidate
    #def get_list_of_existing_abs_paths_to_parse(self, abs_paths):
    #    ret = []
    #    for abs_path in abs_paths:
    #        print(abs_path)
    #        if os.path.exists(abs_path):
    #            Logger().debug('parsing ' + abs_path)
    #            if abs_path == self.get_xml_abs_path():
    #                abs_path = ''
    #            ret.append(abs_path)
    #    return ret

    def parse(self):
        paths = []
        # start pre-2.0 opencpi
        paths += [self.abs_path + '/Project.mk']
        # intentionally put xml path last so that its attributes take precedence
        # TODO consolidate with get_asset2() from AttributeBase
        paths.append(self.get_xml_abs_path())
        # end pre-2.0 opencpi
        paths = self.get_list_of_existing_abs_paths_to_parse(paths)
        clibs = self.get_attr_list('ComponentLibraries', None, paths)
        if len(clibs) > 0:
            self._component_libraries = clibs
        hlibs = self.get_attr_list('HdlLibraries', None, paths)
        if len(hlibs) > 0:
            self.hdl_libraries = hlibs
        deps = self.get_attr_list('ProjectDependencies', None, paths)
        if len(deps) > 0:
            self.project_dependencies = deps
        package_prefix = self.get_attr('PackagePrefix', None, paths)
        if package_prefix != '':
            self.package_prefix = package_prefix 
        package_name = self.get_attr('PackageName', None, paths)
        if package_name != '':
            self.package_name = package_name
        package_id = self.get_attr('PackageID', None, paths)
        if package_id != '':
            self.package_id = package_id

    def discover(
            self, do_component_libraries=True, do_hdl_primitives=True,
            do_hdl_assemblies=True):
        # start of bullets at top of CDG section 14
        if do_component_libraries:
            tmp = self.abs_path.split('/')[-1]
            Logger().info('discovering project ' + tmp)
            self.discover_components()
            self.discover_component_libraries()
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
        dirs = ['components', 'hdl/devices', 'hdl/cards']
        dirs += ['hdl/adapters', 'hdl/platforms']
        dir_abs_paths = []
        for _dir in dirs:
            dir_abs_path = self.abs_path + '/' + _dir
            if os.path.isdir(dir_abs_path):
                # add to dir_abs_path the absolute path to the directories
                # of the following form from CDG section 14.2.3., if they exist,
                # regardless of whether a "sub"-library directory, e.g.
                # components/<library>, exists:
                #   - components/
                #   - hdl/devices/
                #   - hdl/cards/
                #   - hdl/adapters/
                #   - hdl/platforms/
                dir_abs_paths.append(dir_abs_path)
                subdir_abs_paths = AssetBase.get_existing_abs_dir_paths_for_asset_consideration(dir_abs_path)
                if _dir == 'components':
                    for subdir_abs_path in subdir_abs_paths:
                        if not ComponentLibrary.get_dir_abs_path_is_worker(subdir_abs_path):
                            # add to dir_abs_path the absolute path to the directories of the
                            # following parents from CDG section 14.2.3., if they exist:
                            #   - hdl/platforms/<platform>/devices
                            #   - components/<library>
                            dir_abs_paths.append(subdir_abs_path)
                elif _dir == 'hdl/platforms':
                    for platform in subdir_abs_paths:
                        subdir_abs_path = platform + '/devices'
                        if os.path.isdir(subdir_abs_path):
                            # add to dir_abs_path the absolute path to the directories of the
                            # following parents from CDG section 14.2.3., if they exist:
                            #   - hdl/platforms/<platform>/devices
                            dir_abs_paths.append(subdir_abs_path)
        return dir_abs_paths

    def discover_component_libraries(self):
        for dir_abs_path in self.get_existing_dir_abs_paths_for_clib_consideration():
            try:
                asset = ComponentLibrary(dir_abs_path)
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

    def discover_hdl_primitives(self):
        self.discover_dir_assets('hdl/primitives')

    def discover_hdl_assemblies(self):
        # TODO check if there is an allowlist, and if so, pass to below call
        self.discover_dir_assets('hdl/assemblies')

    def discover_hdl_cards(self):
        discovery_path = self.abs_path + '/hdl/cards/specs'
        if os.path.isdir(discovery_path):
            for _dir in AssetBase.listdir_assets(discovery_path):
                # TODO catch InvalidAssetError instead of all exceptions
                try:
                    asset = HdlCard(discovery_path + '/' + _dir)
                    self.append_discovered_asset(asset)
                except InvalidAssetError:
                    pass

    def discover_hdl_platforms(self):
        # TODO check if there is an allowlist, and if so, pass to below call
        self.discover_dir_assets('hdl/platforms')

    def get_built_in_hdl_libraries(self):
        """ HDG section 5 "The built-in ocpi.core project includes several HDL
            primitive libraries, and some are always available for use by all
            workers" - here are the implied "some" """
        # these are intentionally in build dependency order
        tmp = ['bsv', 'fixed_float', 'ocpi', 'util', 'protocol', 'cdc']
        return tmp + ['platform', 'sdp', 'axi']

    def get_hdl_primitive_dependent_libraries(self, hdl_primitive = None):
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
        if (hdl_primitive.libraries is not None) and (len(hdl_primitive.libraries) > 0):
            for lib in hdl_primitive.libraries:
                # split necessary because some Libraries are specified w/ package id, e.g., ocpi.core.bsv
                ret.append(lib.split('.')[-1])
        return ret

    def get_hdl_worker_dependent_libraries(self, comp_library, worker):
        ret = self.get_built_in_hdl_libraries()
        for lib in comp_library.hdl_libraries:
            ret.append(lib)
        for lib in worker.libraries:
            ret.append(lib)
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

    def get_build_output_path(self, asset, hdl_target = None,
            hdl_platform = None):
        ret = asset.abs_path
        tmp = ''
        if asset.get_type() == 'hdl assembly':
            tmp = asset.name + '_' + hdl_platform + '_'
            if len(asset.containers) == 0:
                tmp += 'base_'
            else:
                if asset.containers[0].config == '':
                    tmp += 'base_'
                else:
                    tmp += asset.containers[0].config + '_'
                tmp += asset.containers[0].name
            ret += '/container-' + tmp + '_'
        ret += '/target-' + get_hdl_target(hdl_platform) + '/'
        if (asset.get_type() == 'hdl primitive') or (asset.get_type() == 'hdl worker'):
            # TODO properly separate into extensible tool
            ret += asset.name + get_worker_build_output_extension(hdl_platform)
        if (asset.get_type() == 'hdl assembly'):
            # TODO properly separate into extensible tool
            ret += tmp + '_rv.' + get_assembly_build_output_extension(hdl_platform)
        return ret

    def build_asset(self, asset, project_registry, tool,
            hdl_target = None, hdl_platform = None, rcc_platform = None, _j = 1):
        fs = TemporaryFilesystem()
        os.system('mkdir -p ' + fs.abs_path)
        global_makefile.abs_path = fs.abs_path + '/Makefile'
        target_name = self.get_build_output_path(asset, get_hdl_target(hdl_platform),
                hdl_platform)
        Logger().info('gathering dependencies')
        global_makefile.rules['all'] = GNUMakeRule()
        target = GNUMakeTarget('all', True)
        global_makefile.rules['all'].targets.append(target)
        global_makefile.rules['all'].prerequisites.append(target_name)
        global_dependency_tree[asset] = DependencyTree()
        self.append_rules_to_makefile(asset, project_registry, tool,
            hdl_target, hdl_platform)
        global_makefile.emit()
        # TODO delete below line
        os.system('cp ' + global_makefile.abs_path + ' /tmp/Makefile')
        tmp = 'make -f ' + global_makefile.abs_path
        if _j > 1:
            tmp += ' -j ' + str(_j)
        if os.system(tmp) != 0:
            raise Exception('build failed')

    def append_prim_rules_to_makefile(self, asset, project_registry, tool,
            tname, hdl_target = None, hdl_platform = None):
        bilibs = self.get_built_in_hdl_libraries()
        #for name in self.get_hdl_primitive_dependent_libraries():
        for name in self.get_hdl_primitive_dependent_libraries(asset):
            #if not ((not self.first) and (name in bilibs)):
            project = project_registry.get_hdl_primitive_project(name)
            prim = None
            for hdl_primitive in project.hdl_primitives:
                if hdl_primitive.name == name:
                    prim = hdl_primitive
                    break
            ppath = self.get_build_output_path(prim, get_hdl_target(hdl_platform),
                    hdl_platform)
            global_makefile.rules[tname].prerequisites.append(ppath)
            global_dependency_tree[asset].dependents.append(prim)
            project.append_rules_to_makefile(prim,
                    project_registry, tool, hdl_target, hdl_platform)
        if self.first:
            self.first = False

    def append_worker_rules_to_makefile(self, asset, project_registry, tool,
            tname, hdl_target = None, hdl_platform = None):
        wproj = project_registry.get_worker_project(asset.name)
        libs = []
        for lib in wproj.component_libraries:
            for worker in lib.workers:
                if worker.name == asset.name:
                    if worker.authoring_model == asset.authoring_model:
                        libs = wproj.get_hdl_worker_dependent_libraries(
                                lib, asset)
                        break
        for name in libs:
            lproj = project_registry.get_hdl_primitive_project(name,
                    wproj)
            prim = None
            for hdl_primitive in lproj.hdl_primitives:
                if hdl_primitive.name == name:
                    prim = hdl_primitive
                    break
            ppath = self.get_build_output_path(prim, get_hdl_target(hdl_platform),
                    hdl_platform)
            global_makefile.rules[tname].prerequisites.append(ppath)
            global_dependency_tree[asset].dependents.append(prim)
            lproj.append_rules_to_makefile(prim,
                    project_registry, tool, hdl_target, hdl_platform)
        if asset.name == hdl_platform:
            _hdl_platform = HdlPlatform(asset.get_dir_abs_path())
            for cfg in _hdl_platform.configurations.values():
                for dev in cfg.devices:
                    _worker = None
                    project = project_registry.get_worker_project(dev)
                    for clib in project.component_libraries:
                        for device in clib.workers:
                            if device.name == dev:
                                _worker = device
                                break
                    wpath= self.get_build_output_path(_worker, get_hdl_target(hdl_platform),
                            hdl_platform)
                    global_makefile.rules[tname].prerequisites.append(wpath)
                    global_dependency_tree[asset].dependents.append(_worker)
                    project.append_rules_to_makefile(_worker, project_registry,
                            tool, hdl_target, hdl_platform)

    def append_hdl_assembly_rules_to_makefile(self, asset, project_registry, tool,
            tname, hdl_target = None, hdl_platform = None):
        for name in self.get_hdl_assembly_dependent_workers(
                project_registry, asset, hdl_platform):
            project = project_registry.get_worker_project(name)
            _worker = None
            for component_library in project.component_libraries:
                for worker in component_library.workers:
                    if worker.name == name:
                        if worker.authoring_model == 'hdl':
                            _worker = worker
                            break
            wpath = self.get_build_output_path(_worker, get_hdl_target(hdl_platform),
                    hdl_platform)
            global_makefile.rules[tname].prerequisites.append(wpath)
            global_dependency_tree[asset].dependents.append(_worker)
            project.append_rules_to_makefile(_worker, project_registry, tool,
                    hdl_target, hdl_platform)

    def append_rules_to_makefile(self, asset, project_registry, tool,
            hdl_target = None, hdl_platform = None):
        """ here the CDG section 4.2 heirarchy is automated """
        #tname = asset.name + '_' + asset.get_type().replace(' ', '_')
        tname = self.get_build_output_path(asset, get_hdl_target(hdl_platform), hdl_platform)
        global_makefile.rules[tname] = GNUMakeRule()
        target = GNUMakeTarget(tname)
        global_makefile.rules[tname].targets.append(target)
        global_dependency_tree[asset] = DependencyTree()
        if asset.get_type() == 'hdl primitive':
            self.append_prim_rules_to_makefile(asset, project_registry, tool,
                    tname, hdl_target, hdl_platform)
        if asset.get_type() == 'hdl worker':
            self.append_worker_rules_to_makefile(asset, project_registry, tool,
                    tname, hdl_target, hdl_platform)
        if asset.get_type() == 'hdl assembly':
            self.append_hdl_assembly_rules_to_makefile(asset, project_registry,
                    tool, tname, hdl_target, hdl_platform)
        # build single asset whose dependencies, if enabled, have already been
        # built
        tool.build_asset(self, asset, tname, hdl_target, hdl_platform,
                False, project_registry, global_dependency_tree)
        #tool.append_rules_to_makefile(asset, tname, hdl_target, hdl_platform,
        #        False, project_registry)


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
            "hdl/platforms/plat/devices" : libraries[6]
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
                    platform_xml = project_abs_path + '/' + 'hdl/platforms/plat/plat.xml'
                    os.system('touch %s' % platform_xml)
                    platform_xml_file = open(platform_xml, 'w')
                    platform_xml_file.write('<HdlPlatform/>\n')
                    platform_xml_file.close()
                    #os.system('cat ' + platform_xml)
                else:
                    num_expected_libs += 1
                    os.system('mkdir -p %s/%s' % (project_abs_path, lib_key))
            project_xml = open(project_abs_path + '/' + 'Project.xml', 'w')
            project_xml.write(
                    '<Project PackagePrefix=\'ocpi\' PackageName=\'proj\'/>\n')
            project_xml.close()
            uut = Project(project_abs_path)
            if num_expected_libs != len(uut.component_libraries):
                passed = False
        os.system('rm -rf %s/*' % project_abs_path)
    os.system('mkdir -p %s' % project_abs_path)
    for ext in ['hdl', 'rcc', 'ocl', 'test']:
        lib_path = '%s/components/foo.%s' % (project_abs_path, ext)
        os.system('mkdir -p ' + lib_path)
        if ext != 'test':
            ff = open(lib_path + '/foo.xml', 'w')
            ff.write('<' + ext  + 'Worker/>\n')
            ff.close()
    uut = Project(project_abs_path)
    if len(uut.component_libraries) == 1:
        if uut.component_libraries[0].name != 'components':
            passed = False
    else:
        passed = False
    log_pass_fail('testing Project discover_component_libraries()', passed)
    if passed is False:
        ret = False
    return ret
