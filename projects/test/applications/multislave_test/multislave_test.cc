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

#include <iostream>
#include <unistd.h>
#include <cstdio>
#include <cassert>
#include <string>
#include <math.h>
#include "OcpiApi.hh"

namespace OA=OCPI::API;
double EPSILON = 0.00000001;

inline bool isAlmostEqual(double a, double b)
{
    return fabs(a - b) < EPSILON;
}

std::string checkWkr1Values(OCPI::API::Application* app, std::string comp_name)
{
  std::string temp_string;
  std::string expected_str;

  app->getProperty(comp_name.c_str(), "my_string", temp_string);
  if (temp_string != "test_string"){
    return comp_name + ".my_string is not set correctly:" + temp_string;
  }

  app->getProperty(comp_name.c_str(), "my_enum", temp_string);
  if (temp_string != "third_enum"){
    return comp_name + ".my_enum is not set correctly. Was :" + temp_string +
              " and should be : third_enum" ;
  }
  expected_str = "struct_bool true,struct_ulong 10,struct_char K";
  app->getProperty(comp_name.c_str(), "test_struct", temp_string);
  if (temp_string != expected_str){
      return comp_name + ".test_struct is not set correctly.  Was :" +
                temp_string + "\n should be : " + expected_str;
  }
  expected_str = "{struct_bool true,struct_ulong 20,struct_char D},"
                 "{struct_bool true,struct_ulong 21,struct_char E},"
                 "{struct_bool true,struct_ulong 22,struct_char F},"
                 "{struct_bool true,struct_ulong 23,struct_char G},"
                 "{struct_bool true,struct_ulong 24,struct_char H},"
                 "{struct_bool true,struct_ulong 25,struct_char I},"
                 "{struct_bool true,struct_ulong 26,struct_char J}";
  app->getProperty(comp_name.c_str(), "test_seq_of_structs", temp_string);
  if (temp_string != expected_str){
      return comp_name + ".test_seq_of_structs is not set correctly.  Was :" +
                temp_string + "\n should be : " + expected_str;
  }
  expected_str = "struct_bool true,struct_ulong 23,struct_char G";
  app->getProperty(comp_name + ".test_seq_of_structs", temp_string, OA::AccessList({3}));
  if (temp_string != expected_str){
      return comp_name + ".test_seq_of_structs[3] is not set correctly.  Was :" +
                temp_string + "\n should be : " + expected_str;
  }
  expected_str = "23";
  {
    OA::Property p(*app, comp_name + ".test_seq_of_structs");
    OA::ULong ul = p.getValue<OA::ULong>(OA::AccessList({3, "struct_ulong"}));
    if (ul != 23)
      return comp_name + ".test_seq_of_structs[3].struct_ulong is not set correctly.  Was :" +
	std::to_string((unsigned long long)ul) + "\n should be : " + expected_str;
  }
  app->getProperty(comp_name + ".test_seq_of_structs", temp_string, OA::AccessList({3, "struct_ulong"}));
  if (temp_string != expected_str){
      return comp_name + ".test_seq_of_structs[3].struct_ulong is not set correctly.  Was :" +
                temp_string + "\n should be : " + expected_str;
  }
  expected_str = "struct_char M,struct_ulong_seq {1,2,3}";
  app->getProperty(comp_name.c_str(), "test_struct_of_seq", temp_string);
  if (temp_string != expected_str){
      return comp_name + ".test_struct_of_seq is not set correctly.  Was :" +
                temp_string + "\n should be : " + expected_str;
  }
  expected_str = "1,2,3";
  app->getProperty(comp_name + ".test_struct_of_seq", temp_string, OA::AccessList({ "struct_ulong_seq" }));
  if (temp_string != expected_str) {
      return comp_name + ".test_struct_of_seq.struct_ulong_seq is not set correctly.  Was :" +
                temp_string + "\n should be : " + expected_str;
  }
  {
    OA::Property prop(*app, comp_name, "test_struct_of_seq");
    if (prop.getSequenceLength({"struct_ulong_seq"}) != 3)
      return comp_name + ".test_struct_of_seq.struct_ulong_seq is not of length 3";
  }
  expected_str = "that,that,that,that,that,that,that,that,that,that";
  app->getProperty(comp_name.c_str(), "test_array_of_str", temp_string);
  if (temp_string != expected_str){
      return comp_name + ".test_array_of_str is not set correctly.  Was :" +
                temp_string + "\n should be : " + expected_str;
  }
  expected_str = "0,10,20,30,40,50,60,70,80,90";
  app->getProperty(comp_name.c_str(), "test_array_ulong", temp_string);
  if (temp_string != expected_str){
      return comp_name + ".test_array_ulong is not set correctly.  Was :" +
                temp_string + "\n should be : " + expected_str;
  }
  expected_str = "{test_ulong 10,test_bool true,test_char A},"
                 "{test_ulong 11,test_bool true,test_char B},"
                 "{test_ulong 12,test_bool true,test_char C},"
                 "{test_ulong 13,test_bool true,test_char D},"
                 "{test_ulong 14,test_bool true,test_char E},"
                 "{test_ulong 15,test_bool true,test_char F},"
                 "{test_ulong 16,test_bool true,test_char G},"
                 "{test_ulong 17,test_bool true,test_char H},"
                 "{test_ulong 18,test_bool true,test_char I},"
                 "{test_ulong 19,test_bool true,test_char J}";
  app->getProperty(comp_name.c_str(), "test_array_of_struct", temp_string);
  if (temp_string != expected_str){
      return comp_name + ".test_array_of_struct is not set correctly.  Was :" +
                temp_string + "\n should be : " + expected_str;
  }
  expected_str = "1,2,3,4,6,7,8,100";
  app->getProperty(comp_name.c_str(), "test_seq_ulong", temp_string);
  if (temp_string != expected_str){
      return comp_name + ".test_seq_ulong is not set correctly.  Was :" +
                temp_string + "\n should be : " + expected_str;
  }
  expected_str = "11,12,13,14,16,17,18,101,102";
  app->getProperty(comp_name.c_str(), "test_seq_ushort", temp_string);
  if (temp_string != expected_str){
      return comp_name + ".test_seq_ushort is not set correctly.  Was :" +
                temp_string + "\n should be : " + expected_str;
  }
  expected_str = "13";
  app->getProperty(comp_name + ".test_seq_ushort", temp_string, OA::AccessList({2}));
  if (temp_string != expected_str){
      return comp_name + ".test_seq_ushort[2] is not set correctly.  Was :" +
                temp_string + "\n should be : " + expected_str;
  }
  {
    OA::Property p(*app, comp_name, "test_seq_ushort");
    assert(p.getSequenceLength() == 9);
  }
  expected_str = "23";
  expected_str = "one,two,three,four,five";
  app->getProperty(comp_name.c_str(), "test_seq_str", temp_string);
  if (temp_string != expected_str){
      return comp_name + ".test_seq_str is not set correctly.  Was :" +
                temp_string + "\n should be : " + expected_str;
  }
  expected_str = "{1,2,3,4,6,7,8,101,0},{1,2,3,4,6,7,8,102,0},{1,2,3,4,6,7,8,103,0},"
                 "{1,2,3,4,6,7,8,104,0},{1,2,3,4,6,7,8,105,0},{1,2,3,4,6,7,8,106,0},"
                 "{1,2,3,4,6,7,8,107,0},{1,2,3,4,6,7,8,108,0}";
  app->getProperty(comp_name.c_str(), "test_seq_of_ulong_arrays", temp_string);
  if (temp_string != expected_str){
      return comp_name + ".test_seq_of_ulong_arrays is not set correctly.  Was :" +
                temp_string + "\n should be : " + expected_str;
  }
  expected_str = "1,2,3,4,6,7,8,105,0";
  app->getProperty(comp_name + ".test_seq_of_ulong_arrays", temp_string, OA::AccessList({4}));
  if (temp_string != expected_str){
      return comp_name + ".test_seq_of_ulong_arrays[4] is not set correctly.  Was :" +
                temp_string + "\n should be : " + expected_str;
  }
  expected_str = "105";
  app->getProperty(comp_name + ".test_seq_of_ulong_arrays", temp_string, OA::AccessList({4,7}));
  if (temp_string != expected_str){
      return comp_name + ".test_seq_of_ulong_arrays[4][7] is not set correctly.  Was :" +
                temp_string + "\n should be : " + expected_str;
  }
  app->getProperty(comp_name + ".my_debug1", temp_string);
  if (temp_string != "123")
    return comp_name + ".my_debug1 not set to 123";
  if (app->getPropertyValue<OA::ULong>(comp_name + ".my_debug1") != 123)
    return comp_name + ".my_debug1 not set to 123";
  app->setProperty(comp_name + ".my_debug1", "34");
  return "";
}

std::string checkValues(OCPI::API::Application* app, std::string comp_name)
{
  std::string ret_val;
  double temp_double;
  unsigned long temp_ulong;
  bool temp_bool;
  char temp_char;
  float temp_float;
  long temp_long;
  //long long temp_longlong;
  short temp_short;
  unsigned char temp_uchar;
  //unsigned long long temp_ulonglong;
  unsigned short temp_ushort;
  std::string temp_string;

  app->getPropertyValue(comp_name, "test_double", temp_double);
  if (!isAlmostEqual(temp_double, 5.0)){
    ret_val = comp_name + ".test_double is not set correctly:" + std::to_string((long double)temp_double) ;
    return ret_val;
  }
  app->getPropertyValue(comp_name, "test_ulong", temp_ulong);
  if (temp_ulong != 10){
    ret_val = comp_name + ".test_ulong is not set correctly";
    return ret_val;
  }

  app->getPropertyValue(comp_name, "test_bool", temp_bool);
  if (temp_bool != true){
    ret_val = comp_name + ".test_bool is not set correctly";
    return ret_val;
  }
  app->getPropertyValue(comp_name, "test_char", temp_char);
  if (temp_char != 'F'){
    ret_val = comp_name + ".test_char is not set correctly";
    return ret_val;
  }
  app->getPropertyValue(comp_name, "test_float", temp_float);
  if (!isAlmostEqual(temp_float, 2.0)){
    ret_val = comp_name + ".test_float is not set correctly";
    return ret_val;
  }
  app->getPropertyValue(comp_name, "test_long", temp_long);
  if (temp_long != 25){
    ret_val = comp_name + ".test_long is not set correctly";
    return ret_val;
  }
  app->getPropertyValue(comp_name, "test_longlong", temp_long);
  if (temp_long != 250){
    ret_val = comp_name + ".test_longlong is not set correctly";
    return ret_val;
  }
  app->getPropertyValue(comp_name, "test_short", temp_short);
  if (temp_short != 6){
    ret_val = comp_name + ".test_short is not set correctly";
    return ret_val;
  }
  app->getPropertyValue(comp_name, "test_uchar", temp_uchar);
  if (temp_uchar != 'G'){
    ret_val = comp_name + ".test_uchar is not set correctly";
    return ret_val;
  }
  app->getPropertyValue(comp_name, "test_ulonglong", temp_ulong);
  if (temp_ulong != 350){
    ret_val = comp_name + ".test_ulonglong is not set correctly";
    return ret_val;
  }
  app->getPropertyValue(comp_name, "test_ushort", temp_ushort);
  if (temp_ushort != 16){
    ret_val = comp_name + ".test_ushort is not set correctly.  Was :" +
              std::to_string(static_cast<unsigned long long>(temp_ushort)) +
              " and should be : 16" ;
    return ret_val;
  }
  bool caught = false;
  bool shouldFail = comp_name == "comp3";
  try { app->setProperty(comp_name + ".my_debug1", "123"); } catch(...) { caught = true; }
  if (caught) {
    if (!shouldFail)
      return "setting debug property " + comp_name + "in a debug worker failed";
    std::cout << "app->setProperty(" + comp_name + ".my_debug1 failed as expected\n";
  } else {
    if (shouldFail)
      return "setting debug property " + comp_name + "in a non-debug worker did not fail";
    std::cout << "app->setProperty(" + comp_name + ".my_debug1 succeeded as expected\n";
  }
  caught = false;
  try { app->getPropertyValue<OA::ULong>(comp_name + ".my_debug1"); } catch(...) { caught = true; }
  if (caught) {
    if (!shouldFail)
      return "setting debug property " + comp_name + "in a debug worker failed";
    std::cout << "app->getPropertyValue(" + comp_name + ".my_debug1 failed as expected\n";
  } else {
    if (shouldFail)
      return "setting debug property " + comp_name + "in a non-debug worker did not fail";
    std::cout << "app->getPropertyValue(" + comp_name + ".my_debug1 succeeded as expected\n";
  }
  return ret_val;
}

static const char
*appWithSlave =
  "<Application>\n"
  "  <Instance component='comp1' name='comp1'>\n"
  "    <Property Name='my_string' Value='\"bad\"'></Property>\n"
  "  </Instance>\n"
  "  <Instance component='comp1' name='comp2'>\n"
  "    <Property Name='my_string' Value='\"bad\"'></Property>\n"
  "  </Instance>\n"
  "  <Instance component='comp2' name='comp3'/>\n"
  "  <Instance Name='proxy1' component='proxy1'>\n"
  "    <slave instance='comp2' slave='second_wkr1'/>\n"
  "    <slave instance='comp1' slave='first_wkr1'/>\n"
  "    <slave name='comp3'/>\n"
  "  </Instance>\n"
  "</Application>\n",
*appWithoutSlave =
  "<Application>\n"
  "  <Instance component='comp1' name='comp1'>\n"
  "    <Property Name='my_string' Value='\"bad\"'></Property>\n"
  "  </Instance>\n"
  "  <Instance component='comp1' name='comp2'>\n"
  "    <Property Name='my_string' Value='\"bad\"'></Property>\n"
  "  </Instance>\n"
  "  <Instance Name='proxy1' component='proxy1'>\n"
  "    <slave instance='comp2' slave='second_wkr1'/>\n"
  "    <slave instance='comp1' slave='first_wkr1'/>\n"
  "    <!-- <slave name='comp3'/> -->\n"
  "  </Instance>\n"
  "</Application>\n";

int main(int /*argc*/, char **argv)
{
  std::string platform;
  if (argv[1] && argv[2]) {
    platform = "comp2=";
    platform += argv[2];
  }
  // Reference OpenCPI_Application_Development document for an explanation of the ACI
  try
  {
    OA::PValue pvs[] = { OA::PVBool("verbose", true),
			 OA::PVBool("dump", true),
			 OA::PVBool("hidden", true),
			 OA::PVString(platform.empty() ? NULL : "platform", platform.c_str()),
			 OA::PVEnd };
    OCPI::API::Application app(argv[1] && argv[1][0] ? appWithoutSlave : appWithSlave, pvs);
    app.initialize(); // all resources have been allocated
    app.start();      // execution is started
    app.wait();       // wait until app is "done"
    app.finish();
    //app.dumpProperties();
    std::string err;
    err = checkValues(&app, "comp1");
    if (!err.empty())
    {
      std::cerr << "app failed: " << err << std::endl;
      return 2;
    }
    err = checkWkr1Values(&app, "comp1");
    if (!err.empty())
    {
      std::cerr << "app failed: " << err << std::endl;
      return 3;
    }
    err = checkValues(&app, "comp2");
    if (!err.empty())
    {
      std::cerr << "app failed: " << err << std::endl;
      return 4;
    }
    err = checkWkr1Values(&app, "comp2");
    if (!err.empty())
    {
      std::cerr << "app failed: " << err << std::endl;
      return 5;
    }
    if (app.getPropertyValue<bool>("proxy1", "wkr2Present"))
      err = checkValues(&app, "comp3");
    if (!err.empty())
    {
      std::cerr << "app failed: " << err << std::endl;
      return 6;
    }
  }
  catch (std::string &e)
  {
    std::cerr << "app failed: " << e << std::endl;
    return 1;
  }
  return 0;
}
