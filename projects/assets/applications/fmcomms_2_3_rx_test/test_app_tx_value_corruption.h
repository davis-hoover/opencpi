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

#ifndef _TEST_APP_TX_VALUE_CORRUPTION_H
#define _TEST_APP_TX_VALUE_CORRUPTION_H

#include "OcpiApi.hh" // OCPI::API namespace
#include "ocpi_component_prop_type_helpers.h" // ocpi_..._t types

#define APP_TX_CORRUPTION_FMCOMMS2_XML "app_tx_corruption_fmcomms2.xml"
#define APP_TX_CORRUPTION_FMCOMMS3_XML "app_tx_corruption_fmcomms3.xml"

namespace OA = OCPI::API;

bool did_pass_test_ocpi_app_tx_corruption_tx_rf_gain_dB()
{
  printf("TEST: ensure no corruption of tx rf_gain_dB\n");
  try
  {
    OCPI::API::Application app(APP_TX_CORRUPTION_FMCOMMS2_XML, NULL);
    app.initialize();
    app.start();
    if(!did_pass_test_expected_value_tx_rf_gain_dB(app, -13., (OA::Long) 13000)) { return false; }
    app.stop();
  }
  catch (std::string &e) {
    fprintf(stderr, "Exception thrown: %s\n", e.c_str());
    return false;
  }

  try
  {
    OCPI::API::Application app(APP_TX_CORRUPTION_FMCOMMS3_XML, NULL);
    app.initialize();
    app.start();
    if(!did_pass_test_expected_value_tx_rf_gain_dB(app, -13., (OA::Long) 13000)) { return false; }
    app.stop();
  }
  catch (std::string &e) {
    fprintf(stderr, "Exception thrown: %s\n", e.c_str());
    return false;
  }

  return true;
}

bool did_pass_test_ocpi_app_tx_corruption_tx_frequency_MHz()
{
  printf("TEST: ensure no corruption of tx frequency_MHz\n");
  try
  {
    OCPI::API::Application app(APP_TX_CORRUPTION_FMCOMMS2_XML, NULL);
    app.initialize();
    app.start();
    if(!did_pass_test_expected_value_tx_frequency_MHz(app, 2468.123, (OA::ULongLong) 2468123000)) { return false; }
    app.stop();
  }
  catch (std::string &e) {
    fprintf(stderr, "Exception thrown: %s\n", e.c_str());
    return false;
  }

  try
  {
    OCPI::API::Application app(APP_TX_CORRUPTION_FMCOMMS3_XML, NULL);
    app.initialize();
    app.start();
    if(!did_pass_test_expected_value_tx_frequency_MHz(app, 2468.123, (OA::ULongLong) 2468123000)) { return false; }
    app.stop();
  }
  catch (std::string &e) {
    fprintf(stderr, "Exception thrown: %s\n", e.c_str());
    return false;
  }

  return true;
}

bool did_pass_test_ocpi_app_tx_corruption_tx_bb_cutoff_frequency_MHz()
{
  printf("TEST: ensure no corruption of tx bb_cutoff_frequency_MHz\n");
  try
  {
    OCPI::API::Application app(APP_TX_CORRUPTION_FMCOMMS2_XML, NULL);
    app.initialize();
    app.start();
    if(!did_pass_test_expected_value_tx_bb_cutoff_frequency_MHz(app, 1.234567, (OA::ULong) 1234567)) { return false; }
    app.stop();
  }
  catch (std::string &e) {
    fprintf(stderr, "Exception thrown: %s\n", e.c_str());
    return false;
  }

  try
  {
    OCPI::API::Application app(APP_TX_CORRUPTION_FMCOMMS3_XML, NULL);
    app.initialize();
    app.start();
    if(!did_pass_test_expected_value_tx_bb_cutoff_frequency_MHz(app, 1.234567, (OA::ULong) 1234567)) { return false; }
    app.stop();
  }
  catch (std::string &e) {
    fprintf(stderr, "Exception thrown: %s\n", e.c_str());
    return false;
  }

  return true;

}

bool did_pass_test_ocpi_app_tx_value_corruption()
{
  if(!did_pass_test_ocpi_app_tx_corruption_tx_rf_gain_dB())             { return false; }
  // bb_gain_dB is unused for the fmcomms_2_3_tx.rcc worker
  if(!did_pass_test_ocpi_app_tx_corruption_tx_frequency_MHz())          { return false; }
  // we do not test tx_sample_rate_MHz because the ocpi.core.tx worker's sample_rate_MHz's value will always override the ocpi.core.tx worker's sample_rate_MHz property value (this is not a shortcoming of any worker but rather the very nature of how the AD961 works)
  // bb_cutoff_frequency_MHz is unused for the fmcomms_2_3_tx.rcc worker
  if(!did_pass_test_ocpi_app_tx_corruption_tx_bb_cutoff_frequency_MHz()) { return false; }

  return true;
}

#endif // _TEST_APP_TX_VALUE_CORRUPTION_H
