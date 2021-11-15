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

#ifndef OCPIUTILSTATICMEMFS_H__
#define OCPIUTILSTATICMEMFS_H__

/**
 * \file
 * \brief Vfs implementation using in-memory files.
 *
 * Revision History:
 *
 *     04/19/2005 - Frank Pilhofer
 *                  Initial version.
 */

#include "Vfs.hh"
#include "VfsStaticMemFile.hh"
#include "OsRWLock.hh"
#include <iostream>
#include <map>

namespace OCPI {
  namespace VFS {
    /**
     * \namespace OCPI::VFS::MemFs
     * \brief Management of in-memory files.
     *
     * The off-line tool <tt>strfile.tcl</tt> allows "compiling"
     * a file into C++ code, so that it can be accessed via a
     * StaticMemFile object.
     * 
     * Example:
     *
     * The following command creates the C++ file <tt>DeploymentXSD.cxx</tt>
     * from the data in the file <tt>Deployment.xsd</tt>.  The C++ file will
     * define a OCPI::VFS::MemFs::MemFileChunk array named <tt>Deployment</tt>
     * in the <tt>RepositoryManager::XSD</tt> namespace, and a variable
     * <tt>Deployment_mtime</tt> of type <tt>std::time_t</tt> with the value
     * of the data file's last modification timestamp.
     *
     * \code
     *   strfile.tcl --var Deployment --ns RepositoryManager::XSD \
     *       --text --chunksize 2047 -o DeploymentXSD.cxx Deployment.xsd
     * \endcode
     *
     * The file can then be used in C++ code as follows:
     *
     * \code
     * #include "VfsMemFileChunk.hh"
     * #include "VfsStaticMemFs.hh"
     * namespace RepositoryManager {
     *   namespace XSD {
     *     extern const ::OCPI::Util::MemFs::MemFileChunk Deployment[];
     *     extern std::time_t Deployment_mtime;
     *   }
     * }
     *
     * OCPI::Util::MemFs::StaticMemFile
     *     DeploymentXSD (RepositoryManager::Deployment,
     *                    RepositoryManager::Deployment_mtime);
     * \endcode
     *
     * The <tt>DeploymentXSD</tt> instance can then be mounted into a
     * OCPI::Util::MemFs::StaticMemFs file system:
     *
     * \code
     *   OCPI::Util::MemFs::StaticMemFs schemaFiles;
     *   schemaFiles.mount ("/Deployment.xsd", &DeploymentXSD, false);
     * \endcode
     *
     * Now, when the file <tt>Deployment.xsd</tt> is opened, the contents
     * of the file can be read.
     *
     * Note that all this MemFileChunk business is necessary because some
     * compilers have a ridiculously low limits for the maximum size of a
     * character array.  ISO 9899:1999 defines "4095 characters in a
     * character string literal (after concatenation)" as a minimally
     * acceptable implementation limit, and some compilers do not even
     * support that.
     */

    namespace MemFs {

      /**
       * \brief Vfs implementation using in-memory files.
       *
       * StaticMemFs represents a collection of in-memory files, which can
       * be browsed and read using the Vfs interface.
       *
       * Files are represented by instances of type
       * OCPI::Util::MemFs::StaticMemFile.
       *
       * This is a read-only file system.
       */

      class StaticMemFs : public OCPI::VFS::Vfs {
      public:
        /**
         * Constructor.
         *
         * The file system is initially empty.
         */

        StaticMemFs ();

        /**
         * Destructor.
         */

        ~StaticMemFs ();

        /**
         * Add a file to the file system.
         *
         * \param[in] name  The name of the file in the file system.
         * \param[in] file  The in-memory file.
         * \param[in] adopt Whether to "adopt" the file. If true,
         *                  \a file will be deleted in the destructor.
         */

        void mount (const std::string & name,
                    OCPI::VFS::MemFs::StaticMemFile * file,
                    bool adopt = false);

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

        void rmdir (const std::string &);

        /*
         * Directory Listing
         */

#if 0 
        OCPI::VFS::Iterator * list (const std::string & dir,
                                         const std::string & pattern = "*");
#endif
        void closeIterator (OCPI::VFS::Iterator *);

        /*
         * File Information
         */

        bool exists (const std::string &, bool * = 0);

        unsigned long long size (const std::string &);

        std::time_t lastModified (const std::string &);

        /*
         * File I/O
         */

        std::iostream * open (const std::string &, std::ios_base::openmode = std::ios_base::in | std::ios_base::out);

        std::istream * openReadonly (const std::string &, std::ios_base::openmode = std::ios_base::in);

        std::ostream * openWriteonly (const std::string &, std::ios_base::openmode = std::ios_base::out | std::ios_base::trunc);

        void close (std::ios *);

        /*
         * File System Operations
         */

        void remove (const std::string &);

        //@}

        /** \cond */

      protected:
        std::string absoluteNameLocked (const std::string &) const;
        static void testFilenameForValidity (const std::string &);

      public:
        struct INode {
          bool adopted;
          StaticMemFile * file;
        };

        typedef std::map<std::string, INode> FileList;

      protected:
        std::string m_cwd;
        std::string m_baseURI;

        FileList m_contents;
        mutable OCPI::OS::RWLock m_lock;

        /** \endcond */

      private:
        /**
         * Not implemented.
         */

        StaticMemFs (const StaticMemFs &);

        /**
         * Not implemented.
         */

        StaticMemFs & operator= (const StaticMemFs &);
      };

    }
  }
}

#endif
