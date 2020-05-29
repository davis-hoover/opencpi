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
"""
Generates reload order rom for coefficient reload based on xilinx _reload_order.txt 

Xilinx FIR compiler IP core's coefficient reload interface requires coefficients be loaded in a specific order. The order is specified in a file ending in _reload_order.txt. The ROM generated by this python script is used to translate coefficients from the property array `taps` order from coefficient 1-NUM_TAPS_p to order expected by coefficient reload interface. 

Xilinx IP core specifies this requirement in the interest of producing an area-efficient FPGA implementation. To keep to fir_real_sse component specification this additional logic is added to maintain 1-NUM_TAPs_p order used by other component implementations. ` 
"""

import argparse
import types 
import os
import pydoc 
import math 
from datetime import datetime, timezone

def parse_cl_vars():
    """
    Construct the argparse object and parse all command line arguments into a dictionary
    """
    description = ("Generate ROM for reload order of coefficents") 
    parser = argparse.ArgumentParser(description=description,
                                    formatter_class=argparse.RawDescriptionHelpFormatter,
                                    prog="generate_reload_rom.py")
    parser.print_help = types.MethodType(lambda self,
                                                    _=None: pydoc.pager("\n" + self.format_help()),
                                             parser)
    parser.print_usage = types.MethodType(lambda self,
                                                 _=None: pydoc.pager("\n" + self.format_usage()),
                                          parser)
    # This displays the error AND help screen when there is a usage error or no arguments provided
    parser.error = types.MethodType(lambda self, error_message: ( 
                                      pydoc.pager(error_message + "\n\n" + self.format_help()), 
                                      exit(1)),parser)  
    parser.add_argument("input_file", nargs=1, help="input file")
    parser.add_argument("output_file", nargs=1, help="output file") 
    
    parser.add_argument("-a_bw", "--addr-bit-width", type=int,
                        help="Specify address bus bit width")
    parser.add_argument("-d_bw", "--data-bit-width", type=int,
                        help="Specify data bus bit width")
    

    cmd_args, args_value = parser.parse_known_args()

    if args_value:
        print("invalid options were uses: " + + " ".join(args_value))
        sys.exit(1)
    return vars(cmd_args)

def extract_reload_order(args):
    """
    Function that extracts reload order from input file and returns array 
    of integers containing order. 
    """

    input_file = args["input_file"][0]  
    order = []

    # open input file and walk each line 
    with open(input_file, 'r') as fileobj:
        for row in fileobj:

            # extract just numbers on each line
            # expected format:
            #   Reload index 0 = Coefficient 44
            numbers_in_str = [int(s) for s in row.split() if s.isdigit()]

	    # append coefficient number to array 
            order.append(numbers_in_str[1])

    return order          

def generate_vhd(args):
    """
    Function that generates vhdl rom based off reload order
    """ 
    input_file_path = args["input_file"][0]
    output_file_path = args["output_file"][0]
    output_filename = os.path.basename(output_file_path)
    entity_name = output_filename.replace(".vhd","")
    out = open(output_file_path, 'w')
    order = args["order"]

    addr_bw_arg = args["addr_bit_width"]
    data_bw_arg = args["data_bit_width"]
	
    num_of_coeff = max(order)
    addr_bw = int(math.ceil(math.log(num_of_coeff,2)))
    data_bw = addr_bw    
  
    # Override calculated data bit widths if arg is specified 
    if addr_bw_arg != None:
        addr_bw = addr_bw_arg
    if data_bw_arg != None: 
        data_bw = data_bw_arg

    data_format = '0' + str(data_bw) + 'b'   
    rom_size = int(math.pow(2, addr_bw))
 
    # Write header     
    now = datetime.now(timezone.utc).astimezone()
    current_time = now.strftime("%a %b %-d %H:%M:%S %Y ")
    current_time = current_time + now.tzname()
    
    out.write("-- THIS FILE WAS GENERATED ON " + current_time + "\n")
    out.write("-- BASED ON FILE: " + input_file_path + "\n")
    out.write("-- YOU PROBABLY SHOULD NOT EDIT IT" + "\n")
    out.write("-- This file contains the VHDL look-up table for reloading coefficents on" + "\n")
    out.write("--   Xilinx FIR Compiler IP core." + "\n")

    # Write libraries
    out.write("Library IEEE; use IEEE.std_logic_1164.ALL, IEEE.numeric_std.all;\n\n")
    
    # Write entity 
    out.write("entity " + entity_name +  " is\n")
    out.write("    port (\n")
    out.write("        clk  : in  std_logic;\n")
    out.write("        addr : in  std_logic_vector(" + str(addr_bw - 1) + " downto 0);\n")
    out.write("        dout : out std_logic_vector(" + str(data_bw - 1) + " downto 0));\n")
    out.write("end "+ entity_name + ";\n\n")

    out.write("architecture behavioral of " + entity_name + " is\n")
    out.write("  type rom_type is array (0 to " + str(rom_size-1) + ") of std_logic_vector(" +
                  str(data_bw-1) + " downto 0);\n")
    out.write("  signal ROM : rom_type := (") 

    # Convert integer into binary based on data width 
    rom_str_arr = [] 
    for val in order: 
        rom_str_arr.append('"'+format(val,data_format) + '", ')

    # Pad ROM to address space 
    for i in range(0, rom_size-len(order)) : 
        rom_str_arr.append('"'+format(0,data_format) + '", ')

    # remove trailing comma 
    rom_str_arr[rom_size-1] = rom_str_arr[rom_size-1].replace(',','')

    # Write out ROM 
    for idx, val in enumerate(rom_str_arr):
        if not(idx % 4): 
            out.write("\n    " + val)
        else:
            out.write(val)
    out.write(" );\n\n")

    # Write process 
    out.write("begin\n")
    out.write("  process(clk)\n")
    out.write("  begin\n")
    out.write("    if rising_edge(clk) then\n")
    out.write("      dout <= ROM(to_integer(unsigned(addr)));\n")
    out.write("    end if;\n")
    out.write("  end process;\n")
    out.write("end behavioral;")

    out.close()

def main():
    """
    Function that is called if this module is called as a main function
    """
    args = parse_cl_vars()

    order = extract_reload_order(args)
    args["order"] = order
    generate_vhd(args)

    #print (order)
    
if __name__ == '__main__':
    main()