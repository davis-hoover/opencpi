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
Abstract classes that are used in other places within the assets module are defined in this file
"""

from abc import ABCMeta, abstractmethod
import os
import sys
import logging
import re
import types
import jinja2
from pathlib import Path
import copy
import shutil
import _opencpi.hdltargets as hdltargets
import _opencpi.util as ocpiutil
import ocpidoc.ocpi_documentation as ocpi_doc

class Asset(metaclass=ABCMeta):
    """
    Parent Class for all Asset objects.  Contains a factory to create each of the asset types.
    Not officially a virtual class but objects of this class are not intended to be directly
    created.
    """
    valid_authoring_models = ['rcc', 'hdl', 'ocl']
    valid_settings = []
    instances_should_be_cached = False

    def __init__(self, directory, name=None, **kwargs):
        """
        initializes Asset member data valid kwargs handled at this level are:
            verbose (T/F) - be verbose with output
            name - Optional argument that specifies the name of the asset if not set defaults to the
                   basename of the directory argument
            directory - The location on the file system of the asset that is being constructed.
                        both relative and global file paths are valid.
        """
        directory = str(directory)
        child_path = kwargs.get('child_path')
        self.parent = Path(directory).resolve() # This is the parent
        self.verbose = kwargs.get('verbose')
        self.name = name
        if not name:
            # If name not specified, caller is implicitly saying that the
            # asset is of a type where the basename is indeed the asset name
            # FIXME: make this illegal for the API
            self.name = self.parent.name
            self.parent = self.parent.parent
        elif not child_path:
            # The API has been called without a separate resolve_child being done
            # so we do it now.  This also assumes that the directory argument is indeed
            # the parent of the asset
            # FIXME:  the parent should be an object in all cases...
            # FIXME:  this is in fact where resolve_child should *always* be done
            parent_type = ocpiutil.get_dirtype(self.parent)
            if parent_type:
                # FIXME: This is a layering violation that can be fixed by merging
                # the factory stuff here in this "base class" file.
                from  _opencpi.assets.factory import AssetFactory
                parent_class = AssetFactory.get_class_from_asset_type(parent_type,
                                                                      self.parent.name)
                args = types.SimpleNamespace(**kwargs)
                args.name = name
                parent_class.resolve_child(self.parent, self.asset_type, args)
                child_path = args.child_path
            else:
                # No asset type means we are not in projects
                child_path = name
        # Derived classes are expected to set this, but intermediate classes
        # might test for it being set or not to detect whether the intermediate
        # class is actually the instantiated one
        if not getattr(self, 'asset_type', None):
            self.asset_type = None
        if not getattr(self, 'make_type', None):
            self.make_type = None
        # Location is the file *or* directory that represents the asset
        self.path = self.parent.joinpath(str(child_path) if child_path else self.name)
        self.directory = str(self.path) # for old code
        if not kwargs.get('non_existent_ok') and not self.path.exists():
            raise ocpiutil.OCPIException(f'Requested {self.asset_type} at "{self.path}" does not '+
                                         f'exist')
        if not getattr(self,'out_of_project',None):
            if not ocpiutil.is_path_in_project(self.path):
                raise ocpiutil.OCPIException(f'Requested asset directory "{directory}" is not in '+
                                             f'a project')

    @classmethod
    def resolve_child(cls, path, child_asset_type, args):
        """ Resolve the actual path for a child asset if needed """
        args.child_path = args.name

    @staticmethod
    def get_asset_path(directory, name, args):
        """
        Determine actual asset path and return the triple: path, name, parent
        This is common code for both creation and construction.
        """
        parent_path = Path(directory).resolve()
        if not name:
           name = parent_path.name
           parent_path = parent_path.parent
        child_path = args.get('child_path')
        return parent_path.joinpath(child_path if child_path else name), name, parent_path

    @staticmethod
    def process_template(template):
        """ Convert our indented templates into a jinja template """
        template = template.lstrip('\n')
        spaces = re.match(" *", template)
        if spaces:
            spaces = spaces.group(0)
            new_template=''
            for line in template.split('\n'):
                if re.match(spaces, line):
                    line = line[len(spaces):]
                new_template+=line+'\n'
            template = new_template
        return jinja2.Template(template, trim_blocks=True,lstrip_blocks=True)

    @staticmethod
    def start_creation(directory, name, asset_type, args):
        """
        For asset creation, do the basic figuring of the actual asset path and
        existence check
        Return the triple:  asset_path, asset_name, parent_path
        """
        path, name, parent = Asset.get_asset_path(directory, name, args)
        if path.exists():
            raise ocpiutil.OCPIException(f'{asset_type} "{name}" already exists at "{str(path)}"')
        return path, name, parent

    @classmethod
    def get_valid_settings(cls):
        """
        Recursive class method that gathers all the valid settings static lists of the current
        class's base classes and combines them into a single set to return to the caller
        """
        ret_val = cls.valid_settings

        for base_class in cls.__bases__:
            # prevents you from continuing up the class hierarchy to "object"
            if callable(getattr(base_class, "get_valid_settings", None)):
                # pylint:disable=no-member
                ret_val += base_class.get_valid_settings()
                # pylint:enable=no-member

        return set(ret_val)

    def get_settings(self):
        """
        Generic method that returns a dictionary of settings associated with a single run or build
        of an object.  valid settings are set at the subclass level and any member variable that
        is not in this list or is not set(equal to None) are removed from the dictionary
        """
        settings_list = copy.deepcopy(vars(self))
        # list constructor is required here because the original arg_list is being
        # changed and we can't change a variable we are iterating over
        for setting, value in list(settings_list.items()):
            if (value in [None, False]) or (setting not in self.get_valid_settings()):
                del settings_list[setting]

        return settings_list

    @staticmethod
    def check_dirtype(dirtype, directory):
        """
        Validate the directory and dirtype, otherwise raise an exception
        """
        if not os.path.isdir(directory):
            err_msg = 'location does not exist at: "{}" when looking for {}'.format(directory, dirtype)
            raise ocpiutil.OCPIException(err_msg)

        make_type,asset_type,_,_,_ = ocpiutil.get_dir_info(directory)
        # Asset_type is more specific than make_type
        true_dirtype = asset_type if asset_type else make_type
        if not true_dirtype:
            true_dirtype = 'unknown'
        if true_dirtype != dirtype:
            err_msg = ' '.join(["Expected directory of type '{}'".format(dirtype), 
                                "but found type '{}'".format(true_dirtype), 
                                "for directory {}".format(directory)])
            raise ocpiutil.OCPIException(err_msg)

    def delete(self, force=False, verbose=None, **kwargs):
        """
        Remove the asset from the file system.  Any additional cleanup on a per asset basis can be done in
        the derived class method after calling this base class method

        Return True if deletion actually took place
        """
        message = f'the {self.asset_type.replace("-", " ")} named "{self.name}" at {self.path}'
        if force or ocpiutil.get_ok(prompt=f'Delete {message}', default=None):
            try:
                if self.path.is_dir():
                    shutil.rmtree(self.path)
                else: # a file based asset in specs, maybe with rst, maybe with lib/symlink
                    self.path.unlink()
                    rst_path = self.path.with_suffix('.rst')
                    if rst_path.exists(): rst_path.unlink() # use missing_ok=True in python 3.8
                    lib_path = self.path.parent.parent.joinpath("lib", self.path.name)
                    if lib_path.is_symlink(): lib_path.unlink() # use missing_ok=True in python 3.8
                if verbose or not force:
                    print(f'Successfully deleted {message}')
                return True
            except Exception as e:
                logging.error(f'Failed to delete {message}')
        return False

    @classmethod
    def get_component_spec_file(cls, file):
        """
        Determines if a provided xml file contains a component spec and returns the component name
        FIXME: this should not be here, but is called from here...
        """
        file=Path(file).name
        return file[:-9] \
            if file.endswith("_spec.xml") or file.endswith("-spec.xml") else None

    def get_valid_components(self):
        """
        this is function is used by both projects and libraries  to find the component specs that
        are owned by that asset.
        TODO move this function to a separate class from asset and have project and library inherit
             from that class???
        """
        ret_val = []
        if os.path.isdir(self.directory + "/specs"):
            files = [dir for dir in os.listdir(self.directory + "/specs")
                     if os.path.isfile(os.path.join(self.directory + "/specs", dir))]
            for comp in files:
                if __class__.get_component_spec_file(self.directory + "/specs/" + comp):
                    ret_val.append(self.directory + "/specs/" + comp)
        # in libraries, spec files can be in .comp directories
        if ocpiutil.get_dirtype(self.directory) == "library":
            for entry in Path(self.directory).iterdir():
                if entry.suffix == ".comp" and entry.is_dir():
                    spec_file = entry.joinpath(entry.stem + "-spec.xml")
                    if spec_file.exists():
                        ret_val.append(entry)
        return ret_val

    @staticmethod
    def create_file_asset(asset_type, suffix, directory, name, ocpitemplate, get_template_dict,
                          project_package_id, args, dir_suffix=None):
        """
        Common static method for creating file-based assets in "specs" directories.
        With support for a mode that has a unique directory, i.e. components with *.comp
        I.e. dir_suffix says: this dir_suffix will be created for this file asset
        """
        dir_path = Path(directory)
        file_only = not dir_suffix or args.get('file_only')

        if file_only:
            dir_path = dir_path.joinpath('specs')
        else:
            assert dir_suffix
            dir_path = dir_path.joinpath(name + dir_suffix)
        if suffix and name.endswith('-' + suffix): # backward
            file_name = name
        elif '-' in name or '.' in name:
            raise ocpiutil.OCPIException(f'invalid name for {asset_type} creation '+
                                         f'contains periods or bad suffix after hyphen: "{name}"')
        elif suffix:
            file_name = name + '-' + suffix
        else:
            file_name = name
        file_path = dir_path.joinpath(file_name + '.xml') # name is actual xml file here
        if file_only: # we rely on this being set to imply file_only
            if file_path.exists():
                raise ocpiutil.OCPIException(f'file for {asset_type} creation already exists: '+
                                             f'"{file_path}".')
            if dir_suffix:
                suffixed_path = Path(directory).joinpath(name + dir_suffix)
                if suffixed_path.exists():
                    raise ocpiutil.OCPIException(f'{asset_type} directory "{suffixed_path}" exists '+
                                                 f' when trying to create: "{file_path}" ')
        elif dir_suffix:
            if not dir_path.name.endswith(dir_suffix):
                raise ocpiutil.OCPIException(f'internal: unexpected directory for {asset_type} '
                                             f'creation not ending in "{dir_suffix}":  "{directory}".')
            elif dir_path.exists():
                raise ocpiutil.OCPIException(f'directory for {asset_type} creation: "{directory}" '+
                                             f'already exists.')
            specs_path = dir_path.parent.joinpath('specs', file_path.name)
            if specs_path.exists():
                raise ocpiutil.OCPIException(f'file for {asset_type} creation: "{specs_path}" '+
                                             f'already exists.')
        else:
            raise ocpiutil.OCPIException(f'internal: unexpected non-specs directory for {asset_type} '
                                             f'creation:  "{directory}".')
        # done error checking, create required directories
        dir_path.mkdir(parents=True, exist_ok=True) # specs dir or *dir_suffix dir
        # write XML file from template
        template = jinja2.Template(ocpitemplate, trim_blocks=True)
        template_dict = get_template_dict(name, directory, **args)
        ocpiutil.write_file_from_string(str(file_path), template.render(**template_dict))
        if project_package_id: # project level specs dir must have a package-id file for the project
            package_id_path = dir_path.joinpath('package-id')
            if not package_id_path.exists():
                package_id_path.write_text(project_package_id + '\n')
        else: # ensure the asset is visible in the lib subdir
            lib_path = Path(dir_path.parent).joinpath("lib")
            lib_path.mkdir(exist_ok = True)
            lib_path.joinpath(file_path.name).\
                symlink_to("../" + dir_path.name + "/" + file_path.name)
        Asset.finish_creation(asset_type, name, file_path if file_only else dir_path,
                              args.get('verbose'))

    @staticmethod
    def finish_creation(asset_type, name, path, verbose):
        """
        Do the common tasks at the end of creating an asset.
        This is a static method because the create static method for the different
        asset classes does not in fact create an object, but just creates
        files and directories in the file system.
        The 'path' argument is the asset, which is a file or a directory
        """
        if os.environ.get('OCPI_NO_DOC') != '1':
            if path.is_dir():
                # FIXME:  all asset types should have an attribute which is their
                # xml file name.
                # For file-based assets, that attribute is the same as path
                if asset_type == 'project':
                    file_name = 'Project'
                else:
                    file_name = path.name.replace('.', '-')
            else:
                file_name = path.name
                if file_name.endswith('.xml'):
                    file_name = file_name[:-4]
            ocpi_doc.create(str(path if path.is_dir() else path.parent), # where to put it
                            asset_type=asset_type, name=name, file_name=file_name,
                            file_only=not path.is_dir(), verbose=verbose)
        if verbose:
            print(f'The {asset_type} "{name}" was created as the '+
                  f'{"directory" if path.is_dir() else "file"} {path}".', file=sys.stderr)

class BuildableAsset(Asset):
    """
    Virtual class that requires that any child classes implement a build method.  Contains settings
    that are specific to all assets that can be run
    """
    valid_settings = ["only_plats", "ex_plats"]
    def __init__(self, directory, name=None, **kwargs):
        """
        Initializes BuildableAsset member data  and calls the super class __init__
        valid kwargs handled at this level are:
            ex_plats (list) - list of platforms(strings) to exclude from a build
            only_plats (list) - list of the only platforms(strings) to build for
        """
        super().__init__(directory, name, **kwargs)
        self.ex_plats = kwargs.get("ex_plats", None)
        self.only_plats = kwargs.get("only_plats", None)

    def build(self, verbose=None, **kwargs):
        """
        This method will build the asset, and is the base class default implentation
        """
        project_path = ocpiutil.is_path_in_project(self.path)
        assert project_path
        if not project_path.joinpath('imports').is_dir():
            ocpiutil.execute_cmd({},
                                 project_path,
                                 action=['imports'],
                                 file=os.environ['OCPI_CDK_DIR']+"/include/project.mk",
                                 verbose=verbose)
        action=[]
        if kwargs.get('rcc'):
            action.append('rcc')
        if kwargs.get('hdl'):
            action.append('hdl')
        if kwargs.get('workers_as_needed'):
            os.environ['OCPI_AUTO_BUILD_WORKERS'] = '1'
        if kwargs.get('generate'):
            action.append('generate')
        if kwargs.get('no_assemblies'):
            action.append('Assemblies=')
        dynamic = kwargs.get('dynamic')
        optimize = kwargs.get('optimize')
        hdl_platform = kwargs.get('hdl_platform')
        hdl_rcc_platform = kwargs.get('hdl_rcc_platform')
        hdl_target = kwargs.get('hdl_target')
        rcc_platform = kwargs.get('rcc_platform')
        worker = kwargs.get('worker')
        export = kwargs.get('export')

        build_suffix = '-'
        if dynamic:
            build_suffix += 'd'
        if optimize:
            build_suffix += 'o'
        if optimize or dynamic:
            if rcc_platform:
                if any("-" in s for s in rcc_platform):
                    raise ocpiutil.OCPIException("You cannot use the --optimize build option and "
                    + "also specify build options in a platform name (in this case: ",
                    rcc_platform, ")")
                else:
                    new_list = [s + build_suffix for s in rcc_platform]
                    rcc_platform = new_list
            else:
                rcc_platform = [os.environ['OCPI_TOOL_PLATFORM'] + build_suffix]
        #Pass settings
        settings = {}
        if hdl_platform:
            settings['hdl_plat_strs'] = hdl_platform
        if hdl_target:
            settings['hdl_target'] = hdl_target
        if rcc_platform:
            settings['rcc_platform'] = rcc_platform
        if hdl_rcc_platform:
            settings['hdl_rcc_platform'] = hdl_rcc_platform
        if worker:
            settings['worker'] = worker
        make_file = ocpiutil.get_makefile(self.directory, self.make_type)[0]
        #Build
        if kwargs.get('orig_noun') == 'tests':
            action.append('test')
        ocpiutil.file.execute_cmd(settings, self.directory, action=action,
                                  file=make_file, verbose=kwargs.get('verbose'))
        if export:
            location=ocpiutil.get_path_to_project_top()
            make_file=ocpiutil.get_makefile(location, "project")[0]
            ocpiutil.execute_cmd({},
                             location,
                             action=['exports'],
                             file=make_file,
                             verbose=verbose)

    def clean(self, **kwargs):
        """
        This method will clean the asset, and is the base class default implentation
        """
        #Specify what to clean
        action=[]
        rcc = kwargs.get('rcc')
        hdl = kwargs.get('hdl')
        simulation = kwargs.get('simulation')
        execution = kwargs.get('execution')
        hdl_platform = kwargs.get('hdl_platform')
        hdl_target = kwargs.get('hdl_target')
        worker = kwargs.get('worker')
        # if any clean types are mentioned, do them all but not the big "clean"
        if rcc:
            action.append('cleanrcc')
        if hdl:
            action.append('cleanhdl')
        if simulation:
            action.append('cleansim')
        if execution:
            action.append('cleanrun')
        if not (rcc or hdl or simulation or execution):
            action.append('clean')
        settings = {}
        if hdl_platform:
            settings['hdl_plat_strs'] = hdl_platform
        if hdl_target:
            settings['hdl_target'] = hdl_target
        if worker:
            settings['worker'] = worker
        make_file = ocpiutil.get_makefile(self.directory, self.make_type)[0]
        #Clean
        ocpiutil.file.execute_cmd(settings, self.directory, action=action, file=make_file,
                                  verbose=kwargs.get('verbose'))

class HDLBuildableAsset(BuildableAsset):
    """
    Virtual class that requires that any child classes implement a build method.  Contains settings
    that are specific to all assets that can be run
    """
    valid_settings = ["hdl_plat_strs", "hdl_tgt_strs"]
    def __init__(self, directory, name=None, **kwargs):
        """
        Initializes HDLBuildableAsset member data  and calls the super class __init__
        valid kwargs handled at this level are:
            hdl_plat_strs (list) - list of hdl platforms(strings) to build for
            hdl_tgt_strs  (list) - list of hdl targets(strings) to build for
        """
        super().__init__(directory, name, **kwargs)

        # Collect the string lists of HDL Targets and Platforms from kwargs
        self.hdl_tgt_strs = kwargs.get("hdl_tgts", None)
        self.hdl_plat_strs = kwargs.get("hdl_plats", None)

        # Initialize the lists of hdl targets/platforms to empty sets
        # Note that they are sets instead of lists to easily avoid duplication
        #    Also note that there is no literal for the empty set in python3.4
        #    because {} is for dicts, so set() must be used.
        self.hdl_targets = set()
        self.hdl_platforms = set()

        import _opencpi.hdltargets as hdltargets
        # If there were HDL Targets provided, construct HdlTarget object for each
        # and add to the hdl_targets set
        if self.hdl_tgt_strs is not None:
            if "all" in self.hdl_tgt_strs:
                self.hdl_targets = set(hdltargets.HdlToolFactory.get_or_create_all("hdltarget"))
            else:
                for tgt in self.hdl_tgt_strs:
                    self.hdl_targets.add(hdltargets.HdlToolFactory.factory("hdltarget", tgt))
        # If there were HDL Platforms provided, construct HdlPlatform object for each
        # and add to the hdl_platforms set.
        # Also get the corresponding HdlTarget and add to the hdl_targets set
        if self.hdl_plat_strs is not None:
            if "all" in self.hdl_plat_strs:
                self.hdl_platforms = set(hdltargets.HdlToolFactory.get_or_create_all("hdlplatform"))
                self.hdl_targets = set(hdltargets.HdlToolFactory.get_or_create_all("hdltarget"))
            elif "local" not in self.hdl_plat_strs:
                for plat in self.hdl_plat_strs:
                    plat = hdltargets.HdlToolFactory.factory("hdlplatform", plat)
                    self.hdl_platforms.add(plat)
                    self.hdl_targets.add(plat.target)

class RCCBuildableAsset(BuildableAsset):
    """
    Virtual class that requires that any child classes implement a build method.  Contains settings
    that are specific to all assets that can be run
    """
    valid_settings = ["rcc_plats"]
    def __init__(self, directory, name=None, **kwargs):
        """
        Initializes HDLBuildableAsset member data  and calls the super class __init__
        valid kwargs handled at this level are:
            rcc_plat (list) - list of rcc platforms(strings) to build for
        """
        super().__init__(directory, name, **kwargs)
        self.rcc_plats = kwargs.get("rcc_plats", None)

class RunnableAsset(Asset):
    """
    Virtual class that requires that any child classes implement a run method.
    """
    valid_settings = []
    def __init__(self, directory, name=None, **kwargs):
        """
        Initializes RunnableAsset member data  and calls the super class __init__
        valid kwargs handled at this level are:
            None
        """
        super().__init__(directory, name, **kwargs)

    @abstractmethod
    def run(self, verbose=False):
        """
        This function will run the asset must be implemented by the child class
        """
        raise NotImplementedError("RunnableAsset.run() is not implemented")

class ShowableAsset(Asset):
    """
    Virtual class that requires that any child classes implement a show function
    """
    def __init__(self, directory, name=None, **kwargs):
        super().__init__(directory, name, **kwargs)

    @abstractmethod
    def show(self, format, verbose, **kwargs):
        """
        This function will show this asset must be implemented by the child class
        """
        raise NotImplementedError("ShowableAsset.show() is not implemented")

class ReportableAsset(Asset):
    """
    Skeleton class providing get/show_utilization functions
    for reporting utilization of an asset.

    get_utilization is generally overridden by sub-classes, but
    show_utilization is usually only overridden for sub-classes that are collections
    of OpenCPI assets (e.g. ones where show_utilization is called for children assets).
    """
    valid_formats = ["table", "latex"]
    def __init__(self, directory, name=None, format='table', **kwargs):
        """
        Initializes ReportableAsset member data  and calls the super class __init__
        valid kwargs handled at this level are:
            format (str) - mode to output utilization info (table, latex)
                                  formats not yet implemented: simple, json, csv
        """
        super().__init__(directory, name, **kwargs)

        self.format = format

    def get_utilization(self):
        """
        This is a placeholder function will be the function that returns ocpiutil.Report instance
        for this asset. Sub-classes should override this function to collect utilization information
        for this asset into a Report object to return.

        The returned Report contains data_points, which is an array of dictionaries. Each
        dict is essentially a data-point mapping dimension/header to value for that point.
        Reports also have metadata regarding ordering & sorting, and can be displayed in
        various formats.
        """
        raise NotImplementedError("ReportableAsset.get_utilization() is not implemented")

    def utilization(self, **kwargs):
        self.show_utilization()

    def show_utilization(self):
        """
        Show the utilization Report for this asset and print/record the results.

        This default behavior is likely sufficient, but sub-classes that are collections of OpenCPI
        assets may override this function to instead iterate over children assets and call their
        show_utilization functions.
        """
        # Get the directory type to add in the header/caption for the utilization info
        dirtype = ocpiutil.get_dirtype(self.directory)
        if dirtype is None:
            dirtype = "asset"
        caption = "Resource Utilization Table for " + dirtype + " \"" + self.name + "\""

        # Get the utilization using this class' hopefully overridden get_utilization() function
        util_report = self.get_utilization()
        if not util_report:
            if dirtype == "hdl-platform":
                plat_obj = hdltargets.HdlToolFactory.factory("hdlplatform", self.name)
                if not plat_obj.get_toolset().is_simtool:
                    logging.warning("Skipping " + caption + " because the report is empty")
            else:
                logging.warning("Skipping " + caption + " because the report is empty")
            return

        if self.format not in self.valid_formats:
            raise ocpiutil.OCPIException("Valid formats for showing utilization are \"" +
                                         ", ".join(self.valid_formats) + "\", but \"" +
                                         str(self.format) + "\" was chosen.")
        if self.format == "table":
            print(caption)
            # Maybe Report.print_table() should accept caption as well?
            # print the Report as a table
            util_report.print_table()
        if self.format == "latex":
            logging.info("Generating " + caption)
            # Record the utilization in LaTeX in a utilization.inc file for this asset
            util_file_path = self.directory + "/utilization.inc"
            with open(util_file_path, 'w') as util_file:
                # Get the LaTeX table string, and write it to the utilization file
                latex_table = util_report.get_latex_table(caption=caption)
                # Only write to the file if the latex table is non-empty
                if latex_table != "":
                    util_file.write(latex_table)
                    logging.info("  LaTeX Utilization Table was written to: " + util_file_path +
                                 "\n")
