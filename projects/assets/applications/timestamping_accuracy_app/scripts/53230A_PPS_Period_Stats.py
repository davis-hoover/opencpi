#!/usr/bin/python

import sys

# https://pypi.org/project/python-vxi11/
# pip install python-vxi11
import vxi11

if len(sys.argv) != 2:
    print("Invalid arguments:  usage is: 53230A_PPS_Period_Stats.py <ip-address-of-53230-counter>")
    sys.exit(1)

freq_cnt =  vxi11.Instrument(sys.argv[1])
freq_cnt.timeout = 110

# Put the device in a known state
freq_cnt.write("*RST")
freq_cnt.write("*CLS")

#Useful for testing
#print(freq_cnt.ask("*IDN?"))

# Use external 10MHz reference
freq_cnt.write("ROSCillator:SOURce EXTernal")

# Disable timeout (otherwise we might lose measurements)
freq_cnt.write("SYSTem:TIMeout INFinity")

# Channel 1 setup:
# This setup was intended to measure 1 PPS of amplitude 3.3-5 V
freq_cnt.write("CONF:PER 1.0,.001")       # Expected signal is 1 Hz
freq_cnt.write("SENSe:FREQuency:MODE CONT")# Measure "a" consecutive triggers
freq_cnt.write("INP1:COUP DC")             # DC coupled
freq_cnt.write("INP1:RANGE 5")             # 5 V range
freq_cnt.write("INP1:SLOPE NEG")           # Falling edge
freq_cnt.write("INP1:LEVEL:AUTO OFF")      # Disable auto trigger
freq_cnt.write("INP1:LEV 1.0")             # Trigger level 1 V

for a in [10,100]:
  print("Measuring Frequency and Computing Statistics for "+str(a)+" Samples")
  print("If measuring PPS, measurement will take "+str(a)+" Seconds")
  freq_cnt.write("SAMP:COUN "+str(a))
  freq_cnt.write("CALC:AVER:STAT ON")
  freq_cnt.write("CALC:STAT ON")

  freq_cnt.write("INIT")
  freq_cnt.write("*WAI")

  print("Min                : "+str((float(freq_cnt.ask("CALC:AVER:MIN?"))-1)/1e-6)+" us")
  print("Max                : "+str((float(freq_cnt.ask("CALC:AVER:MAX?"))-1)/1e-6)+" us")
  print("Average            : "+str((float(freq_cnt.ask("CALC:AVER:AVER?"))-1)/1e-6)+" us")
  print("Standard Deviation : "+str((float(freq_cnt.ask("CALC:AVER:SDEV?")))/1e-6)+" us")
  print("Peak-to-Peak       : "+str((float(freq_cnt.ask("CALC:AVER:PTP?")))/1e-6)+" us")

sys.exit()
