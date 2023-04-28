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

set_property -dict [ list \
    CONFIG.ADC0_Clock_Dist {0} \
    CONFIG.ADC0_Fabric_Freq {90.000} \
    CONFIG.ADC0_Outclk_Freq {225.000} \
    CONFIG.ADC0_PLL_Enable {false} \
    CONFIG.ADC0_Refclk_Freq {3600.000} \
    CONFIG.ADC0_Sampling_Rate {3.600000} \
    CONFIG.ADC1_Clock_Dist {0} \
    CONFIG.ADC1_Clock_Source {1} \
    CONFIG.ADC1_Enable {1} \
    CONFIG.ADC1_Fabric_Freq {90.000} \
    CONFIG.ADC1_Outclk_Freq {225.000} \
    CONFIG.ADC1_PLL_Enable {false} \
    CONFIG.ADC1_Refclk_Freq {3600.000} \
    CONFIG.ADC1_Sampling_Rate {3.600000} \
    CONFIG.ADC2_Clock_Dist {0} \
    CONFIG.ADC2_Clock_Source {2} \
    CONFIG.ADC2_Enable {1} \
    CONFIG.ADC2_Fabric_Freq {90.000} \
    CONFIG.ADC2_Outclk_Freq {225.000} \
    CONFIG.ADC2_PLL_Enable {false} \
    CONFIG.ADC2_Refclk_Freq {3600.000} \
    CONFIG.ADC2_Sampling_Rate {3.600000} \
    CONFIG.ADC3_Clock_Source {3} \
    CONFIG.ADC3_Enable {1} \
    CONFIG.ADC3_Fabric_Freq {90.000} \
    CONFIG.ADC3_Outclk_Freq {225.000} \
    CONFIG.ADC3_PLL_Enable {false} \
    CONFIG.ADC3_Refclk_Freq {3600.000} \
    CONFIG.ADC3_Sampling_Rate {3.600000} \
    CONFIG.ADC_CalOpt_Mode00 {1} \
    CONFIG.ADC_CalOpt_Mode01 {1} \
    CONFIG.ADC_CalOpt_Mode02 {1} \
    CONFIG.ADC_CalOpt_Mode03 {1} \
    CONFIG.ADC_CalOpt_Mode12 {1} \
    CONFIG.ADC_CalOpt_Mode13 {1} \
    CONFIG.ADC_CalOpt_Mode20 {1} \
    CONFIG.ADC_CalOpt_Mode21 {1} \
    CONFIG.ADC_CalOpt_Mode22 {1} \
    CONFIG.ADC_CalOpt_Mode23 {1} \
    CONFIG.ADC_CalOpt_Mode32 {1} \
    CONFIG.ADC_CalOpt_Mode33 {1} \
    CONFIG.ADC_Coarse_Mixer_Freq00 {0} \
    CONFIG.ADC_Coarse_Mixer_Freq01 {0} \
    CONFIG.ADC_Coarse_Mixer_Freq02 {0} \
    CONFIG.ADC_Coarse_Mixer_Freq03 {0} \
    CONFIG.ADC_Coarse_Mixer_Freq12 {0} \
    CONFIG.ADC_Coarse_Mixer_Freq13 {0} \
    CONFIG.ADC_Coarse_Mixer_Freq20 {0} \
    CONFIG.ADC_Coarse_Mixer_Freq21 {0} \
    CONFIG.ADC_Coarse_Mixer_Freq22 {0} \
    CONFIG.ADC_Coarse_Mixer_Freq23 {0} \
    CONFIG.ADC_Coarse_Mixer_Freq32 {0} \
    CONFIG.ADC_Coarse_Mixer_Freq33 {0} \
    CONFIG.ADC_Data_Type00 {1} \
    CONFIG.ADC_Data_Type01 {1} \
    CONFIG.ADC_Data_Type02 {1} \
    CONFIG.ADC_Data_Type03 {1} \
    CONFIG.ADC_Data_Type12 {1} \
    CONFIG.ADC_Data_Type13 {1} \
    CONFIG.ADC_Data_Type20 {1} \
    CONFIG.ADC_Data_Type21 {1} \
    CONFIG.ADC_Data_Type22 {1} \
    CONFIG.ADC_Data_Type23 {1} \
    CONFIG.ADC_Data_Type32 {1} \
    CONFIG.ADC_Data_Type33 {1} \
    CONFIG.ADC_Data_Width00 {1} \
    CONFIG.ADC_Data_Width01 {1} \
    CONFIG.ADC_Data_Width02 {1} \
    CONFIG.ADC_Data_Width03 {1} \
    CONFIG.ADC_Data_Width12 {1} \
    CONFIG.ADC_Data_Width13 {1} \
    CONFIG.ADC_Data_Width20 {1} \
    CONFIG.ADC_Data_Width21 {1} \
    CONFIG.ADC_Data_Width22 {1} \
    CONFIG.ADC_Data_Width23 {1} \
    CONFIG.ADC_Data_Width32 {1} \
    CONFIG.ADC_Data_Width33 {1} \
    CONFIG.ADC_Decimation_Mode00 {40} \
    CONFIG.ADC_Decimation_Mode01 {40} \
    CONFIG.ADC_Decimation_Mode02 {40} \
    CONFIG.ADC_Decimation_Mode03 {40} \
    CONFIG.ADC_Decimation_Mode12 {40} \
    CONFIG.ADC_Decimation_Mode13 {40} \
    CONFIG.ADC_Decimation_Mode20 {40} \
    CONFIG.ADC_Decimation_Mode21 {40} \
    CONFIG.ADC_Decimation_Mode22 {40} \
    CONFIG.ADC_Decimation_Mode23 {40} \
    CONFIG.ADC_Decimation_Mode32 {40} \
    CONFIG.ADC_Decimation_Mode33 {40} \
    CONFIG.ADC_Dither00 {true} \
    CONFIG.ADC_Dither01 {true} \
    CONFIG.ADC_Dither02 {true} \
    CONFIG.ADC_Dither03 {true} \
    CONFIG.ADC_Dither12 {true} \
    CONFIG.ADC_Dither13 {true} \
    CONFIG.ADC_Dither20 {true} \
    CONFIG.ADC_Dither21 {true} \
    CONFIG.ADC_Dither22 {true} \
    CONFIG.ADC_Dither23 {true} \
    CONFIG.ADC_Dither32 {true} \
    CONFIG.ADC_Dither33 {true} \
    CONFIG.ADC_Mixer_Mode00 {0} \
    CONFIG.ADC_Mixer_Mode01 {0} \
    CONFIG.ADC_Mixer_Mode02 {0} \
    CONFIG.ADC_Mixer_Mode03 {0} \
    CONFIG.ADC_Mixer_Mode12 {0} \
    CONFIG.ADC_Mixer_Mode13 {0} \
    CONFIG.ADC_Mixer_Mode20 {0} \
    CONFIG.ADC_Mixer_Mode21 {0} \
    CONFIG.ADC_Mixer_Mode22 {0} \
    CONFIG.ADC_Mixer_Mode23 {0} \
    CONFIG.ADC_Mixer_Mode32 {0} \
    CONFIG.ADC_Mixer_Mode33 {0} \
    CONFIG.ADC_Mixer_Type00 {2} \
    CONFIG.ADC_Mixer_Type01 {2} \
    CONFIG.ADC_Mixer_Type02 {2} \
    CONFIG.ADC_Mixer_Type03 {2} \
    CONFIG.ADC_Mixer_Type12 {2} \
    CONFIG.ADC_Mixer_Type13 {2} \
    CONFIG.ADC_Mixer_Type20 {2} \
    CONFIG.ADC_Mixer_Type21 {2} \
    CONFIG.ADC_Mixer_Type22 {2} \
    CONFIG.ADC_Mixer_Type23 {2} \
    CONFIG.ADC_Mixer_Type32 {2} \
    CONFIG.ADC_Mixer_Type33 {2} \
    CONFIG.ADC_NCO_Freq00 {0.01} \
    CONFIG.ADC_NCO_Freq01 {0.01} \
    CONFIG.ADC_NCO_Freq02 {0.01} \
    CONFIG.ADC_NCO_Freq03 {0.01} \
    CONFIG.ADC_NCO_Freq12 {0.01} \
    CONFIG.ADC_NCO_Freq13 {0.01} \
    CONFIG.ADC_NCO_Freq20 {0.01} \
    CONFIG.ADC_NCO_Freq21 {0.01} \
    CONFIG.ADC_NCO_Freq22 {0.01} \
    CONFIG.ADC_NCO_Freq23 {0.01} \
    CONFIG.ADC_NCO_Freq32 {0.01} \
    CONFIG.ADC_NCO_Freq33 {0.01} \
    CONFIG.ADC_OBS02 {false} \
    CONFIG.ADC_OBS22 {false} \
    CONFIG.ADC_OBS32 {false} \
    CONFIG.ADC_RESERVED_1_00 {false} \
    CONFIG.ADC_RESERVED_1_02 {false} \
    CONFIG.ADC_RESERVED_1_10 {false} \
    CONFIG.ADC_RESERVED_1_12 {false} \
    CONFIG.ADC_RESERVED_1_20 {false} \
    CONFIG.ADC_RESERVED_1_22 {false} \
    CONFIG.ADC_RESERVED_1_30 {false} \
    CONFIG.ADC_RESERVED_1_32 {false} \
    CONFIG.ADC_Slice02_Enable {true} \
    CONFIG.ADC_Slice03_Enable {true} \
    CONFIG.ADC_Slice12_Enable {true} \
    CONFIG.ADC_Slice13_Enable {true} \
    CONFIG.ADC_Slice20_Enable {true} \
    CONFIG.ADC_Slice21_Enable {true} \
    CONFIG.ADC_Slice22_Enable {true} \
    CONFIG.ADC_Slice23_Enable {true} \
    CONFIG.ADC_Slice30_Enable {false} \
    CONFIG.ADC_Slice31_Enable {false} \
    CONFIG.ADC_Slice32_Enable {true} \
    CONFIG.ADC_Slice33_Enable {true} \
    CONFIG.DAC2_Clock_Dist {1} \
    CONFIG.DAC2_Enable {1} \
    CONFIG.DAC2_Fabric_Freq {90.000} \
    CONFIG.DAC2_Outclk_Freq {225.000} \
    CONFIG.DAC2_PLL_Enable {false} \
    CONFIG.DAC2_Refclk_Freq {3600.000} \
    CONFIG.DAC2_Sampling_Rate {3.600000} \
    CONFIG.DAC3_Clock_Source {6} \
    CONFIG.DAC3_Enable {1} \
    CONFIG.DAC3_Fabric_Freq {90.000} \
    CONFIG.DAC3_Outclk_Freq {225.000} \
    CONFIG.DAC3_PLL_Enable {false} \
    CONFIG.DAC3_Refclk_Freq {3600.000} \
    CONFIG.DAC3_Sampling_Rate {3.600000} \
    CONFIG.DAC_Coarse_Mixer_Freq20 {3} \
    CONFIG.DAC_Coarse_Mixer_Freq30 {3} \
    CONFIG.DAC_Coarse_Mixer_Freq32 {3} \
    CONFIG.DAC_Data_Width30 {2} \
    CONFIG.DAC_Data_Width32 {2} \
    CONFIG.DAC_Interpolation_Mode20 {1} \
    CONFIG.DAC_Interpolation_Mode30 {40} \
    CONFIG.DAC_Interpolation_Mode32 {40} \
    CONFIG.DAC_Invsinc_Ctrl30 {true} \
    CONFIG.DAC_Invsinc_Ctrl32 {true} \
    CONFIG.DAC_Mixer_Mode30 {0} \
    CONFIG.DAC_Mixer_Mode32 {0} \
    CONFIG.DAC_Mixer_Type20 {1} \
    CONFIG.DAC_Mixer_Type30 {2} \
    CONFIG.DAC_Mixer_Type32 {2} \
    CONFIG.DAC_NCO_Freq30 {0.3} \
    CONFIG.DAC_NCO_Freq32 {0.020} \
    CONFIG.DAC_RESERVED_1_20 {false} \
    CONFIG.DAC_RESERVED_1_21 {false} \
    CONFIG.DAC_RESERVED_1_22 {false} \
    CONFIG.DAC_RESERVED_1_23 {false} \
    CONFIG.DAC_RESERVED_1_30 {false} \
    CONFIG.DAC_RESERVED_1_31 {false} \
    CONFIG.DAC_RESERVED_1_32 {false} \
    CONFIG.DAC_RESERVED_1_33 {false} \
    CONFIG.DAC_Slice20_Enable {true} \
    CONFIG.DAC_Slice30_Enable {true} \
    CONFIG.DAC_Slice32_Enable {true} ] [get_ips $ip_module]
 
set ip_dir managed_ip_project/managed_ip_project.srcs/sources_1/ip/$ip_module
generate_target all [get_files $ip_dir/$ip_module.xci]
create_ip_run [get_files -of_objects [get_fileset sources_1] $ip_dir/$ip_module.xci]
launch_runs ${ip_module}_synth_1 -jobs 8
wait_on_run ${ip_module}_synth_1
open_run ${ip_module}_synth_1 -name ${ip_module}_synth_1
write_edif -security_mode all -force ../$ip_module.edf
write_vhdl -mode synth_stub $ip_dir/${ip_module}_stub.vhdl -force
