# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.

# This TCL script generates the verilog wrapper for the PS7 primitive, under Vivado.
# The ip_name is passed into this script as an argument.
# The generated Verilog "processor instantiator" is a highly parameterized wrapper
# instantiating the underlying PS7 primitive.  This wrapper does a variety of
# signal adaptations based on the parameters.
# The result of the script is that the wrapper verilog is copied to ".."
# And a file named wrapper-module is placed there with the name of the wrapper module
# which includes the version.
package require fileutil

set ip_name [lindex $argv 0]
set ip_part [lindex $argv 1]
set ip_module ${ip_name}_0

proc copy_sources {directory pattern} {
   # Find files in the specified directory
   set file_set [fileutil::findByPattern $directory -regexp $pattern]

   # Copy matching file set to gen directory
   file copy -force $file_set ../
}

create_project managed_ip_project managed_ip_project -force -part $ip_part
set_property target_language VHDL [current_project]

create_ip -name fir_compiler -vendor xilinx.com -library ip -module_name $ip_module

set_property -dict [list CONFIG.CoefficientVector {1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1} CONFIG.Coefficient_Reload {true} CONFIG.Sample_Frequency {4} CONFIG.Clock_Frequency {100} CONFIG.S_DATA_Has_FIFO {false} CONFIG.Has_ACLKEN {true} CONFIG.Has_ARESETn {true} CONFIG.Coefficient_Sets {1} CONFIG.Coefficient_Sign {Signed} CONFIG.Quantization {Integer_Coefficients} CONFIG.Coefficient_Width {16} CONFIG.Coefficient_Fractional_Bits {0} CONFIG.Coefficient_Structure {Inferred} CONFIG.Data_Width {16} CONFIG.Output_Rounding_Mode {Full_Precision} CONFIG.Output_Width {39} CONFIG.Filter_Architecture {Systolic_Multiply_Accumulate} CONFIG.ColumnConfig {3}] [get_ips $ip_module]

update_compile_order -fileset sources_1 

set_property generate_synth_checkpoint false [get_files $ip_module.xci]

generate_target all [get_files $ip_module.xci]

export_ip_user_files -of_object [get_files $ip_module.xci] -no_script -sync -force -quiet 

launch_runs synth_1 -jobs 8 
wait_on_run synth_1 
open_run synth_1 -name synth_1

# Vivado 2020.2 has a different resulting directory structure when generating the IP
if {[version -short] >= "2020.2"} {
  copy_sources managed_ip_project/managed_ip_project.gen/sources_1/ip/$ip_module reload_order
} else {
  copy_sources managed_ip_project/managed_ip_project.srcs/sources_1/ip/$ip_module reload_order
}

write_edif -security_mode all ../$ip_module.edf
write_vhdl -mode synth_stub ../$ip_module\_stub.vhd 
write_vhdl ../$ip_module\_sim.vhd
