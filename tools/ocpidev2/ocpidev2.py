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
from _opencpi.assets.library2 import ComponentLibrary


def ocpidevsignint(sig, frame):
    raise Exception('Ctrl-C stopped execution')


def add_build_arguments(parser, noun):
    parser.add_argument('--hdl-target', default=[], action='append')
    parser.add_argument('--hdl-platform', default=[], action='append')
    parser.add_argument('--rcc-platform', default=[], action='append')
    parser.add_argument('-j', nargs='?', type=int, default=1)
    parser.add_argument('noun', nargs='?', default=None)
    parser.add_argument('name', nargs='?', default=None)
    return parser


def add_create_arguments(parser, noun):
    """ add create-specific arguments as per man ocpidev-create """
    parser.add_argument('-k', '--keep', default=False, action='store_true')
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
    if noun == 'protocol':
        group = parser.add_mutually_exclusive_group()
        group.add_argument('-p', '--project', default=False, action='store_true')
        group.add_argument('--hdl-library', nargs='?', default='')
        group.add_argument('-l', '--library', default=None)
    parser.add_argument('noun', default=None)
    parser.add_argument('name', default=None)
    return parser


def add_show_arguments(parser, noun):
    parser.add_argument('--global-scope', default=False, action='store_true')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--simple', default=False, action='store_true')
    group.add_argument('--table', default=False, action='store_true')
    group.add_argument('--json', default=False, action='store_true')
    parser.add_argument('authoring_model', nargs='?', default='')
    parser.add_argument('noun', nargs='?', default=None)
    parser.add_argument('name', nargs='?', default=None)
    return parser


def add_run_arguments(parser, noun):
    parser.add_argument('-G', '--only-platform', default=False, action='store_true')
    parser.add_argument('-O', '--exclude-platform', default=False, action='store_true')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--hdl-library', nargs='?', default='')
    group.add_argument('-l', '--library', default=None)
    parser.add_argument('--accumulate-errors', default=False, action='store_true')
    parser.add_argument('--case', default=[], action='append')
    parser.add_argument('--keep-simulations', default=False, action='store_true')
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
        args.noun = unknown_arg
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
            args.name = args.noun
            args.noun = args.authoring_model
            args.authoring_model = ''
        if args.name in nouns:
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
            else:
                args.adjective = ''
                args.noun = args.name
            args.name = None
        if (args.authoring_model != '') and \
           (args.authoring_model != 'hdl') and \
           (args.authoring_model != 'rcc'):
            raise Exception('invalid authoring model: ' + args.authoring_model)
    except AttributeError:
        # TODO replace this hack
        args.authoring_model = ''
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
    for _dir in mylist:
        _dir = os.path.normpath(os.path.abspath(_dir))
        if _dir in tmp.d:
            Logger().warn('-d has duplicate ' + _dir)
        else:
            tmp.d.append(_dir)
    cli_dict = vars(tmp)
    # make CLI look like attrs (necessary for create cli verb)
    cli_dict = ({key.replace('_', ''): val for key, val in cli_dict.items()})
    return cli_dict


def get_create_registry(cli_dict):
    create_registry = False
    if cli_dict['verb'] == 'clean':
        create_registry = True
    if cli_dict['verb'] == 'create':
        create_registry = True
    if cli_dict['verb'] == 'build':
        create_registry = True
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


# TODO delete
global g_suppress_warn


def _help(cli_dict, project_registry):
  if cli_dict['verb'] == '':
      os.system('man ocpidev2')
  else:
      os.system('man ocpidev2-' + cli_dict['verb'])

def build(cli_dict, project_registry):
    # may eventually support unregistered projects in addition to registry,
    # but probably not
    project_registry.build(cli_dict)

def clean(cli_dict, project_registry):
    # may eventually support unregistered projects in addition to registry,
    # but probably not
    project_registry.clean(cli_dict)

def create(cli_dict, project_registry):
    # may eventually support unregistered projects in addition to registry,
    # but probably not
    project_registry.create(cli_dict)

def delete(cli_dict, project_registry):
    # may eventually support unregistered projects in addition to registry,
    # but probably not
    project_registry.delete(cli_dict)

def run(cli_dict, project_registry):
    # may eventually support unregistered projects in addition to registry,
    # but probably not
    project_registry.run(cli_dict)

def show(cli_dict, project_registry):
    # may eventually support unregistered projects in addition to registry,
    # but probably not
    project_registry.show(cli_dict)

def main():
    ret = 0
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
        elif cli_dict['verb'] == 'build':
            build(cli_dict, project_registry)
        elif cli_dict['verb'] == 'clean':
            clean(cli_dict, project_registry)
        elif cli_dict['verb'] == 'create':
            create(cli_dict, project_registry)
        elif cli_dict['verb'] == 'show':
            show(cli_dict, project_registry)
        elif cli_dict['verb'] == 'unittest':
            unittest(cli_dict, project_registry)
        else:
            raise Exception('verb ' + cli_dict['verb'] + ' is not supported')
    except Exception as exception:
        Logger().error(str(exception))
        ret = 1
    return ret

if __name__ == '__main__':
    exit(main())
