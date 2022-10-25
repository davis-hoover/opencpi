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

#ifndef _TEST_FMCOMMS2_3DRC_HH
#define _TEST_FMCOMMS2_3DRC_HH

#include <iostream>
#include "test.hh"
#define IS_LOCKING // this is still experimental
#include "FMCOMMS2_3DRC.hh"

void test_FMCOMMS2_3Configurator_direction(
    FMCOMMS2_3Configurator& uut,
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

void test_FMCOMMS2_3Configurator_tuning_freq(
    FMCOMMS2_3Configurator& uut,
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

void test_FMCOMMS2_3Configurator_bandwidth(
    FMCOMMS2_3Configurator& uut,
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

void test_FMCOMMS2_3Configurator_sampling_rate(
    FMCOMMS2_3Configurator& uut,
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

void test_FMCOMMS2_3Configurator_samples_are_complex(
    FMCOMMS2_3Configurator& uut,
    const char* chan) {
  uut.unlock_all();
  TEST(chan, sc, 0       , false,0.000001, false)
  uut.unlock_all();
  TEST(chan, sc, 1       , false,0.000001, true )
  uut.unlock_all();
  TEST(chan, sc, 2       , false,0.000001, false)
}

void test_FMCOMMS2_3Configurator_gain_mode(
    FMCOMMS2_3Configurator& uut,
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

void test_FMCOMMS2_3Configurator_rx_gain_unconditional(
    FMCOMMS2_3Configurator& uut,
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
void test_FMCOMMS2_3Configurator_rx_gain_conditional_70(
    FMCOMMS2_3Configurator& uut,
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
void test_FMCOMMS2_3Configurator_rx_gain_conditional_1300(
    FMCOMMS2_3Configurator& uut,
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
void test_FMCOMMS2_3Configurator_rx_gain_conditional_4000(
    FMCOMMS2_3Configurator& uut,
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

void test_FMCOMMS2_3Configurator_rx_gain_conditional(
    FMCOMMS2_3Configurator& uut,
    const char* chan) {
  test_FMCOMMS2_3Configurator_rx_gain_conditional_70(uut,chan);
  test_FMCOMMS2_3Configurator_rx_gain_conditional_1300(uut,chan);
  test_FMCOMMS2_3Configurator_rx_gain_conditional_4000(uut,chan);
}

void test_FMCOMMS2_3Configurator_tx_gain_unconditional(
    FMCOMMS2_3Configurator& uut,
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

void test_FMCOMMS2_3Configurator_gain(
    FMCOMMS2_3Configurator& uut,
    const char* chan,bool rx) {
  if(rx) {
    test_FMCOMMS2_3Configurator_rx_gain_unconditional(uut,chan);
    /// @TODO enable below test(s)
    //test_FMCOMMS2_3Configurator_rx_gain_conditional(uut,chan);
  }
  else {
    test_FMCOMMS2_3Configurator_tx_gain_unconditional(uut,chan);
  }
}

void test_FMCOMMS2_3Configurator_channel(
    FMCOMMS2_3Configurator& uut,
    const char* chan,bool rx) {
  test_FMCOMMS2_3Configurator_direction(uut,chan,rx);
  test_FMCOMMS2_3Configurator_tuning_freq(uut,chan);
  test_FMCOMMS2_3Configurator_bandwidth(uut,chan,rx);
  test_FMCOMMS2_3Configurator_sampling_rate(uut,chan);
  test_FMCOMMS2_3Configurator_samples_are_complex(uut,chan);
  test_FMCOMMS2_3Configurator_gain_mode(uut,chan,rx);
  test_FMCOMMS2_3Configurator_gain(uut,chan,rx);
}

void test_FMCOMMS2_3Configurator_channels(
    FMCOMMS2_3Configurator& uut,
    bool rx) {
  std::vector<const char*> data_streams;
  if(rx) {
    data_streams.push_back("rx1a");
    data_streams.push_back("rx2a");
  }
  else {
    data_streams.push_back("tx1a");
    data_streams.push_back("tx2a");
  }
  for(auto it=data_streams.begin(); it!=data_streams.end(); ++it) {
    test_FMCOMMS2_3Configurator_channel(uut,*it,rx);
  }
}

int test_FMCOMMS2_3Configurator() {
  int ret = 0;
  try {
    for(int32_t fmcomms_num=2; fmcomms_num<=3; fmcomms_num++) {
      FMCOMMS2_3Configurator uut(fmcomms_num);
      bool rx = true;
      test_FMCOMMS2_3Configurator_channels(uut,rx);
      rx = false;
      test_FMCOMMS2_3Configurator_channels(uut,rx);
    }
    std::cout << "[INFO] PASS\n";
  }
  catch(std::string& err) {
    ret = 1;
    std::cout << err;
  }
  return ret;
}

#endif // _TEST_FMCOMMS2_3DRC_HH
