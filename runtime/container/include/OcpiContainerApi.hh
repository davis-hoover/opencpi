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

// The API header for container APIs
// We go to some lengths to make this file NOT reference any other internal non-API files.
#ifndef OCPI_CONTAINER_API_H
#define OCPI_CONTAINER_API_H
#include <stdarg.h>
#include <string>
#include <initializer_list>
#include <cassert>
#include "OcpiPValueApi.hh"
#include "OcpiPropertyApi.hh"
#include "OcpiExceptionApi.hh"
#include "OcpiLibraryApi.hh"

namespace OCPI {
  namespace Container {
    class Port;
    class Worker;
    class LocalLauncher;
    class Application;
  }
  namespace Remote {
    class RemoteLauncher;
  }
  namespace Base {
    class Member;
  }
  namespace RCC {
    class RCCUserSlave;
  }
  namespace API {
    class ExternalPort;
    class ExternalBuffer {
    protected:
      virtual ~ExternalBuffer();
    public:
      virtual void
	release() = 0,
	take() = 0,
	put() = 0,
	put(size_t length, uint8_t opCode = 0, bool endOfData = false, size_t direct = 0) = 0;
    };
    class ExternalPort {
    protected:
      virtual ~ExternalPort();
    public:
      // Return zero if there is no buffer ready
      // data pointer may be null if end-of-data is true.
      // This means NO MESSAGE, not a zero length message.
      // I.e. if "data" is null, length is not valid.
      virtual ExternalBuffer *
        getBuffer(uint8_t *&data, size_t &length, uint8_t &opCode, bool &endOfData) = 0;
      // Return zero when no buffers are available.
      virtual ExternalBuffer *getBuffer(uint8_t *&data, size_t &length) = 0;
      inline ExternalBuffer *
      getInputBuffer(uint8_t *&data, size_t &length, uint8_t &opCode, bool &eof) {
        return getBuffer(data, length, opCode, eof);
      }
      // Return zero when no buffers are available.
      inline ExternalBuffer *getOutputBuffer(uint8_t *&data, size_t &length) {
        return getBuffer(data, length);
      }
      // Use this when end of data indication happens AFTER the last message.
      // Use the endOfData argument to put, when it is known at that time
      // Return false when cannot do it due to flow control.
      // i.e. both getBuffer and endOfData can return NULL/false when it can't be done
      virtual bool endOfData() = 0;
      // Return whether there are still buffers to send that can't be flushed now.
      virtual bool tryFlush() = 0;
      // put/send the most recently gotten output buffer
      virtual void put(size_t length, uint8_t opCode, bool end, size_t direct = 0) = 0;
      // put/send a particular buffer, PERHAPS FROM ANOTHER PORT
      virtual void put(OCPI::API::ExternalBuffer &b) = 0;
      // UNSUPPORTED AND SUBJECT TO CHANGE AT THIS TIME
      // Supply info for minimal marshalling/demarshalling of messages of scalars
      // Return OA::OCPI_None if opcode is out of range of known protocol information
      // Note nbytes for string "scalars" is max bytes per string
      virtual OCPI::API::BaseType getOperationInfo(uint8_t opCode, size_t &nbytes) = 0;
    };
    class Property;
    class PropertyInfo;
    class PropertyAccess {
    public:
      virtual ~PropertyAccess();
      virtual void propertyWritten(unsigned ordinal) const = 0;
      virtual void propertyRead(unsigned ordinal) const = 0;
      virtual size_t getSequenceLengthProperty(const PropertyInfo &, const OCPI::Base::Member &m,
					     size_t offset) const = 0;
      // FIXME:  These should be protected, but the proxy code generator uses them too
      // These methods are used by the Property methods below when the
      // fast path using memory-mapped access cannot be used.
#define OCPI_DATA_TYPE(sca,corba,letter,bits,run,pretty,store)		\
      virtual void							\
      set##pretty##Property(const PropertyInfo &, const OCPI::Base::Member &m, size_t offset, \
			    const run, unsigned idx) const = 0;			\
      virtual void							\
      set##pretty##SequenceProperty(const PropertyInfo &, const run *, size_t nElements) const = 0; \

    OCPI_PROPERTY_DATA_TYPES
#undef OCPI_DATA_TYPE
#undef OCPI_DATA_TYPE_S
// The ordinal-based one is for proxies, with no navigation, but indexing
// The prop/member one is for ACI, which has navigation
#define OCPI_DATA_TYPE(sca,corba,letter,bits,run,pretty,store)		\
    virtual run								\
    get##pretty##Property(const PropertyInfo &, const OCPI::Base::Member &, size_t off, \
			  unsigned idx) const = 0;			\
    virtual unsigned							\
    get##pretty##SequenceProperty(const PropertyInfo &, run *, size_t length) const = 0; \

// The ordinal-based one is for proxies, with no navigation, but indexing
// The prop/member one is for ACI, which has navigation
#define OCPI_DATA_TYPE_S(sca,corba,letter,bits,run,pretty,store)	\
    virtual void							\
    get##pretty##Property(const PropertyInfo &, const OCPI::Base::Member &, size_t off, char *, \
			  size_t length, unsigned idx) const = 0;	\
    virtual unsigned							\
    get##pretty##SequenceProperty(const PropertyInfo &, char **, size_t length, char *buf, \
				  size_t space) const = 0; \

    OCPI_PROPERTY_DATA_TYPES
#undef OCPI_DATA_TYPE
#undef OCPI_DATA_TYPE_S
#define OCPI_DATA_TYPE_S OCPI_DATA_TYPE
    };
    class Worker : virtual public PropertyAccess {
      friend class Property;
      friend class OCPI::RCC::RCCUserSlave;
      virtual PropertyInfo &setupProperty(const char *name,
					  volatile uint8_t *&m_writeVaddr,
					  const volatile uint8_t *&m_readVaddr) const = 0;
      virtual PropertyInfo &setupProperty(unsigned n,
					  volatile uint8_t *&m_writeVaddr,
					  const volatile uint8_t *&m_readVaddr) const = 0;
      virtual bool beforeStart() const = 0;
    protected:
      virtual ~Worker();
    public:
      virtual bool isOperating() const = 0;
      virtual void start() = 0;
      virtual void stop() = 0;
      virtual void release() = 0;
      virtual void beforeQuery() = 0;
      virtual void afterConfigure() = 0;
      virtual void test() = 0;
      // ==========================================================================================
      // Updated access API, consistent with worker, property, slave, string or const char *
      // These all use AccessList to access values that are part of a property
      // ==========================================================================================
      virtual void setProperty(const char* prop_name, const char *value,
			       AccessList &list = emptyList) const = 0;
      void setProperty(const std::string &prop_name, const std::string &value,
		       AccessList &list = emptyList) const {
	setProperty(prop_name.c_str(), value.c_str(), list);
      }
      virtual const char *getProperty(const char *prop_name, std::string &value,
				      AccessList &list = emptyList,
				      PropertyOptionList &options = noPropertyOptions,
				      PropertyAttributes *attributes = NULL) const = 0;
      const char *getProperty(const std::string &name, std::string &value,
			      AccessList &list = emptyList,
			      PropertyOptionList &options = noPropertyOptions,
			      PropertyAttributes *attributes = NULL) const {
	return getProperty(name.c_str(), value, list, options, attributes);
      }
      // Returns NULL when ordinal is invalid
      virtual const char *getProperty(unsigned ordinal, std::string &value,
				      AccessList &list = emptyList,
				      PropertyOptionList &options = noPropertyOptions,
				      PropertyAttributes *attributes = NULL) const = 0;
      // ==========================================================================================
      // End of access list interfaces
      // ==========================================================================================
      // Untyped property list setting - slow but convenient
      virtual void setProperties(const char *props[][2]) =  0;
      // Typed property list setting - slightly safer, still slow
      virtual void setProperties(const PValue *props) =  0;
      virtual bool getProperty(unsigned ordinal, std::string &name, std::string &value,
			       bool *unreadablep = NULL, bool hex = false,
			       bool *cachedp = NULL, bool uncached = false, bool *hiddenp = NULL)
	                      = 0;
    protected:
      virtual void setProperty(const PropertyInfo &prop, const char *v, AccessList &list) const = 0;
      virtual const char *getProperty(const PropertyInfo &prop, std::string &v, AccessList &list,
				      PropertyOptionList &options = noPropertyOptions,
				      PropertyAttributes *attributes = NULL) const = 0;
    public:
#undef OCPI_DATA_TYPE
#undef OCPI_DATA_TYPE_S
#define OCPI_DATA_TYPE(sca,corba,letter,bits,run,pretty,store)		\
      virtual run get##pretty##Parameter(unsigned ordinal, unsigned idx) const = 0; \
      virtual run get##pretty##PropertyOrd(unsigned ordinal, unsigned idx) const = 0; \
      virtual void						\
      set##pretty##PropertyOrd(unsigned ordinal, const run, unsigned idx) const = 0; \
      virtual void							\
      set##pretty##Cached(const PropertyInfo &, const OCPI::Base::Member &m, size_t offset, \
			  run, unsigned idx) const = 0;		\
      virtual void							\
      set##pretty##SequenceCached(const PropertyInfo &, const run *, size_t nElements) const = 0; \
      virtual run							\
      get##pretty##Cached(const PropertyInfo &, const OCPI::Base::Member &, size_t off, \
			  unsigned idx) const = 0;			\
      virtual unsigned							\
      get##pretty##SequenceCached(const PropertyInfo &, run *, size_t length) const = 0; \

#define OCPI_DATA_TYPE_S(sca,corba,letter,bits,run,pretty,store)                  \
      virtual void get##pretty##Parameter(unsigned ordinal, char *, size_t length, \
					  unsigned idx) const = 0; \
      virtual void set##pretty##PropertyOrd(unsigned ordinal, run val, unsigned idx) const = 0; \
      virtual void							\
      get##pretty##PropertyOrd(unsigned ord, char *, size_t length, unsigned idx) const = 0; \
      virtual void							\
      set##pretty##Cached(const PropertyInfo &, const OCPI::Base::Member &m, size_t offset, \
			  run, unsigned idx) const = 0;		\
      virtual void							\
      set##pretty##SequenceCached(const PropertyInfo &, const run *, size_t nElements) const = 0; \
      virtual run							\
      get##pretty##Cached(const PropertyInfo &, const OCPI::Base::Member &, size_t off, char *, \
			  size_t length, unsigned idx) const = 0;	\
      virtual unsigned							\
      get##pretty##SequenceCached(const PropertyInfo &, char **, size_t length, char *buf, \
				  size_t space) const = 0;		\

    OCPI_PROPERTY_DATA_TYPES
#undef OCPI_DATA_TYPE
#undef OCPI_DATA_TYPE_S
#define OCPI_DATA_TYPE_S OCPI_DATA_TYPE
      virtual size_t getSequenceLengthCached(const PropertyInfo &, const OCPI::Base::Member &,
					     size_t off) const = 0;
      virtual void getRawPropertyBytes(size_t offset, uint8_t *buf, size_t count) = 0;
      virtual void setRawPropertyBytes(size_t offset, const uint8_t *buf, size_t count) = 0;
    };

    class Container {
    public:
      virtual ~Container();
      // Do some work for this container
      // Return true if there is more to do.
      // Argument is yield time for blocking
      //      virtual bool run(uint32_t usecs = 0) = 0;
      // Perform the work of a separate thread, returning only when there is
      // nothing else to do.
      virtual void thread() = 0;
      virtual void stop() = 0;
      virtual const std::string &name() const = 0;
      virtual const std::string &os() const = 0;
      virtual const std::string &osVersion() const = 0;
      virtual const std::string &platform() const = 0;
      virtual const std::string &model() const = 0;
      virtual const std::string &arch() const = 0;
      virtual bool dynamic() const = 0;
    };
    class ContainerManager {
    public:
      static Container
        *find(const char *model, const char *which = NULL, const PValue *props = NULL),
	*find(const PValue *list),
	*get(unsigned n);
      static void
	list(bool onlyPlatforms),
	shutdown();
    };
    class Application; // forward reference for applications that span containers.
    // User interface for runtime property support for a worker.
    // Optimized for low-latency scalar and/or memory mapped access.
    // Not virtual.
    // Note that the API for this has the user typically constructing this structure
    // on their stack so that access to members (in inline methods) has no indirection.
    class Property {
      friend class OCPI::Container::Worker;
      // First, the reference memebers to maximize code sharing among constructors
    protected:
      const Worker &m_worker;               // which worker do I belong to
    public:
      PropertyInfo &m_info;           // details about property, not defined in the API
    private:
      OCPI::Base::Member &m_member;   // details about top-level member, not defined in the API
    private:
      const volatile uint8_t *m_readVaddr;
      volatile uint8_t *m_writeVaddr;
      bool m_readSync, m_writeSync;   // these exist to avoid exposing the innards of m_info.
      //      const static std::string s_empty;
    public:
      unsigned m_ordinal;
      Property(const Application &, const char *, const char * = NULL);
      Property(const Worker &, const char *);
      Property(const Application &, const std::string &, const char * = NULL);
      Property(const Worker &, const std::string &);
    protected:
      Property(const Worker &, unsigned);
    private:
      void init();
      void throwError(const char *err) const;
      const OCPI::Base::Member
	&descend(AccessList &list, size_t &offset, size_t *dimensionp = NULL) const;
      template <typename val_t> void setValueInternal(const OCPI::Base::Member &m, size_t off,
						      const val_t val) const;
      template <typename val_t> val_t getValueInternal(const OCPI::Base::Member &m,
						       size_t off) const;
      void checkTypeAlways(const OCPI::Base::Member &m, BaseType ctype, size_t n,
			   bool write) const;
      inline void checkType(const OCPI::Base::Member &m, BaseType ctype, size_t n,
			    bool write) const {
#if !defined(NDEBUG) || defined(OCPI_API_CHECK_PROPERTIES)
        checkTypeAlways(m, ctype, n, write);
#else
        (void)m;(void)ctype;(void)n;(void)write;
#endif
      }
    public:
      inline bool readSync() const { return m_readSync; }
      inline bool writeSync() const { return m_writeSync; }
      BaseType baseType() const;
      // If it is a string property, how big a buffer should I allocate to retrieve the value?
      size_t stringBufferLength() const;
      // We don't use scalar-type-based templates (sigh) so we can control which
      // types are supported explicitly.  C++ doesn't quite do the right thing.
      // The "m_writeVaddr/m_readVaddr" members are only non-zero if the
      // implementation does not produce errors and it is atomic at this data size

#define OCPI_DATA_TYPE(sca,corba,letter,bits,run,pretty,store)                  \
      inline void							        \
      set##pretty##Value(const OCPI::Base::Member &m, size_t offset, run val,   \
			 bool uncached = false) const {				\
        checkType(m, OCPI_##pretty, 0, true);			                \
        if (m_writeVaddr && uncached) {						\
	  /* avoid strict aliasing violation */                                 \
          /* was: *(store *)m_writeVaddr= *(store*)((void*)&(val));*/	        \
	  union { run runval; store storeval; } u; u.runval = val;	        \
          *reinterpret_cast<volatile store *>(m_writeVaddr+offset)= u.storeval; \
	  if (m_writeSync)						        \
             m_worker.propertyWritten(m_ordinal);                               \
        } else if (uncached)						        \
          m_worker.set##pretty##Property(m_info, m, offset, val, 0);    	\
        else								        \
          m_worker.set##pretty##Cached(m_info, m, offset, val, 0);    	        \
      }                                                                         \
      inline void set##pretty##Value(run val, bool uncached = false) const {    \
        set##pretty##Value(m_member, 0, val, uncached);			        \
      }									        \
      inline void set##pretty##SequenceValue(const run *vals, size_t n,         \
					     bool uncached = false) const {     \
        checkType(m_member, OCPI_##pretty, n, true);				\
        if (uncached)							        \
	  m_worker.set##pretty##SequenceProperty(m_info, vals, n);	        \
	else								        \
	  m_worker.set##pretty##SequenceCached(m_info, vals, n);		\
      }                                                                         \
      inline run							        \
      get##pretty##Value(const OCPI::Base::Member &m, size_t offset,            \
			 bool uncached = false) const {  			\
        checkType(m, OCPI_##pretty, 0, false);			                \
        if (m_readVaddr && uncached) {                                          \
	  if (m_readSync)			         			\
             m_worker.propertyRead(m_ordinal);                                  \
          union { store s; run r; }u;                                           \
          u.s = *(store *)(m_readVaddr + offset);			        \
          return u.r;                                                           \
        } else if (uncached)						        \
          return m_worker.get##pretty##Property(m_info, m, offset, 0);          \
        else								        \
          return m_worker.get##pretty##Cached(m_info, m, offset, 0);    	\
      }                                                                         \
      inline run get##pretty##Value(bool uncached = false) const {              \
	return get##pretty##Value(m_member, 0, uncached);			        \
      }									        \
      inline unsigned get##pretty##SequenceValue(run *vals, size_t n,           \
						 bool uncached = false) const { \
        checkType(m_member, OCPI_##pretty, n, false);				\
        if (uncached)							        \
	  return m_worker.get##pretty##SequenceProperty(m_info, vals, n);        \
	else								        \
	  return m_worker.get##pretty##SequenceCached(m_info, vals, n);	\
      }
#undef OCPI_DATA_TYPE_S
      // for a string we will take a function call overhead
#define OCPI_DATA_TYPE_S(sca,corba,letter,bits,run,pretty,store)                   \
      inline void							           \
      set##pretty##Value(const OCPI::Base::Member &m, size_t offset, const run val,\
                         bool uncached = false) const {			           \
        checkType(m, OCPI_##pretty, 0, true);				           \
	if (uncached)							           \
	  m_worker.set##pretty##Property(m_info, m, offset, val, 0);	           \
	else								           \
	  m_worker.set##pretty##Cached(m_info, m, offset, val, 0);	           \
      }                                                                            \
      inline void set##pretty##Value(const run val, bool uncached = false) const { \
	set##pretty##Value(m_member, 0, val, uncached); 			   \
      }                                                                            \
      inline void set##pretty##SequenceValue(const run *vals, size_t n,            \
					     bool uncached = false) const {        \
        checkType(m_member, OCPI_##pretty, n, true);				   \
	if (uncached)            						   \
	  m_worker.set##pretty##SequenceProperty(m_info, vals, n);	           \
	else								           \
	  m_worker.set##pretty##SequenceCached(m_info, vals, n);	                   \
      }                                                                            \
      inline const char *						           \
      get##pretty##Value(const OCPI::Base::Member &m, size_t offset, char *val,    \
			 size_t length, bool uncached = false) const {		   \
        checkType(m, OCPI_##pretty, 0, false);				           \
	if (uncached)							           \
          m_worker.get##pretty##Property(m_info, m, offset, val, length, 0);       \
	else								           \
          m_worker.get##pretty##Cached(m_info, m, offset, val, length, 0);         \
	return val;							           \
      }                                                                            \
      inline void get##pretty##Value(char *val, size_t length,                     \
				     bool uncached = false) const {	           \
	get##pretty##Value(m_member, 0, val, length, uncached);			   \
      }                                                                            \
      inline unsigned							           \
      get##pretty##SequenceValue(char **vals, size_t n, char *buf, size_t space,   \
				 bool uncached = false) const {                    \
        checkType(m_member, OCPI_##pretty, n, false);				   \
	if (uncached)							           \
	  return m_worker.get##pretty##SequenceProperty(m_info, vals, n, buf, space);\
	else								           \
	  return m_worker.get##pretty##SequenceCached(m_info, vals, n, buf, space); \
      }
      OCPI_PROPERTY_DATA_TYPES
#undef OCPI_DATA_TYPE_S
#define OCPI_DATA_TYPE_S OCPI_DATA_TYPE
#undef OCPI_DATA_TYPE
      // ==========================================================================================
      // Updated access API, consistent with worker, property, slave, string or const char *
      // These all use AccessList to access values that are part of a property
      // ==========================================================================================
      void setProperty(const char *value, AccessList &list = emptyList) {
	m_worker.setProperty(m_info, value, list);
      }
      void setProperty(const std::string &value, AccessList &list = emptyList) {
	setProperty(value.c_str(), list);
      }
      const char *getProperty(std::string &value, AccessList &list = emptyList) {
	return m_worker.getProperty(m_info, value, list);
      }
      template <typename T> void setValue(T val, AccessList &l = emptyList) const;
      void setValue(const std::string &val, AccessList &l = emptyList) const;
      template <typename T> T getValue(AccessList &l = emptyList) const; // must call with explicit type
      // Get current length of sequence
      size_t getSequenceLength(AccessList &l = emptyList, bool uncached = false) const;
      // ==========================================================================================
      // End of access list interfaces
      // ==========================================================================================

    };
    // ACI functions for using servers
    void useServers(const char *server = NULL, const PValue *params = NULL,
		    bool verbose = false);
    void useServer(const char *server, bool verbose = false);
    void enableServerDiscovery();
    bool isServerSupportAvailable();
  }
}
#endif
