#!/usr/bin/env python3

# Custom include directive with text replacement
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


import os
import sys

from sphinx.util.docutils import SphinxDirective
from docutils import io, nodes, statemachine, utils
from docutils.utils.error_reporting import SafeString, ErrorString
from docutils.parsers.rst import directives, states


class OcpiDocumentationInclude(SphinxDirective):
    """
    Like the standard "Include" directive, but interprets absolute paths
    "correctly", i.e. relative to the source directory. It also has the
    added ability to substitute text within the included text prior to
    parsing it.

    Include content read from a separate source file.

    The included file will be parsed.  The encoding of the included
    file can be specified.  Only a part of the file may be included
    by specifying start and end line or text to match before and/or
    after the text to be used.

    NOTE: This was taken from the Include in
    docutils.parsers.rst.directives.misc and then altered to add
    the string replacements.
    """

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    has_content = True
    option_spec = {"encoding": directives.encoding,
                   "tab-width": int,
                   "start-line": int,
                   "end-line": int,
                   "start-after": directives.unchanged_required,
                   "end-before": directives.unchanged_required
                   }

    standard_include_path = os.path.join(os.path.dirname(states.__file__),
                                         "include")

    def run(self):
        """
        Include a file as part of the content of this reST file - but
        perform some string replacements before parsing.

        NOTE: This was taken from the Include in
        docutils.parsers.rst.directives.misc and then altered to add
        the string replacements.

        Returns:
            An empty list.
        """

        if not self.state.document.settings.file_insertion_enabled:
            raise self.warning("\"%s\" directive disabled." % self.name)
        source = self.state_machine.input_lines.source(
            self.lineno - self.state_machine.input_offset - 1)
        source_dir = os.path.dirname(os.path.abspath(source))
        path = directives.path(self.arguments[0])
        if path.startswith("<") and path.endswith(">"):
            path = os.path.join(self.standard_include_path, path[1:-1])
        path = os.path.normpath(os.path.join(source_dir, path))
        path = utils.relative_path(None, path)
        path = nodes.reprunicode(path)
        encoding = self.options.get(
            "encoding", self.state.document.settings.input_encoding)
        e_handler = self.state.document.settings.input_encoding_error_handler
        tab_width = self.options.get(
            "tab-width", self.state.document.settings.tab_width)
        try:
            self.state.document.settings.record_dependencies.add(path)
            include_file = io.FileInput(source_path=path,
                                        encoding=encoding,
                                        error_handler=e_handler)
        except UnicodeEncodeError as error:
            raise self.severe(u"Problems with \"%s\" directive path:\n"
                              "Cannot encode input file path \"%s\" "
                              "(wrong locale?)." %
                              (self.name, SafeString(path)))
        except IOError as error:
            raise self.severe(u"Problems with \"%s\" directive path:\n%s." %
                              (self.name, ErrorString(error)))

        # Get to-be-included content
        startline = self.options.get("start-line", None)
        endline = self.options.get("end-line", None)
        try:
            if startline or (endline is not None):
                lines = include_file.readlines()
                rawtext = "".join(lines[startline:endline])
            else:
                rawtext = include_file.read()
        except UnicodeError as error:
            raise self.severe(u"Problem with \"%s\" directive:\n%s" %
                              (self.name, ErrorString(error)))
        # start-after/end-before: no restrictions on newlines in match-text,
        # and no restrictions on matching inside lines vs. line boundaries
        after_text = self.options.get("start-after", None)
        if after_text:
            # skip content in rawtext before *and incl.* a matching text
            after_index = rawtext.find(after_text)
            if after_index < 0:
                raise self.severe("Problem with \"start-after\" option of \"%s\" "
                                  "directive:\nText not found." % self.name)
            rawtext = rawtext[after_index + len(after_text):]
        before_text = self.options.get("end-before", None)
        if before_text:
            # skip content in rawtext after *and incl.* a matching text
            before_index = rawtext.find(before_text)
            if before_index < 0:
                raise self.severe("Problem with \"end-before\" option of \"%s\" "
                                  "directive:\nText not found." % self.name)
            rawtext = rawtext[:before_index]

        # Added step to do string replacements before the to-be-included
        # content is parsed
        rawtext = self._do_replacements(rawtext)

        include_lines = statemachine.string2lines(rawtext, tab_width,
                                                  convert_whitespace=True)
        for i, line in enumerate(include_lines):
            if len(line) > self.state.document.settings.line_length_limit:
                raise self.warning("\"%s\": line %d exceeds the"
                                   " line-length-limit." % (path, i+1))

        # include as rST source
        #
        # Prevent circular inclusion:
        source = utils.relative_path(None, source)
        clip_options = (startline, endline, before_text, after_text)
        include_log = self.state.document.include_log
        if not include_log:  # new document:
            # log entries: (<source>, <clip-options>, <insertion end index>)
            include_log = [(source, (None, None, None, None), sys.maxsize/2)]
        # cleanup: we may have passed the last inclusion(s):
        include_log = [entry for entry in include_log
                       if entry[2] >= self.lineno]
        if (path, clip_options) in [(pth, opt)
                                    for (pth, opt, e) in include_log]:
            raise self.warning("circular inclusion in \"%s\" directive: %s"
                               % (self.name, " < ".join([path] + [pth for (pth, opt, e)
                                                                  in include_log[::-1]])))
        # include as input
        self.state_machine.insert_input(include_lines, path)
        # update include-log
        include_log.append((path, clip_options, self.lineno))
        self.state.document.include_log = [(pth, opt, e+len(include_lines)+2)
                                           for (pth, opt, e) in include_log]
        return []

    def _do_replacements(self, rawtext):
        """
        Get the list of replacements to make from the content
        of the directive - and go through the raw text from
        the included file and perform string replacments.

        Args:
            rawtext (``str``): The raw text content of the include file.

        Returns:
            A ``str`` containing the text after the string replacments are performed.
        """

        for line in self.content:
            if len(line) > 0:
                needle = line[0:line.find(":")].strip()
                replacement = line[line.find(":")+1:].strip()
                rawtext = rawtext.replace(needle, replacement)
        return rawtext
