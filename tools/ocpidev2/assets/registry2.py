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
                    project = Project(project_abs_path, False)
                    project.discover(do_component_libraries, do_hdl_primitives)
                self.projects.append(project)
        Logger().debug('end of project discovery')

    def register(self, cli_dict, _dir):
        project = Project(_dir, False)  # raises if not a project
        symlink_path = self.abs_path + '/' + str(project.get_package_id())
        if not os.path.islink(symlink_path):
            os.symlink(project.abs_path, symlink_path)

    def unregister_project(self, _dir):
        project = Project(_dir, False)  # raises if not a project
        pid = str(project.get_package_id())
        try:
            System('unlink ' + self.abs_path + '/' + pid)
        except SystemCallError:
            raise Exception(pid + ' is not registered')

    def get_assets(self, _dir):
        assets = []
        for project in self.projects:
            if (_dir + '/') in (project.get_dir_abs_path() + '/'):
                assets.extend(project.get_assets_within(_dir))
        return assets

    def get_project(self, cli_dict, _dir):
        project = next((proj for proj in self.projects if
                        (proj.get_dir_abs_path() + '/') in (_dir + '/')), None)
        if project is None:
            project_dir_abs_path = _dir
            while True:
                try:
                    project = Project(project_dir_abs_path, True)
                    project.discover()
                    break
                except InvalidAssetError:
                    project_dir_abs_path = \
                        project_dir_abs_path.rsplit('/', 1)[0]
                    if len(project_dir_abs_path) <= 1:
                        break
        if project is None:
            msg = ("Invalid path: '" + _dir + "'. Please perform 'create "
                   + cli_dict['noun'] + "' within a valid, registered "
                   "project.")
            raise Exception(msg)
        return project

    def build(self, cli_dict, _dir):
        """ builds assets by creating a temporary makefile and calls make -j
            on it and then deleting it """
        if not os.path.exists(_dir):
            raise Exception(_dir + ' does not exist')
        # TODO support cli_dict extension (override) of this tool
        tool = LegacyBuildTool()
        fs = TemporaryFilesystem()
        assets = self.get_assets(_dir)
        makefile = self.plan_build(assets, cli_dict['hdltarget'],
                                   cli_dict['hdlplatform'],
                                   cli_dict['rccplatform'], fs, tool)
        self.execute_build(cli_dict['hdltarget'], cli_dict['hdlplatform'],
                           cli_dict['rccplatform'], fs,
                           makefile, cli_dict['j'], tool)

    def clean(self, cli_dict, _dir):
        if not os.path.exists(_dir):
            raise Exception(_dir + ' does not exist')
        cleaned = False
        for project in self.projects:
            if (project.abs_path + '/') in (_dir + '/'):
                project.clean(_dir)
                cleaned = True
        if not cleaned:
            raise Exception('cannot clean directory not in registered project')

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
            Project(dir_abs_path, False, cli_dict).create()
            if cli_dict['register']:
                self.register_project(dir_abs_path)
        else:
            self.get_project(cli_dict, _dir).create_asset(cli_dict, _dir)

    def delete(self, cli_dict, _dir):
        if cli_dict['noun'] == 'registry':
            pass
        elif cli_dict['noun'] == 'project':
            dir_abs_path = _dir + '/' + cli_dict['name']
            Project(dir_abs_path, False, cli_dict).delete()
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
                cmd += " Cases='"
                for case in cli_dict['case']:
                    cmd += case
                cmd += "'"
            System(cmd)

    def show(self, cli_dict):
        if cli_dict['noun'] == 'registry':
            print(self.abs_path)
        else:
            json_dict = {}
            for project in self.projects:
                json_dict = project.show(cli_dict, json_dict)
            if cli_dict['simple']:
                print('')
            if cli_dict['json']:
                print(str(json_dict))

    def unregister(self, cli_dict, _dir):
        if cli_dict['noun'] == 'project':
            self.unregister_project(_dir)

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

    def append_asset_rules_to_makefile_variable(self, asset, hdl_targets,
                                                hdl_platforms, rcc_platforms,
                                                makefile, gnu_make_target_str,
                                                tool):
        """ here the CDG section 4.2 heirarchy is automated """
        # target = get_target(hdl_platform, rcc_platform)
        makefile.rules[gnu_make_target_str] = GNUMakeRule()
        target = GNUMakeTarget(gnu_make_target_str)
        makefile.rules[gnu_make_target_str].targets.append(target)
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
                msg += unreg_project + " "
            raise Exception(msg)

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
        for rcc_platform in rcc_platforms:
            self.install_rcc_platform_if_not_installed(rcc_platform)
        makefile.emit()
        # System('cat ' + makefile.abs_path)
        self.export_projects(makefile)
        cmd = 'make -f ' + makefile.abs_path
        if _j > 1:
            cmd += ' -j ' + str(_j)
        System(cmd)
        self.clean_imports_exports()


class LegacyBuildTool():
    """ Relies (internally) on imports/exports. Intended to possibly,
        eventually, be overridden by user-defined, vendor-specific tool python
        files/classes """

    def get_make_build_str(self, cmd, _list, var):
        if len(_list) > 0:
            cmd += ' ' + var + "='"
            first = True
            for entry in _list:
                if not first:
                    cmd += ' '
                first = False
                cmd += entry
            cmd += "'"
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
