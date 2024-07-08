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
from _opencpi.assets.application2 import *


def ocpidevsignint(sig, frame):
    raise Exception('Ctrl-C stopped execution')


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


def test_show(ret):
    show({'d' : [''], 'help' : False, 'verbose' : False, 'noun' : 'components'})
    show({'d' : [''], 'help' : False, 'verbose' : False, 'noun' : 'libraries'})
    show({'d' : [''], 'help' : False, 'verbose' : False, 'noun' : 'projects'})
    show({'d' : [''], 'help' : False, 'verbose' : False, 'noun' : 'registry'})
    show({'d' : [''], 'help' : False, 'verbose' : False, 'noun' : 'workers'})
    return ret


def unittest():
    ret = True
    # ret = test_GNUMakefile(ret)
    ret = test_Component(ret)
    ret = test_Component_create(ret)
    ret = test_ComponentLibrary(ret)
    ret = test_ComponentLibrary_create(ret)
    ret = test_RccAssembly(ret)
    ret = test_Project_discover_component_libraries(ret)
    ret = test_Project_create(ret)
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
    ret = test_Test_create(ret)
    ret = test_Application_create(ret)
    ret = test_show(ret)
    return ret


def add_show_arguments(parser):
    #parser.add_argument('--global-scope', action='store_true')
    return parser


def add_create_arguments(parser, noun):
    if noun == 'project':
        project = Project('', False, None)
        for attr in project.get_attr_infos():
            if attr.cli is not None:
                parser.add_argument(attr.cli[0], attr.cli[1], nargs='?',
                                    default='')
        parser.add_argument('--register', default=False, action='store_true')
    if noun == 'library':
        library = ComponentLibrary('', False, None)
        for attr in library.get_attr_infos():
            if attr.cli is not None:
                parser.add_argument(attr.cli[0], attr.cli[1], nargs='?',
                                    default='')
    if noun == 'component':
        component = Component('', False, None)
        for attr in component.get_attr_infos():
            if attr.cli is not None:
                if attr.is_bool:
                    parser.add_argument(attr.cli[0], attr.cli[1], default='',
                                        action='store_true')
                else:
                    parser.add_argument(attr.cli[0], attr.cli[1], nargs='?',
                                        default='')
        parser.add_argument('-t', '--create-test', default=False, action='store_true')
        parser.add_argument('-p', '--project', default=False, action='store_true')
    if noun == 'test':
        test = Test('', False, None)
        for attr in test.get_attr_infos():
            if attr.cli is not None:
                if attr.is_bool:
                    parser.add_argument(attr.cli[0], attr.cli[1], default='',
                                        action='store_true')
                else:
                    parser.add_argument(attr.cli[0], attr.cli[1], nargs='?',
                                        default='')
    if noun == 'application':
        group = parser.add_mutually_exclusive_group()
        group.add_argument('-X', '--xml-app', default=False, action='store_true')
        group.add_argument('-x', '--xml-dir-app', default=False, action='store_true')
    return parser


def add_build_arguments(parser):
    parser.add_argument('--hdl-target', nargs='?', default='')
    parser.add_argument('--hdl-platform', nargs='?', default='')
    parser.add_argument('--rcc-platform', nargs='?', default='')
    parser.add_argument('-j', nargs='?', default=1)
    return parser


def get_arg_parser():
    parser = argparse.ArgumentParser(description='', add_help=False)
    parser.add_argument('-d', default=[], action='append')
    parser.add_argument('-h', '--help', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('verb', nargs='?', default='')
    if 'show' in sys.argv:
        parser = add_show_arguments(parser)
    elif 'create' in sys.argv:
        if 'project' in sys.argv:
            parser = add_create_arguments(parser, 'project')
        if 'library' in sys.argv:
            parser = add_create_arguments(parser, 'library')
        if 'component' in sys.argv:
            parser = add_create_arguments(parser, 'component')
        if 'test' in sys.argv:
            parser = add_create_arguments(parser, 'test')
        if 'application' in sys.argv:
            parser = add_create_arguments(parser, 'application')
    elif 'build' in sys.argv:
        parser = add_build_arguments(parser)
    parser.add_argument('noun', nargs='?', default=None)
    parser.add_argument('name', nargs='?', default=None)
    return parser


def get_args(parser):
    # below 3 lines parse, allowing for posix conformance (intermixed args)
    (args, unknown_args) = parser.parse_known_args()
    for unknown_arg in unknown_args:
        args.noun = unknown_arg
    return args


def get_cli_dict_and_validate_args(args):
    """ get a dictionary of settings which looks like CLI args and has been modified as needed """
    nouns = ['registry', 'project', 'projects', 'libraries', 'components',
             'workers', 'library', 'component', 'test', 'application']
    # TODO move below 3 lines to AssetBase once proper checks in place
    if args.name:
        if not args.name.isidentifier():
            raise ValueError("'" + args.name + "' is not a valid name")
    if (args.noun is not None) and (args.noun not in nouns):
        if args.verb != 'apply':
            raise Exception('noun ' + str(args.noun) + ' is not supported')
    tmp = args
    mylist = args.d.copy()
    tmp.d = []
    if len(mylist) == 0:
        tmp.d.append('')
    for _dir in mylist:
        if _dir is None:
            _dir = ''
        else:
            _dir = os.path.abspath(_dir)
        if _dir in tmp.d:
            Logger().warn('-d has duplicate ' + _dir)
        else:
            tmp.d.append(_dir)
    cli_dict = vars(tmp)
    # make CLI look like attrs (necessary for create cli verb)
    cli_dict = ({key.replace('_', '') : val for key, val in cli_dict.items()})
    return cli_dict


def get_cli_dict():
    return get_cli_dict_and_validate_args(get_args(get_arg_parser()))
    """ cli_dict['d']     a list of strings, where an empty string is meant
                          to represent no -d was specified at the CLI
        cli_dict['verb']  contains verb string
        cli_dict['noun']  contains noun string (empty if unspecifed at CLI)
        cli_dict['name']  contains name string (empty if unspecifed at CLI)
        cli_dict['component']    entry may not exist
        cli_dict['createtest']   entry may not exist, boolean
        cli_dict['usehdlfileio'] entry may not exist, boolean
        cli_dict['xmlapp']       entry may not exist, boolean
        cli_dict['xmldirapp']    entry may not exist, boolean """


def create(cli_dict, project_registry):
    for _dir in cli_dict['d']:
        if _dir == '':
            _dir = os.getcwd()
        if cli_dict['noun'] == 'project':
            abs_path = _dir + '/' + cli_dict['name']
            Project(abs_path, False, cli_dict).create()
            if cli_dict['register'] == True:
                register('project', abs_path)
        else:
            project = next((proj for proj in project_registry.projects if
                            proj.abs_path + '/' in _dir + '/'), None)
            if project is None:
                raise Exception("Invalid path: '" + _dir + "'. Please perform "
                                "create " + cli_dict['noun'] + " in a valid "
                                "registered project directory.")
            if cli_dict['noun'] == 'library':
                component_lib_path = _dir + '/' + cli_dict['name']
                ComponentLibrary(
                    component_lib_path, False, cli_dict
                ).create(project, _dir)
            if cli_dict['noun'] == 'application':
                application_path = _dir + '/' + cli_dict['noun'] + 's/' + cli_dict['name']
                applications_dir = project.abs_path + '/applications'
                if _dir != project.abs_path and _dir != applications_dir:
                    raise Exception("Invalid path: '" + _dir + "'. Please "
                                    "perform create application at the top of "
                                    "a valid registered project or within the "
                                    "applications directory.")
                Application(
                    application_path, False, cli_dict
                ).create(project.abs_path, cli_dict['xmlapp'], cli_dict['xmldirapp'])
            if cli_dict['noun'] in ['component', 'test']:
                # Check path is a valid component library directory
                valid_path = any(_dir == lib.abs_path for lib in
                                 project.component_libraries)
                if not valid_path:
                    raise Exception("Invalid path: `" + _dir + "'. Please "
                                    "perform create " + cli_dict['noun'] + " "
                                    "in a valid component library.")
                if cli_dict['noun'] == 'component':
                    spec_create = True if cli_dict['project'] else False
                    component_path = (
                        _dir + '/' + cli_dict['name'] + '.comp' + '/' + cli_dict['name'] +
                        '-comp.xml'
                    )
                    package_id = project.get_package_id()
                    Component(
                        component_path, False, cli_dict
                    ).create(package_id, spec_create, project.abs_path)
                    if cli_dict['createtest'] == True:
                        test_path = _dir + '/' + cli_dict['name'] + '.test'
                        cli_dict['component'] = ''
                        cli_dict['usehdlfileio'] = ''
                        Test(test_path, False, cli_dict).create()
                if cli_dict['noun'] == 'test':
                    test_path = _dir + '/' + cli_dict['name'] + '.test'
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
                                   'registered projects.')
                            raise Exception(msg)
                    # If --component not used, check for the component in path
                    else:
                        valid_create_test = False
                        for ext in ['.rcc', '.hdl', '.comp']:
                            if os.path.exists(_dir + '/' + cli_dict['name'] + ext):
                                 valid_create_test = True
                        if not valid_create_test:
                            raise Exception('A ' + cli_dict['name'] + ' component does '
                                            'not yet exist to create a unit-test '
                                            'for.')
                    Test(test_path, False, cli_dict).create()


def throw_if_not_installed(platform):
    """ TODO move to the ProjectRegistry class """
    ocpi_cdk_dir = os.environ.get('OCPI_CDK_DIR')
    if platform is not None:
        if not os.path.isdir(ocpi_cdk_dir + '/' + platform):
            raise Exception('platform ' + platform + ' is not installed')


def install_rcc_platform_if_not_installed(project_registry, rcc_platform):
    """ TODO move to the ProjectRegistry class """
    for proj in project_registry.projects:
        if str(proj.get_package_id()) == 'ocpi.core':
            tmp_path = proj.abs_path + '/rcc/platforms/'
            if not os.path.isdir(tmp_path + rcc_platform + '/gen'):
                if os.system('ocpiadmin install platform ' + rcc_platform) != 0:
                    raise Exception('failed to build rcc platform ' + rcc_platform)


def throw_if_project_dependencies_not_registered(project, project_registry):
    """ TODO move to the ProjectRegistry class """
    unreg_projects = (project_registry.
                      get_project_dependencies_not_registered(project))
    if len(unreg_projects) != 0:
        msg = 'Project Registry incomplete, please register project(s): '
        for unreg_project in unreg_projects:
            msg += unreg_project + " "
        raise Exception(msg)


def export_projects(project_registry, hdl_platform, hdl_target, rcc_platform,
                    hdl_build_tool):
    """ TODO START fix this mess and move back into tool class """
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
                hdl_build_tool.export_project(
                        proj, hdl_platform, hdl_target, rcc_platform)


def _help(cli_dict, project_registry):
    if cli_dict['verb'] == '':
        os.system('man ocpidev2')
    else:
        os.system('man ocpidev2-' + cli_dict['verb'])


def build(cli_dict, project_registry):
    hdl_build_tool = LegacyOCPIDevHDLBuildTool()  # TODO make extensible
    if (cli_dict['hdltarget'] != '') or (cli_dict['hdlplatform'] != ''):
        if os.environ.get('XILINX_VIVADO') is not None:
            msg = 'cannot run ocpidev2 when Vivado environment is sourced'
            raise Exception(msg)
    if cli_dict['rccplatform'] != '':
        throw_if_not_installed(cli_dict['rccplatform'])
    # if hdl_platform is not None:
    #     throw_if_not_installed(hdl_platform)
    for _dir in cli_dict['d']:
        if _dir == '':
            _dir = os.getcwd()
        abs_path = _dir
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
            if (cli_dict['hdltarget'] != '') or (cli_dict['hdlplatform'] != ''):
                for hdl_primitive in project.hdl_primitives:
                    assets_to_build.append(hdl_primitive)
                for hdl_assembly in project.hdl_assemblies:
                    assets_to_build.append(hdl_assembly)
                for component_library in project.component_libraries:
                    for worker in component_library.workers:
                        if worker.get_type() == 'hdl worker':
                            assets_to_build.append(worker)
            if cli_dict['rccplatform'] != '':
                install_rcc_platform_if_not_installed(
                        project_registry, cli_dict['rccplatform'])
                for component_library in project.component_libraries:
                    for worker in component_library.workers:
                        if worker.get_type() == 'rcc worker':
                            assets_to_build.append(worker)
                for application in project.applications:
                    assets_to_build.append(application)
        throw_if_project_dependencies_not_registered(
            project, project_registry)
        if cli_dict['rccplatform'] != '':
            install_rcc_platform_if_not_installed(
                    project_registry, cli_dict['rccplatform'])
        export_projects(project_registry, cli_dict['hdlplatform'],
                        cli_dict['hdltarget'], cli_dict['rccplatform'],
                        hdl_build_tool)
        project.build_assets(
                assets_to_build, project_registry, hdl_build_tool,
                cli_dict['hdltarget'], cli_dict['hdlplatform'],
                cli_dict['rccplatform'], cli_dict['j'])
        # TODO move below 8 lines outside OCPIDev class (Legacy...)
        # IMPORTANT - below 7 lines necessary to mitigate stale files
        #for proj in project_registry.projects:
        #    os.system('rm -rf $(find ' + proj.abs_path + ' -type f -name imports)')
        #    os.system('rm -rf $(find ' + proj.abs_path + ' -type f -name exports)')
        #    os.system('rm -rf $(find ' + proj.abs_path + ' -type d -name imports)')
        #    os.system('rm -rf $(find ' + proj.abs_path + ' -type d -name exports)')
        #    os.system('rm -rf $(find ' + proj.abs_path + ' -type l -name imports)')
        #    os.system('rm -rf $(find ' + proj.abs_path + ' -type l -name exports)')


def show(cli_dict, project_registry):
    if cli_dict['help']:
        os.system('man ocpidev2-show')
    else:
        if cli_dict['noun'] is None:
            raise Exception('show must have a noun')
        for _dir in cli_dict['d']:
            if cli_dict['noun'] == 'registry':
                if (_dir == '') or \
                   (_dir in project_registry.abs_path):
                    print(project_registry.abs_path)
            msg = ''
            for project in project_registry.projects:
                if cli_dict['noun'] == 'projects':
                    if (_dir == '') or \
                       (_dir in project.abs_path):
                        msg = str(project.get_package_id())
                        if cli_dict['verbose']:
                            msg += ' '
                            for idx in range(30-len(msg)):
                                msg += ' '
                            msg += project.abs_path
                        print(msg)
                if cli_dict['noun'] == 'components':
                    for component in project.components:
                        if (_dir == '') or \
                           (_dir in component.abs_path):
                            print(str(project.get_package_id()) + '.' + component.name)
                for component_library in project.component_libraries:
                    pid = component_library.get_package_id(str(project.get_package_id()))
                    if cli_dict['noun'] == 'libraries':
                        if (_dir == '') or \
                           (_dir in component_library.abs_path):
                            print(pid)
                    if cli_dict['noun'] == 'components':
                        for component in component_library.components:
                            if (_dir == '') or \
                               (_dir in component.abs_path):
                                print(pid + '.' + component.name)
                    if cli_dict['noun'] == 'workers':
                        for worker in component_library.workers:
                            if (_dir == '') or \
                               (_dir in worker.abs_path):
                                print(pid + '.' + worker.name + '.' +
                                      worker.authoring_model)
                if cli_dict['noun'] == 'libraries':
                    for hdl_primitive in project.hdl_primitives:
                        if (_dir == '') or \
                           (_dir in hdl_primitive.abs_path):
                            print(str(project.get_package_id()) + '.' +
                                  hdl_primitive.name)


def register(cli_dict, project_registry):
    for _dir in cli_dict['d']:
        if _dir == '':
            _dir = os.getcwd()
        if cli_dict['noun'] == 'project':
            project_registry.register_project(_dir)


def unregister(cli_dict, project_registry):
    for _dir in cli_dict['d']:
        if _dir == '':
            _dir = os.getcwd()
        if cli_dict['noun'] == 'project':
            project_registry.unregister_project(_dir)


def clean(cli_dict, project_registry):
    for _dir in cli_dict['d']:
        if _dir == '':
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


def get_create_registry(cli_dict):
    create_registry = False
    if cli_dict['verb'] == 'build':
        create_registry = True
    if cli_dict['verb'] == 'clean':
        create_registry = True
    if cli_dict['verb'] == 'create':
        create_registry = True
    if cli_dict['verb'] == 'show':
        create_registry = True
    if cli_dict['verb'] == 'register':
        create_registry = True
    if cli_dict['verb'] == 'unregister':
        create_registry = True
    return create_registry


def get_enable_registry_discovery(cli_dict):
    disc = True
    if cli_dict['verb'] == 'clean':
        disc = False
    if cli_dict['verb'] == 'show':
        disc = cli_dict['noun'] != 'registry'
        disc = disc and (cli_dict['noun'] != 'projects')
    if cli_dict['verb'] == 'register':
        disc = False
    if cli_dict['verb'] == 'unregister':
        disc = False
    return disc


if __name__ == '__main__':
    exit_status = 0
    #try:
    signal.signal(signal.SIGINT, ocpidevsignint)
    cli_dict = get_cli_dict()
    print(cli_dict)
    project_registry = None
    if get_create_registry(cli_dict):
        disc = get_enable_registry_discovery(cli_dict)
        project_registry = ProjectRegistry(disc, disc)
    if cli_dict['help']:
        _help(cli_dict, project_registry)
    elif cli_dict['verb'] == 'build':
        build(cli_dict, project_registry)
    elif cli_dict['verb'] == 'clean':
        clean(cli_dict, project_registry)
    elif cli_dict['verb'] == 'create':
        create(cli_dict, project_registry)
    elif cli_dict['verb'] == 'show':
        show(cli_dict, project_registry)
    elif cli_dict['verb'] == 'register':
        register(cli_dict, project_registry)
    elif cli_dict['verb'] == 'unregister':
        unregister(cli_dict, project_registry)
    else:
        raise Exception('verb ' + cli_dict['verb'] + ' is not supported')
    #except Exception as exception:
    #    Logger().error(str(exception))
    #    exit_status = 1
    exit(exit_status)
