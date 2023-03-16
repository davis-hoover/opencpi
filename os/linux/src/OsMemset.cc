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

#include <inttypes.h>
#include <stdlib.h>
#include <stdio.h>
#include "ocpi-config.h"


#if defined(OCPI_ARCH_aarch64)
/* There is an invalid assumption made by arm64 on certain systems that results in an alignment
 * fault when memset's "DC ZVA" instruction is used on uncached memory.
 *
 * So, we override memset for arm64 instead of using the assembly routine that calls that instruction.
 * arm64's DC ZCA causes an alignment fault if used on any type of device memory.... Well it treats
 * uncached memory as device memory here and causes an alignment fault for valid calls to memset on
 * uncached memory. See https://patchwork.kernel.org/patch/6362401/ for more information on this
 * issue and solutions that have been explored. Also see comments on zeromem_dczva here
 * https://github.com/ARM-software/arm-trusted-firmware/blob/master/lib/aarch64/misc_helpers.S
 *
 * OpenCPI creates uncached DMA mappings for the CPU using the O_SYNC flag to the open() calls to the
 * driver (e.g. in DtDmaXfer.cxx).
 */

#ifdef __cplusplus
extern "C" {
#endif

void *memset(void *s, int c, size_t n) {
    // This implementation could be optimized in the following ways:
    // Check if 'n' bytes is aligned on 16, 32, 64 bit boundaries, and use uint* types matching that
    // alignment to reduce the number of iterations in the loop below.
  uint8_t *p = (uint8_t *) s; while (n--) *p++ = (uint8_t)c;
    return s;
}
void *memcpy(void *dst, const void *src, size_t n) {
  uint8_t *d = (uint8_t *)dst, *s = (uint8_t *)src;
  while (n)
    *d++ = *s++, --n;
  return dst;
}

#ifdef __cplusplus
}
#endif

#endif // OCPI_ARCH_arm64
