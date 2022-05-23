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
Defining rcc/hdl platform related classes
"""

import os
import sys
import logging
import collections
from pathlib import Path
import jinja2
import _opencpi.assets.template as ocpitemplate
import json
import _opencpi.util as ocpiutil
import _opencpi.hdltargets as hdltargets
from .abstract import ShowableAsset, HDLBuildableAsset, ReportableAsset, Asset
from .assembly import HdlAssembly
from .worker import HdlWorker
from .factory import AssetFactory


class RccPlatformsCollection(ShowableAsset):
    """
    Collection of RCC Platforms. This class represents the rcc/platforms directory.
    """
    valid_settings = []
    def __init__(self, directory, name=None, verb=None, assets=None, **kwargs):
        if assets != None:
            self.out_of_project = True
        self.asset_type = 'rcc-platforms'
        kwargs['non_existent_ok'] = True
        super().__init__(directory, name, **kwargs)
        self.platforms = []
        dir_path = Path(self.directory)
        if assets != None: # we're being handed a list of paths
            for p in assets:
                self.platforms.append(RccPlatform(p))
        elif dir_path.exists(): # collection can be empty
            self.check_dirtype("rcc-platforms", self.directory)
            for path in Path(self.directory).iterdir():
                if path.is_dir() and path.joinpath(path.name+".mk").exists():
                    self.platforms.append(RccPlatform(str(path)))

    def show(self, format, verbose, **kwargs):
        """
        Show all of the RCC platforms in this collection
        """
        if format == "simple":
            for plat in self.platforms:
                print(plat.name + " ", end='')
            print()
        elif format == "table":
            rows = [["Platform", "Package-ID", "Target"]]
            for plat in self.platforms:
                rows.append([plat, plat.package_id, plat.attrs['target']])
            ocpiutil.print_table(rows, underline="-")
        elif format == "json":
            plat_dict={}
            for plat in self.platforms:
                plat_dict[plat.name] = plat.attrs
            json.dump(plat_dict, sys.stdout)
            print()

class HdlPlatformsCollection(HDLBuildableAsset, ReportableAsset):
    """
    Collection of HDL Platform Workers. This class represents the hdl/platforms directory.
    """

    valid_settings = []
    def __init__(self, directory, name=None, verb=None, assets=None, **kwargs):
        """
        Initializes HdlPlatformsCollection member data  and calls the super class __init__.
        Throws an exception if the directory passed in is not a valid hdl-platforms directory.
        """
        if assets != None:
            self.out_of_project = True
        self.asset_type = 'hdl-platforms'
        super().__init__(directory, name, **kwargs)
        self.platforms = []
        if assets != None: # we're being handed a list of paths
            for p in assets:
                self.platforms.append(AssetFactory.factory("hdl-platform", p,
                                                               **kwargs))
        elif verb != 'create':
            self.check_dirtype("hdl-platforms", self.directory)
            for path in Path(self.directory).iterdir():
                if path.is_dir() and path.joinpath(path.name+".xml").exists():
                    self.platforms.append(HdlPlatformWorker(str(path)))

    def show_utilization(self):
        """
        Show utilization separately for each hdl-platform in this collection
        """
        for platform in self.platform_list:
            platform.show_utilization()

    def build(self, **kwargs):
        """
        This is a placeholder function will be the function that builds this Asset
        """
        raise NotImplementedError("HdlPlatformsCollection.build() is not supported")

    def show(self, format=None, **kwargs):
        """
        Show all of the HDL platforms in this collection
        """
        if format == "simple":
            for plat in self.platforms:
                print(plat.name + " ", end='')
            print()
        elif format == "table":
            rows = [["Platform", "Package-ID", "Family", "Part", "Vendor", "Toolset"]]
            for plat in self.platforms:
                rows.append([plat.name + ('' if plat.attrs['built'] else '*'),
                             plat.package_id, plat.attrs['family'],
                             plat.attrs["part"], plat.attrs["vendor"],
                             plat.attrs["tool"]])
            ocpiutil.print_table(rows, underline="-")
            print("* An asterisk indicates that the platform has not been built yet.\n" +
                  "  Assemblies and tests cannot be built until the platform is built.")
        elif format == "json":
            plat_dict={}
            for plat in self.platforms:
                plat_dict[plat.name] = plat.attrs
            json.dump(plat_dict, sys.stdout)
            print()

# pylint:disable=too-many-ancestors
class HdlPlatformWorker(HdlWorker, ReportableAsset):
    """
    An HDL Platform Worker is a special case of HDL Worker that defines an HDL Platform.
    HDL Platforms have named build Configurations. HDL Platform Workers and Configurations
    can only be built for the HDL Platform that the worker defines.

    Each instance has a dictionary of configurations. This dict is of the form:
    self.platform_configs = {<config-name> : <HdlPlatformWorkerConfig-instance>}

    Each instance is bound to a single HdlPlatform instance (self.platform)

    """

    def __init__(self, directory, name=None, **kwargs):
        """
        Initializes HdlPlatformWorker member data  and calls the super class __init__. Throws an
        exception if the directory passed in is not a valid hdl-platform directory. Initialize
        platform configurations for this platform worker.
        valid kwargs handled at this level are:
            None
        """
        super().__init__(directory, name, **kwargs)
        self.asset_type = 'hdl-platform' #?
        self.make_type = 'hdl-platform' #?
        self.check_dirtype("hdl-platform", self.directory)
        project_dir = ocpiutil.get_path_to_project_top(self.directory)
        project_package_id = ocpiutil.get_project_package(project_dir)
        self.platform_configs = {}
        self.attrs = ocpiutil.get_platform_attributes(project_package_id, self.directory,
                                                      self.name, "hdl")
        if not self.attrs:
            raise ocpiutil.OCPIException("Could not find HDL Platform for its worker:  " + self.name)
        self.package_id = self.attrs['package_id']
        config_list = self.attrs.get('configurations')
        if not config_list:
            raise ocpiutil.OCPIException("Could not get list of HDL Platform Configurations for:" +
                                         name)
        #TODO this should be guarded by a init kwarg variable, not always needed i.e. show project
        self.init_platform_configs(config_list)

    # def get_make_vars(self):
    #     """
    #     Collect the list of build configurations and package id for this Platform Worker.
    #     """
    #     # Get the list of Configurations from make
    #     logging.debug("Get the list of platform Configurations from make")
    #     mkf=ocpiutil.get_makefile(self.directory, "hdl/hdl-platform")
    #     try:
    #         plat_vars = ocpiutil.set_vars_from_make(mkf,
    #                                                 mk_arg="ShellHdlPlatformVars=1 showinfo",
    #                                                 verbose=False)
    #     except ocpiutil.OCPIException:
    #         # if the make call causes and error assume configs are blank
    #         plat_vars = {"Configurations" : "", "Package":"N/A"}
    #     if "Configurations" not in plat_vars:
    #         raise ocpiutil.OCPIException("Could not get list of HDL Platform Configurations " +
    #                                      "from \"" + mkf[1])
    #     self.package_id = plat_vars["Package"]
    #     # This should be a list of Configuration NAMES
    #     config_list = plat_vars["Configurations"]
    #     return config_list

    def init_platform_configs(self, config_list):
        """
        Construct an HdlPlatformWorkerConfig for each and add to the self.platform_configs map.
        """
        # Directory for each config is <platform-worker-directory>/config-<configuration>
        for config_name in config_list:
            # Construct the Config instance and add to map
            self.platform_configs[config_name] = \
                HdlPlatformWorkerConfig(directory=self.directory,
                                        name=config_name,
                                        platform=self,
                                        child_path='config-' + config_name,
                                        non_existent_ok=True)

    def get_utilization(self):
        """
        Get any utilization information for this Platform Worker's Configurations

        The returned Report contains a data-point (dict) for each Configuration, stored in the
        Report instance's data_points array. Each data-point maps dimension/header to value for
        that configuration.
        """
        # Add to the default list of reportable synthesis items to report on
        ordered_headers = ["Configuration"] + hdltargets.HdlReportableToolSet.get_ordered_items()
        sort_priority = hdltargets.HdlReportableToolSet.get_sort_priority() + ["Configuration"]
        # Initialize an empty data-set with these default headers
        util_report = ocpiutil.Report(ordered_headers=ordered_headers, sort_priority=sort_priority)
        # Sort based on configuration name
        for cfg_name in sorted(self.platform_configs):
            # Get the dictionaries of utilization report items for this Platform Worker.
            # Each dictionary returned corresponds to one implementation of this
            # container, and serves as a single data-point/row.
            # Add all data-points for this container to the running list
            sub_report = self.platform_configs[cfg_name].get_utilization()
            if sub_report:
                # We want to add the container name as a report element
                # Add this data-set to the list of utilization dictionaries. It will serve
                # as a single data-point/row in the report
                sub_report.assign_for_all_points(key="Configuration", value=cfg_name)
                util_report += sub_report
        return util_report

    def _get_template_dict(name, directory, **kwargs):
        """
        used by the create function/verb to generate the dictionary of viabales to send to the
        jinja2 template.
        valid kwargs handled at this level are:
            platform       (string)      - Platform name
            comp_lib       (list of str) - Specify ComponentLibraries in Makefile
            xml_include    (list of str) - Specify XmlIncludeDirs in Makefile
            include_dir    (list of str) - Specify IncludeDirs in Makefile
            prim_lib       (list of str) - Specify Libraries in Makefile
            hdl_part       (string)      - Part name, defalt=xc7z020-1-clg484
            time_freq      (string)      - Time frequency, default=100e6
            no_sdp         (bool)        - No SDP (legacy usage)
        """
        hdl_part = kwargs.get("hdl_part", None)
        time_freq = kwargs.get("time_freq", None)
        no_sdp = kwargs.get("no_sdp", False)
        use_sdp = True if no_sdp == False else False
        comp_lib = kwargs.get("comp_lib", None)
        if comp_lib:
            comp_lib = " ".join(comp_lib)
        xml_include = kwargs.get("xml_include", None)
        if xml_include:
            xml_include = " ".join(xml_include)
        include_dir = kwargs.get("include_dir", None)
        if include_dir:
            include_dir = " ".join(include_dir)
        prim_lib = kwargs.get("prim_lib", None)
        if prim_lib:
            prim_lib = " ".join(prim_lib)
        template_dict = {
                        "platform" : name,
                        "comp_lib" : comp_lib,
                        "xml_include" :xml_include,
                        "include_dir" : include_dir,
                        "prim_lib" : prim_lib,
                        "hdl_part": hdl_part,
                        "time_freq": time_freq,
                        "use_sdp": use_sdp,
                        }
        return template_dict

    @staticmethod
    def create(name, directory, verbose=None, **kwargs):
        """
        Create an HDL platform asset
        """
        dir_path, name, parent_path = Asset.start_creation(directory, name, 'HDL Platform', kwargs)
        dir_path.mkdir(parents=True)
        platforms_path = parent_path.joinpath('platforms.xml')
        if not platforms_path.exists():
            template = jinja2.Template(ocpitemplate.HDLPLATFORM_PLATFORMS_XML, trim_blocks=True)
            ocpiutil.write_file_from_string(platforms_path, template.render(**{}))
        template_dict = HdlPlatformWorker._get_template_dict(name, directory, **kwargs)
        template = jinja2.Template(ocpitemplate.HDLPLATFORM_PLATFORM_XML, trim_blocks=True)
        ocpiutil.write_file_from_string(dir_path.joinpath(name + ".xml"), template.render(**template_dict))
        Asset.finish_creation('HDL platform', name, dir_path, verbose)


# pylint:enable=too-many-ancestors

class HdlPlatformWorkerConfig(HdlAssembly):
    """
    HDL Platform Worker Configurations are build-able HDL Assemblies that contain their
    HDL Platform Worker as well as HDL Device Workers. Each configuration can only be
    built for the HDL Platform defined by the configuration's HDL Platform Worker.

    Each instance has a target-<hdl-target> sub-directory where build artifacts can be found.

    Each instance is bound to a single HdlPlatform instance (self.platform)
    """
    def __init__(self, directory, name, platform=None, **kwargs):
        """
        Initializes HdlPlatformWorkerConfig member data and calls the super class __init__.
        valid kwargs handled at this level are:
            platform (HdlPlatform) - The HdlPlatform object that is bound to this configuration.
        """
        self.asset_type = 'hdl-platform-config'
        super().__init__(directory, name, **kwargs)
        self.platform = platform
        if self.platform is None:
            raise ocpiutil.OCPIException("HdlPlatformWorkerConfig cannot be constructed without " +
                                         "being provided a platform")
        self.subdir_prefix = directory + "/config-" + name

    #placeholder function
    def build(self, **kwargs):
        """
        This is a placeholder function will be the function that builds this Asset
        """
        raise NotImplementedError("HdlPlatformWorkerConfig.build() is not implemented")

    def get_utilization(self):
        """
        Get any utilization information for this instance

        The returned Report contains a single data-point (dict) for this Configuration,
        stored in the Report instance's data_points array.
        The data-point maps dimension/header to value for that configuration.

        Since a Platform Configuration is a synthesis asset, the utilization report will
        be generated with mode=synth
        """
        # We report for this Config's HDL Platform's toolset
        toolset = self.platform.target.toolset
        if isinstance(toolset, hdltargets.HdlReportableToolSet):
            return toolset.construct_report_item(self.subdir_prefix, target=self.platform.target,
                                                 mode="synth")
        else:
            return ocpiutil.Report()

class Platform(Asset):
    """
    Base Class for both rcc and hdl platforms
    """
    @classmethod
    def show_all(cls, format):
        """
        shows the list of all rcc and hdl platforms in the format specified from format
        (simple, table, or json)
        """
        if format == "simple":
            print("RCC:")
            RccPlatform.show_all(format)
            print("HDL:")
            HdlPlatform.show_all(format)
        elif format == "table":
            #need to combine rcc and hdl into a single table
            rcc_table = RccPlatform.get_all_table(RccPlatform.get_all_dict())
            rcc_table[0].insert(1, "Type")
            rcc_table[0].append("HDL Part")
            rcc_table[0].append("HDL Vendor")
            for my_list in rcc_table[1:]:
                my_list.append("N/A")
            for my_list in rcc_table[1:]:
                my_list.append("N/A")
            for my_list in rcc_table[1:]:
                my_list.insert(1, "rcc")
            hdl_table = HdlPlatform.get_all_table(HdlPlatform.get_all_dict())
            for my_list in hdl_table[1:]:
                my_list.insert(1, "hdl")
            for my_list in hdl_table[1:]:
                rcc_table.append(my_list)
            ocpiutil.print_table(rcc_table, underline="-")

        elif format == "json":
            rcc_dict = RccPlatform.get_all_dict()
            hdl_dict = HdlPlatform.get_all_dict()

            plat_dict = {"rcc":rcc_dict, "hdl":hdl_dict}
            json.dump(plat_dict, sys.stdout)
            print()

# pylint:disable=too-few-public-methods
class Target(object):
    """
    Base Class for both rcc and hdl targets
    """
    @classmethod
    def show_all(cls, format):
        """
        shows the list of all rcc and hdl targets in the format specified from format
        (simple, table, or json)
        """
        if format == "simple" or format == "table":
            print("RCC:")
            RccTarget.show_all(format)
            print("HDL:")
            HdlTarget.show_all(format)
        elif format == "json":
            rcc_dict = RccTarget.get_all_dict()
            hdl_dict = HdlTarget.get_all_dict()

            target_dict = {"rcc":rcc_dict, "hdl":hdl_dict}
            json.dump(target_dict, sys.stdout)
            print()
# pylint:enable=too-few-public-methods

class RccPlatform(Platform):
    """
    An OpenCPI RCC software platform
    """
    def __init__(self, directory, name=None, **kwargs):
        """
        Constructor for RccPlatform no extra values from kwargs processed in this constructor
        """
        self.asset_type = 'rcc-platform'
        super().__init__(directory, name, **kwargs)
        self.check_dirtype("rcc-platform", directory)
        project_dir = ocpiutil.get_path_to_project_top(self.directory)
        project_package_id = ocpiutil.get_project_package(project_dir)
        self.attrs = ocpiutil.get_platform_attributes(project_package_id, self.directory,
                                                      self.name, "rcc")
        if not self.attrs:
            raise ocpiutil.OCPIException("Could not find RCC Platform for:  " + self.name)
        self.package_id = self.attrs['package_id']

    def __str__(self):
        return self.name

    @classmethod
    def get_all_dict(cls):
        """
        returns a dictionary with all available rcc platforms from the RccAllPlatforms make variable
        """
        rcc_dict = ocpiutil.get_make_vars_rcc_targets()
        try:
            rcc_plats = rcc_dict["RccAllPlatforms"]
        except TypeError:
            raise ocpiutil.OCPIException("No RCC platforms found. Make sure the core project is " +
                                         "registered or in the OCPI_PROJECT_PATH.")
        plat_dict = {}
        for plat in rcc_plats:
            plat_dict[plat] = {}
            plat_dict[plat]["target"] = rcc_dict["RccTarget_" + plat][0]
            #proj_top = ocpiutil.get_project_package(rcc_dict["RccPlatformDir_" + plat][0])
            #plat_dict[plat]["package_id"] = proj_top + ".platforms." + plat
            plat_dict[plat]["package_id"] = rcc_dict["RccPlatformPackageID_" + plat][0]
            plat_dict[plat]["directory"] = rcc_dict["RccPlatformDir_" + plat][0]
        return plat_dict

    @staticmethod
    def get_all_table(cls, plat_dict):
        """
        returns a table (but does not print it) with all the rcc platforms in it
        """
        row_1 = ["Platform", "Package-ID", "Target"]
        rows = [row_1]
        for plat in plat_dict:
            rows.append([plat, plat_dict[plat]["package_id"], plat_dict[plat]["target"]])
        return rows

    @classmethod
    def show_all(cls, format):
        """
        shows all of the rcc platforms in the format that is specified using format
        (simple, table, or json)
        """
        plat_dict = cls.get_all_dict()

        if format == "simple":
            for plat in plat_dict:
                print(plat + " ", end='')
            print()
        elif format == "table":
            ocpiutil.print_table(cls.get_all_table(plat_dict), underline="-")
        elif format == "json":
            json.dump(plat_dict, sys.stdout)
            print()

class RccTarget(object):
    """
    An OpenCPI Rcc software platform (mostly meaningless just a internal for make)
    """
    def __init__(self, name, target):
        """
        Constructor for RccTarget no extra values from kwargs processed in this constructor
        """
        self.name = name
        self.target = target

    def __str__(self):
        return self.name

    @classmethod
    def get_all_dict(cls):
        """
        returns a dictionary with all available rcc targets from the RccAllPlatforms make variable
        """
        rcc_dict = ocpiutil.get_make_vars_rcc_targets()
        try:
            rcc_plats = rcc_dict["RccAllPlatforms"]

        except TypeError:
            raise ocpiutil.OCPIException("No RCC platforms found. Make sure the core project is " +
                                         "registered or in the OCPI_PROJECT_PATH.")
        target_dict = {}
        for plat in rcc_plats:
            target_dict[plat] = {}
            target_dict[plat]["target"] = rcc_dict["RccTarget_" + plat][0]
        return target_dict

    @classmethod
    def show_all(cls, format):
        """
        shows all of the rcc targets in the format that is specified using format
        (simple, table, or json)
        """
        target_dict = cls.get_all_dict()

        if format == "simple":
            for plat in target_dict:
                print(target_dict[plat]["target"] + " ", end='')
            print()
        elif format == "table":
            row_1 = ["Platform", "Target"]
            rows = [row_1]
            for plat in target_dict:
                rows.append([plat, target_dict[plat]["target"]])
            ocpiutil.print_table(rows, underline="-")
        elif format == "json":
            json.dump(target_dict, sys.stdout)
            print()

class HdlPlatform(Platform):
    """
    HdlPlatform
    A HDL Platform (e.g. zed, ml605, alst4, modelsim) has an exact-part number
    (e.g xc7z020-1-clg484) and a corresponding target (e.g zynq, virtex6,
    stratix4, modelsim). A flag is set which indicates whether this platform
    has been built yet.

    Example (doctest):
        >>> platform0 = HdlPlatform("myplat0", target1, "exactpart0")
        >>> platform1 = HdlPlatform("myplat1", target1, "exactpart1")
        >>> platform2 = HdlPlatform("myplat2", target2, "exactpart2")
        >>> [platform0.name, platform0.target.name, str(platform0.target.toolset)]
        ['myplat0', 'mytgt1', 'mytool1']
        >>> [platform1.name, platform1.target.name, str(platform1.target.toolset)]
        ['myplat1', 'mytgt1', 'mytool1']
        >>> [platform2.name, platform2.target.name, str(platform2.target.toolset)]
        ['myplat2', 'mytgt2', 'mytool2']
        >>> platform0.exactpart
        'exactpart0'
    """
    #TODO change to use kwargs too many arguments
    def __init__(self, name, target, exactpart, directory, built=False, package_id=None):
        """
        HdlPlatform constructor
        """
        self.out_of_project = True
        self.asset_type = 'hdl-platform' # redundant with HdlPlatformWorker
        super().__init__(directory, name, non_existent_ok=True) # not a real file system asset
        self.target = target
        self.exactpart = exactpart
        self.built = built
        self.dir = ocpiutil.rchop(directory, "/lib")
        if self.dir and not package_id and os.path.exists(self.dir):
            self.package_id = ocpiutil.get_platforms[name]['package_id']
        else:
            self.package_id = ""

    def __str__(self):
        return self.name

    def __lt__(self, other):
        if self.target.vendor < other.target.vendor:
            return True
        elif self.target.vendor == other.target.vendor:
            return str(self) < str(other)
        else:
            return False

    def get_toolset(self):
        """
        Return the toolset for this target
        """
        return self.target.toolset

    #TODO this can be static its not using cls
    @classmethod
    def get_all_dict(cls):
        """
        returns a dictionary with all available hdl platforms from the HdlAllPlatforms make variable
        """
        all_plats = hdltargets.HdlToolFactory.get_or_create_all("hdlplatform")
        plat_dict = {}
        for plat in all_plats:
            plat_dict[plat.name] = {}
            plat_dict[plat.name]["vendor"] = plat.target.vendor
            plat_dict[plat.name]["target"] = plat.target.name
            plat_dict[plat.name]["part"] = plat.exactpart
            plat_dict[plat.name]["built"] = plat.built
            plat_dict[plat.name]["directory"] = plat.dir
            plat_dict[plat.name]["tool"] = plat.target.toolset.name
            plat_dict[plat.name]["package_id"] = plat.package_id

        return plat_dict

    #TODO this can be static its not using cls
    @classmethod
    def get_all_table(cls, plat_dict):
        """
        returns a table (but does not print it) with all the hdl platforms in it
        """
        row_1 = ["Platform", "Package-ID", "Target", "Part", "Vendor", "Toolset"]
        rows = [row_1]
        for plat in plat_dict:
            built = ""
            if not plat_dict[plat]["built"]:
                built = "*"
            rows.append([plat + built, plat_dict[plat]["package_id"], plat_dict[plat]["target"],
                         plat_dict[plat]["part"], plat_dict[plat]["vendor"],
                         plat_dict[plat]["tool"]])
        return rows

    @classmethod
    def show_all(cls, format):
        """
        shows all of the hdl platforms in the format that is specified using format
        (simple, table, or json)
        """
        plat_dict = cls.get_all_dict()
        if format == "simple":
            for plat in plat_dict:
                print(plat + " ", end='')
            print()
        elif format == "table":
            ocpiutil.print_table(cls.get_all_table(plat_dict), underline="-")
            print("* An asterisk indicates that the platform has not been built yet.\n" +
                  "  Assemblies and tests cannot be built until the platform is built.\n")
        elif format == "json":
            json.dump(plat_dict, sys.stdout)
            print()


class HdlTarget(object):
    """
    HdlTarget
    A HDL target corresponds to a family (e.g. zynq, virtex6, stratix4) of parts.
    A target belongs to a vendor/top target (e.g. xilinx, altera, modelsim),
    and is associated with a toolset (e.g. vivado, quartus, xsim, modelsim).

    Example (doctest):
        >>> target0 = HdlTarget("mytgt0", "vend1", ["part0.1", "part0.2"], tool1)
        >>> target1 = HdlTarget("mytgt1", "vend1", ["part1.1", "part1.2"], tool1)
        >>> target2 = HdlTarget("mytgt2", "vend2", ["part2"], tool2)
        >>> [target1.name, target1.vendor, target1.parts, str(target1.toolset)]
        ['mytgt1', 'vend1', ['part1.1', 'part1.2'], 'mytool1']
        >>> [target2.name, target2.vendor, target2.parts, str(target2.toolset)]
        ['mytgt2', 'vend2', ['part2'], 'mytool2']
        >>> target1.name
        'mytgt1'
        >>> target1.parts
        ['part1.1', 'part1.2']
        >>> target2.vendor
        'vend2'
    """
    def __init__(self, name, vendor, parts, toolset):
        """
        Create an instance of HdlTarget.
        Give it a name and associate it with a vendor, a list of parts, and an HdlToolSet.
        """
        self.name = name
        self.vendor = vendor
        self.parts = parts
        # If the caller passed in a toolset instance instead of name, just assign
        # the instance (no need to construct or search for one). This is especially
        # useful for simple tests of this class (e.g. see doctest setup at end of file
        if isinstance(toolset, hdltargets.HdlToolSet):
            self.toolset = toolset
        else:
            self.toolset = hdltargets.HdlToolFactory.factory("hdltoolset", toolset)

    def __str__(self):
        return self.name

    def __lt__(self, other):
        if self.vendor < other.vendor:
            return True
        elif self.vendor == other.vendor:
            return str(self) < str(other)
        else:
            return False

    #TODO this can be static its not using cls
    @classmethod
    def get_all_dict(cls):
        """
        returns a dictionary with all available hdl targets from the HdlAllTargets make variable
        """
        target_dict = {}
        for vendor in hdltargets.HdlToolFactory.get_all_vendors():
            vendor_dict = {}
            for target in hdltargets.HdlToolFactory.get_all_targets_for_vendor(vendor):
                vendor_dict[target.name] = {"parts": target.parts,
                                            "tool": target.toolset.title}
            target_dict[vendor] = vendor_dict

        return target_dict

    #TODO this can be static its not using cls when get_all_dict is static
    @classmethod
    def show_all(cls, format):
        """
        shows all of the hdl targets in the format that is specified using format
        (simple, table, or json)
        """
        target_dict = cls.get_all_dict()
        if format == "simple":
            for vendor in target_dict:
                for target in target_dict[vendor]:
                    print(target + " ", end='')
            print()
        elif format == "table":
            rows = [["Target", "Parts", "Vendor", "Toolset"]]
            for vendor in target_dict:
                for target in target_dict[vendor]:
                    rows.append([target,
                                 ", ".join(target_dict[vendor][target]["parts"]),
                                 vendor,
                                 target_dict[vendor][target]["tool"]])
            ocpiutil.print_table(rows, underline="-")
        elif format == "json":
            json.dump(target_dict, sys.stdout)
            print()

class PlatformsCollection(ShowableAsset):
    """
    Collection of Platforms (of all types).
    """
    valid_settings = []
    def __init__(self, directory, name=None, verb=None, assets=None, **kwargs):
        if assets != None:
            self.out_of_project = True
        self.asset_type = 'platforms'
        super().__init__(directory, name, **kwargs)
        self.platforms = []
        dir_path = Path(self.directory)
        if assets != None: # we're being handed a list of paths
            for p in assets:
                model = p.parent.parent.name
                self.platforms.append(AssetFactory.factory(model+'-platform', str(p)))

    def show(self, format, verbose, **kwargs):
        """
        Show all of the platforms in this collection
        """
        if format == "simple":
            for plat in self.platforms:
                print(plat.name + " ", end='')
            print()
        elif format == "table":
            rows = [["Platform", "Package-ID", "Directory"]]
            for plat in self.platforms:
                rows.append([plat.name + ('' if plat.attrs['built'] else '*'),
                             plat.package_id, plat.directory])
            ocpiutil.print_table(rows, underline="-")
            print("* An asterisk indicates that the platform has not been built yet.\n" +
                  "  Assemblies and tests cannot be built until the platform is built.")
        elif format == "json":
            plat_dict={'rcc':{},'hdl':{}}
            for plat in self.platforms:
                plat_dict[plat.attrs['model']][plat.name] = plat.attrs
            json.dump(plat_dict, sys.stdout)
            print()

class HdlTargetsCollection(ShowableAsset):
    """
    Collection of HDL Targets (of all types).
    """
    valid_settings = []

    @staticmethod
    def ppp(x):
        return x[1].get('project',"NONE")

    def __init__(self, directory, name=None, verb=None, assets=None, **kwargs):
        self.out_of_project = True
        self.asset_type = 'hdl-targets'
        super().__init__(directory, name, **kwargs)
        dir_path = Path(self.directory)
        assert assets != None
        #assets.sort(key=lambda x:x[1].get('project',''))
        self.families = collections.OrderedDict(sorted(assets, key=HdlTargetsCollection.ppp))

    def show(self, format, verbose, **kwargs):
        """
        Show all of the platforms in this collection
        """
        if format == "simple":
            for name,_ in self.families.items():
                print(name + " ", end='')
            print()
        elif format == "table":
            _,_,toolsets,_ = ocpiutil.get_hdl_builtins() # need to get toolset name
            rows = [['Target/', 'Defined by', '', '', ''],
                    ["Family", 'Platform', 'Vendor', 'Tool', 'Parts']]
            for name,attrs in self.families.items():
                rows.append([name, attrs.get('package_id',''), attrs['vendor'],
                             toolsets[attrs['toolset']]['tool'], ' '.join(list(attrs['parts'].keys()))])
            ocpiutil.print_table(rows, underline="-", heading_rows=2)
        elif format == "json":
            json.dump(self.families, sys.stdout)
            print()
