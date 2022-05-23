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

# This file is the CLI to the various operations that can be performed on assets
# It uses the underlying OO API, currently in the assets/ subdir

import sys
import traceback
import os
from pathlib import Path
import _opencpi.assets.factory as ocpifactory
import _opencpi.assets.registry as ocpiregistry
import _opencpi.assets.library as ocpilibrary
import _opencpi.assets.abstract as ocpiabstract
import _opencpi.util as ocpiutil
import ocpiargparse
from ocpidev_args import args_dict
# FIXME:  nuke these 2 lines when we confirm no real usage of getProjMetaData
sys.path.append(os.getenv('OCPI_CDK_DIR') + '/scripts/')
import genProjMetaData

def main():
    """
    Calls ocpiargparser.py to parse command line arguments and calls
    appropriate function or method for the noun/verb combination,
    """
    args = ocpiargparse.parse_args(args_dict, prog='ocpidev')
    assert args.noun # we expect the parser to determine this
    # The CWD is now the directory indicated by the --directory option, if supplied.
    # A missing "noun" has been determined by the arg parser based on this CWD because
    # lots of validation in the arg parser depends on knowing the noun

    try:
        # 1. do stuff that cannot handled by the generic parser
        args = postprocess_args(args)

        # 2. collect all the info about the CWD, after --directory option handling
        # note that the CWD cannot imply an asset that is just a file (like a protocol)
        make_type, asset_type, directory, _, _ = ocpiutil.get_dir_info()
        if args.verbose > 1:
            print(f'Executing in the current directory of type:  {asset_type}')

        # 3. Based on a) where we are (cwd), b) the noun we are targeting, and c) options,
        #    find out these things:
        #    - the targeted asset's parent's path
        #    - the parent's type
        #      (which *might* be a *subdir* of the parent's own dir)
        #    - the actual asset type (noun) of the target (perhaps changed from CLI original)
        #    - the name of the targeted asset (might be changed here)
        #    - whether the parent needs to supply/find assets for a collection
        parent_path, parent_type, args.noun, args.name, parent_collects = \
            get_parent(args, Path(directory), asset_type if asset_type else make_type,
                       ensure_exists=args.verb!='create')
        if args.verbose > 1:
            print(f'The parent asset of this "{args.noun}" asset is a "{parent_type}" asset',
                  file=sys.stderr)
        args.directory = parent_dir = str(parent_path)

        # 3. Get more info about parent and ask it to do a few things:
        if not parent_type.startswith('unknown'):
            parent_class = \
                ocpifactory.AssetFactory.get_class_from_asset_type(parent_type, parent_path.name)
            if parent_collects and parent_path.exists():
                # 3a. If the parent needs to collect the targeted (plural) assets for a collection,
                # ask it to, and stash the list of (usually) asset paths in the args structure
                # as a sort of option for when the collection object is constructed
                args.assets = []
                parent = parent_class(parent_dir, None, verb=args.verb, verbose=args.verbose)
                parent.add_assets(args.noun, **vars(args)) # args.assets will be appended
                args.name = None
            elif args.name:
                # 3b. Let the parent resolve further the identity of the target, in particular figuring
                # out its relative pathname from its parent and putting it in args.child_path
                # This is a static method since the parent might not exist in some cases
                parent_class.resolve_child(parent_path, args.noun, args)

        # 4. Determine the class of the target object that will be operated on
        # and check for the class's existence (i.e. whether it is supported)
        asset_class = ocpifactory.AssetFactory.get_class_from_asset_type(args.noun, args.name)

        # 5. Determine the method (and object) to call to perform the verb
        if args.verb == 'create':
            # Creation uses static methods and not constructors (not yet anyway)
            asset_method = getattr(asset_class, 'create', None)
            if parent_type == 'library':
                # CLI says that libraries may be auto-created when you create something inside them
                maybe_autocreate_library(parent_path, args.verbose)
            elif parent_type == 'libraries':
                # CLI says that a "libraries" directory/asset may be auto-created when you create
                # a library
                maybe_autocreate_libraries(parent_path, args.verbose)
        else:
            asset = ocpifactory.AssetFactory.get_instance(asset_class, **vars(args))
            asset_method = getattr(asset, args.verb, None)      # get the method bound to the object
        if not asset_method:
            raise NotImplementedError
        if args.verbose > 1:
            print(f'Executing command "{args.verb} {args.orig_noun.replace("-"," ")} '+
                  f'in directory: {directory}', file=sys.stderr)
        asset_method(**vars(args))
        # This is horrible and should be nuked in favor of ocpidev show
        if args.verb == "create" or args.verb == "delete" and not args.noun in ["project", "registry"]:
            projdir = ocpiutil.get_path_to_project_top(parent_dir)
            if projdir:
                os.chdir(projdir)
                genProjMetaData.main(projdir)
    except NotImplementedError as e:
        print(f'There is no support for the "{args.verb}" operation on "{args.noun}" assets',
              file=sys.stderr)
        sys.exit(1)
    except ocpiutil.OCPIException as e:
        print(f'Error: {e}',file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        # Verb failed in an unexpected way;
        traceback.print_exc(file=sys.stderr)
        ocpiutil.logging.critical(e) # say something
        sys.exit(1)
    sys.exit(0)


def postprocess_args(args):
    """
    Post-processes user arguments - do what the argparser is unable to do for various reasons
    including some backward compatibility hacks like accepting suffixes in names.
    Also, remove CLI accomodations to common user mistyping before using the API
    """
    if not 'noun' in args or not args.noun:
        ocpiutil.logging.error(f'Unable to determine asset type from directory '+
                               f'"{Path().cwd()}":  provide asset type as "noun" argument')
        sys.exit(1)
    args.orig_noun = args.noun # some methods like to know the noun before it is "improved"
    if args.name == '.':
        args.name = None
    if args.noun == 'spec':
        args.noun = 'component'
        args.file_only = True
        print('Warning:  The "spec" noun is deprecated, use "component" instead.\n'+
              'Warning:  Use the --file-only option to force a single spec file in the "specs"\n'+
              'Warning:  subdirectory.  The newer default behavior is to create a "<name>.comp"\n'+
              'Warning:  subdirectory for the component with a <name>-comp.xml file containing\n'+
              'Warning:  the component specification XML.',
              file=sys.stderr)
    # The CLI currently allows for lots of unclean asset names.
    # Here we scrub this cruft before using the API
    if args.noun == 'component' and args.name:
        if args.name.endswith('.xml'):
            args.name = args.name[:-4]
        if args.name.endswith('-spec') or args.name.endswith('-comp'):
            args.name = args.name[:-5]
    if args.noun == 'protocol' and args.name:
        if args.name.endswith('.xml'):
            args.name = args.name[:-4]
        if args.name.endswith('-prot'):
            args.name = args.name[:-5]
    if args.noun in ['hdl-card', 'hdl-slot'] and args.name:
        if args.name.endswith('.xml'):
            args.name = args.name[:-4]
        if args.name.endswith('-' + args.noun[4:]):
            args.name = args.name[:-5]
    for model in ocpiabstract.Asset.valid_authoring_models:
        if hasattr(args, model + '_noun'):
            args.model = 'model'
    if args.noun == 'worker':
        # exceptional case where special characters are valid in asset names
        name = args.name if args.name else Path.cwd().name
        split = name.split('.')
        if len(split) != 2 or split[0] == '' or split[1] == '':
            ocpiutil.logging.error(f'the name "{name}" for a worker must include the '+
                                   f'authoring model after a period')
            sys.exit(1)
        args.name = split[0]
        args.model = split[1]
        if args.model not in ocpiabstract.Asset.valid_authoring_models:
            ocpiutil.logging.error(f'"{args.model}" is an invalid authoring model.  Valid ones '+
                                   f'are "{ocpiabstract.Asset.valid_authoring_models}"')
            sys.exit(1)
        args.noun = args.model + '-worker'
    elif args.noun == 'hdl-primitive':
        args.noun = 'hdl-' + args.primitive_noun
        delattr(args, 'hdl_noun')
        delattr(args, 'primitive_noun')
        args.model = 'hdl'
    elif args.noun == 'hdl-device':
        if args.name and args.name.endswith('.hdl'):
            args.name = args.name[:-4]
        args.model = 'hdl'
    elif args.noun == 'test':
        if args.name and args.name.endswith('.test'):
            args.name = args.name.split('.')[0]
    if args.noun not in ['registry', 'project'] and args.name and (not args.name.isidentifier() or
                                                                   args.name[0] == '_'):
        ocpiutil.logging.error(f'"{args.name}" is an invalid asset name.')
        sys.exit(1)
    if not getattr(args, 'format',None):
        if getattr(args, 'simple',None):
            args.format = 'simple'
        elif getattr(args, 'json',None):
            args.format = 'json'
        else:
            args.format = 'table'
    # These allow these options to propagated into any "make" execution
    if args.no_doc:
        os.environ["OCPI_NO_DOC"] = "1"
    if args.doc_only:
        os.environ["OCPI_DOC_ONLY"] = "1"
    return args


def maybe_autocreate_library(parent_path, verbose):
    """
    Create a library as a side effect of creating something in a library
    This is a somewhat random CLI "feature": HDL component libraries
    under "hdl" in a project get autocreated when something is created in them
    We do not pass any options into this auto-creation other than verbose
    """
    if parent_path.parent.name == 'hdl' and not parent_path.exists():
        if not parent_path.parent.exists():
            ocpilibrary.LibrariesCollection.create(parent_path.parent.name,
                                                 parent_path.parent.parent, verbose=verbose)
        ocpilibrary.Library.create(parent_path.name, parent_path.parent, verbose=verbose)


def maybe_autocreate_libraries(libraries_path, verbose):
    """
    Create a libraries directory as a side effect of creating a library
    We do not pass any options into this auto-creation other than verbose
    """
    assert libraries_path.name in ['hdl','components']
    if not libraries_path.exists():
        ocpilibrary.LibrariesCollection.create(libraries_path.name, libraries_path.parent,
                                               verbose=verbose)


# All finders take in the cwd path, the previously-determined asset type of the cwd,
# the targeted asset type (noun), and optional targeted name
# Finders then return a tuple of:
# - the parent path of the targeted asset
# - the asset type of this parent path
# - a possible adjusted asset type of the targeted asset
# - a possibly adjusted (or determined) name of the targeted asset
# - a boolean indicating whether it is a plural
# Finders work with "create", where the asset does not exist yet, as well as
# all other verbs which target an existing asset
def find_hdl_slot(args, parent_path, cwd_type, noun, name):
    """ Find where a slot should be:  project-specs, platform devices lib, any specified library"""
    assert cwd_type in ['project','hdl-platforms','library']
    parent_type = cwd_type
    if cwd_type == 'hdl-platforms':
        if not args.platform:
            raise ocpiutil.OCPIException(f'when specifying an HDL device when in the hdl/platforms directory, '+
                                         f'the platform must be specified')
        parent_path = parent_path.joinpath(args.platform, 'devices', 'specs')
        parent_type = 'library'
    elif cwd_type == 'library':
        if not parent_path.parent.name == 'hdl':
            raise ocpiutil.OCPIException(f'HDL devices can only be specified in an HDL library '+
                                         f'under the hdl/ subdirectory of a project')
        parent_path = parent_path.joinpath('specs')
    return parent_path, parent_type, noun, name, False


def find_hdl_device(args, target_path, cwd_type, noun, name):
    """ finder function for HDL devices, cards, and slots """
    assert cwd_type in ['project','hdl-platforms','library']
    if cwd_type == 'library':
        if not target_path.parent.name == 'hdl':
            raise ocpiutil.OCPIException(f'HDL devices can only be specified in an HDL library '+
                                         f'under the hdl/ subdirectory of a project')
    elif cwd_type == 'hdl-platforms':
        if not args.platform:
            raise ocpiutil.OCPIException(f'when specifying an HDL device when in the hdl/platforms directory, '+
                                         f'the platform must be specified')
        target_path = target_path.joinpath(args.platform, 'devices')
    # Must be in a project dir
    elif args.platform:
        target_path = target_path.joinpath('hdl', 'platforms', args.platform, 'devices')
    elif getattr(args, 'hdl_library', None):
        if noun in ['hdl-card', 'hdl-slot']:
            if args.hdl_library != 'cards':
                raise ocpiutil.OCPIException(f'HDL cards and slots can only be at the '+
                                             f'project/specs level or in the hdl/cards library')
        target_path = target_path.joinpath('hdl', args.hdl_library)
    elif getattr(args,'project',None) and noun in ['hdl-card', 'hdl-slot']:
        target_path = target_path.joinpath('specs')
    elif noun == 'hdl-device': # devices default to the devices library
        target_path = target_path.joinpath('hdl','devices')
    elif noun == 'hdl-card': # cards default to the cards library
        target_path = target_path.joinpath('hdl','cards')
    elif noun == 'hdl-slot': # slots default to the cards library
        target_path = target_path.joinpath('hdl','cards')
    else:  # project level without saying where it should go
        raise ocpiutil.OCPIException(f'HDL devices, cards or slots require an indication of '+
                                     f'where in the project they should be, using the --project, '
                                     f'--hdl-library, or --platform options')
    return target_path, "library", noun, name, False


def find_library(args, parent_path, parent_type, noun, name):
    """
    Find the library for library-based assets
    Called assuming some library identifier option is specified
    """
    assert parent_type in ['project', 'libraries']
    library = getattr(args, 'library', None)
    hdl_library = getattr(args, 'hdl_library', None)
    platform = getattr(args, 'platform', None)
    if noun == 'library': # must stay a parent of the library
        assert parent_type == 'project'
        assert not library and not hdl_library and not platform
        if name != 'components':
            parent_path = parent_path.joinpath('components')
            parent_type = 'libraries'
        return parent_path, parent_type, noun, name, False
    # So if noun is not a library, we are looking for things *inside* a library
    if parent_type == 'libraries':
        if not library:
           raise ocpiutil.OCPIException(f'no library was specified in a "libraries" directory')
        parent_path = parent_path.joinpath(library)
    elif library:
        parent_path = parent_path.joinpath('components',
                                           args.library if args.library != 'components' else '')
    elif hdl_library:
        parent_path = parent_path.joinpath('hdl', args.hdl_library)
    elif platform:
        parent_path = parent_path.joinpath('hdl', 'platforms', args.platform, 'devices')
    else:
       parent_path = parent_path.joinpath('components')
       if not parent_path.is_dir() or ocpiutil.get_dirtype(parent_path) != 'library':
           raise ocpiutil.OCPIException(f'no library was specified and a single "components" '+
                                        f'library does not exist')
    if args.ensure_exists and not parent_path.is_dir():
        raise ocpiutil.OCPIException(f'no library exists at "{parent_path}"')
    return parent_path, 'library', noun, name, False


def find_library_or_project(args, target_path, cwd_type, noun, name):
    """
    For navigating to a library or at the project level, when at the project level
    """
    assert cwd_type == 'project'
    if args.project:
        return target_path, "project", noun, name, False
    return find_library(args, target_path, cwd_type, noun, name)


def find_library_or_libraries(args, cwd_path, cwd_type, noun, name):
    """
    For navigating to a library or libraries in a project when you are looking
    for assets that live in libraries
    """
    assert not name
    assert cwd_type in ['project', 'libraries']
    if cwd_type == 'libraries':
        if args.library:
            return find_library(args, cwd_path, cwd_type, noun, name)
    elif cwd_type == 'project':
        if args.library or args.hdl_library or args.platform:
            return find_library(args, cwd_path, cwd_type, noun, name)
    return cwd_path, cwd_type, noun, name, True


def find_registry_or_project(args, cwd_path, cwd_type, noun, name):
    """
    Deal with the nasty special case of the "set" and "unset" verbs which mention the noun
    "registry" while actually operating on the project.
    FIXME:  come up with a clean verb to associate a registry with a project
    or perhaps simply make "set-registry" and "unset-registry" verbs in the CLI
    """
    assert noun == 'registry'
    if args.verb in ['set','unset']:
        if cwd_type != 'project':
            raise ocpiutil.OCPIException(f'The "set registry" command can only be issued in a '+
                                         f'project\'s directory')
        args.verb = args.verb + "_registry" # verbs that operate on projects
        args.registry = name # possibly relative path to project
        return cwd_path, cwd_type, "project", None, False
    # so we are actually operating on a registry in which case the returned
    # parent is the CWD since the documentation says the registry is simply named.
    if name:
        # the registry is named, which means it independent of the project
        registry_path = cwd_path.joinpath(name) # name might be a path (absolute or relative)
    elif args.local_scope:
        registry_path = ocpiregistry.Registry.get_registry_path_from_project(cwd_path)
    else:
        registry_path = ocpiregistry.Registry.get_default_registry_path()
    return registry_path.parent, 'unknown-outside-project', noun, registry_path.name, False


def get_parent(args, cwd, cwd_asset_type, ensure_exists=True):
    """
    Taking as input:
    -- where we are (CWD after -d)
    -- the asset_type or make_type of this initial CWD
    -- the user-specified verb and noun and name (in args)
    Determine the parent asset (its asset type and directory and name) of the
    targeted asset (noun and name), and possibly adjust the target object's
    type and noun and name
    Note that a parent asset MUST be a directory so the returned directory
    is unambiguously the directory of the parent assset.

    Return the tuple of (parent-dir, parent-type, target noun, parent-name, whether-to-collect)

    "Whether-to-collect" means that the parent must be queried for some plural noun, which can
    never happen when the target asset type is the type of the CWD.
    """
    if cwd_asset_type == args.noun:        # shortcut if we are in the right dirtype already
        if args.name: # if a name is supplied make sure it matches the cwd
            # If name is provided, make sure it is consistent with CWD
            # Note post processing of args.name has already stripped any suffixes
            # FIXME:  make this test O-O based on asset type, not here in the CLI
            name = args.name
            if args.noun.endswith('worker'):
                name += '.' + args.model
            elif args.noun == 'component':
                name += '.comp'
            elif args.noun == 'test':
                name += '.test'
            if name != cwd.name:
                raise ocpiutil.OCPIException(f'When in the "{cwd_asset_type}" directory "{cwd}", '+
                                             f'the given name "{args.name}" is wrong.')
        return cwd.parent, 'unknown', args.noun, \
            cwd.name if cwd_asset_type == 'project' else cwd.stem, False
    # Dictionary to map the pair of [CWD asset type, target asset type (noun) ] to
    # information that helps determine the ultimate parent of the targeted asset
    parent_dict = {
        'project': {
            # How to get from a project to the identified noun and maybe name
            # First element is dirs to append.  Some assets cannot be referenced from the project level,
            # e.g. containers. (since we don't have --assembly yet)
            # This map is all asset types and plurals, just for documentation/completeness.
            # Invalid ones have 'None'
            'application':            {'name': True, 'append': 'applications',
                                         'parent': 'applications'},
            'applications':           {'name': False, 'append': 'applications',
                                         'optional': True},
            'component':              {'name': True, 'finder': find_library_or_project},
            'components':             {'name': False, 'plural': True},
            'hdl-assemblies':         {'name': 'assemblies', 'append': 'hdl',
                                         'optional': True},
            'hdl-assembly':           {'name': True, 'append': 'hdl/assemblies',
                                         'parent':'hdl-assemblies'},
            'hdl-card':               {'name': True, 'append': 'hdl/cards',
                                         'parent': 'library'},
            'hdl-cards':              {'name': True, 'append': 'hdl/card/specs',
                                         'optional': True},
            "hdl-container":           None,
            "hdl-containers":          None,
            'hdl-core':               {'name': True, 'append': 'hdl/primitives',
                                         'parent': 'hdl-primitives'},
            'hdl-device':             {'name': True, 'finder': find_hdl_device},
            'hdl-devices':            {'name': True, 'finder': find_hdl_device,
                                         'optional': True},
            'hdl-library':            {'name': True, 'append': 'hdl/primitives',
                                         'parent': 'hdl-primitives'},
            'hdl-platform':           {'name': True, 'append': 'hdl/platforms',
                                         'parent': 'hdl-platforms'},
            'hdl-platforms':          {'name': False, 'plural': True},
            'hdl-primitives':         {'name': False, 'append': 'hdl/primitives', 
                                        'optional': True},
            'hdl-slot':               {'name': True, 'finder': find_hdl_device},
            'hdl-slots':              {'name': False, 'finder': find_hdl_slot},
            'hdl-targets':            {'name': False, 'plural': True},
            'hdl-worker':             {'name': True, 'finder': find_library},
            'libraries':              {'name': False, 'plural': True},
            'library':                {'name': True, 'finder': find_library},
            'ocl-worker':             {'name': True, 'finder': find_library},
            'platforms':              {'name': False, 'plural': True},
            'prerequisite':           {'name': True},
            'prerequisites':          {},
            "project":                 None,
            "projects":               {'name': False, 'registry': True,
                                         'plural': True},
            'protocol':               {'name': True, 'finder': find_library_or_project},
            'protocols':              {'name': True, 'finder': find_library_or_project,
                                         'optional': True},
            "rcc-platform":           {'name': True, 'append': 'rcc/platforms'},
            'rcc-platforms':          {'name': False, 'append': 'rcc/platforms',
                                         'parent': 'hdl-platforms', 'optional': True},
            'rcc-worker':             {'name': True, 'finder': find_library},
            'registry':               {'finder': find_registry_or_project},
            'test':                   {'name': True, 'finder': find_library},
            'tests':                  {'name': False, 'finder': find_library_or_libraries},
            'worker':                 {'name': True, 'finder': find_library},
            'workers':                {'name': False, 'finder': find_library_or_libraries,
                                         'optional': True},
            },
        'applications': {
            'application':            {'name': True},
            'applications':           {'name': 'applications'},
        },
        'hdl-assemblies': {
            'hdl-assemblies':         {'name': 'assemblies', 'append': 'hdl'},
            'hdl-assembly':           {'name': True},
        },
        'hdl-assembly': {
            "hdl-container":          {'name': True }
        },
        'hdl-platform': {
            'component':              {'name': True, 'append': 'devices'},
            'components':             {'name': False, 'append': 'devices', 'optional': True},
            'protocol':               {'name': True, 'append': 'devices'},
            'protocols':              {'name': False, 'append': 'devices', 'optional': True},
            'test':                   {'name': True, 'append': 'devices'},
            'tests':                  {'name': False, 'append': 'devices', 'optional': True},
            'worker':                 {'name': True,  'append': 'devices'},
            'workers':                {'name': False, 'append': 'devices', 'optional': True},
        },
        'hdl-platforms': {
            'hdl-platform':           {'name': True},
        },
        'hdl-primitives': {
            'hdl-primitive-libraries':{'name': False, 'append': 'hdl/primitives'},
            'hdl-library':            {'name': True},
            'hdl-core':               {'name': True},
            'hdl-primitive-cores':    {'name': False, 'append': 'hdl/primitives'},
            'hdl-primitives':         {'name': False, 'append': 'hdl', 'name': 'primitives'},
        },
        'libraries': {
            'component':              {'name': True, 'finder': find_library},
            'components':             {'name': False, 'finder': find_library_or_libraries},
            'hdl-worker':             {'name': True, 'finder': find_library},
            'library':                {'name': True},
            'protocol':               {'name': True, 'finder': find_library},
            'protocols':              {'name': False, 'finder': find_library_or_libraries},
            'rcc-worker':             {'name': True, 'finder': find_library},
            'test':                   {'name': True, 'finder': find_library},
            'tests':                  {'name': False, 'finder': find_library_or_libraries},
            'worker':                 {'name': True, 'finder': find_library},
            'workers':                {'name': False, 'finder': find_library_or_libraries},
        },
        'library': {
            'component':              {'name': True},
            'components':             {'name': False},
            'hdl-worker':             {'name': True},
            'ocl-worker':             {'name': True},
            'protocol':               {'name': True},
            'protocols':              {'name': False},
            'rcc-worker':             {'name': True},
            'test':                   {'name': True},
            'tests':                  {'name': False},
            'worker':                 {'name': True},
            'workers':                {'name': False},
        },
        'prerequisites': {
            'prerequisite':           {'name': True, 'append': 'prerequisites'},
        },
        'rcc-worker': {
            'worker':                 {'noun': 'rcc-worker', 
                                         'name': 'none-or-same'},
        },
        'unknown-outside-project': {
            'components':             {'name': False, 'registry': True,
                                         'plural': True}, # for global scope
            'hdl-platforms':          {'name': False, 'registry': True,
                                         'plural': True}, # for global scope
            'hdl-targets':            {'name': False, 'registry': True,
                                         'plural': True}, # for global scope
            'project':                {'name': True},
            'projects':               {'name': False, 'registry': True,
                                         'plural': True},
            'rcc-platforms':          {'name': False, 'registry': True,
                                         'plural': True}, # for global scope
            'rcc-targets':            {'name': False, 'registry': True,
                                         'plural': True}, # for global scope
            'registry':               {},
            'platforms':              {'name': False, 'registry': True,
                                         'plural': True},
            'prerequisites':          {},
            'targets':                {'name': False, 'registry': True,
                                         'plural': True},
            'workers':                {'name': False, 'registry': True,
                                         'plural': True},
        },
        'unknown-in-project': {
            "registry":               {'name': True},
        }
     }

    if not cwd_asset_type:
        cwd_asset_type = \
            'unknown-in-project' if ocpiutil.get_path_to_project_top(str(cwd)) else \
            'unknown-outside-project'
    noun = args.noun
    name = args.name
    parent_path = cwd
    parent_type = cwd_asset_type
    pmap = parent_dict.get(cwd_asset_type)
    assert pmap
    pmap = pmap.get(noun)
    if pmap == None:
        raise ocpiutil.OCPIException(f'When in a "{cwd_asset_type}" directory, operating on '+
                                     f'{"" if noun.endswith("s") else "a "}'+
                                     f'{noun} is invalid')
    map_name = pmap.get('name')
    if map_name == False:
        if name:
            raise ocpiutil.OCPIException(f'When in a "{cwd_asset_type}" type directory, '+
                                         f'providing the name "{name}" is invalid')
    elif map_name == True:
        if not name:
            raise ocpiutil.OCPIException(f'When in a "{cwd_asset_type}" type directory, '+
                                         f'the "{noun}" must be named')
    elif map_name == 'none-or-same':
        if name and name != Path(args.directory).name:
            raise ocpiutil.OCPIException(f'When in a "{cwd_asset_type}" type directory, '+
                                         f'the "{noun}" must be same name or not mentioned')
        name = None
    elif map_name != None:
        name = map_name
    map_noun = pmap.get('noun')
    if map_noun: # map is forcing the noun
        noun = map_noun
    append = pmap.get('append')
    if append: # map is appending to CWD to get parent dir
        parent_path = parent_path.joinpath(append)
    if pmap.get('parent'):
        parent_type = pmap.get('parent')
    if pmap.get('registry'):
        parent_path = Path(ocpiregistry.Registry.get_default_registry_dir())
        parent_type = 'registry'
    collect = pmap.get('plural')
    finder = pmap.get('finder')
    if finder:
        args.ensure_exists = ensure_exists
        parent_path, parent_type, noun, name, collect = \
            finder(args, parent_path, parent_type, noun, name)
    if ensure_exists and not pmap.get('optional'):
        if  not parent_path.exists():
            raise ocpiutil.OCPIException(f'The directory "{parent_path}" does not exist where a '+
                                         f'"{noun}" directory with name "{name}" is expected.')
        if name and not parent_path.joinpath(name).exists():
            ocpiutil.OCPIException(f'The "{noun}" named "{name}" in directory "{parent_path}" '+
                                   f'does not exist')

    return parent_path, parent_type, noun, name, collect


if __name__ == '__main__':
    main()
