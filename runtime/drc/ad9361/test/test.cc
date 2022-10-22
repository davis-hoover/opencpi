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

void test_AD9361Configurator_direction(
    AD9361Configurator& uut,
    const char* chan,bool rx) {
  if(rx) {
    uut.unlock_all();
    TEST(chan, di, (int32_t)data_stream_direction_t::rx, false, 0., true);
    uut.unlock_all();
    TEST(chan, di, (int32_t)data_stream_direction_t::tx, false, 0., false);
  }
  else {
    uut.unlock_all();
    TEST(chan, di, (int32_t)data_stream_direction_t::rx, false, 0., false);
    uut.unlock_all();
    TEST(chan, di, (int32_t)data_stream_direction_t::tx, false, 0., true);
  }
}

void test_AD9361Configurator_tuning_freq(
    AD9361Configurator& uut,
    const char* chan) {
  uut.unlock_all();
  TEST(chan, fc, 69.99   , true, 0.000001, false)
  uut.unlock_all();
  TEST(chan, fc, 70.     , true, 0.000001, true )
  uut.unlock_all();
  TEST(chan, fc, 3000.   , true, 0.000001, true )
  uut.unlock_all();
  TEST(chan, fc, 6000.   , true, 0.000001, true )
  uut.unlock_all();
  TEST(chan, fc, 6001.01 , true, 0.000001, false)
}

void test_AD9361Configurator_bandwidth(
    AD9361Configurator& uut,
    const char* chan,bool rx) {
  ///@TODO Check Values
    // - Does NOT match Data sheet
    // - Datasheet: <200 KHz - 56 MHz
    // - Not sure where 400 KHz comes from
  if(rx) {
    uut.unlock_all();
    TEST(chan, bw, 0.39    , true, 0.000001, false)
    uut.unlock_all();
    TEST(chan, bw, 0.4     , true, 0.000001, true )
    uut.unlock_all();
    TEST(chan, bw, 30.     , true, 0.000001, true )
    uut.unlock_all();
    TEST(chan, bw, 56.     , true, 0.000001, true )
    uut.unlock_all();
    TEST(chan, bw, 56.01   , true, 0.000001, false)
  }
  else {
    uut.unlock_all();
    TEST(chan, bw, 1.24    , true, 0.000001, false)
    uut.unlock_all();
    TEST(chan, bw, 1.25    , true, 0.000001, true )
    uut.unlock_all();
    TEST(chan, bw, 30.     , true, 0.000001, true )
    uut.unlock_all();
    TEST(chan, bw, 40.     , true, 0.000001, true )
    uut.unlock_all();
    TEST(chan, bw, 40.01   , true, 0.000001, false)
  }
}

void test_AD9361Configurator_sampling_rate(
    AD9361Configurator& uut,
    const char* chan) {
  uut.unlock_all();
  TEST(chan, fs, 2.08    , true, 0.000001, false)
  uut.unlock_all();
  TEST(chan, fs, 2.083334, true, 0.000001, true )
  uut.unlock_all();
  TEST(chan, fs, 32.     , true, 0.000001, true )
  uut.unlock_all();
  TEST(chan, fs, 61.44   , true, 0.000001, true )
  uut.unlock_all();
  TEST(chan, fs, 61.45   , true, 0.000001, false)
}

void test_AD9361Configurator_samples_are_complex(
    AD9361Configurator& uut,
    const char* chan) {
  uut.unlock_all();
  TEST(chan, sc, 0       , false,0.000001, false)
  uut.unlock_all();
  TEST(chan, sc, 1       , false,0.000001, true )
  uut.unlock_all();
  TEST(chan, sc, 2       , false,0.000001, false)
}

void test_AD9361Configurator_gain_mode(
    AD9361Configurator& uut,
    const char* chan,bool rx) {
  uut.unlock_all();
  TEST(chan, gm, -1      , false,0.000001, false)
  uut.unlock_all();
  TEST(chan, gm, 0       , false,0.000001, rx   )
  uut.unlock_all();
  TEST(chan, gm, 1       , false,0.000001, true )
  uut.unlock_all();
  TEST(chan, gm, 2       , false,0.000001, false)
}

void test_AD9361Configurator_rx_gain_unconditional(
    AD9361Configurator& uut,
    const char* chan) {
  /*uut.unlock_all();
  TEST(chan, gn, -11.    , true ,0.000001, false)
  uut.unlock_all();
  TEST(chan, gn, -10.    , true ,0.000001, true )
  uut.unlock_all();
  TEST(chan, gn, -4.     , true ,0.000001, true )
  uut.unlock_all();
  TEST(chan, gn, -3.     , true ,0.000001, true )*/
  uut.unlock_all();
  TEST(chan, gn, -1.     , true ,0.000001, true )
  ///@TODO remove below test
  uut.unlock_all();
  TEST(chan, gn, -2.     , true ,0.000001, false)
  uut.unlock_all();
  TEST(chan, gn, 0.      , true ,0.000001, true )
  uut.unlock_all();
  TEST(chan, gn, 62.     , true ,0.000001, true )
  ///@TODO remove below test
  uut.unlock_all();
  TEST(chan, gn, 63.     , true ,0.000001, false)
  /*uut.unlock_all();
  TEST(chan, gn, 63.     , true ,0.000001, true )
  uut.unlock_all();
  TEST(chan, gn, 71.     , true ,0.000001, true )
  uut.unlock_all();
  TEST(chan, gn, 72.     , true ,0.000001, true )
  uut.unlock_all();
  TEST(chan, gn, 73.     , true ,0.000001, true )
  uut.unlock_all();
  TEST(chan, gn, 73.     , true ,0.000001, true )
  ///@TODO / FIXME fails rx2
  //uut.unlock_all();
  //TEST(chan, gn, 74.     , true ,0.000001, false)*/
}

// @brief if fc [70 - 1300 MHz], possible gain: -1 - 73 dB
void test_AD9361Configurator_rx_gain_conditional_70(
    AD9361Configurator& uut,
    const char* chan) {
  // lower bounds
  uut.unlock_all();
  TEST(chan, fc, 70.01   , true, 0.000001, true )
  TEST(chan, gn, -2.     , true ,0.000001, false)
  uut.unlock_all();
  TEST(chan, fc, 1299.01 , true, 0.000001, true )
  TEST(chan, gn, -2.     , true ,0.000001, false)
  uut.unlock_all();
  TEST(chan, fc, 70.01   , true, 0.000001, true )
  TEST(chan, gn, -1.     , true ,0.000001, true )
  uut.unlock_all();
  TEST(chan, fc, 1299.01 , true, 0.000001, true )
  TEST(chan, gn, -1.     , true ,0.000001, true )
  // middle
  uut.unlock_all();
  TEST(chan, fc, 70.01   , true, 0.000001, true )
  TEST(chan, gn, 50.     , true ,0.000001, true )
  uut.unlock_all();
  TEST(chan, fc, 1299.01 , true, 0.000001, true )
  TEST(chan, gn, 50.     , true ,0.000001, true )
  // upper bounds
  uut.unlock_all();
  TEST(chan, fc, 70.01   , true, 0.000001, true )
  TEST(chan, gn, 73.     , true ,0.000001, true )
  uut.unlock_all();
  TEST(chan, fc, 1299.01 , true, 0.000001, true )
  TEST(chan, gn, 73.     , true ,0.000001, true )
  uut.unlock_all();
  TEST(chan, fc, 70.01   , true, 0.000001, true )
  TEST(chan, gn, 74.     , true ,0.000001, false)
  uut.unlock_all();
  TEST(chan, fc, 1299.01 , true, 0.000001, true )
  TEST(chan, gn, 74.     , true ,0.000001, false)
}

// @brief if fc [1300 - 4000 MHz), possible gain: -3 - 71 dB
void test_AD9361Configurator_rx_gain_conditional_1300(
    AD9361Configurator& uut,
    const char* chan) {
  // lower bounds
  uut.unlock_all();
  TEST(chan, fc, 1300.01 , true, 0.000001, true )
  TEST(chan, gn, -4      , true ,0.000001, false)
  uut.unlock_all();
  TEST(chan, fc, 3999.01 , true, 0.000001, true )
  TEST(chan, gn, -4      , true ,0.000001, false)
  uut.unlock_all();
  TEST(chan, fc, 1300.01 , true, 0.000001, true )
  TEST(chan, gn, -3.     , true ,0.000001, true )
  uut.unlock_all();
  TEST(chan, fc, 3999.01 , true, 0.000001, true )
  TEST(chan, gn, -3.     , true ,0.000001, true )
  // middle
  uut.unlock_all();
  TEST(chan, fc, 1300.01 , true, 0.000001, true )
  TEST(chan, gn, 50.     , true ,0.000001, true )
  uut.unlock_all();
  TEST(chan, fc, 3999.01 , true, 0.000001, true )
  TEST(chan, gn, 50.     , true ,0.000001, true )
  // upper bounds
  uut.unlock_all();
  TEST(chan, fc, 1300.01 , true, 0.000001, true )
  TEST(chan, gn, 71.     , true ,0.000001, true )
  uut.unlock_all();
  TEST(chan, fc, 3999.01 , true, 0.000001, true )
  TEST(chan, gn, 71.     , true ,0.000001, true )
  uut.unlock_all();
  TEST(chan, fc, 1300.01 , true, 0.000001, true )
  TEST(chan, gn, 72.     , true ,0.000001, false)
  uut.unlock_all();
  TEST(chan, fc, 3999.01 , true, 0.000001, true )
  TEST(chan, gn, 72.     , true ,0.000001, false)
}

// @brief if fc [4000 - 6000 MHz], possible gain: -10 - 62 dB
void test_AD9361Configurator_rx_gain_conditional_4000(
    AD9361Configurator& uut,
    const char* chan) {
  // lower bounds
  uut.unlock_all();
  TEST(chan, fc, 4000.01 , true, 0.000001, true )
  TEST(chan, gn, -11.    , true ,0.000001, false)
  uut.unlock_all();
  TEST(chan, fc, 5999.01 , true, 0.000001, true )
  TEST(chan, gn, -11.    , true ,0.000001, false)
  uut.unlock_all();
  TEST(chan, fc, 4000.01 , true, 0.000001, true )
  TEST(chan, gn, -10.    , true ,0.000001, true )
  uut.unlock_all();
  TEST(chan, fc, 5999.01 , true, 0.000001, true )
  TEST(chan, gn, -10.    , true ,0.000001, true )
  // median bounds
  uut.unlock_all();
  TEST(chan, fc, 4000.01 , true, 0.000001, true )
  TEST(chan, gn, 50.     , true ,0.000001, true )
  uut.unlock_all();
  TEST(chan, fc, 5999.01 , true, 0.000001, true )
  TEST(chan, gn, 50.     , true ,0.000001, true )
  // upper bounds
  uut.unlock_all();
  TEST(chan, fc, 4000.01 , true, 0.000001, true )
  TEST(chan, gn, 62.     , true ,0.000001, true )
  uut.unlock_all();
  TEST(chan, fc, 5999.01 , true, 0.000001, true )
  TEST(chan, gn, 62.     , true ,0.000001, true )
  uut.unlock_all();
  TEST(chan, fc, 4000.01 , true, 0.000001, true )
  TEST(chan, gn, 63.     , true ,0.000001, false)
  uut.unlock_all();
  TEST(chan, fc, 5999.01 , true, 0.000001, true )
  TEST(chan, gn, 63.     , true ,0.000001, false)
}

void test_AD9361Configurator_rx_gain_conditional(
    AD9361Configurator& uut,
    const char* chan) {
  test_AD9361Configurator_rx_gain_conditional_70(uut,chan);
  test_AD9361Configurator_rx_gain_conditional_1300(uut,chan);
  test_AD9361Configurator_rx_gain_conditional_4000(uut,chan);
}

void test_AD9361Configurator_tx_gain_unconditional(
    AD9361Configurator& uut,
    const char* chan) {
  uut.unlock_all();
  TEST(chan, gn, -89.76  , true, 0.000001, false)
  uut.unlock_all();
  TEST(chan, gn, -89.75  , true, 0.000001, true )
  uut.unlock_all();
  TEST(chan, gn, -40.    , true, 0.000001, true )
  uut.unlock_all();
  TEST(chan, gn, 0.      , true, 0.000001, true )
  TEST(chan, gn, 0.01    , true, 0.000001, false)
}

void test_AD9361Configurator_gain(
    AD9361Configurator& uut,
    const char* chan,bool rx) {
  if(rx) {
    test_AD9361Configurator_rx_gain_unconditional(uut,chan);
    /// @TODO enable below test(s)
    //test_AD9361Configurator_rx_gain_conditional(uut,chan);
  }
  else {
    test_AD9361Configurator_tx_gain_unconditional(uut,chan);
  }
}

void test_AD9361Configurator_channel(
    AD9361Configurator& uut,
    const char* chan,bool rx) {
  test_AD9361Configurator_direction(uut,chan,rx);
  test_AD9361Configurator_tuning_freq(uut,chan);
  test_AD9361Configurator_bandwidth(uut,chan,rx);
  test_AD9361Configurator_sampling_rate(uut,chan);
  test_AD9361Configurator_samples_are_complex(uut,chan);
  test_AD9361Configurator_gain_mode(uut,chan,rx);
  test_AD9361Configurator_gain(uut,chan,rx);
}

void test_AD9361Configurator_channels(
    AD9361Configurator& uut,
    bool rx) {
  std::vector<const char*> data_streams;
  if(rx) {
    data_streams.push_back("rx1");
    data_streams.push_back("rx2");
  }
  else {
    data_streams.push_back("tx1");
    data_streams.push_back("tx2");
  }
  for(auto it=data_streams.begin(); it!=data_streams.end(); ++it) {
    test_AD9361Configurator_channel(uut,*it,rx);
  }
}

int test_AD9361Configurator() {
  int ret = 0;
  AD9361Configurator uut;
  try {
    bool rx = true;
    test_AD9361Configurator_channels(uut,rx);
    rx = false;
    test_AD9361Configurator_channels(uut,rx);
    std::cout << "[INFO] PASS\n";
  }
  catch(std::string& err) {
    ret = 1;
    std::cout << err;
  }
  return ret;
}

/*void test_AD9361DDCConfigurator_tuning_freq(
    AD9361DDCConfigurator& uut,
    const char* chan) {
  uut.unlock_all();
  TEST(chan, fc, 39.27   , true, 0.000001, false)
  uut.unlock_all();
  TEST(chan, fc, 39.28   , true, 0.000001, true )
  uut.unlock_all();
  TEST(chan, fc, 3000.   , true, 0.000001, true )
  uut.unlock_all();
  TEST(chan, fc, 6030.7190625 , true, 0.000001, true )
  uut.unlock_all();
  TEST(chan, fc, 6039.71907, true, 0.000001, false)
}

void test_AD9361DDCConfigurator_bandwidth(
    AD9361DDCConfigurator& uut,
    const char* chan,bool rx) {
  ///@TODO Check Values
    // - Does NOT match Data sheet
    // - Datasheet: <200 KHz - 56 MHz
    // - Not sure where 400 KHz comes from
  if(rx) {
    uut.unlock_all();
    TEST(chan, bw, 0.000023, true, 0.000001, false)
    uut.unlock_all();
    TEST(chan, bw, 0.000024140625, true, 0.000001, true )
    uut.unlock_all();
    TEST(chan, bw, 10.     , true, 0.000001, true )
    uut.unlock_all();
    TEST(chan, bw, 14.     , true, 0.000001, true )
    uut.unlock_all();
    TEST(chan, bw, 14.01   , true, 0.000001, false)
  }
  else {
    uut.unlock_all();
    TEST(chan, bw, 1.24    , true, 0.000001, false)
    uut.unlock_all();
    TEST(chan, bw, 1.25    , true, 0.000001, true )
    uut.unlock_all();
    TEST(chan, bw, 30.     , true, 0.000001, true )
    uut.unlock_all();
    TEST(chan, bw, 40.     , true, 0.000001, true )
    uut.unlock_all();
    TEST(chan, bw, 40.01   , true, 0.000001, false)
  }
}

void test_AD9361DDCConfigurator_sampling_rate(
    AD9361DDCConfigurator& uut,
    const char* chan) {
  uut.unlock_all();
  TEST(chan, fs, 0.000253, true, 0.000001, false)
  uut.unlock_all();
  TEST(chan, fs, 0.000255, true, 0.000001, true )
  uut.unlock_all();
  TEST(chan, fs, 10.     , true, 0.000001, true )
  uut.unlock_all();
  TEST(chan, fs, 15.36   , true, 0.000001, true )
  uut.unlock_all();
  TEST(chan, fs, 15.37   , true, 0.000001, false)
}

void test_AD9361DDCConfigurator_gain(
    AD9361DDCConfigurator& uut,
    const char* chan,bool rx) {
  if(rx) {
    test_AD9361DDCConfigurator_rx_gain_unconditional(uut,chan);
    /// @TODO enable below test(s)
    //test_AD9361DDCConfigurator_rx_gain_conditional(uut,chan);
  }
  else {
    test_AD9361DDCConfigurator_tx_gain_unconditional(uut,chan);
  }
}

void test_AD9361DDCConfigurator_channel(
    AD9361DDCConfigurator& uut,
    const char* chan,bool rx) {
  test_AD9361DDCConfigurator_direction(uut,chan,rx);
  test_AD9361DDCConfigurator_tuning_freq(uut,chan);
  test_AD9361DDCConfigurator_bandwidth(uut,chan,rx);
  test_AD9361DDCConfigurator_sampling_rate(uut,chan);
  test_AD9361DDCConfigurator_samples_are_complex(uut,chan);
  test_AD9361DDCConfigurator_gain_mode(uut,chan,rx);
  test_AD9361DDCConfigurator_gain(uut,chan,rx);
}

void test_AD9361DDCConfigurator_channels(
    AD9361DDCConfigurator& uut,
    bool rx) {
  std::vector<const char*> data_streams;
  if(rx) {
    data_streams.push_back("rx1");
    data_streams.push_back("rx2");
  }
  else {
    data_streams.push_back("tx1");
    data_streams.push_back("tx2");
  }
  for(auto it=data_streams.begin(); it!=data_streams.end(); ++it) {
    test_AD9361DDCConfigurator_channel(uut,*it,rx);
  }
}

int test_AD9361DDCConfigurator() {
  int ret = 0;
  AD9361DDCConfigurator uut;
  try {
    bool rx = true;
    test_AD9361DDCConfigurator_channels(uut,rx);
    rx = false;
    test_AD9361DDCConfigurator_channels(uut,rx);
    std::cout << "[INFO] PASS\n";
  }
  catch(std::string& err) {
    ret = 1;
    std::cout << err;
  }
  return ret;
}*/

int main() {
  int ret = test_AD9361Configurator();
  /*if(ret == 0) {
    ret = test_AD9361DDCConfigurator();
  }*/
  return ret;
}
