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
 * Definitions for an assembly that is processed against the available libraries
 * to look for available implementations, and to filter based on selection criteria.
 * This assembly adds the library (and implementation candidates) aspect to the
 * underlying OU::Assembly, which is just about representing the metadata
 * independent of the library aspect of implementations
 */
#ifndef OCPI_LIBRARY_ASSEMBLY_H
#define OCPI_LIBRARY_ASSEMBLY_H

#include <string>
#include <forward_list>
#include "OcpiLibraryManager.h"
#include "OcpiUtilAssembly.h"

namespace OCPI {
  namespace Library {

    class Assembly;
    // This class represents a candidate implementation for an instance.
    struct Candidate {
      // The impl is not a reference since std::vector must copy it :-(
      const Implementation *impl;
      unsigned score;
      mutable Assembly *slaves; // hold a slave/sub assembly to be merged when this candidate is used
      mutable size_t nInstances, nConnections;
      // Temporary port delegations need to be "undone" by using these fixups
      struct Fixup {
	OCPI::Util::Assembly::Connection *appConn;
	OCPI::Util::Assembly::Connection *slaveConn;
	OCPI::Util::Assembly::ConnPort   *connPort;        // where to restore the app conn
	OCPI::Util::Assembly::ConnPort    masterConnPort;  // The port/index value to restore
	unsigned masterOrdinal;
	Fixup(OCPI::Util::Assembly::Connection *a_appConn,
	      OCPI::Util::Assembly::Connection *a_slaveConn,
	      OCPI::Util::Assembly::ConnPort *a_connPort,
	      unsigned a_masterOrdinal)    // The master port to restore
	  : appConn(a_appConn), slaveConn(a_slaveConn), connPort(a_connPort),
	    masterConnPort(*a_connPort), masterOrdinal(a_masterOrdinal) {
	}
      };
      std::forward_list<Fixup> m_portFixups;
      inline Candidate(const Implementation &a_impl, unsigned a_score)
	: impl(&a_impl), score(a_score), slaves(NULL), nInstances(0), nConnections(0) {}
    };
    typedef std::vector<Candidate> Candidates;   // a set of candidates for an instance
    typedef Candidates::iterator CandidatesIter;

    // A library::assembly adds value to the underlying/inherited util::assembly
    // By finding candidate implementations in the available artifact libraries,
    // and perhaps adding proxy slave instances
    class Assembly : public OCPI::Util::Assembly,  public ImplementationCallback {
      // This instance class below is the library layer's overlay on the basic OU instance
      // It usually just references the OU::Assembly instance, but in the case of
      // proxies or file IO, the library layer may add instances
    public:
      struct Instance {
	OCPI::Util::Assembly::Instance &m_utilInstance; // lower level assy instance structure
	OCPI::Util::Assembly::Port **m_assyPorts;       // map impl port ordinal to OU assy port
                                                	// we do the map based on the first impl
	Candidates m_candidates;                        // The candidate impls for this instance
	unsigned m_nPorts;
	size_t m_scale;
	std::string m_device;                           // if instance specifies a device
	Instance *m_master;                             // The master if this is a slave
	Instance(OCPI::Util::Assembly::Instance &utilInstance, Instance *master = NULL);
	~Instance();

	bool resolveUtilPorts(const Implementation &i, OCPI::Util::Assembly &a);
	bool checkConnectivity(Candidate &c, Assembly &assy);
	bool foundImplementation(const Implementation &i, std::string &model,
				 std::string &platform);
        void strip_pf(std::string&) const;
	const std::string &name() const { return m_utilInstance.m_name; }
	const std::string &specName() const { return m_utilInstance.m_specName; }
	const OCPI::Util::Assembly::Properties &properties() const {
	  return m_utilInstance.m_properties;
	}
      };
    private:
      typedef std::vector<Instance *> Instances;
      typedef Instances::iterator InstancesIter;
      std::string m_model;                        // used during implementation processing
      std::string m_platform;                     // ditto
      const PValue *m_params;                     // params of assembly during parsing (not copied)
      unsigned m_maxCandidates;                   // maximum number of candidates for any instance
      Instance *m_tempInstance;                   // our instance currently being processed
      Instances m_instances;                      // This layer's instances
      bool      m_deployed;                       // deployment decisions are already made
      size_t    m_nAppInstances;                  // original app instance count
    public:
      // explicit Assembly(const char *file, const OCPI::Util::PValue *params);
      // explicit Assembly(const std::string &string, const OCPI::Util::PValue *params);
      explicit Assembly(ezxml_t xml, const char *name, const OCPI::Util::PValue *params);
      ~Assembly();
      Instance &instance(size_t n) const { return *m_instances[n]; }
      size_t nInstances() { return m_instances.size(); }
      size_t nAppInstances() const { return m_nAppInstances; }
      Instances &instances() { return m_instances; }
      OCPI::Util::Assembly::Instance &utilInstance(size_t n) const {
	return m_instances[n]->m_utilInstance;
      }
      bool badConnection(const Implementation &thisImpl, const OCPI::Util::Port &thisPort,
			 const Implementation &otherImpl, const OCPI::Util::Port &otherPort);
      Port **assyPorts(size_t inst) {
	assert(m_instances[inst]->m_assyPorts);
	return m_instances[inst]->m_assyPorts;
      }
      Port *assyPort(size_t inst, size_t port) {
	assert(m_instances[inst]->m_assyPorts);
	return m_instances[inst]->m_assyPorts[port];
      }
      // Reference counting
      void operator ++( int );
      void operator --( int );

      const char *getPortAssignment(const char *pName, const char *assign, size_t &instn,
				    size_t &portn, const OCPI::Util::Port *&port,
				    const char *&value, bool removeExternal = false);
    private:
      void addInstance(const OCPI::Util::PValue *params);
      const char *addFileIoInstances(const OCPI::Util::PValue *params);
      void findImplementations(const OCPI::Util::PValue *params);
      bool foundImplementation(const Implementation &i, bool &accepted);
      int m_refCount;
    };
  }
}
#endif
