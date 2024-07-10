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


def test_show(ret):
    show({'d': [''], 'help': False, 'verbose': False, 'noun': 'components'})
    show({'d': [''], 'help': False, 'verbose': False, 'noun': 'libraries'})
    show({'d': [''], 'help': False, 'verbose': False, 'noun': 'projects'})
    show({'d': [''], 'help': False, 'verbose': False, 'noun': 'registry'})
    show({'d': [''], 'help': False, 'verbose': False, 'noun': 'workers'})
    return ret


def unittest(cli_dict, project_registry):
    ret = True
    # ret = test_GNUMakefile(ret)
    ret = test_Component(ret)
    ret = test_ComponentLibrary(ret)
    ret = test_RccAssembly(ret)
    # ret = test_Project_discover_component_libraries(ret)
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
    # ret = test_show(ret)
    return ret


def add_show_arguments(parser):
    # parser.add_argument('--global-scope', action='store_true')
    parser.add_argument('authoring_model', nargs='?', default='')
    parser.add_argument('noun', nargs='?', default=None)
    parser.add_argument('name', nargs='?', default=None)
    return parser


def get_arg_parser():
    parser = argparse.ArgumentParser(description='', add_help=False)
    parser.add_argument('-d', default=[], action='append')
    parser.add_argument('-h', '--help', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')
    # only intended to be used for tab completion
    parser.add_argument('--suppress-warn', action='store_true')
    parser.add_argument('verb', nargs='?', default='')
    if 'show' in sys.argv:
        parser = add_show_arguments(parser)
    elif 'create' in sys.argv:
        noun = ''
        if 'project' in sys.argv:
            noun = 'project'
        if 'library' in sys.argv:
            noun = 'library'
        if 'component' in sys.argv:
            noun = 'component'
        if 'test' in sys.argv:
            noun = 'test'
        if 'application' in sys.argv:
            noun = 'application'
        if 'protocol' in sys.argv:
            noun = 'protocol'
        parser = add_create_arguments(parser, noun)
    elif 'build' in sys.argv:
        parser = add_build_arguments(parser)
    else:
        parser.add_argument('noun', nargs='?', default=None)
        parser.add_argument('name', nargs='?', default=None)
    return parser


def get_args(parser):
    # below 3 lines parse, allowing for posix conformance (intermixed args)
    (args, unknown_args) = parser.parse_known_args()
    for unknown_arg in unknown_args:
        args.noun = unknown_arg
    return args


def get_cli_dict():
    """ get a dictionary of settings which looks like CLI args and has been
        modified as needed """
    args = get_args(get_arg_parser())
    nouns = ['application', 'applications', 'registry', 'platform',
             'platforms', 'project', 'projects', 'protocol', 'libraries',
             'component', 'components', 'workers', 'library', 'component',
             'test', 'tests']
    Logger().debug('args : ' + str(args))
    try:
        if args.authoring_model in nouns:
            args.name = args.noun
            args.noun = args.authoring_model
            args.authoring_model = ''
    except AttributeError:
        # TODO replace this hack
        args.authoring_model = None
    # TODO move below 3 lines to AssetBase once proper checks in place
    if args.verb != 'unittest':
        if args.name:
            if not args.name.isidentifier():
                raise ValueError("'" + args.name + "' is not a valid name")
        if not args.help:
            if (args.noun is not None) and (args.noun not in nouns):
                if args.verb != 'apply':
                    msg = 'noun ' + str(args.noun) + ' is not supported'
                    raise Exception(msg)
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
    cli_dict = ({key.replace('_', ''): val for key, val in cli_dict.items()})
    return cli_dict


def _help(cli_dict, project_registry):
    if cli_dict['verb'] == '':
        os.system('man ocpidev2')
    else:
        os.system('man ocpidev2-' + cli_dict['verb'])


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
                if cli_dict['noun'].startswith('application'):
                    for application in project.applications:
                        if (cli_dict['name'] is None) or \
                           (cli_dict['name'] == application.name):
                            if (_dir == '') or \
                               (_dir in application.abs_path):
                                msg = str(project.get_package_id()) + '.'
                                msg += application.name
                                if cli_dict['verbose']:
                                    msg += ' '
                                    for idx in range(60-len(msg)):
                                        msg += ' '
                                    msg += application.abs_path
                                print(msg)
                if cli_dict['noun'].startswith('component'):
                    for component in project.components:
                        if (cli_dict['name'] is None) or \
                                (cli_dict['name'] == component.name):
                            if (_dir == '') or \
                                   (_dir in component.abs_path):
                                msg = str(project.get_package_id()) + '.'
                                msg += component.name
                                if cli_dict['verbose']:
                                    msg += ' '
                                    for idx in range(60-len(msg)):
                                        msg += ' '
                                    msg += component.abs_path
                                print(msg)
                if cli_dict['noun'].startswith('librar'):
                    for hdl_primitive in project.hdl_primitives:
                        if (cli_dict['name'] is None) or \
                                (cli_dict['name'] == hdl_primitive.name):
                            if (_dir == '') or \
                               (_dir in hdl_primitive.abs_path):
                                if (cli_dict['authoringmodel'] == '') or \
                                        (cli_dict['authoringmodel'] == 'hdl'):
                                    msg = str(project.get_package_id()) + '.'
                                    msg += hdl_primitive.name
                                    if cli_dict['verbose']:
                                        msg += ' '
                                        for idx in range(50-len(msg)):
                                            msg += ' '
                                        msg += hdl_primitive.abs_path
                                    print(msg)
                if cli_dict['noun'].startswith('project'):
                    if (cli_dict['name'] is None) or \
                       (cli_dict['name'] == project.name):
                        if (_dir == '') or \
                           (_dir in project.abs_path):
                            msg = str(project.get_package_id())
                            if cli_dict['verbose']:
                                msg += ' '
                                for idx in range(30-len(msg)):
                                    msg += ' '
                                msg += project.abs_path
                            print(msg)
                if cli_dict['noun'].startswith('platform'):
                    for hdl_platform in project.hdl_platforms:
                        if (cli_dict['name'] is None) or \
                                (cli_dict['name'] == hdl_platform.name):
                            if (_dir == '') or \
                               (_dir in hdl_platform.abs_path):
                                if (cli_dict['authoringmodel'] == '') or \
                                        (cli_dict['authoringmodel'] == 'hdl'):
                                    msg = hdl_platform.name
                                    if cli_dict['verbose']:
                                        msg += ' '
                                        for idx in range(50-len(msg)):
                                            msg += ' '
                                        msg += hdl_platform.abs_path
                                    print(msg)
                    for rcc_platform in project.rcc_platforms:
                        if (cli_dict['name'] is None) or \
                                (cli_dict['name'] == rcc_platform.name):
                            if (_dir == '') or \
                               (_dir in rcc_platform.abs_path):
                                if (cli_dict['authoringmodel'] == '') or \
                                        (cli_dict['authoringmodel'] == 'rcc'):
                                    msg = rcc_platform.name
                                    if cli_dict['verbose']:
                                        msg += ' '
                                        for idx in range(50-len(msg)):
                                            msg += ' '
                                        msg += rcc_platform.abs_path
                                    print(msg)
                for component_library in project.component_libraries:
                    ppid = str(project.get_package_id())
                    pid = component_library.get_package_id(ppid)
                    if cli_dict['noun'].startswith('librar'):
                        if (cli_dict['name'] is None) or \
                                (cli_dict['name'] == component_library.name):
                            if (_dir == '') or \
                               (_dir in component_library.abs_path):
                                if cli_dict['authoringmodel'] == '':
                                    msg = pid
                                    if cli_dict['verbose']:
                                        msg += ' '
                                        for idx in range(50-len(msg)):
                                            msg += ' '
                                        msg += component_library.abs_path
                                    print(msg)
                    if cli_dict['noun'].startswith('component'):
                        for component in component_library.components:
                            if (cli_dict['name'] is None) or \
                                    (cli_dict['name'] == component.name):
                                if (_dir == '') or \
                                   (_dir in component.abs_path):
                                    msg = pid + '.' + component.name
                                    if cli_dict['verbose']:
                                        msg += ' '
                                        for idx in range(60-len(msg)):
                                            msg += ' '
                                        msg += component.abs_path
                                    print(msg)
                    if cli_dict['noun'] == 'workers':
                        for worker in component_library.workers:
                            if (_dir == '') or \
                               (_dir in worker.abs_path):
                                if (cli_dict['authoringmodel'] == '') or \
                                       (cli_dict['authoringmodel'] ==
                                        worker.authoring_model):
                                    msg = pid + '.' + worker.name + '.' + \
                                          worker.authoring_model
                                    if cli_dict['verbose']:
                                        msg += ' '
                                        for idx in range(50-len(msg)):
                                            msg += ' '
                                        msg += worker.abs_path
                                    print(msg)
                    if cli_dict['noun'].startswith('test'):
                        for test in component_library.tests:
                            if (_dir == '') or \
                               (_dir in test.abs_path):
                                msg = pid + '.' + test.name
                                if cli_dict['verbose']:
                                    msg += ' '
                                    for idx in range(50-len(msg)):
                                        msg += ' '
                                    msg += test.abs_path
                                print(msg)


def get_create_registry(cli_dict):
    create_registry = False
    if cli_dict['verb'] == 'show':
        create_registry = True
    return create_registry


def get_enable_registry_discovery(cli_dict):
    disc = True
    if cli_dict['verb'] == 'show':
        disc = cli_dict['noun'] != 'registry'
        disc = disc and (cli_dict['noun'] != 'projects')
    if cli_dict['help']:
        disc = False
    return disc


global g_suppress_warn


if __name__ == '__main__':
    exit_status = 0
    try:
        signal.signal(signal.SIGINT, ocpidevsignint)
        cli_dict = get_cli_dict()
        if cli_dict['suppresswarn']:
            set_g_suppress_warn(True)
        Logger().debug('cli_dict : ' + str(cli_dict))
        project_registry = None
        if get_create_registry(cli_dict):
            disc = get_enable_registry_discovery(cli_dict)
            project_registry = ProjectRegistry(disc, disc)
        if cli_dict['help']:
            _help(cli_dict, project_registry)
        elif cli_dict['verb'] == 'show':
            show(cli_dict, project_registry)
        elif cli_dict['verb'] == 'unittest':
            unittest(cli_dict, project_registry)
        else:
            raise Exception('verb ' + cli_dict['verb'] + ' is not supported')
    except Exception as exception:
        Logger().error(str(exception))
        exit_status = 1
    exit(exit_status)
