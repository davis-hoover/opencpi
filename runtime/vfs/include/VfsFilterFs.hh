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

#ifndef OCPIUTILFILTERFS_H__
#define OCPIUTILFILTERFS_H__

/**
 * \file
 * \brief Filters access to files in a file system.
 *
 * Revision History:
 *
 *     04/19/2005 - Frank Pilhofer
 *                  Initial version.
 *
 */

#include "Vfs.hh"

namespace OCPI {
    namespace VFS {

      /**
       * \brief Filters access to files in a file system.
       *
       * This class implements the OCPI::VFS::Vfs interface.
       *
       * All file access is delegated to a secondary OCPI::VFS::Vfs
       * instance, after passing an "access" check. This can be used to
       * selectively allow or disallow access to certain files.
       *
       * This is an abstract class.  The access() predicate must be
       * implemented in a derived class.
       */

      class FilterFs : public OCPI::VFS::Vfs {
      public:
        /**
         * Constructor.
         *
         * \param[in] delegatee The secondary Vfs instance to delegate all
         *                      file access to, after passing the access
         *                      check.
         */

        FilterFs (OCPI::VFS::Vfs & delegatee);

        /**
         * Destructor.
         */

        ~FilterFs ();

      protected:
        /**
         * The predicate whether to allow or disallow file access.
         * Must be implemented by a derived class.
         *
         * If the operation returns, access is granted, and the file
         * access is delegated to the \a delegatee that was passed to
         * the constructor.
         *
         * This operation shall throw an exception to deny access.
         *
         * \param[in] name The file that a client wishes to access.
         *                 The \a name may be absolute or relative.
         *                 The file may not exist, e.g., when opening
         *                 a file for writing.
         * \param[in] mode Identifies the type of access that is desired,
         *                 such as std::ios_base::in, std::ios_base::out,
         *                 std::ios_base::trunc, or a combination thereof.
         *                 If a file is to be moved, the \a mode parameter
         *                 is set to std::ios_base::in | std::ios_base::trunc;
         *                 if a file or directory is to be removed, the
         *                 \a mode parameter is set to std::ios_base::trunc.
         * \param[in] isDirectory Whether \a name is used as a file or
         *                 directory.
         *
         * \throw std::string To deny access.  This exception is
         * propagated to the caller.
         */

        virtual void access (const std::string & name,
                             std::ios_base::openmode mode,
                             bool isDirectory)
= 0;

      public:
        /**
         * \name Implementation of the OCPI::VFS::Vfs interface.
         *
         * These operations are implemented by FilterFs, delegating to
         * the delegatee after passing the access check.
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

#if 0
        /*
         * Directory Listing
         */

        Iterator * list (const std::string & dir,
                         const std::string & pattern = "*");

        void closeIterator (Iterator *);
#endif
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

        void copy (const std::string &, Vfs *, const std::string &);

        void move (const std::string &, Vfs *, const std::string &);

        void rename (const std::string &, const std::string &);

        void remove (const std::string &);

        //@}

      protected:
        OCPI::VFS::Vfs & m_delegatee;

      private:
        /**
         * Not implemented.
         */

        FilterFs (const FilterFs &);

        /**
         * Not implemented.
         */

        FilterFs & operator= (const FilterFs &);
      };

    }
}

#endif
