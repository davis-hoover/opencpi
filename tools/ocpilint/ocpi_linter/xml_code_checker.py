#!/usr/bin/env python3

# Run code checks on XML files
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

"""Standard XML tests to run against ocpi projects."""

import pathlib
import subprocess
import re

from . import base_code_checker
from . import utilities
from lxml import etree as ElementTree


class XmlCodeCheckerDefaults(base_code_checker.BaseCodeCheckerDefaults):
    """Default settings for XmlCodeChecker class."""
    license_notice = (open(pathlib.Path(__file__).parent
                           .joinpath("license_notices").joinpath("xml.txt"), "r")
                      .read())
    maximum_line_length = 132
    comment_maximum_line_length = 132


class XmlCodeChecker(base_code_checker.BaseCodeChecker):
    """Formatter and checker for XML."""
    checker_settings = XmlCodeCheckerDefaults

    @staticmethod
    def get_supported_file_extensions():
        """Return a list of file extension this code checker supports.

        Returns:
            List of file extensions
        """
        return [".xml"]

    def test_xml_000(self):
        """Run XML lint on file.

        **Test name:** XML Lint

        XML lint is run with the options:

         * No net (do not search online for any entries)

         * No blanks

         * No compact

         * Format

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "XML lint"

        before_code = list(self._code)
        if not self._check_installed("xmllint"):
            issues = [{
                "line": None,
                "message": "XML lint not installed. Cannot run test."}]

            return test_name, issues

        # Handle comments to the right of elements by moving them to the
        # line beginning. This stops them being placed below the element
        # by xmllint after reformatting.
        # E.g. <a b="1"/> <!-- c --> => <!-- c --> <a b="1"/>
        reformat = []
        for line_text in self._code:
            comments = re.findall(r"<!--(.+?)-->", line_text)
            first_element = re.search(r"^\s*<(?!!--)(.+?)>", line_text)
            if comments and first_element:
                for comment in reversed(comments):
                    line_text = re.sub(
                        r"<!--(.+?)-->$", "", line_text).strip()
                    line_text = f"<!--{comment}-->{first_element.group()}"
            reformat.append(line_text + "\n")

        # Re-write file with changes
        with open(self.path, "w") as linted_file:
            linted_file.writelines(reformat)

        process = subprocess.Popen(["xmllint", "--nonet", "--noblanks",
                                    "--nocompact", "--format", self.path,
                                    "-o", self.path],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        process.wait()
        xml_lint_issues = process.communicate()[1].decode("utf-8").split(
            "\n")[0:-1]

        issues = []
        for issue in xml_lint_issues:
            if issue.count(":") > 3:
                line_number = int(issue.split(":")[1].strip())
                message = ":".join(issue.split(":")[2:]).strip()
                issues.append({"line": line_number, "message": message})

        # Get updated file format
        self._read_in_code()

        # Reformat code after xmllint has run since all tags now exist on
        # a single line which is not a human-readable format if they are
        # very long

        # Empty list to store our changes
        reformat = []
        element_indent = 0
        for line_text in self._code:
            max_line_length = self.checker_settings.maximum_line_length
            # Comments are not indented by xmllint so do this here based
            # on the previous element indent
            if re.search(r"^\s*<(?!!--).*$", line_text) is not None:
                element_indent = line_text.find("<")
            if line_text.find("<!--") == 0:
                line_text = " " * element_indent + line_text
            if len(line_text) > max_line_length:
                # Save line indentation amount
                indent = " " * line_text.find(line_text.split()[0])
                # Get content that starts with "<" and the following
                # character is not a "!"
                if re.search(r"^\s*<(?!!)", line_text):
                    # Get all attributes and values, and process them
                    # E.g. <a b="1" c="1"/>
                    #   => [ ["b", "'1'"], ["c", "'1'"] ]
                    pattern = r"\s+(\w+)\s*=\s*(\"[^\"]*\"|'[^']*')"
                    attributes = [list(val) for val in re.findall(
                        pattern, line_text)]
                    for attribute in attributes:
                        # Remove whitespace at beginning and end
                        # E.g. "'  3,4,5  '" => "'3,4,5'"
                        attribute[1] = (
                            attribute[1][0]  # First quote
                            + re.sub(r"^\s+|\s+$", "", attribute[1][1:-1])
                            + attribute[1][-1])  # End quote
                        # Remove excess whitespace
                        # E.g. "'3,   4,   5'" => "'3, 4, 5'"
                        attribute[1] = re.sub(r"\s+", " ", attribute[1])
                        # Remove space after comma (if not description)
                        # E.g. "'3, 4, 5'" => "'3,4,5'"
                        if attribute[0].lower() != "description":
                            attribute[1] = re.sub(r", ", ",", attribute[1])

                    # Break up attributes across multiple lines with the
                    # right indentation if the character limit is exceeded
                    # E.g. <a b="1" c="2", d="3,4,5">
                    #   => <a b="1" c="2",\n  d="3,4,5"/>
                    formatted_attrs = ""
                    index = len(indent) + len(line_text.split()[0])
                    for attr_name, attr_value in attributes:
                        calc_line_length = (index
                                            + len(attr_name)
                                            + len(attr_value) + 2)
                        index = calc_line_length
                        if calc_line_length > max_line_length:
                            formatted_attrs += "\n " + " " * len(indent)
                            index = (len("  " + " " * len(indent))
                                     + len(attr_name) + len(attr_value) + 1)
                        # Check for cases where even though an attribute is
                        # placed on its own line the character limit is
                        # still exceeded
                        if index > max_line_length:
                            # Character limit exceeded for a single
                            # attribute. Split it up.
                            def insert_newlines(text, limit):
                                result = ""
                                line = ""
                                pos = 0
                                while pos < len(text):
                                    # Only add \n after a comma or a space
                                    next_comma = text.find(",", pos)
                                    next_space = text.find(" ", pos)
                                    if next_comma == -1:
                                        next_comma = len(text) + 1
                                    if next_space == -1:
                                        next_space = len(text) + 1
                                    next_pos = min(next_comma, next_space)
                                    word = text[pos:next_pos+1]
                                    if len(line) + len(word) > limit:
                                        # Remove trailing whitespace
                                        if re.findall(r"\S", line):
                                            line = re.sub(
                                                r"\s+$", "", line)
                                            result += line + "\n"
                                            # Add an indent for every line
                                            # after the first
                                            line = "  "
                                    line += word
                                    pos = next_pos + 1
                                if re.findall(r"\S", line):
                                    result += line + "\n"
                                return result

                            # Format long attribute with new lines inserted
                            # and indentation applied
                            indent_extra = "  " + " " * len(indent)
                            attr_all = f"{attr_name}={attr_value}"
                            attr_all = insert_newlines(attr_all,
                                                       max_line_length - len(indent_extra))
                            newline_pos = ([match.start(0) for match in (
                                re.finditer(r"\n", attr_all))])
                            # Apply indent to attribute
                            if len(newline_pos) > 1:
                                attr_all = (attr_all[:newline_pos[0]] +
                                            attr_all[newline_pos[0]:-1].replace(
                                    "\n", "\n" + indent_extra))
                            # Append attribute
                            formatted_attrs += (f" {attr_all}")
                            # Remove trailing whitespace if any
                            formatted_attrs = re.sub(
                                r"\s+$", "", formatted_attrs)
                            # Update index
                            newline_pos = formatted_attrs.rfind("\n")
                            index = len(formatted_attrs[newline_pos:])
                        else:
                            # Append attribute
                            formatted_attrs += f" {attr_name}={attr_value}"
                    # Join the formatted start tag and attributes
                    if line_text.endswith("/>"):
                        end_tag = "/>"
                    else:
                        end_tag = ">"
                    line_text = (f"{indent}{line_text.split()[0]}"
                                 + f"{formatted_attrs}"
                                 + end_tag)

            reformat.append(line_text + "\n")

        # Ensure a single "\n" exists at the end
        while reformat[-1] is "\n":
            reformat = reformat[:-1]
        if not reformat[-1].endswith("\n"):
            reformat[-1] += "\n"

        # Re-write file with changes
        with open(self.path, "w") as linted_file:
            linted_file.writelines(reformat)
        # Read in changes to the file
        self._read_in_code()
        if (self._code != before_code):
            line_number = 0
            for i, (l1, l2) in enumerate(zip(before_code, self._code)):
                if l1 != l2:
                    line_number = i+1
                    break
            issues.append({"line": line_number,
                           "message": "File was reformatted by xmllint."})

        return test_name, issues

    def test_xml_001(self):
        """Check the first lines in file are in the correct format.

        **Test name:** Correct opening lines

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "Correct opening lines"

        issues = []

        if len(self._code) < self.minimum_number_of_lines:
            issues = [{"line": None,
                       "message": "File is not large enough to include license notice."}]
            return test_name, issues

        # License notice
        line_number = 1
        if (len(self._code) - line_number) < self.checker_settings.license_notice.count("\n"):
            issues.append({
                "line": None,
                "message": "File does not contain the expected license notice."})
            return test_name, issues

        for license_line in self.checker_settings.license_notice.splitlines():
            if self._code[line_number] != license_line:
                issues.append({
                    "line": line_number + 1,
                    "message": "License notice is incorrect, should be \""
                    + license_line + "\"."})
            line_number = line_number + 1

        return test_name, issues

    def test_xml_002(self):
        """Check only double quotation marks are used.

        **Test name:** Double quotation marks

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "Double quotation marks"

        issues = []

        # Single quotes in comments and attributes are allowed - so remove
        # comments and attribute content before checking
        reduced_content = self._remove_xml_comments(self._code)
        reduced_content = self._remove_xml_attribute_content(reduced_content)
        for line_number, line_text in enumerate(reduced_content):
            if "'" in line_text:
                issues.append({
                    "line": line_number + 1,
                    "message": "Single quotation marks should not be used, "
                               + "double quotation marks must be used."})

        return test_name, issues

    def test_xml_003(self):
        """Check comment lines do not exceed maximum length.

        **Test name:** Comments line length

        Lines which are commented out XML are allowed to exceed the limit
        to ensure the XML that has been commented out remains valid.

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "Comments line length"

        issues = []
        comment_line = False
        for line_number, line_text in enumerate(self._code):
            if "<!--" in line_text:
                comment_line = True
            if comment_line:
                max_length = self.checker_settings.comment_maximum_line_length
                if len(line_text) > max_length:
                    # Ensure not commented out code, which is allowed to be any length
                    test_if_xml = line_text.replace("<!--", "").replace(
                        "-->", "").strip()
                    if not (test_if_xml[0] == "<" and test_if_xml[-1] == ">"):
                        issues.append({
                            "line": line_number + 1,
                            "message": "Comment lines must not exceed length "
                                       + f"limit ({max_length} characters)."})
            if "-->" in line_text:
                comment_line = False

        return test_name, issues

    def test_xml_004(self):
        """Check all non-comment code is in lower case.

        **Test name:** Lower case text

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "Lower case text"

        issues = []
        within_description_tag = False
        within_description_attrib = False
        reduced_code = self._remove_xml_comments(self._code)
        for line_number, line_text in enumerate(reduced_code):
            # Do not check description. Do not import XML as XML tree as
            # want to keep track of the line numbers for reporting to the
            # user.
            if within_description_tag:
                # Within description tag - don't check tag content.
                check_text = ""
                # Look for the end tag.
                tag_end_location = line_text.find("</description>")
                if tag_end_location > 0:
                    within_description_tag = False
                    check_text = line_text[tag_end_location:]
            elif within_description_attrib:
                # Within description attribute - don't check content.
                check_text = ""
                # Look for the end attribute.
                attr_end_location = line_text.find("\"")
                if attr_end_location > 0:
                    within_description_attrib = False
                    check_text = line_text[attr_end_location:]
            else:
                tag_location = line_text.find("<description>")
                attr_location = line_text.find(" description=")
                if tag_location > 0:
                    within_description_tag = True
                    # Get all text apart from the description tag content
                    tag_location += len("<description>")
                    check_text = line_text[0:tag_location]
                    line_text = line_text[tag_location:]
                    tag_end_location = line_text.find("</description>")
                    if tag_end_location > 0:
                        within_description_tag = False
                        check_text += line_text[tag_end_location:]
                elif attr_location > 0:
                    within_description_attrib = True
                    # Get all text apart from the description value
                    check_text = line_text[0:attr_location]
                    line_text = line_text[attr_location:]
                    parts = str(line_text).split("\"", 2)
                    before = parts[0]
                    # description_contents=parts[1]
                    after = str.join("\"", parts[2:])
                    check_text += before + "\"\"" + after
                    if len(after) > 0:
                        within_description_attrib = False
                else:
                    check_text = line_text

            if check_text.lower() != check_text:
                issues.append({
                    "line": line_number + 1,
                    "message": "XML files must be all lower case."})

        return test_name, issues

    def test_xml_005(self):
        """Check writable property set in component specification.

        **Test name:** Component specification: Property writable attribute set

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = (
            "Component specification: Property writable attribute set")

        issues = []
        if self._component_spec():
            root = self._get_code_as_xml_dom()
            if root is None:
                return test_name, [{"line": 0,
                                    "message": "Unable to parse xml."}]
            for property_element in root.findall("property"):
                # Each non-parameter property, must have writable set
                if not property_element.attrib.get("parameter", False):
                    if not property_element.attrib.has_key("writable"):
                        issues.append({
                            "line": property_element.sourceline,
                            "message": "Writable attribute of properties "
                                       + "must be explicitly set."})

        return test_name, issues

    def test_xml_006(self):
        """Check producer of ports set in component specification.

        **Test name:** Component specification: Port producer set

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "Component specification: Port producer set"
        issues = []
        if self._component_spec():
            root = self._get_code_as_xml_dom()
            if root is None:
                return test_name, [{"line": 0,
                                    "message": "Unable to parse xml."}]
            for port_element in root.findall("port"):
                # Each port element must have a producer attribute set
                if not port_element.attrib.has_key("producer"):
                    issues.append({
                        "line": port_element.sourceline,
                        "message": "Producer attributes of ports must be "
                                   + "explicitly set."})

        return test_name, issues

    def test_xml_007(self):
        """Check default value set for properties in worker description.

        **Test name:** Worker description: Property default set

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "Worker description: Property default set"

        issues = []
        # If a worker description file
        if self._worker_description():
            root = self._get_code_as_xml_dom()
            if root is None:
                return test_name, [{"line": 0,
                                    "message": "Unable to parse xml."}]
            for property_element in root.findall("property"):
                # All non volatile property element must have a default value
                if not property_element.attrib.get("volatile", False):
                    if not property_element.attrib.has_key("default"):
                        issues.append({
                            "line": property_element.sourceline,
                            "message": "Properties must have a default value set."})

        return test_name, issues

    def test_xml_008(self):
        """Test no longer used - new tests can be added at this test number.

        **Test name:** None

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "None"

        issues = []

        return test_name, issues

    def test_xml_009(self):
        """Check a build specification is set, and default not used.

        **Test name:** Build file: Configuration specified

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "Build file: Configuration specified"

        issues = []

        if self._build_file():
            root = self._get_code_as_xml_dom()
            if root is None:
                return test_name, [{"line": 0,
                                    "message": "Unable to parse xml."}]
            if not root.tag == "build":
                issues.append({
                    "line": None,
                    "message": "No <build> tag found in build file."})
            # lxml child iterator that ignores non-elements such as comments
            elements = list(root.iterchildren(tag=ElementTree.Element))
            if len(elements) == 0:
                issues.append({"line": None,
                               "message": "Empty build file detected." +
                                          " Build cases must be set."})

        return test_name, issues

    def test_xml_010(self):
        """Check component specification name set.

        **Test name:** Component specification: Name set

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "Component specification: Name set"

        issues = []

        if self._component_spec():
            root = self._get_code_as_xml_dom()
            if root is None:
                return test_name, [{"line": 0,
                                    "message": "Unable to parse xml."}]
            if root.tag == "componentspec":
                if root.attrib.has_key("name"):
                    issues.append({
                        "line": root.sourceline,
                        "message": "A component specification must not "
                                   + "have a name attribute, so the "
                                   + "default of the file name is used."})

        return test_name, issues

    def test_xml_011(self):
        """Check in component specification attributes in correct order.

        **Test name:** Component specification: Properties, inputs then outputs

        In a component specification all the properties must be listed, then
        all the inputs and then all the outputs.

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "Component specification: Properties, inputs then outputs"

        issues = []
        outputs_found = False
        inputs_found = False

        if not self._component_spec():
            return test_name, issues
        root = self._get_code_as_xml_dom()
        if root is None:
            return test_name, [{"line": 0,
                                "message": "Unable to parse xml."}]
        for element in root.iter("property", "port"):
            if element.tag == "property":
                if outputs_found:
                    issues.append({
                        "line": element.sourceline,
                        "message": "A property found after an output "
                        + "port. Correct order is properties, "
                        + "inputs, then outputs."})
                if inputs_found:
                    issues.append({
                        "line": element.sourceline,
                        "message": "A property found after an input port. "
                        + "Correct order is properties, "
                        + "inputs, then outputs."})

            if element.tag == "port":
                value = element.attrib["producer"]
                if value is None:
                    issues.append({
                        "line": element.sourceline,
                        "message": "Port does not have the \"producer\" attribute."})
                if str(value).lower() == "true":
                    outputs_found = True
                elif str(value).lower() == "false":
                    inputs_found = True
                    if outputs_found:
                        issues.append({
                            "line": element.sourceline,
                            "message": "An input port found after an output"
                            + " port. Correct order is inputs,"
                            + " outputs, then properties."})
                else:
                    issues.append({
                        "line": element.sourceline,
                        "message": "A port has an unexpected value for the \"producer\" attribute."})

        return test_name, issues

    def test_xml_012(self):
        """Check default value set for properties in a component specification.

        **Test name:** Component specification: Property default set

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "Component specification: Property default set"

        issues = []

        if self._component_spec():
            root = self._get_code_as_xml_dom()
            if root is None:
                return test_name, [{"line": 0,
                                    "message": "Unable to parse xml."}]
            for property_element in root.findall("property"):
                # All non volatile property elements must have a default value
                if not property_element.attrib.get("volatile", False):
                    if not property_element.attrib.has_key("default"):
                        issues.append({
                            "line": property_element.sourceline,
                            "message": "All properties must have a default value."
                        })

        return test_name, issues

    def test_xml_013(self):
        """Check descriptions set for properties in a component specification.

        **Test name:** Component specification: Property descriptions

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "Component specification: Properties descriptions"

        issues = []

        if self._component_spec():
            root = self._get_code_as_xml_dom()
            if root is None:
                return test_name, [{"line": 0,
                                    "message": "Unable to parse xml."}]
            for property_element in root.findall("property"):
                if not property_element.attrib.has_key("description"):
                    issues.append({
                        "line": property_element.sourceline,
                        "message": "All properties should have a description."
                    })

        return test_name, issues

    def _get_code_as_xml_dom(self):
        """Parse the current `_code` into an XML element tree.

        Returns: The element tree or None on error.
        """
        try:
            root = ElementTree.fromstring("\n".join(self._code))
        except ElementTree.XMLSyntaxError:
            root = None
        return root

    def _component_spec(self):
        """Report if current file being checked is a component specification.

        Returns:
            True if the current file being checked is a component
            specification, otherwise returns False.
        """
        if str(self.path)[-9:] == "-spec.xml":
            return True
        else:
            return False

    def _worker_description(self):
        """Report if the current file being checked is a worker description.

        Returns:
            True if the current file being checked is a worker description,
            otherwise returns False.
        """
        # To test if a worker description, check if the parent directory's name
        # is the same as the file's name before any ".".
        if self.path.parent.with_suffix(".xml").name == self.path.name:
            return True
        else:
            return False

    def _build_file(self):
        """Report if the current file being checked is a build file.

        Returns:
            True is the current file being checked is a build file, otherwise
            returns False.
        """
        if self.path.name[-10:] == "-build.xml":
            return True
        else:
            return False

    def _remove_xml_comments(self, input_lines):
        """Remove comment symbols and their content from the file content.

        Args:
            input_lines (List of str): The content of the file

        Returns:
            List of strings representing the file content without the comments.
        """
        reduced_content = [""] * len(input_lines)

        block_comment_start = "<!--"
        block_comment_end = "-->"
        currently_in_comment = False
        for line_number, line_text in enumerate(input_lines):

            while len(line_text) > 0:
                # If in a comment, check if ended and use any trailing content
                if currently_in_comment:
                    endPos = line_text.find(block_comment_end)
                    if endPos >= 0:
                        _, line_text = line_text.split(block_comment_end, 1)
                        currently_in_comment = False
                    else:
                        # Comment continues over lines
                        line_text = ""

                # If not currently a comment, check if one starts this line
                if not currently_in_comment:
                    if line_text.find(block_comment_start) >= 0:
                        content, line_text = line_text.split(
                            block_comment_start, 1)
                        reduced_content[line_number] += content
                        currently_in_comment = True
                    # Otherwise not a comment so take whole line
                    else:
                        reduced_content[line_number] += line_text
                        line_text = ""

        return reduced_content

    def _remove_xml_attribute_content(self, input_lines):
        """Remove attribute contents from the file.

        Removes anything within double quotes, leaving just "".

        Args:
            input_lines (List of str): The content of the file

        Returns:
            List of strings representing the file content without the comments.
        """
        reduced_content = [""] * len(input_lines)

        quote_character = "\""
        currently_in_quotes = False
        for line_number, line_text in enumerate(input_lines):

            while len(line_text) > 0:
                # If in quotes, check if ended and use any trailing content
                if currently_in_quotes:
                    endPos = line_text.find(quote_character)
                    if endPos >= 0:
                        _, line_text = line_text.split(quote_character, 1)
                        reduced_content[line_number] += quote_character
                        currently_in_quotes = False
                    else:
                        # Quoted string continues over lines
                        line_text = ""

                # If not currently in quotes, check if one starts this line
                if not currently_in_quotes:
                    if line_text.find(quote_character) >= 0:
                        content, line_text = line_text.split(
                            quote_character, 1)
                        reduced_content[line_number] += content
                        reduced_content[line_number] += quote_character
                        currently_in_quotes = True
                    # Otherwise no quotes so take whole line
                    else:
                        reduced_content[line_number] += line_text
                        line_text = ""

        return reduced_content
