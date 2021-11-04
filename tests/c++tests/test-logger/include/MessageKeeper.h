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

#ifndef OCPILOGGERTESTMESSAGEKEEPER_H__
#define OCPILOGGERTESTMESSAGEKEEPER_H__

#include "UtilLogger.hh"
#include <string>

/*
 * ----------------------------------------------------------------------
 * Implementation of the Logger interface that makes the last log
 * message available. Not thread safe.
 * ----------------------------------------------------------------------
 */

class MessageKeeperOutput : public OCPI::Logger::Logger {
 public:
  class MessageKeeperOutputBuf : public LogBuf {
  public:
    MessageKeeperOutputBuf ();
    ~MessageKeeperOutputBuf ();

    void setLogLevel (unsigned short);
    void setProducerId (const char *);
    void setProducerName (const char *);

    unsigned short getLogLevel () const;
    std::string getProducerId () const;
    std::string getProducerName () const;
    std::string getMessage () const;

  protected:
    int sync ();
    int_type overflow (int_type = std::streambuf::traits_type::eof());
    std::streamsize xsputn (const char *, std::streamsize);

  protected:
    bool m_first;
    unsigned short m_logLevel;
    std::string m_producerId;
    std::string m_producerName;
    std::string m_logMessage;
  };

 public:
  MessageKeeperOutput ();
  ~MessageKeeperOutput ();

  unsigned short getLogLevel () const;
  std::string getProducerId () const;
  std::string getProducerName () const;
  std::string getMessage () const;

 protected:
  MessageKeeperOutputBuf m_obuf;
};

#endif
