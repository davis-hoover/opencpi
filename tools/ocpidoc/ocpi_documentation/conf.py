#!/usr/bin/env python3

# Sphinx configuration file
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


import datetime
import pathlib
import sys


BUILD_FOLDER = "doc"

# Allow Sphinx extension to be found
sys.path.append(str(pathlib.Path(__file__).resolve().absolute().parent))

# Options set in this file can be found at
# http://www.sphinx-doc.org/en/master/usage/configuration.html

project = "OpenCPI assets"

show_authors = False

# Show version like OpenCPI docs, maybe OpenCPI doc build script can update this file
version = "OpenCPI Release: develop"
release = ""

needs_sphinx = "2.4"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.mathjax",
    "sphinxcontrib.spelling",
    "ocpi_sphinx_ext"
]

templates_path = []
source_suffix = ".rst"
language = "en"
exclude_patterns = [f"{BUILD_FOLDER}*",
                    "**ocpi_documentation/ocpi_documentation*",
                    "**/exports/*",
                    "**/imports/*",
                    "**/lib/*",
                    "exports/**",
                    "imports/**",
                    "lib/**"]

pygments_style = "sphinx"

math_number_all = False

numfig = True

# This code changes numbering format to what's used in OpenCPI docs
numfig_format = {
    "figure": "Figure %s:",
    "table": "Table %s:",
    "code-block": "Listing %s",
    "section": "Section %s"
}

html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "logo_only": True,
}
html_static_path = ["static"]
# OpenCPI logo from briefings
html_logo = "static/logo_ocpi.svg"
# Style sheet for OpenCPI added to CSS file list
html_css_files = ["css/test_result.css, css/ocpidocument-style.css"]
html_title = "OpenCPI assets"
html_short_title = "OCPI assets"
html_favicon = "static/favicon.ico"
html_last_updated_fmt = "%d %B %Y"
html_permalinks = False
html_sidebars = {
    "**": ["localtoc.html",
           "searchbox.html"]
}
html_use_index = True
html_show_sourcelink = False
html_show_sphinx = False
html_show_copyright = False
html_copy_source = False

spelling_lang = "en_US"
spelling_word_list_filename = str(pathlib.Path(__file__).parent.joinpath(
    "dictionary.txt").resolve())
spelling_show_suggestions = True

# Defines a tight table style to override the RTD theme's wide table format


def setup(app):
    app.add_css_file("css/ocpidocument-style.css")
