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

/*
 * Unit test utilities include file.
 *
 * 06/01/09 - John Miller 
 * Added RPL support.
 *
 * 06/01/09 - John Miller
 * Initial Version
 */
#include <stdio.h>
#include <signal.h>
#include <sstream>
#include <list>
#include "OsMisc.hh"
#include "OsAssert.hh"
#include "TimeEmit.hh"
#include "TransportRDTInterface.hh"
#include "UtilThread.hh"
#include "BasePValue.hh"
#include "Container.h"
#include "ContainerWorker.h"
#include "ContainerPort.h"
#include "RCC_Worker.h"

extern bool g_testUtilVerbose;
// #define TUPRINTF if(g_testUtilVerbose) printf
#define TUPRINTF ocpiDebug

typedef void SignalCb(int);

class SignalHandler {
 public:
  SignalHandler( SignalCb * callback=NULL ) 
    {
      m_cb = callback;
      once = false;
      signal (SIGTERM,my_catcher);
      signal (SIGILL,my_catcher);
      signal (SIGABRT,my_catcher);
      signal (SIGINT,my_catcher);
      signal (SIGHUP,my_catcher);
      signal (SIGQUIT,my_catcher);
      //      signal (SIGTSTP,my_catcher);
    }

  static void my_catcher( int signum )
    {
      if ( once ) return;
      printf("Got a signal, number = %d\n", signum );
      if ( m_cb ) {
        once = true;
        // OCPI::Time::Emit::shutdown(); our shutdown code does this anyway, in a better place
        m_cb(signum);
      }
    }

 private:
  static SignalCb * m_cb;
  static bool once;
};


struct ContainerDesc {
  std::string             ep;
  std::string             type;
  ContainerDesc(const char* pep, const char* ptype )
  :ep(pep),type(ptype){}
};

struct CApp {
  OCPI::API::Container*         container;
  OCPI::Container::Worker*      worker;
  OCPI::API::ContainerApplication *      app;
};

struct CWorker {
  size_t                          cid;
  OCPI::Container::Worker *       worker;
  struct ConData {
    CWorker*     worker;
    int          pid;
    ConData() : worker(NULL), pid(0) {}
  };
  struct Pdata {
    OCPI::Base::PValue            *props;
    bool                          input;
    size_t                        bufferCount;
    OCPI::Container::Port *       port;
    ConData                       down_stream_connection;
    Pdata():props(NULL),bufferCount(2),port(NULL) {}
  };
  unsigned sPortCount;
  unsigned tPortCount;
  Pdata                  pdata[32];
CWorker(unsigned tports, unsigned sports):sPortCount(sports), tPortCount(tports){};
  size_t operator=(size_t i)
  {
    worker=0; cid=i; return i;
#if 0
    for ( int n=0; n<32; n++ ) {
      pdata[n].down_stream_connection.worker = NULL;
    }
#endif
  }
};

#define PORT_0 0
#define PORT_1 1
#define PORT_2 2
#define PORT_3 3
#define PORT_4 4
#define PORT_5 5

#define CATCH_ALL_RETHROW( msg )                                        \
  catch ( int& ii ) {                                                        \
    TUPRINTF("gpp: Caught an int exception while %s = %d\n", msg,ii );        \
    throw;                                                                \
  }                                                                        \
  catch ( OCPI::Util::EmbeddedException& eex ) {                                \
    TUPRINTF(" gpp: Caught an embedded exception while %s:\n", msg);        \
    TUPRINTF( " error number = %d", eex.m_errorCode );                        \
    TUPRINTF( " aux info = %s\n", eex.m_auxInfo.c_str() );                \
    throw;                                                                \
  }                                                                        \
  catch( std::string& stri ) {                                                \
    TUPRINTF("gpp: Caught a string exception while %s = %s\n", msg, stri.c_str() ); \
    throw;                                                                \
  }                                                                        \
  catch( ... ) {                                                        \
    TUPRINTF("gpp: Caught an unknown exception while %s\n",msg );        \
    throw;                                                                \
  }

#if 0

#define CHECK_WCI_CONROL_ERROR(err, op, ca, w)                                \
  if ( err != WCI_SUCCESS ) {                                                \
    std::string err_str = w.worker->getLastControlError(); \
    TUPRINTF("ERROR: WCI control(%d) returned %d, error string = %s\n", op, err, err_str.c_str() ); \
    throw std::string("WCI control error");                                \
  }



#define CHECK_WCI_WRITE_ERROR(err, ca, w )                                \
  if ( err != WCI_SUCCESS ) {                                                \
    std::string err_str = w.worker->getLastControlError(); \
    TUPRINTF("ERROR: WCI write returned %d, error string = %s\n", err, err_str.c_str() ); \
    throw std::string("WCI Write error");                                \
  }
#endif


#define TRY_AND_SET(var, str, exp, code)		 \
  do {							 \
    str = "";                                            \
    var = OU::NO_ERROR_;				 \
    try {						 \
      code;						 \
    }  catch (OCPI::Util::EmbeddedException &ee_) {	 \
      var = ee_.getErrorCode(); str = ee_.m_auxInfo;	 \
    } catch (std::string& err) { \
      var = OU::LAST_ERROR_ID;	 \
      str = err; \
    }  catch (...) {					 \
      var = OU::LAST_ERROR_ID;				 \
    }							 \
    TUPRINTF("Expected error string (%s) got %u (%s)\n", \
	     exp, var, str.c_str() );			 \
  } while (0)

namespace OCPI {
  namespace CONTAINER_TEST {
    void  dumpPortData( OCPI::Container::PortData * pd );
    void testDispatch(OCPI::API::Container* rcc_container);
    void initWorkers(std::vector<CApp>& ca, std::vector<CWorker*>& workers );
    void enableWorkers( std::vector<CApp>& ca, std::vector<CWorker*>& workers );
    void disableWorkers( std::vector<CApp>& ca, std::vector<CWorker*>& workers );
    void disconnectPorts( std::vector<CApp>& ca, std::vector<CWorker*>& workers );
    void destroyWorkers( std::vector<CApp>& ca, std::vector<CWorker*>& workers );
    void destroyContainers( std::vector<CApp>& ca, std::vector<CWorker*>& workers );
    void createPorts( std::vector<CApp>& ca, std::vector<CWorker*>& workers );
    void connectWorkers(std::vector<CApp>& ca, std::vector<CWorker*>& workers );
    std::vector<CApp> createContainers( std::vector<const char*>& eps, 
                                        OCPI::Xfer::EventManager*& event_manager, bool use_polling );

    std::vector<CApp> createContainers( std::vector<ContainerDesc>& eps, 
                                        OCPI::Xfer::EventManager*& event_manager, bool use_polling );

    struct DThreadData {
      bool run;
      std::vector<CApp> containers;
      OCPI::Xfer::EventManager* event_manager;
    };
    OCPI::Util::Thread* runTestDispatch( DThreadData& tdata );

    OCPI::Container::Worker *createWorker(CApp &capp, OCPI::RCC::RCCDispatch *rccd);
    OCPI::Container::Worker *createWorker(OCPI::API::ContainerApplication *app,
					  OCPI::RCC::RCCDispatch *rccd);
  }

}




