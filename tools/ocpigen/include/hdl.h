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

#ifndef HDL_H
#define HDL_H
#include "wip.h"
#include "clock.h"
class HdlDevice;
typedef HdlDevice DeviceType;
typedef std::list<DeviceType *>     DeviceTypes;
typedef DeviceTypes::const_iterator DeviceTypesIter;
struct Device;
typedef std::list<Device *>     Devices;
typedef Devices::const_iterator DevicesIter;

struct ExtTuple {
  Signal *signal;
  size_t index;
  std::string ext;
  bool single; // mapping is for a single signal in a vector
ExtTuple(Signal *arg_signal, size_t arg_index, const std::string &arg_ext, bool arg_single)
: signal(arg_signal), index(arg_index), ext(arg_ext), single(arg_single) {
  }
};
typedef std::list<ExtTuple> ExtMap_;
class ExtMap : public ExtMap_ {
 public:
  Signal *findSignal(const std::string &s, size_t &n) {
    for (ExtMap_::const_iterator i = begin(); i != end(); i++)
      if (!strcasecmp((*i).ext.c_str(), s.c_str())) {
	n = (*i).index;
	return (*i).signal;
      }
    return NULL;
  }
  const char *findSignal(Signal &s, size_t n, bool &isSingle) const {
    for (ExtMap_::const_iterator i = begin(); i != end(); i++)
      if ((*i).signal == &s && (*i).index == n) {
	isSingle = (*i).single;
	return (*i).ext.c_str();
      }
    return NULL;
  }
  void push_back(Signal *s, size_t n, const std::string &e, bool single) {
    ExtMap_::push_back(ExtTuple(s, n, e, single));
  }
};

#define myComment() hdlComment(m_language)
static inline const char *hdlComment(Language lang) { return lang == VHDL ? "--" : "//"; }
extern const char *endians[];

// These are for all implementaitons whether assembly or written
#define HDL_TOP_ATTRS "Pattern", "PortPattern", "DataWidth", "library", "ExactParts"
// These are for implementaitons that you write (e.g. not generated assemblies), not devices
#define HDL_WORKER_ATTRS  IMPL_ATTRS, HDL_TOP_ATTRS, "outer", "endian", "Pattern", "PortPattern", \
                          "DataWidth", "library"
#define HDL_WORKER_ELEMS IMPL_ELEMS, "timeinterface", "memoryinterface", "streaminterface", "clock", \
    "messageinterface"

// All types of assemblies currently do not introduce any special elements
// so there is no "extra" elements for any of them, only top attrs, and instance attrs

// XML for HDL assemblies, that are not configurations or containers
#define HDL_ASSEMBLY_EXTRA_TOP_ATTRS HDL_TOP_ATTRS, "language", "containers", "defaultcontainers",
#define HDL_ASSEMBLY_EXTRA_INST_ATTRS "paramconfig",

// XML for HDL platform configuration assemblies (not the config xml files)
#define HDL_CONFIG_ASSEMBLY_EXTRA_TOP_ATTRS HDL_ASSEMBLY_EXTRA_TOP_ATTRS
#define HDL_CONFIG_ASSEMBLY_EXTRA_INST_ATTRS HDL_ASSEMBLY_EXTRA_INST_ATTRS "device",

// XML for HDL platform configuration assemblies (not the config xml files)
#define HDL_CONTAINER_ASSEMBLY_EXTRA_TOP_ATTRS HDL_CONFIG_ASSEMBLY_EXTRA_TOP_ATTRS
#define HDL_CONTAINER_ASSEMBLY_EXTRA_INST_ATTRS HDL_CONFIG_ASSEMBLY_EXTRA_INST_ATTRS "adapter", "interconnect", "configure",

class HdlAssembly : public Worker {
public:
  static HdlAssembly *
    create(ezxml_t xml, const char *xfile, const std::string &parentFile, Worker *parent,
	   const char *&err);
  HdlAssembly(ezxml_t xml, const char *xfile, const std::string &parentFile, Worker *parent,
	      const char *&err);
  virtual ~HdlAssembly();
};



// Global to let worker know whether an assembly is being built or just a worker
//extern bool hdlAssy;

#endif
