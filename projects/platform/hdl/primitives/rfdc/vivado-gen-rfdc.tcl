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

set ip_part [lindex $argv 0]

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
create_ip -name usp_rf_data_converter -vendor xilinx.com -library ip -version 2.5 -module_name rfdc_ip

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
    CONFIG.ADC_Slice02_Enable {true} \
    CONFIG.ADC_Data_Type02 {1} \
    CONFIG.ADC_Decimation_Mode02 {40} \
    CONFIG.ADC_Mixer_Type02 {2} \
    CONFIG.ADC_Mixer_Mode02 {0} \
    CONFIG.ADC_Data_Width02 {1} \
    CONFIG.ADC_Coarse_Mixer_Freq02 {0} \
    CONFIG.ADC_RESERVED_1_02 {0} \
    CONFIG.ADC_Slice03_Enable {true} \
    CONFIG.ADC_Data_Type03 {1} \
    CONFIG.ADC_Decimation_Mode03 {40} \
    CONFIG.ADC_Mixer_Type03 {2} \
    CONFIG.ADC_Mixer_Mode03 {0} \
    CONFIG.ADC_Data_Width03 {1} \
    CONFIG.ADC_Coarse_Mixer_Freq03 {0} \
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
    CONFIG.ADC_Data_Width21 {1} CONFIG.ADC_Coarse_Mixer_Freq21 {0} \
    CONFIG.ADC_Slice22_Enable {true} \
    CONFIG.ADC_Data_Type22 {1} \
    CONFIG.ADC_Decimation_Mode22 {40} \
    CONFIG.ADC_Mixer_Type22 {2} \
    CONFIG.ADC_Mixer_Mode22 {0} \
    CONFIG.ADC_Data_Width22 {1} \
    CONFIG.ADC_Coarse_Mixer_Freq22 {0} \
    CONFIG.ADC_RESERVED_1_22 {0} \
    CONFIG.ADC_OBS22 {0} \
    CONFIG.ADC_Slice23_Enable {true} \
    CONFIG.ADC_Data_Type23 {1} \
    CONFIG.ADC_Decimation_Mode23 {40} \
    CONFIG.ADC_Mixer_Type23 {2} \
    CONFIG.ADC_Mixer_Mode23 {0} \
    CONFIG.ADC_Data_Width23 {1} \
    CONFIG.ADC_Coarse_Mixer_Freq23 {0} ] [get_ips rfdc_ip]
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
    CONFIG.DAC_RESERVED_1_33 {0}] [get_ips rfdc_ip]
generate_target all [get_files managed_ip_project/managed_ip_project.srcs/sources_1/ip/rfdc_ip/rfdc_ip.xci]

set gen_dir managed_ip_project/managed_ip_project.gen/sources_1/ip/rfdc_ip
copy_file $gen_dir/synth/rfdc_ip.v ../
copy_file $gen_dir/synth/rfdc_ip.xdc ../
copy_file $gen_dir/synth/rfdc_ip_address_decoder.v ../
copy_file $gen_dir/synth/rfdc_ip_axi_lite_ipif.v ../
copy_file $gen_dir/synth/rfdc_ip_bgt_fsm.v ../
copy_file $gen_dir/synth/rfdc_ip_block.v ../
copy_file $gen_dir/synth/rfdc_ip_clk_detection.v ../
copy_file $gen_dir/synth/rfdc_ip_clocks.xdc ../
copy_file $gen_dir/synth/rfdc_ip_constants_config.sv ../
copy_file $gen_dir/synth/rfdc_ip_counter_f.v ../
copy_file $gen_dir/synth/rfdc_ip_device_rom.sv ../
copy_file $gen_dir/synth/rfdc_ip_drp_access_ctrl.v ../
copy_file $gen_dir/synth/rfdc_ip_drp_arbiter.v ../
copy_file $gen_dir/synth/rfdc_ip_drp_arbiter_adc.v ../
copy_file $gen_dir/synth/rfdc_ip_drp_control.v ../
copy_file $gen_dir/synth/rfdc_ip_drp_control_top.v ../
copy_file $gen_dir/synth/rfdc_ip_irq_req_ack.v ../
copy_file $gen_dir/synth/rfdc_ip_irq_sync.v ../
copy_file $gen_dir/synth/rfdc_ip_ooc.xdc ../
copy_file $gen_dir/synth/rfdc_ip_overvol_irq.v ../
copy_file $gen_dir/synth/rfdc_ip_por_fsm.sv ../
copy_file $gen_dir/synth/rfdc_ip_por_fsm_disabled.sv ../
copy_file $gen_dir/synth/rfdc_ip_por_fsm_top.sv ../
copy_file $gen_dir/synth/rfdc_ip_powerup_state_irq.v ../
copy_file $gen_dir/synth/rfdc_ip_pselect_f.v ../
copy_file $gen_dir/synth/rfdc_ip_register_decode.v ../
copy_file $gen_dir/synth/rfdc_ip_rf_wrapper.v ../
copy_file $gen_dir/synth/rfdc_ip_rst_cnt.v ../
copy_file $gen_dir/synth/rfdc_ip_slave_attachment.v ../
copy_file $gen_dir/synth/rfdc_ip_tile_config.sv ../
copy_file $gen_dir/synth/rfdc_ipbufg_gt_ctrl.v ../
