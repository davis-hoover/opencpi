#!/usr/bin/python3

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
import argparse
import signal
from _opencpi.assets.abstract2 import *
from _opencpi.assets.registry2 import ProjectRegistry
# below is for unittests
from _opencpi.assets.component2 import *
from _opencpi.assets.library2 import *
from _opencpi.assets.primitive2 import *
from _opencpi.assets.project2 import *
from _opencpi.assets.worker2 import *
from _opencpi.assets.assembly2 import *
from _opencpi.assets.platform2 import *
from _opencpi.assets.test2 import *


def mysigint(sig, frame):
    raise Exception('Ctrl-C stopped execution')


class OCPIDev():
    """ Component Development Guide section 15 """

    def __init__(self, hdl_build_tool):
        self.hdl_build_tool = hdl_build_tool

    def create(self, _dir ,cli_dict):
        _dir = os.path.abspath(_dir)
        cwd = os.getcwd()
        if cli_dict is not None:
            # The below line supports create, removes underscores to make CLI
            # look like attrs
            cli_dict = (
                {key.replace('_', '') : val for key, val in cli_dict.items()}
            )
        if args.noun == 'project':
            abs_path = cwd + '/' + args.name
            Project(abs_path, False, cli_dict).create()
        else:
            # Check path is a valid registered project directory
            project_registry = ProjectRegistry()
            project = next((proj for proj in project_registry.projects if
                            proj.abs_path + '/' in _dir + '/'), None)
            if project is None:
                raise Exception('Please perform create ' + args.noun + ' in a '
                                'registered project directory')
            if args.noun == 'library':
                component_lib_path = _dir + '/' + args.name
                ComponentLibrary(
                    component_lib_path, False, cli_dict
                ).create(project, _dir)
            if args.noun in ['component', 'test']:
                # Check path is a valid component library directory
                valid_path = any(_dir == lib.abs_path for lib in
                                 project.component_libraries)
                if not valid_path:
                    raise Exception('Please perform create ' + args.noun +
                                    ' in a valid component library')
                if args.noun == 'component':
                    component_path = (
                        _dir + '/' + args.name + '.comp' + '/' + args.name +
                        '-comp.xml'
                    )
                    package_id = project.get_package_id()
                    Component(
                        component_path, False, cli_dict
                    ).create(package_id)
                if args.noun == 'test':
                    test_path = _dir + '/' + args.name + '.test'
                    # If --component arg used, check for component existence
                    if cli_dict['component']:
                        comp_to_search = cli_dict['component']
                        components = []
                        for project in project_registry.projects:
                            for component in project.components:
                                components.append(component)
                            for comp_lib in project.component_libraries:
                                for component in comp_lib.components:
                                    components.append(component)
                        valid_comp = any(comp_to_search == comp.name for comp in components)
                        if not valid_comp:
                            msg = ('The component ' + cli_dict['component'] +
                                   ' does not exist within any of the '
                                   'registered projects')
                            raise Exception(msg)
                    # If --component not used, check for the component in path
                    else:
                        valid_create_test = False
                        for ext in ['.rcc', '.hdl', '.comp']:
                            if os.path.exists(_dir + '/' + args.name + ext):
                                 valid_create_test = True
                        if not valid_create_test:
                            raise Exception('A ' + args.name + ' component does '
                                            'not yet exist to create a unit-test '
                                            'for')
                    Test(test_path, False, cli_dict).create()

    def delete(self, noun):
        raise Exception('delete is not supported at this time')

    def throw_if_project_dependencies_not_registered(
            self, project, project_registry):
        unreg_projects = (project_registry.
                          get_project_dependencies_not_registered(project))
        if len(unreg_projects) != 0:
            msg = "Project Registry incomplete, please register project(s): "
            for unreg_project in unreg_projects:
                msg += unreg_project + " "
            raise Exception(msg)

    def install_rcc_platform_if_not_installed(
            self, project_registry, rcc_platform):
        for proj in project_registry.projects:
            if str(proj.get_package_id()) == 'ocpi.core':
                tmp_path = proj.abs_path + '/rcc/platforms/'
                if not os.path.isdir(tmp_path + rcc_platform + '/gen'):
                    if os.system('ocpiadmin install platform ' + rcc_platform) != 0:
                        raise Exception('failed to build rcc platform ' + rcc_platform)

    def throw_if_not_installed(self, platform):
        ocpi_cdk_dir = os.environ.get('OCPI_CDK_DIR')
        if platform is not None:
            if not os.path.isdir(ocpi_cdk_dir + '/' + platform):
                raise Exception('platform ' + platform + ' is not installed')

    def build(self, noun, hdl_target, hdl_platform, rcc_platform, _dir, _j):
        if (hdl_target != '') or (hdl_platform != ''):
            if os.environ.get('XILINX_VIVADO') is not None:
                msg = 'cannot run ocpidev2 when Vivado environment is sourced'
                raise Exception(msg)
        if rcc_platform != '':
            self.throw_if_not_installed(rcc_platform)
        # if hdl_platform is not None:
        #     self.throw_if_not_installed(hdl_platform)
        project_registry = ProjectRegistry()
        abs_path = os.path.abspath(_dir)
        project = None
        assets_to_build = []
        for project2 in project_registry.projects:
            if project2.abs_path == os.path.realpath(abs_path):
                project = project2
        if project is None:
            project = project_registry.get_abs_path_project(abs_path)
            asset = project.get_asset(abs_path)
            if asset is None:
                if abs_path in project.get_buildable_paths():
                    for buildable_path in project.get_buildable_paths():
                        for component_library in project.component_libraries:
                            for asset in component_library.workers:
                                if abs_path in asset.get_dir_abs_path():
                                    assets_to_build.append(asset)
                        for asset in project.applications:
                            if abs_path in asset.get_dir_abs_path():
                                assets_to_build.append(asset)
                        for asset in project.hdl_primitives:
                            if abs_path in asset.get_dir_abs_path():
                                assets_to_build.append(asset)
                        for asset in project.hdl_assemblies:
                            if abs_path in asset.get_dir_abs_path():
                                assets_to_build.append(asset)
                        for asset in project.hdl_devices:
                            if abs_path in asset.get_dir_abs_path():
                                assets_to_build.append(asset)
                else:
                    raise Exception(_dir + ' is not buildable')
            else:
                assets_to_build.append(asset)
        else:
            if (hdl_target != '') or (hdl_platform != ''):
                for hdl_primitive in project.hdl_primitives:
                    assets_to_build.append(hdl_primitive)
                for hdl_assembly in project.hdl_assemblies:
                    assets_to_build.append(hdl_assembly)
                for component_library in project.component_libraries:
                    for worker in component_library.workers:
                        if worker.get_type() == 'hdl worker':
                            assets_to_build.append(worker)
            if rcc_platform != '':
                self.install_rcc_platform_if_not_installed(
                        project_registry, rcc_platform)
                for component_library in project.component_libraries:
                    for worker in component_library.workers:
                        if worker.get_type() == 'rcc worker':
                            assets_to_build.append(worker)
                for application in project.applications:
                    assets_to_build.append(application)
        self.throw_if_project_dependencies_not_registered(
            project, project_registry)
        # ============ TODO START fix this mess and move back into tool class
        if rcc_platform != '':
            self.install_rcc_platform_if_not_installed(
                    project_registry, rcc_platform)
        dependency_ordered_pid_strs = []
        # initial hack to handle circular platform/assets circular dependency
        for proj in project_registry.projects:
            if str(proj.get_package_id()) == 'ocpi.core':
                dependency_ordered_pid_strs.append(str(proj.get_package_id()))
        for proj in project_registry.projects:
            if str(proj.get_package_id()) == 'ocpi.platform':
                dependency_ordered_pid_strs.append(str(proj.get_package_id()))
        for proj in project_registry.projects:
            if str(proj.get_package_id()) == 'ocpi.assets':
                dependency_ordered_pid_strs.append(str(proj.get_package_id()))
        # proper project dependency order, with timeout hack to handle circular
        # dependencies
        timeout = 10000
        while len(dependency_ordered_pid_strs) != \
                len(project_registry.projects):
            if timeout == 0:
                break
            timeout -= 1
            for proj in project_registry.projects:
                deps_covered = True
                for dependent_proj in proj.project_dependencies:
                    if dependent_proj not in dependency_ordered_pid_strs:
                        deps_covered = False
                if deps_covered:
                    if str(proj.get_package_id()) not in dependency_ordered_pid_strs:
                        dependency_ordered_pid_strs.append(
                                str(proj.get_package_id()))
        # timeout hack to handle circular dependencies,
        # (we gave up on dependency order!)
        if timeout == 0:
            for proj in project_registry.projects:
                if str(proj.get_package_id()) not in dependency_ordered_pid_strs:
                    dependency_ordered_pid_strs.append(str(proj.get_package_id()))
        # do the final export in psuedo-dependency-order
        for package_id_str in dependency_ordered_pid_strs:
            for proj in project_registry.projects:
                if str(proj.get_package_id()) == package_id_str:
                    # TODO move below 7 lines outside OCPIDev class (Legacy...)
                    # IMPORTANT - below 6 lines necessary to remove stale files
                    os.system('rm -rf $(find ' + proj.abs_path + ' -type f -name imports)')
                    os.system('rm -rf $(find ' + proj.abs_path + ' -type f -name exports)')
                    os.system('rm -rf $(find ' + proj.abs_path + ' -type d -name imports)')
                    os.system('rm -rf $(find ' + proj.abs_path + ' -type d -name exports)')
                    os.system('rm -rf $(find ' + proj.abs_path + ' -type l -name imports)')
                    os.system('rm -rf $(find ' + proj.abs_path + ' -type l -name exports)')
                    self.hdl_build_tool.export_project(
                            proj, hdl_platform, hdl_target, rcc_platform)
        # ============ END fix this mess and move back into tool class
        for asset in assets_to_build:
            project.build_asset(
                    asset, project_registry, self.hdl_build_tool,
                    hdl_target, hdl_platform, rcc_platform, _j)
        # TODO move below 8 lines outside OCPIDev class (Legacy...)
        # IMPORTANT - below 7 lines necessary to mitigate stale files
        #for proj in project_registry.projects:
        #    os.system('rm -rf $(find ' + proj.abs_path + ' -type f -name imports)')
        #    os.system('rm -rf $(find ' + proj.abs_path + ' -type f -name exports)')
        #    os.system('rm -rf $(find ' + proj.abs_path + ' -type d -name imports)')
        #    os.system('rm -rf $(find ' + proj.abs_path + ' -type d -name exports)')
        #    os.system('rm -rf $(find ' + proj.abs_path + ' -type l -name imports)')
        #    os.system('rm -rf $(find ' + proj.abs_path + ' -type l -name exports)')

    def clean(self, noun, _dir):
        project_registry = ProjectRegistry(False, False)
        if _dir is None:
            if noun == []:
                _dir = os.getcwd()
        cleaned = False
        for project in project_registry.projects:
            if project.abs_path in os.path.realpath(_dir):
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
                cleaned = True
        if not cleaned:
            raise Exception('cannot clean directory not in registered project')

    def show(self, noun):
        disc = noun != 'registry'
        disc = disc and (noun != 'projects')
        project_registry = ProjectRegistry(disc, disc)
        if noun == 'registry':
            print(project_registry.abs_path)
        for project in project_registry.projects:
            print("project.abs_path = " + project.abs_path)
            if noun == 'projects':
                msg = str(project.get_package_id()) + ' '
                for idx in range(30-len(msg)):
                    msg += ' '
                print(msg + project.abs_path)
            if noun == 'components':
                for component in project.components:
                    print(str(project.get_package_id()) + '.' + component.name)
            for component_library in project.component_libraries:
                print("component_library.abs_path = " + component_library.abs_path)
                pid = component_library.get_package_id(str(project.get_package_id()))
                if noun == 'libraries':
                    print(pid)
                if noun == 'components':
                    for component in component_library.components:
                        print(pid + '.' + component.name)
                if noun == 'workers':
                    for worker in component_library.workers:
                        print(pid + '.' + worker.name + '.' +
                              worker.authoring_model)
            if noun == 'libraries':
                for hdl_primitive in project.hdl_primitives:
                    print(str(project.get_package_id()) + '.' + hdl_primitive.name)

    def register(self, noun):
        project_registry = ProjectRegistry(
                do_discover_component_libraries=False,
                do_discover_hdl_primitives=False)
        if noun == 'project':
            project_registry.register_project()

    def unregister(self, noun):
        project_registry = ProjectRegistry(
                do_discover_component_libraries=False,
                do_discover_hdl_primitives=False)
        if noun == 'project':
            project_registry.unregister_project()

    def set(self, noun):
        raise Exception('set is not supported at this time')

    def unset(self, noun):
        raise Exception('unset is not supported at this time')

    def run(self, noun):
        raise Exception('run is not supported at this time')

    def refresh(self, noun):
        Logger().warn('refresh is unecessary in ocpidev2')

    def apply(self, noun):
        # all patches should be created from the project perspective
        if noun == 'patches':
            project_registry = ProjectRegistry()
            for project in project_registry.projects:
                patches_dir_abs_path = project.abs_path + '/patches'
                if os.path.isdir(patches_dir_abs_path):
                    for patch_dir_name in os.listdir(patches_dir_abs_path):
                        patch_dir_abs_path = patches_dir_abs_path + '/' + patch_dir_name
                        if os.path.isdir(patch_dir_abs_path):
                            authoring_model = ''
                            asset_name = patch_dir_name
                            if asset_name.endswith('.hdl') or asset_name.endswith('.rcc') or asset_name.endswith('.ocl') or asset_name.endswith('.test'):
                                tmp = asset_name.rsplit('.', 1)
                                asset_name = tmp[0]
                                authoring_model = tmp[1]
                            pid = asset_name.rsplit('.', 1)[0]
                            for p2 in project_registry.projects:
                                if p2.get_package_id() == pid:
                                    for patch_file_name in os.listdir(patch_dir_abs_path):
                                        patch_file_abs_path = patch_dir_abs_path + '/' + patch_file_name
                                        if os.path.isfile(patch_file_abs_path):
                                            for asset in p2.assets:
                                                if asset.name == asset_name.split('.')[-1]:
                                                    if (asset.get_type() == 'hdl worker') or (asset.get_type() == 'rcc worker') or (asset.get_type() == 'ocl worker'):
                                                        if asset.authoring_model != authoring_model:
                                                            continue
                                                        cmd = 'cd ' + p2.abs_path + ' && patch -p0 --forward < ' + patch_file_abs_path + ' || true'
                                                        System(cmd)
        else:
            raise Exception('apply does not support ' + noun)


# TODO delete this and probably re-write other Tool Layers (TL) in python
class LegacyOCPIDevHDLBuildTool():

    def __init__(self):
        self.first = True
        pass

    def export_project(self, project, hdl_platform, hdl_target, rcc_platform):
        Logger().info(
            'LegacyOCPIDevHDLBuildTool: exporting project ' +
            project.abs_path.split('/')[-1])
        hdl = (hdl_platform is not None) or (hdl_target is not None)
        if hdl or (rcc_platform != ''):
            cmd = 'ocpidev build -d ' + project.abs_path + ' --no-doc'
            if Environment().ocpi_log_level < 8:
                cmd += ' >/dev/null 2>&1'
            #cmd = 'cd ' + project.abs_path + ' && $OCPI_CDK_DIR/scripts/export-project.sh'
            #if Environment().ocpi_log_level >= 9:
            #    cmd += ' -v'
            #cmd += ' -'
            if os.system(cmd) != 0:
                raise Exception('failed to export project ' + str(project.get_package_id()) + ', set log level to 8 or higher for more info')

    def install_rcc_platform_if_not_installed(
            self, project_registry, rcc_platform):
        for proj in project_registry.projects:
            if str(proj.get_package_id()) == 'ocpi.core':
                tmp_path = proj.abs_path + '/rcc/platforms/'
                if not os.path.isdir(tmp_path + rcc_platform + '/gen'):
                    Logger().debug('ocpiadmin install platform ' + rcc_platform)
                    if os.system('ocpiadmin install platform ' + rcc_platform) != 0:
                        raise Exception('failed to build rcc platform ' + rcc_platform)

    def get_build_output_path(self, asset, hdl_target='',
            hdl_platform=''):
        ret = asset.abs_path
        tmp = ''
        if asset.get_type() == 'hdl assembly':
            tmp = asset.name + '_' + hdl_platform + '_'
            if asset.containers[0].config is None:
                tmp += 'base_'
            else:
                tmp += asset.containers[0].config + '_'
            tmp += asset.containers[0].name
            ret += '/container-' + tmp + '_'
        ret += '/target-' + get_hdl_target(hdl_platform) + '/'
        #if (asset.get_type() == 'hdl primitive') or (asset.get_type() == 'hdl worker'):
        #    ret += asset.name + '_rv.edf'
        #if (asset.get_type() == 'hdl assembly'):
        #    ret += tmp + '_rv.edf'
        return ret

    def get_gnu_make_recipe(self, asset):
        ret = 'ocpidev build -d ' + asset.get_dir_abs_path()
        if hdl_target != '':
            ret += ' --hdl-target ' + hdl_target
        if hdl_platform != '':
            ret += ' --hdl-platform ' + hdl_platform
        if no_doc:
            ret += ' --no-doc'
        return ret
    #def emit_makefile(self, dependency_tree, hdl_target, hdl_platform):
    #    makefile = GNUMakefile(None)
    #    for key, asset in dependency_tree.items():
    #        tar = self.get_build_output_path(asset, hdl_target, hdl_platform)
    #        makefile.rules['all'] = GNUMakeRule()
    #        target = GNUMakeTarget('all', True)
    #        for dependent in dependency_tree.dependents:
    #            prereq = self.get_build_output_path(asset, hdl_target,
    #                    hdl_platform)
    #            makefile.rules[tar].prerequisites.append(prereq)
    #            makefile.rules[tar].recipe = get_gnu_make_recipe(tar)
    #    makefile.emit()
    def build_asset(self, project, asset, tname,
            hdl_target='', hdl_platform='', rcc_platform='',
            no_doc=False, project_registry=None, dependency_tree=None):
        _j = 1
        # try:
        if self.first:
            self.first = False
            # for proj in project_registry.projects:
            #     self.export_project(proj)
        # while not os.path.isfile(asset.abs_path + '/.build'):
        # while os.path.isfile(asset.abs_path + '/.lock'):
        #    Logger().info('waiting on lock for ' + asset.abs_path)
        #    time.sleep(10)
        # Logger().info('building ' + asset.get_type() + ' ' + asset.name)
        # os.system('touch ' + asset.abs_path + '/.lock')
        # self.emit_makefile(dependency_tree, hdl_target, hdl_platform)
        cmd = ''
        if Environment().ocpi_log_level >= 7:
            cmd += '@echo [INFO] building ' + asset.get_type() + ' ' + asset.name
            cmd += '\n\t'
        if Environment().ocpi_log_level < 8:
            cmd += '@'
        cmd += 'ocpidev build -d ' + asset.get_dir_abs_path()
        if hdl_target != '':
            cmd += ' --hdl-target ' + hdl_target
        if hdl_platform != '':
            cmd += ' --hdl-platform ' + hdl_platform
        if rcc_platform != '':
            cmd += ' --rcc-platform ' + rcc_platform
        if no_doc:
            cmd += ' --no-doc'
        if Environment().ocpi_log_level < 8:
            cmd += ' >/dev/null 2>&1'
        cmd += '\n\t'
        # cmd += '@[ ! -f ' + global_makefile.rules[tname].targets[0].string + ' ] && echo [ERROR] build of ' + asset.get_type() + ' ' + asset.name + ' failed'
        # cmd += '\n\t'
        # cmd += '@[ -f ' + global_makefile.rules[tname].targets[0].string + ' ]'
        # cmd += '\n\t'
        #if (Environment().ocpi_log_level >= 8) and (_j > 1):
        cmd += '@echo [INFO] building ' + asset.get_type() + ' ' + asset.name + ' done'
        global_makefile.rules[tname].recipe = cmd
        Logger().debug('creating make rule: ' + str(global_makefile.rules[tname]))
        #if os.system(cmd) != 0:
        #    raise Exception('build failed ')
        #os.system('touch ' + asset.abs_path + '/.build')
        #os.system('rm -rf ' + asset.abs_path + '/.lock')
        #except Exception as exception:
        #    if os.path.isfile(asset.abs_path + '/.lock'):
        #        os.system('rm -rf ' + asset.abs_path + '/.lock')
        #    raise exception


def unittest():
    ret = True
    # ret = test_GNUMakefile(ret)
    ret = test_Component(ret)
    ret = test_Component_create(ret)
    ret = test_ComponentLibrary(ret)
    ret = test_ComponentLibrary_create(ret)
    ret = test_RccAssembly(ret)
    ret = test_Project_discover_component_libraries(ret)
    # ret = test_ProjectRegistry(ret)
    # ret = test_OCPIDev(ret)
    ret = test_Worker(ret)
    ret = test_HdlLibrary(ret)
    ret = test_HdlAssembly(ret)
    # ret = test_HdlAssemblyInstance(ret)
    ret = test_Property(ret)
    ret = test_HdlContainerDevice(ret)
    ret = test_HdlContainer(ret)
    ret = test_HdlCardPlatformBase(ret)
    ret = test_HdlPlatform(ret)
    ret = test_HdlPlatformConfiguration(ret)
    ret = test_HdlCard(ret)
    # ret = test_LegacyOCPIDevHDLBuildTool(ret)
    return ret


def add_create_arguments(parser, verb):
    # TODO: Might be better to place all attrs in AssetBase, then
    # AssetBase.get_attr_infos('<asset-type>') to avoid 'if verb =='
    if verb == 'project':
        project = Project('', False, None)
        for attr in project.get_attr_infos():
            if attr.cli is not None:
                parser.add_argument(attr.cli[0], attr.cli[1], nargs='?', default='')
    #if verb == 'library':
    #    library = ComponentLibrary('', False, None)
    #    for attr in library.get_attr_infos():
    #        if attr.cli is not None:
    #            parser.add_argument(attr.cli[0], attr.cli[1], nargs='?', default='')
    if verb == 'component':
        component = Component('', False, None)
        for attr in component.get_attr_infos():
            if attr.cli is not None:
                parser.add_argument(attr.cli[0], attr.cli[1], nargs='?', default='')
    if verb == 'test':
        test = Test('', False, None)
        for attr in test.get_attr_infos():
            if attr.cli is not None:
                if attr.is_bool:
                    parser.add_argument(attr.cli[0], attr.cli[1], default='',
                                        action=attr.action)
                else:
                    parser.add_argument(attr.cli[0], attr.cli[1], nargs='?',
                                        default='')
    return parser


def add_build_arguments(parser):
    parser.add_argument('--hdl-target', nargs='?', default='')
    parser.add_argument('--hdl-platform', nargs='?', default='')
    parser.add_argument('--rcc-platform', nargs='?', default='')
    return parser


if __name__ == '__main__':
    exit_status = 0
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-d', nargs='?', default=None)
    parser.add_argument('-j', nargs='?', default=1)
    parser.add_argument('verb')
    if 'create' in sys.argv:
        if 'project' in sys.argv:
            parser = add_create_arguments(parser, 'project')
        #if 'library' in sys.argv:
        #    parser = add_create_arguments(parser, 'library')
        if 'component' in sys.argv:
            parser = add_create_arguments(parser, 'component')
        if 'test' in sys.argv:
            parser = add_create_arguments(parser, 'test')
    if 'build' in sys.argv:
        parser = add_build_arguments(parser)
    #required = ('create' in sys.argv) or ('build' in sys.argv) or ('show' in sys.argv)
    #if required:
    #    parser.add_argument('noun')
    #else:
    #    parser.add_argument('noun', nargs='?', default=None)
    parser.add_argument('noun', nargs='?', default=None)
    parser.add_argument('name', nargs='?', default=None)
    args = parser.parse_args()
    try:
        nouns = ['registry', 'project', 'projects', 'libraries', 'components',
                 'workers', 'library', 'component', 'test']
        if (args.noun is not None) and (args.noun not in nouns):
            if args.verb != 'apply':
                raise Exception('noun ' + str(args.noun) + ' is not supported')
        signal.signal(signal.SIGINT, mysigint)
        hdl_build_tool = LegacyOCPIDevHDLBuildTool()
        _dir = args.d
        if args.d is None:
            if (args.noun is None) or (args.verb != 'clean'):
                _dir = os.getcwd()
        if args.verb == 'create':
            if args.noun is None:
                raise Exception("Please provide a noun to perform a create action")
            if args.name is None:
                raise Exception('ocpidev2 create ' + args.noun + ' <name> required')
            OCPIDev(hdl_build_tool).create(_dir, vars(args))
        elif args.verb == 'delete':
            OCPIDev(hdl_build_tool).delete(args.noun)
        elif args.verb == 'build':
            OCPIDev(hdl_build_tool).build(
                args.noun, args.hdl_target, args.hdl_platform,
                args.rcc_platform, _dir, int(args.j))
        elif args.verb == 'clean':
            OCPIDev(hdl_build_tool).clean(args.noun, _dir)
        elif args.verb == 'show':
            OCPIDev(hdl_build_tool).show(args.noun)
        elif args.verb == 'register':
            OCPIDev(hdl_build_tool).register(args.noun)
        elif args.verb == 'unregister':
            OCPIDev(hdl_build_tool).unregister(args.noun)
        elif args.verb == 'run':
            OCPIDev(hdl_build_tool).run(args.noun)
        elif args.verb == 'refresh':
            OCPIDev(hdl_build_tool).refresh(args.noun)
        elif args.verb == 'unittest':
            if unittest():
                exit_status = 0
            else:
                exit_status = 1
        elif args.verb == 'apply':
            OCPIDev(hdl_build_tool).apply(args.noun)
        else:
            raise Exception('verb ' + args.verb + ' is not supported')
    except Exception as exception:
        Logger().error(str(exception))
        exit_status = 1
    exit(exit_status)
