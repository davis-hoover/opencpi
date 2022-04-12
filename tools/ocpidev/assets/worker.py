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
Definition of rcc and hdl workers and related classes
"""

import os
import sys
import re
import logging
import json
import jinja2
from abc import abstractmethod
from pathlib import Path
from xml.etree import ElementTree as ET
import _opencpi.hdltargets as hdltargets
import _opencpi.util as ocpiutil
from .abstract import HDLBuildableAsset, ReportableAsset, RCCBuildableAsset, ShowableAsset, Asset
from .component import ShowableComponent

class Worker(ShowableComponent):
    """
    Any OpenCPI Worker. This class is authoring model agnostic and represents all workers of any
    type. In general, something is a worker if it has an OWD (OpenCPI Worker Description File),
    and implements an OCS (OpenCPI Component Specification).
    """
    def __init__(self, directory, name=None, model=None, **kwargs):
        super().__init__(directory, name, **kwargs)
        if not self.asset_type:
            self.asset_type = 'worker'
        if not self.make_type:
            self.make_type = 'worker'
        self.model = model if model else self.name.split('.')[1]
        self.make_type = 'worker'
        package_id = kwargs.get("package_id")
        self.package_id = package_id if package_id else self._init_package_id()
        super().init_metadata(self.make_type, Path(self.directory),
                              Path(self.name.split('.')[0]+'.xml'), kwargs)
        self.build_configs = {}
        self.init_build_configs(**kwargs)

    all_worker_xml_attrs = (
        """
        {% if args.spec != 'none': %}
            {% if args.spec: %}
            Spec='{{args.spec}}'
            {% elif args.emulates: %}
            Spec='emulator'
            {% else: %}
            Spec='{{args.name.split('.')[0]}}'
            {% endif %}
        {% endif %}
        {% if args.xml_include: %}
            XmlIncludeDirs='{{' '.join(args.xml_include)}}'
        {% endif %}
        {% if args.include_dir: %}
            IncludeDirs='{{' '.join(args.include_dir)}}'
        {% endif %}
        {% if args.comp_lib: %}
            ComponentLibraries='{{' '.join(args.comp_lib)}}'
        {% endif %}
        {% if args.prim_lib: %}
            Libraries='{{' '.join(args.prim_lib)}}'
        {% endif %}
        {% if args.other: %}
            SourceFiles='{{' '.join(args.other)}}'
        {% endif %}
        {% if args.only_target: %}
            OnlyTargets='{{' '.join(args.only_target)}}'
        {% endif %}
        {% if args.exclude_target: %}
            ExcludeTargets='{{' '.join(args.exclude_target)}}'
        {% endif %}
        {% if args.only_platform: %}
            OnlyPlatforms='{{' '.join(args.only_platform)}}'
        {% endif %}
        {% if args.exclude_platform: %}
            ExcludePlatforms='{{' '.join(args.exclude_platform)}}'
        {% endif %}"""
        )
    all_worker_xml_elems = (
        """
        {% if args.spec == 'none': %}
            <componentspec/>
            <!-- Enter any worker properties here -->
            <!-- Enter any worker ports here -->
        {% else: %}
            <!-- Enter any augmentation of spec properties using <specproperty> elements here -->
            <!-- Enter any worker-specific properties using <property> elements here -->
        {% endif %}"""
    )

    @staticmethod
    def do_create(name, directory, pretty_type, asset_type, template, verbose=None, **kwargs):
        """
        Create a worker - called by each derived class
        """
        dir_path, kwargs['name'], parent_path = \
            Asset.start_creation(directory, name, pretty_type, kwargs)
        # This assertion is not valid for hdl/devices etc. at least for now.
        # assert parent_path.exists() # library must exist before worker is created
        dir_path.mkdir(parents=True)
        ocpiutil.write_file_from_string(dir_path.joinpath(name.replace('.','-') + ".xml"),
                                        Asset.process_template(template).render({'args' : kwargs}))
        Asset.finish_creation(asset_type, name, dir_path, verbose)

    @staticmethod
    def get_authoring_model(directory):
        """
        Each worker has an Authoring Model. Given a worker directory, return its Authoring Model.
        """
        dir_path = Path(directory)
        if '.' not in dir_path.name:
            dir_path = dir_path.resolve() #expensive
        return dir_path.parts[-1]

    def show(self, format, verbose, **kwargs):
        """
        Print out the ports, properties, and slaves of a given worker in the format that is
        provided by the caller

        Function attributes:
          format     - the mode to print out the information in table or simple are the only valid
                       options
          verbose    - integer for verbosity level 0 is default and lowest and anything above 1
                       shows struct internals and hidden properties
          kwargs     - no extra kwargs arguments expected
        """
        json_dict = self._get_show_dict(verbose)
        # add worker specific stuff to the dictionary
        prop_dict = json_dict["properties"]
        for prop in self.property_list:
            if verbose > 0 or prop.get("hidden", "0") == "0":
                prop_dict[prop["name"]]["isImpl"] = prop.get("isImpl", "0")
                access_dict = prop_dict[prop["name"]]["accessibility"]
                if prop_dict[prop["name"]]["isImpl"] == "0":
                    access_dict["specinitial"] = prop.get("specinitial", "0")
                    access_dict["specparameter"] = prop.get("specparameter", "0")
                    access_dict["specwritable"] = prop.get("specwritable", "0")
                    access_dict["specreadback"] = prop.get("specreadable", "0")
                    access_dict["specvolitile"] = prop.get("specvolitile", "0")
        slave_dict = {}
        for slave in self.slave_list:
            slave_dict[slave] = {"name": slave}
        json_dict["slaves"] = slave_dict

        if format == "simple" or format == "table":
            print("Worker: " + json_dict["name"] + " Package ID: " + json_dict["package_id"])
            print("Worker directory: " + json_dict["directory"])
            self._show_ports_props(json_dict, format, verbose, True)
            if json_dict.get("slaves"):
                rows = [["Slave Name"]]
                for slave in json_dict["slaves"]:
                    rows.append([json_dict["slaves"][slave]["name"]])
                ocpiutil.print_table(rows, underline="-")
        else:
            json.dump(json_dict, sys.stdout)
            print()

    def init_build_configs(self, **kwargs):
        """
        Parse this worker's build XML and populate its "configs" dictionary
        with mappings of <config-index> -> <config-instance>
        """
        # Determine if the build XML is named .build or -build.xml
        if os.path.exists(self.directory + "/" + os.path.basename(self.name) + "-build.xml"):
            build_xml = self.directory + "/" + self.name + "-build.xml"
        elif os.path.exists(self.directory + "/" + self.name + ".build"):
            build_xml = self.directory + "/" + self.name + ".build"
        else:
            # If neither is found, there is no build XML and so we assume there is only one config
            # and assign it index 0
            self.build_configs[0] = WorkerConfig(directory=self.directory, name=self.name,
                                                 config_index=0, **kwargs)
            return

        # Begin parsing the build XML
        root = ET.parse(build_xml).getroot()
        #TODO confirm root.tag is build?

        # Find each build configuration, get the ID, get all parameters (place in dict),
        # construct the HdlWorkerConfig instance, and add it to the "configs" dict
        for config in root.findall("configuration"):
            config_id = config.get("id")
            # Confirm the ID is an integer
            if config_id is not None:
                if not ocpiutil.isint(config_id):
                    raise ocpiutil.OCPIException("Invalid configuration ID in build XML \"" +
                                                 build_xml + "\".")
            # Find elements with type "parameter", and load them into the param_dict
            # as name -> value
            param_dict = {}
            for param in config.findall("parameter") + config.findall("Parameter"):
                pname = param.get("name")
                value = param.get("value")
                param_dict[pname] = value

            # Initialize the config instance with this worker's directory and name, and the
            # configuration's ID and parameter dictionary
            if config_id:
                self.build_configs[int(config_id)] = WorkerConfig(directory=self.directory,
                                                                  name=self.name,
                                                                  config_index=int(config_id),
                                                                  config_params=param_dict,
                                                                  **kwargs)

    def get_config_params_report(self):
        """
        Create a Report instance containing an entry for each configuration of this worker.
        Return that report. The Report's data_points member is an array that will hold
        a data-point (stored as a dictionary) for each configuration. The keys of each
        data-point/dict will be "Configuration" or parameter name, and the values are
        configuration index or parameter values.
        """
        # Initialize a report with headers matching "Configuration" and the parameter names
        report = ocpiutil.Report(ordered_headers=["Configuration"] +
                                 list(self.build_configs[0].param_dict.keys()))

        # For each configuration, construct a data-point with Configuration=index
        # and entries for each parameter key/value (just copy param_dict)
        for idx, config in self.build_configs.items():
            params = config.param_dict.copy()
            params["Configuration"] = idx
            # Append this data-point to the report
            report.append(params)
        return report

    def show_config_params_report(self):
        """
        Print out the Report of this Worker's configuration parameters.
        Each row will represent a single configuration, with each column representing
        either the Configuration index or a parameter value.

        Modes can be:
            table: plain text table to terminal
            latex: print table in LaTeX format to configurations.inc file in this
                   HdlLibraryWorker's directory
        """
        # TODO should this function and its output modes be moved into a super-class?
        dirtype = ocpiutil.get_dirtype(self.directory)
        caption = "Table of Worker Configurations for " + str(dirtype) + ": " + str(self.name)
        if self.format == "table":
            print(caption)
            # Print the resulting Report as a table
            self.get_config_params_report().print_table()
        elif self.format == "latex":
            logging.info("Generating " + caption)
            # Record the report in LaTeX in a configurations.inc file for this asset
            util_file_path = self.directory + "/configurations.inc"
            with open(util_file_path, 'w') as util_file:
                # Get the LaTeX table string, and write it to the configurations file
                latex_table = self.get_config_params_report().get_latex_table(caption=caption)
                # Only write to the file if the latex table is non-empty
                if latex_table != "":
                    util_file.write(latex_table)
                    logging.info("  LaTeX Configurations Table was written to: " + util_file_path +
                                 "\n")
        else:
            raise ocpiutil.OCPIException("Valid formats for showing worker configurations are \"" +
                                         ", ".join(self.valid_formats) + "\", but \"" +
                                         str(self.format) + "\" was chosen.")

# Placeholder class
class RccWorker(Worker,RCCBuildableAsset):
    """
    This class represents a RCC worker.
    """
    def __init__(self, directory, name=None, **kwargs):
        self.asset_type = 'rcc-worker'
        self.make_type = None
        super().__init__(directory, name, **kwargs)
        self.check_dirtype('rcc-worker', self.directory)

    template_xml = (
        """
        <!-- This file defines the {{args.name}} RCC worker. -->
        <RccWorker
            Language='{{args.language if args.language else "c++"}}'
            Version='{{args.version if args.version else '2'}}'"""+Worker.all_worker_xml_attrs+
        """
        {% if args.rcc_static_prereq: %}
            StaticPrereqLibs='{{' '.join(args.rcc_static_prereq)}}'
        {% endif %}
        {% if args.rcc_dynamic_prereq: %}
            DynamicPrereqLibs='{{' '.join(args.rcc_dynamic_prereq)}}'
        {% endif %}
            >"""+Worker.all_worker_xml_elems+
        """
        </RccWorker>
        """)

    @staticmethod
    def create(name, directory, verbose=None, **kwargs):
        """
        Create an RCC worker
        """
        Worker.do_create(name, directory, 'RCC Worker', 'rcc-worker', __class__.template_xml,
                         **kwargs)

class HdlCore(HDLBuildableAsset):
    """
    This represents any build-able HDL Asset that is core-like (i.e. is not a primitive library).

    For synthesis tools, compilation of a HdlCore generally results in a netlist.
        Note: for simulation tools, this criteria generally cannot be used because netlists
              are not commonly used for compilation targeting simulation
    """
    def __init__(self, directory, name=None, **kwargs):
        super().__init__(directory, name, **kwargs)

#THIS IS A PLACEHOLDER - to ultimately check the spec across project and library dependencies
def get_spec(parent_path, name, spec):
    if spec == None:
        spec = name
    project_path = is_path_to_project(parent_path)
    # First check whether there is a spec in the same library
    if (parent_path.joinpath("specs", name + '-spec.xml').exists() or
        parent_path.joinpath("specs", name + '_spec.xml').exists() or
        parent_path.joinpath(name + ".comp", name + "-spec.xml").exists()):
        return name
    if (project_path.joinpath("specs", name + '-spec.xml').exists() or
        project_path.joinpath("specs", name + '_spec.xml').exists()):
        return name
    print(f'Warning:  no spec option was specified and no component spec was found with the '+
          f'name "{name}" in this "{parent_path.name}" library or this project',
          file=sys.stderr)
    print(f'          this will fail to build unless the component spec is found in another '+
          f'library or another project',
          file=sys.stderr)
    return name

# pylint:disable=too-many-ancestors
class HdlWorker(Worker, HdlCore):
    """
    This class represents a HDL worker.
    Examples are HDL Library Worker, HDL Platform Worker ....
    """
    def __init__(self, directory, name=None, **kwargs):
        kwargs['model'] = 'hdl'
        super().__init__(directory, name, **kwargs)
        if not self.asset_type:
            self.asset_type = 'hdl-worker'
        if not self.make_type:
            self.make_type = None

# pylint:enable=too-many-ancestors

# pylint:disable=too-many-ancestors
class HdlLibraryWorker(HdlWorker, ReportableAsset):
    """
    An HDL Library worker is any HDL Worker that lives in a component/worker library.
    In general, this is any HDL Worker that is not an HDL Platform or Device Worker.
    This is not a perfect name for this asset-type, but it is accurate. This is any
    HDL worker that lives in a library.

    HdlLibraryWorker instances have configurations stored in "configs" which map configuration
    indices to HdlLibraryWorkerConfig instance.
    """
    def __init__(self, directory, name=None, **kwargs):
        """
        Construct HdlLibraryWorker instance, and initialize configurations of this worker.
        Forward kwargs to configuration initialization.
        """
        super().__init__(directory, name, **kwargs)
        self.check_dirtype('hdl-worker', self.directory)

    template_xml = (
        """
        <!-- This file defines the {{args.name}} HDL application worker. -->
        <HdlWorker
            Language='{{args.language if args.language else "vhdl"}}'
            Version='{{args.version if args.version else '2'}}'"""+Worker.all_worker_xml_attrs+
        """
        {% if args.core: %}
            Cores='{{' '.join(args.core)}}'
        {% endif %}
            >"""+Worker.all_worker_xml_elems+
        """
        </HdlWorker>
        """)

    @staticmethod
    def create(name, directory, verbose=None, **kwargs):
        """
        Create an HDL library worker
        """
        Worker.do_create(name, directory, 'HDL Worker', 'hdl-worker', __class__.template_xml,
                         **kwargs)

    def get_utilization(self):
        """
        Get any utilization information for this Platform Worker's Configurations

        The returned Report contains a data-point (dict) for each Configuration, stored in the
        Report instance's data_points array. Each data-point maps dimension/header to value for
        that configuration.
        """
        # Add to the default list of reportable synthesis items to report on
        ordered_headers = ["Configuration"] + hdltargets.HdlReportableToolSet.get_ordered_items()
        sort_priority = ["Configuration"] + hdltargets.HdlReportableToolSet.get_sort_priority()
        # Initialize an empty data-set with these default headers
        util_report = ocpiutil.Report(ordered_headers=ordered_headers, sort_priority=sort_priority)
        # Sort based on configuration name
        for cfg_name in sorted(self.build_configs):
            # Get the dictionaries of utilization report items for this Platform Worker.
            # Each dictionary returned corresponds to one implementation of this
            # container, and serves as a single data-point/row.
            # Add all data-points for this container to the running list
            sub_report = self.build_configs[cfg_name].get_utilization()
            if sub_report:
                # We want to add the container name as a report element
                # Add this data-set to the list of utilization dictionaries. It will serve
                # as a single data-point/row in the report
                sub_report.assign_for_all_points(key="Configuration", value=cfg_name)
                util_report += sub_report
        return util_report

    def show_utilization(self, **kwargs):
        """
        Show this worker's configurations with their parameter settings.
        Also show this worker's utilization report.
        """
        self.show_config_params_report()
        super().show_utilization(**kwargs)
# pylint:enable=too-many-ancestors

#TODO should implement HdlBuildableAsset
class WorkerConfig(ReportableAsset):
    """
    A configuration of an HdlLibraryWorker. An instance
    of this class represents one combination of an HDL worker's
    build-time parameters.
    """
    def __init__(self, directory, name=None, config_index=0, config_params={}, **kwargs):
        """
        Initializes HdlLibraryWorkerConfig member data and calls the super class __init__.
        valid kwargs handled at this level are:
            config_index (int) - index of this worker configuration. This dictates where the
                                 configuration's generated files will live and which build
                                 parameters map to this configuration.
        """
        super().__init__(directory, name, **kwargs)
        # We expect the config_index to be passed in via kwargs
        # These are generally defined in the worker build XML
        self.index = config_index
        # The worker sub-directory starts with 'target'.
        # It is then followed by the configuration index,
        # unless the index is 0.
        if self.index == 0:
            self.subdir_prefix = directory + "/target-"
        else:
            self.subdir_prefix = directory + "/target-" + str(self.index) + "-"
        # The config_params will contain build parameters for this configuration
        # in the form: parameter-name -> value
        self.param_dict = config_params

    def build(self, **kwargs):
        """
        This function will build the asset, must be implemented by the child class
        """
        raise NotImplementedError("build() is not implemented")

    def get_utilization(self):
        """
        Get the utilization Report instance for this worker configuration
        Do so for each target provided all within a single Report

        Since a Worker Configuration is a synthesis asset, the utilization report will
        be generated with mode=synth
        """
        # Get the default list of reportable synthesis items to report on
        ordered_headers = hdltargets.HdlReportableToolSet.get_ordered_items()
        sort_priority = hdltargets.HdlReportableToolSet.get_sort_priority()
        # Initialize an empty data-set with these default headers
        util_report = ocpiutil.Report(ordered_headers=ordered_headers, sort_priority=sort_priority)
        # Add data-points to this report/set for each target
        for tgt in self.hdl_targets:
            tgtdir = self.subdir_prefix + tgt.name
            if isinstance(tgt.toolset, hdltargets.HdlReportableToolSet):
                util_report += tgt.toolset.construct_report_item(directory=tgtdir, target=tgt,
                                                                 mode="synth")
        return util_report

class HdlDeviceWorker(HdlWorker, ReportableAsset):
    """
    An HDL device worker is a specialized HdlLibraryWorker
    The only difference is some create options and the XML tag
    """
    def __init__(self, directory, name=None, **kwargs):
        """
        Construct HdlLibraryWorker instance, and initialize configurations of this worker.
        Forward kwargs to configuration initialization.
        """
        self.asset_type = 'hdl-device'
        super().__init__(directory, name, **kwargs)
        self.check_dirtype('hdl-device', self.directory)

    template_xml = (
        """
        <!-- This file defines the {{args.name}} HDL application worker. -->
        <HdlDevice
            Language='{{args.language if args.language else "vhdl"}}'
            Version='{{args.version if args.version else '2'}}'"""+Worker.all_worker_xml_attrs+
        """
        {% if args.core: %}
            Cores='{{' '.join(args.core)}}'
        {% endif %}
        {% if args.emulates: %}
            Emulates='{{args.emulates}}'
        {% endif %}
            >
        {% if args.supports: %}
          {% for s in args.supports: %}
          <Supports Worker='{{s}}'>
            <!-- Add connections between this subdevice and the supported device,e.g.
            <Connect Port='rawprops' To='rprops' Index='0'/>
              -->
          </Supports>
          <!-- If this subdevice is sharing raw properties, include the line below.
               The count is the number of device workers that may share this subdevice
               The optional attribute is whether all the devices must be present

                  <rawprop name='rprops' count='2' optional='true'/>

               For each device worker this subdevice supports, include lines like these:
               Note the index is relative to the rawprops counted above
               <supports worker='lime_tx'>
                 <connect port='rawprops' to='rprops' index='1'/>
               </supports>
            -->
          {% endfor %}
        {% endif %}
        """+Worker.all_worker_xml_elems+
        """
            <!-- Enter any signal definitions using <signal> elements -->
        </HdlDevice>
        """)

    @staticmethod
    def create(name, directory, verbose=None, **kwargs):
        """
        Create an HDL library worker
        """
        Worker.do_create(name, directory, 'HDL Device Worker', 'hdl-device', __class__.template_xml,
                         **kwargs)

class WorkersCollection(ShowableAsset):
    """
    Collection of workers of any type
    """
    valid_settings = []
    def __init__(self, directory=None, name=None, assets=None, **kwargs):
        if assets != None:
            self.out_of_project = True
        super().__init__(directory, name, **kwargs)
        self.workers = []
        if assets != None:
            for worker_dir,parent_package_id in assets:
                worker_name = Path(worker_dir).name
                self.workers.append(Worker(worker_dir, None,
                                           package_id=parent_package_id + '.' + worker_name))
        else:
            self.check_dirtype('library', self.directory)
            for subdir in Path(self.directory).iterdir():
                if subdir.is_dir() and subdir.name != 'specs':
                    dirtype = ocpiutil.get_dirtype(subdir)
                    if dirtype and dirtype.endswith("worker"):
                        self.workers.append(Worker(str(subdir), None, **kwargs))

    def show(self, format=None, **kwargs):
        """
        Show all the components in all the projects in the registry
        """
        if format == "simple":
            for wkr in self.workers:
                print(wkr.name + " ", end="")
            print()
        elif format == "table":
            rows = [['Worker', 'Library Package ID', 'Directory']]
            for wkr in self.workers:
                rows.append([wkr.name, wkr.package_id, wkr.directory])
            ocpiutil.print_table(rows, underline="-")
        elif format == "json":
            worker_dict = {}
            for wkr in self.workers:
                worker_dict[wkr.package_id] = { 'name' : wkr.name, 'package_id' : wkr.package_id,
                                                'model' : wkr.model, 'directory' : wkr.directory }
            json.dump(worker_dict, sys.stdout)
            print()
