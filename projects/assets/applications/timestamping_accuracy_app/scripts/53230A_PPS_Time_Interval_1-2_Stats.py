#!/usr/bin/python

import sys

# https://pypi.org/project/python-vxi11/
# pip install python-vxi11
import vxi11

if len(sys.argv) != 2:
    print("Invalid arguments:  usage is: 53230A_PPS_Time_Interval_Stats.py <ip-address-of-53230-counter>")
    sys.exit(1)

freq_cnt =  vxi11.Instrument(sys.argv[1])

# Put the device in a known state
freq_cnt.write("*RST")
freq_cnt.write("*CLS")

#Useful for testing
print(freq_cnt.ask("*IDN?"))

# Use external 10MHz reference
freq_cnt.write("ROSCillator:SOURce EXTernal")

# Disable timeout (otherwise we might lose measurements)
freq_cnt.write("SYSTem:TIMeout INFinity")

# Channel 1 setup:
# This setup was intended to measure the phase delay between two input signals
# of amplitudes 3.3-5 V
freq_cnt.write("CONF:TINT (@1), (@2)")             # Channel 1 time interval measurement
freq_cnt.write("INP1:COUP DC")               # DC coupled
freq_cnt.write("INP2:COUP DC")               # DC coupled
freq_cnt.write("INP1:RANGE 5")               # 5 V range
freq_cnt.write("INP2:RANGE 5")               # 5 V range
freq_cnt.write("INP1:LEVEL:AUTO OFF")        # Disable auto trigger
freq_cnt.write("INP2:LEVEL:AUTO OFF")        # Disable auto trigger
freq_cnt.write("INP1:LEV 1.0")              # Start threshold 1 V
freq_cnt.write("INP2:LEV 1.0")              # Stop threshold 1 V
freq_cnt.write("INP1:SLOP POS")             # Start on falling edge
freq_cnt.write("INP2:SLOP POS")             # Stop on falling edge

for a in [10,100]:
  print("Measuring Frequency and Computing Statistics for "+str(a)+" Samples")
  print("If measuring PPS, measurement will take "+str(a)+" Seconds")
  freq_cnt.timeout = a+10
  freq_cnt.write("SAMP:COUN "+str(a))
  freq_cnt.write("CALC:AVER:STAT ON")
  freq_cnt.write("CALC:STAT ON")

  freq_cnt.write("INIT")
  freq_cnt.write("*WAI")

  print("Min                : "+str((float(freq_cnt.ask("CALC:AVER:MIN?"))))+" s")
  print("Max                : "+str((float(freq_cnt.ask("CALC:AVER:MAX?"))))+" s")
  print("Average            : "+str((float(freq_cnt.ask("CALC:AVER:AVER?"))))+" s")
  print("Standard Deviation : "+str((float(freq_cnt.ask("CALC:AVER:SDEV?")))/1e-6)+" us")
  print("Peak-to-Peak       : "+str((float(freq_cnt.ask("CALC:AVER:PTP?")))/1e-6)+" us")

sys.exit()
