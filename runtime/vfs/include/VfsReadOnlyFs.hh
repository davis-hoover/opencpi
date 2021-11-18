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

#ifndef OCPIUTILREADONLYFS_H__
#define OCPIUTILREADONLYFS_H__

/**
 * \file
 * \brief Denies write access to files in a file system.
 *
 * Revision History:
 *
 *     04/19/2005 - Frank Pilhofer
 *                  Initial version.
 *
 */

#include "VfsFilterFs.hh"

namespace OCPI {
    namespace VFS {

      /**
       * \brief Denies write access to files in a file system.
       *
       * This class implements the OCPI::VFS::Vfs interface.
       *
       * All read access is delegated to a secondary OCPI::VFS::Vfs.
       * Any write access is denied.
       */

      class ReadOnlyFs : public OCPI::VFS::FilterFs {
      public:
        /**
         * Constructor
         *
         * \param[in] delegatee The secondary Vfs instance to delegate all
         *                      read access to.
         */

        ReadOnlyFs (OCPI::VFS::Vfs & delegatee);

        /**
         * Destructor.
         */

        ~ReadOnlyFs ();

      protected:
        /**
         * \name Implementation of the OCPI::VFS::FilterFs interface.
         */

        //@{

        void access (const std::string & name,
                     std::ios_base::openmode mode,
                     bool isDirectory);

        //@}
      };

    }
}

#endif
