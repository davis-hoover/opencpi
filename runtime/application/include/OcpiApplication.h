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
 * Definitions for the top level application, whose workers are executed on a
 * variety of containers.  The "Application" object is a runtime thing that is an instance of
 * an assembly.  Thus the assembly is the template for the application.
 *
 * This file is NOT an exposed API file.
 */
#ifndef OCPI_APPLICATION_H
#define OCPI_APPLICATION_H

#include <string>
#include <map>
#include "OcpiUtilMisc.h"
#include "OcpiLibraryAssembly.h"
#include "ContainerManager.h"
#include "ContainerApplication.h"
#include "ContainerLauncher.h"
#include "OcpiApplicationApi.h"

// These are application PValue parameters that should ALSO be given to discovery.
#define OCPI_DISCOVERY_PARAMETERS "verbose"
// These are pvalue parameters that should ONLY be given to discovery.
#define OCPI_DISCOVERY_ONLY_PARAMETERS "simDir", "simTicks"
namespace OCPI {
  namespace Container {
    class Launcher;
    class LocalLauncher;
    class RemoteLauncher;
  }
  namespace API {

    class ApplicationI {
      std::string m_timeString; // used as a temp in printing time intervals
      OS::Time m_earliest, m_constructed, m_initialized, m_started, m_finished;
      typedef OCPI::Container::Container::CMap CMap;
      ezxml_t m_deployXml;
      ezxml_t m_appXml;
      char   *m_copy; // copy of input XML string
      OCPI::Library::Assembly &m_assembly;

      size_t m_nInstances;
      struct Deployment {
	size_t m_scale;                                // scale of this deployment
	std::vector<unsigned> m_containers;            // containers used by this deployment
	std::vector<const OCPI::Library::Implementation *> m_impls; // implementation on each container
	CMap m_feasible;
	bool m_hasMaster;                       // convenience
	std::string m_name;                     // convenience
	const OCPI::Util::Assembly::Properties *m_properties; // convenience
	std::vector<size_t> m_slaves;           // the instance ordinals of explicit slaves
	// These members are used *after* deployment planning
	size_t m_firstMember;                   // index of first member in launch members
	OCPI::Container::Launcher::Crew m_crew;	// launcher info for this instance;
	std::vector<unsigned> m_usedContainers; // container for each crew member

	Deployment();
	~Deployment();
	Deployment(const Deployment&) = default;
	Deployment &operator=(const Deployment &d);
	void set(const std::string &name, size_t scale, const unsigned *containers,
		 const OCPI::Library::Implementation * const *impls, CMap map, bool hasMaster,
		 const OCPI::Library::Assembly::Properties * );
      };
      // This structure is used during deployment planning.
      struct Instance : public OCPI::Container::Callback {
	Deployment m_deployment;      // Current deployment when generating all of them
	//	Deployment m_bestDeployment;
	std::vector<CMap> m_feasibleContainers;
	const char *m_containerName;  // used to avoid touching the container
	// The launcher info for this application instance;
	//OCPI::Container::Launcher::Crew m_crew;
	// Support for collecting candidate together that have the same actual implementation
	// code even though they may be compiled for different targets.
	// map is from the qualified impl name to a list of candidate indices.
	typedef std::list<unsigned> Candidates;
	typedef Candidates::iterator CandidatesIter;
	typedef std::map<std::string, Candidates> ScalableCandidates;
	typedef ScalableCandidates::value_type ScalablePair;
	typedef ScalableCandidates::iterator ScalableCandidatesIter;
	ScalableCandidates m_scalableCandidates;
	// This array is of indices in the usedcontainer array, not global indices
	// std::vector<unsigned> m_usedContainers; // container for each crew member
	//	size_t m_firstMember;           // index of first member in launch members
	CMap m_curMap;                  // temp indicating possible containers for a candidate
	//	unsigned m_curContainers;       // temp that counts containers for a candidate
	Instance();
	~Instance();
        const char *init(const OCPI::Library::Assembly &assy, size_t n, bool verbose,
			 const PValue *params);
	void collectCandidate(const OCPI::Library::Candidate &c, unsigned n);
	void finalizePortParam(OCPI::Util::Assembly::Instance &ui, const OCPI::Util::PValue *params,
			       const char *param);
	bool foundContainer(OCPI::Container::Container &i);
      };
      struct Booking {
	OCPI::Library::Artifact *m_artifact;
	CMap m_usedImpls;         // which fixed implementations in the artifact are in use
	Booking() : m_artifact(NULL), m_usedImpls(0) {}
      };
      std::vector<Instance> m_instances;
      std::vector<Deployment> m_bestDeployments;
      // The instance objects for the launcher
      OCPI::Container::Launcher::Members m_launchMembers;
      OCPI::Container::Launcher::Connections m_launchConnections;
      Booking *m_bookings;
      // This class represents a mapping from an externally visible property of the assembly
      // to an individual property of an instance. It must be at this layer
      // (not util::assembly or library::assembly) because it potentially depends on the
      // implementation specific properties of the implementations selected.
      struct Property {
	std::string m_name;     // qualified name (instance[.:=]property) or mapped name
	unsigned m_instance;    // ordinal of instance in assembly
	unsigned m_property;    // ordinal of property in implememtation of instance
	const char *m_dumpFile; // pointer to dump file if one was specified
      } *m_properties;
      // This is a queue entry for a delayed property value setting
      struct DelayedPropertyValue {
	unsigned m_instance;
	const OCPI::Util::Property *m_property;
	OCPI::Util::Value m_value;
      };
      typedef std::multimap<OCPI::Util::Assembly::Delay, DelayedPropertyValue> DelayedPropertyValues;
      DelayedPropertyValues    m_delayedPropertyValues;
      size_t m_nProperties;
      CMap m_allMap;              // A map of all containers chosen/used
      unsigned *m_global2used;         // A map from global ordinals to our "used" orinals
      unsigned m_nContainers;     // how many containers have been used
      unsigned *m_usedContainers; // A map from used container to global container

      // Now the runtime state.
      std::set<OCPI::Container::Launcher *> m_launchers; // the launchers used by our containers
      OCPI::Container::Container **m_containers;      // the actual containers we are using
      OCPI::Container::Application **m_containerApps; // per used container, the container app

      // This structure captures info to allow the connection to be made AFTER launch.
      // It is basically a map from the name of the external assembly port to the
      // launcher connection that includes that external assembly port.
      struct External {
	OCPI::Container::Launcher::Connection &m_connection;
	OCPI::Container::LocalPort *m_external; // created (later) from connectExternal.
	inline External(OCPI::Container::Launcher::Connection &conn)
	  : m_connection(conn), m_external(NULL) {}
      };
      typedef std::map<const char*, External, OCPI::Util::ConstCharComp> Externals;
      typedef std::pair<const char*, External> ExternalPair;
      typedef Externals::iterator ExternalsIter;
      Externals m_externals;
      std::vector<External *> m_externalsOrdered; // to support ordinal-based navigation
      enum CMapPolicy {
	RoundRobin,
	MinProcessors,
	MaxProcessors
      };
      CMapPolicy m_cMapPolicy;
      unsigned   m_processors;
      unsigned m_currConn;
      unsigned m_bestScore;
      // This list is a copy of the connections active for the deployment
      std::list<OCPI::Util::Assembly::Connection> m_bestConnections;
      bool m_hex;
      bool m_hidden;
      bool m_uncached;
      bool m_launched;
      bool m_verbose;
      bool m_dump;
      std::string m_dumpFile;
      bool m_dumpPlatforms;
      Application &m_apiApplication;

      void clear();
      void init(const OCPI::API::PValue *params);
      void initExternals(const OCPI::API::PValue *params);
      void setLaunchPort(OCPI::Container::Launcher::Port &p, const OCPI::Util::Port *mp,
			 const OCPI::Util::PValue *connParams, const std::string &name,
			 const OCPI::Util::PValue *portParams,
			 const OCPI::Container::Launcher::Member *member,
			 const OCPI::Util::Assembly::External *ep, size_t scale, size_t index);
      void initLaunchConnections();
      const OCPI::Container::Launcher::Connection &
	findOtherConnection(const OCPI::Container::Launcher::Port &p);
      void initLaunchMembers();
      void finalizeLaunchPort(OCPI::Container::Launcher::Port &p);
      void finalizeLaunchConnections();
      void finalizeLaunchMembers();
      void checkPropertyValue(unsigned nInstance, const OCPI::Util::Worker &w,
			      const OCPI::Util::Assembly::Property &aProp, unsigned *&pn,
			      OCPI::Util::Value *&pv);
      const OCPI::Util::Port *getMetaPort(unsigned n) const;
      // return our used-container ordinal
      unsigned addContainer(unsigned container, bool existOk = false);
      unsigned getUsedContainer(unsigned container);
      void delegateAssyPort(OCPI::Util::Assembly::Port &assyPort, unsigned instNum,
			    unsigned slaveInstNum, const OCPI::Library::Implementation &slaveImpl,
			    const OCPI::Util::Port &masterPort,
			    const OCPI::Util::Port *&slavePort);
      bool maybeDelegate(unsigned instNum, OCPI::Util::Assembly::Port &assyPort,
			 const OCPI::Util::Port *&port,
			 const OCPI::Library::Implementation *&impl);
      bool maybeDelegateToSlavePort(unsigned instNum, const OCPI::Library::Implementation &slaveImpl,
				    const OCPI::Util::Port &port,
				    OCPI::Util::Assembly::Port *&otherAssyPort);
      bool resolveInstanceSlaves(unsigned instNum, OCPI::Library::Candidate &c,
				 const std::string &reject);
      void restoreSlaves(OCPI::Library::Candidate &c);
      bool connectionsOk(OCPI::Library::Candidate &c, unsigned instNum);
      void finalizeProperties(const OCPI::Util::PValue *params);
      const char *finalizePortParam(const OCPI::Util::PValue *params, const char *pName);
      void finalizeExternals();
      bool resolveExplicitSlaves();
      bool bookingOk(Booking &b, OCPI::Library::Candidate &c, unsigned n);
      void policyMap(Deployment &d, unsigned instNum);
      void setPolicy(const OCPI::API::PValue *params);
      Property &findProperty(const char * worker_inst_name, const char * prop_name = NULL) const;
      void dumpDeployment(unsigned score);
      void doScaledInstance(unsigned instNum, unsigned score);
      void deployInstance(unsigned instNum, unsigned score, size_t scale,
			  unsigned *containers, const OCPI::Library::Implementation **impls,
			  CMap feasible);
      void doInstance(unsigned instNum, unsigned score);
      void checkExternalParams(const char *pName, const OCPI::Util::PValue *params);
      void prepareInstanceProperties(unsigned nInstance,
				     const OCPI::Library::Implementation &impl,
				     unsigned *&pn, OCPI::Util::Value *&pv);
      void planDeployment(const PValue *params);
      void importDeployment(const char *file, ezxml_t &xml, const PValue *params);
      const char *timeDiff(OS::Time later, OS::Time earlier);
    public:
      explicit ApplicationI(OCPI::API::Application &app, const char *file,
			    const OCPI::API::PValue *params = NULL);
      //      explicit ApplicationI(OCPI::API::Application &app, const std::string &string,
      //			    const OCPI::API::PValue *params = NULL);
      explicit ApplicationI(OCPI::API::Application &app, ezxml_t xml, const char *name,
			    const OCPI::API::PValue *params = NULL);
      explicit ApplicationI(OCPI::API::Application &app, OCPI::Library::Assembly &,
			    const OCPI::API::PValue *params = NULL);
      ~ApplicationI();
      OCPI::Library::Assembly &assembly() { return m_assembly; }
      const std::string &name() const { return m_assembly.name(); }
      void initialize();
      void startMasterSlave(bool isMaster, bool isSlave, bool isSource);
      void start();
      void stop();
      bool verbose() const { return m_verbose; }
      void setDelayedProperties();
      bool wait(unsigned long timeout_us, bool timeOutIsError);
      bool wait(OS::Timer *timer);
      void finish();
      ExternalPort &getPort(const char *, const OCPI::API::PValue *);
      ExternalPort &getPort(unsigned index, std::string &name );
      size_t getPortCount();
      friend struct Property;
      size_t nProperties() const { return m_nProperties; }
      const OCPI::Util::Property *property(unsigned ordinal, std::string &name) const;
      Worker &getPropertyWorker(const char *name, const char *&pname) const;
      const char *getProperty(unsigned ordinal, std::string &value, AccessList &list = emptyList,
			      PropertyOptionList &options = noPropertyOptions,
			      PropertyAttributes *attributes = NULL) const;
      const char *getProperty(const char *pname, std::string &value, AccessList &list = emptyList,
			      PropertyOptionList &options = noPropertyOptions,
			      PropertyAttributes *attributes = NULL) const;
      bool getProperty(unsigned ordinal, std::string &name, std::string &value, bool hex,
		       bool *parp, bool *cachedp, bool uncached, bool *hiddenp) const;
      void getProperty(const char * wname, const char * pname, std::string &value, bool hex);
      void setProperty(const char* worker_name, const char* prop_name, const char *value,
		       OCPI::API::AccessList &list = OCPI::API::emptyList);
      void dumpDeployment(const char *appFile, const std::string &file);
      void dumpProperties(bool printParameters, bool printCached, const char *context) const;
      void genScaPrf(const char *outDir) const;
      void genScaScd(const char *outDir) const;
      void genScaSpd(const char *outDir, const char *pkg) const;
    };
    // This is here to avoid exposing the ezxml_t stuff to the API
    class ApplicationX : public Application {
    public:
      ApplicationX(ezxml_t xml, const char *name, const OCPI::API::PValue *params = NULL);
      // Tool classes not for runtime
      inline void genScaPrf(const char *outDir) const { m_application.genScaPrf(outDir); }
      inline void genScaScd(const char *outDir) const { m_application.genScaScd(outDir); }
      inline void genScaSpd(const char *outDir, const char *pkg) const {
	m_application.genScaSpd(outDir, pkg);
      }
    };
  }
}
#endif
