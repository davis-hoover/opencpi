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
 * THIS FILE WAS ORIGINALLY GENERATED ON Wed Aug 24 11:47:41 2011 EDT
 * BASED ON THE FILE: vsadd.xml
 * YOU ARE EXPECTED TO EDIT IT
 *
 * This file contains the OCL implementation skeleton for worker: vsadd
 */

#include "vsadd-worker.h"

/*
 * Required work group size for worker vsadd run() function.
#define OCL_WG_X 64
#define OCL_WG_Y 1
#define OCL_WG_Z 1
 */

/*
 * Methods to implement for worker vsadd, based on metadata.
 */

static OCLResult
vsadd_run(VsaddWorker* self, __global VsaddProperties *properties) {
  const size_t n_elems = self->ports.in.current.length / sizeof(float);
  __global const float* src = (__global float *)self->ports.in.current.data;
  __global float* dst = (__global float *)self->ports.out.current.data;
  size_t gid = get_global_id(0);

  if (gid >= n_elems)
    return OCL_DONE;
  dst[gid] = src[gid] + properties->scalar;
  self->ports.out.current.length = self->ports.in.current.length;
  self->ports.out.current.opCode = self->ports.in.current.opCode;
  return OCL_ADVANCE;
}

