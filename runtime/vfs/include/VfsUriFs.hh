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

#ifndef OCPIUTILURIFS_H__
#define OCPIUTILURIFS_H__

/**
 * \file
 * \brief Delegate file access to mounted file systems, using URIs as file names.
 *
 * Revision History:
 *
 *     04/19/2005 - Frank Pilhofer
 *                  Initial version.
 *
 */

#include "Vfs.hh"
#include "OsRWLock.hh"
#include <iostream>
#include <string>
#include <ctime>
#include <vector>
#include <map>

namespace OCPI {
    namespace VFS {

      /**
       * \brief Delegate file access to mounted file systems, using URIs as file names.
       *
       * This class implements the OCPI::VFS::Vfs interface.
       *
       * URIs are directly used as file names, so that URI path components
       * make up the file name's path components, e.g.,
       * "/http/www.mc.com/index.html".
       *
       * All access is delegated to a set of "mounted" secondary Vfs
       * instances, based on whether a secondary Vfs supports the URI,
       * as determined by its URIToName() operation.
       */

      class UriFs : public OCPI::VFS::Vfs {
      public:
        /**
         * Constructor.
         *
         * Initializes the UriFs instance with an empty set of delegatees.
         */

        UriFs ();

        /**
         * Destructor.
         *
         * Deletes all adopted delegatees.
         */

        ~UriFs ();

        /**
         * Mounts a delegatee.
         *
         * File access is delegated to \a delegatee if the
         * URIToName() operation confirms that the file is located in
         * the \a delegatee's file system.
         *
         * \param[in] delegatee A secondary Vfs instance to delegate
         *                      accesses to, if the delegatee covers
         *                      the namespace that a file is in. 
         * \param[in] adopt     Whether the delegatee is to be adopted.
         *                      If true, the delegatee is deleted when
         *                      unmounted or by the destructor.
         */

        void mount (OCPI::VFS::Vfs * delegatee, bool adopt = false);

        /**
         * Unmount a delegatee.
         *
         * If the delegatee was adopted during mount(), it is deleted.
         *
         * \param[in] delegatee The Vfs instance to unmount.
         */

        void unmount (OCPI::VFS::Vfs * delegatee);

        /**
         * \name Implementation of the OCPI::VFS::Vfs interface.
         *
         * These operations are implemented by UriFs, delegating to
         * the appropriate delegatee.
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
        Iterator * list (const std::string & dir,
                         const std::string & pattern = "*");

        void closeIterator (Iterator *);
#endif
	OCPI::VFS::Dir &openDir(const std::string&);

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

        void copy (const std::string &, OCPI::VFS::Vfs *, const std::string &);

        void move (const std::string &, OCPI::VFS::Vfs *, const std::string &);

        void remove (const std::string &);

        //@}

      protected:
        /** \cond */
        struct MountPoint {
          bool adopted;
          std::string baseURI;
          OCPI::VFS::Vfs * fs;
        };

        typedef std::vector<MountPoint> MountPoints;
        typedef std::map<OCPI::VFS::Iterator *, OCPI::VFS::Vfs *> OpenIterators;
        typedef std::map<std::ios *, OCPI::VFS::Vfs *> OpenFiles;
    
      protected:
        std::string absoluteNameLocked (const std::string &) const;
        std::string absoluteNameToURI (const std::string &) const;
        OCPI::VFS::Vfs * findFs (const std::string &, std::string &) const;

      protected:
        std::string m_cwd;
        MountPoints m_mountPoints;
        OpenIterators m_openIterators;
        OpenFiles m_openFiles;
        mutable OCPI::OS::RWLock m_lock;

        /** \endcond */

      private:
        /**
         * Not implemented.
         */

        UriFs (const UriFs &);

        /**
         * Not implemented.
         */

        UriFs & operator= (const UriFs &);
      };

    }
}

#endif
