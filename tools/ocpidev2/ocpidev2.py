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
from _opencpi.assets.registry2 import ProjectRegistry, unittest
from _opencpi.assets.project2 import Project
# below imports only necessary for get_attr_infos() calls
from _opencpi.assets.component2 import Component
from _opencpi.assets.library2 import ComponentLibrary
from _opencpi.assets.test2 import Test
from _opencpi.assets.worker2 import Worker


def ocpidevsignint(sig, frame):
    """ add create-specific arguments as per man ocpidev2-build """
    raise Exception('Ctrl-C stopped execution')


def add_create_show_build_arguments(parser):
    parser.add_argument('authoring_model', nargs='?', default='')
    parser.add_argument('noun', nargs='?', default=None)
    parser.add_argument('name', nargs='?', default=None)
    return parser

def add_build_arguments(parser, noun):
    parser.add_argument('--hdl-target', default=[], action='append')
    parser.add_argument('--hdl-platform', default=[], action='append')
    parser.add_argument('--rcc-platform', default=[], action='append')
    parser.add_argument('-j', nargs='?', type=int, default=1)
    parser = add_create_show_build_arguments(parser)
    return parser


def add_create_arguments(parser, noun):
    """ add create-specific arguments as per man ocpidev2-create """
    parser.add_argument('-k', '--keep', default=False, action='store_true')
    asset = None
    if noun == 'project':
        asset = Project('', False, None)
        parser.add_argument('--register', default=False, action='store_true')
    if noun == 'library':
        asset = ComponentLibrary('', False, None)
    if noun == 'component':
        asset = Component('', False, None)
        parser.add_argument('-t', '--create-test', default=False,
                            action='store_true')
        parser.add_argument('-p', '--project', default=False,
                            action='store_true')
    if noun == 'test':
        asset = Test('', False, None)
    if noun == 'application':
        group = parser.add_mutually_exclusive_group()
        group.add_argument('-X', '--xml-app', default=False,
                           action='store_true')
        group.add_argument('-x', '--xml-dir-app', default=False,
                           action='store_true')
    if noun == 'protocol':
        group = parser.add_mutually_exclusive_group()
        group.add_argument('-p', '--project', default=False,
                           action='store_true')
        group.add_argument('--hdl-library', nargs='?', default='')
        group.add_argument('-l', '--library', default=None)
    if noun == 'primitive':
        parser.add_argument('-p', '--project', default=False,
                            action='store_true')
    if noun == 'worker':
        # dict created to weed out unnecessary warnings...
        asset = Worker('', False, {'language': 'vhdl', 'version': 2})
    if asset is not None:
        for attr in asset.get_attr_infos():
            if attr.cli is not None:
                if attr.is_bool:
                    parser.add_argument(attr.cli[0], attr.cli[1],
                            default=([] if attr.is_list else (False if attr.is_bool else '')),
                            action=('append' if attr.is_list else (('store_true' if attr.is_bool else 'store'))))
                else:
                    parser.add_argument(attr.cli[0], attr.cli[1], nargs='?',
                            default=([] if attr.is_list else (False if attr.is_bool else '')),
                            action=('append' if attr.is_list else (('store_true' if attr.is_bool else 'store'))))
    parser = add_create_show_build_arguments(parser)
    return parser


def add_delete_arguments(parser, noun):
    # TODO this should probably be done better
    return add_create_arguments(parser, noun)

def add_show_arguments(parser, noun):
    """ add create-specific arguments as per man ocpidev2-show """
    parser.add_argument('--global-scope', default=False, action='store_true')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--simple', default=False, action='store_true')
    group.add_argument('--table', default=False, action='store_true')
    group.add_argument('--json', default=False, action='store_true')
    parser = add_create_show_build_arguments(parser)
    return parser


def add_run_arguments(parser, noun):
    parser.add_argument('-G', '--only-platform', default=False,
                        action='store_true')
    parser.add_argument('-O', '--exclude-platform', default=False,
                        action='store_true')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--hdl-library', nargs='?', default='')
    group.add_argument('-l', '--library', default=None)
    parser.add_argument('--accumulate-errors', default=False,
                        action='store_true')
    parser.add_argument('--case', default=[], action='append')
    parser.add_argument('--keep-simulations', default=False,
                        action='store_true')
    parser.add_argument('--phase', default=[], action='append')
    parser.add_argument('--remotes', nargs='?', default='')
    parser.add_argument('--view', default=False, action='store_true')
    return parser


def get_arg_parser():
    parser = argparse.ArgumentParser(description='', add_help=False)
    parser.add_argument('-d', default=[], action='append')
    parser.add_argument('-h', '--help', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')
    # only intended to be used for tab completion
    parser.add_argument('--suppress-warn', action='store_true')
    parser.add_argument('verb', nargs='?', default='')
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
    if 'worker' in sys.argv:
        noun = 'worker'
    if 'build' in sys.argv:
        parser = add_build_arguments(parser, noun)
    elif 'create' in sys.argv:
        parser = add_create_arguments(parser, noun)
    elif 'show' in sys.argv:
        parser = add_show_arguments(parser, noun)
    elif 'run' in sys.argv:
        parser = add_run_arguments(parser, noun)
    else:
        parser.add_argument('noun', nargs='?', default=None)
        parser.add_argument('name', nargs='?', default=None)
    return parser


def get_args(parser):
    # below 3 lines parse, allowing for posix conformance (intermixed args)
    (args, unknown_args) = parser.parse_known_args()
    for unknown_arg in unknown_args:
        if unknown_arg.startswith('application') or \
           unknown_arg.startswith('assembl') or \
           unknown_arg.startswith('component') or \
           unknown_arg.startswith('card') or \
           unknown_arg.startswith('device') or \
           unknown_arg.startswith('project') or \
           unknown_arg.startswith('registr') or \
           unknown_arg.startswith('slot') or \
           unknown_arg.startswith('librar') or \
           unknown_arg.startswith('test'):
            args.noun = unknown_arg
        else:
            raise Exception('invalid argument: ' + unknown_arg)
    return args


def get_cli_dict():
    """ get a dictionary of settings which looks like CLI args and has been
        modified as needed """
    args = get_args(get_arg_parser())
    nouns = ['assembly', 'assemblies',
             'application', 'applications',
             'core', 'cores',
             'card', 'cards',
             'component', 'components',
             'platform', 'platforms',
             'primitive', 'primitives',
             'project', 'projects',
             'protocol', 'protocols',
             'registry',
             'library', 'libraries',
             'slot', 'slots',
             'test', 'tests',
             'worker', 'workers']
    Logger().debug('args : ' + str(args))
    try:
        args.adjective = ''
        if args.authoring_model in nouns:
            # first correction - extract proper authoring model and align the rest
            args.name = args.noun
            args.noun = args.authoring_model
            args.authoring_model = ''
        Logger().debug('args : ' + str(args))
        if (args.name in nouns) and args.noun.startswith('primitive'):
            if args.name == 'core':
                args.adjective = 'core'
                args.noun = 'primitive'
            elif args.name == 'cores':
                args.adjective = 'core'
                args.noun = 'primitives'
            elif args.name == 'library':
                args.adjective = 'library'
                args.noun = 'primitive'
            elif args.name == 'libraries':
                args.adjective = 'library'
                args.noun = 'primitives'
            elif (args.name != 'platform') and (args.name != 'protocol'):
                args.adjective = ''
                args.noun = args.name
            if (args.name != 'platform') and (args.name != 'protocol'):
                args.name = None
        Logger().debug('args : ' + str(args))
        if (args.authoring_model != '') and \
           (args.authoring_model != 'hdl') and \
           (args.authoring_model != 'rcc'):
            raise Exception('invalid authoring model: ' + args.authoring_model)
    except AttributeError:
        # TODO replace this hack
        args.authoring_model = ''
    # TODO move below 3 lines to AssetBase once proper checks in place
    if args.verb != 'unittest':
        if args.noun == 'worker':
            if not (('.hdl' in args.name) or \
                    ('.rcc' in args.name) or \
                    ('.ocl' in args.name)):
                raise Exception(args.name + ' is and invalid worker name')
            args.authoring_model = args.name.split('.')[1]
            args.name = args.name.split('.')[0]
        elif args.noun == 'test':
            if not ('.test' in args.name):
                raise Exception(args.name + ' is and invalid test name')
            args.name = args.name.split('.')[0]
        else:
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
    for _dir in mylist:
        _dir = os.path.normpath(os.path.abspath(_dir))
        if _dir in tmp.d:
            Logger().warn('-d has duplicate ' + _dir)
        else:
            tmp.d.append(_dir)
    cli_dict = vars(tmp)
    if (cli_dict['noun'] == 'worker'):
       if ('.' in cli_dict['name']):
          if not (('.hdl' in cli_dict['name']) or \
             ('.rcc' in cli_dict['name']) or \
             ('.ocl' in cli_dict['name'])):
              raise Exception(cli_dict['name'] + ' is and invalid worker name')
    if (cli_dict['noun'] == 'test'):
       if ('.' in cli_dict['name']):
            if not ('.test' in cli_dict['name']):
              raise Exception(cli_dict['name'] + ' is and invalid test name')
    # make CLI look like attrs (necessary for create cli verb)
    cli_dict = ({key.replace('_', ''): val for key, val in cli_dict.items()})
    return cli_dict


# TODO delete
global g_suppress_warn

def get_local_project(_dir):
    project = None
    project_dir_abs_path = _dir
    while True:
        try:
            project = Project(project_dir_abs_path, True)
            project.discover()
            break
        except InvalidAssetError:
            project_dir_abs_path = project_dir_abs_path.rsplit('/', 1)[0]
            if len(project_dir_abs_path) <= 1:
                break
    #if project == None:
    #    raise Exception('directory ' + _dir + ' is not within a project')
    return project

def dispatch_verb(cli_dict):
    """ this method implements functionality common across verbs, then
        dispatches to individual verb calls """
    project_registry = None
    if cli_dict['help']:
        if cli_dict['verb'] == '':
            os.system('man ocpidev2')
        else:
            os.system('man ocpidev2-' + cli_dict['verb'])
    else:
        if cli_dict['d'] == []:
            cli_dict['d'].append(Environment().getcwd())
        for _dir in cli_dict['d']:
            local_project = get_local_project(_dir)
            if ((cli_dict['verb'] == 'create') and (local_project is None)) or \
               (cli_dict['verb'] != 'create'):
                project_registry = ProjectRegistry(True, True)
            if not ((cli_dict['verb'] == 'create') and (cli_dict['noun'] == 'library')):
                msg = 'performing \'' + cli_dict['verb']
                if cli_dict['noun'] != None:
                    msg += ' ' + cli_dict['noun']
                if cli_dict['name'] != None:
                    msg += ' ' + cli_dict['name']
                msg += '\''
                Logger().log(3, msg + ' within directory ' + _dir)
            if cli_dict['verb'] == 'build':
                project_registry.build(cli_dict, _dir)
            elif cli_dict['verb'] == 'clean':
                project_registry.clean(cli_dict, _dir)
            elif cli_dict['verb'] == 'create':
                if local_project is None:
                    project_registry.create(cli_dict, _dir)
                else:
                    local_project.create_asset(cli_dict, _dir)
            elif cli_dict['verb'] == 'delete':
                project_registry.delete(cli_dict, _dir)
            elif cli_dict['verb'] == 'refresh':
                Logger().warn('refresh is not necessary in ocpidev2')
            elif cli_dict['verb'] == 'register':
                project_registry.register(cli_dict, _dir)
            elif cli_dict['verb'] == 'run':
                project_registry.run(cli_dict, _dir)
            elif cli_dict['verb'] == 'show':
                project_registry.show(cli_dict, _dir)
            elif cli_dict['verb'] == 'unregister':
                project_registry.unregister(cli_dict, _dir)
            else:
                raise Exception('verb ' + cli_dict['verb'] + ' is not supported')
            if (cli_dict['verb'] == 'create') and (cli_dict['noun'] == 'library'):
                # this message is printed below and not above due to weird create
                # components dir message of same form in project2.py that needs
                # to happen first
                msg = 'performing \'' + cli_dict['verb']
                if cli_dict['noun'] != None:
                    msg += ' ' + cli_dict['noun']
                if cli_dict['name'] != None:
                    msg += ' ' + cli_dict['name']
                msg += '\''
                Logger().log(3, msg + ' within directory ' + _dir)

def main():
    ret = 0
    try:
        signal.signal(signal.SIGINT, ocpidevsignint)
        cli_dict = get_cli_dict()
        if cli_dict['suppresswarn']:
            set_g_suppress_warn(True)
        Logger().debug('cli_dict : ' + str(cli_dict))
        dispatch_verb(cli_dict)
    except Exception as exception:
        Logger().error(str(exception))
        ret = 1
    return ret


if __name__ == '__main__':
    exit(main())
