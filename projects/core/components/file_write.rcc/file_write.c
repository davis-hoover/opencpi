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
 * THIS FILE WAS ORIGINALLY GENERATED ON Wed Dec 21 15:54:06 2011 EST
 * BASED ON THE FILE: file_read.xml
 * YOU ARE EXPECTED TO EDIT IT
 *
 * This file contains the RCC implementation skeleton for worker: file_read
 */
#define _GNU_SOURCE // for asprintf
#include <fcntl.h>
#include <stdio.h>
#include <errno.h>
#include <string.h>
#include <unistd.h>
#include "file_write_Worker.h"

typedef struct {
  int fd;
  int started;
  RCCTime startTime;
  uint64_t sum;
  uint32_t count;
} MyState;

FILE_WRITE_METHOD_DECLARATIONS;
RCCDispatch file_write = {
 /* insert any custom initializations here */
 FILE_WRITE_DISPATCH
 .memSize = sizeof(MyState)
};

/*
 * Methods to implement for worker file_read, based on metadata.
 */

static RCCResult
start(RCCWorker *self) {
  MyState *s = self->memory;
  File_writeProperties *p = self->properties;

  if (s->started)
    return self->container.setError("file_write cannot be restarted");
  if ((s->fd = creat(p->fileName, 0666)) < 0)
    return self->container.setError("error creating file \"%s\": %s",
				    p->fileName, strerror(errno));
  s->started = 1;
  return RCC_OK;
} 

static RCCResult
release(RCCWorker *self) {
  MyState *s = self->memory;
  if (s->started)
    close(s->fd);
 return RCC_OK;
}

static RCCResult
run(RCCWorker *self, RCCBoolean timedOut, RCCBoolean *newRunCondition) {
 RCCPort *port = &self->ports[FILE_WRITE_IN];
 File_writeProperties *props = self->properties;
 MyState *s = self->memory;
 ssize_t rv;

 // printf("In file_write.c got %zu/%u data = %x\n", port->input.length, port->input.u.operation,
 //	*(uint32_t *)port->current.data);

 (void)timedOut;(void)newRunCondition;
 if (self->firstRun)
   s->startTime = self->container.getTime();
 if (port->input.eof) { // length == 0 && port->input.u.operation == 0 && props->stopOnEOF)
   uint64_t nanos = self->container.nanoTime(self->container.getTime() - s->startTime);
   props->bytesPerSecond = (props->bytesWritten * 1000000000llu) / (nanos ? nanos : 1);
   return RCC_ADVANCE_DONE;
 }
 if (props->messagesInFile) {
   struct {
     uint32_t length;
     uint32_t opcode;
   } m = { port->input.length, port->input.u.operation };
   if ((rv = write(s->fd, &m, sizeof(m)) != (ssize_t)sizeof(m)))
     return self->container.setError("error writing header to file: %s (%zd)", strerror(errno), rv);
 }
 if (port->input.length) {
   if (props->countData) { // touch the data and check it if is correct
     uint32_t *p = (uint32_t *)port->current.data;
     for (unsigned n = port->input.length/sizeof(uint32_t); n; --n) {
       if (s->count++ != *p)
	 return self->container.setError("counting error: is %u, should be %u", *p, --s->count);
       s->sum += *p++;
     }
   }
   if (!props->suppressWrites &&
       (rv = write(s->fd, port->current.data, port->input.length)) != (ssize_t)port->input.length)
     return self->container.setError("error writing data to file: length %zu(%zx): %s (%zd)",
				     port->input.length, port->input.length, strerror(errno), rv);
}
 props->bytesWritten += port->input.length;
 props->messagesWritten++; // this includes non-EOF ZLMs even though no data was written.
 return RCC_ADVANCE;
}
