#!/usr/bin/env python3
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

from copy import copy
from inspect import signature
from pathlib import Path
from subprocess import call
import sys
import _opencpi.assets as ocpiassets
import _opencpi.util as ocpiutil
import ocpiargparse
from ocpidev_args import args_dict
from _opencpi.assets import application
import ocpidev_utilization
import ocpishow 
import ocpidev_run

def main():
    """
    Calls ocpiargparser.py to parse command line arguments and calls
    appropriate function or method for the noun/verb combination,
    falling back to ocpidev.sh when necessary.
    TODO: There are a lot of try/except statements to fall back to 
    ocpidev.sh when needed. As more code gets updated to python, these
    try/excepts can and should be removed.
    """
    cdk_dir = ocpiutil.get_cdk_dir() # Check cdk path exists and is valid
    args = ocpiargparse.parse_args(args_dict, prog='ocpidev')
    # This is not strictly correct if verb happens to be the value an option that precedes positional verb.
    sys.argv.remove(args.verb)
    sys.argv[0] = args.verb;
    # If verb is handled by another python script or function, hand off to it.
    # TODO: change argparsers in these scripts to use ocpiargs.py
    if args.verb == 'show':
        rc = ocpishow.main()
        sys.exit(rc)
    elif args.verb == 'utilization':
        rc = ocpidev_utilization.main()
        sys.exit(rc)
    elif args.verb == 'run':
        rc = ocpidev_run.main()
    
    args = postprocess_args(args)
    orig_dir = Path.cwd()
    change_dir(args.directory)
    delattr(args, 'directory')

    if args.verb == 'create':
        ocpicreate(args, cdk_dir, orig_dir)
    elif args.verb in ['set', 'unset']:
        ocpi_set_unset(args)
    try:
        directory,name = get_working_dir(args)
    except:
    # Could not get working directory. Likely un-implemented noun.
    # Fall back ocpidev.sh
        ocpidev_sh(cdk_dir=cdk_dir, orig_dir=orig_dir)
    if args.noun in ['project', 'library', 'registry']:
    # Libraries, projects, and registries want the full path as the directory
        directory = str(Path(directory,name))

    try:
    # Try to instantiate the appropriate asset from noun
        asset_factory = ocpiassets.factory.AssetFactory()
        asset = asset_factory.factory(args.noun, directory, name)
    except ocpiutil.OCPIException as e:
    # Noun not implemented; fall back to ocpidev.sh
        ocpidev_sh(cdk_dir, orig_dir)
    try:
    # Try to get appropriate method from verb
        asset_method = getattr(asset, args.verb) 
    except AttributeError as e:
    # Verb not implemented; fall back to ocpidev.sh
        ocpidev_sh(cdk_dir, orig_dir)
    try:
    # Get verb method parameters, collect them from args, and try to
    # call verb method with collected args
        sig = signature(asset_method)
        method_args = {}
        for param in sig.parameters:
            method_args[param] = getattr(args, param, '')
        if getattr(args, 'verbose', False):
            msg = 'Executing the "{} {}" command in directory: {}'.format(
                args.verb, args.noun, asset.directory)
            print(msg)
        asset_method(**method_args)
    except ocpiutil.OCPIException as e:
        ocpiutil.logging.error(e)
        sys.exit(1)
    except Exception as e:
    # Verb not implemented fully/at all; fall back to ocpidev.sh
        ocpidev_sh(cdk_dir, orig_dir)


def postprocess_args(args):
    """
    Post-processes user arguments
    """
    noun = getattr(args, 'noun', '')
    if noun == 'spec':
        args.noun = 'component'
    elif noun == 'hdl-slot':
        args.noun = 'hdl-card'
    if hasattr(args, 'rcc-noun'):
        args.model = 'rcc'
    elif args.noun == 'worker':
        args.model = Path(args.name).suffix
        if not args.model:
            err_msg = ' '.join([
                'Unsupported authoring model "{}"'.format(args.model), 
                'for worker located at "{}"'.format(args.directory)
            ])
            raise ocpiutil.OCPIException(err_msg)
    else:
        args.model = 'hdl'
    return args


def ocpi_set_unset(args):
    """
    set and unset the registry of the project
    """
    name = getattr(args, 'name', '')
    name = name if name else ''
    directory = str(Path.cwd())

    try:
        asset_factory = ocpiassets.factory.AssetFactory()
        project = asset_factory.factory('project', directory, name)
        if args.verb == 'unset':
            project.unset_registry()
            sys.exit()
        if args.registry_directory:
            registry_directory = args.registry_directory
        else:
            registry_directory = ocpiassets.registry.Registry.get_default_registry_dir()
        project.set_registry(registry_directory)
    except ocpiutil.OCPIException as e:
        ocpiutil.logging.error(e)
        sys.exit(1)
    sys.exit()


def ocpicreate(args, cdk_dir=None, orig_dir=None):
    """
    Gets proper class from noun and calls its create() static method
    """
    class_dict = {
        "project": ocpiassets.project.Project,
        "library": ocpiassets.library.Library,
        "application": ocpiassets.application.Application,
    }
    if args.noun not in class_dict:
    # Noun not implemented by this function; fall back to ocpidev.sh
        ocpidev_sh(cdk_dir, orig_dir)
    directory,name = get_working_dir(args, ensure_exists=False)
    delattr(args, 'name')
    args = vars(args)
    noun = args.pop('noun', '')
    try:
        class_dict[noun].create(name, directory, **args)
    except ocpiutil.OCPIException as e:
        ocpiutil.logging.error(e)
        sys.exit(1)
    sys.exit()


def get_working_dir(args, ensure_exists=True):
    """
    Calls ocpiutil.get_ocpidev_working_dir() to get the appropriate
    directory for an asset. Splits the directory into name and parent 
    directory tuple and returns them.
    """
    kwargs = copy(vars(args))
    name = kwargs.pop('name', '')
    name = name if name else ''
    noun = kwargs.pop('noun', '')
    
    if noun == 'registry' or (noun == 'project' and args.verb == 'create'):
        working_path = Path(Path.cwd(), name)
    else:
        working_path = Path(ocpiutil.get_ocpidev_working_dir(
            noun, name, ensure_exists=ensure_exists, **kwargs))
    name = str(working_path.name)
    working_dir = str(working_path.parent)
    
    return working_dir,name


def change_dir(directory):
    """
    Calls ocpiutil.change_dir to change to specified directory.
    Catches and logs any OCPIException that is raised and exits.
    """
    try:
        ocpiutil.change_dir(directory)
    except ocpiutil.OCPIException as e:
        ocpiutil.logging.error(e)
        sys.exit(1)


def ocpidev_sh(cdk_dir=None, orig_dir=None):
    """Calls ocpidev.sh and exits"""
    if not cdk_dir:
        cdk_dir = ocpiutil.get_cdk_dir()
    if orig_dir:
        ocpiutil.change_dir(orig_dir)
    ocpidev_sh_path = str(Path(cdk_dir, 'scripts', 'ocpidev.sh'))
    cmd = sys.argv
    cmd.insert(0, ocpidev_sh_path)
    rc = call(cmd)
    sys.exit(rc)


if __name__ == '__main__':
    main()
