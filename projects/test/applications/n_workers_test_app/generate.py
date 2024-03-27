#!/usr/bin/env python3
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

import os
import sys
import argparse
from pathlib import Path

# Class to generate components, assembly, and application files
class Generate:
    def __init__(self, number, host):
        self.num = number
        self.host = host
        self.root = os.environ['OCPI_ROOT_DIR']

    # Generate hdl components symlinks
    def components(self):
        print("Creating " + str(self.num) + " bias_vhdl components")
        # Create each component symlink
        for n in range(0, self.num):
            # Create component directory
            p = Path(self.root + "/projects/test/components/bias_vhdl" + str(n) + ".hdl")
            p.mkdir(parents=True, exist_ok=True)
    
            # Create vhd symlink
            vhd_name = Path("bias_vhdl" + str(n) + ".vhd")
            vhd_link = p / vhd_name
            bias_vhd = self.root + "/projects/core/components/bias_vhdl.hdl/bias_vhdl.vhd"
            if not vhd_link.exists():
                os.symlink(bias_vhd, vhd_link) 
            
            # Create xml symlink
            xml_name = Path("bias_vhdl" + str(n) + ".xml")
            xml_link = p / xml_name
            bias_xml = self.root + "/projects/core/components/bias_vhdl.hdl/bias_vhdl.xml"
            if not xml_link.exists():
                os.symlink(bias_xml, xml_link) 

    # Generate spec xml symlink
    def spec(self):
        print("Creating spec file for bias_vhdl components")
        bias_spec = Path(self.root + "/projects/core/components/specs/bias_spec.xml")
        spec_link = Path(self.root + "/projects/test/components/specs/bias_spec.xml")
        if not spec_link.exists():
           os.symlink(bias_spec, spec_link)
    
    # Generate assembly xml file
    def assembly(self):
        print("Creating n_workers_" + str(self.num) + ".xml assembly file")
        # Create assembly directory
        p = Path(self.root + "/projects/test/hdl/assemblies/n_workers_" + str(self.num))
        p.mkdir(parents=True, exist_ok=True)
    
        # Create assembly xml file
        asm_name = Path("n_workers_" + str(self.num) + ".xml")
        asm_file = p / asm_name
        if not asm_file.exists():
            # Build assembly xml text
            text = "<HdlAssembly>\n" 
            text += "  <Instance Worker='bias_vhdl0' connect='bias_vhdl1' external='in'/>\n"
            for n in range(1, self.num-1):
                text +=  "  <Instance Worker='bias_vhdl" + str(n) + "' connect='bias_vhdl" + str(n+1) + "'/>\n"
            text += "  <Instance Worker='bias_vhdl" + str(self.num-1) + "' external='out'/>\n"
            text += "</HdlAssembly>\n"

            # Write text to file
            with open(asm_file, 'w') as f:
                f.write(text)
    
    # Generate application xml file
    def application(self):
        print("Creating n_workers_" + str(self.num) + ".xml application file")
        # Create application xml file
        app_file = Path(self.root + "/projects/test/applications/n_workers_test_app/n_workers_" + str(self.num) + ".xml")
        if not app_file.exists():
            # Build application xml text
            text =  "<Application done='file_write'>\n"
            text += "  <Instance component='ocpi.core.file_read' platform='" + self.host + "' connect='bias0'>\n"
            text += "    <Property name='filename' value='data.input'/>\n"
            text += "  </Instance>\n"
            for n in range(1, self.num):
                text += "  <Instance component='ocpi.test.bias' connect='bias" + str(n) + "'>\n"
                text += "    <property name='biasValue' value='1'/>\n"
                text += "  </Instance>\n"
            text += "  <Instance component='ocpi.test.bias' connect='file_write'>\n"
            text += "    <property name='biasValue' value='1'/>\n"
            text += "  </Instance>\n"
            text += "  <Instance component='ocpi.core.file_write' platform='" + self.host + "'>\n"
            text += "    <Property name='filename' value='data.output'/>\n"
            text += "  </Instance>\n"
            text += "</Application>\n"

            # Write text to file
            with open(app_file, 'w') as f:
                f.write(text)

def over_one(value):
    ivalue = int(value)
    if ivalue < 2:
        raise argparse.ArgumentTypeError("%s is an invalid entry, only positive int values will be accepted" % value)
    return ivalue

def main():
    __doc__ = 'Generates workers, assembly, and application files to test n number of workers within OpenCPI Framework'
    # Parse CLI arguments
    parser = argparse.ArgumentParser(
                        description=__doc__,
                        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-n', '--number', type=over_one, default=2, 
                        help="Number of vhdl_bias workers to create for the assembly, default and minimum is 2")
    parser.add_argument('-o', '--host', type=str, default="ubuntu20_04", 
                        help="Host OS the application is launched from, default is ubuntu20_04")
   
    args = parser.parse_args(args=None if sys.argv[1:] else ['--help'])
    
    if os.environ.get('OCPI_ROOT_DIR') is None:
        raise EnvironmentError("OCPI_ROOT_DIR does not exist, source opencpi-setup.sh")

    gen = Generate(args.number, args.host)
    gen.components()
    gen.spec()
    gen.assembly()
    gen.application()

if __name__ == '__main__':
    sys.exit(main())
