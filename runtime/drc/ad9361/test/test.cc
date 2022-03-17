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

#define IS_LOCKING // this is still experimental

#include <iostream>
#include "AD9361DRC.hh"
using namespace DRC;
config_key_t di = config_key_direction;
config_key_t fc = config_key_tuning_freq_MHz;
config_key_t bw = config_key_bandwidth_3dB_MHz;
config_key_t fs = config_key_sampling_rate_Msps;
config_key_t sc = config_key_samples_are_complex;
config_key_t gm = config_key_gain_mode;
config_key_t gn = config_key_gain_dB;

bool res;
//cfg = config key
//val = value to lock to
//dot = do_include_tolerance
//tol = tolerance value
//exp = boolean expected lock success for given config key, value, and tolerance
#define TEST(data_stream,cfg,val,dot,tol,expected) \
  res = dot ? uut.lock_config(data_stream,cfg,val,tol) : uut.lock_config(data_stream,cfg,val); \
  std::cout << (res == expected ? "[INFO] PASS" : "[ERROR] FAIL"); \
  std::cout << " data_stream,cfg,val,dot,tol,expected="; \
  std::cout << data_stream << "," << cfg << "," << val << "," << dot << "," << tol << "," << expected << "\n"; \
  if(res != expected) { \
    throw std::string("[ERROR] FAIL\n"); \
  }

int test_AD9361Configurator() {
  // RX CHANNEL
  int ret = 0;
  AD9361Configurator uut;
  try {
    std::vector<const char*> data_stream_rx;
    data_stream_rx.push_back("rx1");
    data_stream_rx.push_back("rx2");
    for(auto it=data_stream_rx.begin (); it!=data_stream_rx.end(); ++it) {
      // direction
      // ================================================
      TEST(*it, di, (int32_t)data_stream_direction_t::rx, false, 0., true);
      uut.unlock_all();
      TEST(*it, di, (int32_t)data_stream_direction_t::tx, false, 0., false);
      uut.unlock_all();
      // Tuning Freq (MHz) [70 MHz - 6.0 GHz]
      // ================================================
      // LOWER BOUNDS
      TEST(*it, fc, 69.99   , true, 0.000001, false)
      uut.unlock_all();
      TEST(*it, fc, 70.     , true, 0.000001, true )
      uut.unlock_all();
      // MEDIAN BOUND
      TEST(*it, fc, 3000.   , true, 0.000001, true )
      uut.unlock_all();
      // UPPER BOUNDS
      TEST(*it, fc, 6000.   , true, 0.000001, true )
      uut.unlock_all();
      TEST(*it, fc, 6001.01 , true, 0.000001, false)
      uut.unlock_all();
      // Bandwidth (MHz)
      // @TODO Check Values
      // - Datasheet: <200 KHz - 56 MHz
      // ================================================
      //  LOWER BOUNDS
      TEST(*it, bw, 0.19    , true, 0.000001, false)
      uut.unlock_all();
      TEST(*it, bw, 0.2     , true, 0.000001, true )
      uut.unlock_all();
      // MEDIAN BOUND
      TEST(*it, bw, 30.     , true, 0.000001, true )
      uut.unlock_all();
      // UPPER BOUNDS
      TEST(*it, bw, 56.     , true, 0.000001, true )
      uut.unlock_all();
      TEST(*it, bw, 56.01   , true, 0.000001, false)
      uut.unlock_all();
      // Sampling rate (Msps) 2.083334 - 61.44
      // @TODO Check Values
      // ================================================
      // LOWER BOUNDS
      TEST(*it, fs, 2.08    , true, 0.000001, false)
      uut.unlock_all();
      TEST(*it, fs, 2.083334, true, 0.000001, true )
      uut.unlock_all();
      // MEDIAN BOUND
      TEST(*it, fs, 32.     , true, 0.000001, true )
      uut.unlock_all();
      // UPPER BOUND
      TEST(*it, fs, 61.44   , true, 0.000001, true )
      uut.unlock_all();
      TEST(*it, fs, 61.45   , true, 0.000001, false)
      uut.unlock_all();
      // Samples are complex
      // ================================================
      TEST(*it, sc, 0       , false,0.000001, false)
      uut.unlock_all();
      TEST(*it, sc, 1       , false,0.000001, true )
      uut.unlock_all();
      TEST(*it, sc, 2       , false,0.000001, false)
      uut.unlock_all();
      // Gain Mode
      // ================================================
      TEST(*it, gm, -1      , false,0.000001, false)
      uut.unlock_all();
      TEST(*it, gm, 0       , false,0.000001, true )
      uut.unlock_all();
      TEST(*it, gm, 1       , false,0.000001, true )
      uut.unlock_all();
      TEST(*it, gm, 2       , false,0.000001, false)
      uut.unlock_all();
      // Gain dB
      // ================================================
      // Unconditional Constraints
      // ------------------------------------------------
      TEST(*it, gn, -11.    , true ,0.000001, false)
      uut.unlock_all();
      TEST(*it, gn, -10.    , true ,0.000001, true )
      uut.unlock_all();
      TEST(*it, gn, -3.     , true ,0.000001, true )
      uut.unlock_all();
      TEST(*it, gn, -1.     , true ,0.000001, true )
      uut.unlock_all();
      TEST(*it, gn, 0.      , true ,0.000001, true )
      uut.unlock_all();
      TEST(*it, gn, 62.     , true ,0.000001, true )
      uut.unlock_all();
      TEST(*it, gn, 71.     , true ,0.000001, true )
      uut.unlock_all();
      TEST(*it, gn, 73.     , true ,0.000001, true )
      uut.unlock_all();
      TEST(*it, gn, 74.     , true ,0.000001, false)
      uut.unlock_all();
      // Conditional Constrains
      // ================================================
      // If fc [70 - 1300]; Possible Gain: -1 - 73 dB
      // LOWER BOUNDS
      // ------------------------------------------------
      TEST(*it, fc, 70.01   , true, 0.000001, true )
      TEST(*it, gn, -2.     , true ,0.000001, false)
      uut.unlock_all();
      TEST(*it, fc, 1299.01 , true, 0.000001, true )
      TEST(*it, gn, -2.     , true ,0.000001, false)
      uut.unlock_all();
      TEST(*it, fc, 70.01   , true, 0.000001, true )
      TEST(*it, gn, -1.     , true ,0.000001, true )
      uut.unlock_all();
      TEST(*it, fc, 1299.01 , true, 0.000001, true )
      TEST(*it, gn, -1.     , true ,0.000001, true )
      uut.unlock_all();
      // MEDIAN BOUND
      // ------------------------------------------------
      TEST(*it, fc, 70.01   , true, 0.000001, true )
      TEST(*it, gn, 50.     , true ,0.000001, true )
      uut.unlock_all();
      TEST(*it, fc, 1299.01 , true, 0.000001, true )
      TEST(*it, gn, 50.     , true ,0.000001, true )
      uut.unlock_all();
      // UPPER BOUNDS
      // ------------------------------------------------
      TEST(*it, fc, 70.01   , true, 0.000001, true )
      TEST(*it, gn, 73.     , true ,0.000001, true )
      uut.unlock_all();
      TEST(*it, fc, 1299.01 , true, 0.000001, true )
      TEST(*it, gn, 73.     , true ,0.000001, true )
      uut.unlock_all();
      TEST(*it, fc, 70.01   , true, 0.000001, true )
      TEST(*it, gn, 74.     , true ,0.000001, false)
      uut.unlock_all();
      TEST(*it, fc, 1299.01 , true, 0.000001, true )
      TEST(*it, gn, 74.     , true ,0.000001, false)
      uut.unlock_all();
      // If fc [1300 - 4000); Possible Gain: -3 - 71 dB
      // LOWER BOUNDS
      // ------------------------------------------------
      TEST(*it, fc, 1300.01 , true, 0.000001, true )
      TEST(*it, gn, -4      , true ,0.000001, false)
      uut.unlock_all();
      TEST(*it, fc, 3999.01 , true, 0.000001, true )
      TEST(*it, gn, -4      , true ,0.000001, false)
      uut.unlock_all();
      TEST(*it, fc, 1300.01 , true, 0.000001, true )
      TEST(*it, gn, -3.     , true ,0.000001, true )
      uut.unlock_all();
      TEST(*it, fc, 3999.01 , true, 0.000001, true )
      TEST(*it, gn, -3.     , true ,0.000001, true )
      uut.unlock_all();
      // MEDIAN BOUND
      // ------------------------------------------------
      TEST(*it, fc, 1300.01 , true, 0.000001, true )
      TEST(*it, gn, 50.     , true ,0.000001, true )
      uut.unlock_all();
      TEST(*it, fc, 3999.01 , true, 0.000001, true )
      TEST(*it, gn, 50.     , true ,0.000001, true )
      uut.unlock_all();
      // UPPER BOUNDS
      // ------------------------------------------------
      TEST(*it, fc, 1300.01 , true, 0.000001, true )
      TEST(*it, gn, 71.     , true ,0.000001, true )
      uut.unlock_all();
      TEST(*it, fc, 3999.01 , true, 0.000001, true )
      TEST(*it, gn, 71.     , true ,0.000001, true )
      uut.unlock_all();
      TEST(*it, fc, 1300.01 , true, 0.000001, true )
      TEST(*it, gn, 72.     , true ,0.000001, false)
      uut.unlock_all();
      TEST(*it, fc, 3999.01 , true, 0.000001, true )
      TEST(*it, gn, 72.     , true ,0.000001, false)
      uut.unlock_all();
      // If fc [4000 - 6000]; Possible Gain: -10 - 62 dB
      // LOWER BOUNDS
      // ------------------------------------------------
      TEST(*it, fc, 4000.01 , true, 0.000001, true )
      TEST(*it, gn, -11.    , true ,0.000001, false)
      uut.unlock_all();
      TEST(*it, fc, 5999.01 , true, 0.000001, true )
      TEST(*it, gn, -11.    , true ,0.000001, false)
      uut.unlock_all();
      TEST(*it, fc, 4000.01 , true, 0.000001, true )
      TEST(*it, gn, -10.    , true ,0.000001, true )
      uut.unlock_all();
      TEST(*it, fc, 5999.01 , true, 0.000001, true )
      TEST(*it, gn, -10.    , true ,0.000001, true )
      uut.unlock_all();
      // MEDIAN BOUND
      // ------------------------------------------------
      TEST(*it, fc, 4000.01 , true, 0.000001, true )
      TEST(*it, gn, 50.     , true ,0.000001, true )
      uut.unlock_all();
      TEST(*it, fc, 5999.01 , true, 0.000001, true )
      TEST(*it, gn, 50.     , true ,0.000001, true )
      // UPPER BOUNDS
      // ------------------------------------------------
      TEST(*it, fc, 4000.01 , true, 0.000001, true )
      TEST(*it, gn, 62.     , true ,0.000001, true )
      uut.unlock_all();
      TEST(*it, fc, 5999.01 , true, 0.000001, true )
      TEST(*it, gn, 62.     , true ,0.000001, true )
      uut.unlock_all();
      TEST(*it, fc, 4000.01 , true, 0.000001, true )
      TEST(*it, gn, 63.     , true ,0.000001, false)
      uut.unlock_all();
      TEST(*it, fc, 5999.01 , true, 0.000001, true )
      TEST(*it, gn, 63.     , true ,0.000001, false)
      uut.unlock_all();
    }
    // TX CHANNEL
    std::vector<const char*> data_stream_tx;
    data_stream_tx.push_back("tx1");
    data_stream_tx.push_back("tx2");
    for(auto it=data_stream_tx.begin (); it!=data_stream_tx.end(); ++it) {
      // direction
      // ================================================
      TEST(*it, di, (int32_t)data_stream_direction_t::rx, false, 0., false);
      uut.unlock_all();
      TEST(*it, di, (int32_t)data_stream_direction_t::tx, false, 0., true);
      uut.unlock_all();
      // Tuning Freq [70 MHz - 6000 MHz]
      // ================================================
      //  LOWER BOUNDS
      TEST(*it, fc, 69.99   , true, 0.000001, false)
      uut.unlock_all();
      TEST(*it, fc, 70.     , true, 0.000001, true )
      uut.unlock_all();
      // MEDIAN BOUND
      TEST(*it, fc, 3000.   , true, 0.000001, true )
      uut.unlock_all();
      // UPPER BOUNDS
      TEST(*it, fc, 6000.   , true, 0.000001, true )
      uut.unlock_all();
      TEST(*it, fc, 6001.01 , true, 0.000001, false)
      uut.unlock_all();
      // Bandwidth [1.25 - 40 MHz]
      // @TODO Check Values
      // ================================================
      //  LOWER BOUNDS
      TEST(*it, bw, 1.24    , true, 0.000001, false)
      uut.unlock_all();
      TEST(*it, bw, 1.25    , true, 0.000001, true )
      uut.unlock_all();
      // MEDIAN BOUND
      TEST(*it, bw, 20.     , true, 0.000001, true )
      uut.unlock_all();
      // UPPER BOUNDS
      TEST(*it, bw, 40.     , true, 0.000001, true )
      uut.unlock_all();
      TEST(*it, bw, 40.01   , true, 0.000001, false)
      uut.unlock_all();
      //Sampling rate [2.08334 - 61.44 Msps]
      // ================================================
      // LOWER BOUNDS
      TEST(*it, fs, 2.08    , true, 0.000001, false)
      uut.unlock_all();
      TEST(*it, fs, 2.083334, true, 0.000001, true )
      uut.unlock_all();
      // MEDIAN BOUND
      TEST(*it, fs, 32.     , true, 0.000001, true )
      uut.unlock_all();
      // UPPER BOUNDS
      TEST(*it, fs, 61.44   , true, 0.000001, true )
      uut.unlock_all();
      TEST(*it, fs, 61.45   , true, 0.000001, false)
      uut.unlock_all();
      // Samples are complex
      // ================================================
      TEST(*it, sc, 0       , false,0.000001, false)
      uut.unlock_all();
      TEST(*it, sc, 1       , false,0.000001, true )
      uut.unlock_all();
      TEST(*it, sc, 2       , false,0.000001, false)
      uut.unlock_all();
      // Gain Mode
      // ================================================
      TEST(*it, gm, 0       , false,0.000001, false)
      uut.unlock_all();
      TEST(*it, gm, 1       , false,0.000001, true )
      uut.unlock_all();
      TEST(*it, gm, 2       , false,0.000001, false)
      uut.unlock_all();
      // Gain (dB) (-89.75 - 0)
      // ================================================
      // LOWER BOUNDS
      TEST(*it, gn, -89.76  , true, 0.000001, false)
      uut.unlock_all();
      TEST(*it, gn, -89.75  , true, 0.000001, true )
      uut.unlock_all();
      // MEDIAN BOUND
      TEST(*it, gn, -40.    , true, 0.000001, true )
      uut.unlock_all();
      // UPPER BOUND
      TEST(*it, gn, 0.      , true, 0.000001, true )
      uut.unlock_all();
      TEST(*it, gn, 0.01    , true, 0.000001, false)
      /// @TODO test gain conditional constraints
    }
    std::cout << "[INFO] PASS\n";
  }
  catch(std::string& err) {
    ret = 1;
    std::cout << err;
  }
  return ret;
}

int test_AD9361DDCConfigurator() {
  // RX CHANNEL
  int ret = 0;
/// @TODO replace below line with proper functionality
#define AD9361DDCConfigurator AD9361Configurator
  AD9361DDCConfigurator uut;
  try {
    std::vector<const char*> data_stream_rx;
    data_stream_rx.push_back("rx1");
    data_stream_rx.push_back("rx2");
    for(auto it=data_stream_rx.begin (); it!=data_stream_rx.end(); ++it) {
      // direction
      // ================================================
      TEST(*it, di, (int32_t)data_stream_direction_t::rx, false, 0., true);
      uut.unlock_all();
      TEST(*it, di, (int32_t)data_stream_direction_t::tx, false, 0., false);
      uut.unlock_all();
      // Tuning Freq (MHz) [39.28 - 6030.7190625 MHz]
      // ================================================
      // LOWER BOUNDS
      TEST(*it, fc, 39.27   , true, 0.000001, false)
      uut.unlock_all();
      TEST(*it, fc, 39.28   , true, 0.000001, true )
      uut.unlock_all();
      // MEDIAN BOUND
      TEST(*it, fc, 3000.   , true, 0.000001, true )
      uut.unlock_all();
      // UPPER BOUNDS
      TEST(*it, fc, 6030.7190625 , true, 0.000001, true )
      uut.unlock_all();
      TEST(*it, fc, 6039.71907, true, 0.000001, false)
      uut.unlock_all();
      // Bandwidth (MHz) [0.000024140625 - 14 MHz]
      // @TODO Check Values
      // ================================================
      //  LOWER BOUNDS
      TEST(*it, bw, 0.000023, true, 0.000001, false)
      uut.unlock_all();
      TEST(*it, bw, 0.000024140625, true, 0.000001, true )
      uut.unlock_all();
      // MEDIAN BOUND
      TEST(*it, bw, 10.     , true, 0.000001, true )
      uut.unlock_all();
      // UPPER BOUNDS
      TEST(*it, bw, 14.     , true, 0.000001, true )
      uut.unlock_all();
      TEST(*it, bw, 14.01   , true, 0.000001, false)
      uut.unlock_all();
      // Sampling rate (Msps) [~0.000255 - 15.36 Msps]
      // @TODO Check Values
      // ================================================
      // LOWER BOUNDS
      TEST(*it, fs, 0.000253, true, 0.000001, false)
      uut.unlock_all();
      TEST(*it, fs, 0.000255, true, 0.000001, true )
      uut.unlock_all();
      // MEDIAN BOUND
      TEST(*it, fs, 10.     , true, 0.000001, true )
      uut.unlock_all();
      // UPPER BOUND
      TEST(*it, fs, 15.36   , true, 0.000001, true )
      uut.unlock_all();
      TEST(*it, fs, 15.37   , true, 0.000001, false)
      uut.unlock_all();
      // Samples are complex
      // ================================================
      TEST(*it, sc, 0       , false,0.000001, false)
      uut.unlock_all();
      TEST(*it, sc, 1       , false,0.000001, true )
      uut.unlock_all();
      TEST(*it, sc, 2       , false,0.000001, false)
      uut.unlock_all();
      // Gain Mode
      // ================================================
      TEST(*it, gm, -1      , false,0.000001, false)
      uut.unlock_all();
      TEST(*it, gm, 0       , false,0.000001, true )
      uut.unlock_all();
      TEST(*it, gm, 1       , false,0.000001, true )
      uut.unlock_all();
      TEST(*it, gm, 2       , false,0.000001, false)
      uut.unlock_all();
      // Gain dB
      // ================================================
      // Unconditional Constraints
      // ------------------------------------------------
      TEST(*it, gn, -11.    , true ,0.000001, false)
      uut.unlock_all();
      TEST(*it, gn, -10.    , true ,0.000001, true )
      uut.unlock_all();
      TEST(*it, gn, -3.     , true ,0.000001, true )
      uut.unlock_all();
      TEST(*it, gn, -1.     , true ,0.000001, true )
      uut.unlock_all();
      TEST(*it, gn, 0.      , true ,0.000001, true )
      uut.unlock_all();
      TEST(*it, gn, 62.     , true ,0.000001, true )
      uut.unlock_all();
      TEST(*it, gn, 71.     , true ,0.000001, true )
      uut.unlock_all();
      TEST(*it, gn, 73.     , true ,0.000001, true )
      uut.unlock_all();
      TEST(*it, gn, 74.     , true ,0.000001, false)
      uut.unlock_all();
      // Conditional Constrains
      // ================================================
      // If fc [70 - 1300]; Possible Gain: -1 - 73 dB
      // LOWER BOUNDS
      // ------------------------------------------------
      TEST(*it, fc, 70.01   , true, 0.000001, true )
      TEST(*it, gn, -2.     , true ,0.000001, false)
      uut.unlock_all();
      TEST(*it, fc, 1299.01 , true, 0.000001, true )
      TEST(*it, gn, -2.     , true ,0.000001, false)
      uut.unlock_all();
      TEST(*it, fc, 70.01   , true, 0.000001, true )
      TEST(*it, gn, -1.     , true ,0.000001, true )
      uut.unlock_all();
      TEST(*it, fc, 1299.01 , true, 0.000001, true )
      TEST(*it, gn, -1.     , true ,0.000001, true )
      uut.unlock_all();
      // MEDIAN BOUND
      // ------------------------------------------------
      TEST(*it, fc, 70.01   , true, 0.000001, true )
      TEST(*it, gn, 50.     , true ,0.000001, true )
      uut.unlock_all();
      TEST(*it, fc, 1299.01 , true, 0.000001, true )
      TEST(*it, gn, 50.     , true ,0.000001, true )
      uut.unlock_all();
      // UPPER BOUNDS
      // ------------------------------------------------
      TEST(*it, fc, 70.01   , true, 0.000001, true )
      TEST(*it, gn, 73.     , true ,0.000001, true )
      uut.unlock_all();
      TEST(*it, fc, 1299.01 , true, 0.000001, true )
      TEST(*it, gn, 73.     , true ,0.000001, true )
      uut.unlock_all();
      TEST(*it, fc, 70.01   , true, 0.000001, true )
      TEST(*it, gn, 74.     , true ,0.000001, false)
      uut.unlock_all();
      TEST(*it, fc, 1299.01 , true, 0.000001, true )
      TEST(*it, gn, 74.     , true ,0.000001, false)
      uut.unlock_all();
      // If fc [1300 - 4000); Possible Gain: -3 - 71 dB
      // LOWER BOUNDS
      // ------------------------------------------------
      TEST(*it, fc, 1300.01 , true, 0.000001, true )
      TEST(*it, gn, -4      , true ,0.000001, false)
      uut.unlock_all();
      TEST(*it, fc, 3999.01 , true, 0.000001, true )
      TEST(*it, gn, -4      , true ,0.000001, false)
      uut.unlock_all();
      TEST(*it, fc, 1300.01 , true, 0.000001, true )
      TEST(*it, gn, -3.     , true ,0.000001, true )
      uut.unlock_all();
      TEST(*it, fc, 3999.01 , true, 0.000001, true )
      TEST(*it, gn, -3.     , true ,0.000001, true )
      uut.unlock_all();
      // MEDIAN BOUND
      // ------------------------------------------------
      TEST(*it, fc, 1300.01 , true, 0.000001, true )
      TEST(*it, gn, 50.     , true ,0.000001, true )
      uut.unlock_all();
      TEST(*it, fc, 3999.01 , true, 0.000001, true )
      TEST(*it, gn, 50.     , true ,0.000001, true )
      uut.unlock_all();
      // UPPER BOUNDS
      // ------------------------------------------------
      TEST(*it, fc, 1300.01 , true, 0.000001, true )
      TEST(*it, gn, 71.     , true ,0.000001, true )
      uut.unlock_all();
      TEST(*it, fc, 3999.01 , true, 0.000001, true )
      TEST(*it, gn, 71.     , true ,0.000001, true )
      uut.unlock_all();
      TEST(*it, fc, 1300.01 , true, 0.000001, true )
      TEST(*it, gn, 72.     , true ,0.000001, false)
      uut.unlock_all();
      TEST(*it, fc, 3999.01 , true, 0.000001, true )
      TEST(*it, gn, 72.     , true ,0.000001, false)
      uut.unlock_all();
      // If fc [4000 - 6000]; Possible Gain: -10 - 62 dB
      // LOWER BOUNDS
      // ------------------------------------------------
      TEST(*it, fc, 4000.01 , true, 0.000001, true )
      TEST(*it, gn, -11.    , true ,0.000001, false)
      uut.unlock_all();
      TEST(*it, fc, 5999.01 , true, 0.000001, true )
      TEST(*it, gn, -11.    , true ,0.000001, false)
      uut.unlock_all();
      TEST(*it, fc, 4000.01 , true, 0.000001, true )
      TEST(*it, gn, -10.    , true ,0.000001, true )
      uut.unlock_all();
      TEST(*it, fc, 5999.01 , true, 0.000001, true )
      TEST(*it, gn, -10.    , true ,0.000001, true )
      uut.unlock_all();
      // MEDIAN BOUND
      // ------------------------------------------------
      TEST(*it, fc, 4000.01 , true, 0.000001, true )
      TEST(*it, gn, 50.     , true ,0.000001, true )
      uut.unlock_all();
      TEST(*it, fc, 5999.01 , true, 0.000001, true )
      TEST(*it, gn, 50.     , true ,0.000001, true )
      // UPPER BOUNDS
      // ------------------------------------------------
      TEST(*it, fc, 4000.01 , true, 0.000001, true )
      TEST(*it, gn, 62.     , true ,0.000001, true )
      uut.unlock_all();
      TEST(*it, fc, 5999.01 , true, 0.000001, true )
      TEST(*it, gn, 62.     , true ,0.000001, true )
      uut.unlock_all();
      TEST(*it, fc, 4000.01 , true, 0.000001, true )
      TEST(*it, gn, 63.     , true ,0.000001, false)
      uut.unlock_all();
      TEST(*it, fc, 5999.01 , true, 0.000001, true )
      TEST(*it, gn, 63.     , true ,0.000001, false)
      uut.unlock_all();
    }
    // TX CHANNEL
    std::vector<const char*> data_stream_tx;
    data_stream_tx.push_back("tx1");
    data_stream_tx.push_back("tx2");
    for(auto it=data_stream_tx.begin (); it!=data_stream_tx.end(); ++it) {
      // direction
      // ================================================
      TEST(*it, di, (int32_t)data_stream_direction_t::rx, false, 0., false);
      uut.unlock_all();
      TEST(*it, di, (int32_t)data_stream_direction_t::tx, false, 0., true);
      uut.unlock_all();
      // Tuning Freq (70 MHz - 6000 MHz)
      // ================================================
      //  LOWER BOUNDS
      TEST(*it, fc, 69.99   , true, 0.000001, false)
      uut.unlock_all();
      TEST(*it, fc, 70.     , true, 0.000001, true )
      uut.unlock_all();
      // MEDIAN BOUND
      TEST(*it, fc, 3000.   , true, 0.000001, true )
      uut.unlock_all();
      // UPPER BOUNDS
      TEST(*it, fc, 6000.   , true, 0.000001, true )
      uut.unlock_all();
      TEST(*it, fc, 6001.01 , true, 0.000001, false)
      uut.unlock_all();
      // Bandwidth (MHz) [0.000024140625 - 14 MHz]
      // @TODO Check Values
      // ================================================
      //  LOWER BOUNDS
      TEST(*it, bw, 0.000023, true, 0.000001, false)
      uut.unlock_all();
      TEST(*it, bw, 0.000024140625, true, 0.000001, true )
      uut.unlock_all();
      // MEDIAN BOUND
      TEST(*it, bw, 14.     , true, 0.000001, true )
      uut.unlock_all();
      // UPPER BOUNDS
      TEST(*it, bw, 14.     , true, 0.000001, true )
      uut.unlock_all();
      TEST(*it, bw, 14.01   , true, 0.000001, false)
      uut.unlock_all();
      // Sampling rate (Msps) [~0.000255 - 15.36 Msps]
      // @TODO Check Values
      // ================================================
      // LOWER BOUNDS
      TEST(*it, fs, 0.000253, true, 0.000001, false)
      uut.unlock_all();
      TEST(*it, fs, 0.000255, true, 0.000001, true )
      uut.unlock_all();
      // MEDIAN BOUND
      TEST(*it, fs, 32.     , true, 0.000001, true )
      uut.unlock_all();
      // UPPER BOUND
      TEST(*it, fs, 15.36   , true, 0.000001, true )
      uut.unlock_all();
      TEST(*it, fs, 15.37   , true, 0.000001, false)
      uut.unlock_all();
      // Samples are complex
      // ================================================
      TEST(*it, sc, 0       , false,0.000001, false)
      uut.unlock_all();
      TEST(*it, sc, 1       , false,0.000001, true )
      uut.unlock_all();
      TEST(*it, sc, 2       , false,0.000001, false)
      uut.unlock_all();
      // Gain Mode
      // ================================================
      TEST(*it, gm, 0       , false,0.000001, false)
      uut.unlock_all();
      TEST(*it, gm, 1       , false,0.000001, true )
      uut.unlock_all();
      TEST(*it, gm, 2       , false,0.000001, false)
      uut.unlock_all();
      // Gain (dB) (-89.75 - 0)
      // ================================================
      // LOWER BOUNDS
      TEST(*it, gn, -89.76  , true, 0.000001, false)
      uut.unlock_all();
      TEST(*it, gn, -89.75  , true, 0.000001, true )
      uut.unlock_all();
      // MEDIAN BOUND
      TEST(*it, gn, -40.    , true, 0.000001, true )
      uut.unlock_all();
      // UPPER BOUND
      TEST(*it, gn, 0.      , true, 0.000001, true )
      uut.unlock_all();
      TEST(*it, gn, 0.01    , true, 0.000001, false)
      /// @TODO test gain conditional constraints
    }
    std::cout << "[INFO] PASS\n";
  }
  catch(std::string& err) {
    ret = 1;
    std::cout << err;
  }
  return ret;
}

#ifdef DISABLE_AD9361
class SlaveDummy {
  public:
  template<typename T> void getProperty(const char* name, T& val) {
  }
  template<typename T> void setProperty(const char* name, T val) {
  }
  uint8_t get_output_port_0() {
  }
  uint8_t get_output_port_1() {
  }
  uint8_t get_output_port_2() {
  }
  void set_output_port_0(uint8_t val) {
  }
  void set_output_port_1(uint8_t val) {
  }
  void set_output_port_2(uint8_t val) {
  }
  void set_force_two_r_two_t_timing(uint8_t val) {
  }
  void set_ENABLE_force_set(uint8_t val) {
  }
  void set_TXNRX_force_set(uint8_t val) {
  }
  void set_Half_Duplex_Mode(uint8_t val) {
  }
  void set_ENSM_Pin_Control(uint8_t val) {
  }
  void set_Level_Mode(uint8_t val) {
  }
  void set_FDD_External_Control_Enable(uint8_t val) {
  }
  void set_config_is_two_r(uint8_t val) {
  }
  void set_config_is_two_t(uint8_t val) {
  }
};
#endif

int main() {
  int ret0 = test_AD9361Configurator();
  if(ret0 != 0) {
    std::cout << "[ERROR]\n";
    return ret0;
  }
  int ret1 = test_AD9361DDCConfigurator();
  if(ret1 != 0) {
    std::cout << "[ERROR]\n";
    return ret1;
  }
  return ret1;
}