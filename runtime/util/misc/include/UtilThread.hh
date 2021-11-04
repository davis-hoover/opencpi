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

/**
 * \file
 * \brief Thread class for asynchronous tasks.
 *
 *   Revision history.
 *
 *   06/24/09 - John Miller
 *   Removed detach() call in destructor if join() was already called.
 *   
 *   01/01/05 - Initial Version
 */

#ifndef OCPI_THREAD_H_
#define OCPI_THREAD_H_

#include <stdlib.h>
#include <stdio.h>
#include "OsThreadManager.hh"

namespace OCPI {
  namespace Util {

    /**
     * \brief Thread class for asynchronous tasks.
     */
    class Thread {

    public:
    Thread() 
      :m_joined(true) 
        {
          m_pobjThreadServices = new OCPI::OS::ThreadManager;
        }
      virtual ~Thread()
        { 
          if ( ! m_joined ) {
            m_pobjThreadServices->detach(); 
          }
          delete m_pobjThreadServices; 
        }

      // User implementation method
      virtual void run()=0;

      // Thread control
      void start();
      void join();

    private:
      OCPI::OS::ThreadManager         *m_pobjThreadServices;
      bool m_joined;
    };
  }
}

#endif 
