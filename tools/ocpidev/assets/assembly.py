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
Definition of HDL assembly and related classes
"""

import os
import logging
import jinja2
import _opencpi.assets.template as ocpitemplate
from pathlib import Path
import _opencpi.util as ocpiutil
import _opencpi.hdltargets as hdltargets
from .factory import AssetFactory
from .abstract import HDLBuildableAsset, ReportableAsset, Asset
from .worker import HdlCore

class HdlAssembly(HdlCore):
    """
    HDL Assembly: any collection/integration of multiple HDL Cores/Workers
    Examples include:
                     HdlApplicationAssembly
                     HdlPlatformConfiguration
                     HdlContainer[Implementation]
    """
    def __init__(self, directory, name=None, **kwargs):
        super().__init__(directory, name, **kwargs)
        # TODO Collect list of included HdlCores

class HdlApplicationAssembly(HdlAssembly, ReportableAsset):
    """
    The classic user-facing HDL Assembly. This is a collection of
    HDL Application/Library Workers. An HdlApplicationAssembly
    may reference the HDL containers that it supports
    """

    def __init__(self, directory, name=None, **kwargs):
        self.asset_type = 'hdl-assembly'
        super().__init__(directory, name, **kwargs)
        # container maps container name/XML to HdlContainer object
        self.containers = {}

    # TODO: Should we just init for all platforms in constructor, or wait for
    # user to call some function that requires containers and enforce that they
    # provide platforms as an argument?
    def collect_container_info(self, platforms):
        """
        Determine which containers exist that support the provided platforms.
        Each container will have a simple XML name and a full/implementation name.
        Each implementation is bound to a platform and platform configuration.

        Return the information in a dictionary with format:
            container_impl_dict =
                {
                    xml/simple-name : {
                                       impl-name : HdlPlatform
                                      }
                }
        """
        container_impl_dict = {}
        # Loop through the provided platforms, and determine what containers,
        # container implementations, and their corresponding platforms are
        # available to this assembly.
        for plat in platforms:
            plat_string = "HdlPlatform=" + plat.name
            # NOTE: We need to call make with a single HdlPlatform set because otherwise
            #       hdl-pre calls multiple sub-make commands and causes complications
            try:
                assemb_vars = ocpiutil.set_vars_from_make(ocpiutil.get_makefile(self.directory, "hdl/hdl-assembly"),
                                                          mk_arg=plat_string +
                                                          " shellhdlassemblyvars " +
                                                          "ShellHdlAssemblyVars=1",
                                                          verbose=False)
            #pylint:disable=broad-except
            except Exception:
                # if the make call throws a error this means that that hdl platform isn't built
                # the better fix is to have make handle this more gracefully
                continue
            #pylint:enable=broad-except
            if "Containers" not in assemb_vars:
                raise ocpiutil.OCPIException("Could not get list of HDL containers from " +
                                             "directory\"" + self.directory + "\"")
            # We get a top-level list of containers (e.g. container XMLs)
            for cname in assemb_vars['Containers']:
                # Get the list of container IMPLEMENTATIONS for this container XML name
                container_impls_str = "HdlContainerImpls_" + cname

                # Each container will have a dictionary for its implementations
                # Each dict will map implementation-name to supported platform
                if cname not in container_impl_dict:
                    # initialize implementation dict to {} for this container
                    container_impl_dict[cname] = {}

                # Ensure that the list of container implementations is found
                if container_impls_str in assemb_vars:
                    # For each container implementation, determine the corresponding HDL platform
                    for impl in assemb_vars[container_impls_str]:
                        container_plat = "HdlPlatform_" + impl
                        # Construct this implementation's platform and add the mapping to the
                        # implementation dictionary
                        plat_obj = hdltargets.HdlToolFactory.factory("hdlplatform",
                                                                     assemb_vars[container_plat][0])
                        container_impl_dict[cname][impl] = plat_obj

            container_impls_str = "HdlBaseContainerImpls"
            # Need to do one more pass to collect information about the base container (if used)
            # and collect its implementations as well
            if container_impls_str in assemb_vars and assemb_vars['HdlBaseContainerImpls']:
                if "base" not in container_impl_dict:
                    # initialize the implementation dict to {} for the base container
                    container_impl_dict["base"] = {}
                # For each implementation of the base container, determine the corresponding
                # HDL platform
                for cname in assemb_vars[container_impls_str]:
                    # Construct this implementation's platform and add the mapping to the
                    # implementation dictionary
                    container_plat = "HdlPlatform_" + cname
                    plat_obj = hdltargets.HdlToolFactory.factory("hdlplatform",
                                                                 assemb_vars[container_plat][0])
                    container_impl_dict["base"][cname] = plat_obj

        return container_impl_dict

    def init_containers(self, platforms):
        """
        Initialize the container instances mapped to by this assembly.
        First collect the container information, next construct each instance.

        Result is a dictionary (self.containers) mapping container-name to
        container object.
        """
        container_impl_dict = self.collect_container_info(platforms)

        for cname, impls in container_impl_dict.items():
            # It would be best if the AssetFactory used _get_or_create for
            # containers, but it cannot because it uses class type and directory
            # to determine uniqueness, and multiple containers share the same assembly directory
            self.containers[cname] = AssetFactory.factory("hdl-container", self.directory,
                                                          name=cname, container_impls=impls)

    def get_utilization(self):
        """
        Get utilization report for this ApplicationAssembly.
        Get the utilization for each of container this assembly references.

        The returned Report contains a data-point (dict) for each Container, stored in the
        Report instance's data_points array. Each data-point maps dimension/header to value for
        that container.
        """
        self.init_containers(self.hdl_platforms)
        # Sort based on container name
        util_report = ocpiutil.Report()
        for cname in sorted(self.containers):
            # Get the dictionaries of utilization report items for this container.
            # Each dictionary returned corresponds to one implementation of this
            # container, and serves as a single data-point/row.
            # Add all data-points for this container to the running list
            util_report += self.containers[cname].get_utilization()
        return util_report

    def _get_template_dict(name, directory, **kwargs):
        """
        used by the create function/verb to generate the dictionary of viabales to send to the
        jinja2 template.
        valid kwargs handled at this level are:
            assembly         (string)    - HDL Assembly name
            only_target      (string)    - Only build for the specified HDL arch
            exclude_target   (string)    - Do not build for the specified HDL arch
            only_platform    (string)    - Only build for the specified HDL platform
            exclude_platform (string)    - Do not build for the specified HDL platform
        """
        only_target = kwargs.get("only_target", None)
        if only_target:
            only_target = " ".join(only_target)
        exclude_target = kwargs.get("exclude_target", None)
        if exclude_target:
            exclude_target = " ".join(exclude_target)
        only_platform = kwargs.get("only_platform", None)
        if only_platform:
            only_platform = " ".join(only_platform)
        exclude_platform = kwargs.get("exclude_platform", None)
        if exclude_platform:
            exclude_platform = " ".join(exclude_platform)
        template_dict = {
                        "assembly" : name,
                        "only_target" : only_target,
                        "exclude_target" : exclude_target,
                        "only_platform" : only_platform,
                        "exclude_platform" : exclude_platform,
                        }
        return template_dict

    @staticmethod
    def create(name, directory, verbose=None, **kwargs):
        """
        Create an HDL assembly asset
        """
        assemblies_path = Path(directory)
        assembly_path = assemblies_path.joinpath(name)
        assembly_file_path = assembly_path.joinpath(name + ".xml")
        if assembly_path.exists():
            raise ocpiutil.OCPIException(f'HdlAssembly "{name}" already exists at "{assembly_path}"')
        if not assemblies_path.exists():
            assemblies_path.mkdir(parents=True)
            template = jinja2.Template(ocpitemplate.HDL_ASSEMBLIES_XML, trim_blocks=True)
            ocpiutil.write_file_from_string(assemblies_path.joinpath("assemblies.xml"),
                                            template.render({}))
        assembly_path.mkdir()
        template_dict = HdlApplicationAssembly._get_template_dict(name, directory, **kwargs)
        template = jinja2.Template(ocpitemplate.HDL_ASSEMBLY_XML, trim_blocks=True)
        ocpiutil.write_file_from_string(assembly_file_path, template.render(**template_dict))
        Asset.finish_creation('HDL assembly', name, assembly_path, verbose)


class HdlAssembliesCollection(HDLBuildableAsset, ReportableAsset):
    """
    This class represents an OpenCPI Project's hdl/assemblies directory
    Instances of this class can contain a list of contained assemblies in "assembly_list"
    """

    def __init__(self, directory, name=None, verb=None, verbose=None, **kwargs):
        """
        Initializes assemblies collection member data and calls the super class __init__. Throws
        an exception if the directory passed in is not a valid  hdl-assemblies directory.
        valid kwargs handled at this level are:
            init_hdl_assembs (T/F) - Instructs the method whether to construct all
                                     HdlApplicationAssembly objects contained in the project
        """
        super().__init__(directory, name, **kwargs)
        self.check_dirtype("hdl-assemblies", self.directory)
        self.assembly_list = []
        if verb == 'utilization' or verb == 'show':
            logging.debug("HdlAssembliesCollection constructor creating HdlApplicationAssembly " +
                          "Objects")
            for assemb_directory in self.get_valid_assemblies():
                self.assembly_list.append(AssetFactory.factory("hdl-assembly", assemb_directory,
                                                               **kwargs))

    def get_valid_assemblies(self):
        """
        Probes make in order to determine the list of active assemblies in the
        assemblies collection
        """
        assembs_list = []
        mkf=ocpiutil.get_makefile(self.directory, "hdl/hdl-assemblies")
        ocpiutil.logging.debug("Getting valid assemblies from: " + mkf[0])
        make_assembs = ocpiutil.set_vars_from_make(mkf,
                                                   mk_arg="ShellAssembliesVars=1 showassemblies",
                                                   verbose=True)["Assemblies"]

        # Collect list of assembly directories
        for name in make_assembs:
            assembs_list.append(self.directory + "/" + name)
        return assembs_list

    def show_utilization(self):
        """
        Show utilization separately for each assembly in this collection
        """
        for assembly in self.assembly_list:
            assembly.show_utilization()

class HdlContainer(HdlAssembly, ReportableAsset):
    """
    Instances of this class represent HDL Containers, which are specified in XML
    and are a special type of HDL Assembly that includes a platform configuration
    and an application assembly as well as other workers.

    An HDL Container can also be implied (e.g. the base/default container)

    Containers have various implementations which are bound to platform configurations.
    These implementations are stored in an instance field "implementations" that maps
    HDL Container Implementation name to HdlContainerImplementation instance.
    """

    def __init__(self, directory, name=None, container_impls={}, **kwargs):
        """
        Initializes HdlContainer member data and calls the super class __init__.
        valid kwargs handled at this level are:
            container_impls (dict) - Dictionary mapping container implementation name
                                     to the HdlPlatform that it maps to.
        """
        super().__init__(directory, name, **kwargs)

        # Maps container implementation names to their corresponding
        # HdlContainerImplementation instances
        self.implementations = {}
        # We expect to see a 'container_impls' argument that is a dictionary mapping
        # full container implementation names to the platforms they support
        for impl_name, plat in container_impls.items():
            impl_dir = self.parent + "/container-" + impl_name
            self.implementations[impl_name] = HdlContainerImplementation(directory=impl_dir,
                                                                         platform=plat)

    def get_utilization(self):
        """
        Get the utilization Report for this Container. It will be combination of reports for
        each container implementation with a leading "Container" column

        The returned Report contains a data-point (dict) for each container implementation,
        stored in the Report instance's data_points array.
        Each data-point maps dimension/header to value for that implementation.
        """
        # Add to the default list of reportable synthesis items to report on
        ordered_headers = ["Container"] + hdltargets.HdlReportableToolSet.get_ordered_items("impl")
        sort_priority = hdltargets.HdlReportableToolSet.get_sort_priority() + ["Container"]
        # Initialize an empty data-set with these default headers
        util_report = ocpiutil.Report(ordered_headers=ordered_headers, sort_priority=sort_priority)
        for impl in self.implementations.values():
            # Get the dictionary that maps utilization report "headers" to discovered "values"
            # Do this for the current container implementation
            sub_report = impl.get_utilization()

            # If the container implementation returns a dict of utilization information,
            # add it to the list
            if sub_report:
                # We want to add the container name as a report element
                sub_report.assign_for_all_points(key="Container", value=self.name)
                # Add this data-set to the list of utilization dictionaries. It will serve
                # as a single data-point/row in the report
                util_report += sub_report
        return util_report

class HdlContainerImplementation(HdlAssembly):
    """
    Instances of this class represent specific implementations of an HDL Container
    A Container Implementation is bound to a single Platform and even a single
    Platform Configuration
    """
    #TODO map to a platform configuration? At least get name from make
    def __init__(self, directory, name=None, platform=None, **kwargs):
        """
        Initializes HdlContainerImplementation member data and calls the super class __init__.
        valid kwargs handled at this level are:
            platform (HdlPlatform) - The HdlPlatform object that is bound to this implementation.
        """
        super().__init__(directory, name, **kwargs)
        self.platform = platform
        # The sub-directory where target-specific artifacts will be made for this
        # container implementation
        self.target_subdir = self.directory + "/target-" + self.platform.target.name

    def get_utilization(self):
        """
        Generate a report/data-set containing the utilization for this implementation
        This will basically just be a report with a single datapoint in it

        The returned Report contains a single data-point (dict) for this container implementation,
        stored in the Report instance's data_points array.
        The data-point maps dimension/header to value for that implementation.

        Since a Container Implementation is an implementation asset, the utilization report will
        be generated with mode=impl
        """
        if isinstance(self.platform.target.toolset, hdltargets.HdlReportableToolSet):
            return self.platform.target.toolset.construct_report_item(directory=self.target_subdir,
                                                                      platform=self.platform,
                                                                      mode="impl")
