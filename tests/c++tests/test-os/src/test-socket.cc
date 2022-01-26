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

#include <ctime>
#include <cstring>

#include "gtest/gtest.h"

#include "OsSocket.hh"
#include "OsMisc.hh"
#include "OsDebug.hh"
#include "OsServerSocket.hh"
#include "OsThreadManager.hh"

namespace
{
  class TestOcpiOsSocket : public ::testing::Test
  {
    protected:
      std::string d_argv0;
  };

  void test03Thread ( void* opaque )
  {
    try
    {
      uint16_t* portNoPtr = reinterpret_cast<uint16_t*> ( opaque );
      OCPI::OS::Socket cs;
      cs.connect( "localhost", *portNoPtr);
      cs.close();
    }
    catch ( const std::string& s )
    {
      std::cout << "Exception(s) " << s << std::endl;
      FAIL();
    }
    catch ( ... )
    {
      std::cout << "Exception(u) unknown" << std::endl;
      FAIL();
    }

  }

  void test04Thread ( void* opaque )
  {
    uint16_t* portNoPtr = reinterpret_cast<uint16_t*> ( opaque );
    OCPI::OS::Socket cs;
    cs.connect ( "localhost", *portNoPtr );
    cs.send ( "Hello World!", 13 );
    cs.close ( );
  }

  void test05Thread ( void* opaque )
  {
    uint16_t* portNoPtr = reinterpret_cast<uint16_t*> ( opaque );

    OCPI::OS::Socket cs;
    cs.connect ( "localhost", *portNoPtr );
    char buffer [ 1024] ;
    char* ptr = buffer;
    size_t count, total = 0;

    do
    {
      count = cs.recv ( ptr, 1024 - total );
      ptr += count;
      total += count;
    }
    while ( count > 0 );

    ptr = buffer;

    do
    {
      count = cs.send ( ptr, total );
      ptr += count;
      total -= count;
    }
    while ( count > 0 && total > 0 );

    cs.close ( );
  }


  struct Test06Data
  {
    OCPI::OS::ServerSocket* sock;
    int timeWaited;
    bool gotException;
  };

  void test06Thread ( void* opaque )
  {
    Test06Data* td = reinterpret_cast<Test06Data*> ( opaque );

    std::time_t beginning = std::time ( 0 );

    try
    {
      td->sock->wait ( 10000 );
    }
    catch ( ... )
    {
      td->gotException = true;
    }

    std::time_t end = std::time ( 0 );
    td->timeWaited = ( int ) ( end - beginning );
  }

  void test07Thread ( void* opaque )
  {
    std::string myAddress = "127.0.0.1";

    const char* ap = myAddress.c_str ( );

    while ( *ap )
    {
      if (*ap != '.' &&
          *ap != '0' && *ap != '1' && *ap != '2' && *ap != '3' &&
          *ap != '4' && *ap != '5' && *ap != '6' && *ap != '7' &&
          *ap != '8' && *ap != '9')
      {
        break;
      }
      ap++;
    }

    uint16_t* portNoPtr = reinterpret_cast<uint16_t*> ( opaque );

    OCPI::OS::Socket cs;
    cs.connect ( myAddress, *portNoPtr );

    if ( !*ap )
    {
      cs.send ( "Hello World!", 13 );
    }
    else
    {
      // oops, the address was not in dotted IP notation
      cs.send ( "WrongAddress", 13 );
    }

    cs.close ( );
  }

  // Test 1: Binding ServerSocket to random port
  TEST( TestOcpiOsSocket, test_1 )
  {
    OCPI::OS::ServerSocket so ( 0 );
    uint16_t portNo = so.getPortNo ( );
    so.close ( );
    EXPECT_GT( portNo, 0u );
    EXPECT_LT( portNo, 65536u );
  }


  // Test 2: Binding ServerSocket to specific port
  TEST( TestOcpiOsSocket, test_2 )
  {
    OCPI::OS::ServerSocket so ( 6274, true );
    uint16_t portNo = so.getPortNo ( );
    so.close ( );
    EXPECT_EQ( portNo, 6274u );
  }


  // Test 3: Accepting connection
  TEST( TestOcpiOsSocket, test_3 )
  {
    try
    {
      uint16_t portNo = 6275;
      OCPI::OS::ServerSocket se ( portNo, true );
      OCPI::OS::ThreadManager tm ( test03Thread, &portNo );
      OCPI::OS::Socket so;
      se.accept (so);
      so.close ( );
      se.close ( );
      tm.join ( );
      EXPECT_EQ( true, true );
    }
    catch ( const std::string& s )
    {
      std::cout << "Exception(s) " << s << std::endl;
      FAIL();
    }
    catch ( ... )
    {
      std::cout << "Exception(u) unknown" << std::endl;
      FAIL();
    }
  }


  // Test 4: Receiving data
  TEST( TestOcpiOsSocket, test_4 )
  {
    try
    {
      uint16_t portNo = 6276;
      OCPI::OS::ServerSocket se ( portNo, true );
      OCPI::OS::ThreadManager tm ( test04Thread, &portNo );
      OCPI::OS::Socket so;
      se.accept(so);
      char buf [ 16 ];
      size_t count = so.recv ( buf, 16 );
      EXPECT_EQ( count, 13u );
      EXPECT_EQ(std::strcmp ( buf, "Hello World!" ), 0 );
      so.close ( );
      se.close ( );
      tm.join ( );
    }
    catch ( const std::string& s )
    {
      std::cout << "Exception(s) " << s << std::endl;
      FAIL();
    }
    catch ( ... )
    {
      std::cout << "Exception(u) unknown" << std::endl;
      FAIL();
    }
  }


  // Test 5: Shutting down one side of a connection
  TEST( TestOcpiOsSocket, test_5 )
  {
    try
    {
      uint16_t portNo = 6277;
      OCPI::OS::ServerSocket se ( portNo, true );
      OCPI::OS::ThreadManager tm ( test05Thread, &portNo );
      OCPI::OS::Socket so;
      se.accept(so);

      const char * ptr = "Hello World!";
      unsigned long long count;

      while ( *ptr )
      {
        count = so.send ( ptr, 1 );
        EXPECT_EQ( count, 1u );
        ptr++;
      }

      so.shutdown ( );

      char buf [ 16 ];

      char *ptr2 = buf;

      do
      {
        count = so.recv ( ptr2, 2 );
        ptr2 += count;
      }
      while ( count > 0 );

      *ptr2 = 0;

      EXPECT_EQ( std::strcmp ( buf, "Hello World!" ), 0 );
      so.close ( );
      se.close ( );
      tm.join ( );
    }
    catch ( const std::string& s )
    {
      std::cout << "Exception(s) " << s << std::endl;
      FAIL();
    }
    catch ( ... )
    {
      std::cout << "Exception(u) unknown" << std::endl;
      FAIL();
    }
  }


  // Test 6: Wake up a thread that is blocked in accept
  TEST( TestOcpiOsSocket, test_6 )
  {
    OCPI::OS::ServerSocket se ( 0 );
    Test06Data td;
    td.sock = &se;
    td.timeWaited = -1;
    td.gotException = false;
    OCPI::OS::ThreadManager tm ( test06Thread, &td );
    OCPI::OS::sleep ( 500 );
    se.close ( );
    tm.join ( );
    EXPECT_NE( td.timeWaited, -1 );
    EXPECT_LT( td.timeWaited, 9 ); // 10 seconds is self-destruct... was 5 but too slow on Jenkins testing
    EXPECT_EQ( td.gotException, true );
  }


  // Test 7: Use dotted decimal IP address
  TEST( TestOcpiOsSocket, test_7 )
  {
    uint16_t portNo = 6276;
    OCPI::OS::ServerSocket se ( portNo, true) ;
    OCPI::OS::ThreadManager tm ( test07Thread, &portNo );
    OCPI::OS::Socket so;
    se.accept(so);
    char buf [ 16 ];
    size_t count = so.recv ( buf, 16 );
    EXPECT_EQ( count, 13u );
    EXPECT_EQ( std::strcmp ( buf, "Hello World!" ), 0 );
    so.close ( );
    se.close ( );
    tm.join ( );
  }

} // End: namespace<unnamed>
