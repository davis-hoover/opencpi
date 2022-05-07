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
Definition of Component and ShowableComponent classes
"""

import os
import re
import sys
import pathlib
import subprocess
import logging
import json
import _opencpi.assets.template as ocpitemplate
from os.path import dirname
from pathlib import Path
from xml.etree import ElementTree as ET
import _opencpi.util as ocpiutil
from .abstract import BuildableAsset,ShowableAsset,Asset

class ShowableComponent(ShowableAsset):
    """
    Any OpenCPI Worker or Component.  Intended to hold all the common functionality of workers and
    components.  Expected to be a virtual class and no real objects will get created of this class
    even though nothing prevents it.
    """
    def __init__(self, directory, name=None, **kwargs):
        super().__init__(directory, name, **kwargs)

    def init_metadata(self, make_type, directory, xml_file, args):
        """
        Initialize the metadata for this asset.
        The directory arg in this case is where xml file lives, not necessarily
        the parent directory of this asset (which is self.directory)
        """
        if args.get('verb') != 'show':
            return
        xml = ocpiutil.get_xml_string_from_file(make_type, directory, xml_file)

        ocpiutil.logging.debug("Component Artifact XML from ocpigen: \n" + str(xml))
        try:
            parsed_xml = ET.fromstring(xml) # convert string to xml tree
        except ET.ParseError as e:
            raise ocpiutil.OCPIException(f'Error in preprocessed results from xml file: {xml_file}: {e}\n'+
                                         f'Output was:  "{xml}"')

        self.property_list = []
        self.port_list = []
        self.slave_list = []
        #set up self.property_list from the xml
        for props in parsed_xml.findall("property"):
            temp_dict = props.attrib
            enum = temp_dict.get("enums")
            if enum:
                temp_dict["enums"] = enum.split(",")
            if props.attrib.get("type") == "Struct":
                temp_dict["Struct"] = self.get_struct_dict_from_xml(props.findall("member"))
            self.property_list.append(temp_dict)
        #set up self.port_list from this dict
        for port in parsed_xml.findall("port"):
            port_details = port.attrib
            for child in port:
                if child.tag == "protocol":
                    port_details["protocol"] = child.attrib.get("padding", "N/A")
            self.port_list.append(port_details)
        #set up self.slave_list from the xml
        for slave in parsed_xml.findall("slave"):
            self.slave_list.append(slave.attrib["worker"])


    def show(self, format, verbose, **kwargs):
        """
        Not implemented and not intended to be implemented
        """
        raise NotImplementedError("show() is not implemented")

    def _init_package_id(self):
        """
        Determine the Package id based on the library or project that the component or worker
        resides in.  Only a component will reside at the top level of a project (in specs dir)
        """
        parent_dir = str(self.parent)
        dirtype = ocpiutil.get_dirtype(parent_dir)
        if dirtype == "library":
            ret_val = ocpiutil.set_vars_from_make(ocpiutil.get_makefile(parent_dir, "library"),
                                                  mk_arg="showpackage ShellLibraryVars=1",
                                                  verbose=True)["Package"][0]
        elif dirtype == "project":
            ret_val = ocpiutil.set_vars_from_make(ocpiutil.get_makefile(parent_dir, "project"),
                                                  mk_arg="projectpackage ShellProjectVars=1",
                                                  verbose=True)["ProjectPackage"][0]
        elif dirtype == "hdl-platforms":
            ret_val = "N/A"
        else:
            raise ocpiutil.OCPIException("Could not determine Package-ID of component dirtype of " +
                                         "parent directory: " + parent_dir + " dirtype: " + str(dirtype))
        return ret_val

    def __show_table_ports_props(self, json_dict, verbose, is_worker):
        """
        print out the ports and properties of the component in table format
        """
        if json_dict.get("properties"):
            rows = ([["Property Name", "Spec Property", "Type", "Accessability"]] if is_worker else
                    [["Property Name", "Type", "Accessability"]])
            for prop in json_dict["properties"]:
                access_str = ""
                for access in json_dict["properties"][prop]["accessibility"]:
                    if json_dict["properties"][prop]["accessibility"][access] == "1":
                        access_str += access + " "
                if is_worker:
                    rows.append([prop,
                                 json_dict["properties"][prop]["isImpl"] == 1,
                                 self.get_type_from_dict(json_dict["properties"][prop]),
                                 access_str])
                else:
                    rows.append([prop,
                                 self.get_type_from_dict(json_dict["properties"][prop]),
                                 access_str])
            ocpiutil.print_table(rows, underline="-")
            if verbose > 0:  #output any structs
                for prop in json_dict["properties"]:
                    if json_dict["properties"][prop]["type"] == "Struct":
                        print("Struct for " + prop)
                        rows = [["Member Name", "Type"]]
                        for member in json_dict["properties"][prop]["Struct"]:
                            member_dict = json_dict["properties"][prop]["Struct"][member]
                            rows.append([member,
                                         self.get_type_from_dict(member_dict)])
                        ocpiutil.print_table(rows, underline="-")
        if json_dict.get("ports"):
            rows = [["Port Name", "Protocol", "Producer"]]
            for port in json_dict["ports"]:
                rows.append([port,
                             json_dict["ports"][port]["protocol"],
                             json_dict["ports"][port]["producer"]])
            ocpiutil.print_table(rows, underline="-")

    @staticmethod
    def __show_simple_ports_props(json_dict):
        """
        print out the ports and properties of the component in simple format 
        """
        if json_dict.get("properties"):
            print("Properties:")
            for prop in json_dict["properties"]:
                print(prop + " ", end="")
            print()
        if json_dict.get("ports"):
            print("ports:")
            for port in json_dict["ports"]:
                print(port + " ", end="")
            print()

    def _show_ports_props(self, json_dict, format, verbose, is_worker):
        """
        Print out the ports and properties of a given component/worker given the dictionary that is
        passed in with this information in it

        Function attributes:
          json_dict  - the constructed dictionary to output the information for
          format    - the mode to print out the information in table or simple are the only valid
                       options
          verbose    - integer for verbosity level 0 is default and lowest and anything above 1
                       shows struct internals and hidden properties
          is_ worker - switch for component vs worker is intended for limited use otherwise there
                       should be 2 separate functions rather then using this Boolean
        """
        if format == "simple":
            self.__show_simple_ports_props(json_dict)
        elif format == "table":
            self.__show_table_ports_props(json_dict, verbose, is_worker)

    def get_struct_dict_from_xml(self, struct):
        """
        Static and recursive function that will generate the dictionary for Struct of Stuct of
        Struct ... etc. data-types.
        """
        ret_dict = {}
        for member in struct:
            name = member.attrib["name"]
            ret_dict[name] = {}
            if member.attrib.get("type", "ULong") == "Struct":
                ret_dict[name]["Struct"] = self.get_struct_dict_from_xml(member.findall("member"))
            ret_dict[name]["type"] = member.attrib.get("type", "ULong")
            ret_dict[name]["name"] = name
            enum = member.attrib.get("enums")
            if enum:
                ret_dict[name]["enums"] = enum.split(",")
            other_details = [detail for detail in member.attrib
                             if detail not in ["type", "name", "enums"]]
            for detail in other_details:
                ret_dict[name][detail] = member.attrib[detail]
        return ret_dict

    @classmethod
    def get_type_from_dict(cls, my_dict):
        """
        For use with printing in table mode will output a more informational data-type for more
        complex data-types like arrays, structs, enums etc.  returns a string of the data-type that
        caller prints out to the screen
        """
        base_type = my_dict.get("type", "ULong")
        is_seq = my_dict.get("sequenceLength")
        is_array = my_dict.get("arrayLength")
        if not is_array:
            is_array = my_dict.get("arrayDimensions")
        is_enum = my_dict.get("enums")
        is_string = my_dict.get("stringLength")
        #change the base-type string for enums or strings
        if is_enum:
            base_type = "Enum " + str(is_enum)
        elif is_string:
            base_type = "String[" + is_string + "]"
        #add sequence or array information on to the front of the output string where applicable
        if is_seq and is_array:
            prop_type = "Sequence{" + is_seq + "} of Array[" + is_array +"] of " + base_type
        elif is_seq:
            prop_type = "Sequence{" + is_seq + "} of " + base_type
        elif is_array:
            prop_type = "Array[" + is_array + "] of " + base_type
        else:
            prop_type = base_type
        return prop_type

    def _get_show_dict(self, verbose):
        """
        compose and return the dictionary that the show verb uses to output information about this
        worker/component.
        Function attributes:
          verbose - data-type of integer if number is non zero hidden properties are added to the
                    dictionary as well as more information about struct data-types
        """
        json_dict = {}
        port_dict = {}
        prop_dict = {}
        for prop in self.property_list:
            if verbose > 0 or prop.get("hidden", "0") == "0":
                combined_reads = prop.get("readable", "0") +  prop.get("readback", "0")
                # doing an or on string values is set to "1" if either readable or readback are "1"
                readback = "0" if combined_reads == "00" else "1"
                prop_detatils = {"accessibility": {"initial" : prop.get("initial", "0"),
                                                   "readback" : readback,
                                                   "writable" : prop.get("writable", "0"),
                                                   "volatile" : prop.get("volatile", "0"),
                                                   "parameter" : prop.get("parameter", "0"),
                                                   "padding" : prop.get("padding", "0")},
                                 "name" : prop.get("name", "N/A"),
                                 "type" : prop.get("type", "ULong")}

                required_details = ["initial", "readback", "writable", "volatile", "parameter",
                                    "padding", "type", "name", "specparameter", "specinitial",
                                    "specwritable", "specreadable", "specvolitile"]
                if verbose <= 0:
                    #Adding this here causes struct to not be put into the dictionary
                    required_details.append("Struct")
                other_details = [detail for detail in prop if detail not in required_details]
                for prop_attr in other_details:
                    prop_detatils[prop_attr] = prop[prop_attr]
                prop_dict[prop["name"]] = prop_detatils
        for port  in self.port_list:
            port_detatils = {"protocol": port.get("protocol", None),
                             "producer": port.get("producer", "0")}
            port_dict[port["name"]] = port_detatils
        json_dict["ports"] = port_dict
        json_dict["properties"] = prop_dict
        json_dict["name"] = self.name
        json_dict["package_id"] = self.package_id
        json_dict["directory"] = self.directory
        return json_dict

class Component(ShowableComponent,BuildableAsset):
    """
    Any OpenCPI Component.
    It is buildable for docs
    """
    def __init__(self, directory, name, **kwargs):
        # Allow the API to incorrectly supply a "specs" directory as the parent asset dir
        dir_path = Path(directory)
        if dir_path.name == 'specs':
            directory = str(dir_path.parent)
        elif dir_path.parts[-2] == 'specs':
            name = dir_path.parts[-1]
            directory = str(dir_path.parent.parent)
        if not getattr(self, 'asset_type', None):
            self.asset_type = 'component'
        super().__init__(directory, name, **kwargs)
        package_id = kwargs.get("package_id")
        self.package_id = package_id if package_id else self._init_package_id()
        my_path = Path(self.directory)
        # yet another place to deal with two types of components
        if my_path.is_dir():
            xml_file = None # it is implicit
            make_type = 'component'
        else:
            xml_file = my_path.name
            my_path = self.parent
            make_type = 'library'
        super().init_metadata(make_type, my_path, xml_file, kwargs)

    @classmethod
    def _get_project_package_id(cls, parent_path, project=None, **kwargs):
        """ If we are at project level, return the project's package_id """
        if project:
            return ocpiutil.set_vars_from_make(ocpiutil.get_makefile(parent_path, "project"),
                                               mk_arg="projectpackage ShellProjectVars=1",
                                               verbose=True)["ProjectPackage"][0]
        return None

    def show(self, format, verbose, **kwargs):
        """
        Print out the ports and properties of a given component in the format that is provided by
        the caller

        Function attributes:
          format    - the mode to print out the information in table or simple are the only valid
                       options
          verbose    - integer for verbosity level 0 is default and lowest and anything above 1
                       shows struct internals and hidden properties
          kwargs     - no extra kwargs arguments expected
        """
        json_dict = self._get_show_dict(verbose)

        if format == "simple" or format == "table":
            print("Component: " + json_dict["name"] + " Package ID: " + json_dict["package_id"])
            print("Directory: " + json_dict["directory"])
            self._show_ports_props(json_dict, format, verbose, False)
        else:
            json.dump(json_dict, sys.stdout)
            print()

    @staticmethod
    def get_workers(directory="."):
        workers = []
        mkf=ocpiutil.get_makefile(directory,"library")
        make_dict = ocpiutil.set_vars_from_make(mkf,
          mk_arg="ShellLibraryVars=1 showlib", verbose=True)
        wkrs = make_dict["Workers"]
        for name in wkrs:
            if name.endswith((".rcc", ".rcc/", ".hdl", ".hdl/")):
                workers.append(name + " ")
        return (workers)

    @staticmethod
    def get_filename(directory, name, project, ensure_exists=True):
        """Gets the appropriate file name of a component asset"""
        if ensure_exists:
            end_list = ["", ".xml", "_spec.xml", "-spec.xml"]
            for ending in end_list:
                path = Path(directory, name+ending)
                if path.exists():
                    return str(path)
                elif project:
                    project_path = Path(ocpiutil.get_path_to_project_top())
                    path = Path(project_path, name+ending)
                    if path.exists():
                        return str(path)
            err_msg = 'Unable to find component "{}" in directory {}'.format(
                name, directory)
            print(err_msg)
            exit(1)
            # An exception now will just call the bash code
            # TODO: replace print/exit with OCPIException
            #raise ocpiutil.OCPIException(err_msg)

        path = Path(directory, name)
        path_stem = path.stem
        if not re.search('_spec$|-spec$', path_stem):
            path_stem += '-spec'
        path_stem += '.xml'
        path = Path(directory, path_stem)
        return str(path)

    @staticmethod
    def create(name, directory, file_only=False, project=None, no_control=None, **kwargs):
        """
        Static method to create a new Component, either as a *.comp directory
        with a *-spec.xml file in that directory, or just a  specs/*-spec.xml file.
        No object is created, only file system operations are performed.
        """
        path, name, parent_path = Asset.start_creation(directory, name, 'component', kwargs)
        if project:
            file_only = True
        if file_only and not project: #  "specs/* file" special case that does not produce any doc
            os.environ['OCPI_NO_DOC'] = '1'
        Asset.create_file_asset("component", "spec" if file_only else "comp", directory, name,
                                ocpitemplate.COMPONENT_SPEC_NO_CTRL_XML
                                if no_control else
                                ocpitemplate.COMPONENT_SPEC_XML,
                                (lambda name, dir, **args: { 'component' : name }),
                                __class__._get_project_package_id(parent_path, **kwargs),
                                kwargs,
                                dir_suffix=None if file_only else '.comp')

    def delete(self, **kwargs):
        """
        Delete the component, whether file-based or directory-based
        """

        was_dir = self.path.is_dir()
        if not super().delete(**kwargs):
            return False # user declined to delete, file or directory
        if was_dir:
            # When the component is a directory, the base class method does not deal with
            # the symlink in lib/ nor the possibility that there is still a spec file in specs.
            for suffix in ['_spec', '-spec', '-comp']:
                name = self.name + suffix + '.xml'
                path = self.path.parent.joinpath('lib', name)
                if path.is_symlink():  path.unlink()
                path = self.path.parent.joinpath('specs', name)
                if path.exists(): path.unlink()
        return True

class Protocol(Component):
    """
    Any OpenCPI Protocol.
    """
    def __init__(self, directory, name=None, **kwargs):
        self.asset_type = 'protocol'
        super().__init__(directory, name, **kwargs)

    @classmethod
    def is_component_prot_file(cls, file):
        """
        Determines if a provided xml file contains a component spec.

        TODO do we actually want to open files to make sure and not just rely on the naming
             convention???
        """
        return file.endswith(("_prot.xml", "-prot.xml"))

    @staticmethod
    def get_filename(directory, name, project, ensure_exists=True):
        """Gets the appropriate file name of a protocol asset"""
        if ensure_exists:
            end_list = ["", ".xml", "_prot.xml", "-prot.xml"]
            for ending in end_list:
                path = Path(directory, name+ending)
                if path.exists():
                    return str(path)
                elif project:
                    project_path = Path(ocpiutil.get_path_to_project_top())
                    path = Path(project_path, name+ending)
                    if path.exists():
                        return str(path)
            err_msg = 'Unable to find protocol "{}" in directory {}'.format(
                name, directory)
            raise ocpiutil.OCPIException(err_msg)

        path = Path(directory, name)
        path_stem = path.stem
        if not re.search('_prot$|-prot$', path_stem):
            path_stem += '-prot'
        path_stem += '.xml'
        path = Path(directory, path_stem)
        return str(path)

    @staticmethod
    def _get_template_dict(name, directory, **kwargs):
        """
        used by the create function/verb to generate the dictionary of viabales to send to the
        jinja2 template.
        valid kwargs handled at this level are:
            protocol           (string)      - Protocol name
            hdl_lib            (string)      - HDL library name
        """
        protname = name.split("-")[0] if name.find("-") else name
        template_dict = {
                        "protocol" : protname,
                        "hdl_lib" : kwargs.get("hdl_library", None)
                        }
        return template_dict

    @staticmethod
    def create(name, directory, **kwargs):
        """
        Static method to create a new Protocol
        """
        path, name, parent_path = Asset.start_creation(directory, name, 'protocol', kwargs)
        Asset.create_file_asset("protocol", "prot", directory, name,
                                ocpitemplate.PROTOCOL_SPEC_XML,
                                __class__._get_template_dict,
                                __class__._get_project_package_id(parent_path, **kwargs), kwargs)

class HdlSlot(Component):
    """
    Any OpenCPI HDL Slot
    """

    def __init__(self, directory, name=None, **kwargs):
        self.asset_type = 'hdl-slot'
        super().__init__(directory, name, **kwargs)

    @staticmethod
    def _get_template_dict(name, directory, **kwargs):
        """
        used by the create function/verb to generate the dictionary of viabales to send to the
        jinja2 template.
        valid kwargs handled at this level are:
            hdl_slot            (string)      - HDL slot name
        """
        slotname = name.split(".")[0] if name.find(".") else name
        template_dict = {
                        "hdl_slot" : slotname,
                        }
        return template_dict

    @staticmethod
    def create(name, directory, **kwargs):
        """
        Static method to create a new HDL slot
        """
        path, name, parent_path = Asset.start_creation(directory, name, 'HDL slot', kwargs)
        Asset.create_file_asset('slot', 'slot', directory, name, ocpitemplate.HDL_SLOT_XML,
                                __class__._get_template_dict,
                                __class__._get_project_package_id(parent_path, **kwargs),
                                kwargs)

class HdlCard(HdlSlot):
    """
    Any OpenCPI HDL Card
    """
    @staticmethod
    def _get_template_dict(name, directory, **kwargs):
        """
        used by the create function/verb to generate the dictionary of viabales to send to the
        jinja2 template.
        valid kwargs handled at this level are:
            hdl_card            (string)      - HDL card name
        """
        cardname = name.split(".")[0] if name.find(".") else name
        template_dict = {
                        "hdl_card" : cardname,
                        }
        return template_dict

    @staticmethod
    def create(name, directory, **kwargs):
        """
        Static method to create a new HDL card
        """
        path, name, parent_path = Asset.start_creation(directory, name, 'HDL card', kwargs)
        Asset.create_file_asset('card', 'card', directory, name, ocpitemplate.HDL_CARD_XML,
                                __class__._get_template_dict,
                                __class__._get_project_package_id(parent_path, **kwargs),
                                kwargs)

class ComponentsCollection(ShowableAsset):
    """
    Collection of components, which are spec files or comp directories
    """
    valid_settings = []
    def __init__(self, directory=None, name=None, assets=None, **kwargs):
        if assets != None:
            self.out_of_project = True
        self.asset_type = 'components'
        super().__init__(directory, name, **kwargs)
        self.components = []
        if assets != None:
            for parent,name,child_path in assets:
                self.components.append(Component(parent,
                                                 **{'name' : name,
                                                    'child_path' : child_path}))
    def show(self, format=None, **kwargs):
        """
        Show all the components in all the projects in the registry
        """
        if format == "simple":
            for comp in self.components:
                print(comp.name + " ", end="")
            print()
        elif format == "table":
            rows = [["Library Package ID", "Component Pathname", "Component"]]
            for comp in self.components:
                rows.append([comp.package_id, str(comp.directory),comp.name])
            ocpiutil.print_table(rows, underline="-")
        elif format == "json":
            dict={}
            for comp in self.components:
                dict.update({comp.name : { 'package_id' : comp.package_id,
                                           'directory' : comp.directory}})
            json.dump(dict, sys.stdout)
            print()
    # pylint:enable=unused-argument
