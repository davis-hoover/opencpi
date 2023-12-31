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

#ifndef HDL_WCI_CONTROL_H
#define HDL_WCI_CONTROL_H

#include "ContainerWorker.hh"
#include "HdlOCCP.hh"
#include "XferAccess.hh"

namespace OCPI {
  namespace HDL {

    // The class that knows about WCI interfaces and the OCCP.
    class Device;
    typedef OCPI::Xfer::Access Access;
    typedef OCPI::Xfer::Accessor Accessor;
    typedef OCPI::Xfer::RegisterOffset RegisterOffset;
    class WciControl : public Access, virtual public OCPI::Container::Controllable,
      virtual public OCPI::API::PropertyAccess, virtual OCPI::Container::WorkerControl {
      friend class Port;
      friend class Device;
      friend class Container;
      friend class Artifact;
      const char *m_implName, *m_instName;
      mutable size_t m_window; // perfect use-case for mutable..
      bool m_hasControl;
      size_t m_timeout;
      //      std::string m_wName;
    protected:
      Access m_properties;              // The accessor to the remote property space
      Device &m_device;
      size_t m_occpIndex;
      OCPI::Metadata::Property *m_propInfo; // the array of property descriptors
      WciControl(Device &device, const char *impl, const char *inst, unsigned index, bool hasControl);
    public:
      WciControl(Device &device, ezxml_t implXml, ezxml_t instXml, OCPI::Metadata::Property *props,
		 bool doInit = true);
      virtual ~WciControl();
      inline size_t index() const { return m_occpIndex; }
    protected:
      // This is shadowed by real application workers, but is used when this is
      // standalone.
      //      const std::string &name() const { return m_wName; }
      void init(bool redo, bool doInit);
      bool isReset() const;
      void propertyWritten(unsigned ordinal) const;
      void propertyRead(unsigned ordinal) const;
      // Add the hardware considerations to the property object that supports
      // fast memory-mapped property access directly to users
      // the key members are "readVaddr" and "writeVaddr"
      virtual void prepareProperty(OCPI::Metadata::Property &md,
				   volatile uint8_t *&writeVaddr,
				   const volatile uint8_t *&readVaddr) const;
      // Map the control op numbers to structure members
      static const unsigned controlOffsets[];
      void checkControlState() const;
      void controlOperation(OCPI::Metadata::Worker::ControlOperation op);
      bool controlOperation(OCPI::Metadata::Worker::ControlOperation op, std::string &err);
      inline uint32_t checkWindow(size_t offset, size_t nBytes) const {
	ocpiAssert(m_hasControl);
	unsigned windowBits = OCCP_WORKER_CONFIG_WINDOW_BITS - OCCP_WORKER_CONFIG_READSIZE_BITS;
	size_t window = offset & (~0u << windowBits);
	ocpiAssert(window == ((offset + nBytes) & (~0u << windowBits)));
	if (window != m_window) {
	  set32Register(window, OccpWorkerRegisters, (uint32_t)(window >> windowBits));
	  m_window = window;
	}
	unsigned arsize = nBytes == 1 ? 0 : nBytes == 2 ? 1 : 2; // log2(nbytes)
	return (uint32_t)((offset & ~(~0u << windowBits)) | (arsize << windowBits));
      }
      void throwPropertyReadError(uint32_t status, size_t offset, size_t n, uint64_t val) const;
      void throwPropertyWriteError(uint32_t status) const;
      void throwPropertySequenceError() const;

#define PUT_GET_PROPERTY(n,wb)                                                    \
      void                                                                        \
      setProperty##n(const OCPI::API::PropertyInfo &info, size_t offset, uint##n##_t val, \
		     unsigned idx) const;				          \
      inline uint##n##_t						          \
      getProperty##n(const OCPI::API::PropertyInfo &info, size_t off, unsigned idx) const { \
        return getPropertyOffset##n(info.m_offset, info.m_readError, off, idx);   \
      }                                                                           \
      inline uint##n##_t						          \
      getPropertyOffset##n(size_t a_base, bool readError, size_t off, unsigned idx) const { \
        uint32_t offset = checkWindow(a_base + off + idx * (n/8), n/8); \
	uint32_t status = 0;                                                      \
        uint##wb##_t val##wb;							  \
	uint##n##_t val;						          \
	if (m_properties.registers()) {					          \
	  if (!readError ||					                          \
	      !(status =						          \
		get32Register(status, OccpWorkerRegisters) &		          \
		OCCP_STATUS_READ_ERRORS)) {                                       \
	    val##wb = m_properties.get##n##RegisterOffset(offset);      	  \
	    switch ((uint32_t)val##wb) {                                          \
	    case OCCP_TIMEOUT_RESULT:                                             \
            case OCCP_RESET_RESULT:                                               \
            case OCCP_ERROR_RESULT:                                               \
            case OCCP_FATAL_RESULT:                                               \
            case OCCP_BUSY_RESULT:                                                \
	      /* The returned data value matches our error codes so we read */    \
	      /* the status register to be sure */			          \
	      status = get32Register(status, OccpWorkerRegisters) &	          \
		       OCCP_STATUS_READ_ERRORS;				          \
	      /* falls thru */						          \
	    default:							          \
	      val = (uint##n##_t)val##wb;                                         \
            }								          \
	  } else                                                                  \
            val = 0;                                                              \
	  if (!status && readError)				          \
	    status =							          \
	      get32Register(status, OccpWorkerRegisters) &		          \
	      OCCP_STATUS_READ_ERRORS;					          \
	} else								          \
	  val = (uint##n##_t)						\
	    (n == 64 ?							\
	     m_properties.accessor()->get64(m_properties.base() + offset, &status) : \
	     m_properties.accessor()->get(m_properties.base() + offset,	sizeof(uint##n##_t), \
					  &status));	\
	if (status)							          \
	  throwPropertyReadError(status, offset, n/8, val);			\
	return val;							          \
      }
      PUT_GET_PROPERTY(8,32)
      PUT_GET_PROPERTY(16,32)
      PUT_GET_PROPERTY(32,32)
      PUT_GET_PROPERTY(64,64)
#undef PUT_GET_PROPERTY

// Convenience macros to directly access scalar properties, with windowing
#define getProperty8Register(m, type) getPropertyOffset8(offsetof(type,m), false, 0, 0)
#define getProperty16Register(m, type) getPropertyOffset16(offsetof(type,m), false, 0, 0)
#define getProperty32Register(m, type) getPropertyOffset32(offsetof(type,m), false, 0, 0)
#define getProperty64Register(m, type) getPropertyOffset64(offsetof(type,m), false, 0, 0)

      void setPropertyBytes(const OCPI::API::PropertyInfo &info, size_t offset,
			    const uint8_t *data, size_t nBytes, unsigned idx) const;

      void getPropertyBytes(const OCPI::API::PropertyInfo &info, size_t offset, uint8_t *buf,
			    size_t nBytes, unsigned idx, bool string) const;
      void setPropertySequence(const OCPI::API::PropertyInfo &p,
			       const uint8_t *val,
			       size_t nItems, size_t nBytes) const;
      unsigned getPropertySequence(const OCPI::API::PropertyInfo &p, uint8_t *buf, size_t n) const;

#undef OCPI_DATA_TYPE_S
      // Set a scalar property value

#define OCPI_DATA_TYPE(sca,corba,letter,bits,run,pretty,store)		\
      void								\
      set##pretty##Property(const OCPI::API::PropertyInfo &info, const OCPI::Base::Member &, \
			    size_t off, const run val, unsigned idx) const { \
	setProperty##bits(info, off, *(uint##bits##_t *)&val, idx);	\
      }									\
      void								\
      set##pretty##SequenceProperty(const OCPI::API::PropertyInfo &info,       \
				    const run *vals,			\
				    size_t length) const {		\
	setPropertySequence(info, (const uint8_t *)vals,			\
			    length, length * (bits/8));			\
      }									\
      run								\
      get##pretty##Property(const OCPI::API::PropertyInfo &info, const OCPI::Base::Member &, \
			    size_t offset, unsigned idx) const {	\
	return (run)getProperty##bits(info, offset, idx);		\
      }									\
      unsigned								\
      get##pretty##SequenceProperty(const OCPI::API::PropertyInfo &info, run *vals, \
				    size_t length) const {		\
	return								     \
	  getPropertySequence(info, (uint8_t *)vals, length * (bits/8));	     \
      }
#define OCPI_DATA_TYPE_S(sca,corba,letter,bits,run,pretty,store)
OCPI_DATA_TYPES
#undef OCPI_DATA_TYPE
      void setStringProperty(const OCPI::API::PropertyInfo &info, const OCPI::Base::Member &,
			     size_t offset, const char* val, unsigned idx) const;
      void setStringSequenceProperty(const OCPI::API::PropertyInfo &, const char * const *,
				     size_t ) const;
      void getStringProperty(const OCPI::API::PropertyInfo &info, const OCPI::Base::Member &,
			     size_t offset, char *val, size_t length, unsigned idx) const;
      unsigned getStringSequenceProperty(const OCPI::API::PropertyInfo &, char * *,
					 size_t ,char*, size_t) const;
    };
    // This is a dummy worker for accesssing workers outside the purview of executing
    // applications.  It is used by ocpihdl when it wants to talk to HDL workers based on
    // the artifact XML embedded in the bitstream, which is the result of the whole bitstream
    // build process, not user-authored.  Many of the methods don't do anything.
    struct DirectWorker : public OCPI::Container::Worker, public WciControl {
      std::string m_name, m_wName;
      Access &m_wAccess;
      unsigned m_timeout;
      DirectWorker(Device &dev, const Access &cAccess, Access &wAccess, ezxml_t impl,
		   ezxml_t inst, const char *idx, unsigned timeout);
      virtual void control(const char *op); // virtual due to driver access, custom in this class
      virtual void status();                // virtual due to driver access, custom in this class
      OCPI::Container::Port *findPort(const char *);
      const std::string &name() const;
      void
      prepareProperty(OCPI::Metadata::Property &, volatile uint8_t *&, const volatile uint8_t *&) 
	const;
      OCPI::Container::Port &
      createPort(const OCPI::Metadata::Port &, const OCPI::Base::PValue *);
      OCPI::Container::Port &
      createOutputPort(OCPI::Metadata::PortOrdinal, size_t, size_t, const OCPI::Base::PValue*);
      OCPI::Container::Port &
      createInputPort(OCPI::Metadata::PortOrdinal, size_t, size_t, const OCPI::Base::PValue*);
      OCPI::Container::Application *application();
      OCPI::Container::Worker *nextWorker();
      void read(size_t, size_t, void *);
      void write(size_t, size_t, const void *);
    };
  }
}
#endif
