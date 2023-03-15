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

# IP is generated with the following configuration only:
# part: xczu48dr-ffvg1517-2-e
# Each tile: 4Gsps, Fine Mixer, RF Port Real
#            AXI-Stream port(s) have both I and Q
# ADC Tile 224: Enabled, Clock Source Tile 224, 40x Decimation Mode,
#               Distribute Clock Input Refclk
# ADC Tile 225: Disabled
# ADC Tile 226: Ensabled, Clock Source Tile 226, 40x Decimation Mode,
#               Distribute Clock Input Refclk
# ADC Tile 227: Disabled
# DAC Tile 228: Disabled
# DAC Tile 229: Disabled
# DAC Tile 230: Enabled, Clock Source Tile 230, 40x Interpolation Mode,
#               Distribute Clock Input Refclk
# DAC Tile 231: Enabled, Clock Source Tile 230, 40x Interpolation Mode

set ip_name [lindex $argv 0]
set ip_part [lindex $argv 1]
set ip_module ${ip_name}_0

proc copy_file {file dest} {
    puts "COPYING $file to $dest"
    if {[file exists $file]} {
        puts "FILE $file exists"
	file copy $file $dest
        return 1
    }
    puts "FILE $file does not exist"
    return 0
}

create_project managed_ip_project managed_ip_project -ip -force -part $ip_part
create_ip -name usp_rf_data_converter -vendor xilinx.com -library ip -version 2.5 -module_name $ip_module

set_property -dict [list \
    CONFIG.ADC0_Sampling_Rate {4.0} \
    CONFIG.ADC0_Refclk_Freq {4000.000} \
    CONFIG.ADC0_Outclk_Freq {31.250} \
    CONFIG.ADC0_Fabric_Freq {100.000} \
    CONFIG.ADC0_Clock_Dist {1} \
    CONFIG.ADC_Data_Type00 {1} \
    CONFIG.ADC_Decimation_Mode00 {40} \
    CONFIG.ADC_Mixer_Type00 {2} \
    CONFIG.ADC_Mixer_Mode00 {0} \
    CONFIG.ADC_Data_Width00 {1} \
    CONFIG.ADC_Coarse_Mixer_Freq00 {0} \
    CONFIG.ADC_RESERVED_1_00 {0} \
    CONFIG.ADC_Data_Type01 {1} \
    CONFIG.ADC_Decimation_Mode01 {40} \
    CONFIG.ADC_Mixer_Type01 {2} \
    CONFIG.ADC_Mixer_Mode01 {0} \
    CONFIG.ADC_Data_Width01 {1} \
    CONFIG.ADC_Coarse_Mixer_Freq01 {0} \
    CONFIG.ADC_Slice02_Enable {false} \
    CONFIG.ADC_Decimation_Mode02 {0} \
    CONFIG.ADC_Mixer_Type02 {3} \
    CONFIG.ADC_Coarse_Mixer_Freq02 {3} \
    CONFIG.ADC_RESERVED_1_02 {0} \
    CONFIG.ADC_OBS02 {0} \
    CONFIG.ADC_Slice03_Enable {false} \
    CONFIG.ADC_Decimation_Mode03 {0} \
    CONFIG.ADC_Mixer_Type03 {3} \
    CONFIG.ADC_Coarse_Mixer_Freq03 {3} \
    CONFIG.ADC2_Enable {1} \
    CONFIG.ADC2_Sampling_Rate {4.0} \
    CONFIG.ADC2_Refclk_Freq {4000.000} \
    CONFIG.ADC2_Outclk_Freq {31.250} \
    CONFIG.ADC2_Fabric_Freq {100.000} \
    CONFIG.ADC2_Clock_Dist {1} \
    CONFIG.ADC_Slice20_Enable {true} \
    CONFIG.ADC_Data_Type20 {1} \
    CONFIG.ADC_Decimation_Mode20 {40} \
    CONFIG.ADC_Mixer_Type20 {2} \
    CONFIG.ADC_Mixer_Mode20 {0} \
    CONFIG.ADC_Data_Width20 {1} \
    CONFIG.ADC_Coarse_Mixer_Freq20 {0} \
    CONFIG.ADC_RESERVED_1_20 {0} \
    CONFIG.ADC_Slice21_Enable {true} \
    CONFIG.ADC_Data_Type21 {1} \
    CONFIG.ADC_Decimation_Mode21 {40} \
    CONFIG.ADC_Mixer_Type21 {2} \
    CONFIG.ADC_Mixer_Mode21 {0} \
    CONFIG.ADC_Data_Width21 {1} \
    CONFIG.ADC_Coarse_Mixer_Freq21 {0} \
    CONFIG.ADC_RESERVED_1_22 {0} \
    CONFIG.ADC_OBS22 {0}] [get_ips $ip_module]

set_property -dict [list \
    CONFIG.DAC2_Enable {1} \
    CONFIG.DAC2_Sampling_Rate {4.0} \
    CONFIG.DAC2_Refclk_Freq {4000.000} \
    CONFIG.DAC2_Outclk_Freq {31.250} \
    CONFIG.DAC2_Fabric_Freq {100.000} \
    CONFIG.DAC2_Clock_Dist {1} \
    CONFIG.DAC_Slice20_Enable {true} \
    CONFIG.DAC_Data_Width20 {2} \
    CONFIG.DAC_Interpolation_Mode20 {40} \
    CONFIG.DAC_Mixer_Type20 {2} \
    CONFIG.DAC_Mixer_Mode20 {0} \
    CONFIG.DAC_Coarse_Mixer_Freq20 {3} \
    CONFIG.DAC_RESERVED_1_20 {0} \
    CONFIG.DAC_RESERVED_1_21 {0} \
    CONFIG.DAC_Slice22_Enable {true} \
    CONFIG.DAC_Data_Width22 {2} \
    CONFIG.DAC_Interpolation_Mode22 {40} \
    CONFIG.DAC_Mixer_Type22 {2} \
    CONFIG.DAC_Mixer_Mode22 {0} \
    CONFIG.DAC_Coarse_Mixer_Freq22 {3} \
    CONFIG.DAC_RESERVED_1_22 {0} \
    CONFIG.DAC_RESERVED_1_23 {0} \
    CONFIG.DAC3_Enable {1} \
    CONFIG.DAC3_Sampling_Rate {4.0} \
    CONFIG.DAC3_Refclk_Freq {4000.000} \
    CONFIG.DAC3_Outclk_Freq {31.250} \
    CONFIG.DAC3_Fabric_Freq {100.000} \
    CONFIG.DAC3_Clock_Source {6} \
    CONFIG.DAC_Slice30_Enable {true} \
    CONFIG.DAC_Data_Width30 {2} \
    CONFIG.DAC_Interpolation_Mode30 {40} \
    CONFIG.DAC_Mixer_Type30 {2} \
    CONFIG.DAC_Mixer_Mode30 {0} \
    CONFIG.DAC_Coarse_Mixer_Freq30 {3} \
    CONFIG.DAC_RESERVED_1_30 {0} \
    CONFIG.DAC_RESERVED_1_31 {0} \
    CONFIG.DAC_Slice32_Enable {true} \
    CONFIG.DAC_Data_Width32 {2} \
    CONFIG.DAC_Interpolation_Mode32 {40} \
    CONFIG.DAC_Mixer_Type32 {2} \
    CONFIG.DAC_Mixer_Mode32 {0} \
    CONFIG.DAC_Coarse_Mixer_Freq32 {3} \
    CONFIG.DAC_RESERVED_1_32 {0} \
    CONFIG.DAC_RESERVED_1_33 {0}] [get_ips $ip_module]

set ip_dir managed_ip_project/managed_ip_project.srcs/sources_1/ip/$ip_module
generate_target all [get_files $ip_dir/$ip_module.xci]
create_ip_run [get_files -of_objects [get_fileset sources_1] $ip_dir/$ip_module.xci]
launch_runs ${ip_module}_synth_1 -jobs 8
wait_on_run ${ip_module}_synth_1
open_run ${ip_module}_synth_1 -name ${ip_module}_synth_1
write_edif -security_mode all ../$ip_module.edf
write_vhdl -mode synth_stub $ip_dir/${ip_module}_stub.vhdl -force
