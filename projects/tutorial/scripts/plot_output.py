#!/usr/bin/env python3
import numpy as np
import matplotlib.pyplot as plt
import sys
# read data from input file
data=np.fromfile(sys.stdin,dtype=np.int16)
# plot the upper 16-bits
plt.figure(1)
plt.plot(data[1::2]) # odds to the upper 16-bits
plt.title("Output Data - Upper 16")
plt.grid()
# plot the lower 16-bits
plt.figure(2)
plt.plot(data[0::2]) # evens to the lower 16 bits
plt.title("Output Data - Lower 16")
plt.grid()
plt.show()
