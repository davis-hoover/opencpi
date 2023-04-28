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
 * Copyright (c) 2023 ICR, Inc.
 *
 * SPDX-License-Identifier: BSD-3-Clause
 */

/*
 * @file	freertos/io.c
 * @brief	Linux libmetal io operations (modified for OpenCPI)
 */

#include <metal/io.h>

unsigned long get_rfdc_ip_segment_base_addr(unsigned long rfdc_ip_reg_addr)
{
  unsigned long ret;
  if (rfdc_ip_reg_addr >= RFDC_IP_ADC3_BASE_ADDR) {
    ret = RFDC_IP_ADC3_BASE_ADDR;
  }
  else if (rfdc_ip_reg_addr >= RFDC_IP_ADC2_BASE_ADDR) {
    ret = RFDC_IP_ADC2_BASE_ADDR;
  }
  else if (rfdc_ip_reg_addr >= RFDC_IP_ADC1_BASE_ADDR) {
    ret = RFDC_IP_ADC1_BASE_ADDR;
  }
  else if (rfdc_ip_reg_addr >= RFDC_IP_ADC0_BASE_ADDR) {
    ret = RFDC_IP_ADC0_BASE_ADDR;
  }
  else if (rfdc_ip_reg_addr >= RFDC_IP_DAC3_BASE_ADDR) {
    ret = RFDC_IP_DAC3_BASE_ADDR;
  }
  else if (rfdc_ip_reg_addr >= RFDC_IP_DAC2_BASE_ADDR) {
    ret = RFDC_IP_DAC2_BASE_ADDR;
  }
  else if (rfdc_ip_reg_addr >= RFDC_IP_DAC1_BASE_ADDR) {
    ret = RFDC_IP_DAC1_BASE_ADDR;
  }
  else if (rfdc_ip_reg_addr >= RFDC_IP_DAC0_BASE_ADDR) {
    ret = RFDC_IP_DAC0_BASE_ADDR;
  }
  else {
    ret = RFDC_IP_CTRL_BASE_ADDR;
  }
  return ret;
}

uint64_t metal_io_access_(struct metal_io_region * io,
    unsigned long offset,
    uint64_t value,
    memory_order order,
    int width,
    int read)
{
  if (io) { // remove compiler error
  }
  if (order == __ATOMIC_RELAXED) { // remove compiler error
  }
  uint64_t ret = 0;
  unsigned long base_addr = get_rfdc_ip_segment_base_addr(offset);
  offset -= base_addr;
  if (width == 1) {
    if (read) {
      ret = (uint64_t)get_uchar_prop(offset, base_addr);
    }
    else {
      set_uchar_prop(offset, base_addr, (uint8_t)(value & 0xff));
    }
  }
  else if (width == 2) {
    if (read) {
      ret = (uint64_t)get_ushort_prop(offset, base_addr);
    }
    else {
      set_ushort_prop(offset, base_addr, (uint16_t)(value & 0xffff));
    }
  }
  else if (width == 4) {
    if (read) {
      ret = (uint64_t)get_ulong_prop(offset, base_addr);
    }
    else {
      uint32_t tmp = (uint32_t)(value & 0xffffffff);
      set_ulong_prop(offset, base_addr, tmp);
    }
  }
  else { // width == 8
    if (read) {
      ret = get_ulonglong_prop(offset, base_addr);
    }
    else {
      set_ulonglong_prop(offset, base_addr, value);
    }
  }
  return ret;
}

uint64_t metal_io_read_(struct metal_io_region *io,
			       unsigned long offset,
			       memory_order order,
			       int width)
{
  return metal_io_access_(io, offset, 0, order, width, 1);
}

void metal_io_write_(struct metal_io_region *io,
			    unsigned long offset,
			    uint64_t value,
			    memory_order order,
			    int width)
{
  metal_io_access_(io, offset, value, order, width, 0);
}

int metal_io_block_read_(struct metal_io_region *io,
				unsigned long offset,
				void *restrict dst,
				memory_order order,
				int len)
{
  uint8_t* pdst = (uint8_t*)dst;
  int idx;
  for (idx=0; idx<len; idx++) {
    *pdst++ = (uint8_t) metal_io_read_(io, offset, order, 1);
  }
  return len;
}

int metal_io_block_write_(struct metal_io_region *io,
				 unsigned long offset,
				 const void *restrict src,
				 memory_order order,
				 int len)
{
  uint8_t* psrc = (uint8_t*)src;
  int idx;
  for (idx=0; idx<len; idx++) {
    metal_io_write_(io, offset, (uint64_t)(*psrc), order, 1);
    psrc++;
  }
  return len;
}

void metal_io_block_set_(struct metal_io_region *io,
				unsigned long offset,
				unsigned char value,
				memory_order order,
				int len)
{
  int idx;
  for (idx=0; idx<len; idx++) {
    metal_io_write_(io, offset, (uint64_t)value, order, 1);
  }
}

static metal_phys_addr_t metal_io_phys_start_ = 0;

// defined here for later use with libmetal/librfdc io registration at librfdc
// initialization time
struct metal_io_region metal_io_region_ = {
	.virt = NULL,
	.physmap = &metal_io_phys_start_,
	.size = (size_t)-1,
	.page_shift = sizeof(metal_phys_addr_t) * CHAR_BIT,
	.page_mask = (metal_phys_addr_t)-1,
	.mem_flags = 0,
	.ops = {
		.read = metal_io_read_,
		.write = metal_io_write_,
		.block_read = metal_io_block_read_,
		.block_write = metal_io_block_write_,
		.block_set = metal_io_block_set_,
		.close = NULL,
		.offset_to_phys = NULL,
		.phys_to_offset = NULL,
	},
};

struct metal_io_ops *metal_io_get_ops(void)
{
	return &metal_io_region_.ops;
}

struct metal_io_region *metal_io_get_region(void)
{
	return &metal_io_region_;
}
