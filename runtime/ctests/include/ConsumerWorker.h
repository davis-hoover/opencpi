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

#ifndef CONSUMER_WORKER_H
#define CONSUMER_WORKER_H


#include "RCC_Worker.hh"

#ifndef WIN32
//#define TIME_TP
#ifdef TIME_TP
#include <time_utils.h>
#endif
#endif

#ifdef RAND_MAX
#undef RAND_MAX
#endif

#define RAND_MAX 31

struct  ConsumerWorkerProperties_ {
  uint32_t startIndex;
  uint32_t longProperty;
};
typedef struct ConsumerWorkerProperties_ ConsumerWorkerProperties;


typedef enum  {
        C_Old_Input,
        C_New_Input
} C_MyWorkerState;

struct ConsumerWorkerStaticMemory_ {
        uint32_t     startIndex;
    C_MyWorkerState state;
        uint32_t     b_count;
        uint32_t      longProperty;

#ifdef TIME_TP
        Timespec        startTime;
#endif

};

typedef struct ConsumerWorkerStaticMemory_ ConsumerWorkerStaticMemory;


#ifdef __cplusplus
extern "C" {
  extern OCPI::RCC::RCCDispatch ConsumerWorkerDispatchTable;
};
#else
extern RCCDispatch ConsumerWorkerDispatchTable;
#endif






#endif
