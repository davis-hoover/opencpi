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


""" This file exposes the Command Line Interface (CLI) below it, and above it
    interfaces with project-like things (ProjectDatabase), and not individual
    asset classes. """


import os
import argparse
import signal
from _opencpi.assets.abstract2 import *
# IMPORTANT - interface with ProjectDatabase, nothing else
from _opencpi.assets.registry2 import ProjectDatabase


def ocpidevsignint(sig, frame):
    """ add create-specific arguments as per man ocpidev2-build """
    raise Exception('Ctrl-C stopped execution')


def add_build_create_show_arguments(parser):
    parser.add_argument('authoring_model', nargs='?', default='')
    parser.add_argument('noun', nargs='?', default=None)
    parser.add_argument('librarytype', nargs='?', default=None)
    parser.add_argument('name', nargs='?', default=None)
    return parser


def add_build_arguments(parser):
    parser.add_argument('--hdl-target', default=[], action='append')
    parser.add_argument('--hdl-platform', default=[], action='append')
    parser.add_argument('--rcc-platform', default=[], action='append')
    parser.add_argument('-j', nargs='?', type=int, default=1)
    parser = add_build_create_show_arguments(parser)
    return parser


def add_create_arguments(parser, noun, authoring_model=''):
    """ add create-specific arguments as per man ocpidev2-create """
    parser.add_argument('-k', '--keep', default=False, action='store_true')
    asset = ProjectDatabase.get_asset_for_create(noun)
    if noun == 'application':
        group = parser.add_mutually_exclusive_group()
        group.add_argument('-X', '--xml-app', default=False,
                           action='store_true')
        group.add_argument('-x', '--xml-dir-app', default=False,
                           action='store_true')
    if noun in ['adapter', 'component', 'device', 'primitive', 'protocol',
                'worker', 'test']:
        group = parser.add_mutually_exclusive_group()
        group.add_argument('--hdl-library', nargs='?', default=None)
        group.add_argument('--library', default=None)
        parser.add_argument('-P', '--platform', default=False)
        if noun in ['component', 'protocol']:
            group.add_argument('-p', '--project', default=False,
                               action='store_true')
    if noun == 'component':
        parser.add_argument('-t', '--create-test', default=False,
                            action='store_true')
    if noun == 'project':
        parser.add_argument('--register', default=False, action='store_true')
    if noun == 'worker':
        parser.add_argument('-W', '--worker', default=[],
                            action='append')
    if asset is not None:
        for attr in asset.get_attr_infos():
            if attr.cli is not None:
                if attr.is_bool:
                    _default = [] if attr.is_list else False
                    _action = 'append' if attr.is_list else \
                              ('store_true' if attr.is_bool else 'store')
                    parser.add_argument(attr.cli[0], attr.cli[1],
                                        default=_default, action=_action)
                else:
                    _default = [] if attr.is_list else \
                               (0 if attr.is_int else '')
                    _action = 'append' if attr.is_list else \
                              ('store_true' if attr.is_bool else 'store')
                    parser.add_argument(attr.cli[0], attr.cli[1], nargs='?',
                                        default=_default, action=_action)
    parser = add_build_create_show_arguments(parser)
    return parser


def add_delete_arguments(parser):
    # TODO this should probably be done better
    return add_create_arguments(parser, '')


def add_show_arguments(parser):
    """ add create-specific arguments as per man ocpidev2-show """
    group1 = parser.add_mutually_exclusive_group()
    group1.add_argument('--local-scope', default=False, action='store_true')
    group1.add_argument('--global-scope', default=True, action='store_true')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--simple', default=False, action='store_true')
    group.add_argument('--table', default=False, action='store_true')
    group.add_argument('--json', default=False, action='store_true')
    parser = add_build_create_show_arguments(parser)
    return parser


def add_run_arguments(parser, noun):
    parser.add_argument('-G', '--only-platform', default=False,
                        action='store_true')
    parser.add_argument('-O', '--exclude-platform', default=False,
                        action='store_true')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--hdl-library', nargs='?', default='')
    group.add_argument('-M', '--library', default=None)
    parser.add_argument('--accumulate-errors', default=False,
                        action='store_true')
    parser.add_argument('--case', default=[], action='append')
    parser.add_argument('--keep-simulations', default=False,
                        action='store_true')
    parser.add_argument('--phase', default=[], action='append')
    parser.add_argument('--remotes', nargs='?', default='')
    parser.add_argument('--view', default=False, action='store_true')
    return parser


def get_cli_noun_verb_tuple(argv):
    verb = ''
    noun = ''
    state = 0
    verbs = ['build', 'clean', 'create', 'delete', 'show', 'run']
    singular_nouns = ['application', 'adapter', 'assembly', 'card',
                      'component', 'device', 'library', 'slot', 'test',
                      'primitive', 'project', 'protocol', 'platform',
                      'registry', 'worker']
    plural_nouns = ['applications', 'adapters', 'assemblies', 'components',
                    'devices', 'libraries', 'slots', 'tests', 'primitives',
                    'projects', 'platforms', 'protocols', 'workers']
    special_nouns = ['primitive', 'library', 'core']
    allow_exception = False
    # state machine with states:
    # 0: waiting on verb
    # 1: waiting on noun
    # 2: got a -<option> or --<option>, waiting on value of that option
    #    (necessary for intermixed arguments)
    for idx in range(len(argv)):
        # print(state)
        # print(argv[idx])
        if (state == 0) and (argv[idx] in verbs):
            verb = argv[idx]
            state = 1
        elif (state == 1):
            if argv[idx][0] == '-':
                state = 2
            elif argv[idx] in ['hdl', 'rcc', 'ocl']:
                pass  # authoring_model = argv[idx]
            elif argv[idx] in ['primitive', 'primitives']:
                noun = argv[idx]
                state = 2
            elif (argv[idx] == 'library') and (argv[idx-1] == 'primitive'):
                pass
            elif (argv[idx] == 'libraries') and (argv[idx-1] == 'primitive'):
                pass
            elif (argv[idx] == 'core') and (argv[idx-1] == 'primitive'):
                pass
            elif (argv[idx] == 'cores') and (argv[idx-1] == 'primitive'):
                pass
            elif argv[idx] in (singular_nouns + plural_nouns):
                noun = argv[idx]
                break
                state = 2
            elif allow_exception:
                raise Exception('invalid noun: ' + argv[idx])
        elif (state == 2):
            allow_exception = False
            state = 1
    return (noun, verb)


def get_arg_parser():
    parser = argparse.ArgumentParser(description='', add_help=False)
    parser.add_argument('-d', default=[], action='append')
    parser.add_argument('-h', '--help', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-l', '--log-level', nargs='?', default=0, type=int)
    # only intended to be used for tab completion
    parser.add_argument('--suppress-warn', action='store_true')
    parser.add_argument('verb', nargs='?', default='')
    (noun, verb) = get_cli_noun_verb_tuple(sys.argv)
    if verb == 'build':
        parser = add_build_arguments(parser)
    elif verb == 'create':
        parser = add_create_arguments(parser, noun)
    elif verb == 'show':
        parser = add_show_arguments(parser)
    elif verb == 'run':
        parser = add_run_arguments(parser)
    else:
        parser.add_argument('noun', nargs='?', default=None)
        parser.add_argument('name', nargs='?', default=None)
    return parser


def get_args(parser):
    # below 3 lines parse, allowing for posix conformance (intermixed args)
    (args, unknown_args) = parser.parse_known_args()
    print(str(unknown_args))
    for unknown_arg in unknown_args:
        if unknown_arg.startswith('application') or \
           unknown_arg.startswith('assembl') or \
           unknown_arg.startswith('component') or \
           unknown_arg.startswith('card') or \
           unknown_arg.startswith('device') or \
           unknown_arg.startswith('platform') or \
           unknown_arg.startswith('project') or \
           unknown_arg.startswith('protocol') or \
           unknown_arg.startswith('primitive') or \
           unknown_arg.startswith('registr') or \
           unknown_arg.startswith('slot') or \
           unknown_arg.startswith('librar') or \
           unknown_arg.startswith('target') or \
           unknown_arg.startswith('test') or \
           unknown_arg.startswith('worker'):
            args.noun = unknown_arg
        elif unknown_arg in get_authoring_models():
            args.auhoring_model = unknown_arg
        elif unknown_arg in ['core', 'cores', 'library', 'libraries']:
            args.noun = 'primitive'
            # later set to adjective...
            args.name = unknown_arg
        elif unknown_arg in ['--xml-dir-app']:
            args.xml_dir_app = unknown_arg  # no idea why this is necessary...
            args.xml_app = None  # no idea why this is necessary...
        else:
            raise Exception('invalid argument: ' + unknown_arg)
    return args


def get_cli_dict():
    """ get a dictionary of settings which looks like CLI """
    args = get_args(get_arg_parser())
    nouns = ['adapter', 'adapters',
             'assembly', 'assemblies',
             'application', 'applications',
             'core', 'cores',
             'card', 'cards',
             'device', 'devices',
             'component', 'components',
             'platform', 'platforms',
             'primitive', 'primitives',
             'project', 'projects',
             'protocol', 'protocols',
             'registry',
             'library', 'libraries',
             'slot', 'slots',
             'target', 'targets',
             'test', 'tests',
             'worker', 'workers']
    # Logger().debug('args : ' + str(args))
    try:
        args.adjective = ''
        if args.authoring_model in nouns:
            # first correction - extract proper authoring model and align the
            # rest
            args.name = args.noun
            args.noun = args.authoring_model
            args.authoring_model = ''
        if args.name is None:
            if args.librarytype != '':
                args.name = args.librarytype
                del args.librarytype
        # Logger().debug('args : ' + str(args))
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
        # Logger().debug('args : ' + str(args))
    except AttributeError:
        # TODO replace this hack
        args.authoring_model = ''
    # TODO move below 3 lines to AssetBase once proper checks in place
    if args.verb != 'unittest':
        if args.noun is not None:
            if not ProjectDatabase.is_worker(args.noun):
                if args.name:
                    if args.noun.startswith('test'):
                        if '.test' in args.name:
                            args.name = args.name.split('.test')[0]
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
    if (cli_dict['noun'] == 'worker') or (cli_dict['noun'] == 'device') or \
       (cli_dict['noun'] == 'adapter'):
        if cli_dict['name'] == None:
            msg = 'name must be specified for \'' + cli_dict['noun'] + '\''
            raise Exception(msg)
        authoring_model_from_name = cli_dict['name'].split('.')[-1]
        authoring_model_is_in_name = '.' in cli_dict['name']
        if authoring_model_is_in_name:
            if authoring_model_from_name not in ['hdl', 'rcc']:
                msg = '\'' + authoring_model_from_name + '\' is an '
                msg += 'invalid authoring model (must be \'hdl\' or '
                msg += '\'rcc\')'
                raise Exception(msg)
        if cli_dict['authoringmodel'] == '':
            if not authoring_model_is_in_name:
                msg = cli_dict['name']
                msg += ' does not have an authoring model, please format the '
                msg += 'name as <foo>.<model>, e.g., \'ocpidev2 create '
                msg += 'worker foo.hdl\''
                raise Exception(msg)
            cli_dict['authoringmodel'] = authoring_model_from_name
        else:
            if cli_dict['authoringmodel'] not in ['hdl', 'rcc']:
                msg = '\'' + cli_dict['authoringmodel'] + '\' is an '
                msg += 'invalid authoring model (must be \'hdl\' or '
                msg += '\'rcc\')'
                raise Exception(msg)
            if authoring_model_is_in_name:
                if cli_dict['authoringmodel'] != authoring_model_from_name:
                    msg = 'authoring model '
                    msg += '\'' + cli_dict['authoringmodel'] + '\' '
                    msg += 'does not match authoring model specified in name '
                    msg += '\'' + cli_dict['name'] + '\' '
                    raise Exception(msg)
        if not authoring_model_is_in_name:
            msg = '<name> ' + '\'' + cli_dict['name'] + '\''
            msg += ' was not specified with an authoring model suffix, '
            msg += 'it is recommended to '
            msg += 'format the name as <foo>.<model>, e.g., \'ocpidev2 '
            msg += 'create worker foo.hdl\''
            Logger().warn(msg)
        cli_dict['name'] = cli_dict['name'].split('.')[0]
    if cli_dict['noun'] is not None:
        bad_hdl = (cli_dict['authoringmodel'] == 'hdl') and \
                  (not ProjectDatabase.is_hdl(cli_dict['noun']))
        bad_rcc = (cli_dict['authoringmodel'] == 'rcc') and \
                  (not ProjectDatabase.is_rcc(cli_dict['noun']))
        msg = 'authoring model '
        if bad_hdl or bad_rcc:
            if bad_none:
                msg += 'must be specified '
            else:
                msg += '\'' + cli_dict['authoringmodel'] + '\' '
                msg += 'is invalid '
            msg += 'for noun \'' + cli_dict['noun'] + '\''
            raise Exception(msg)
    if cli_dict['noun'] is not None:
        if cli_dict['noun'].endswith('s'):
            if cli_dict['name'] is not None:
                msg = 'cannot specify name when noun \'' + cli_dict['noun']
                msg += '\' is plural'
                raise Exception(msg)
        else:
            if ((cli_dict['name'] is None) and (cli_dict['d'] == [])) and \
               (cli_dict['noun'] != 'registry'):
                raise Exception('must specify name or -d')
    if ('worker' in cli_dict.keys()) and (cli_dict['worker'] != []):
        raise Exception('do not use --worker, instead create separate workers')
    if 'localscope' not in cli_dict.keys():
        cli_dict['localscope'] = False
    if 'globalscope' not in cli_dict.keys():
        cli_dict['globalscope'] = True
    if cli_dict['name'] is not None:
        if cli_dict['name'] in ['gen', 'lib']:
            raise Exception('name \'' + cli_dict['name'] + '\' is not allowed')
    return cli_dict


# TODO delete
global g_suppress_warn


def main():
    ret = 0
    try:
        signal.signal(signal.SIGINT, ocpidevsignint)
        cli_dict = get_cli_dict()
        if cli_dict['suppresswarn']:
            set_g_suppress_warn(True)
        if cli_dict['loglevel']:
            set_g_log_level(cli_dict['loglevel'])
        Logger().debug('cli_dict : ' + str(cli_dict))
        ProjectDatabase().dispatch_verb(cli_dict)
    except Exception as exception:
        Logger().error(str(exception))
        ret = 1
    return ret


if __name__ == '__main__':
    exit(main())
