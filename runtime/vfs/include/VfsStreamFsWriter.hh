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

// -*- c++ -*-

#ifndef OCPIUTILSTREAMFSWRITER_H__
#define OCPIUTILSTREAMFSWRITER_H__

/**
 * \file
 * \brief Aggregate a set of files into a single data stream.
 *
 * Revision History:
 *
 *     05/27/2005 - Frank Pilhofer
 *                  Initial version.
 *
 */

#include <iostream>
#include <string>
#include <ctime>
#include <map>
#include "OsMutex.hh"
#include "Vfs.hh"

namespace OCPI {
  namespace VFS {
    /**
     * \brief Aggregate a set of files into a single data stream.
     *
     * The motivation is to write and read sets of files in bulk,
     * without having to go out to a "real" file system, where
     * opening and closing files might be expensive.
     */

    namespace StreamFs {

      /**
       * \brief Aggregate a set of files into a single data stream.
       *
       * Stores multiple files, sequentially and linearly, into the same
       * data stream, resulting in a serialized "FileSystem" within the
       * stream.  Only one file can be open for writing at any time.  All
       * files must be written in one session.  Files can not be read,
       * removed or modified.
       *
       * The class is single-threaded only, not reentrant.
       *
       * The motivation is to write and read sets of files in bulk,
       * without having to go out to a "real" file system, where
       * opening and closing files might be expensive.
       *
       * This functionality is similar in spirit to the "tar" utility.
       * One difference is that "tar" requires a priori knowledge of
       * the file sizes, while this class does not.
       */

      class StreamFsWriter : public OCPI::VFS::Vfs {
      public:
        /**
         * Constructor.
         *
         * Must call open().
         */

        StreamFsWriter ();

        /**
         * Constructor.
         *
         * Calls #openFs (\a stream).
         *
         * \param[in] stream  The stream to write files to.
         *
         * \pre \a stream shall be open for writing in binary mode.
         * \post \a stream shall not be manipulated directly throughout
         * the lifetime of this object.
         */

        StreamFsWriter (std::ostream * stream);

        /**
         * Constructor.
         *
         * Calls #openFs (\a fs, \a name).
         *
         * \param[in] fs    A file system instance that will contain the
         *                  file.
         * \param[in] name  The name of the file in the file system to
         *                  write to.
         *
         * \throw std::string If the file can not be opened for writing.
         */

        StreamFsWriter (OCPI::VFS::Vfs * fs, const std::string & name);

        /**
         * Destructor.
         *
         * Calls closeFs(), ignoring any errors.
         */

        ~StreamFsWriter ();

        /**
         * \name Opening and closing stream file systems.
         */

        //@{

        /**
         * Sets the stream to write the file system contents to.
         *
         * \param[in] stream  The stream to write files to.
         *
         * \pre \a stream shall be open for writing in binary mode.
         * \post \a stream shall not be manipulated outside of this object
         * throughout the lifetime of this StreamFsWriter instance.
         */

        void openFs (std::ostream * stream);

        /**
         * Opens a file to write the file system contents to.
         *
         * \param[in] fs    A file system instance that will contain the
         *                  file.
         * \param[in] name  The name of the file in the file system to
         *                  write to.
         *
         * \throw std::string If the file can not be opened for writing.
         */

        void openFs (OCPI::VFS::Vfs * fs, const std::string & name);

        /**
         * Closes the file system.
         *
         * \throw std::string Write error.
         * \throw std::string Propagated from OCPI::VFS::Vfs::close().
         *
         * \pre No files are open.
         * \note This is required to write the table of contents.
         */

        void closeFs ();

        //@}

        /**
         * \name Implementation of the OCPI::VFS::Vfs interface.
         */

        //@{

        /*
         * File Name URI Mapping
         */

        std::string baseURI () const;

        std::string nameToURI (const std::string &) const;

        std::string URIToName (const std::string &) const;

        /*
         * Directory Management
         */

        std::string cwd () const;

        void cd (const std::string &);

        void mkdir (const std::string &);

        /**
         * Not supported by this file system.
         */

        void rmdir (const std::string &);

        /*
         * Directory Listing
         */
        
#if 0
        /**
         * Not supported by this file system.
         */

        OCPI::VFS::Iterator * list (const std::string & dir,
                                         const std::string & pattern = "*");

        /**
         * Not supported by this file system.
         */

        void closeIterator (OCPI::VFS::Iterator *);
#endif
        /*
         * File Information
         */

        /**
         * Not supported by this file system.
         */

        bool exists (const std::string &, bool * = 0);

        /**
         * Not supported by this file system.
         */

        unsigned long long size (const std::string &);

        /**
         * Not supported by this file system.
         */

        std::time_t lastModified (const std::string &);

        /*
         * File I/O
         */

        /**
         * Not supported by this file system.
         */

        std::iostream * open (const std::string &, std::ios_base::openmode = std::ios_base::in | std::ios_base::out);

        /**
         * Not supported by this file system.
         */

        std::istream * openReadonly (const std::string &, std::ios_base::openmode = std::ios_base::in);

        std::ostream * openWriteonly (const std::string &, std::ios_base::openmode = std::ios_base::out | std::ios_base::trunc);

        void close (std::ios *);

        /*
         * File System Operations. Not implemented.
         */

        /**
         * Not implemented by this file system.
         */

        void remove (const std::string &);

        //@}

      protected:
        /** \cond */

        void dumpTOC ();

        std::string absoluteNameLocked (const std::string &) const;

      public:
        struct Node {
          unsigned long long pos;
          unsigned long long size;
          std::time_t lastModified;
        };

        typedef std::map<std::string, Node> TOC;

      protected:
        Vfs * m_fs;
        std::string m_name;
        std::ostream * m_stream;
        unsigned long long m_pos;

        TOC m_toc;
        std::string m_cwd;
        std::string m_baseURI;

        unsigned long m_openFiles;
        mutable OCPI::OS::Mutex m_mutex;
        /** \endcond */

      private:
        /**
         * Not implemented.
         */

        StreamFsWriter (const StreamFsWriter &);

        /**
         * Not implemented.
         */

        StreamFsWriter & operator= (const StreamFsWriter &);
      };

    }
  }
}

#endif
