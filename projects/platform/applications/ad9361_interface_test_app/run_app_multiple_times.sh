#! /bin/bash
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

#sample_rates="3.0 4.0 5.0 6.0 7.0 8.0 10.0 15.0 20.0 28.0 30.0"
sample_rates="4.0 7.0 8.0 10.0 15.0 20.0 30.0 40.0 50.0 60.0 61.44"
number_of_repeats=10

total_success_counter=0
total_run_counter=0
retval=0

echo ""
echo "Running interface test at sample rates: $sample_rates";
echo "Each test repeated $number_of_repeats times";
echo "Key: '+' = PASS, '-' = FAIL ";

for sample_rate in $sample_rates; do
  success_counter=0
  run_counter=0  

  echo "";
  echo -n "Sample rate: $sample_rate MHz [";
  for (( i = 0 ; i < number_of_repeats ; i++)); do    
    let run_counter++;
    let total_run_counter++;
    ./target-xilinx19_2_aarch32/ad9361_interface_test_app -s $sample_rate > /dev/null;
    RESULT=$?
    if [ $RESULT -eq 0 ]; then
      let success_counter++;
      let total_success_counter++;
      echo -n "+"
    else 
      echo -n "-" 
      retval=1;
    fi
    sleep $[ ( $RANDOM % 5 )  + 1 ]s
  done
  echo "]"
  echo "    Results: $success_counter / $run_counter passed";
done

echo ""
echo "Overal results: $total_success_counter / $total_run_counter passed";

exit $retval


