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

from inspect import signature
from pathlib import Path
from subprocess import call
import sys
import _opencpi.assets as ocpiassets
import _opencpi.util as ocpiutil
import ocpiargparse
from ocpidev_args import args_dict
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
    cdk_dir = ocpiutil.get_cdk_path() # Check cdk path exists and is valid
    args = ocpiargparse.parse_args(args_dict, prog='ocpidev')
    args = postprocess_args(args)
    orig_dir = Path.cwd()
    change_dir(args)
    sys.argv = sys.argv[1:]
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
        sys.exit(rc)
    elif args.verb == 'create':
        ocpicreate(args)

    try:
    # Try to instantiate the appropriate asset from noun
        name = getattr(args, 'name', '')
        name = name if name else ''
        dir=args.directory
        # This is temporary until the more comprehensive solution based on get_subdir is done
        if ocpiutil.get_dirtype(dir) == "project":
            if args.noun == "worker":
                dir += "/components"
                if args.library and args.library != "components":
                    dir += "/" + args.library
            elif args.noun == "hdl-primitives":
                dir += "/hdl/primitives"
        directory = str(Path(dir, name))
        # End of temporary fix until get_subdir is ported here
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
            method_args[param] = getattr(args, param)
        if args.verbose:
            msg = 'Executing the "{} {}" command in "{}" directory: {}'.format(
                args.verb, args.noun, args.noun, asset.directory)
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
    TODO: docstring
    """
    args.libbase = 'hdl' if hasattr(args, 'hdl-noun') else None
    if not hasattr(args, 'library') or args.library == None:
    # If library option not provided
        if args.noun in ['card', 'slot', 'hdl-card', 'hdl-slot']:
            args.library = str(Path('hdl', 'cards'))
        elif hasattr(args, 'hdl_library') and args.hdl_library is not None:
            args.library = str(Path('hdl', args.hdl_library))
    print(args)
    return args


def get_subdir(args):
    """
    TODO: docstring
    """
    libassets = ['worker', 'device', 'spec', 'component', 'protocol', 
                 'properties', 'signals', 'test', 'card', 'slot']
    if not args.noun in libassets:
        if not hasattr(args, 'hdl_noun') or not args.hdl_noun in libassets:
            return None

    subdir_path = None
    dir_path = Path.cwd()
    dirtype = ocpiutil.get_dirtype(dir_path)
    print(dirtype)
    do_autocreate = False
    standalone = True
    if not hasattr(args, 'standalone') or args.standalone == False:
        standalone = False
    if not standalone:
    # Not standalone
        if dirtype == 'project':
        # Current directory is of type project
            hdl_path = Path(dir_path, 'hdl')
            if hasattr(args, 'library') and args.library is not None:
            # library argument was used
                library_path = Path(args.library)
                if args.libbase == 'hdl' and not hdl_path.exists():
                    hdl_path.mkdir()
                if library_path.name in ['cards', 'devices', 'adapters']:
                    subdir_path = Path(dir_path, library_path)
                    do_autocreate = True
                elif args.library == 'components':
                    subdir_path = Path(dir_path, library_path)
                elif library_path.parent == 'hdl':
                    subdir_path = Path(dir_path, library_path)
                else:
                    subdir_path = Path(dir_path, 'components', 'library')
            elif hasattr(args, 'platform') and args.platform is not None:
            # platform argument was used
                model = 'hdl' if hasattr(args, 'hdl_noun') else 'rcc'
                platform_path = Path(dir_path, model, args.platform)
                if not platform_path.exists():
                    err_msg = 'the platform {} does not exist in {}'.format(
                        args.platform, str(platform_path))
                    raise ocpiutil.OCPIException(err_msg)
          
    if not subdir_path.exists() and args.verb == 'create' and do_autocreate:
        ocpiassets.library.Library.make_library(subdir_path, subdir_path)
    if not subdir_path.exists():
        err_msg = 'the library for "{}" does not exist'.format(
            str(subdir_path))
        raise ocpiutil.OCPIException(err_msg)
    dirtype = ocpiutil.get_dirtype(str(subdir_path))
    do_project = True if hasattr(args, 'project') and args.project else False
    if not standalone and dirtype != 'library' and not do_project:
        err_msg = ' '.join(['the directory for "{}"'.format(str(subdir_path)),
                            'is not a library - it is of type',
                            '"{}"'.format(dirtype)])
        raise ocpiutil.OCPIException(err_msg)

    return subdir_path
    

def change_dir(args):
    """
    TODO: doctstring
    """
    try:
        ocpiutil.change_dir(args.directory)
        subdir = get_subdir(args)
        if subdir:
            ocpiutil.change_dir(subdir)
    except ocpiutil.OCPIException as e:
        ocpiutil.logging.error(e)
        sys.exit(1)


def ocpicreate(args):
    """
    Gets proper class from noun and calls its create() static method
    """
    class_dict = {
        "project": ocpiassets.project.Project,
        "library": ocpiassets.library.Library,
    }
    if args.noun not in class_dict:
    # Noun not implemented by this function; fall back to ocpidev.sh
        ocpidev_sh()
    args = vars(args)
    name = args.pop('name', None)
    directory = args.pop('directory', None)
    try:
        class_dict[args["noun"]].create(name, directory, **args)
    except ocpiutil.OCPIException as e:
        ocpiutil.logging.error(e)
        sys.exit(1)
    sys.exit()


def ocpidev_sh(cdk_dir, orig_dir=None):
    """Calls ocpidev.sh and exits"""
    if orig_dir:
        change_dir(orig_dir)
    ocpidev_sh_path = str(Path(cdk_dir, 'scripts', 'ocpidev.sh'))
    cmd = sys.argv
    cmd.insert(0, ocpidev_sh_path)
    rc = call(cmd)
    sys.exit(rc)


if __name__ == '__main__':
    main()
