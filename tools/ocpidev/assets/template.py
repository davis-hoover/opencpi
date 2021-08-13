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
simulations/
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

LIB_DIR_MAKEFILE= ("""# This is the {{name}} library

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

LIBRARIES_XML = ("""<!-- This is the XML file for the components directory when there are multiple
     libraries in their own sub directories underneath this components directory -->
<libraries/>
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

APP_APPLICATION_XML = ("""<applications>
    <!-- To restrict the applications that are built or run, you can set the Applications
    attribute to the specific list of which ones you want to build and run, e.g.:
    <libraries Applications='app1 app3'/>
    Otherwise all applications will be built and run -->
</applications>
\n""")

APP_APPLICATION_APP_CC = ("""#include <iostream>
#include <string>
#include "OcpiApi.hh"

namespace OA = OCPI::API;

int main(/*int argc, char **argv*/) {
  // For an explanation of the ACI, see:
  // https://opencpi.gitlab.io/releases/develop/docs/OpenCPI_Application_Development_Guide.pdf

  try {
    OA::Application app("{{app}}.xml");
    app.initialize(); // all resources have been allocated
    app.start();      // execution is started

    // Do work here.

    // Must use either wait()/finish() or stop(). The finish() method must
    // always be called after wait(). The start() method can be called
    // again after stop().
    app.wait();       // wait until app is "done"
    app.finish();     // do end-of-run processing like dump properties
    // app.stop();

  } catch (std::string &e) {
    std::cerr << "app failed: " << e << std::endl;
    return 1;
  }
  return 0;
}
\n""")

APP_APPLICATION_APP_XML = ("""<!-- The {{app}} application xml file -->
<Application>
  <Instance Component='ocpi.core.nothing' Name='nothing'/>
</Application>
\n""")

COMPONENT_SPEC_XML = ("""<!-- This is the spec file (OCS) for: {{component}}
     Add component spec attributes, like "protocol".
     Add property elements for spec properties.
     Add port elements for i/o ports -->
<ComponentSpec>
  <!-- Add property and port elements here -->
</ComponentSpec>
\n""")

COMPONENT_SPEC_NO_CTRL_XML = ("""<!-- This is the spec file (OCS) for: {{component}}
     Add component spec attributes, like "protocol".
     Add property elements for spec properties.
     Add port elements for i/o ports -->
<ComponentSpec NoControl='true'>
  <!-- Add property and port elements here -->
</ComponentSpec>
\n""")

COMPONENT_HDL_LIB_XML = ("""<!-- This is the XML file for the hdl/{{hdl_lib}} library
     All workers created here in *.<model> directories will be built automatically
     All tests created here in *.test directories will be built/run automatically
     To limit the workers that actually get built, set the Workers= attribute
     To limit the tests that actually get built/run, set the Tests= attribute

     Any attribute definitions that should apply to all individual worker/test
     in this library belong in this xml file-->
<library>
  <!-- Add items here -->
</library>
\n""")

PROTOCOL_SPEC_XML = ("""<!-- This is the spec file (OPS) for protocol: {{protocol}}
     Add <operation> elements for message types.
     Add protocol summary attributes if necessary to override attributes
     inferred from operations/messages -->
<Protocol> <!-- add protocol summary attributes here if necessary -->
  <!-- Add operation elements here -->
</Protocol>
\n""")

TEST_GENERATE_PY = ("""#!/usr/bin/env python3

\"\"\"
Use this file to generate your input data.
Args: <list-of-user-defined-args> <input-file>
\"\"\"
\n""")

TEST_VERIFY_PY = ("""#!/usr/bin/env python3

\"\"\"
Use this script to validate your output data against your input data.
Args: <list-of-user-defined-args> <output-file> <input-files>
\"\"\"
\n""")

TEST_VIEW_SH = ("""#!/bin/bash --noprofile

# Use this script to view your input and output data.
# Args: <list-of-user-defined-args> <output-file> <input-files>
\n""")

TEST_NAME_TEST_XML = ("""<!-- This is the test xml for testing component "{{test}}" -->
<Tests UseHDLFileIo='true'>
  <!-- Here are typical examples of generating for an input port and verifying results
       at an output port
  <Input Port='in' Script='generate.py'/>
  <Output Port='out' Script='verify.py' View='view.sh'/>
  -->
  <!-- Set properties here.
       Use Test='true' to create a test-exclusive property. -->
</Tests>
\n""")

HDLPLATFORM_PLATFORMS_XML = ("""<!-- To restrict the HDL platforms that are built, you can set the Platforms
     attribute to the specific list of which ones you want to build, e.g.:
     Platforms='pf1 pf3'
     Otherwise all platforms will be built
     Alternatively, set the ExcludePlatforms attribute to the ones you want to exclude-->
<hdlplatforms/>
\n""")

HDLPLATFORM_PLATFORM_XML = ("""<!-- This file defines the {{platform}} HDL platform 
    Set the "part" attribute to the part (die-speed-package, e.g. xc7z020-1-clg484) for the platform
    Set this variable to the names of any other component libraries with devices required by this
    platform. Do not use slashes.  If there is an hdl/devices library in this project, it will be
    searched automatically, as will "devices" in any projects this project depends on.
    An example might be something like "our_special_devices", which would exist in this or
    other projects.-->
<HdlPlatform Spec="platform-spec"
{%if hdl_part: %}
    Part='{{hdl_part}}'>
{% else %}
    Part='xc7z020-1-clg484'>
{% endif %}
    <SpecProperty Name='platform' Value='{{platform}}'/>
    <!-- These next two lines must be present in all platforms -->
    <MetaData Master="true"/>
    <TimeBase Master="true"/>
{%if use_sdp: %}
    <SDP Name='sdp' Master='true'/>
{% endif %}
    <!-- Set your time server frequency -->
    <Device Worker='time_server'>
{%if time_freq: %}
        <Property Name='frequency' Value='{{time_freq}}'/>
{% else %}
        <Property Name='frequency' Value='100e6'/>
{% endif %}
    </Device>
    <!-- Put any additional platform-specific properties here using <Property> -->
    <!-- Put any built-in (physically present) devices here using <device> -->
    <!-- Put any card slots here using <slot> -->
    <!-- Put ad hoc signals here using <signal> -->
</HdlPlatform>
\n""")

HDL_ASSEMBLIES_XML = ("""<!-- This is the XML file for the hdl/assemblies directory
     To restrict the HDL assemblies that are built, you can set the Assemblies
     attribute to the specific list of which ones you want to build, e.g.:
       Assemblies='assy1 assy3'
     Otherwise all assemblies will be built
     Alternatively, you can set ExcludeAssemblies to list the ones you want to exclude -->
<assemblies>
</assemblies>
\n""")

HDL_ASSEMBLY_XML = ("""<!-- This is the HDL XML Makefile for assembly: {{assembly}}
     The file '{{assembly}}.xml' defines the assembly.
     The default container for all assemblies is one that connects all external ports to
     the devices interconnect to communicate with software workers or other FPGAs.
     Limit this assembly to certain platforms or targets with
     Exclude/Only and Targets/Platforms ie:
        OnlyTargets=
        ExcludeTargets=
        OnlyPlatforms=
        ExcludePlatforms=
     If you want to connect external ports of the assembly to local devices on the platform,
     you must define container XML files, and mention them in a "Containers" variable here, e.g.:
     Containers='take_input_from_local_ADC' -->
<HdlAssembly>
{%if only_target: %}
     OnlyTargets='{{only_target}}'
{% endif %}
{%if exclude_target: %}
     ExcludeTargets='{{exclude_target}}'
{% endif %}
{%if only_platform: %}
     OnlyPlatforms='{{only_platform}}'
{% endif %}
{%if exclude_platform: %}
     ExcludePlatforms='{{exclude_platform}}'
{% endif %}
</HdlAssembly>
\n""")

HDL_CARDS_XML = ("""<!-- This is the XML file for the hdl/cards library
     All workers created here in *.<model> directories will be built automatically
     All tests created here in *.test directories will be built/run automatically
     To limit the workers that actually get built, set the Workers= attribute
     To limit the tests that actually get built/run, set the Tests= attribute

     Any attribute definitions that should apply to all individual worker/test
     in this library belong in this xml file-->
<library
>
</library>
\n""")

HDL_SLOT_XML = ("""<!-- This is the slot definition file for slots of type: {{hdl_slot}}
     Add <signal> elements for each signal in the slot -->
<SlotType>
  <!-- Add signal elements here -->
</SlotType>
\n""")

HDL_CARD_XML = ("""<!-- This is the card definition file for cards of type: {{hdl_card}}
     Add <signal> elements for each signal in the card -->
<Card>
  <!-- Add device elements here, with signal mappings to card signals -->
</Card>
\n""")
