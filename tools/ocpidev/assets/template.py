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
This module holds the templates for assset creation.  these in theroy could be moved out to seperate
files in the future if that makes sence.  This file is intended to be easily editable by people who
know nothing about ocpidev internals but want to change templates for outputs of ocpidev create
"""

PROJ_EXPORTS="""
# This file specifies aspects of this project that are made available to users,
# by adding or subtracting from what is automatically exported based on the
# documented rules.
# Lines starting with + add to the exports
# Lines starting with - subtract from the exports
all

\n\n"""
PROJ_GIT_IGNORE = """
# Lines starting with '#' are considered comments.
# Ignore (generated) html files,
#*.html
# except foo.html which is maintained by hand.
#!foo.html
# Ignore objects and archives.
*.rpm
*.obj
*.so
*~
*.o
target-*/
*.deps
gen/
*.old
*.hold
*.orig
*.log
lib/
#Texmaker artifacts
*.aux
*.synctex.gz
*.out
**/doc*/*.pdf
**/doc*/*.toc
**/doc*/*.lof
**/doc*/*.lot
run/
exports/
imports
*.pyc
\n\n"""

PROJ_GIT_ATTR = """
*.ngc -diff
*.edf -diff
*.bit -diff
\n\n"""

PROJ_PROJECT_MK ="""# This Makefile fragment is for the {{name}} project

# Package identifier is used in a hierarchical fashion from Project to Libraries....
# The PackageName, PackagePrefix and Package variables can optionally be set here:
# PackageName defaults to the name of the directory
# PackagePrefix defaults to local
# Package defaults to PackagePrefix.PackageName
#
# ***************** WARNING ********************
# When changing the PackageName or PackagePrefix of an existing project the
# project needs to be both unregistered and re-registered then cleaned and
# rebuilt. This also includes cleaning and rebuilding any projects that
# depend on this project.
# ***************** WARNING ********************
#
{%if package_name: %}
PackageName={{package_name}}
{% endif %}
{%if package_prefix: %}
PackagePrefix={{package_prefix}}
{% endif %}
{%if package_id: %}
Package={{package_id}}
{% endif %}
{%if depend: %}
ProjectDependencies={{depend}}
{% endif %}
{%if prim_lib: %}
Libraries={{prim_lib}}
{% endif %}
{%if include_dir: %}
IncludeDirs={{include_dir}}
{% endif %}
{%if xml_include: %}
XmlIncludeDirs={{xml_include}}
{% endif %}
{%if comp_lib: %}
ComponentLibraries={{comp_lib}}
{% endif %}
\n\n"""

PROJ_MAKEFILE= ("""# This file is protected by Copyright. Please refer to the COPYRIGHT file
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

$(if $(realpath $(OCPI_CDK_DIR)),,\\
  $(error The OCPI_CDK_DIR environment variable is not set correctly.))
# This is the Makefile for the {{name}} project.
include $(OCPI_CDK_DIR)/include/project.mk
\n""")

LIB_MAKEFILE= ("""# This is the Makefile for the components directory when there are multiple
# libraries in their own directories underneath this components directory
$(if $(realpath $(OCPI_CDK_DIR)),,\\
  $(error The OCPI_CDK_DIR environment variable is not set correctly.))
include $(OCPI_CDK_DIR)/include/libraries.mk
\n""")

LIB_DIR_MAKEFILE= ("""# This is the bar library

# All workers created here in *.<model> will be built automatically
# All tests created here in *.test directories will be built/run automatically
# To limit the workers that actually get built, set the Workers= variable
# To limit the tests that actually get built/run, set the Tests= variable

# Any variable definitions that should apply for each individual worker/test
# in this library belong in Library.xml

include $(OCPI_CDK_DIR)/include/library.mk
\n""")

PROJ_GUI_PROJECT = ("""<?xml version="1.0" encoding="UTF-8"?>
<projectDescription>
  <name>{{determined_package_id}}</name>
  <comment></comment>
  <projects></projects>
  <buildSpec></buildSpec>
  <natures></natures>
</projectDescription>
\n""")

PROJ_PROJECT_XML_LEGACY = ("""<project
{%if package_name: %}
       PackageName='{{package_name}}'
{% endif %}
{%if package_prefix: %}
       PackagePrefix='{{package_prefix}}'
{% endif %}
{%if package_id: %}
       Package='{{package_id}}'
{% endif %}
{%if depend: %}
       ProjectDependencies='{{depend}}'
{% endif %}
{%if prim_lib: %}
       Libraries='{{prim_lib}}'
{% endif %}
{%if include_dir: %}
       IncludeDirs='{{include_dir}}'
{% endif %}
{%if xml_include: %}
       XmlIncludeDirs='{{xml_include}}'
{% endif %}
{%if comp_lib: %}
       ComponentLibraries='{{comp_lib}}'
{% endif %}
/>
\n""")

PROJ_PROJECT_XML = ("""<project>
{%if package_name: %}
       <OcpiProperty>
               <name>PackageName</name>
               <value>{{package_name}}</value>
       </OcpiProperty>
{% endif %}
{%if package_prefix: %}
       <OcpiProperty>
               <name>PackagePrefix</name>
               <value>{{package_prefix}}</value>
       </OcpiProperty>
{% endif %}
{%if package_id: %}
       <OcpiProperty>
               <name>Package</name>
               <value>{{package_id}}</value>
       </OcpiProperty>
{% endif %}
{%if depend: %}
       <OcpiProperty>
               <name>ProjectDependencies</name>
               <value>{{depend}}</value>
       </OcpiProperty>
{% endif %}
{%if prim_lib: %}
       <OcpiProperty>
               <name>Libraries</name>
               <value>{{prim_lib}}</value>
       </OcpiProperty>
{% endif %}
{%if include_dir: %}
       <OcpiProperty>
               <name>IncludeDirs</name>
               <value>{{include_dir}}</value>
       </OcpiProperty>
{% endif %}
{%if xml_include: %}
       <OcpiProperty>
               <name>XmlIncludeDirs</name>
               <value>{{xml_include}}</value>
       </OcpiProperty>
{% endif %}
{%if comp_lib: %}
       <OcpiProperty>
               <name>ComponentLibraries</name>
               <value>{{comp_lib}}</value>
       </OcpiProperty>
{% endif %}
</project>
\n""")

LIB_DIR_XML = ("""<library
{%if package_name: %}
       PackageName='{{package_name}}'
{% endif %}
{%if package_prefix: %}
       PackagePrefix='{{package_prefix}}'
{% endif %}
{%if package_id: %}
       Package='{{package_id}}'
{% endif %}
{%if prim_lib: %}
       Libraries='{{prim_lib}}'
{% endif %}
{%if include_dir: %}
       IncludeDirs='{{include_dir}}'
{% endif %}
{%if xml_include: %}
       XmlIncludeDirs='{{xml_include}}'
{% endif %}
{%if comp_lib: %}
       ComponentLibraries='{{comp_lib}}'
{% endif %}
/>
\n""")
