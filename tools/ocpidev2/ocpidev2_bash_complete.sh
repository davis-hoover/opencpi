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

get_compgen_str_for_verb() {
  str=$1
  comp_line=$2
  #verbs=("build" "clean" "register" "unregister" "show")
  verbs=("show")
  for verb in "${verbs[@]}"; do
    if [[ $comp_line == *"$verb"* ]]; then
      break;
    else
      str="$str $verb"
    fi
  done
  echo $str
}

get_compgen_str_for_option_only_allowed_once() {
  str=$1
  option=$2
  comp_line=$3
  if [[ $comp_line != *"$option"* ]]; then
    str="$str $option"
  fi
  echo $str
}

get_compgen_str_for_long_short_option_only_allowed_once() {
  str=$1
  long=$2
  short=$3
  comp_line=$4
  if [[ $comp_line != *"$long"* ]]; then
    if [[ $comp_line != *"$short"* ]]; then
      str="$str $short $long"
    fi
  fi
  echo $str
}

_ocpidev2()
{
  str=""
  #str=$(get_compgen_str_for_option_only_allowed_once "$str" "-d" "$COMP_LINE")
  str=$(get_compgen_str_for_long_short_option_only_allowed_once "$str" "-h" "--help" "$COMP_LINE")
  str=$(get_compgen_str_for_long_short_option_only_allowed_once "$str" "-v" "--verbose" "$COMP_LINE")
  if [ "$3" == "build" ]; then
    str=$(get_compgen_str_for_long_short_option_only_allowed_once "$str" "-j" "--jobs" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "--hdl-platform" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "--hdl-target" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "--rcc-platform" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "--rcc-platform" "$COMP_LINE")
    COMPREPLY=( $(compgen -W "$str" -- "$2") )
  elif [ "$3" == "--hdl-target" ]; then
    # these are the values hardcoded in abstract2.py get_target(), for now (BAD! - TODO fix this)
    COMPREPLY=( $(compgen -W "zynq zynq_ise zynq_ultra virtex6" -- "$2") )
  elif [ "$3" == "--hdl-platform" ]; then
    COMPREPLY=( $(compgen -W "$(ocpidev2 show hdl platforms | sed "s/.*\.//g")" -- "$2") )
  elif [ "$3" == "--rcc-platform" ]; then
    COMPREPLY=( $(compgen -W "$(ocpidev2 show hdl platforms | sed "s/.*\.//g")" -- "$2") )
  elif [ "$3" == "show" ]; then
    #COMPREPLY=( $(compgen -W "registry projects components workers libraries hdl rcc" -- "$2") )
    COMPREPLY=( $(compgen -W "$str registry projects components workers libraries" -- "$2") )
  elif [ "$3" == "hdl" ]; then
    COMPREPLY=( $(compgen -W "workers" -- "$2") )
  elif [ "$3" == "rcc" ]; then
    COMPREPLY=( $(compgen -W "workers" -- "$2") )
  elif [ "$3" == "-d" ]; then
    COMPREPLY=( $(compgen -d -S / -- "$2") )
  elif [ "$3" == "clean" ]; then
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "-d" "$COMP_LINE")
    COMPREPLY=( $(compgen -W "$str" -- "$2") )
  elif [ "$3" == "unittest" ]; then
    COMPREPLY=()
  elif [ "$3" == "ocpidev2" ]; then
    str=$(get_compgen_str_for_verb "$str" "$COMP_LINE")
    COMPREPLY=( $(compgen -W "$str" -- "$2") )
  elif [ "$3" == "registry" ]; then
    COMPREPLY=( $(compgen -W "$str" -- "$2") )
  elif [ "$3" == "projects" ]; then
    COMPREPLY=( $(compgen -W "$str" -- "$2") )
  elif [ "$3" == "components" ]; then
    COMPREPLY=( $(compgen -W "$str" -- "$2") )
  elif [ "$3" == "workers" ]; then
    COMPREPLY=( $(compgen -W "$str" -- "$2") )
  elif [ "$3" == "libraries" ]; then
    COMPREPLY=( $(compgen -W "$str" -- "$2") )
  elif [ "$3" == "register" ]; then
    COMPREPLY=( $(compgen -W "project" -- "$2") )
  elif [ "$3" == "unregister" ]; then
    COMPREPLY=( $(compgen -W "project" -- "$2") )
  else
    str=$(get_compgen_str_for_verb "$str" "$COMP_LINE")
    COMPREPLY=( $(compgen -W "$str" -- "$2") )
  fi
  # below line necessary for -d argument
  [[ $COMPREPLY == */ ]] && compopt -o nospace
}
complete -F _ocpidev2 ocpidev2
