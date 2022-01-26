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

#ifndef OCPIUTILFILEFS_H__
#define OCPIUTILFILEFS_H__

/**
 * \file
 * \brief Vfs implementation based on the local file system.
 *
 * Revision History:
 *
 *     04/19/2005 - Frank Pilhofer
 *                  Initial version.
 *
 */

#include <iostream>
#include <string>
#include <ctime>

#include "OsMutex.hh"

#include "Vfs.hh"

namespace OCPI {
  namespace VFS {
    /**
     * \brief Vfs implementation based on the local file system.
     */
      /**
       * \brief Vfs implementation based on the local file system.
       *
       * This class implements the OCPI::VFS::Vfs file system
       * interface, based on the operating system's idea of a file
       * system.  All operations are delegated to the functions in
       * the OCPI::OS::FileSystem namespace.
       *
       * Two difference with respect to the OCPI::OS::FileSystem functions
       * are that each FileFs instance maintains its own root directory,
       * so that only a subtree is exposed, and that each FileFs instance
       * maintains its own working directory.
       */

      class FileFs : public Vfs {
        void setURI();
      public:
        /**
         * Constructor.
         *
         * \param[in] root The directory that is used as this file system's
         *             root directory.  It will be prepended to all file
         *             names that are accessed by this FileFs instance.
         *             The parameter must be an absolute path name that
         *             identifies an existing directory.  Since ".." is
         *             not a valid path component, only files within the
         *             \a root and its subdirectories will be accessible.
	 *             The default constructor uses the cwd.
         */
        FileFs (const char *root = NULL);

        /**
         * Destructor.
         */

        ~FileFs ();

        /**
         * \name Map to and from file system paths.
         */

        //@{

        /**
         * Convert the name of a file within this file system to a path
         * within the local file system.  Essentially, this prepends the
         * root directory to the file name.  The path name can then be
         * used with the functions in the OCPI::OS::FileSystem namespace.
         *
         * \param[in] name The name of a file within this file system.
         * \return    An absolute path name within the local file system.
         *
         * \throw std::string If name is not a valid file name.
         */

        std::string nameToPath (const std::string & name) const;

        /**
         * Convert a local file system path name to a file name within
         * this file system instance.
         *
         * \param[in] path A path name within the local file system.
         * \return         A file name within this file system.
         *
         * \throw std::string If \a path is not a valid path name, or
         * if it points to a location outside of this file system's
         * root directory.
         */

        std::string pathToName (const std::string & path) const;

        //@}

        /**
         * \name Map to and from native file names.
         */

        //@{

        /**
         * Convert the name of a file within this file system to a file
         * name in native format, i.e., one that can be passed to system
         * calls.  This is equivalent to
         * OCPI::OS::FileSystem::toNativeName (nameToPath(name));
         *
         * \param[in] name A file name within this file system.
         * \return         An absolute file name in "native" format.
         *
         * \throw std::string If name is not a valid file name.
         */

        std::string toNativeName (const std::string & name) const;

        /**
         * Convert a native file name to a file name within this file
         * system. This is equivalent to
         * pathToName (OCPI::OS::FileSystem::fromNativeName (path));
         *
         * \param[in] path A file name in "native" format.
         * \return         A file name within this file system.
         *
         * \throw std::string If path is not a valid native file name,
         * or if it points to a location outside of this file system's
         * root directory.
         */

        std::string fromNativeName (const std::string & path) const;
        
        //@}
        
        /**
         * \name Implementation of the OCPI::VFS::Vfs interface.
         */

        //@{

        /*
         * The operations below implement the Vfs interface. See the Vfs
         * interface for more detail.
         */

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
	OCPI::VFS::Dir &openDir(const std::string&);
#if 0

        OCPI::VFS::Iterator * list (const std::string & dir,
                                         const std::string & pattern = "*");

        void closeIterator (OCPI::VFS::Iterator *);
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

        void move (const std::string &, Vfs *, const std::string &);

        void rename (const std::string &, const std::string &);

        void remove (const std::string &);

        std::string nativeFilename (const std::string &) const;

        //@}

      protected:
        /** \cond */

        static void testFilenameForValidity (const std::string &);

        std::string absoluteNameLocked (const std::string &) const;

      protected:
        std::string m_baseURI;
        std::string m_root;
        std::string m_cwd;
        mutable OCPI::OS::Mutex m_lock;

        /** \endcond */

      private:
        /**
         * Not implemented.
         */

        FileFs (const FileFs &);

        /**
         * Not implemented.
         */

        FileFs & operator= (const FileFs &);
      };

  }
}

#endif
