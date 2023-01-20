/*
 * This file is protected by Copyright. Please refer to the COPYRIGHT file
 * distributed with this source distribution.
 *
 * This file is part of OpenCPI <http://www.opencpi.org>
 *
 * OpenCPI is free software: you can redistribute it and/or modify it under the
 * terms of the GNU Lesser General Public License as published by the Free
 * Software Foundation, either version 3 of the License, or (at your option) any
 * later version.
 *
 * OpenCPI is distributed in the hope that it will be useful, but WITHOUT ANY
 * WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
 * A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
 * details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef _TEST_HH
#define _TEST_HH

#include "DRC.hh"
using namespace DRC;
config_key_t di = config_key_direction;
config_key_t fc = config_key_tuning_freq_MHz;
config_key_t bw = config_key_bandwidth_3dB_MHz;
config_key_t fs = config_key_sampling_rate_Msps;
config_key_t sc = config_key_samples_are_complex;
config_key_t gm = config_key_gain_mode;
config_key_t gn = config_key_gain_dB;

bool result;
//cfg = config key
//val = value to lock to
//dot = do_include_tolerance
//tol = tolerance value
//exp = boolean expected lock success for given config key, value, and tolerance
#define TEST(data_stream,cfg,val,dot,tol,expected) \
  result = dot ? uut.lock_config(data_stream,cfg,val,tol) : uut.lock_config(data_stream,cfg,val); \
  std::cout << (result == expected ? "[INFO] PASS" : "[ERROR] FAIL"); \
  std::cout << " data_stream,cfg,val,dot,tol,expected="; \
  std::cout << data_stream << "," << cfg << "," << val << "," << dot << "," << tol << "," << expected << "\n"; \
  if(result != expected) { \
    throw std::string("[ERROR] FAIL\n"); \
  }

#endif // _TEST_HH
