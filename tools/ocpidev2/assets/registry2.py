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


""" This file connects the CLI below with the verb (build/create/etc) interface
    (ProjectDatabase class) interface of the Project above. It
    interfaces with projects and not individual asset classes. """


import os
from _opencpi.assets.abstract2 import *
# IMPORTANT - interface with AssetBase and Project, nothing else
from _opencpi.assets.abstract2 import AssetBase
from _opencpi.assets.project2 import Project, test_Project


class ProjectRegistry():
    """ Component Development Guide section 14.3 """

    def __init__(self):
        self.abs_path = None
        self.projects = []

    def get_project_dependencies_not_registered(self, project):
        registered_projects = []
        non_registered_projects = []
        for registered_project in self.projects:
            pid = str(registered_project.get_package_id())
            registered_projects.append(pid)
        for dep in project.project_dependencies:
            if dep not in registered_projects:
                non_registered_projects.append(dep)
        return non_registered_projects

    def get_abs_path_is_project(self, abs_path):
        """ return whether indicated path is a project """
        ret = False
        if os.path.isfile(abs_path + '/Project.xml'):
            ret = True
        # start pre-2.0 opencpi
        if os.path.isfile(abs_path + '/Project.mk'):
            ret = True
        # end pre-2.0 opencpi
        return ret

    def get_hdl_primitive_project(self, name, worker_project=None):
        """ get project which contains named hdl primitive, where HDL
            Development Guide section 4.4.1 defines the search precedence """
        # TODO make compliant with CDG section 8.1.11
        ret = None
        if worker_project is not None:
            for hdl_primitive in worker_project.hdl_primitives:
                if hdl_primitive.name == name:
                    ret = worker_project
            if ret is None:
                for project in self.projects:
                    if str(project.get_package_id()) == 'ocpi.core':
                        for hdl_primitive in project.hdl_primitives:
                            if hdl_primitive.name == name:
                                ret = project
        if ret is None:
            for project in self.projects:
                for hdl_primitive in project.hdl_primitives:
                    if hdl_primitive.name == name:
                        ret = project
        if ret is None:
            raise_not_found_in_projects('hdl primitive', name)
        return ret

    def get_component_by_name(self, name):
        component = None
        for project in self.projects:
            component = project.get_component_by_name(name)
            if component is not None:
                break
        return component

    def get_list_of_component_strings_by_name_deps(self, name,
                                                   package_dependencies):
        """ get list of package id-qualified name per component found in this
            registry's project, or an empty list if not found """
        ret = []
        for package_id in package_dependencies:
            for project in self.projects:
                if project.get_package_id() == package_id:
                    _list = project.get_list_of_component_strings_by_name(name)
                    ret.extend(_list)
        return ret

    def get_worker_project(self, name, abs_path=None, authoring_model=''):
        """ get project which contains named worker """
        ret = None
        for project in self.projects:
            if project.get_worker_by_name(name, authoring_model) is not None:
                ret = project
        if ret is None:
            raise_not_found_in_projects('worker', name)
        return ret

    def get_hdl_assembly_project(self, name):
        """ get project which contains named assembly """
        ret = None
        for project in self.projects:
            for hdl_assembly in project.hdl_assemblies:
                if hdl_assembly.name == name:
                    ret = project
        if ret is None:
            raise_not_found_in_projects('hdl assembly', name)
        return ret

    def get_abs_path_project(self, abs_path):
        """ get project which contains indicated abs_path """
        ret = None
        for project in self.projects:
            if (project.abs_path + '/') in (abs_path + '/'):
                ret = project
        if ret is None:
            raise_not_found_in_projects('path', abs_path)
        return ret

    def get_core_project_assets(self, _type):
        ret = []
        for project in self.projects:
            if str(project.get_package_id()) == 'ocpi.core':
                if _type == 'hdl adapters':
                    discovery_path = project.abs_path + '/hdl/adapters'
                elif _type == 'hdl devices':
                    discovery_path = project.abs_path + '/hdl/devices'
                for entry in AssetBase.listdir_assets(discovery_path):
                    if '.hdl' in entry:
                        name = entry.split('.')[0]
                        owd_path = discovery_path + '/' + entry + '/' + \
                            name + '.xml'
                        if os.path.isfile(owd_path):
                            for clib in project.component_libraries:
                                for asset in clib.workers:
                                    if asset.get_xml_abs_path() == owd_path:
                                        ret.append(asset.name)
        return ret

    def get_hdl_worker_dependent_workers(self, worker, hdl_platform):
        """ get list of worker objects, across the project registry, on which
            the worker depends, including
            1) subdevice workers (if the worker is a device worker)
            2) device workers in the worker platform configuration (if the
               worker is a platform worker) """
        ret = []
        if worker.authoring_model == 'hdl':
            for project in self.projects:
                for comp_library in project.component_libraries:
                    for potential_subdevice in comp_library.workers:
                        for support in potential_subdevice.supports:
                            if support == worker.name:
                                ret.append(potential_subdevice)
        if worker.name == hdl_platform:
            for project in self.projects:
                for _hdl_platform in project.hdl_platforms:
                    plat_dir_abs_path = _hdl_platform.get_dir_abs_path()
                    if plat_dir_abs_path == worker.get_dir_abs_path():
                        for cfg in _hdl_platform.configurations.values():
                            for dev in cfg.devices:
                                _worker = None
                                proj = self.get_worker_project(dev.name, None,
                                                               'hdl')
                                for clib in proj.component_libraries:
                                    for device in clib.workers:
                                        if device.name == dev.name:
                                            ret.append(device)
                                            break
        return ret

    def discover(self, do_discover_component_libraries=True,
                 do_discover_hdl_primitives=True, local_project=None):
        self.discover_abs_path()
        self.discover_projects(do_discover_component_libraries,
                               do_discover_hdl_primitives, local_project)
        found = False
        for project in self.projects:
            if str(project.get_package_id()) == 'ocpi.core':
                found = True
        if not found:
            Logger().warn('ocpi.core is not registered')

    def discover_abs_path(self):
        ocpi_project_registry_dir = os.environ.get('OCPI_PROJECT_REGISTRY_DIR')
        if ocpi_project_registry_dir is None:
            ocpi_cdk_dir = os.environ.get('OCPI_CDK_DIR')
            if ocpi_cdk_dir is None:
                raise Exception('OpenCPI environment not setup')
            abs_path = ocpi_cdk_dir + '/../project-registry'  # undocumented
        else:
            abs_path = ocpi_project_registry_dir
        self.abs_path = abs_path

    def discover_projects(self, do_component_libraries, do_hdl_primitives,
                          local_project):
        Logger().debug('start of project discovery')
        for _dir in AssetBase.listdir_assets(self.abs_path):
            abs_path = self.abs_path + '/' + _dir
            project_abs_path = os.path.realpath(abs_path)
            if (not os.path.exists(project_abs_path)) or \
                    not (self.get_abs_path_is_project(project_abs_path)):
                name = project_abs_path.split('/')[-1]
                msg = 'registry corrupted for ' + name
                msg += ' project entry (broken symlink: ' + abs_path + ')'
                Logger().warn(msg)
            if self.get_abs_path_is_project(project_abs_path):
                if (local_project is not None) and \
                   (local_project.get_dir_abs_path() == project_abs_path):
                    # append pre-constructed project avoids warning duplication
                    project = local_project
                else:
                    project = Project(project_abs_path)
                    project.discover(do_component_libraries, do_hdl_primitives)
                self.projects.append(project)
        Logger().debug('end of project discovery')

    def get_project_symlink_path(self, project):
        return self.abs_path + '/' + project.get_package_id()

    def register(self, cli_dict, _dir):
        dir_abs_path = _dir
        if cli_dict['name'] is not None:
            dir_abs_path += '/' + cli_dict['name']
        try:
            project = Project(dir_abs_path)  # raises if not a project
        except InvalidAssetError:
            msg = 'project \'' + cli_dict['name'] + '\' does not exist'
            raise InvalidAssetError(msg)
        symlink_path = self.get_project_symlink_path(project)
        if not os.path.islink(symlink_path):
            os.symlink(project.abs_path, symlink_path)

    def unregister(self, cli_dict, _dir):
        self.discover_registered_projects()
        if cli_dict['noun'] == 'project':
            dir_abs_path = _dir
            if cli_dict['name'] is not None:
                dir_abs_path += '/' + cli_dict['name']
            try:
                # raises if not a project
                project = Project(dir_abs_path)
            except InvalidAssetError:
                msg = 'project \'' + cli_dict['name'] + '\' does not exist'
                raise InvalidAssetError(msg)
            symlink_path = self.get_project_symlink_path(project)
            try:
                System('unlink ' + symlink_path)
            except SystemCallError:
                pid = project.get_package_id()
                raise Exception(pid + ' is not registered')

    def get_project(self, cli_dict, _dir):
        project = next((proj for proj in self.projects if
                        (proj.get_dir_abs_path() + '/') in (_dir + '/')), None)
        if project is None:
            project_dir_abs_path = _dir
            while True:
                print(project_dir_abs_path)
                try:
                    project = Project(project_dir_abs_path, None)
                    project.discover()
                    break
                except InvalidAssetError as err:
                    print(str(err))
                    project_dir_abs_path = \
                        project_dir_abs_path.rsplit('/', 1)[0]
                    if len(project_dir_abs_path) <= 1:
                        break
        if project is None:
            msg = ('invalid path: \'' + _dir + '\', please perform \'create '
                   + cli_dict['noun'] + '\' within a valid, registered '
                   'project')
            raise Exception(msg)
        return project

    def dispatch_verb(self, cli_dict):
        """ this method implements functionality common across verbs, then
            dispatches to individual verb calls """
        if cli_dict['help']:
            if cli_dict['verb'] == '':
                os.system('man ocpidev2')
            else:
                os.system('man ocpidev2-' + cli_dict['verb'])
        else:
            dirs_to_operate_on = cli_dict['d'].copy()
            if dirs_to_operate_on == []:
                dirs_to_operate_on.append(Environment().getcwd())
            if cli_dict['verb'] == 'show':
                set_g_suppress_warn(True)
            for _dir in dirs_to_operate_on:
                if not ((cli_dict['verb'] == 'create') and
                   (cli_dict['noun'] == 'library')):
                    msg = 'performing \'' + cli_dict['verb']
                    if cli_dict['noun'] is not None:
                        msg += ' ' + cli_dict['noun']
                    if cli_dict['name'] is not None:
                        msg += ' ' + cli_dict['name']
                    msg += '\''
                    Logger().log(3, msg + ' within directory ' + _dir)
                if cli_dict['verb'] == 'build':
                    self.build(cli_dict, _dir)
                elif cli_dict['verb'] == 'clean':
                    self.clean(cli_dict, _dir)
                elif cli_dict['verb'] == 'create':
                    self.create(cli_dict, _dir)
                elif cli_dict['verb'] == 'delete':
                    self.delete(cli_dict, _dir)
                elif cli_dict['verb'] == 'refresh':
                    Logger().warn('refresh is not necessary in ocpidev2')
                elif cli_dict['verb'] == 'register':
                    self.register(cli_dict, _dir)
                elif cli_dict['verb'] == 'run':
                    self.run(cli_dict, _dir)
                elif cli_dict['verb'] == 'show':
                    self.show(cli_dict, _dir)
                elif cli_dict['verb'] == 'unregister':
                    self.unregister(cli_dict, _dir)
                elif cli_dict['verb'] == 'unittest':
                    unittest(cli_dict, _dir)
                else:
                    raise Exception('verb ' + cli_dict['verb'] +
                                    ' is not supported')
                if (cli_dict['verb'] == 'create') and \
                   (cli_dict['noun'] == 'library'):
                    # this message is printed below and not above due to weird
                    # create components dir message of same form in project2.py
                    # that needs to happen first
                    msg = 'performing \'' + cli_dict['verb']
                    if cli_dict['noun'] is not None:
                        msg += ' ' + cli_dict['noun']
                    if cli_dict['name'] is not None:
                        msg += ' ' + cli_dict['name']
                    msg += '\''
                    Logger().log(3, msg + ' within directory ' + _dir)

    def build(self, cli_dict, _dir):
        """ builds assets by creating a temporary makefile and calls make -j
            on it and then deleting it """
        self.dispatch_verb_for_single_dir(cli_dict, _dir)

    def clean(self, cli_dict, _dir):
        self.dispatch_verb_for_single_dir(cli_dict, _dir)

    def create(self, cli_dict, _dir):
        if cli_dict['name'] is None:
            raise Exception('\'create\' requires a name')
        if cli_dict['keep']:
            Logger().warn('--keep is unnecessary')
        if cli_dict['noun'] == 'registry':
            try:
                System('mkdir -p ' + _dir + '/' + cli_dict['name'])
            except SystemCallError:
                raise Exception('registry already exists')
        elif cli_dict['noun'] == 'project':
            dir_abs_path = _dir + '/' + cli_dict['name']
            Project(dir_abs_path, cli_dict).create()
            if cli_dict['register']:
                self.register(cli_dict, dir_abs_path)
        else:
            self.get_project(cli_dict, _dir).create_asset(cli_dict, _dir)

    def delete(self, cli_dict, _dir):
        if cli_dict['noun'] == 'registry':
            pass
        elif cli_dict['noun'] == 'project':
            dir_abs_path = _dir + '/' + cli_dict['name']
            Project(dir_abs_path, cli_dict).delete()
        else:
            self.get_project(cli_dict, _dir).delete_asset(cli_dict, _dir)
        pass

    def run(self, cli_dict, _dir):
        if not os.path.exists(_dir):
            raise Exception(_dir + ' does not exist')
        cmd = 'make -C ' + Test(_dir).get_dir_abs_path()
        phases = ['run']
        if cli_dict['phase'] != '':
            phases = cli_dict['phase']
        for phase in phases:
            cmd += ' ' + phase
            if cli_dict['keepsimulations']:
                cmd += ' KeepSimulations=1'
            if cli_dict['view']:
                cmd += ' View=1'
            if cli_dict['accumulateerrors']:
                cmd += ' AccumulateErrorlations=1'
            if len(cli_dict['case']) > 0:
                cmd += ' Cases=\''
                for case in cli_dict['case']:
                    cmd += case
                cmd += '\''
            System(cmd)

    def export_projects(self, makefile):
        """ plan_build_exports() must occur before this method is called """
        dependency_ordered_pid_strs = []
        # initial hack to handle circular platform/assets circular dependency
        for proj in self.projects:
            if str(proj.get_package_id()) == 'ocpi.core':
                dependency_ordered_pid_strs.append(str(proj.get_package_id()))
        for proj in self.projects:
            if str(proj.get_package_id()) == 'ocpi.platform':
                dependency_ordered_pid_strs.append(str(proj.get_package_id()))
        for proj in self.projects:
            if str(proj.get_package_id()) == 'ocpi.assets':
                dependency_ordered_pid_strs.append(str(proj.get_package_id()))
        # proper project dependency order, with timeout hack to handle circular
        # dependencies
        timeout = 10000
        while len(dependency_ordered_pid_strs) != \
                len(self.projects):
            if timeout == 0:
                break
            timeout -= 1
            for proj in self.projects:
                deps_covered = True
                for dependent_proj in proj.project_dependencies:
                    if dependent_proj not in dependency_ordered_pid_strs:
                        deps_covered = False
                if deps_covered:
                    if str(proj.get_package_id()) not in \
                            dependency_ordered_pid_strs:
                        dependency_ordered_pid_strs.append(
                                str(proj.get_package_id()))
        # timeout hack to handle circular dependencies,
        # (we gave up on dependency order!)
        if timeout == 0:
            for proj in self.projects:
                if str(proj.get_package_id()) not in \
                        dependency_ordered_pid_strs:
                    somepid = str(proj.get_package_id())
                    dependency_ordered_pid_strs.append(somepid)
        # do the final export in psuedo-dependency-order
        for package_id_str in dependency_ordered_pid_strs:
            for proj in self.projects:
                if str(proj.get_package_id()) == package_id_str:
                    # TODO move below 7 lines outside OCPIDev class (Legacy...)
                    # IMPORTANT - below 6 lines necessary to remove stale files
                    p = proj.abs_path
                    os.system('rm -rf $(find ' + p + ' -type f -name imports)')
                    os.system('rm -rf $(find ' + p + ' -type f -name exports)')
                    os.system('rm -rf $(find ' + p + ' -type d -name imports)')
                    os.system('rm -rf $(find ' + p + ' -type d -name exports)')
                    os.system('rm -rf $(find ' + p + ' -type l -name imports)')
                    os.system('rm -rf $(find ' + p + ' -type l -name exports)')
                    Logger().info(
                        'LegacyBuildTool: exporting project ' +
                        proj.abs_path.split('/')[-1])
                    System('make -f ' + makefile.abs_path + ' ' +
                           proj.abs_path + '/exports')

    # TODO probably a single authoritative xml is needed to parse this from....
    def get_target(self, hdl_platform, rcc_platform=''):
        # TODO parse tools/.../hdl-targets.xml, ml605.mk instead of below code
        ret = hdl_platform
        if rcc_platform == '':
            if hdl_platform == 'zed':
                ret = 'zynq'
            elif hdl_platform == 'zcu106':
                ret = 'zynq_ultra'
            elif hdl_platform == 'zed_ise':
                ret = 'zynq_ise'
            elif hdl_platform == 'zcu104':
                ret = 'zynq_ultra'
            elif hdl_platform == 'zed_ether':
                ret = 'zynq'
            elif hdl_platform == 'ml605':
                ret = 'virtex6'
            elif hdl_platform == 'alst4x':
                ret = 'stratix'
            elif hdl_platform == 'alst4':
                ret = 'stratix'
            elif hdl_platform == 'matchstiq_z1':
                ret = 'zynq'
            elif hdl_platform == 'e31x':
                ret = 'zynq'
            elif hdl_platform == 'zrf8_48dr':
                ret = 'zynq_ultra'
        else:
            ret = rcc_platform
        return ret

    def append_prim_rules_to_makefile_variable(self, asset, hdl_targets,
                                               hdl_platforms, rcc_platforms,
                                               makefile, gnu_make_target_str,
                                               tool):
        bilibs = Project.get_built_in_hdl_libraries()
        first_proj = self.get_hdl_primitive_project(asset.name)
        for name in first_proj.get_hdl_primitive_dependent_libraries(asset):
            project = self.get_hdl_primitive_project(name)
            prim = None
            for hdl_primitive in project.hdl_primitives:
                if hdl_primitive.name == name:
                    prim = hdl_primitive
                    break
            for hdl_platform in hdl_platforms:
                target = get_target(hdl_platform, '')
                ppath = tool.get_build_artifact_abs_path(prim, target,
                                                         hdl_platform, '',
                                                         self)
                makefile.rules[gnu_make_target_str].prerequisites.append(ppath)
                # recursion
                makefile = self.append_asset_rules_to_makefile_variable(
                    prim, [target], [hdl_platform], [], makefile, ppath, tool)
        recipe = tool.get_gnu_make_recipe(asset, hdl_targets, hdl_platforms,
                                          rcc_platforms)
        makefile.rules[gnu_make_target_str].recipe = recipe
        return makefile

    def append_worker_rules_to_makefile_variable(self, asset, hdl_targets,
                                                 hdl_platforms, rcc_platforms,
                                                 makefile, gnu_make_target_str,
                                                 tool):
        """ asset is the worker for which to append the rules """
        wproj = self.get_worker_project(asset.name, None,
                                        asset.authoring_model)
        libs = []
        for lib in wproj.component_libraries:
            for worker in lib.workers:
                if worker.name == asset.name:
                    if worker.authoring_model == asset.authoring_model:
                        libs = wproj.get_hdl_worker_dependent_libraries(
                                lib, asset)
                        break
        for hdl_platform in wproj.hdl_platforms:
            if hdl_platform.worker.name == asset.name:
                if hdl_platform.worker.authoring_model == \
                   asset.authoring_model:
                    libs = wproj.get_hdl_worker_dependent_libraries(
                            lib, asset)
                    break
        for name in libs:
            lproj = self.get_hdl_primitive_project(name, wproj)
            prim = None
            for hdl_primitive in lproj.hdl_primitives:
                if hdl_primitive.name == name:
                    prim = hdl_primitive
                    break
            for platform in (hdl_platforms + rcc_platforms):
                hdl_platform = ''
                rcc_platform = ''
                if platform in hdl_platforms:
                    hdl_platform = platform
                if platform in rcc_platforms:
                    rcc_platform = platform
                target = self.get_target(hdl_platform, rcc_platform)
                ppath = tool.get_build_artifact_abs_path(prim, target,
                                                         hdl_platform,
                                                         rcc_platform, self)
                makefile.rules[gnu_make_target_str].prerequisites.append(ppath)
                # recursion
                hdlp = hdl_platform
                rccp = rcc_platform
                makefile = \
                    self.append_asset_rules_to_makefile_variable(prim,
                                                                 [target],
                                                                 [hdlp],
                                                                 [rccp],
                                                                 makefile,
                                                                 ppath,
                                                                 tool)
        for hdl_platform in hdl_platforms:
            for worker in self.get_hdl_worker_dependent_workers(asset,
                                                                hdl_platform):
                for platform in (hdl_platforms + rcc_platforms):
                    hdl_platform = ''
                    rcc_platform = ''
                    if platform in hdl_platforms:
                        hdl_platform = platform
                    if platform in rcc_platforms:
                        rcc_platform = platform
                    ppath = tool.get_build_artifact_abs_path(worker, target,
                                                             hdl_platform,
                                                             rcc_platform,
                                                             self)
                    gstr = gnu_make_target_str
                    makefile.rules[gstr].prerequisites.append(ppath)
                    # recursion
                    hdlp = hdl_platform
                    rccp = rcc_platform
                    makefile = \
                        self.append_asset_rules_to_makefile_variable(worker,
                                                                     [target],
                                                                     [hdlp],
                                                                     [rccp],
                                                                     makefile,
                                                                     ppath,
                                                                     tool)
        if asset.name == hdl_platform:
            for project in self.projects:
                for _hdl_platform in project.hdl_platforms:
                    if _hdl_platform.worker.get_dir_abs_path() == \
                       worker.get_dir_abs_path():
                        for cfg in _hdl_platform.configurations.values():
                            for dev in cfg.devices:
                                _worker = None
                                project = self.get_worker_project(dev.name,
                                                                  None, 'hdl')
                                for clib in project.component_libraries:
                                    for device in clib.workers:
                                        if device.name == dev.name:
                                            _worker = device
                                            break
                                for platform in (hdl_platforms +
                                                 rcc_platforms):
                                    hdl_platform = ''
                                    rcc_platform = ''
                                    if platform in hdl_platforms:
                                        hdl_platform = platform
                                    target = self.get_target(hdl_platform,
                                                             rcc_platform)
                                    ww = _worker
                                    tt = targetr
                                    hdlp = hdl_platform
                                    wpath = \
                                        tool.get_build_artifact_abs_path(ww,
                                                                         tt,
                                                                         hdlp,
                                                                         self)
                                    mm = makefile
                                    gstr = gnu_make_target_str
                                    mm.rules[gstr].prerequisites.append(wpath)
                                    makefile = mm
                                    # recursion
                                    makefile = \
                                        self.ap_as_ru_to_ma_va(_worker,
                                                               [target],
                                                               [hdl_platform],
                                                               [], makefile,
                                                               wpath, tool)
        recipe = tool.get_gnu_make_recipe(asset, hdl_targets, hdl_platforms,
                                          rcc_platforms)
        makefile.rules[gnu_make_target_str].recipe = recipe
        return makefile

    def ap_as_ru_to_ma_va(self, asset, hdl_targets, hdl_platforms,
                          rcc_platforms, makefile, gnu_make_target_str, tool):
        self.append_asset_rules_to_makefile_variable(asset, hdl_targets,
                                                     hdl_platforms,
                                                     rcc_platforms, makefile,
                                                     gnu_make_target_str, tool)

    def get_hdl_assembly_dependent_workers(self, hdl_assembly, hdl_platform):
        ret = []
        for instance in hdl_assembly.instances:
            ret.append(instance.worker)
        # TODO optimize the below 2 lines per container requirements
        ret += self.get_core_project_assets('hdl adapters')
        ret += self.get_core_project_assets('hdl devices')
        ret.append(hdl_platform)
        for container in hdl_assembly.containers:
            # tmp = (container.platform == hdl_platform)
            # tmp = tmp or (hdl_platform in container.only_platforms)
            # if tmp and (hdl_platform not in container.exclude_platforms):
            for devname, dev in container.devices.items():
                # use the card or platform to disambiguate zero-based ordinal
                # described in PDG section 5.4.4.4
                for project in self.projects:
                    search_list = None
                    if dev.card is None:
                        search_list = project.hdl_platforms
                    else:
                        search_list = project.hdl_cards
                    for entry in search_list:
                        for key, val in entry.devices.items():
                            if key == devname:
                                ret.append(val)
        msg = 'for assembly ' + hdl_assembly.name
        msg += ', got dependent workers ' + str(ret)
        Logger().debug(msg)
        return ret

    def append_hdl_assembly_rules_to_makefile_variable(self, hdl_assembly,
                                                       hdl_targets,
                                                       hdl_platforms,
                                                       rcc_platforms, makefile,
                                                       gnu_make_target_str,
                                                       tool):
        for project in self.projects:
            if project.get_assets_within(hdl_assembly.abs_path) != []:
                local_project = project
                break
        for hdl_platform in hdl_platforms:
            for name in self.get_hdl_assembly_dependent_workers(
                    hdl_assembly, hdl_platform):
                # order in CDG section 14.8 is enforced
                worker = local_project.get_worker_by_name(name, 'hdl')
                if worker is None:
                    for dir_abs_path in Environment().ocpi_project_path:
                        proj = Project(dir_abs_path).get_worker_by_name(name,
                                                                        'hdl')
                        worker = proj.get_worker_by_name(name, 'hdl')
                        if worker is not None:
                            break
                if worker is None:
                    project = self.get_worker_project(name, None, 'hdl')
                    worker = project.get_worker_by_name(name, 'hdl')
                target = self.get_target(hdl_platform, '')
                wpath = tool.get_build_artifact_abs_path(worker, target,
                                                         hdl_platform, '',
                                                         self)
                makefile.rules[gnu_make_target_str].prerequisites.append(wpath)
                # recursion
                hdlp = hdl_platform
                makefile = \
                    self.append_asset_rules_to_makefile_variable(worker,
                                                                 [target],
                                                                 [hdlp],
                                                                 [], makefile,
                                                                 wpath, tool)
            recipe = tool.get_gnu_make_recipe(hdl_assembly, hdl_targets,
                                              hdl_platforms, rcc_platforms)
            makefile.rules[gnu_make_target_str].recipe = recipe

    def append_project_rules_to_makefile_variable(self, asset, hdl_targets,
                                                  hdl_platforms, rcc_platforms,
                                                  makefile,
                                                  gnu_make_target_name, tool):
        recipe = tool.get_gnu_make_recipe(asset, hdl_targets, hdl_platforms,
                                          rcc_platforms)
        makefile.rules[gnu_make_target_name].recipe = recipe
        return makefile

    def append_application_rules_to_makefile_variable(self, asset, hdl_targets,
                                                      hdl_platforms,
                                                      rcc_platforms,
                                                      makefile,
                                                      gnu_make_target_name, tool):
        recipe = tool.get_gnu_make_recipe(asset, hdl_targets, hdl_platforms,
                                          rcc_platforms)
        makefile.rules[gnu_make_target_name].recipe = recipe
        return makefile

    def append_asset_rules_to_makefile_variable(self, asset, hdl_targets,
                                                hdl_platforms, rcc_platforms,
                                                makefile, gnu_make_target_str,
                                                tool):
        """ here the CDG section 4.2 heirarchy is automated """
        # target = get_target(hdl_platform, rcc_platform)
        makefile.rules[gnu_make_target_str] = GNUMakeRule()
        target = GNUMakeTarget(gnu_make_target_str)
        makefile.rules[gnu_make_target_str].targets.append(target)
        if asset.get_type() == 'application':
            makefile = self.append_application_rules_to_makefile_variable(
                    asset, hdl_targets, hdl_platforms, rcc_platforms,
                    makefile, gnu_make_target_str, tool)
        if asset.get_type() == 'hdl primitive':
            makefile = self.append_prim_rules_to_makefile_variable(
                    asset, hdl_targets, hdl_platforms, rcc_platforms,
                    makefile, gnu_make_target_str, tool)
        if (asset.get_type() == 'hdl worker') or \
           (asset.get_type() == 'rcc worker'):
            makefile = self.append_worker_rules_to_makefile_variable(
                    asset, hdl_targets, hdl_platforms, rcc_platforms,
                    makefile, gnu_make_target_str, tool)
        if asset.get_type() == 'hdl assembly':
            self.append_hdl_assembly_rules_to_makefile_variable(
                    asset, hdl_targets, hdl_platforms, rcc_platforms,
                    makefile, gnu_make_target_str, tool)
        if asset.get_type() == 'project':
            makefile = self.append_project_rules_to_makefile_variable(
                    asset, hdl_targets, hdl_platforms, rcc_platforms,
                    makefile, gnu_make_target_str, tool)
        Logger().debug('creating make rule: ' +
                       str(makefile.rules[gnu_make_target_str]))
        return makefile

    def throw_if_project_dependencies_not_registered(project):
        unreg_projects = self.get_project_dependencies_not_registered(project)
        if len(unreg_projects) != 0:
            msg = 'the following project dependencies are not registered: '
            for unreg_project in unreg_projects:
                msg += unreg_project + ' '
            raise Exception(msg)

    def install_rcc_platform_if_not_installed(self, rcc_platform):
        for project in self.projects:
            if project.get_package_id() == 'ocpi.core':
                tmp_path = project.abs_path + '/rcc/platforms/'
                if not os.path.isdir(tmp_path + rcc_platform + '/gen'):
                    System('ocpiadmin install platform ' + rcc_platform)

    def clean_imports_exports(self):
        """ TODO is this class the right place for this? """
        for proj in self.projects:
            tmp = 'rm -rf $(find ' + proj.get_dir_abs_path()
            System(tmp + ' -type f -name imports)')
            System(tmp + ' -type f -name exports)')
            System(tmp + ' -type d -name imports)')
            System(tmp + ' -type d -name exports)')
            System(tmp + ' -type l -name imports)')
            System(tmp + ' -type l -name exports)')

    def plan_build_exports(self, makefile, tool):
        """ necessary prerequisite to export_projects() """
        for project in self.projects:
            gnu_make_target_str = \
                tool.get_build_artifact_abs_path(project, '', '', '', self)
            # set targets/platforms empty to only export and not build assets
            tar = gnu_make_target_str
            makefile = \
                self.append_asset_rules_to_makefile_variable(project, [], [],
                                                             [], makefile,
                                                             tar, tool)
        return makefile

    def plan_build(self, assets, hdl_targets, hdl_platforms,
                   rcc_platforms, fs, tool):
        Logger().info('planning build (gathering dependencies)')
        makefile = GNUMakefile(None)
        makefile.abs_path = fs.abs_path + '/Makefile'
        makefile.rules['all'] = GNUMakeRule()
        makefile.rules['all'].targets.append(GNUMakeTarget('all', True))
        makefile = self.plan_build_exports(makefile, tool)
        for asset in assets:
            artifact_list = hdl_targets + hdl_platforms + rcc_platforms
            for artifact_list_entry in artifact_list:
                hdl_target = ''
                hdl_platform = ''
                rcc_platform = ''
                if artifact_list_entry in hdl_targets:
                    hdl_target = artifact_list_entry
                if artifact_list_entry in hdl_platforms:
                    hdl_platform = artifact_list_entry
                if artifact_list_entry in rcc_platforms:
                    rcc_platform = artifact_list_entry
                gnu_make_target_str = \
                    tool.get_build_artifact_abs_path(asset, hdl_target,
                                                     hdl_platform,
                                                     rcc_platform, self)
                makefile.rules['all'].prerequisites.append(gnu_make_target_str)
                makefile = self.append_asset_rules_to_makefile_variable(
                    asset, hdl_targets, hdl_platforms,
                    rcc_platforms, makefile, gnu_make_target_str, tool)
        return makefile

    def execute_build(self, hdl_targets, hdl_platforms, rcc_platforms, fs,
                      makefile, _j, tool):
        # self.throw_if_project_dependencies_not_registered(project)
        self.clean_imports_exports()
        Logger().info('executing build')
        os.system('mkdir -p ' + fs.abs_path)
        makefile.emit()
        # System('cat ' + makefile.abs_path)
        self.export_projects(makefile)
        for rcc_platform in rcc_platforms:
            self.install_rcc_platform_if_not_installed(rcc_platform)
        cmd = 'make -f ' + makefile.abs_path
        if _j > 1:
            cmd += ' -j ' + str(_j)
        System(cmd)
        self.clean_imports_exports()


class ProjectDatabase(ProjectRegistry):
    """ This class represents all projects on which actions can be performed,
        regardless of whether they are registered or not. The list of projects
        is inherited from ProjectRegistry, and potentially expanded to include
        local project, if the local project is unregistered """

    def __init__(self):
        ProjectRegistry.__init__(self)
        # -1 indicates not local project has been assigned to self.projects yet
        self.local_project_idx = -1
        self.local_project_is_registered = False

    @staticmethod
    def is_worker(noun):
        return Project.is_worker(noun)

    @staticmethod
    def is_hdl(noun):
        return Project.is_hdl(noun)

    @staticmethod
    def is_rcc(noun):
        return Project.is_rcc(noun)

    @staticmethod
    def get_asset_for_create(noun):
        return Project.get_asset_for_create(noun)

    def discover_local_project(self, _dir):
        project_dir_abs_path = _dir
        while True:
            try:
                local_project = Project(project_dir_abs_path)
                for (idx, project) in enumerate(self.projects):
                    if project.get_dir_abs_path() == \
                       local_project.get_dir_abs_path():
                        self.local_project_is_registered = True
                        self.local_project_idx = idx
                if not self.local_project_is_registered:
                    local_project.discover()
                    self.projects.append(local_project)
                    self.local_project_idx = len(self.projects)-1
                Logger().debug('operating in local project ' +
                               local_project.get_dir_abs_path())
                break
            except InvalidAssetError:
                project_dir_abs_path = project_dir_abs_path.rsplit('/', 1)[0]
                if len(project_dir_abs_path) <= 1:
                    break

    def discover_registered_projects(self):
        ProjectRegistry.discover(self, True, True)

    def create(self, cli_dict, _dir):
        if cli_dict.get('component'):
            self.discover_registered_projects()  # for warnings
        self.discover_local_project(_dir)
        if (cli_dict['verb'] == 'create') and \
           (cli_dict['noun'] == 'test'):
            spec = cli_dict['name']  # default
            if cli_dict['component']:
                spec = cli_dict['component']
            c_strs = self.get_list_of_component_strings_by_name(spec)
            if len(c_strs) == 0:
                Logger().warn('spec ' + spec + ' not found')
            elif len(c_strs) > 1:
                msg = 'multiple component specs found, \'' + c_strs[0]
                msg += '\' will be used but others were also found: '
                msg += ', '.join(c_strs[1:])
                Logger().warn(msg)
        if self.local_project_idx == -1:
            ProjectRegistry.create(self, cli_dict, _dir)
        else:
            local_project = self.projects[self.local_project_idx]
            local_project.create_asset(cli_dict, _dir)

    def get_list_to_show(self, cli_dict, first, _type, asset, project,
                         list_to_show, json_dict):
        pid = str(project.get_package_id())
        if (_type == 'component') or (_type.endswith('worker')) or \
           (_type == 'component library'):
            for component_library in project.component_libraries:
                cl = component_library
                p = project.get_component_library_package_id(cl)
                if (asset in component_library.components) or \
                   (asset in component_library.workers) or \
                   (asset == cl):
                    pid = p
                    break
        pid_and_name = pid
        if (not cli_dict['noun'].startswith('project')) and \
           (not cli_dict['noun'].startswith('librar')):
            pid_and_name += '.' + asset.name
        msg = ''
        if first and cli_dict['simple']:
            msg += ' '
        msg += pid_and_name
        if cli_dict['noun'].startswith('target'):
            msg = asset.name + '.rcc'
        if Project.is_worker(cli_dict['noun']):
            msg += '.' + asset.authoring_model
        if cli_dict['noun'].startswith('platform'):
            if type(asset) == 'hdl platform':
                msg += '.hdl'
            if type(asset) == 'rcc platform':
                msg += '.rcc'
        if cli_dict['verbose'] or cli_dict['table']:
            if not cli_dict['noun'].startswith('target'):
                # an hdl target, for example, is not an asset
                # with an associated directory
                msg += ' '
                for idx in range(60-len(msg)):
                    msg += ' '
                msg += asset.abs_path
        json_dict[pid_and_name] = {'package_id': pid}
        if not cli_dict['noun'].startswith('target'):
            # an hdl target, for example, is not an asset
            # with an associated directory
            json_dict[pid_and_name]['directory'] = \
                asset.get_dir_abs_path()
        if not cli_dict['json']:
            if msg not in list_to_show:
                list_to_show.append(msg)
        return (list_to_show, json_dict)

    def filter_assets(self, cli_dict, assets,
                      assets_on_which_verb_will_be_performed, project, _type,
                      list_to_show=[], json_dict={}):
        """" assets                                 input assets being filtered
             assets_on_which_verb_will_be_performed in/out final list being
                                                    built up """
        first = True
        for asset in assets:
            passed_any_name_checks = (cli_dict['name'] is None) or \
                    (cli_dict['name'] == asset.name)
            if passed_any_name_checks:
                passed_any_dir_checks = (cli_dict['d'] == []) or \
                        any([(_dir + '/') in (asset.abs_path + '/') for _dir in
                            cli_dict['d']])
                if passed_any_dir_checks:
                    containing_path = \
                        asset.get_dir_abs_path().rsplit('/', 1)[0]
                    if cli_dict['noun'].startswith('librar'):
                        is_hdl = containing_path.endswith('hdl') or \
                                 containing_path.split('/')[-3] == 'hdl'
                    else:
                        hdlp = 'hdl/primitives'
                        is_hdl = containing_path.endswith('hdl/adapters') or \
                            containing_path.endswith('hdl/cards') or \
                            containing_path.endswith('hdl/devices') or \
                            containing_path.endswith(hdlp) or \
                            containing_path.endswith('hdl/platforms')
                    passed_any_hdl_checks = True
                    if (cli_dict['authoringmodel'] == 'hdl'):
                        passed_any_hdl_checks = \
                            (asset.get_type() == 'hdl adapter') or \
                            (asset.get_type() == 'hdl assembly') or \
                            (asset.get_type() == 'hdl card') or \
                            (asset.get_type() == 'hdl device') or \
                            (asset.get_type() == 'hdl librar') or \
                            (asset.get_type() == 'hdl primitive') or \
                            (asset.get_type() == 'hdl primitive core') or \
                            (asset.get_type() == 'hdl platform') or \
                            (asset.get_type() == 'hdl slot') or \
                            (asset.get_type() == 'hdl target') or \
                            (asset.get_type() == 'hdl worker')
                    elif (cli_dict['authoringmodel'] == 'rcc'):
                        passed_any_hdl_checks = \
                            (asset.get_type() == 'rcc worker') or \
                            (asset.get_type() == 'rcc platform')
                    if cli_dict['noun'].startswith('librar'):
                        passed_any_hdl_checks = True
                    passed_any_device_checks = \
                        (not cli_dict['noun'].startswith('device')) or \
                        (cli_dict['noun'].startswith('device') and
                         asset.is_device)
                    passed_any_adapter_checks = \
                        (not cli_dict['noun'].startswith('adapter')) or \
                        (cli_dict['noun'].startswith('adapter') and
                         containing_path.endswith('hdl/adapters'))
                    if passed_any_hdl_checks and \
                            passed_any_device_checks and \
                            passed_any_adapter_checks:
                        assets_on_which_verb_will_be_performed.append(asset)
                        if cli_dict['verb'] == 'show':
                            (list_to_show, json_dict) = self.get_list_to_show(
                                cli_dict, first, _type, asset, project,
                                list_to_show, json_dict)
                        first = False
        return [json_dict, assets_on_which_verb_will_be_performed,
                list_to_show]

    def get_assets_on_which_verb_will_be_performed(self, cli_dict, _dir):
        """ for single directory (either working directory or a singel -d
            option, retrieve list of assets on which the verb will be
            performed """
        ret = []
        for (idx, project) in enumerate(self.projects):
            if (cli_dict['noun'] is not None) and \
               (cli_dict['noun'].startswith('project')):
                if not self.local_project_is_registered:
                    if idx == self.local_project_idx:
                        msg = project.get_name() + ' is not registered'
                        set_g_suppress_warn(False)
                        Logger().warn(msg)
                        set_g_suppress_warn(True)
            if cli_dict['d'] == []:
                _dir = project.get_dir_abs_path()
            assets = project.get_assets_within(_dir)
            if cli_dict['noun'] is None:
                ret.extend(assets)
            else:
                for _type in Project.get_types_from_cli_dict(cli_dict):
                    assets_of_type = project.get_assets_of_type(_type)
                    [_, ret, _] = self.filter_assets(cli_dict, assets_of_type,
                                                     ret, project, _type)
        return ret

    def dispatch_verb_for_single_dir(self, cli_dict, _dir):
        """ only 'build' and 'clean' and 'show' verbs for now """
        if not os.path.exists(_dir):
            raise Exception(_dir + ' does not exist')
        if cli_dict['globalscope'] and (not cli_dict['localscope']):
            self.discover_registered_projects()
        self.discover_local_project(_dir)
        assets = self.get_assets_on_which_verb_will_be_performed(cli_dict,
                                                                 _dir)
        if (len(assets) == 0):
            if ((cli_dict['noun'] is not None) and
                    (not cli_dict['noun'].endswith('s')) and
                    (not cli_dict['noun'].startswith('target')) and
                    (not cli_dict['noun'].startswith('registry'))):
                msg = 'could not find '
                msg += cli_dict['noun'] + ' \'' + cli_dict['name'] + '\''
                raise Exception(msg)
        if (len(assets) > 1) and \
           (cli_dict['noun'] is not None) and \
           (not cli_dict['noun'].endswith('s')):
            msg = 'multiple entries found for '
            msg += cli_dict['noun'] + ' \'' + cli_dict['name']
            msg += '\''
            raise Exception(msg)
        if cli_dict['verb'] == 'build':
            # TODO support cli_dict extension (override) of this tool
            tool = LegacyBuildTool()
            fs = TemporaryFilesystem()
            makefile = self.plan_build(assets, cli_dict['hdltarget'],
                                       cli_dict['hdlplatform'],
                                       cli_dict['rccplatform'], fs, tool)
            self.execute_build(cli_dict['hdltarget'],
                               cli_dict['hdlplatform'],
                               cli_dict['rccplatform'], fs,
                               makefile, cli_dict['j'], tool)
        elif cli_dict['verb'] == 'clean':
            cleaned = False
            if cli_dict['noun'] is None:
                for project in self.projects:
                    if (project.abs_path + '/') in (_dir + '/'):
                        Project.clean(_dir)
                        cleaned = True
            else:
                for asset in assets:
                    Project.clean(asset.get_dir_abs_path())
                    cleaned = True
            if not cleaned:
                msg = 'cannot clean directory \'' + _dir + '\' not in a project'
                raise Exception(msg)
        elif cli_dict['verb'] == 'show':
            list_to_show = []
            json_dict = {}
            if cli_dict['globalscope']:
                msg = '--global-scope does not change behavior, '
                msg += 'see man ocpidev2-show'
                Logger().warn(msg)
            if cli_dict['noun'] == 'registry':
                if cli_dict['json']:
                    json_dict[self.abs_path] = {'directory': self.abs_path}
                else:
                    list_to_show = [self.abs_path]
            else:
                if (cli_dict['noun'] is not None) and \
                   (cli_dict['noun'].startswith('target') and
                   ((cli_dict['authoringmodel'] == '') or
                        (cli_dict['authoringmodel'] == 'hdl'))):
                    for target in ['zynq', 'zynq_ultra', 'zynq_ise', 'virtex6',
                                   'stratix']:
                        if (cli_dict['name'] is None) or \
                           (cli_dict['name'] == target):
                            print(target + '.hdl')
                for project in self.projects:
                    for _type in Project.get_types_from_cli_dict(cli_dict):
                        project_assets = []
                        for asset in assets:
                            if (project.get_dir_abs_path() + '/') in \
                               (asset.get_dir_abs_path() + '/'):
                                project_assets.append(asset)
                        [json_dict, _, list_to_show] = self.filter_assets(
                            cli_dict, project_assets, [], project, _type,
                            list_to_show, json_dict)
            if cli_dict['json']:
                print(str(json_dict))
            else:
                # the list is sorted so that assets are generally
                # printed in order of project...component
                # library... etc
                if len(list_to_show) > 0:
                    sep = ' ' if cli_dict['simple'] else '\n'
                    end = '' if cli_dict['simple'] else '\n'
                    print(*sorted(list_to_show), sep=sep, end=end)
                if cli_dict['simple']:
                    print('')

    def show(self, cli_dict, _dir):
        self.dispatch_verb_for_single_dir(cli_dict, _dir)

    def get_list_of_component_strings_by_name(self, spec):
        """ get list of package id-qualified names of components in the order
            order defined in CDG section 14.8 """
        local_project = self.projects[self.local_project_idx]
        c_strs = local_project.get_list_of_component_strings_by_name(spec)
        if len(c_strs) > 1:
            msg = 'multiple component specs matched name \'' + spec
            msg += '\' in the local project: ' + ', '.join(c_strs)
            Logger().warn(msg)
            c_strs = [c_strs[0]]
        else:
            deps = local_project.attrs['ProjectDependencies']
            tmp = self.get_list_of_component_strings_by_name_deps(spec, deps)
            c_strs.extend(tmp)
        return c_strs


class LegacyBuildTool():
    """ Relies (internally) on imports/exports. Intended to possibly,
        eventually, be overridden by user-defined, vendor-specific tool python
        files/classes """

    def get_make_build_str(self, cmd, _list, var):
        if len(_list) > 0:
            cmd += ' ' + var + '=\''
            first = True
            for entry in _list:
                if not first:
                    cmd += ' '
                first = False
                cmd += entry
            cmd += '\''
        return cmd

    def get_mk_filename(self, asset):
        ret = ''
        if asset.get_type() == 'application':
            ret = 'application.mk'
        if asset.get_type() == 'hdl primitive':
            ret = 'hdl/hdl-library.mk'
        if (asset.get_type() == 'hdl worker') or \
           (asset.get_type() == 'rcc worker'):
            ret = 'worker.mk'
        if asset.get_type() == 'hdl assembly':
            ret = 'hdl/hdl-assembly.mk'
        if asset.get_type() == 'project':
            ret = 'project.mk'
        return ret

    def get_build_artifact_extension(self, hdl_target='',
                                     rcc_platform='', is_assembly=False):
        # TODO better separate this into target-specific class/API
        ret = 'bitz' if is_assembly else 'edf'
        if hdl_target.startswith('virtex') or hdl_target.startswith('stratix'):
            ret = 'sof' if is_assembly else 'qsf'
        return ret

    def get_build_artifact_abs_path(self, asset, hdl_target,
                                    hdl_platform, rcc_platform,
                                    project_registry):
        """ intended to be a standard API which defines how an asset is built
            using this Tool class """
        if hdl_platform != '':
            hdl_target = project_registry.get_target(hdl_platform,
                                                     rcc_platform)
        ret = asset.get_dir_abs_path()
        tmp = ''
        if asset.get_type() == 'project':
            ret += '/exports'
        else:
            if asset.get_type() == 'hdl assembly':
                tmp = asset.name + '_' + hdl_platform + '_'
                if len(asset.containers) == 0:
                    tmp += 'base_'
                else:
                    if asset.containers[0].attrs['Config'] == '':
                        tmp += 'base_'
                    else:
                        tmp += asset.containers[0].attrs['Config'] + '_'
                    tmp += asset.containers[0].name
                ret += '/container-' + tmp + '_'
            ret += '/target-' + hdl_target + '/'
            ret += asset.name
            asm = True
            if (asset.get_type() == 'hdl primitive') or \
               (asset.get_type() == 'hdl worker') or \
               (asset.get_type() == 'rcc worker'):
                asm = False
            if (asset.get_type() == 'hdl assembly'):
                ret += tmp + '_rv'
            ext = self.get_build_artifact_extension(hdl_target, rcc_platform,
                                                    asm)
            ret += '.' + ext
        return ret

    def get_gnu_make_recipe(self, asset, hdl_targets=[], hdl_platforms=[],
                            rcc_platforms=[]):
        """ intended to be a standard API which defines how an asset is built
            using this Tool class """
        cmd = 'make -C ' + asset.get_dir_abs_path()
        if not os.path.exists(asset.get_dir_abs_path() + '/Makefile'):
            cmd += ' -f ' + Environment().ocpi_cdk_dir
            cmd += '/include/' + self.get_mk_filename(asset)
        cmd = self.get_make_build_str(cmd, hdl_targets, 'HdlTargets')
        cmd = self.get_make_build_str(cmd, hdl_platforms, 'HdlPlatforms')
        cmd = self.get_make_build_str(cmd, rcc_platforms, 'RccPlatforms')
        return cmd


def unittest(cli_dict, project_registry):
    ret = True
    ret = test_ProjectRegistry(ret)
    ret = test_Project(ret)
    if not ret:
        raise Exception('unittest failed')


def test_ProjectRegistry(ret):
    passed = True
    try:
        project_registry = ProjectRegistry()
    except InvalidAssetError:
        passed = False
    log_pass_fail('testing ProjectRegistry', passed)
    if passed is False:
        ret = False
    return ret
