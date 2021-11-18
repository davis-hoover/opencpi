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

/**
 * \file
 * \brief Time Emit output format classes
 *
 * Revision History:
 *
 *     01/10/2012 - John F. Miller
 *                  Initial version.
 */


#ifndef __OCPI_TIME_EMIT_OUPUTFORMATTER_H__
#define __OCPI_TIME_EMIT_OUPUTFORMATTER_H__

#include <stdio.h>
#include <iostream>
#include <algorithm>
#include <memory>
#include "TimeEmit.hh"

#define min(a,b) a<b?a:b
#define max(a,b) a>b?a:b

namespace OCPI {

  namespace TimeEmit {
    
    namespace Formatter {

#ifdef OCPI_TIME_EMIT_SUPPORT
      typedef OCPI::Time::Emit::OwnerId OwnerId;
      typedef OCPI::Time::Emit::EventId EventId;
      class XMLReader {

     private:
	ezxml_t m_xml;  // root
	ezxml_t m_desc_xml;
	ezxml_t m_owner_xml;
	ezxml_t m_event_xml;

      public:
	XMLReader( std::string & filename ) {


	  // First read in the events
	  std::string xml_data("<EventData>\n");
	  try {
	      std::ifstream in( filename.c_str(), std::ios::in );
		char b[512];
	      do {
		in.getline( b, 512 );
		if ( strcmp( b, "<EventData>" ) == 0 ) break;
		Event e;
		char buf[256];
		int id,owner,type;
		sscanf( b, "%d,%d,%d,%llu,%s", &id, &owner,&type, (unsigned long long*) &e.hdr.time_ticks, buf);
		e.hdr.eid = (uint16_t)id;
		e.hdr.owner = (uint16_t)owner;
		e.svalue = buf;
		
		switch (type ) {
		case OCPI::Time::Emit::DT_u:
		  e.v.uvalue = strtoul( e.svalue.c_str(), NULL,0 );
		  break;
		case OCPI::Time::Emit::DT_i:
		  e.v.ivalue = strtol( e.svalue.c_str(),NULL,0 );
		  break;
		case OCPI::Time::Emit::DT_c:
		  e.v.cvalue = (char*)e.svalue.c_str();
		  break;
		case OCPI::Time::Emit::DT_d:
		  e.v.dvalue = strtod( e.svalue.c_str(),NULL );
		  break;
		}
		m_events.push_back(e);
	      } while( in.good() );
	      std::sort( m_events.begin(), m_events.end(), SortPredicate );
#ifndef NDEBUG
	      std::cout << "***** Total number of events in XML = " << m_events.size() << std::endl;
#endif
	      do {
		in.getline( b, 512 );	    
		xml_data+=b;
	      } while ( in.good() );
	  }
	  catch ( ... ) {
	    std::cerr << "Could not parse timing file " << filename << std::endl;
	  }

	  m_xml = ezxml_parse_str( (char*)xml_data.c_str(), xml_data.length() );
	  if (!m_xml) {
	    std::string err =  "Could not parse the time file " + filename;
	    throw err;
	  }
	  // Descriptor node
	  m_desc_xml = ezxml_child( m_xml, "Descriptors");
	  m_owner_xml = ezxml_child( m_xml, "Owners");
	  m_event_xml = ezxml_child( m_xml, "Events");
	  if ( m_desc_xml==0 || m_owner_xml==0 ) {
	    std::string err =  "Could not parse the time file " + filename;
	    err += " Bad format";
	    throw err;
	  }
	  parseDescriptors();
	  parseOwners();
	}
	~XMLReader() {
	  ezxml_free(m_xml);
	}
	struct Event {
	  OCPI::Time::Emit::EventQEntry hdr;
	  OCPI::Time::SValue            v;
	  std::string                   svalue;
	};
	struct Description {
	  EventId id;
	  OCPI::Time::Emit::EventType etype;
	  OCPI::Time::Emit::DataType  dtype;
	  std::string desc;
	  uint32_t    width;
	};

	// The Owner is the source of an emiited event
	struct Owner {
	  OwnerId id;
	  std::string name;
	  OwnerId parentIndex;
	  std::string postfix;
	};
	std::vector<Event> & getEvents(){return m_events;}
	std::vector<Description> & getDescriptions(){return m_desc;}

	Description & getDescription( unsigned id ) {
	  ocpiAssert(id < m_desc.size() );
	  return m_desc[id];
	}
	std::vector<Owner> & getOwners(){return m_owners;}
	Owner & getOwner( unsigned owner ) {
	  ocpiAssert( owner < m_owners.size() );
	  return m_owners[owner];
	}
	std::string & ownerString( unsigned id ) {
	  ocpiAssert(id < m_owners.size() );
	  return m_owners[id].name;
	}
	std::string  ownersString( unsigned id ) {
	  ocpiAssert(id < m_owners.size() );
	  std::string s;
	  auto pi= m_owners[id].parentIndex;
	  while ( pi > 0 ) {
	    s += ownerString(pi);
	    s += ":";	    
	    pi = m_owners[pi].parentIndex;
	  }	  
	  s+= m_owners[id].name;
	  return s;
	}
	std::string & descString( unsigned id ) {
	  ocpiAssert(id < m_desc.size() );
	  return m_desc[id].desc;
	}
	OCPI::Time::Emit::EventType 
	  getEventType( Event & e ) 
	  {
	    ocpiAssert( e.hdr.eid < m_desc.size() );
	    return m_desc[e.hdr.eid].etype;
	  }

	bool eventProducedBy( unsigned event, unsigned owner )
	{
	  std::vector<Event>::iterator it;
	  for ( it=m_events.begin(); it!=m_events.end(); it++) {
	    if ( ((*it).hdr.eid == event) && ((*it).hdr.owner == owner )) {
	      return true;
	    }
	  }
	  return false;
	}

      private:
	std::vector<Description> m_desc;
	static bool SortPredicateDesc( const Description& d1, const Description& d2 )
	  {
	    return d1.id < d2.id;
	  }
	void parseDescriptors() {
	  for (ezxml_t x = ezxml_cchild(m_desc_xml, "Class"); x; x = ezxml_cnext(x)) {
	    Event e;
#ifndef NDEBUG
	    std::cout << ezxml_cattr(x,"id") << " " << ezxml_cattr(x,"description") <<  std::endl;
#endif
	    Description d;
	    d.id =  (OwnerId)atoi( ezxml_cattr(x,"id") );
	    d.width = (unsigned)atoi( ezxml_cattr(x,"width") );
	    d.desc =   ezxml_cattr(x,"description");
	    OCPI::Time::Emit::EventType etype = (OCPI::Time::Emit::EventType)atoi( ezxml_cattr(x,"etype") );	    
	    switch( etype ) {
	    case OCPI::Time::Emit::Transient:
	    case OCPI::Time::Emit::State:
	    case OCPI::Time::Emit::Value:
	      d.etype = etype;
	      break;
	    default:
	      ocpiAssert("Bad type found in data"==0);
	    };
	    d.dtype = (OCPI::Time::Emit::DataType)atoi( ezxml_cattr(x,"dtype") );
	    m_desc.push_back(d);
	  }
	  std::sort( m_desc.begin(), m_desc.end(), SortPredicateDesc );
	}
	std::vector<Owner> m_owners;
	static bool SortPredicateOwners( const Owner& o1, const Owner& o2 )
	  {
	    return o1.id < o2.id;
	  }
	void parseOwners() {
	  for (ezxml_t x = ezxml_cchild(m_owner_xml, "Owner"); x; x = ezxml_cnext(x)) {
	    Event e;
#ifndef NDEBUG
	    std::cout << ezxml_cattr(x,"id") << " " << ezxml_cattr(x,"name") << ezxml_cattr(x,"parent") << 
	      std::endl;
#endif
	    Owner o;
	    o.id =  (OwnerId)atoi( ezxml_cattr(x,"id") );
	    o.name =   ezxml_cattr(x,"name");
	    o.parentIndex = (OwnerId)atoi( ezxml_cattr(x,"parent") );
	    m_owners.push_back(o);
	  }
	  std::sort( m_owners.begin(), m_owners.end(), SortPredicateOwners );
	}  
	static bool SortPredicate( const Event& e1, const Event& e2 )
	  {
	    return e1.hdr.time_ticks < e2.hdr.time_ticks;
	  }
	std::vector<Event> m_events;
	void  parseEvents() {
	  for (ezxml_t x = ezxml_cchild(m_event_xml, "Event"); x; x = ezxml_cnext(x)) {
	    Event e;

#ifndef NDEBUG
	    std::cout << ezxml_cattr(x,"id") << " " << ezxml_cattr(x,"owner") << " " << ezxml_cattr(x,"time") << " " << ezxml_cattr(x,"type") << " " 
		      << ezxml_cattr(x,"value") << " " << std::endl;
#endif

	    sscanf( ezxml_cattr(x,"time"), "%llu", (unsigned long long*) &e.hdr.time_ticks);
	    e.hdr.eid = (EventId)atoi( ezxml_cattr(x,"id") );
	    e.hdr.owner = (OwnerId)atoi( ezxml_cattr(x,"owner") );
	    e.svalue = ezxml_cattr(x,"value");
	    if ( strcmp( ezxml_cattr(x,"type"), "Long") == 0 ) {
	      sscanf( e.svalue.c_str(), "%lld", (long long*)&e.v.ivalue);
	    }
	    else  if ( strcmp( ezxml_cattr(x,"type"), "ULong") == 0 ) {
	      sscanf( e.svalue.c_str(), "%llu", (unsigned long long*)&e.v.uvalue);
	    }
	    else  if ( strcmp( ezxml_cattr(x,"type"), "char") == 0 ) {
	      sscanf( e.svalue.c_str(), "%s", e.v.cvalue);
	    }
	    else  if ( strcmp( ezxml_cattr(x,"type"), "Double") == 0 ) {
	      sscanf( e.svalue.c_str(), "%lf", &e.v.dvalue);
	    }
	    m_events.push_back(e);
	  }
	  std::sort( m_events.begin(), m_events.end(), SortPredicate );

#ifndef NDEBUG
	  std::cout << "***** Total number of events in XML = " << m_events.size() << std::endl;
#endif

	}
      };

      // Comma Separated Values formatter
      class CSVWriter {
      private:
	XMLReader & m_xml_reader;
	bool m_smart;
	int  m_line;
	
      public:
	CSVWriter( XMLReader & xml_data, bool smart)  
	  :m_xml_reader(xml_data),m_smart(smart),m_line(1)
	  {       
	    // Empty
	  }  
	  void formatDumpToStreamRaw( std::ostream& out )
	  {
	    std::vector<XMLReader::Event>::iterator it;
	    for ( it=m_xml_reader.getEvents().begin(); it!=m_xml_reader.getEvents().end(); it++ ) {
	      out << (*it).hdr.eid << "," << (*it).hdr.time_ticks << "," << m_xml_reader.getDescription((*it).hdr.eid).width << "," <<
		(*it).svalue << "," <<	m_xml_reader.ownersString( (*it).hdr.owner ) << "," << 
		"\"" << m_xml_reader.descString( (*it).hdr.eid ) << "\"" << std::endl;
	    }
	  }

	  void formatStateEvent(  std::ostream& out, std::string & eventStr, std::string & owner ) {
	    std::vector<XMLReader::Event>::iterator it;
	    XMLReader::Event * e=NULL;
	    int count=0;
	    uint64_t t,
	      maxt=0,
	      mint = UINT64_MAX;

	    for ( it=m_xml_reader.getEvents().begin(); it!=m_xml_reader.getEvents().end(); it++ ) {
	      // If only a selected id has been chosen
	      if ( m_xml_reader.descString( (*it).hdr.eid ) != eventStr ) {
		continue;
	      }
	      if (  m_xml_reader.ownersString( (*it).hdr.owner ).find( owner ) == std::string::npos ) {
		continue;
	      }
	      count++;
	      if (  m_xml_reader.getDescription((*it).hdr.eid).etype  == OCPI::Time::Emit::State ) {
		if ( e && ( (*it).svalue == "0" ) ) {
		  t = (*it).hdr.time_ticks - e->hdr.time_ticks ; 
		  mint=min(t,mint);
		  maxt=max(t,maxt);
		}
		else {
		  t = 0;
		}
		char ts[128];
		if ( t ) 
		  snprintf(ts,128,"%lld",(long long)t);
		else
		  snprintf(ts,128,"%s","");		  
		    
		out << (*it).hdr.eid << "," << (*it).hdr.time_ticks << "," << m_xml_reader.getDescription((*it).hdr.eid).width << "," <<
		  (*it).svalue << "," <<	m_xml_reader.ownersString( (*it).hdr.owner ) << "," << 
		  "\"" << m_xml_reader.descString( (*it).hdr.eid ) << "\"" << 
		  "," << ts <<
		  std::endl;
	      }
	      e = &(*it);
	    }
	    if ( count ) {
	      out << "," << "," << "," << "," << "," << "," << std::endl;
	      out << "," << "," << "," << "," << "," << "," << std::endl;
	      out << ",,,,,,," << "\"Average\"," << "=SUM(G" << m_line <<
		"..G" << m_line+count-1 << ")/" << count/2 << std::endl;
	      out << ",,,,,,," << "\"Max\",," << maxt << std::endl;
	      out << ",,,,,,," << "\"Min\",,," << mint << std::endl;
	      out << std::endl << std::endl << std::endl;
	      m_line += count + 8;
	    }
	  }

	  void formatTransientEvent(  std::ostream& out, std::string & eventStr, std::string & owner ) {
	    std::vector<XMLReader::Event>::iterator it;
	    XMLReader::Event * e=NULL;
	    int count=0;
	    uint64_t t,
	      maxt=0,
	      mint = UINT64_MAX;

	    for ( it=m_xml_reader.getEvents().begin(); it!=m_xml_reader.getEvents().end(); it++ ) {
	      // If only a selected id has been chosen
	      if ( m_xml_reader.descString( (*it).hdr.eid ) != eventStr ) {
		continue;
	      }
	      if (  m_xml_reader.ownersString( (*it).hdr.owner ).find( owner ) == std::string::npos ) {
		continue;
	      }
	      count++;
	      if (  m_xml_reader.getDescription((*it).hdr.eid).etype  == OCPI::Time::Emit::Transient ) {

		if ( e && ( (count%2)==0 ) ) {
		  t = (*it).hdr.time_ticks - e->hdr.time_ticks ; 
		  mint=min(t,mint);
		  maxt=max(t,maxt);
		}
		else {
		  t = 0;
		}
		char ts[128];
		if ( t ) 
		  snprintf(ts,128,"%lld",(long long)t);
		else
		  snprintf(ts,128,"%s","");		  
		out << (*it).hdr.eid << "," << (*it).hdr.time_ticks << "," << m_xml_reader.getDescription((*it).hdr.eid).width << "," <<
		  (*it).svalue << "," <<	m_xml_reader.ownersString( (*it).hdr.owner ) << "," << 
		  "\"" << m_xml_reader.descString( (*it).hdr.eid ) << "\"" << 
		  "," << ts  <<
		  std::endl;
	      }
	      e = &(*it);
	    }
	    if ( count ) {
	      out << "," << "," << "," << "," << "," << "," << std::endl;
	      out << "," << "," << "," << "," << "," << "," << std::endl;
	      out << ",,,,,,," << "\"Average\"," << "=SUM(G" << m_line <<
		"..G" << m_line+count-1 << ")/" << count/2 << std::endl;
	      out << ",,,,,,," << "\"Max\",," << maxt << std::endl;
	      out << ",,,,,,," << "\"Min\",,," << mint << std::endl;
	      out << std::endl << std::endl << std::endl;
	      m_line += count + 8;
	    }
	  }

	  void smartFormatEvents(  std::ostream& out )
	  {
	    std::vector<XMLReader::Description>::iterator it;

	    // Add Header
	    out << "Event ID, Time nS, Width, Value, Owner, Desc, DetaT,,AverageT, MaxT, MinT" << std::endl; m_line++;
	    out << std::endl; m_line++;

	    //  output all of the state events
	    for ( it=m_xml_reader.getDescriptions().begin(); it!=m_xml_reader.getDescriptions().end(); it++ ) {	    
	      if ( (*it).etype == OCPI::Time::Emit::State ) {
		
		// Organize the state data by owner
		for ( unsigned id=0; id<m_xml_reader.getOwners().size(); id++ ) { 
		  std::string owner = m_xml_reader.ownersString( id );
		  formatStateEvent( out, (*it).desc, owner );
		}
	      }
	    }


	    //  output all of the transient events
	    for ( it=m_xml_reader.getDescriptions().begin(); it!=m_xml_reader.getDescriptions().end(); it++ ) {	    
	      if ( (*it).etype == OCPI::Time::Emit::Transient ) {
		
		// Organize the state data by owner
		for ( unsigned id=0; id<m_xml_reader.getOwners().size(); id++ ) { 
		  std::string owner = m_xml_reader.ownersString( id );
		  formatTransientEvent( out, (*it).desc, owner );
		}
	      }
	    }

	    	       
	       


	    
	    


	  }


	  void formatDumpToStreamFormatted( std::ostream& out )
	  {
	    std::string tstr = "Worker Run";
	    std::string owner = "tx_fir_r";
	    if ( m_smart ) {
	      smartFormatEvents(out);
	    }
	    else {
	      formatDumpToStreamRaw(out);
	    }
	  }
      };

      inline std::ostream &
	operator<< (std::ostream& out, CSVWriter& t ) {
	t.formatDumpToStreamFormatted(out);
	return out;
      }


      // VCD output class
      class VCDWriter {
      private:

	XMLReader & m_xml_reader;

	struct EventInstance {
	  OCPI::Time::Emit::OwnerId     owner;
	  OCPI::Time::Emit::EventId     id;
	  std::string       sym;
	  EventInstance(OCPI::Time::Emit::OwnerId     o,
			OCPI::Time::Emit::EventId     i,
			std::string       s)
	    :owner(0),id(i),sym(s){( void ) o;}
	};

	struct ecmp {
	  bool operator()(const int e1, const  int e2) const
	  {
	    return e1 < e2;
	  }
	};

#define SYMSTART 33
#define SYMEND   90
#define SYMLEN (SYMEND-SYMSTART)
	
	std::string itos(unsigned n, char * digits ) {
	  char s[16];
	  unsigned base = SYMLEN;
	  unsigned i=0;
	  do {      
	    s[i++] = digits[n % base]; 
	  } while ((n /= base) > 0);   
	  s[i] = '\0';

	  //std::cerr << "ITOS returning " << s << std::endl;

	  return std::string( s );
	}


	  void getVCDVarSyms( std::map<int,std::string,ecmp> & varsyms )
	  {
	    unsigned int n;	    
	    char digits[SYMLEN];
	    for( int u=0; u<SYMLEN; u++)digits[u]=static_cast<char>(u+SYMSTART);
	    n = SYMLEN+1;
	    std::vector<XMLReader::Description>::iterator it;
	    for ( it=m_xml_reader.getDescriptions().begin(); it!=m_xml_reader.getDescriptions().end(); it++ ) {
	      varsyms[(*it).id] = itos( n++, digits );
#ifndef NDEBUG
	      std::cerr << "id = " << (*it).id << " sym = " << varsyms[(*it).id] << std::endl;
#endif
	    }
	  }

      
	  void dumpVCDScope( std::ostream& out, XMLReader::Owner & owner,
			     std::map< int, std::string, ecmp > & varsyms,
			     std::vector<EventInstance> & allEis )
	  {
	    std::string pname( owner.name );
	    std::replace(pname.begin(),pname.end(),' ','_');
	    out << "$scope module " << pname.c_str() << " $end" << std::endl; 

#define EMIT_POSTFIX_REQUIRED
#ifdef EMIT_POSTFIX_REQUIRED

	    char digits[SYMLEN];
	    for( int u=0; u<SYMLEN; u++)digits[u]=static_cast<char>(u+SYMSTART);
	    for( int n=0; n<=owner.id/SYMLEN; n++) {
	      owner.postfix = itos( owner.id, digits );
	      //	      std::cerr << "Postfix = " << owner.postfix;
	    }
#endif

	    // Dump the variables for this object
	    std::vector<XMLReader::Description>::iterator it;
	    for ( it=m_xml_reader.getDescriptions().begin();
		  it!=m_xml_reader.getDescriptions().end();  it++ ) {
	      if ( m_xml_reader.eventProducedBy( (*it).id, owner.id ) ) {
		std::string tn((*it).desc);
		std::replace(tn.begin(),tn.end(),' ','_');
		std::string type;
		type = ((*it).width > 1) ? "integer" : "reg";

		out << "$var " << type << " " << (*it).width << " " << varsyms[(*it).id] << owner.postfix<<
		  " " <<  tn << " $end" << std::endl;
		std::string sym = varsyms[(*it).id] + owner.postfix;

		allEis.push_back( EventInstance(owner.id,(*it).id,sym) );
	      }
	    }
    
	    // Now dump our children
	    unsigned int id;
	    int mod=0;
	    for ( id=0; id<m_xml_reader.getOwners().size(); id++ ) {
	      if ( (mod++%10000) == 0 ) std::cerr << "." << std::flush;
	      if ( m_xml_reader.getOwner(id).parentIndex == owner.id ) {
		dumpVCDScope( out, m_xml_reader.getOwner(id), varsyms, allEis );
	      }
	    }
	    out << "$upscope $end" << std::endl;
	  }


	struct TimeLineData {
	  OCPI::Time::Emit::Time t;
	  std::string                time;
	  std::string                values;
	};
	static bool SortPredicate( const TimeLineData& tl1, const TimeLineData& tl2 )
	  {
	    return tl1.t < tl2.t;
	  }

      public:

	VCDWriter( XMLReader & reader ) 
	  :m_xml_reader(reader){}

	std::ostream& formatDumpToStream( std::ostream& out )
	  {
	    std::vector<XMLReader::Owner>::iterator hit;
	    std::map< int, std::string, ecmp > varsyms;
	    std::vector<EventInstance> allEis;
	    OCPI::Time::Emit::OwnerId owner;
	    int mod=0;

	    std::cerr << "This can take several minutes depending on the event count" << std::endl;

	    // Date
	    char date[80];
	    const char *fmt="%A, %B %d %Y %X";
	    struct tm* pmt;
	    time_t     raw_time;
	    time ( &raw_time );
	    pmt = gmtime( &raw_time );
	    strftime(date,80,fmt,pmt);
	    out << "$date" << std::endl;
	    out << "         " << date << std::endl;
	    out << "$end" << std::endl;  

	    // Version
	    out << "$version" << std::endl;  
	    out << "            OCPI VCD Software Event Dumper V1.0" << std::endl;
	    out << "$end" << std::endl;  
  
	    // Timescale
	    out << "$timescale" << std::endl;    
	    out << "          1 ns" << std::endl;
	    out << "$end" << std::endl;

	    // Now for the class definitions  
	    out << "$scope module Software $end" << std::endl;    

	    // For each top level object generate its $var defs and then dump its children
	    getVCDVarSyms( varsyms );

	    std::cerr << "." << std::flush;

	    // Here we output each scoped owner class and then define which event each class will emit
	    for ( owner=0, hit=m_xml_reader.getOwners().begin();
		  hit!=m_xml_reader.getOwners().end(); hit++,owner++ ) {
	      if ( (*hit).parentIndex == OCPI::Time::Emit::NoOwner ) {
		dumpVCDScope( out, m_xml_reader.getOwner(owner), varsyms, allEis );
	      }
	      if ( (mod++%1000) == 0 ) std::cerr << "." << std::flush;
	    }

	    std::cerr << "." << std::flush;

	    out << "$upscope $end" << std::endl;
	    out << "$enddefinitions $end" << std::endl;

	    std::vector<EventInstance>::iterator eisit;
	    // Dump out the initial values
	    out << "$dumpvars" << std::endl;
	    for ( eisit=allEis.begin(); eisit!=allEis.end(); eisit++ ) {
	      if ( m_xml_reader.getDescription( (*eisit).id ).width > 1 ) {
		out << "b0 " << (*eisit).sym.c_str() << std::endl;
	      }
	      else {
		out << "0" << (*eisit).sym.c_str() << std::endl;
	      }
	    }
	    out << "$end" << std::endl;  
	    std::cerr << "." << std::flush;


	    // Now emit the events
	    OCPI::Time::Emit::Time start_time = 0;
	    std::vector<TimeLineData> tldv;
	    std::vector<XMLReader::Event>::iterator it;
	    for ( it=m_xml_reader.getEvents().begin(); it!=m_xml_reader.getEvents().end(); it++) {
	      XMLReader::Owner& xowner = m_xml_reader.getOwner((*it).hdr.owner);
	      if ( start_time == 0 ) {
		start_time = (*it).hdr.time_ticks;
	      }
	      TimeLineData tld;

	      if ( (mod++%10000) == 0 ) std::cerr << "." << std::flush;

	      // event time
	      char tbuf[256];

#define EMIT_RELATIVE_TIME
#ifdef EMIT_RELATIVE_TIME
	      OCPI::Time::Emit::Time ctime = (*it).hdr.time_ticks-start_time;
#else
	      OCPI::Time::Emit::Time ctime = (*it).hdr.time_ticks;
#endif
	      snprintf(tbuf,256,"\n#%lld\n",(long long)ctime);
	      tld.t = ctime;
	      tld.time = tbuf;

	      switch ( m_xml_reader.getEventType( (*it) )  ) {

	      case OCPI::Time::Emit::Transient:
		{
		  tld.values += "1" + varsyms[(*it).hdr.eid] + xowner.postfix.c_str() + "\n";
		  snprintf(tbuf,256,"#%lld\n",(long long)(ctime+1));
		  tld.values += tbuf;
		  tld.values += "0" + varsyms[(*it).hdr.eid] + xowner.postfix.c_str() + "\n";
		}
		break;
	      case OCPI::Time::Emit::State:
		{
		  snprintf(tbuf,256,"%d",((*it).v.uvalue == 0) ? 0 : 1);
		  tld.values += tbuf;
		    tld.values += varsyms[(*it).hdr.eid] + xowner.postfix.c_str() + "\n";
		}
		break;
	      case OCPI::Time::Emit::Value:
		{
		  tld.values += "b";
		  XMLReader::Description & emap = m_xml_reader.getDescription( (*it).hdr.eid ) ;
		  switch ( emap.dtype ) {
		  case OCPI::Time::Emit::DT_u:
		  case OCPI::Time::Emit::DT_i:
		  case OCPI::Time::Emit::DT_d:
		    {
		      uint32_t* ui = reinterpret_cast<uint32_t*>(&(*it).v.uvalue);
		      ui++;
		      for (int n=0; n<2; n++ ) {
			for ( uint32_t i= (1u<<31); i>=(uint32_t)1; ) {
			  tld.values += ((i & *ui)==i) ? "1" : "0";
			  i = i>>1;
			}
			ui--;
		      }
		      tld.values += " ";
		      tld.values +=  varsyms[(*it).hdr.eid] + xowner.postfix.c_str() + "\n";
		    }
		  case OCPI::Time::Emit::DT_c:  // Not handled in GTKwave
		    break;
		  }
		}
	      }
	      tldv.push_back(tld);
	    }
	    std::sort( tldv.begin(), tldv.end(), SortPredicate );

#ifndef NDEBUG
	    printf("***** size = %d \n", (int)tldv.size() );
#endif

#ifdef NO_TIME_DUPS
	    unsigned int n;
	    if ( tldv.size() ) {
	      for(n=0; n<tldv.size()-1; n++) {  
		if ( tldv[n].time_ticks == tldv[n+1].time_ticks ) {
		  tldv[n].values += "\n";
		  tldv[n].values += tldv[n+1].values;
		  tldv.erase(tldv.begin()+n+1);
		  n=0;
		}
	      }
	    }
#endif

	    for(unsigned int n=0; n<tldv.size(); n++ ) {
	      out << tldv[n].time;
	      out << tldv[n].values;
	    }

	    // End of file
	    out << std::endl << "$dumpoff" << std::endl;
	    /*
	    for ( eisit=allEis.begin(); eisit!=allEis.end(); eisit++ ) {
	      out << "x" << (*eisit).sym.c_str() << std::endl;
	    }
	    */
	    out << "$end" << std::endl;  
	    return out;
	    }


	  };


      inline std::ostream &
	operator << (std::ostream& out, VCDWriter& t ) {
	t.formatDumpToStream(out);
	return out;
      }

#endif // OCPI_TIME_EMIT_SUPPORT

    }
  }
}

#endif
