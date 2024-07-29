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

################
# Script Setup #
################
source $env(OCPI_CDK_DIR)/include/hdl/vivado-util.tcl

# Arguments
## Generic
set assembly_name                     ""
set part                              ""
## Optimization
set checkpoint_after_opt              0
set constraints_for_opt               ""
set options_for_opt_design            ""
set pre_opt_hook                      ""
set run_opt_power_opt_design          ""
## Placement
set checkpoint_after_place            0
set options_for_place_design          ""
set options_for_place_phys_opt_design ""
set run_place_phys_opt_design         ""
## Routing
set checkpoint_after_route            1
set options_for_route_design          ""
set options_for_route_phys_opt_design ""
set run_route_phys_opt_design         ""
## Timing
set options_for_report_timing         ""
## Bitstream
set constraints_for_bitstream         ""
set options_for_write_bitstream       ""

parse_args $argv

# Functions
## Print out the amount of time taken for the current stage to finish in a
## common way.
##  * `stage`:      The name of the stage.
##  * `start_time`: The time that the stage started.
##  * `end_time`:   The time that the stage ended.
proc print_stage_duration {stage start_time end_time} {
  set first_line_whitespace [string repeat " " 5]
  set last_line_whitespace [string repeat " " [string length $stage]]
  set banner_fill [string repeat "=" [string length $stage]]
  puts "
======| Finished: $stage |======
  $stage time:$first_line_whitespace [expr $end_time - $start_time] seconds
  post-$stage time: [expr [clock seconds] - $end_time] seconds
  total time:$last_line_whitespace [expr [clock seconds] - $start_time] seconds
==========================$banner_fill
"
}

## Load all constraints in a given string.
##  * `constraints`: String of the form "file_path?assignments".
##    * `assignments` is a list of variable assignments of the form `var=val`,
##      each separated by one of `\`, `;`, or `&`.
proc load_constraints {constraints} {
  if {[info exists constraints] && [string length $constraints] > 0} {
    puts "Loading XDC: $constraints"
    set words [split $constraints ?]
    set constraints_file [lindex $words 0]
    set assignments [split [lindex $words 1] \;&]
    foreach assignment $assignments {
        lassign [split $assignment =] var val
        set $var $val
        puts "setting var:$var to val:$val"
    }
    # unmanaged means tcl control statements (if, loop, source) are allowed in the file
    # https://support.xilinx.com/s/question/0D52E00006hpkDSSAY/readxdc-unmanaged-?
    read_xdc -unmanaged $constraints_file
  }
}

## Write a checkpoint for a given stage.
##  * `stage`:  The name of the stage.
##  * `enable`: `1` if the write should happen, `0` if it shouldn't.
proc optional_write_checkpoint {assembly_name stage enable} {
  if {$enable} {
    set write_checkpoint_start_time [clock seconds]
    write_checkpoint -force $assembly_name-$stage.dcp
    set write_checkpoint_end_time [clock seconds]
    print_stage_duration \
      "$stage-write-checkpoint" \
      $write_checkpoint_start_time \
      $write_checkpoint_end_time
  }
}

#################
# Project Setup #
#################
create_project -part $part -force $assembly_name
set_property top $assembly_name [current_fileset]

# Work out what stage the build needs to start at
set checkpoint ""
set stage ""
if {![file exists $assembly_name-opt.dcp]} {
  set checkpoint "synth"
  set stage "opt"
} elseif {![file exists $assembly_name-place.dcp]} {
  set checkpoint "opt"
  set stage "place"
} elseif {![file exists $assembly_name-route.dcp]} {
  set checkpoint "place"
  set stage "route"
} elseif {![file exists $assembly_name.rpx]} {
  set checkpoint "route"
  set stage "timing"
} elseif {![file exists $assembly_name.bit] || ![file exists $assembly_name.ltx]} {
  set checkpoint "route"
  set stage "bit"
}
# Open design (supports continuation from cancelled build)
set open_start_time [clock seconds]
if {[string equal $checkpoint "synth"]} {
  read_edif $assembly_name.edf
  link_design -mode default -part $part
} else {
  open_checkpoint $assembly_name-$checkpoint.dcp
}
set open_end_time [clock seconds]
print_stage_duration "$stage-open-checkpoint" $open_start_time $open_end_time

################
# Optimization #
################
if {[string equal $stage "opt"]} {
  set opt_start_time [clock seconds]
  # Read in XDC constraints
  load_constraints $constraints_for_opt
  # Source pre-opt hook
  if {[info exists pre_opt_hook] && [string length $pre_opt_hook] > 0 && [file exist $pre_opt_hook]} {
    puts "Sourcing pre-opt hook: $pre_opt_hook"
    source $pre_opt_hook
  }
  # Optimize
  opt_design {*}$options_for_opt_design
  # Optionally run power optimization
  if {[info exists run_opt_power_opt_design] && [string equal $run_opt_power_opt_design true]} {
    power_opt_design
  }
  # Finish
  set opt_end_time [clock seconds]
  print_stage_duration $stage $opt_start_time $opt_end_time
  optional_write_checkpoint $assembly_name $stage $checkpoint_after_opt
  set stage "place"
} else {
  puts "Warning: $assembly_name-opt.dcp exists - skipping `opt_design`"
}

#############
# Placement #
#############
if {[string equal $stage "place"]} {
  set place_start_time [clock seconds]
  # Place
  place_design {*}$options_for_place_design
  # Optionally run physical optimization
  if {[info exists run_place_phys_opt_design] && [string equal $run_place_phys_opt_design true]} {
    phys_opt_design {*}$options_for_place_phys_opt_design
  }
  # Finish
  set place_end_time [clock seconds]
  print_stage_duration $stage $place_start_time $place_end_time
  optional_write_checkpoint $assembly_name $stage $checkpoint_after_place
  set stage "route"
} else {
  puts "Warning: $assembly_name-place.dcp exists - skipping `place_design`"
}

###########
# Routing #
###########
if {[string equal $stage "route"]} {
  set route_start_time [clock seconds]
  # Route
  route_design {*}$options_for_route_design
  # Optionally run physical optimization
  if {[info exists run_route_phys_opt_design] && [string equal $run_route_phys_opt_design true]} {
    phys_opt_design {*}$options_for_route_phys_opt_design
  }
  # Finish
  set route_end_time [clock seconds]
  print_stage_duration $stage $route_start_time $route_end_time
  optional_write_checkpoint $assembly_name $stage $checkpoint_after_route
  set stage "timing"
} else {
  puts "Warning: $assembly_name-route.dcp exists - skipping `route_design`"
}

##########
# Timing #
##########
if {[string equal $stage "timing"]} {
  set timing_start_time [clock seconds]
  # Timing
  report_timing -rpx $assembly_name.rpx {*}$options_for_report_timing
  # Finish
  set timing_end_time [clock seconds]
  print_stage_duration $stage $timing_start_time $timing_end_time
  set stage "bit"
} else {
  puts "Warning: $assembly_name.rpx exists - skipping `report_timing`"
}

#############
# Bitstream #
#############
if {[string equal $stage "bit"]} {
  set bitstream_start_time [clock seconds]
  # Read in XDC constraints
  load_constraints $constraints_for_bitstream
  # Bitstream and debug probes
  write_bitstream $assembly_name.bit {*}$options_for_write_bitstream
  write_debug_probes -force $assembly_name.ltx
  # Reports
  report_utilization
  report_clock_networks
  report_design_analysis
  report_clocks
  # Finish
  set bitstream_end_time [clock seconds]
  print_stage_duration $stage $bitstream_start_time $bitstream_end_time
} else {
  puts "Warning: $assembly_name.bit exists - skipping `write_bitstream`"
}
