#!/usr/bin/env python3.6
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
# You should have received a copy of the GNU Lesser General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.
"""
Module for constructing an argparse parser and parsing user arguments 
from the command line
"""

import argparse
import os
import sys
from pathlib import Path
import _opencpi.util as ocpiutil


class _HelpAction(argparse.Action):
    """
    Argparse Action class that handles the action for the '--help' arg.
    Searches for a man page to display when the '--help' arg is
    encountered. 
    """
    def __init__(self, keys=list(), nargs=0, **kwargs):
        """
        Initializes the _HelpAction object. A 'keys' list of nouns and 
        verbs is kept to be used by the __call__ method for searching 
        for man pages.
        """
        self.keys = keys
        super(_HelpAction, self).__init__(nargs=nargs, **kwargs)
            

    def __call__(self, parser, *args):
        """
        Searches through a 'keys' list of nouns and verbs to find a man 
        page for the key. Will fall back to the parser's help page if
        one is not found.
        """
        cdk_path = ocpiutil.get_cdk_dir()
        man_dir = Path(cdk_path, 'doc', 'man', 'man1')
        prog = Path(parser.prog.split()[0]).stem
        keys = self.keys[:3]
        for key in keys[::-1]:
        # Look for man page for last 3 keys in reverse (subnoun, noun, verb)
            man_name = '{}-{}.1'.format(prog, key)
            man_path = Path(man_dir, man_name)
            if man_path.exists():
                break
        if not self.keys or not man_path.exists():
        # Fall back to default command man page if one does not exist for
        # subnoun, noun, or verb
            man_name = '{}.1'.format(prog)
            man_path = Path(man_dir, man_name)
        if man_path.exists():
        # If a man page exists, call it
            rc = os.system("man {}".format(man_path))
            parser.exit(rc)
        else:
        # Fall back to parser help
            parser.print_help()
            parser.exit()


class _VersionAction(argparse.Action):
    """
    Argparse Action class that handles the action for the '--version'
    arg and exits.
    """
    def __init__(self, nargs=0, **kwargs):
        """Initializes the _VersionAction object"""
        super(_VersionAction, self).__init__(nargs=nargs, **kwargs)

    def __call__(self, parser, *args):
        """
        Calls 'ocpirun' with the '--version' flag and exits
        """
        cmd = 'ocpirun --version'
        rc = os.system(cmd)

        parser.exit(rc)


def parse_args(args_dict, prog=None):
    """
    Takes a dictionary of arguments and an optional program name. 
    Calls _preprocess_args() to preprocess user arguments. 
    Calls _make_parser() to construct a parser and then calls the 
    parser's parse_known_args() method and returns the parsed arguments.

    The dictionary may contain the following keys and values:
    "verbs" : a list or dict of sub-commands which may also contain a 
        "nouns" subdict and/or an "options" subdict. The "nouns" subdict
        may also contain a "nouns" and/or "options" subdict.
    "options" : list or dict containing optional arguments which may 
        also contain a subdict of argparse settings. Used for
        pre-processing user args
    "common options" : same as above but for non-verb/noun specific
        optional arguments
    """
    args = _preprocess_args(args_dict)
    parser = _make_parser(args_dict, prog=prog)
    args,_ = parser.parse_known_args(args)
    args = _postprocess_args(args)

    return args


def _make_parser(args_dict, prog=None):
    """
    Creates the ArgumentParser using the dictionary args_dict. If the
    dictionary contains the key 'verbs', calls _make_subparsers() to 
    make subparsers for each verb. If the key contains 'options', they 
    are collected to pass to the call to make_subparsers.
    """
    # Options common to all opencpi commands
    options_dict = {
        'help': {
            'long': '--help',
            'action': _HelpAction
        },
        'version': {
            'long': '--version',
            'action': _VersionAction
        },
        'log_level': {
            'long': '--log-level'
        },
        'verbose': {
            'long': '--verbose',
            'short': '-v',
            'action': 'store_true'
        }
    }
    if 'common_options' in args_dict:
    # Options common to all subcommands for this particular command
        options_dict.update(args_dict['common_options'])
    parser = argparse.ArgumentParser(add_help=False)
    parser.prog = prog
    parser = _make_options(parser, options_dict)
    if 'verbs' in args_dict:
    # Make subparsers for verbs
        verbs_dict = args_dict['verbs']
        if not verbs_dict or not isinstance(verbs_dict, dict):
        # Empty verbs or not a dict, so return parser
            return parser
        parser = _make_subparsers(parser, verbs_dict, {}, options_dict, 'verb')

    return parser


def _make_subparsers(parser, subparser_dict, parent_options_dict, 
        common_options_dict, dest, parent_keys=list()):
    """
    Creates subparsers for each key,val pair in the dictionary
    subparser_dict. If the dictionary contains the key 'nouns', calls
    itself recursively to make subparsers for each noun. If the
    dictionary contains the key 'options', they are added to a copy
    of the parent_options_dict, to be passed to a call to 
    _make_options() once no more subnouns are left to add.
    """
    subparsers = parser.add_subparsers(dest=dest)
    subparsers.required = subparser_dict.pop('required', True)
    if not subparsers.required:
    # Because the subparser is not required, this may be the end of the
    # parser, so add options
        parser = _make_options(parser, parent_options_dict)
    
    for key,val in subparser_dict.items():
    # Iterate through dict, making subparser for each key,val pair
        keys = list(parent_keys) # copy parent_keys so to not affect original
        keys.append(key)
        common_options_dict['help']['keys'] = keys
        subparser = subparsers.add_parser(key, add_help=False)
        subparser = _make_options(subparser, common_options_dict)
        # Make copy of parent options dict, so to not affect original
        options_dict = dict(parent_options_dict)
        if not val or not isinstance(val, dict):
        # End of parser, so make options and continue
            subparser = _make_options(subparser, parent_options_dict)
            continue
        if 'options' in val and val['options']:
        # Update options dict
            options_dict.update(val['options'])
        if 'nouns' in val and val['nouns'] and isinstance(val['nouns'], dict):
        # Make subparsers for nouns
            nouns_dict = val['nouns']
            child_dest = 'noun' if dest == 'verb' else '{}_noun'.format(key)
            subparser = _make_subparsers(subparser, nouns_dict, options_dict, 
                common_options_dict, child_dest, parent_keys=keys)
        else:
        # End of parser, so make options and continue
            subparser = _make_options(subparser, options_dict)
        
    return parser


def _make_options(parser, options_dict):
    """
    Adds options from the options_dict to the parser. If the option
    belongs to a mutually exclusive group, creates a group from the 
    parser to add the option to.
    """
    mut_exc_groups = {}
    for option,option_dict in options_dict.items():
        if not option_dict or not isinstance(option_dict, dict):
        # Empty options or not a dict, so add argument with name only
            parser.add_argument(option)
            continue
        # Copy dict before popping, so to not affect original
        option_dict = dict(option_dict)
        long_name = option_dict.pop('long', None)
        if long_name and not isinstance(long_name, list):
            long_name = [long_name]
        short_name = option_dict.pop('short', None)
        mut_exc_group = option_dict.pop('mut_exc_group', None)
        if ('action' not in option_dict 
            or option_dict['action'] in ['store', 'append']):
        # Format the metavar
            metavar = option_dict.pop('metavar', None)
            if not metavar:
                metavar = '<{}>'.format(option)
            option_dict['metavar'] = metavar
        if mut_exc_group:
        # Add option to a mutually exclusive group
            if mut_exc_group in mut_exc_groups:
                group = mut_exc_groups[mut_exc_group]
            else:
                group = parser.add_mutually_exclusive_group()
                mut_exc_groups[mut_exc_group] = group
        else:
            group = parser
        if short_name and long_name:
            group.add_argument(short_name, *long_name, **option_dict)
        elif short_name and not long_name:
            group.add_argument(short_name, dest=option, **option_dict)
        elif long_name and not short_name:
            group.add_argument(*long_name, **option_dict)
        else:
            group.add_argument(option, **option_dict)

    return parser


def _preprocess_args(args_dict, args=None):
    """
    Creates and runs a pre-processing parser to collect optional 
    arguments so that they can be moved to the end of arguments to 
    enable the full parser to detect them wherever they appear.
    """
    if not args:
        args = sys.argv[1:]
    if not args:
        args = ['--help']
    parser = argparse.ArgumentParser(
        add_help=False, argument_default=argparse.SUPPRESS)
    options_dict = args_dict['options']
    options_dict.update(args_dict['common_options'])
    parser = _make_options(parser, options_dict)
    args,extra = parser.parse_known_args(args)
    args_dict = vars(args).items()
    args = []
    for arg,val in args_dict:
        arg = arg.replace('_', '-')
        if isinstance(val,bool):
            arg = arg = '--{}'.format(arg)
        else:
            arg = '--{}={}'.format(arg,val)
        args.append(arg)
    
    return extra+args


def _postprocess_args(args):
    """
    Post-processes args after they have been parsed.
    """
    if hasattr(args, "noun"):
    # If the parser works with "nouns", post-process noun attribute by
    # getting noun from its dir type when noun not provided and by q
    # setting noun to <noun>-<subnoun> if subnoun provided
        if not args.noun:
        # Get noun by the dirtype
            args.noun = ocpiutil.get_dirtype(args.directory)
        subnoun_key = '{}_noun'.format(args.noun)
        if hasattr(args, subnoun_key):
        # Get subnoun if one exists
            subnoun = getattr(args, subnoun_key)
            args.noun = '{}-{}'.format(args.noun, subnoun)

    return args