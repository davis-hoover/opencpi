#!/usr/bin/env python3

# Testing summary directive
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


import json
import pathlib
import sphinx

import docutils
import docutils.parsers.rst

from . import docutils_helpers


class OcpiDocumentationTestResultSummary(docutils.parsers.rst.Directive):
    """ ocpi_documentation_test_result_summary directive
    """
    has_context = False
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True
    # Allow setting of the test log location (ignoring the automatically
    # determined location)
    option_spec = {"test_log": str}

    def run(self):
        """ Action when ocpi_documentation_test_result_summary directive called

        Generates a table which summaries the component unit tests including
        details of variables set in the testing in any generate stage scripts,
        the condition(s) that needs to be met for testing to pass and the
        results of the testing.

        Returns:
            List with the docutils tree map to replace the directive in the
                source text with.
        """
        # Variable to add the resulting output to
        content = []

        # If lint log set as option use that value otherwise set automatic path
        if "test_log" in self.options:
            test_log_path = pathlib.Path(
                self.state.document.attributes["source"]).parent.joinpath(
                self.options["test_log"]).resolve()
            # Give warning in this case as user has set log path manually, but
            # file does not exist. While file not existing is a valid event
            # when the user has manually set this likely they know the path
            # exists.
            if not test_log_path.is_file():
                self.state_machine.reporter.warning(
                    f"{test_log_path} is not a valid file path",
                    line=self.lineno)
        else:
            test_log_path = pathlib.Path(
                self.state.document.attributes["source"]).parent.joinpath(
                "test_log.json")

        if not test_log_path.is_file():
            content.append(docutils.nodes.paragraph(
                "", "Component testing not completed."))
            return content

        # For each test case and each worker, if all the subcases have passed
        # then the test case is marked as passed. If any subcase has failed
        # then the test case for that worker is marked as failed.
        with open(test_log_path, "r") as test_log_file:
            test_log = json.load(test_log_file)
        test_summary = {}
        workers = []
        for case, subcases in test_log.items():
            test_summary[case] = {}
            for subcase in subcases.values():
                for generator_or_comparison_or_worker, detail in \
                        subcase.items():
                    if generator_or_comparison_or_worker in [
                            "generator", "comparison_method"]:
                        continue
                    worker = generator_or_comparison_or_worker
                    test_summary[case][worker] = "PASSED"
                    if worker not in workers:
                        workers.append(worker)
                    for platform in detail.values():
                        for port_result in platform["result"].values():
                            if port_result is False:
                                test_summary[case] = "FAILED"

        component_name = pathlib.Path(
            self.state.document.attributes["source"]).stem[0:-6]
        component_name = component_name.replace("_", "-")

        test_summary_table = docutils.nodes.table("")
        table_group = docutils.nodes.tgroup("", cols=(len(workers) + 1))
        # Colwidth is the percentage width of the table, 20% will be allocated
        # to the test number column the rest will be assigned to the worker
        # results column
        table_group.append(docutils.nodes.colspec("", colwidth=20))
        column_widths = int(80 / max(len(workers), 1))
        for _ in workers:
            table_group.append(docutils.nodes.colspec(
                "", colwidth=column_widths))

        header_row = []
        header_row.append(docutils.nodes.entry(
            "", docutils.nodes.paragraph("", "Test case")))
        for worker in workers:
            header_row.append(docutils.nodes.entry(
                "", docutils.nodes.literal("", worker)))
        table_group.append(
            docutils.nodes.thead("", docutils.nodes.row("", *header_row)))

        table_body = docutils.nodes.tbody("")
        for case, worker_results in test_summary.items():
            row = []

            test_link = sphinx.addnodes.pending_xref(
                "", refdoc=self.state.document.settings.env.docname,
                refdomain="std", refexplicit="True",
                reftarget=f"{component_name}-test{case}", reftype="ref",
                refwarn=True)
            link_text = docutils.nodes.inline(text=f"Test {case}")
            test_link.append(link_text)
            row_entry = docutils.nodes.entry()
            row_paragraph = docutils.nodes.paragraph()
            row_paragraph.append(test_link)
            row_entry.append(row_paragraph)

            row.append(row_entry)
            for worker in workers:
                if worker in worker_results:
                    row.append(self._worker_result_entry(
                        worker_results[worker]))
                else:
                    row.append(self._worker_result_entry("NOT_RUN"))
            table_body.append(docutils.nodes.row("", *row))
        table_group.append(table_body)
        test_summary_table.append(table_group)
        content.append(test_summary_table)

        return content

    def _worker_result_entry(self, result):
        """ Get test result table entry

        Args:
            result (str): The test result as a string (PASSED, FAILED or
                NOT_RUN).

        Returns:
            docutils.nodes.entry that contains the test result entry.
        """
        # Defining the paragraph classes means the different styling will be
        # added by the uses custom CSS theme
        if result.upper() == "PASSED":
            return docutils.nodes.entry(
                "", docutils.nodes.paragraph("",
                                             "Passed",
                                             classes=["testpassed"]))
        elif result.upper() == "FAILED":
            return docutils.nodes.entry(
                "", docutils.nodes.paragraph("",
                                             "Failed",
                                             classes=["testfailed"]))
        elif result.upper() == "NOT_RUN":
            return docutils.nodes.entry(
                "", docutils.nodes.paragraph("",
                                             "Not run",
                                             classes=["testwarning"]))
        else:
            self.state_machine.reporter.warning(
                f"Unexpected test result found: {result}",
                line=self.lineno)

        return docutils.nodes.entry()
