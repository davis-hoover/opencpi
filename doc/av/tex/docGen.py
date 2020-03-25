#!/usr/bin/env python3.4
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

# TODO / FIXME: Handle xinclude properly

from argparse import ArgumentParser
import os
import itertools
import re
import shutil
import sys
import textwrap
from xml.etree import ElementTree as etree
from enum import Enum
import collections

try:
    import jinja2
    from jinja2 import Template
except ImportError:
    print("ERROR : Could not import jinja2; try 'sudo yum install python34-jinja2'",
          file=sys.stderr)
    sys.exit(1)

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../../../tools/cdk/python/')
import _opencpi.util  as ocpi
# Set OCPI_LOG_LEVEL to a desired number to see warnings or debug statements

# User setup:
USE_SECTION_NUMBERS = False
NEWLINE_PER_TABLE_CELL = False

# End of user-configurable data (if you change these, some code or string constants need fixes)
SECTION_HEADER = r"\section"+(('*', '')[USE_SECTION_NUMBERS])+"{{{}}}\n"
mywrapper = textwrap.TextWrapper(width=shutil.get_terminal_size()[0])

# http://eosrei.net/articles/2015/11/latex-templates-python-and-jinja2-generate-pdfs
LATEX_JINJA_ENV = jinja2.Environment(
    block_start_string=r'\BLOCK{',
    block_end_string='}',
    variable_start_string=r'\VAR{',
    variable_end_string='}',
    comment_start_string=r'\#{',
    comment_end_string='}',
    line_statement_prefix='%%',
    line_comment_prefix='%#',
    trim_blocks=True,
    autoescape=False,
    loader=jinja2.FileSystemLoader(os.path.dirname(os.path.realpath(__file__))+"/snippets/jinja2/")
)


def scramble_case(val):
    """ Scrambles all permutations of a string's case
    >>> scramble_case('ab')
    ['AB', 'Ab', 'aB', 'ab']
    >>> scramble_case('ab3')
    ['AB3', 'Ab3', 'aB3', 'ab3']
    """
    # https://stackoverflow.com/a/11144539/836748
    # Want unique, otherwise numbers make repeats because lower = upper
    temp_set = set(map(''.join, itertools.product(*list(zip(val.upper(), val.lower())))))
    temp_list = list(temp_set)
    temp_list.sort()
    return temp_list


def get_xml_attrs_as_list(xml_root, keys):
    """ Extracts XML attributes based on given keys in any case """
    ret = []
    for key in [scramble_case(k) for k in keys]:
        for i in key:
            for attr in xml_root.iter():
                if attr.tag == i:
                    ret.append(attr)
    return ret


def get_anycase(attrs, key):
    """ Helper function to call attrs.get() based on given keys in any case permutation.
        Calls "items" on attrs because lxml element does not act as a pythonic list
        (it doesn't support "in")
    """
    attr_keys = [v[0] for v in list(attrs.items())]
    valid_keys = [k for k in scramble_case(key) if k in attr_keys]
    if valid_keys:
        assert len(valid_keys) == 1  # There should never be more than one permutation
        return attrs.get(valid_keys[0])
    return None


def get_dict_from_attrs(attrs, keys):
    """ Creates dict based on given keys in any case permutation
    >>> test = {'key1': 'A', 'key2': 'B', 'KeY3': 'C'}
    >>> get_dict_from_attrs(test, ['KEY3']) ==  {'KEY3': 'C'}
    True
    >>> get_dict_from_attrs(test, ['kEy1', 'KEY3']) == {'KEY3': 'C', 'kEy1': 'A'}
    True
    >>> get_dict_from_attrs(test, [])
    {}
    >>> get_dict_from_attrs(test, ['Nope'])
    {'Nope': None}

    """
    return {key: get_anycase(attrs, key) for key in keys}


def name_from_path(ocs_file_path):
    """ Computes base component name from full path
    >>> name_from_path('../../specs/fifo-spec.xml')
    'fifo'
    >>> name_from_path('../../fifo.hdl/fifo.xml')
    'fifo'
    >>> name_from_path('fifo-spec.xml')
    'fifo'
    >>> name_from_path('fifo.xml')
    'fifo'
    """
    file_name = os.path.split(ocs_file_path)[-1]  # Last element of path
    file_basename = os.path.splitext(file_name)[0]
    return re.sub('[_-]spec', '', file_basename)  # Strip off -spec or _spec


def latexify(string):
    """ Escapes TeX-reserved characters
    >>> latexify("this is a test")
    'this is a test'
    >>> latexify("this is a test & so was this") == r"this is a test \& so was this"
    True
    >>> latexify("this_is_a_test") == r"this\_is\_a\_test"
    True
    >>> latexify("Please don't % comment ^^this^^ out") == r"Please don't \% comment \^{}\^{}this\^{}\^{} out"
    True
    """
    string = string.replace('_', r'\_')
    string = string.replace('&', r'\&')
    string = string.replace('%', r'\%')
    string = string.replace('^', r'\^{}')
    return string


class Attribute(object):
    """ Provides methods useful for XML attributes like ports or properties """
    def get_bool_val(self, attr_val):
        ret = (attr_val or "false") in scramble_case("true")
        ret = ret or ((attr_val or "0") == "1")
        return ret

    def get_latex_table_row_list(self):
        return ([latexify("a"), latexify("b")])

    def as_latex_table_row(self):
        """ This will generate a table row based on list given to it """
        my_list = self.get_latex_table_row_list()
        return r"""\hline
{}\\
""".format(" &{}".format((' ', '\n')[NEWLINE_PER_TABLE_CELL]).join(my_list))  # Note: The \n gives line per cell vs row


class Property(Attribute):
    """ Property class that self-generates from XML attributes dict """
    # TODO: Use the Property class from ocpidev stuff?
    # NOTE: not using _name because pylint barfs w/ PropertyLatexTableRow
    def __init__(self, xml):
        my_dict = self.get_dict_from_attrs(xml)
        self.name = my_dict["Name"]
        self.ptype = my_dict["Type"].lower().capitalize() or "Ulong"
        self.sequence_length = my_dict["SequenceLength"]
        if my_dict["ArrayDimensions"] is None:
            self.array_dimensions = my_dict["ArrayDimensions"]
        else:
            try:
                self.array_dimensions = int(my_dict["ArrayDimensions"])
            except:
                self.array_dimensions = my_dict["ArrayDimensions"]
        self.volatile = self.get_bool_val(my_dict["Volatile"])
        self.readable = self.get_bool_val(my_dict["Readable"])
        self.readback = self.get_bool_val(my_dict["Readback"])
        self.writable = self.get_bool_val(my_dict["Writable"])
        self.initial = self.get_bool_val(my_dict["Initial"])
        self.parameter = self.get_bool_val(my_dict["Parameter"])
        self.enums = my_dict["Enums"]
        self.default = None
        if self.array_dimensions is None:
            self.default = my_dict["Default"]
            if (self.ptype == "Bool") and self.default:
                self.default = self.get_bool_val(self.default)
        else:
            if self.ptype == "Bool":
                defaults = None
                try:
                    tmp = int(my_dict["Default"], 0)
                    defaults = [str(int(digit)) for digit in bin(tmp)[2:]]
                except ValueError as err:
                    defaults = my_dict["Default"].split(",")
                self.default = []
                for ii in range(len(defaults)):
                    self.default.append(self.get_bool_val(defaults[ii]))
            else:
                self.default = []
                defaults = my_dict["Default"].split(",")
                for ii in range(len(defaults)):
                    self.default.append(defaults[ii])
        self.readsync = self.get_bool_val(my_dict["ReadSync"])
        self.writesync = self.get_bool_val(my_dict["WriteSync"])
        self.description = my_dict["Description"] or ''

    def get_dict_from_attrs(self, attrs):
        """ Creates dict based on a property's attributes """
        keys = ["Name", "Type", "SequenceLength",
                "Volatile", "Readable", "Readback", "Writable",
                "Initial", "Parameter", "Enums", "Default", "ReadSync", "WriteSync",
                "Description", "ArrayDimensions", "Value"]
        ret = get_dict_from_attrs(attrs, keys)

        # Check for ArrayLength as a fallback if ArrayDimensions missing
        if not ret["ArrayDimensions"]:
            ret["ArrayDimensions"] = get_anycase(attrs, "ArrayLength")

        # Enforce defaults
        if not ret["Type"]:
            ret["Type"] = "ulong"
        if not ret["Default"]:
            ret["Default"] = ret["Value"]
            if not ret["Value"]:
                if (ret["Initial"] or ret["Writable"] or ret["Parameter"]):
                    ret["Default"] = 0

        return ret

    def get_latex_table_row_list(self):
        accessibility_str = []
        if self.volatile:
            accessibility_str.append("Volatile")
        if self.readable:
            accessibility_str.append("Readable")
        if self.readback:
            accessibility_str.append("Readback")
        if self.writable:
            accessibility_str.append("Writable")
        if self.initial:
            accessibility_str.append("Initial")
        if self.parameter:
            accessibility_str.append("Parameter")
        if self.readsync:
            accessibility_str.append("ReadSync")
        if self.writesync:
            accessibility_str.append("WriteSync")
        accessibility_str = ", ".join(accessibility_str)
        if self.default is None:
            default_str = "-"
        default = self.default
        if self.ptype == "Bool":
            default = str(default).lower().capitalize()
        return [
            latexify(str(self.name)),
            latexify(str(self.ptype).lower().capitalize()),
            latexify(str(self.sequence_length or '-')),
            latexify(str(self.array_dimensions or '-')),
            latexify(accessibility_str),
            latexify(str(self.enums or "Standard")).replace(",", ", "),
            latexify("-" if (self.default is None) else str(self.default)),
            latexify(str(self.description or '-'))
        ]


class Port(Attribute):
    def __init__(self, port_xml_root):
        my_dict = get_dict_from_attrs(port_xml_root,
                  ["Name", "Producer", "Protocol", "Optional"])
        self.name = my_dict["Name"]
        self.producer = my_dict["Producer"] or False
        self.protocol = my_dict["Protocol"]
        self.optional = self.get_bool_val(my_dict["Optional"]) or False

    def get_latex_table_row_list(self):
        return [latexify(str(self.name)),
            latexify(str(self.producer).lower().capitalize()),
            latexify(str(self.protocol or '(none)')),
            latexify(str(self.optional).lower().capitalize())
        ]


class Component():
    def __init__(self, ocs_xml_root, name):
        self.name = name
        # OrderedDict used so that order or original XML is preserved
        self.properties = collections.OrderedDict()
        self.ports = collections.OrderedDict()
        for root in get_xml_attrs_as_list(ocs_xml_root, ["Property"]):
            prop = Property(root)
            self.properties[prop.name] = prop
        for root in get_xml_attrs_as_list(ocs_xml_root,
                                          ["DataInterfaceSpec", "Port"]):
            port = Port(root)
            self.ports[port.name] = port


class SpecProperty(Property):
    def __init__(self, xml, ocs_prop):
        my_dict = self.get_dict_from_attrs(xml)
        self.name = ocs_prop.name 
        self.ptype = ocs_prop.ptype
        self.sequence_length = my_dict["SequenceLength"] or ocs_prop.sequence_length
        self.array_dimensions = my_dict["ArrayDimensions"] or ocs_prop.array_dimensions
        self.volatile = my_dict["Volatile"] or ocs_prop.volatile
        self.readable = my_dict["Readable"] or ocs_prop.readable
        self.readback = my_dict["Readback"] or ocs_prop.readback
        self.writable = my_dict["Writable"] or ocs_prop.writable
        self.initial = my_dict["Initial"] or ocs_prop.initial
        self.parameter = my_dict["Parameter"] or ocs_prop.parameter
        self.enums = my_dict["Enums"] or ocs_prop.enums
        self.default = my_dict["Default"] or ocs_prop.default
        self.readsync = my_dict["ReadSync"] or ocs_prop.readsync
        self.writesync = my_dict["WriteSync"] or ocs_prop.writesync
        self.description = my_dict["Description"] or ocs_prop.description


class Worker(Component):
    def __init__(self, ocs_xml_root, owd_xml_root, comp_name, name, authoring_model):
        Component.__init__(self, ocs_xml_root, comp_name)
        self.component_name = comp_name # important distinction
        self.name = name # important distinction
        self.authoring_model = authoring_model
        for root in get_xml_attrs_as_list(owd_xml_root, ["SpecProperty"]):
            prop_name = get_dict_from_attrs(root, ["Name"])["Name"]
            spec_prop = SpecProperty(root, self.properties[prop_name])
            self.properties[spec_prop.name] = spec_prop
        for root in get_xml_attrs_as_list(owd_xml_root, ["Property"]):
            prop = Property(root)
            self.properties[prop.name] = prop


class RCCWorker(Worker):
    def __init__(self, ocs_xml, owd_xml, component_name, name):
        Worker.__init__(self, ocs_xml, owd_xml, component_name, name,
                        authoring_model="rcc")


class HDLWorker(Worker):
    class StreamInterface(Port):
        def __init__(self, worker, port_xml_root, stream_ifc_xml_root=None):
            """ The default value of stream_ifc_xml_root is None because not all
                OCS ports will have StreamInterface elements in an OWD. """
            self.data_width = worker.data_width
            Port.__init__(self, port_xml_root)
            if stream_ifc_xml_root is None:
                self.clock = None
                self.clock_direction = "-"
                self.worker_eof = False
                self.insert_eom = False
            else:
                attrs = ["Name", "Clock", "ClockDirection", "WorkerEOF",
                         "InsertEOM", "DataWidth"]
                my_dict = None
                my_dict = get_dict_from_attrs(stream_ifc_xml_root, attrs)
                self.data_width = self.data_width or (my_dict["DataWidth"] or \
                    "(see HDL doc for instructions on calculating default value)")
                self.clock = my_dict["Clock"] or ("(control clock)" if \
                             my_dict["ClockDirection"] is None else None)
                self.clock_direction = my_dict["ClockDirection"] or "-"
                if worker.version == 2:
                    self.worker_eof = self.get_bool_val(my_dict["WorkerEOF"])
                    self.insert_eom = self.get_bool_val(my_dict["InsertEOM"])
                else:
                    self.worker_eof = False
                    self.insert_eom = False

        def get_latex_table_row_list(self):
            ret = [latexify("StreamInterface")]
            ret += Port.get_latex_table_row_list(self)
            ret += [
                latexify(str(self.data_width)),
                latexify(self.clock or "-"),
                latexify(self.clock_direction),
                latexify(str(self.worker_eof).lower().capitalize()),
                latexify(str(self.insert_eom).lower().capitalize())
            ]
            return ret

    def __init__(self, ocs_xml_root, owd_xml_root, comp_name, name):
        Worker.__init__(self, ocs_xml_root, owd_xml_root, comp_name, name,
                        authoring_model="hdl")
        my_dict = get_dict_from_attrs(owd_xml_root, ["DataWidth", "Version"])
        self.data_width = my_dict["DataWidth"]
        self.version = int(my_dict["Version"] or 1)
        # OrderedDict used so that order or original XML is preserved
        self.stream_interfaces = collections.OrderedDict()
        for port_xml_root in get_xml_attrs_as_list(ocs_xml_root,
                                          ["DataInterfaceSpec", "Port"]):
            ocs_port_has_matching_owd_stream_interface = False
            for stream_ifc_xml_root in get_xml_attrs_as_list(
                    owd_xml_root, ["StreamInterface"]):
                if get_dict_from_attrs(port_xml_root, ["Name"]) == \
                        get_dict_from_attrs(stream_ifc_xml_root, ["Name"]):
                    interface = self.StreamInterface(self, port_xml_root,
                                                     stream_ifc_xml_root)
                    self.stream_interfaces[interface.name] = interface
                    ocs_port_has_matching_owd_stream_interface = True
                    break
            if not ocs_port_has_matching_owd_stream_interface:
                # port still needs to be added
                interface = self.StreamInterface(self, port_xml_root)
                self.stream_interfaces[interface.name] = interface


def normalize_file_name(filename):
    """ This function will normalize a filename by returning a matching
    file if it already exists, e.g. (if the latter already exists)
    iqstream_max_calculator.tex => IQStream_Max_Calculator.tex
    * The function name implies more may be done later (e.g. Title Case) """
    files = [f for f in os.listdir('.') if f.lower() == filename.lower()]
    if files:
        return files[0]
    return filename


def emit_latex_header(out_file, user_edits, copyright):
    """ Writes standardized LaTeX header indicating if user is expected to edit file """
    edit_str = "this file is intended to be edited" if user_edits \
        else "editing this file is NOT recommended"
    out_file.write(
r"""%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% this file was generated by docGen.py
% {}
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
""".format(edit_str))
    if copyright:
        out_file.write(
            '\iffalse\n'
            'This file is protected by Copyright. Please refer to the COPYRIGHT file\n'
            'distributed with this source distribution.\n'
            '\n'
            'This file is part of OpenCPI <http://www.opencpi.org>\n'
            '\n'
            'OpenCPI is free software: you can redistribute it and/or modify it under the\n'
            'terms of the GNU Lesser General Public License as published by the Free Software\n'
            'Foundation, either version 3 of the License, or (at your option) any later\n'
            'version.\n'
            '\n'
            'OpenCPI is distributed in the hope that it will be useful, but WITHOUT ANY\n'
            'WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A\n'
            'PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.\n'
            '\n'
            'You should have received a copy of the GNU Lesser General Public License along\n'
            'with this program. If not, see <http://www.gnu.org/licenses/>.\n'
            '\\fi\n'
        )


def prompt_to_overwrite(filename, warn_existing=False):
    """ Will prompt use to ensure 'filename' shouldn't be overwritten.
        Will return True if the file should be overwritten.
        If "warn_existing" set, it will imply they should NOT answer yes.
        """
    if not os.path.isfile(filename):
        return True
    if warn_existing:
        msg = "exists and you PROBABLY DON'T want to rewrite it!"
        ocpi.logging.warning(filename + msg)
    msg = "WARN : file " + filename + " already exists, overwrite (y or n)? "
    res = ''
    while res not in ['y', 'n']:
        res = input(msg)
    return res == "y"


def emit_datasheet_tex_file(comp_name, copyright, prompt):
    """ Main routine that creates the LaTeX files after parsing the XML.
    """
    datasheet_filename = normalize_file_name(comp_name + ".tex")
    UC_NAME = (" ".join(re.split('[-_]', comp_name))).title()
    LC_NAME = latexify(comp_name)

    if not prompt and os.path.isfile(datasheet_filename):
            return
    if not prompt_to_overwrite(datasheet_filename, warn_existing=True):
        return
    print_info("emitting {0} (compile using rubber -d {0})".format(datasheet_filename))
    j_template = LATEX_JINJA_ENV.get_template("Component_Template.tex")
    with open(datasheet_filename, 'w') as datasheet_file:
        emit_latex_header(datasheet_file, user_edits=False, copyright=copyright)
        print(j_template.render(LC_NAME=LC_NAME, UC_NAME=UC_NAME), file=datasheet_file)
    return


def emit_property_table_inc_file(thing_with_props, filename, title_text, name,
                                 is_OCS, first_worker, copyright, prompt):
    j_template = LATEX_JINJA_ENV.get_template("Properties.tex")
    latex_rows = []
    if prompt:
        if not prompt_to_overwrite(filename):
            return
    for key in thing_with_props.properties:
        latex_rows.append(thing_with_props.properties[key].as_latex_table_row())
    with open(filename, 'w') as outfile:
        print_info("emitting {0}".format(filename))
        emit_latex_header(outfile, user_edits=False, copyright=copyright)
        print(j_template.render(title_text=title_text,
                                latex_rows=latex_rows,
                                is_OCS=is_OCS,
                                first_worker=first_worker,
                                comp_name=name,
                                sec_star=('*', '')[USE_SECTION_NUMBERS]
                               ), file=outfile)


def emit_ports_table_inc_file(thing_with_ports, filename, title_text, name,
                              is_OCS, is_HDL, first_worker, copyright, prompt):
    """ Main routine for port tables to a file """
    j_template = LATEX_JINJA_ENV.get_template("Ports.tex")
    latex_rows = []
    if prompt:
        if not prompt_to_overwrite(filename):
            return
    if is_HDL:
        for key in thing_with_ports.stream_interfaces:
            latex_rows.append(
                thing_with_ports.stream_interfaces[key].as_latex_table_row())
    else:
        for key in thing_with_ports.ports:
            latex_rows.append(thing_with_ports.ports[key].as_latex_table_row())
    with open(filename, 'w') as outfile:
        print_info("emitting {0}".format(filename))
        emit_latex_header(outfile, user_edits=False, copyright=copyright)
        print(j_template.render(title_text=title_text,
                                latex_rows=latex_rows,
                                is_OCS=is_OCS,
                                is_HDL=is_HDL,
                                first_worker=first_worker,
                                comp_name=name,
                                sec_star=('*', '')[USE_SECTION_NUMBERS]
                               ), file=outfile)


def emit_latex_inc_files(component, worker_dict, copyright, prompt):
    """ Creates the various .inc snippet files based on parsed data """
    emit_developer_doc_inc_file(copyright=copyright, prompt=prompt)
    emit_property_table_inc_file(component,
                                 filename="component_spec_properties.inc",
                                 title_text="Component Properties",
                                 name=component.name,
                                 is_OCS=True,
                                 first_worker=False,
                                 copyright=copyright, prompt=prompt)
    emit_ports_table_inc_file(component,
                              filename="component_ports.inc",
                              title_text="Component Ports",
                              name=component.name,
                              is_OCS=True, is_HDL=False,
                              first_worker=False,
                              copyright=copyright, prompt=prompt)
    with open('worker_properties.inc', 'w') as fprop:
        emit_latex_header(fprop, user_edits=False, copyright=copyright)
        with open('worker_interfaces.inc', 'w') as finterface:
            emit_latex_header(finterface, user_edits=False, copyright=copyright)
            first_worker = True
            if len(worker_dict) > 0:
                sec_star=('*', '')[USE_SECTION_NUMBERS]
                fprop.write("\n\section" + sec_star + "{Worker Properties}\n")
            for key in worker_dict:
                name = worker_dict[key].name + "." + worker_dict[key].authoring_model
                filename = name + '_properties.inc'
                fprop.write("\input{" + filename + "}\n")
                emit_property_table_inc_file(worker_dict[key],
                                             filename=filename,
                                             title_text="Worker Properties",
                                             name=latexify(name),
                                             is_OCS=False,
                                             first_worker=first_worker,
                                             copyright=copyright, prompt=prompt)
                first_worker = False
            first_worker = True
            if len(worker_dict) > 0:
                sec_star=('*', '')[USE_SECTION_NUMBERS]
                finterface.write("\n\section" + sec_star + "{Worker Interfaces}\n")
            for key in worker_dict:
                name = worker_dict[key].name + "." + worker_dict[key].authoring_model
                filename = name + '_interfaces.inc'
                finterface.write("\input{" + filename + "}\n")
                is_HDL = worker_dict[key].authoring_model == "hdl"
                emit_ports_table_inc_file(worker_dict[key],
                                          filename=filename,
                                          title_text="Worker Interfaces",
                                          name=latexify(name),
                                          is_OCS=False, is_HDL=is_HDL,
                                          first_worker=first_worker,
                                          copyright=copyright, prompt=prompt)
                first_worker = False
        fprop.close()
        finterface.close()


def emit_developer_doc_inc_file(copyright, prompt):
    """ Creates "main" developer doc that they probably DON'T want to edit """
    DEVELOPER_DOC_INC_FILENAME = 'developer_doc.inc'
    if not prompt and os.path.isfile(DEVELOPER_DOC_INC_FILENAME):
        return
    if not prompt_to_overwrite(DEVELOPER_DOC_INC_FILENAME, warn_existing=True):
        return
    print_info("emitting " + DEVELOPER_DOC_INC_FILENAME +
               "(developers should edit this)")
    j_template = LATEX_JINJA_ENV.get_template("Developer_Doc.tex")
    with open(DEVELOPER_DOC_INC_FILENAME, 'w') as out_file:
        emit_latex_header(out_file, user_edits=True, copyright=copyright)
        print(j_template.render(), file=out_file)


def input_file_contains_xi_include(filename):
    ret = False
    with open(filename, "r") as input_file:
        for line in input_file:
            for case in scramble_case("xi:include"):
                if case in line:
                    ret = True
                    break
    return ret


def throw_if_any_files_have_xi_include(files):
    for ff in files:
        if input_file_contains_xi_include(ff):
            raise Exception("File contains xi:include, which is not yet supported. Exiting now.")


def print_info(msg):
    print("INFO : ", msg)


def parse_files(ocs, owds):
    component = None
    worker_dict = {}
    ocs_xml_root = None
    tree = etree.parse(ocs)
    xml_root = tree.getroot()
    comp_name = name_from_path(ocs)
    for elem in scramble_case("ComponentSpec"):
        for xml in xml_root.iter(elem):
            component = Component(xml_root, comp_name)
            ocs_xml_root = xml_root
            break
    if component is None:
        raise Exception("file " + ocs + " could not be parsed")
    if owds is not None:
        for owd in owds:
            tree = etree.parse(owd)
            xml_root = tree.getroot()
            name = name_from_path(owd)
            worker = None
            for elem in scramble_case("RccWorker"):
                for root_iter in xml_root.iter(elem):
                    worker = RCCWorker(ocs_xml_root, root_iter, comp_name, name)
                    worker_dict[worker.name + "." + worker.authoring_model] = worker
            for elem in scramble_case("HdlWorker"):
                for root_iter in xml_root.iter(elem):
                    worker = HDLWorker(ocs_xml_root, root_iter, comp_name, name)
                    worker_dict[worker.name + "." + worker.authoring_model] = worker
            for elem in scramble_case("HdlDevice"):
                for root_iter in xml_root.iter(elem):
                    worker = HDLWorker(ocs_xml_root, root_iter, comp_name, name)
                    worker_dict[worker.name + "." + worker.authoring_model] = worker
            if worker is None:
                raise Exception("file " + owd + " could not be parsed")
    return [component, worker_dict]


def main():
    parser = ArgumentParser("Generates LaTeX source files suitable for "
             "compiling a component datasheet (including associated workers)")
    parser.add_argument('ocs', help='path to OCS file')
    parser.add_argument('-owd', action='append',
                        help='path to OWD file (can specify multiple)')
    parser.add_argument('-c', '--copyright', default=False, action='store_true',
                        help='insert copyright into LaTex files')
    parser.add_argument('-n', '--no-prompt', default=False, action='store_true',
                        help='will not prompt for overwrite of existing auto-generated files (no overwrite will occur)')
    args = parser.parse_args()

    throw_if_any_files_have_xi_include([args.ocs])
    if args.owd is not None:
        throw_if_any_files_have_xi_include(args.owd)
    [component, worker_dict] = parse_files(args.ocs, args.owd)
    emit_datasheet_tex_file(component.name, args.copyright,
                            prompt=not args.no_prompt)
    emit_latex_inc_files(component, worker_dict, args.copyright,
                         prompt=not args.no_prompt)


if __name__ == '__main__':
    main()
