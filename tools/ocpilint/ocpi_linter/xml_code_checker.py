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

from . import base_code_checker
from . import utilities


class XmlCodeCheckerDefaults(base_code_checker.BaseCodeCheckerDefaults):
    """Default settings for XmlCodeChecker class."""
    license_notice = (open(pathlib.Path(__file__).parent
                           .joinpath("license_notices").joinpath("xml.txt"), "r")
                      .read())


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

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = "XML lint"

        before_code = list(self._code)
        if self._check_installed("xmllint"):
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

            if (self._code != before_code):
                line_number = 0
                for i, (l1, l2) in enumerate(zip(before_code, self._code)):
                    if l1 != l2:
                        line_number = i+1
                        break
                issues.append({"line": line_number,
                               "message": "File was reformatted by xmllint."})

        else:
            issues = [{
                "line": None,
                "message": "XML lint not installed. Cannot run test."}]

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

        # Single quotes in comments are allowed - so remove comments before checking
        reduced_content = self._remove_block_comments(self._code,
                                                      "<!--", "-->")
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
        comment_line = False
        within_description_tag = False
        for line_number, line_text in enumerate(self._code):
            # If not a comment, check all text is lower case
            if "<!--" in line_text:
                comment_line = True
            if comment_line is False:
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
                else:
                    tag_location = line_text.find("<description>")
                    attr_location = line_text.find(" description=")
                    if tag_location > 0:
                        within_description_tag = True
                        # Get all text apart from the description tag content
                        check_text = line_text[0:tag_location]
                        tag_end_location = line_text.find("</description>")
                        if tag_end_location > 0:
                            within_description_tag = False
                            check_text = (check_text +
                                          line_text[tag_end_location:])
                    elif attr_location > 0:
                        check_text = line_text[0:attr_location]
                        # Get all text apart from the description value (indexed
                        # at 1 after the split operation)
                        check_text = (check_text +
                                      line_text[attr_location:].split("\"")[0])
                        check_text = check_text + " ".join(
                            line_text[attr_location:].split("\"")[2:])
                    else:
                        check_text = line_text
                if check_text.lower() != check_text:
                    issues.append({
                        "line": line_number + 1,
                        "message": "XML files must be all lower case."})
            if "-->" in line_text:
                comment_line = False

        return test_name, issues

    def test_xml_005(self):
        """Check writable property set in component specification.

        **Test name:** Component specification: Property writable attribute
            set

        Returns:
            A tuple containing a string with the test name and a list of the
            identified test issues.
        """
        test_name = (
            "Component specification: Property writable attribute set")

        issues = []
        if self._component_spec():
            for line_number, line_text in enumerate(self._code):
                # If a property being set
                if ("<property " in line_text) and (
                        "parameter=\"true\"" not in line_text):
                    if not "writable=" in line_text:
                        issues.append({
                            "line": line_number + 1,
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
            for line_number, line_text in enumerate(self._code):
                # If a port being set
                if "<port " in line_text and "producer=" not in line_text:
                    issues.append({
                        "line": line_number + 1,
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
            for line_number, line_text in enumerate(self._code):
                # If a port being set
                if ("<property " in line_text
                    and "default=" not in line_text
                        and "volatile=\"true\"" not in line_text):
                    issues.append({
                        "line": line_number + 1,
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
        start_of_build = 0
        end_of_build = 0

        if self._build_file():
            for line_number, line_text in enumerate(self._code):
                if "<build>" in line_text:
                    start_of_build = line_number
                if "</build>" in line_text:
                    end_of_build = line_number

            if start_of_build == 0 and end_of_build == 0:
                issues.append({
                    "line": None,
                    "message": "Opening <build> tag and closing </build> tag "
                               + "not found in build file."})
            if start_of_build != 0 and start_of_build == end_of_build:
                issues.append({
                    "line": None,
                    "message": "Empty build file detected. Build cases must "
                               + "be set."})

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
            for line_number, line_text in enumerate(self._code):
                if "<componentspec" in line_text:
                    if "name=" in line_text:
                        issues.append({
                            "line": line_number + 1,
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

        if self._component_spec():
            for line_number, line_text in enumerate(self._code):
                if "<property" in line_text:
                    if outputs_found:
                        issues.append({
                            "line": line_number + 1,
                            "message": "A property found after an output "
                                       + "port. Correct order is properties, "
                                       + "inputs, then outputs."})
                    if inputs_found:
                        issues.append({
                            "line": line_number + 1,
                            "message": "A property found after an input port. "
                                       + "Correct order is properties, "
                                       + "inputs, then outputs."})

                if "<port" in line_text and "producer=\"false\"" in line_text:
                    inputs_found = True
                    if outputs_found:
                        issues.append({
                            "line": line_number + 1,
                            "message": "An input port found after an output "
                                       + "port. Correct order is inputs, "
                                       + "outputs, then properties."})

                if "<port" in line_text and "producer=\"true\"" in line_text:
                    outputs_found = True

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
            for line_number, line_text in enumerate(self._code):
                if ("<property " in line_text
                    and "default=" not in line_text
                        and "volatile=\"true\"" not in line_text):
                    issues.append({
                        "line": line_number + 1,
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
            for line_number, line_text in enumerate(self._code):
                if "<property" in line_text and \
                        "description=" not in line_text:
                    issues.append({
                        "line": line_number + 1,
                        "message": "All properties should have a description."
                    })

        return test_name, issues

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
