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

// This file contains definitions for the OpenCPI ad9361 helper code but is not
// used by the ADI NoOS code

#ifndef _AD9361_PLATFORM
#define _AD9361_PLATFORM
#include <pthread.h>

namespace OCPI {
namespace AD9361 {
  // C++ version using thread-safety
  struct CallBack {
    // Return the thread key for the callbacks
    static pthread_key_t get_opencpi_key();
    virtual void get_byte(uint8_t id_no, uint16_t addr, uint8_t *buf) = 0;
    virtual void set_byte(uint8_t id_no, uint16_t addr, const uint8_t *buf) = 0;
    virtual void set_reset(uint8_t id_no, bool on) = 0;
    const char *worker;
  };
}
}

// AD9361_Register_Map_Reference_Manual_UG-671.pdf refers to register bits
// as D7 - D0
#define BITMASK_D7 0x80
#define BITMASK_D6 0x40
#define BITMASK_D5 0x20
#define BITMASK_D4 0x10
#define BITMASK_D3 0x08
#define BITMASK_D2 0x04
#define BITMASK_D1 0x02
#define BITMASK_D0 0x01

struct regs_general_rfpll_divider_t {
  uint8_t general_rfpll_dividers;
};

struct regs_clock_bbpll_t {
  uint8_t clock_bbpll;
};

#define DEFINE_AD9361_SETTING(AD9361_setting_value, AD9361_setting_type) \
typedef AD9361_setting_type AD9361_setting_value##_t; \
AD9361_setting_value##_t AD9361_setting_value; \

// structure used by NoOS platform code to "call back into OpenCPI from below", with no dependencies,
// this is initialized by the opencpi code
typedef struct {
  void (*get_byte)(uint8_t id_no, uint16_t addr, uint8_t *buf);
  void (*set_byte)(uint8_t id_no, uint16_t addr, const uint8_t *buf);
  void (*set_reset)(uint8_t id_no, bool on);
  const char *worker;
}  Ad9361Opencpi;

extern Ad9361Opencpi ad9361_opencpi;
#define THIS_OPENCPI_WORKER_STRING ad9361_opencpi.worker;

// GPIO_RESET_PIN is an arbitrary chosen (yet unique among *_PIN macros) value
#define GPIO_RESET_PIN        0

#endif // _AD9361_COMMON
