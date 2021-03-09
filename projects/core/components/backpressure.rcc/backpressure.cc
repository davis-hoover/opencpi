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
 *
 * This worker exists only to satisfy the applications generated for unit tests
 * It passes through the data it receives without change
 * It should not be used in any user applications, as it does nothing.
 *
 */

#include "backpressure-worker.hh"

using namespace OCPI::RCC; // for easy access to RCC data types and constants
using namespace BackpressureWorkerTypes;

class BackpressureWorker : public BackpressureWorkerBase {
    size_t myBufferIndex;
    size_t myBufferSize;
    bool lastBufferComplete;

    RCCResult start ()
    {
        myBufferIndex = 0;
        myBufferSize = 0;
        lastBufferComplete = true;
        return RCC_OK;
    }

    RCCResult stop ()
    {
        return RCC_OK;
    }

    RCCResult run(bool /*timedout*/) {
        out.setOpCode(in.opCode());        // Set the metadata for the output message
        // Allow ZLMs to pass through unmolested.
        if (in.length() < 1) {
            out.setLength(0);
            return RCC_ADVANCE;
        }

        //treating the buffers as arrays of unsigned bytes
        const uint8_t  *inData  = static_cast<const uint8_t*>(in.data());
        uint8_t *outData =  static_cast<uint8_t*>(out.data());

        out.checkLength(in.length());
        memcpy(outData, inData, in.length());
        out.setLength( in.length() );
        return RCC_ADVANCE;
    }
};

BACKPRESSURE_START_INFO
BACKPRESSURE_END_INFO
