#!/usr/bin/env python3.4

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
This script configures the 53230A counter for different types of measurements
used to characterize the Hardware Time Server 

The measurement setup was intended to measure 1 PPS of amplitude 3.3 - 5 V

"""
import sys

try:
    import vxi11
except ImportError:
    # To be replaced in 2.0 with proper Python dependencies
    # Recommended way to use pip within a program (but not best practice)
    # https://pip.pypa.io/en/latest/user_guide/#using-pip-from-your-program
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--user', 'python-vxi11'])
    import os
    os.execv(__file__, sys.argv)

# There are issues the Instrument class cleaning up properly 
# https://github.com/python-ivi/python-usbtmc/issues/44
def clean_exit(instrument_obj, err):
    freq_cnt.close()
    sys.exit(err)
    
if len(sys.argv) != 3:
    print("Invalid arguments: usage is: 53230A_Counter_PPS_Stats.py <ip-address-of-53230-counter> <measurement-type>")
    sys.exit(1)

measurement_type = sys.argv[2].lower()
if (measurement_type != "frequency" and measurement_type != "period" and 
    measurement_type != "single_period" and measurement_type != "time_interval_2-1" and
    measurement_type != "ref_check"):
    print("Invalid measurement type. Valid measurements types are:")
    print("ref_check, frequency, period, single_period, time_interval_2-1")
    sys.exit(2)

freq_cnt = vxi11.Instrument(sys.argv[1])
NUM_MEASUREMENTS = [100]
    
# Put the device in a known state
freq_cnt.write("*RST")
freq_cnt.write("*CLS")

# Use external 10MHz reference
freq_cnt.write("ROSCillator:SOURce EXTernal")

# Check 10 MHz reference 
if measurement_type == "ref_check":
    expected_ref_freq = "+1.00000000E+007"
    ref_freq = freq_cnt.ask("ROSCillator:EXTernal:FREQuency?") #Check ref frequency
    if ref_freq != expected_ref_freq:
        print("Incorrect input reference frequency: " + ref_freq)
        print("Expected " + expected_ref_freq)
        clean_exit(freq_cnt, 3)
    freq_cnt.write("ROSCillator:EXTernal:CHECk ONCE")          #Check ref validity
    clean_exit(freq_cnt, 0)

#Measurement specific parameters
#Setup measurement
#Channel 1 parameters common to all measurements
freq_cnt.write("INP1:COUP DC")                  # DC coupled
freq_cnt.write("INP1:LEVEL:AUTO OFF")           # Disable auto trigger
freq_cnt.write("INP1:RANGE 5")                  # 5 V range
#Measurement specific parameters
if measurement_type == "frequency":
    measurement_name = "Frequency Error:"
    freq_cnt.write("CONF:FREQ 1.0,.001")  # Expected signal is 1 Hz
    freq_cnt.write("SENSe:FREQuency:MODE CONT") # Measure "a" consecutive triggers
    freq_cnt.write("INP1:SLOPE NEG")            # Falling edge
    freq_cnt.write("INP1:LEV 1.0")              # Trigger level 1 V
elif measurement_type == "period":
    measurement_name = "Jitter:"
    freq_cnt.write("CONF:PER 1.0,.001")    # Expected signal is 1 Hz
    freq_cnt.write("SENSe:FREQuency:MODE CONT") # Measure "a" consecutive triggers
    freq_cnt.write("INP1:SLOPE NEG")            # Falling edge
    freq_cnt.write("INP1:LEV 1.0")              # Trigger level 1 V
elif measurement_type == "single_period":
    measurement_name = "Jitter:"
    freq_cnt.write("CONF:SPER")          
    freq_cnt.write("INP1:LEV1 1.7")             # Threshold 1 V
    freq_cnt.write("INP1:SLOP2 POS")            # Rising edge
elif measurement_type == "time_interval_2-1":
    measurement_name = "Phase Accuracy:"
    freq_cnt.write("CONF:TINT (@2), (@1)")    
    #Channel 1
    freq_cnt.write("INP1:LEV 1.0")              # Start threshold 1 V
    freq_cnt.write("INP1:SLOP POS")             # Start on rising edge
    #Channel 1
    freq_cnt.write("INP2:COUP DC")              # DC coupled
    freq_cnt.write("INP2:LEVEL:AUTO OFF")       # Disable auto trigger
    freq_cnt.write("INP2:RANGE 5")              # 5 V range
    freq_cnt.write("INP2:LEV 1.0")              # Stop threshold 1 V
    freq_cnt.write("INP2:SLOP POS")             # Stop on rising edge
else:
    print("Invalid measurement type. Valid measurements types are:")
    print("frequency, period, single_period, time_interval_1-1, time_interval_2-1")
    clean_exit(freq_cnt, 4)

#Make measurement
MEASUREMENT_BUFFER_SEC = 10

if measurement_type == "frequency":
    units=" Hz"
else:
    units=" s"

for a in NUM_MEASUREMENTS:
    print(measurement_name)
    
    # Set timeouts
    if measurement_type == "single_period":
        freq_cnt.timeout = a * 2 + MEASUREMENT_BUFFER_SEC #single period measurement take 2 s each
    else:
        freq_cnt.timeout = a + MEASUREMENT_BUFFER_SEC
    freq_cnt.write("SYSTem:TIMeout " + str(freq_cnt.timeout))

    freq_cnt.write("SAMP:COUN " + str(a))
    freq_cnt.write("CALC:AVER:STAT ON")
    freq_cnt.write("CALC:STAT ON")
    freq_cnt.write("INIT")
    freq_cnt.write("*WAI")
  
    if measurement_type == "frequency":
        print("Min                : " + str(freq_cnt.ask("CALC:AVER:MIN?")) + units)
        print("Max                : " + str(freq_cnt.ask("CALC:AVER:MAX?")) + units)
    if measurement_type == "time_interval_2-1":
        print("Average            : " + str(freq_cnt.ask("CALC:AVER:AVER?")) + units)
    if measurement_type == "frequency" or measurement_type == "single_period":
        print("Standard Deviation : " + str(freq_cnt.ask("CALC:AVER:SDEV?")) + units)
    if measurement_type == "frequency":
        print("Short Term Stability:")
        print("Allan Deviation    : " + str(freq_cnt.ask("CALC:AVER:ADEV?")))

clean_exit(freq_cnt, 0)
