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
 * THIS FILE WAS ORIGINALLY GENERATED ON Thu Jul 29 08:03:24 2010 EDT
 * BASED ON THE FILE: copy.xml
 * YOU ARE EXPECTED TO EDIT IT
 *
 * This file contains the RCC implementation skeleton for worker: copy
 */
#include <string.h>
#include "copy_Worker.h"

COPY_METHOD_DECLARATIONS;
RCCDispatch copy = {
  /* insert any custom initializations here */
  COPY_DISPATCH
};

/*
 * Methods to implement for worker copy, based on metadata.
*/

static RCCResult run(RCCWorker *self,
                     RCCBoolean timedOut,
                     RCCBoolean *newRunCondition) {
  ( void ) timedOut;
  ( void ) newRunCondition;
  RCCPort
    *in = &self->ports[COPY_IN],
    *out = &self->ports[COPY_OUT];
#if 0
  self->container.send(out, in->current, in->input.u.operation, in->input.length);
  return RCC_OK;
#else
  memcpy(self->ports[COPY_OUT].current.data, in->current.data, in->input.length);
  out->output.u.operation = in->input.u.operation;
  out->output.length = in->input.length;
  return RCC_ADVANCE;
#endif
}
