#!/usr/bin/env python3
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
import sys
import os.path
import math
import itertools
import numpy as np
import csv

# This script calculates the mulitply and divide factors for a pll based clock generator
# Right now this only supports xilinx zynq 7000 series mmcm and pll and does a brute force optimization
# to optimize the VCO frequency. It reads in a csv file containing the part/speed grade specfic information
# needed in order to calculate the multiply and divide factors.
# Referenced this stack overflow post for some of this code:
# https://stackoverflow.com/questions/39236863/restrict-scipy-optimize-minimize-to-integer-values

# TODO Make this more generic and normalize for Xilinx and Intel (if intel's primitive needs to use this)

def objective(FIN, x):
    M = x[0]
    N = x[1]
    return FIN*(M/N)

def constraint1(FIN, x):
    M = x[0]
    N = x[1]
    O = x[2]
    return ((FIN*M)/(N*O))

def brute_force_optimization(FIN, FOUT, clock_prim):
    global M
    global N
    global O
    global FVCO_MIN
    global FVCO_MAX
    global FOUT_MIN
    global FOUT_MAX
    global M_MIN
    global M_MAX
    global D_MIN
    global D_MAX
    if(clock_prim == "mmcme2"):
        with open('zynq_7000_1C_1I_1LI_MMCM_spec.csv', mode='r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                FIN_MIN = float(row["MMCM_FIN_MIN"])
                FIN_MAX = float(row["MMCM_FIN_MAX"])
                FOUT_MIN = float(row["MMCM_FOUT_MIN"])
                FOUT_MAX = float(row["MMCM_FOUT_MAX"])
                if (FIN < FIN_MIN):
                    print("FIN is less than minimum allowed input frequency")
                    sys.exit(1)
                elif (FIN > FIN_MAX):
                    print("FIN is greater than maximum allowed input frequency")
                    sys.exit(1)
                elif (FOUT < FOUT_MIN):
                    print("FOUT is less than minimum allowed output frequency")
                    sys.exit(1)
                elif (FOUT > FOUT_MAX):
                    print("FOUT is greater than maximum allowed output frequency")
                    sys.exit(1)
                FVCO_MIN =float( row["MMCM_FVCO_MIN"])
                FVCO_MAX = float(row["MMCM_FVCO_MAX"])
                MMCM_FPFD_MIN = float(row["MMCM_FPFD_MIN"])
                MMCM_FPFD_MAX = float(row["MMCM_FPFD_MAX"])
                M_MIN = float(row["M_MIN"])
                M_MAX = float(row["M_MAX"])
                D_MIN = int(row["D_MIN"])
                D_MAX = int(row["D_MAX"])
                O_MIN = float(row["O_MIN"])
                O_MAX = float(row["O_MAX"])
        N_MIN_CALC = int(math.ceil(FIN/MMCM_FPFD_MAX))
        if (N_MIN_CALC < D_MIN):
            N_MIN_CALC = D_MIN
        N_MAX_CALC = int(math.floor(FIN/MMCM_FPFD_MIN))
        if (N_MAX_CALC > D_MAX):
            N_MAX_CALC = D_MAX
        M_MIN_CALC = math.ceil((FVCO_MIN/FIN)*N_MIN_CALC)
        if (M_MIN_CALC < M_MIN):
            M_MIN_CALC = M_MIN
        M_MAX_CALC = math.floor((FVCO_MAX/FIN)*N_MAX_CALC)
        if (M_MAX_CALC > M_MAX):
            M_MAX_CALC = M_MAX
        # Generate all possible values for M, N, and O
        # Multiplying the Max - Min by 8 and adding 1 because that will give a step size of 0.125
        M = np.linspace(M_MIN_CALC,M_MAX_CALC, int((M_MAX_CALC-M_MIN_CALC)*8)+1)
        N = [i for i in range(N_MIN_CALC, N_MAX_CALC+1)]
        O = np.linspace(O_MIN,O_MAX, int((O_MAX-O_MIN)*8)+1)
    elif(clock_prim == "plle2"):
        with open('zynq_7000_1C_1I_1LI_PLL_spec.csv', mode='r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                FIN_MIN = float(row["PLL_FIN_MIN"])
                FIN_MAX = float(row["PLL_FIN_MAX"])
                FOUT_MIN = float(row["PLL_FOUT_MIN"])
                FOUT_MAX = float(row["PLL_FOUT_MAX"])
                if (FIN < FIN_MIN):
                    print("FIN is less than minimum allowed input frequency")
                    sys.exit(1)
                elif (FIN > FIN_MAX):
                    print("FIN is greater than maximum allowed input frequency")
                    sys.exit(1)
                elif (FOUT < FOUT_MIN):
                    print("FOUT is less than minimum allowed output frequency")
                    sys.exit(1)
                elif (FOUT > FOUT_MAX):
                    print("FOUT is greater than maximum allowed output frequency")
                    sys.exit(1)
                FVCO_MIN =float( row["PLL_FVCO_MIN"])
                FVCO_MAX = float(row["PLL_FVCO_MAX"])
                PLL_FPFD_MIN = float(row["PLL_FPFD_MIN"])
                PLL_FPFD_MAX = float(row["PLL_FPFD_MAX"])
                M_MIN = int(row["M_MIN"])
                M_MAX = int(row["M_MAX"])
                D_MIN = int(row["D_MIN"])
                D_MAX = int(row["D_MAX"])
                O_MIN = int(row["O_MIN"])
                O_MAX = int(row["O_MAX"])

        N_MIN_CALC = int(math.ceil(FIN/PLL_FPFD_MAX))
        if (N_MIN_CALC < D_MIN):
            N_MIN_CALC = D_MIN
        N_MAX_CALC = int(math.floor(FIN/PLL_FPFD_MIN))
        if (N_MAX_CALC > D_MAX):
            N_MAX_CALC = D_MAX
        M_MIN_CALC = int(math.ceil((FVCO_MIN/FIN)*N_MIN_CALC))
        if (M_MIN_CALC < M_MIN):
            M_MIN_CALC = M_MIN
        M_MAX_CALC = int(math.floor((FVCO_MAX/FIN)*N_MAX_CALC))
        if (M_MAX_CALC > M_MAX):
            M_MAX_CALC = M_MAX
        # Generate all possible values for M, N, and O
        M = [i for i in range(M_MIN_CALC, M_MAX_CALC+1)]
        N = [i for i in range(N_MIN_CALC, N_MAX_CALC+1)]
        O = [i for i in range(O_MIN, O_MAX+1)]


    combinationsMN = list(itertools.product(M, N))
    # Find M and O values that will give an answer that is in range of min and max MMCM FVCO values.
    reduced_combinationsMN = [combination for combination in combinationsMN if (objective(FIN, combination) >= FVCO_MIN and objective(FIN, combination) <= FVCO_MAX)]
    combinationsMNO = [MN + (O, ) for MN, O in list(itertools.product(reduced_combinationsMN, O))]

    sol = []
    # Try to find exact match first
    good_combos_exact = [(combination, objective(FIN, combination)) for combination in combinationsMNO if (constraint1(FIN, combination) == FOUT and constraint1(FIN, combination) >= FOUT_MIN and constraint1(FIN, combination) <= FOUT_MAX)]
    if not good_combos_exact:
        # Find M, N, and O values that will get a close enough answer for FOUT
        good_combos = [(combination, objective(FIN, combination)) for combination in combinationsMNO if (math.isclose(constraint1(FIN, combination), FOUT, rel_tol=1e-3) and constraint1(FIN, combination) >= FOUT_MIN and constraint1(FIN, combination) <= FOUT_MAX)]
        if not good_combos:
            print("No feasible M, N, and O values for desired output frequency")
            sys.exit(1)
        else:
            # Find the M, N, and O values that maximizes FVCO
            sol = [(c,v) for c,v in good_combos if v == max([v for c,v in good_combos])]
    else:
        # Find the M, N, and O values that maximizes FVCO
        sol = [(c,v) for c,v in good_combos_exact if v == max([v for c,v in good_combos_exact])]

    with open('info.txt', mode='w') as output_file:
        output_file.write("Requested Output Frequency: " + str(FOUT) + ". Actual Output Freqeuncy: " + str(round(constraint1(FIN, sol[0][0]), 3)) + "\n")
        output_file.write("VCO Frequency: " + str(sol[0][1]) + "\n")
        output_file.write("Chosen M value: " + str(sol[0][0][0]) + "\n")
        output_file.write("Chosen N value: " + str(sol[0][0][1]) + "\n")
        output_file.write("Chosen O value: " + str(sol[0][0][2]) + "\n")
    return sol

def main():
    FIN = float(sys.argv[1])
    FOUT = float(sys.argv[2])
    clock_prim = sys.argv[4]
    supported_parts=["isim", "xsim", "zynq", "zynq_ise"]
    if (sys.argv[3] in supported_parts):
        sol = brute_force_optimization(FIN, FOUT, clock_prim)
        with open('M.txt', mode='w') as output_file:
            output_file.write(str(sol[0][0][0]) + "\n")
        with open('N.txt', mode='w') as output_file:
            output_file.write(str(sol[0][0][1]) + "\n")
        with open('O.txt', mode='w') as output_file:
            output_file.write(str(sol[0][0][2]) + "\n")
main()
