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
#include "OcpiPValueApi.h"
#include "OcpiUtilPropertyApi.h"
#include "OcpiUtilExceptionApi.h"
#include "OcpiLibraryApi.h"

namespace OCPI {
  namespace Container {
    class Port;
    class Worker;
    class LocalLauncher;
  }
  namespace Remote {
    class RemoteLauncher;
  }
  namespace Util {
    class Member;
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
    class Port {
      friend class OCPI::Container::LocalLauncher;
      friend class OCPI::Container::Port;
      friend class OCPI::Remote::RemoteLauncher;
    protected:
      virtual ~Port();
      virtual OCPI::Container::Port &containerPort() = 0;
    public:
      virtual void connect(Port &other, const PValue *myParams = NULL,
			   const PValue *otherParams = NULL) = 0;
    };
    class Property;
    class PropertyInfo;
    class PropertyAccess {
    public:
      virtual ~PropertyAccess();
      virtual void propertyWritten(unsigned ordinal) const = 0;
      virtual void propertyRead(unsigned ordinal) const = 0;
      // FIXME:  These should be protected, but the proxy code generator uses them too
      // These methods are used by the Property methods below when the
      // fast path using memory-mapped access cannot be used.
#define OCPI_DATA_TYPE(sca,corba,letter,bits,run,pretty,store)		\
      virtual void							\
      set##pretty##Property(const PropertyInfo &, const Util::Member *m, size_t offset, \
			    const run, unsigned idx) const = 0;			\
      virtual void							\
      set##pretty##SequenceProperty(const Property &, const run *, size_t nElements) const = 0; \

    OCPI_PROPERTY_DATA_TYPES
#undef OCPI_DATA_TYPE
#undef OCPI_DATA_TYPE_S
// The ordinal-based one is for proxies, with no navigation, but indexing
// The prop/member one is for ACI, which has navigation
#define OCPI_DATA_TYPE(sca,corba,letter,bits,run,pretty,store)		\
    virtual run								\
    get##pretty##Property(const PropertyInfo &, const Util::Member *, size_t off, \
			  unsigned idx) const = 0;			\
    virtual unsigned							\
    get##pretty##SequenceProperty(const Property&, run *, size_t length) const = 0; \

// The ordinal-based one is for proxies, with no navigation, but indexing
// The prop/member one is for ACI, which has navigation
#define OCPI_DATA_TYPE_S(sca,corba,letter,bits,run,pretty,store)	\
    virtual void							\
    get##pretty##Property(const PropertyInfo &, const Util::Member *, size_t off, char *, \
			  size_t length, unsigned idx) const = 0;	\
    virtual unsigned							\
    get##pretty##SequenceProperty(const Property &, char **, size_t length, char *buf, \
				  size_t space) const = 0; \

    OCPI_PROPERTY_DATA_TYPES
#undef OCPI_DATA_TYPE
#undef OCPI_DATA_TYPE_S
#define OCPI_DATA_TYPE_S OCPI_DATA_TYPE
    };
    class Worker : virtual public PropertyAccess {
      friend class Property;
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
      virtual Port &getPort(const char *name, const PValue *props = NULL) = 0;
      virtual void start() = 0;
      virtual void stop() = 0;
      virtual void release() = 0;
      virtual void beforeQuery() = 0;
      virtual void afterConfigure() = 0;
      virtual void test() = 0;
      // Untyped property setting - slowest but convenient
      virtual void setProperty(const char *name, const char *value) = 0;
      // Untyped property list setting - slow but convenient
      virtual void setProperties(const char *props[][2]) =  0;
      // Typed property list setting - slightly safer, still slow
      virtual void setProperties(const PValue *props) =  0;
      virtual bool getProperty(unsigned ordinal, std::string &name, std::string &value,
			       bool *unreadablep = NULL, bool hex = false,
			       bool *cachedp = NULL, bool uncached = false, bool *hiddenp = NULL)
	                      = 0;
#undef OCPI_DATA_TYPE
#undef OCPI_DATA_TYPE_S
#define OCPI_DATA_TYPE(sca,corba,letter,bits,run,pretty,store)		\
      virtual run get##pretty##Parameter(unsigned ordinal, unsigned idx) const = 0; \
      virtual run get##pretty##PropertyOrd(unsigned ordinal, unsigned idx) const = 0; \
      virtual void						\
      set##pretty##PropertyOrd(unsigned ordinal, const run, unsigned idx) const = 0;

#define OCPI_DATA_TYPE_S(sca,corba,letter,bits,run,pretty,store)                  \
      virtual void get##pretty##Parameter(unsigned ordinal, char *, size_t length, \
					  unsigned idx) const = 0; \
      virtual void set##pretty##PropertyOrd(unsigned ordinal, run val, unsigned idx) const = 0; \
      virtual void							\
      get##pretty##PropertyOrd(unsigned ord, char *, size_t length, unsigned idx) const = 0;

    OCPI_PROPERTY_DATA_TYPES
#undef OCPI_DATA_TYPE
#undef OCPI_DATA_TYPE_S
#define OCPI_DATA_TYPE_S OCPI_DATA_TYPE
      virtual void getRawPropertyBytes(size_t offset, uint8_t *buf, size_t count) = 0;
      virtual void setRawPropertyBytes(size_t offset, const uint8_t *buf, size_t count) = 0;
    };

    // This class is used when the application is being constructed using
    // API calls placing specific workers on specific containers.
    // When the ContainerApplication is deleted, all the workers placed on it
    // are destroyed together.
    class ContainerApplication {
    public:
      virtual ~ContainerApplication();
      // Create an application from an explicit artifact url
      // specifying lots of details, including a particular implementation and
      // possibly a particular pre-existing instance:
      //
      // file - name of artifact file
      // artifactParams - artifact loading parameters
      // instName - instance name within the application
      // implName - implementation name within the artifact (e.g. which worker)
      // preInstName - name of the pre-existing instance within the artifact (if it has them)
      // wProps - initial values of worker properties
      // wParams - extensible parameters for worker creation
      // selectCriteria - implementation selection criteria
      virtual Worker &createWorker(const char *file, const PValue *artifactParams,
				   const char *instName, const char *implName,
				   const char *preInstName = NULL,
				   const PValue *wProps = NULL,
				   const PValue *wParams = NULL,
				   const char *selectCriteria = NULL) = 0;
      // Simpler method to create a worker by its spec name (name provided in the spec file),
      // with the artifact found from looking at libraries in the library path, finding
      // what implementation will run on the container of this container-app.
      // Since some implementations might have connectivity contraints,
      // we also pass in a simple list of other workers destined for
      // the same container and how they are connected to this one.
      // The list is terminated with the "port" member == NULL
      virtual Worker &createWorker(const char *instName, const char *specName,
				   const PValue *wProps = NULL,
				   const PValue *wParams = NULL,
				   const char *selectCriteria = NULL,
				   const Connection *connections = NULL) = 0;
      //      virtual void start() = 0;
    };
    class Container {
    public:
      virtual ~Container();
      virtual ContainerApplication *createApplication(const char *name = NULL,
						      const PValue *props = NULL) = 0;
      // Do some work for this container
      // Return true if there is more to do.
      // Argument is yield time for blocking
      virtual bool run(uint32_t usecs = 0) = 0;
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
    // Structure to capture indexing arrays and sequences and navigating to struct members
    // The only intended usage is in the initializer_list below
    struct Access {
      union {
	size_t m_index;
	const char *m_member;
      };
      bool m_number;
      Access(size_t subscript)   : m_index(subscript), m_number(true) {} // get element
      // Allow (signed) ints for convenience, including 0, which should not end up being NULL for const char*
      Access(int subscript)      : m_index((assert(subscript >= 0), (size_t)subscript)), m_number(true) {}
      Access(const char *member) : m_member(member), m_number(false) {}; // get member
    };
    typedef const std::initializer_list<Access> AccessList;
    const AccessList emptyList; // because GCC 4.4 doesn't completely support init lists
    // User interface for runtime property support for a worker.
    // Optimized for low-latency scalar and/or memory mapped access.
    // Not virtual.
    // Note that the API for this has the user typically constructing this structure
    // on their stack so that access to members (in inline methods) has no indirection.
    class Property {
      friend class OCPI::Container::Worker;
    protected:
      const Worker &m_worker;               // which worker do I belong to
    private:
      const volatile uint8_t *m_readVaddr;
      volatile uint8_t *m_writeVaddr;
    public:
      PropertyInfo &m_info;           // details about property, not defined in the API
      unsigned m_ordinal;
    private:
      bool m_readSync, m_writeSync;   // these exist to avoid exposing the innards of m_info.
    public:
      Property(const Application &, const char *, const char * = NULL);
      Property(const Worker &, const char *);
    private:
      Property(const Worker &, unsigned);
      void throwError(const char *err) const;
      template <typename val_t> void setValueInternal(const OCPI::Util::Member &m, size_t off,
						      const val_t val) const;
      template <typename val_t> val_t getValueInternal(const OCPI::Util::Member &m, 
						       size_t off) const;
      void checkTypeAlways(const OCPI::Util::Member *m, BaseType ctype, size_t n,
			   bool write) const;
      inline void checkType(const OCPI::Util::Member *m, BaseType ctype, size_t n,
			    bool write) const {
#if !defined(NDEBUG) || defined(OCPI_API_CHECK_PROPERTIES)
        checkTypeAlways(m, ctype, n, write);
#else
        (void)m;(void)ctype;(void)n;(void)write;
#endif
      }
      const OCPI::Util::Member &descend(AccessList &list, size_t &offset) const;
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
      set##pretty##Value(const OCPI::Util::Member *m, size_t offset, run val) const { \
        checkType(m, OCPI_##pretty, 0, true);			                \
        if (m_writeVaddr) {						        \
	  /* avoid strict aliasing violation */                                 \
          /* was: *(store *)m_writeVaddr= *(store*)((void*)&(val));*/	        \
	  union { run runval; store storeval; } u; u.runval = val;	        \
          *reinterpret_cast<volatile store *>(m_writeVaddr+offset)= u.storeval; \
	  if (m_writeSync)						        \
             m_worker.propertyWritten(m_ordinal);                               \
        } else								        \
          m_worker.set##pretty##Property(m_info, m, offset, val, 0);    	\
      }                                                                         \
      inline void set##pretty##Value(run val) const {                           \
        set##pretty##Value(NULL, 0, val);        				\
      }									        \
      inline void set##pretty##SequenceValue(const run *vals, size_t n) const { \
        checkType(NULL, OCPI_##pretty, n, true);				\
        m_worker.set##pretty##SequenceProperty(*this, vals, n);                 \
      }                                                                         \
      inline run							        \
      get##pretty##Value(const OCPI::Util::Member *m, size_t offset) const {    \
        checkType(m, OCPI_##pretty, 0, false);			                \
        if (m_readVaddr) {                                                      \
	  if (m_readSync)			         			\
             m_worker.propertyRead(m_ordinal);                                  \
          union { store s; run r; }u;                                           \
          u.s = *(store *)(m_readVaddr + offset);			        \
          return u.r;                                                           \
        } else                                                                  \
          return m_worker.get##pretty##Property(m_info, m, offset, 0); \
      }                                                                         \
      inline run get##pretty##Value() const {                                   \
	return get##pretty##Value(NULL, 0);				        \
      }									        \
      inline unsigned get##pretty##SequenceValue(run *vals, size_t n) const {   \
        checkType(NULL, OCPI_##pretty, n, false);				\
        return m_worker.get##pretty##SequenceProperty(*this, vals, n);          \
      }
#undef OCPI_DATA_TYPE_S
      template <typename T> void setValue(T val, AccessList &l = emptyList) const;
      void setValue(const std::string &val, AccessList &l = emptyList) const;
      template <typename T> T getValue(AccessList &l = emptyList) const; // must call with explicit type
      // for a string we will take a function call overhead
#define OCPI_DATA_TYPE_S(sca,corba,letter,bits,run,pretty,store)                   \
      inline void							           \
      set##pretty##Value(const OCPI::Util::Member *m, size_t offset, const run val) const { \
        checkType(m, OCPI_##pretty, 0, true);				           \
        m_worker.set##pretty##Property(m_info, m, offset, val, 0); \
      }                                                                            \
      inline void set##pretty##Value(const run val) const {                        \
	set##pretty##Value(NULL, 0, val);				           \
      }                                                                            \
      inline void set##pretty##SequenceValue(const run *vals, size_t n) const {    \
        checkType(NULL, OCPI_##pretty, n, true);				   \
        m_worker.set##pretty##SequenceProperty(*this, vals, n);                    \
      }                                                                            \
      inline void							           \
      get##pretty##Value(const OCPI::Util::Member *m, size_t offset, char *val,    \
			 size_t length) const {				           \
        checkType(m, OCPI_##pretty, 0, false);				           \
        m_worker.get##pretty##Property(m_info, m, offset, val, length, 0); \
      }                                                                            \
      inline void get##pretty##Value(char *val, size_t length) const {             \
	get##pretty##Value(NULL, 0, val, length);			\
      }                                                                            \
      inline unsigned get##pretty##SequenceValue                                   \
        (char **vals, size_t n, char *buf, size_t space) const {                   \
        checkType(NULL, OCPI_##pretty, n, false);				   \
        return m_worker.get##pretty##SequenceProperty                              \
          (*this, vals, n, buf, space);                                            \
      }
      OCPI_PROPERTY_DATA_TYPES
#undef OCPI_DATA_TYPE_S
#define OCPI_DATA_TYPE_S OCPI_DATA_TYPE
#undef OCPI_DATA_TYPE
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
