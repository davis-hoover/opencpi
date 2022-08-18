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

source $env(OCPI_CDK_DIR)/include/hdl/vivado-util.tcl

set stage               ""
set target_file         ""
set checkpoint          ""
set part                ""
set edif_file           ""
set constraints         ""
set pre_opt_hook        ""
set impl_opts           ""
set incr_comp           ""
set power_opt           ""
set post_place_opt      ""
set post_route_opt      ""
set phys_opt_opts       ""

parse_args $argv

create_project -part $part -force [file rootname $target_file]

# Read in an implementation checkpoint
if {[info exists checkpoint] && [string length $checkpoint] > 0} {
  read_checkpoint -part $part $checkpoint
}

# Read in container edif
if {[info exists edif_file] && [string length $edif_file] > 0} {
  read_edif $edif_file
}

# Open the design/link
set mode default
link_design -mode $mode -part $part

# Read in XDC constraints
if {[info exists constraints] && [string length $constraints] > 0} {
  puts "Loading XDC: $constraints"
  read_xdc $constraints
}

# Source platform pre-opt hook, if present
if {[info exists pre_opt_hook] && [string length $pre_opt_hook] > 0 && [file exist $pre_opt_hook]} {
  puts "Sourcing platform pre-opt hook: $pre_opt_hook"
  source $pre_opt_hook
}

# For each stage, allow loading of checkpoint
# Take current stage as parameter, and run the corresponding
# implementation step
set stage_start_time [clock seconds]
puts "Running Implementation stage $stage"
set command ""
switch $stage {
  opt {
    set command "opt_design $impl_opts ;"
    # Optionally run power optimization
    if {[info exists power_opt] && [string equal $power_opt true]} { 
      set command "$command power_opt_design"
    }
  }
  place {
    # Attempt to find an incremental-compile result to use. First look
    # for a post-route checkpoint. Then fall back on a post-place checkpoint.
    if {[info exists incr_comp] && [string equal $incr_comp true]} { 
      set incr_dcp $target_file
      set route_dcp [glob -nocomplain [file dirname $target_file]/*-route.dcp]
      if {[file exists $route_dcp]} {
        set incr_dcp $route_dcp
      }
      if {[file exist $incr_dcp]} {
        read_checkpoint -incremental $incr_dcp
      }
    }
    set command "$command place_design $impl_opts ;"
    if {[info exists post_place_opt] && [string equal $post_place_opt true]} { 
      set command "$command phys_opt_design $phys_opt_opts ;"
    }
  }
  route {
    set command "route_design $impl_opts ;"
    if {[info exists incr_comp] && [string equal $incr_comp true]} { 
      set command "$command report_incremental_reuse"
    }
    if {[info exists post_route_opt] && [string equal $post_route_opt true]} { 
      set command "$command phys_opt_design $phys_opt_opts ;"
    }
  }
  timing {
    set command "report_timing $impl_opts ;"
    set command "$command report_timing -rpx $target_file $impl_opts"
  }
  bit {
    set command "write_bitstream $target_file $impl_opts ;"
    set command "$command write_debug_probes -force [regsub {\.bit$} $target_file {.ltx}] ;"
    set command "$command report_utilization ;"
    set command "$command report_clock_networks ;"
    set command "$command report_design_analysis ;"
    set command "$command report_clocks ;"
  }
}

puts "Command: $command"
eval "$command"

set stage_end_time [clock seconds]

puts "Writing checkpoint for stage $stage"
if {![string equal $stage bit] && ![string equal $stage timing]} {
  write_checkpoint -force $target_file
}

set final_time [clock seconds]

puts "======Timing broken up into subtasks======
-----------------------------------------------------------------
|  Implementation Stage time: [expr $stage_end_time - $stage_start_time] seconds \t|
-----------------------------------------------------------------
| Post-stage operations time: [expr [clock seconds] - $stage_end_time] seconds \t|
-----------------------------------------------------------------
|                 Total time: [expr [clock seconds] - $stage_start_time] seconds \t|
-----------------------------------------------------------------"

