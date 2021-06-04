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
import os
from pathlib import Path
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
    ocpiutil.get_cdk_path() # Check cdk path exists and is valid
    args = ocpiargparse.parse_args(args_dict, prog='ocpidev')
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
        directory = str(Path(args.directory, name))
        asset_factory = ocpiassets.factory.AssetFactory()
        asset = asset_factory.factory(args.noun, directory, name)
    except ocpiutil.OCPIException as e:
    # Noun not implemented; fall back to ocpidev.sh
        print(e)
        # ocpidev_sh()
    try:
    # Try to get appropriate method from verb
        asset_method = getattr(asset, args.verb) 
    except AttributeError as e:
    # Verb not implemented; fall back to ocpidev.sh
        print(e)
        # ocpidev_sh()
    try:
    # Get verb method parameters, collect them from args, and try to
    # call verb method with collected args
        sig = signature(asset_method)
        method_args = {}
        for param in sig.parameters:
            method_args[param] = getattr(args, param)
        asset_method(**method_args)
    except ocpiutil.OCPIException as e:
        ocpiutil.logging.error(e)
    except Exception as e:
    # Verb not implemented fully/at all; fall back to ocpidev.sh
        print(e)
        # ocpidev_sh()


def ocpicreate(args):
    """
    Gets proper class from noun and calls its create() static method
    """
    class_dict = {
        "project": ocpiassets.project.Project,
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


def ocpidev_sh():
    """Calls ocpidev.sh and exits"""
    cdk_dir = ocpiutil.get_cdk_path()
    ocpidev_sh_path = Path(cdk_dir, 'scripts', 'ocpidev.sh')
    args = ' '.join(sys.argv)
    cmd = '{} {}'.format(ocpidev_sh_path, args)
    rc = os.system(cmd)
    sys.exit(rc)


if __name__ == '__main__':
    main()