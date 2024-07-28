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
  verbs=("show unittest")
  for verb in "${verbs[@]}"; do
    if [[ $comp_line == *"$verb"* ]]; then
      continue;
    else
      str="$str $verb"
    fi
  done
  echo $str
}

get_compgen_str_for_noun() {
  str=$1
  comp_line=$2
  nouns=("registry" "projects" "components" "workers" "libraries")
  for noun in "${nouns[@]}"; do
    if [[ $comp_line == *"$noun"* ]]; then
      continue;
    else
      str="$str $noun"
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

#  elif [ "$3" == "adapter" ]; then
#    assets=$(echo $(printf "%s\n" $(ocpidev2 show adapters --suppress-warn | sed "s/.*\.//g")) | uniq)
#    COMPREPLY=( $(compgen -W "$assets" -- "$2") )

_ocpidev2()
{
  str=""
  str=$(get_compgen_str_for_long_short_option_only_allowed_once "$str" "-h " "--help " "$COMP_LINE")
  #str=$(get_compgen_str_for_long_short_option_only_allowed_once "$str" "-v " "--verbose" "$COMP_LINE")
  if [ "$3" == "show" ]; then
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "adapter" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "adapters" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "application" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "applications" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "assembly" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "assemblies" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "card" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "cards" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "component" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "components" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "device" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "devices" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "hdl" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "library" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "libraries" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "platform" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "platforms" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "primitive" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "primitives" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "project" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "projects" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "registry" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "rcc" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "slot" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "slots" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "test" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "tests" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "worker" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "workers" "$COMP_LINE")
    COMPREPLY=( $(compgen -W "$str" -- "$2") )
  elif [ "$3" == "hdl" ]; then
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "adapter" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "adapters" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "assembly" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "assemblies" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "card" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "cards" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "device" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "devices" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "library" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "libraries" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "platform" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "platforms" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "primitive" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "primitives" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "slot" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "slots" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "target" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "targets" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "worker" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "workers" "$COMP_LINE")
    COMPREPLY=( $(compgen -W "$str" -- "$2") )
  elif [ "$3" == "primitive" ]; then
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "core" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "cores" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "library" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "libraries" "$COMP_LINE")
  elif [ "$3" == "rcc" ]; then
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "platform" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "platforms" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "target" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "targets" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "worker" "$COMP_LINE")
    str=$(get_compgen_str_for_option_only_allowed_once "$str" "workers" "$COMP_LINE")
    COMPREPLY=( $(compgen -W "$str" -- "$2") )
  elif [ "$3" == "-d" ]; then
    COMPREPLY=( $(compgen -d -S / -- "$2") )
  elif [ "$3" == "unittest" ]; then
    COMPREPLY=( $(compgen -W "-v --verbose" -- "$2") )
  elif [ "$3" == "ocpidev2" ]; then
    str=$(get_compgen_str_for_verb "$str" "$COMP_LINE")
    COMPREPLY=( $(compgen -W "$str" -- "$2") )
  elif [ "$3" == "registry" ]; then
    str=$(get_compgen_str_for_long_short_option_only_allowed_once "$str" "-v " "--verbose " "$COMP_LINE")
    COMPREPLY=( $(compgen -W "$str -d" -- "$2") )
  elif [ "$3" == "project" ]; then
    assets=$(echo $(printf "%s\n" $(ocpidev2 show projects --suppress-warn | sed "s/.*\.//g")) | uniq)
    COMPREPLY=( $(compgen -W "$assets" -- "$2") )
  elif [ "$3" == "component" ]; then
    assets=$(echo $(printf "%s\n" $(ocpidev2 show components --suppress-warn | sed "s/.*\.//g")) | uniq)
    COMPREPLY=( $(compgen -W "$assets" -- "$2") )
  elif [ "$3" == "workers" ]; then
    str=$(get_compgen_str_for_long_short_option_only_allowed_once "$str" "-v " "--verbose " "$COMP_LINE")
    COMPREPLY=( $(compgen -W "$str -d" -- "$2") )
  elif [ "$3" == "register" ]; then
    str=$(get_compgen_str_for_long_short_option_only_allowed_once "$str" "-v " "--verbose " "$COMP_LINE")
    COMPREPLY=( $(compgen -W "$str project" -- "$2") )
  elif [ "$3" == "unregister" ]; then
    COMPREPLY=( $(compgen -W "project" -- "$2") )
  elif [ "$3" == "-h" ]; then
    COMPREPLY=( $(compgen -W "" -- "$2") )
  elif [ "$3" == "--help" ]; then
    COMPREPLY=( $(compgen -W "" -- "$2") )
  elif [ "$3" == "-v" ]; then
    str=$(get_compgen_str_for_long_short_option_only_allowed_once "" "-v " "--verbose " "$COMP_LINE")
    if [[ $COMP_LINE != *"unittest"* ]]; then
      COMPREPLY=( $(compgen -W "$str -d" -- "$2") )
    else
      COMPREPLY=( $(compgen -W "$str" -- "$2") )
    fi
  elif [ "$3" == "--verbose" ]; then
    str=$(get_compgen_str_for_long_short_option_only_allowed_once "" "-v " "--verbose " "$COMP_LINE")
    if [[ $COMP_LINE != *"unittest"* ]]; then
      COMPREPLY=( $(compgen -W "$str -d" -- "$2") )
    else
      COMPREPLY=( $(compgen -W "$str" -- "$2") )
    fi
  elif [ "$3" == "applications" ]; then
    str=$(get_compgen_str_for_long_short_option_only_allowed_once "$str" "-v " "--verbose " "$COMP_LINE")
    COMPREPLY=( $(compgen -W "$str -d" -- "$2") )
  elif [ "$3" == "components" ]; then
    str=$(get_compgen_str_for_long_short_option_only_allowed_once "$str" "-v " "--verbose " "$COMP_LINE")
    COMPREPLY=( $(compgen -W "$str -d" -- "$2") )
  elif [ "$3" == "libraries" ]; then
    str=$(get_compgen_str_for_long_short_option_only_allowed_once "$str" "-v " "--verbose " "$COMP_LINE")
    COMPREPLY=( $(compgen -W "$str -d" -- "$2") )
  elif [ "$3" == "projects" ]; then
    str=$(get_compgen_str_for_long_short_option_only_allowed_once "$str" "-v " "--verbose " "$COMP_LINE")
    COMPREPLY=( $(compgen -W "$str -d" -- "$2") )
  else
    #str=$(get_compgen_str_for_verb "$str" "$COMP_LINE")
    #str=$(get_compgen_str_for_noun "$str" "$COMP_LINE")
    #COMPREPLY=( $(compgen -W "$str" -- "$2") )
    str=$(get_compgen_str_for_long_short_option_only_allowed_once "$str" "-v " "--verbose " "$COMP_LINE")
    COMPREPLY=( $(compgen -W "$str -d" -- "$2") )
  fi
  # below line necessary for -d argument
  [[ $COMPREPLY == */ ]] && compopt -o nospace
}
complete -F _ocpidev2 ocpidev2
