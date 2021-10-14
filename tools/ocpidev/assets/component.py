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
Definition of Componnet and ShowableComponent classes
"""

import os
import re
import sys
import subprocess
import logging
import json
import jinja2
import _opencpi.assets.template as ocpitemplate
from os.path import dirname
from pathlib import Path
from xml.etree import ElementTree as ET
import _opencpi.util as ocpiutil
from .abstract import ShowableAsset

class ShowableComponent(ShowableAsset):
    """
    Any OpenCPI Worker or Component.  Intended to hold all the common functionality of workers and
    components.  Expected to be a virtual class and no real objects will get created of this class
    even though nothing prevents it.
    """
    def __init__(self, directory, name=None, **kwargs):
        super().__init__(directory, name, **kwargs)
        # should be set in child classes
        self.ocpigen_xml = self.ocpigen_xml if self.ocpigen_xml else ""
        if kwargs.get("init_ocpigen_details", False):
            self.get_ocpigen_metadata(self.ocpigen_xml)
        package_id = kwargs.get("package_id", None)
        self.package_id = package_id if package_id else self.__init_package_id()

    def show(self, details, verbose, **kwargs):
        """
        Not implemented and not intended to be implemented
        """
        raise NotImplementedError("show() is not implemented")

    def get_ocpigen_metadata(self, xml_file):
        """
        Ask ocpigen (the code generator)  to parse the worker(OWD) or component(OCS) xml file and
        spit out an artifact xml that this function parses into class variables.
          property_list - list of every property, each property in this list will be a dictionary of
                          all the xml attributes associated with it from the artifact xml
          port_list     - list of every port each port in this list will be a dictionary of
                          all the xml attributes associated with it from the artifact xml some of
                          which are unused
          slave_list    - list of every slave worker's name expected to be blank for an OCS

        Function attributes:
          xml_file - the file to have ocpigen parse
        """
        #get list of locations to look for include xml files from make
        parent_dir = str(Path(self.directory))
        if ocpiutil.get_dirtype(parent_dir) not in ['library', 'project']:
            parent_dir = str(Path(parent_dir).parent)
        if ocpiutil.get_dirtype(parent_dir) == "library":
            xml_dirs = ocpiutil.set_vars_from_make(ocpiutil.get_makefile(parent_dir, "library"),
                                                   mk_arg="showincludes ShellLibraryVars=1",
                                                   verbose=True)["XmlIncludeDirsInternal"]
        elif ocpiutil.get_dirtype(parent_dir) == "project":
            xml_dirs = ocpiutil.set_vars_from_make(ocpiutil.get_makefile(parent_dir, "project"),
                                                   mk_arg="projectincludes ShellProjectVars=1",
                                                   verbose=True)["XmlIncludeDirsInternal"]
        #call ocpigen -G
        ocpigen_cmd = ["ocpigen", "-G", "-O", "none", "-V", "none", "-H", "none"]
        for inc_dir in xml_dirs:
            ocpigen_cmd.append("-I")
            ocpigen_cmd.append(inc_dir)
        ocpigen_cmd.append(os.path.basename(xml_file))
        ocpiutil.logging.debug("running ocpigen cmd: " + str(ocpigen_cmd))
        old_log_level = os.environ.get("OCPI_LOG_LEVEL", "0")
        os.environ["OCPI_LOG_LEVEL"] = "0"
        comp_xml = subprocess.Popen(ocpigen_cmd, stdout=subprocess.PIPE,cwd=self.directory).communicate()[0]
        os.environ["OCPI_LOG_LEVEL"] = old_log_level

        #put xml output file into an ElementTree object
        ocpiutil.logging.debug("Component Artifact XML from ocpigen: \n" + str(comp_xml))
        try:
            parsed_xml = ET.fromstring(comp_xml)
        except ET.ParseError:
            raise ocpiutil.OCPIException("Error with xml file from ocpigen.\n\nocpigen command: " +
                                         str(ocpigen_cmd) + "\n\nxml output: \n" + str(comp_xml))

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

    def __init_package_id(self):
        """
        Determine the Package id based on the library or project that the Worker resides in.  only
        a component will reside at the top level of a project.
        """
        dir = self.directory if os.path.isdir(self.directory) else dirname(self.directory)
        parent_dir = str(Path(dir).parent)
        dirtype = str(ocpiutil.get_dirtype(parent_dir))
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
                                         "parent directory: " + parent_dir + " dirtype: " + dirtype)
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

    def _show_ports_props(self, json_dict, details, verbose, is_worker):
        """
        Print out the ports and properties of a given component/worker given the dictionary that is
        passed in with this information in it

        Function attributes:
          json_dict  - the constructed dictionary to output the information for
          details    - the mode to print out the information in table or simple are the only valid
                       options
          verbose    - integer for verbosity level 0 is default and lowest and anything above 1
                       shows struct internals and hidden properties
          is_ worker - switch for component vs worker is intended for limited use otherwise there
                       should be 2 separate functions rather then using this Boolean
        """
        if details == "simple":
            self.__show_simple_ports_props(json_dict)
        elif details == "table":
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

class Component(ShowableComponent):
    """
    Any OpenCPI Component.
    """
    def __init__(self, directory, name=None, **kwargs):
        if not name:
            name = str(Path(directory).name)
            directory = str(Path(directory).parent)
        name_stem = Path(name).stem
        self.ocpigen_xml = str(Path(directory, name_stem)) + '.xml'
        super().__init__(directory, name, **kwargs)

    @staticmethod
    def get_package_id(directory="."):
        """
        Determine the Package id based on the library or project that the Worker resides in.  only
        a component will reside at the top level of a project.
        """
        dir = directory if os.path.isdir(directory) else dirname(directory)
        parent_dir = str(Path(dir).parent)
        dirtype = str(ocpiutil.get_dirtype(parent_dir))
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
        elif dirtype == "libraries":
            raise ocpiutil.OCPIException("Specify a library or create a flattened 'components' directory.")
        else:
            raise ocpiutil.OCPIException("Could not determine Package-ID for " +
                                         "parent directory: " + parent_dir +
                                         " and directory type: " + dirtype)
        return ret_val

    @classmethod
    def is_component_spec_file(cls, file):
        """
        Determines if a provided xml file contains a component spec.

        TODO do we actually want to open files to make sure and not just rely on the naming
             convention???
        """
        return file.endswith(("_spec.xml", "-spec.xml"))

    def show(self, details, verbose, **kwargs):
        """
        Print out the ports and properties of a given component in the format that is provided by
        the caller

        Function attributes:
          details    - the mode to print out the information in table or simple are the only valid
                       options
          verbose    - integer for verbosity level 0 is default and lowest and anything above 1
                       shows struct internals and hidden properties
          kwargs     - no extra kwargs arguments expected
        """
        json_dict = self._get_show_dict(verbose)

        if details == "simple" or details == "table":
            print("Component: " + json_dict["name"] + " Package ID: " + json_dict["package_id"])
            print("Directory: " + json_dict["directory"])
            self._show_ports_props(json_dict, details, verbose, False)
        else:
            json.dump(json_dict, sys.stdout)
            print()

    def add_link(filename, directory="."):
        libdir = Path(directory, "lib")
        if not libdir.exists():
            os.mkdir(libdir)
        specdir = Path(directory, "specs")
        if not specdir.exists():
            os.mkdir(specdir)
        # Symlinks must have relative paths
        savepath = os.getcwd()
        os.chdir(directory)
        lnkfile = "lib/" + filename
        if not os.path.exists(lnkfile):
            specfile = "../specs/" + filename
            os.symlink(specfile, lnkfile)
        os.chdir(savepath)
        
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
    def get_working_dir(name, ensure_exists=True, **kwargs):
        cur_dirtype = ocpiutil.get_dirtype()
        valid_dirtypes = ["project", "libraries", "library", "hdl-platform"]
        verb = kwargs.get('verb', '')
        library = kwargs.get('library', '')
        hdl_library = kwargs.get('hdl_library', '')
        platform = kwargs.get('platform', '')
        project = kwargs.get('project', '')
        working_path = Path.cwd()
        if len(list(filter(None, [library, hdl_library, platform]))) > 1:
            ocpiutil.throw_invalid_libs_e()
        if cur_dirtype not in valid_dirtypes:
            ocpiutil.throw_not_valid_dirtype_e(valid_dirtypes)
        if not name:
            ocpiutil.throw_not_blank_e("component", "name", True)
        project_path = Path(ocpiutil.get_path_to_project_top())
        if library:
            if not library == 'components':
                working_path = Path(project_path, 'components', library)
            else:
                working_path = Path(project_path, library)
            if not working_path.exists():
                print("Error: Library '" + library + "' does not exist")
                exit(1)
        elif hdl_library:
            working_path = Path(project_path, 'hdl', hdl_library)
        elif platform:
            working_path = Path(project_path, 'hdl', 'platforms', platform, 'devices')
        elif project:
            working_path = project_path
        elif cur_dirtype == "hdl-platform":
            working_path = Path(working_path, 'devices')
        elif cur_dirtype == 'libraries':
            if ocpiutil.get_dirtype("components") == "libraries":
                ocpiutil.throw_specify_lib_e()
            working_path = Path(working_path, 'components')
        # Legacy: ocipidev defaults to 'components' without the -p option
        elif cur_dirtype == 'project' and verb in ["create","delete"]:
            working_path = Path(project_path, 'components')
            if not working_path.exists():
                print("OCPI:ERROR: The 'components' library does not exist")
                exit(1)
 
        specs_path = Path(working_path, 'specs')
        if not specs_path.exists() and not ensure_exists:
            os.makedirs(str(specs_path))
        working_dir = Component.get_filename(
            str(specs_path), name, project, ensure_exists)
        return working_dir

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

    def _get_template_dict(name, directory, **kwargs):
        """
        used by the create function/verb to generate the dictionary of viabales to send to the
        jinja2 template.
        valid kwargs handled at this level are:
            comp            (string)      - Component name
        """
        compname = name.split("-")[0] if name.find("-") else name
        template_dict = {
                        "component" : compname,
                        "hdl_lib" : kwargs.get("hdl_library", None)
                        }
        return template_dict

    @staticmethod
    def create(name, directory, **kwargs):
        """
        Static method to create a new Component, aka spec
        """
        verbose = kwargs.get("verbose", True)
        sub_lib = kwargs.get("library", None)
        hdl_lib = kwargs.get("hdl_library", None)
        proj = kwargs.get("project", True)
        dirtype = ocpiutil.get_dirtype(directory)
        pkg_id = Component.get_package_id(directory)
        logging.debug("Package_ID: " + pkg_id)
        if not (proj or dirtype == "project"):
            parent_dir = str(Path(directory).parent)
            workers = str(Component.get_workers(parent_dir))[1:-1] + "\n"
            logging.debug("Workers: " + workers)

        template_dict = Component._get_template_dict(name, directory, **kwargs)
        if not os.path.exists(directory):
            os.mkdir(directory)
        if hdl_lib:
            os.chdir("hdl/" + hdl_lib)
            hdlfile = os.getcwd() + "/" + hdl_lib + ".xml"
            template = jinja2.Template(ocpitemplate.COMPONENT_HDL_LIB_XML, trim_blocks=True)
            ocpiutil.write_file_from_string(hdlfile, template.render(**template_dict))
        os.chdir(directory)
        specfile = os.getcwd() + "/" + name
        if os.path.isfile(specfile):
            raise ocpiutil.OCPIException(specfile + " already exists")
        if kwargs.get("no_control", None) == True:
            template = jinja2.Template(ocpitemplate.COMPONENT_SPEC_NO_CTRL_XML, trim_blocks=True)
            ocpiutil.write_file_from_string(specfile, template.render(**template_dict))
        else:
            template = jinja2.Template(ocpitemplate.COMPONENT_SPEC_XML, trim_blocks=True)
            ocpiutil.write_file_from_string(specfile, template.render(**template_dict))

        if (proj or dirtype == "project"):
            if not os.path.isfile("package-id"):
                ocpiutil.write_file_from_string("package-id", pkg_id + "\n")
        else:
            Component.add_link(name, str(Path(directory).parent))
            workers = str(Component.get_workers(parent_dir))[1:-1]
            logging.debug("Workers: " + workers)
        if verbose:
            print("Component '" + name + "' was created at " + specfile)


class Protocol(Component):
    """
    Any OpenCPI Protocol.
    """
    @classmethod
    def is_component_prot_file(cls, file):
        """
        Determines if a provided xml file contains a component spec.

        TODO do we actually want to open files to make sure and not just rely on the naming
             convention???
        """
        return file.endswith(("_prot.xml", "-prot.xml"))

    @staticmethod
    def get_working_dir(name, ensure_exists=True, **kwargs):
        cur_dirtype = ocpiutil.get_dirtype()
        valid_dirtypes = ["project", "libraries", "library", "hdl-platform"]
        library = kwargs.get('library', '')
        hdl_library = kwargs.get('hdl_library', '')
        platform = kwargs.get('platform', '')
        project = kwargs.get('project', '')
        working_path = Path.cwd()
        if len(list(filter(None, [library, hdl_library, platform]))) > 1:
            ocpiutil.throw_invalid_libs_e()
        if cur_dirtype not in valid_dirtypes:
            ocpiutil.throw_not_valid_dirtype_e(valid_dirtypes)
        if not name:
            ocpiutil.throw_not_blank_e("component", "name", True)
        project_path = Path(ocpiutil.get_path_to_project_top())
        if library:
            if not library == 'components':
                working_path = Path(project_path, 'components', library)
            else:
                working_path = Path(project_path, library)
        elif hdl_library:
            working_path = Path(project_path, 'hdl', hdl_library)
        elif platform:
            working_path = Path(
                project_path, 'hdl', 'platforms', platform, 'devices')
        elif project:
            working_path = project_path
        elif cur_dirtype == "hdl-platform":
            working_path = Path(working_path, 'devices')
        elif cur_dirtype == 'libraries':
            if ocpiutil.get_dirtype("components") == "libraries":
                ocpiutil.throw_specify_lib_e()
            working_path = Path(working_path, 'components')
        elif cur_dirtype == 'project':
            working_path = Path(project_path, 'components')
            if not working_path.exists():
                print("OCPI:ERROR: The 'components' library does not exist")
                exit(1)
        
        specs_path = Path(working_path, 'specs')
        if not specs_path.exists() and not ensure_exists:
            os.makedirs(specs_path)
        working_dir = Protocol.get_filename(
            str(specs_path), name, project, ensure_exists)
        return working_dir

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
        verbose = kwargs.get("verbose", True)
        sub_lib = kwargs.get("library", None)
        hdl_lib = kwargs.get("hdl_library", None)
        proj = kwargs.get("project", True)
        dirtype = ocpiutil.get_dirtype(directory + "/..")
        pkg_id = Component.get_package_id(directory)
        logging.debug("Package_ID: " + pkg_id)
        if not (proj or dirtype == "project"):
            parent_dir = str(Path(directory).parent)
            workers = str(Component.get_workers(parent_dir))[1:-1] + "\n"
            logging.debug("Workers: " + workers)

        template_dict = Protocol._get_template_dict(name, directory, **kwargs)
        if not os.path.exists(directory):
            os.mkdir(directory)
        if hdl_lib:
            os.chdir("hdl/" + hdl_lib)
            hdlfile = os.getcwd() + "/" + hdl_lib + ".xml"
            template = jinja2.Template(ocpitemplate.COMPONENT_HDL_LIB_XML, trim_blocks=True)
            ocpiutil.write_file_from_string(hdlfile, template.render(**template_dict))
        os.chdir(directory)
        protfile = os.getcwd() + "/" + name
        if os.path.isfile(protfile):
            raise ocpiutil.OCPIException(protfile + " already exists")
        template = jinja2.Template(ocpitemplate.PROTOCOL_SPEC_XML, trim_blocks=True)
        ocpiutil.write_file_from_string(protfile, template.render(**template_dict))
        if (proj or dirtype == "project"):
            if not os.path.isfile("package-id"):
                ocpiutil.write_file_from_string("package-id", pkg_id + "\n")
        else:
            Component.add_link(name, str(Path(directory).parent))
            workers = str(Component.get_workers(parent_dir))[1:-1] + "\n"
            logging.debug("Workers: " + workers)
        if verbose:
            print("Protocol '" + name + "' was created at " + protfile)


class Slot(Component):
    """
    Any OpenCPI HDL Slot
    """
    @staticmethod
    def get_working_dir(name, ensure_exists=True, **kwargs):
        cur_dirtype = ocpiutil.get_dirtype()
        valid_dirtypes = [ "project", "library" ]
        if cur_dirtype not in valid_dirtypes:
            ocpiutil.throw_not_valid_dirtype_e(valid_dirtypes)
        project_path = Path(ocpiutil.get_path_to_project_top())
        working_path = Path(project_path, 'hdl', 'cards', 'specs')
        if not working_path.exists():
            os.makedirs(str(working_path))
        working_path = Path(working_path, name + '.xml')
        return working_path

    def gen_cards_xml(template_dict, libdir="."):
        libfile = str(Path(libdir, "cards.xml"))
        if not os.path.isfile(libfile):
            template = jinja2.Template(ocpitemplate.HDL_CARDS_XML, trim_blocks=True)
            ocpiutil.write_file_from_string(libfile, template.render(**template_dict))

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
        slotfile = str(Path(directory, name))
        if os.path.isfile(slotfile):
            raise ocpiutil.OCPIException(slotfile + " already exists")

        template_dict = Slot._get_template_dict(name, directory, **kwargs)
        verbose = kwargs.get("verbose", True)
        dirtype = ocpiutil.get_dirtype(directory + "/..")
        parent_dir = str(Path(directory).parent)
        Slot.gen_cards_xml(template_dict, parent_dir)
        pkg_id = Component.get_package_id(directory)
        workers = str(Component.get_workers(parent_dir))[1:-1] + "\n"
        logging.debug("Workers: " + workers + "Package_ID: " + pkg_id)
        template = jinja2.Template(ocpitemplate.HDL_SLOT_XML, trim_blocks=True)
        ocpiutil.write_file_from_string(slotfile, template.render(**template_dict))
        Component.add_link(name, parent_dir)
        if verbose:
            print("HDL slot '" + name + "' was created at " + slotfile)

class Card(Slot):
    """
    Any OpenCPI HDL Card
    """
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
        cardfile = str(Path(directory, name))
        if os.path.isfile(cardfile):
            raise ocpiutil.OCPIException(cardfile + " already exists")

        template_dict = Card._get_template_dict(name, directory, **kwargs)
        verbose = kwargs.get("verbose", True)
        dirtype = ocpiutil.get_dirtype(directory + "/..")
        parent_dir = str(Path(directory).parent)
        Slot.gen_cards_xml(template_dict, parent_dir)
        pkg_id = Component.get_package_id(directory)
        workers = str(Component.get_workers(parent_dir))[1:-1] + "\n"
        logging.debug("Workers: " + workers + "Package_ID: " + pkg_id)
        template = jinja2.Template(ocpitemplate.HDL_CARD_XML, trim_blocks=True)
        ocpiutil.write_file_from_string(cardfile, template.render(**template_dict))
        Component.add_link(name, parent_dir)
        if verbose:
            print("HDL card '" + name + "' was created at " + cardfile)
