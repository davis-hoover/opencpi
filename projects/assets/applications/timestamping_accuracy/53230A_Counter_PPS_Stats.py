#!/usr/bin/python

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

# https://pypi.org/project/python-vxi11/
# pip install python-vxi11
import vxi11

if len(sys.argv) != 3:
    print("Invalid arguments: usage is: 53230A_Counter_PPS_Stats.py <ip-address-of-53230-counter> <measurement-type>")
    sys.exit(1)

freq_cnt =  vxi11.Instrument(sys.argv[1])
measurement_type = sys.argv[2].lower()
NUM_MEASUREMENTS = [10, 100]

if (measurement_type != "frequency" and measurement_type != "period" and 
    measurement_type != "single_period" and measurement_type != "time_interval_1-2"):
    print("Invalid measurement type. Valid measurements types are:")
    print("frequency, period, single_period, time_interval_1-2")
    sys.exit(2)

# Put the device in a known state
freq_cnt.write("*RST")
freq_cnt.write("*CLS")

# Use external 10MHz reference
freq_cnt.write("ROSCillator:SOURce EXTernal")

# Disable timeout (otherwise we might lose measurements)
freq_cnt.write("SYSTem:TIMeout INFinity")

#Setup measurement
#Channel 1 parameters common to all measurements
freq_cnt.write("INP1:COUP DC")                  # DC coupled
freq_cnt.write("INP1:LEVEL:AUTO OFF")           # Disable auto trigger
freq_cnt.write("INP1:RANGE 5")                  # 5 V range
#Measurement specific parameters
if measurement_type == "frequency":
    freq_cnt.write("CONF:FREQ 1.0,.001")        # Expected signal is 1 Hz
    freq_cnt.write("SENSe:FREQuency:MODE CONT") # Measure "a" consecutive triggers
    freq_cnt.write("INP1:SLOPE NEG")            # Falling edge
    freq_cnt.write("INP1:LEV 1.0")              # Trigger level 1 V
elif measurement_type == "period":
    freq_cnt.write("CONF:PER 1.0,.001")         # Expected signal is 1 Hz
    freq_cnt.write("SENSe:FREQuency:MODE CONT") # Measure "a" consecutive triggers
    freq_cnt.write("INP1:SLOPE NEG")            # Falling edge
    freq_cnt.write("INP1:LEV 1.0")              # Trigger level 1 V
elif measurement_type == "single_period":
    freq_cnt.write("CONF:SPER (@1)")          
    freq_cnt.write("INP1:LEV1 1.7")             # Threshold 1 V
    freq_cnt.write("INP1:SLOP2 POS")            # Rising edge
elif measurement_type == "time_interval_1-2":
    freq_cnt.write("CONF:TINT (@1), (@2)")    
    #Channel 1
    freq_cnt.write("INP1:LEV 1.0")              # Start threshold 1 V
    freq_cnt.write("INP1:SLOP POS")             # Start on rising edge
    #Channel 2
    freq_cnt.write("INP2:COUP DC")              # DC coupled
    freq_cnt.write("INP2:LEVEL:AUTO OFF")       # Disable auto trigger
    freq_cnt.write("INP2:RANGE 5")              # 5 V range
    freq_cnt.write("INP2:LEV 1.0")              # Stop threshold 1 V
    freq_cnt.write("INP2:SLOP POS")             # Stop on rising edge
else:
    print("Invalid measurement type. Valid measurements types are:")
    print("frequency, period, single_period, time_interval_1-1, time_interval_1-2")
    sys.exit(3)

#Make measurement
MEASUREMENT_BUFFER_SEC = 10

if measurement_type == "frequency":
    units=" Hz"
else:
    units=" s"

for a in NUM_MEASUREMENTS:
    print("Measurement type: " + measurement_type)
    print("Computing Statistics for " + str(a) + " Measurements")
    print("If measuring PPS, measurement will take approximately " + str(a) + " Seconds")

    if measurement_type == "single_period":
        freq_cnt.timeout = a * 2 + MEASUREMENT_BUFFER_SEC #single period measurement take 2 s each
    else:
        freq_cnt.timeout = a + MEASUREMENT_BUFFER_SEC

    freq_cnt.write("SAMP:COUN " + str(a))
    freq_cnt.write("CALC:AVER:STAT ON")
    freq_cnt.write("CALC:STAT ON")
    freq_cnt.write("INIT")
    freq_cnt.write("*WAI")
  
    print("Min                : " + str(freq_cnt.ask("CALC:AVER:MIN?")) + units)
    print("Max                : " + str(freq_cnt.ask("CALC:AVER:MAX?")) + units)
    print("Average            : " + str(freq_cnt.ask("CALC:AVER:AVER?")) + units)
    print("Standard Deviation : " + str(freq_cnt.ask("CALC:AVER:SDEV?")) + units)
    if measurement_type == "frequency":
        print("Allan Deviation    : " + str(freq_cnt.ask("CALC:AVER:ADEV?")))
    else:
        print("Peak-to-Peak       : " + str(freq_cnt.ask("CALC:AVER:PTP?")) + units)

sys.exit()
