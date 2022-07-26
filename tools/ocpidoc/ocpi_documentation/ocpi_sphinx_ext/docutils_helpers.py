#!/usr/bin/env python3

# Helper functions for working with docutils
#
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
# A PARTICULAR PURPOSE. See the GNU Lesser General Public License for
# more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import sys
import pathlib
import docutils
import xml_tools

def rst_string_convert(state, rst_text):
    """ Convert Restructure Text string to docutils node representation

    Args:
        state (docutils.state instance): The docutils state instance for where
            this string text is to be converted.
        rst_text (str): Restructured Text to be converted.

    Returns:
        docutils.nodes.paragraph object of the converted text.
    """
    # Convert the ReStructured Text into docutils tree / representation, using
    # nested_parse(). Need to use StringList for nested_parse(). Second
    # argument which is zero here is the offset to use in the first argument,
    # here want all of the text so set to zero.
    docutils_paragraph = docutils.nodes.paragraph()
    state.nested_parse(docutils.statemachine.StringList(rst_text.split("\n")),
                       0,
                       docutils_paragraph)

    return docutils_paragraph


def list_item_name_code_value(name, value):
    """ Prepare a docutils list item with a "name: value" format

    Args:
        name (str): The name (first part of the list item text) to be included
            on the list item, in standard font and before a ":".
        value (str): The code formatted part of the list item text, to go after
            the ":".

    Returns:
        docutils item.
    """
    if name[-1] != " ":
        name = name + " "
    if name[-2] != ":":
        name = name[:-1] + ": "

    value = str(value)

    item = docutils.nodes.list_item()
    item_text = docutils.nodes.paragraph(text=name)

    # 'value' can be a large array, so limit the number of characters per line
    # by inserting a line break after the commas that occur before the
    # character limit
    character_limit = 80
    while True:
        value_limited = ""
        while value != "":
            comma_index = value.find(",")
            if comma_index == -1:
                comma_index = len(value) - 1
            new_line_length = len(value_limited) + comma_index + 1
            if value_limited == "" or new_line_length <= character_limit:
                value_limited += value[:comma_index + 1]
                value = value[comma_index + 1:]
            else:
                break
        item_text.append(docutils.nodes.literal(text=value_limited))
        if value != "":
            item_text.append(docutils.nodes.paragraph("\n"))
        else:
            item.append(item_text)
            break

    return item


def list_members(name, members):
    """ Prepare a docutils list item using a dictionary of members

    Args:
        name (str): The name (first part of the list item text) to be included
            on the list item, in standard font and before a ":".
        members (dir): a hierarchical dictionary of members.
    Returns:
        docutils item.
    """
    member_item = docutils.nodes.list_item()
    member_item.append(docutils.nodes.paragraph(text=name + ":"))
    member_details_list = docutils.nodes.bullet_list()
    for item, value in members.items():
        if value["type"]["data_type"] == "struct":
            member_details_list.append(
                list_members(item, value["type"]["members"]))
        else:
            member_item_title = docutils.nodes.list_item()
            member_item_title.append(docutils.nodes.paragraph(text=item + ":"))
            member_sub_item_list = docutils.nodes.bullet_list()
            for member_name, member_value in value["type"].items():
                member_sub_item_list.append(
                    list_item_name_code_value(member_name, member_value))
            member_item_title.append(member_sub_item_list)
            member_details_list.append(member_item_title)

    if len(member_details_list) > 0:
        member_item.append(member_details_list)

    return member_item

# If there was a base class for the directives that called this, then
# this would be a method with no arguments
def get_component_spec(source, reporter, line, component_spec_path = None):
    """ Get the component spec's dictionary based on where the source doc is

    Args:
        source (str): The pathname of the primary source document
        reporter (LoggingReporter): Class used to log
        line(int): The line in the primary source document
        component_spec_path (optional, str): The spec path given in the "component_spec" option, if present.
    Returns:
        the dictionary version of the component specification (XML) or None if there isn't one
    """
    source_dir = pathlib.Path(source).resolve().parent
    library_specs_dir = source_dir.joinpath("../specs")
    # The documentation for a component must be in the same project as its spec, and the spec is
    # either in the .comp directory, the ../specs directory or in the project's specs directory
    library_dir = source_dir.parent
    project_specs_dir = (library_dir.parent
                         if library_dir.name == 'components'
                         else library_dir.parent.parent).joinpath("specs")
    component_name = source_dir.stem
    if component_spec_path is not None:
        path = pathlib.Path(component_spec_path)
        if path.exists(): # might be symlink
            component_spec_path = path
        else:
            reporter.warning(
                ("Directive on this line cannot find the given component "
                 f"specification file: \"{component_spec_path}\". "
                 f"Will look for \"{component_name}[-comp|-spec|_spec].xml\" in either "
                 f"the component directory, \"{source_dir}\", the library's "
                 f"specs directory \"{library_specs_dir}\" or the project's "
                 f"specs directory \"{project_specs_dir}\"."),
                line=line)
            component_spec_path = None
    if component_spec_path is None:
        for dir in [ source_dir, library_specs_dir, project_specs_dir ]:
            for suffix in [ "-comp.xml", "-spec.xml", "_spec.xml" ]:
                path = dir.joinpath(component_name + suffix)
                if path.exists(): # might be symlink
                    component_spec_path = path
                    break
            if component_spec_path:
                break
    if component_spec_path:
        with xml_tools.parser.ComponentSpecParser(component_spec_path) as file_parser:
            return file_parser.get_dictionary()
    reporter.warning(
        ("Directive on this line cannot find the expected component specification file, "
         f"\"{component_name}[-spec|_spec|-comp].xml\" in either the component directory, "
         f"\"{source_dir}\", the library's specs directory \"{library_specs_dir}\" or "
         f"the project's specs directory \"{project_specs_dir}\"."),
        line=line)
    return None
