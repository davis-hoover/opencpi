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

#ifndef OCPIUTILCDR_H__
#define OCPIUTILCDR_H__

/**
 * \file
 * \brief A small CDR engine.
 *
 * Revision History:
 *
 *     05/24/2005 - Frank Pilhofer
 *                  Initial version.
 *
 */

#include "OsDataTypes.hh"
#include <string>

namespace OCPI {
  namespace Util {
    /**
     * \brief A small CDR engine.
     */

    namespace CDR {

      /**
       * Determine the byteorder of the local system.
       *
       * \return true on little-endian systems, false on big-endian
       *         systems.
       */

      bool nativeByteorder ();

      /**
       * Copy 2 octets in reverse order, thus changing the byteorder.
       *
       * \param[in] pdest The destination.
       * \param[in] psrc  The source.
       *
       * \pre \a pdest and \a psrc must not overlap.
       */

      void copyswap2 (char * pdest, const char * psrc);

      /**
       * Copy 4 octets in reverse order, thus changing the byteorder.
       *
       * \param[in] pdest The destination.
       * \param[in] psrc  The source.
       *
       * \pre \a pdest and \a psrc must not overlap.
       */

      void copyswap4 (char * pdest, const char * psrc);

      /**
       * Copy 8 octets in reverse order, thus changing the byteorder.
       *
       * \param[in] pdest The destination.
       * \param[in] psrc  The source.
       *
       * \pre \a pdest and \a psrc must not overlap.
       */

      void copyswap8 (char * pdest, const char * psrc);

      /**
       * \brief CDR Encoder
       *
       * Marshals data into a binary <em>std::string</em>, following the
       * CDR rules, using the native byteorder.
       */

      class Encoder {
      public:
        /**
         * Constructor.
         */

        Encoder ();

        /**
         * Add padding so that the following data is aligned with respect
         * to the beginning of the stream.
         *
         * \param[in] mod The modulus to align to.
         */

        void align (unsigned long mod);

        /**
         * \name Marshalling data.
         */

        //@{

        /**
         * Marshal a boolean value.
         *
         * \param[in] value A boolean value.
         */

        void putBoolean (bool value);

        /**
         * Marshal an octet value.
         *
         * \param[in] value An octet value.
         */

        void putOctet (unsigned char value);

        /**
         * Marshal a CORBA::UShort value.  Padding is added if necessary.
         *
         * \param[in] value A CORBA::UShort value.
         */

        void putUShort (OCPI::OS::uint16_t value);

        /**
         * Marshal a CORBA::ULong value.  Padding is added if necessary.
         *
         * \param[in] value A CORBA::ULong value.
         */

        void putULong (OCPI::OS::uint32_t value);
        void putLong (OCPI::OS::int32_t value);
        
        /**
         * Marshal a CORBA::ULongLong value.  Padding is added if necessary.
         *
         * \param[in] value A CORBA::ULongLong value.
         */

        void putULongLong (OCPI::OS::uint64_t value);

        /**
         * Marshal a CORBA string.
         *
         * \param[in] value A string.
         */

        void putString (const std::string & value);

        /**
         * Marshal a sequence&lt;octet&gt;.
         *
         * \param[in] value An octet sequence.
         */

        void putOctetSeq (const std::string & value);

        //@}

        /**
         * Get the CDR-encoded marshalled data.
         *
         * \note The string may contain binary data and should not be
         * used as a C string.  Use std::string::data() and
         * std::string::length().
         *
         * \note The data is encoded using the native byteorder, which
         * must be communicated to the decoder.  (It may be embedded in
         * the stream itself.)
         */

        const std::string & data () const;

      protected:
        std::string m_data;
      };

      /**
       * \brief CDR Decoder
       */

      class Decoder {
      public:
        /**
         * \brief Thrown as an exception by the CDR Decoder.
         *
         * The exception that is thrown when data can not be decoded.
         */

        struct InvalidData {};

      public:
        /**
         * Constructor.
         *
         * \param[in] data Pointer to the CDR-encoded data to decode.
         * \param[in] size The length of the data blob, in octets.
         *
         * \post \a data shall not be modified for the lifetime of this
         * object, as no copy is made.
         */

        Decoder (const void * data, unsigned long size);

        /**
         * Constructor.
         *
         * \param[in] data CDR-encoded data to decode.
         *
         * \post \a data shall not be modified for the lifetime of this
         * object, as no copy is made.
         */

        Decoder (const std::string & data);

        /**
         * Get the current byteorder value.
         *
         * \return The decoder's current byteorder setting, true for
         *         little-endian, false for big-endian.
         */

        bool byteorder () const;

        /**
         * Set the byteorder for unmarshalling.  If this is different
         * than the native byteorder, data will be byte-swapped when
         * unmarshalled.
         *
         * \param[in] bo The byteorder to use, true for little-endian,
         *               false for big-endian.
         */

        void byteorder (bool bo);

        /**
         * Skip data so that the following data is aligned with respect
         * to the beginning of the stream.
         *
         * \param[in] mod The modulus to align to.
         */

        void align (unsigned long mod);

        /**
         * Returns the remaining number of octets in the buffer.
         *
         * This value can be used, e.g., to guard against invalid values
         * for the length of a sequence: if the length claims to be one
         * billion, then we can complain that the buffer does not contain
         * as much data, rather than failing to adjust the length of the
         * sequence.
         *
         * \return The number of octets left in the buffer.
         */

        unsigned long remainingData () const;

        /**
         * \name Unmarshalling data.
         */

        //@{

        /**
         * Unmarshal a boolean value.
         *
         * \param[out] value The boolean value.
         *
         * \throw InvalidData At the end of the stream.
         */

        void getBoolean (bool & value);

        /**
         * Unmarshal an octet value.
         *
         * \param[out] value The octet value.
         *
         * \throw InvalidData At the end of the stream.
         */

        void getOctet (unsigned char & value);

        /**
         * Unmarshal a CORBA::UShort value, aligning and byte-swapping if
         * necessary.
         *
         * \param[out] value The CORBA::UShort value.
         *
         * \throw InvalidData At the end of the stream.
         */

        void getUShort (OCPI::OS::uint16_t & value);

        /**
         * Unmarshal a CORBA::ULong value, aligning and byte-swapping if
         * necessary.
         *
         * \param[out] value The CORBA::ULong value.
         *
         * \throw InvalidData At the end of the stream.
         */

        void getULong (OCPI::OS::uint32_t & value);
        void getLong (OCPI::OS::int32_t & value);

        /**
         * Unmarshal a CORBA::ULongLong value, aligning and byte-swapping
         * if necessary.
         *
         * \param[out] value The CORBA::ULongLong value.
         *
         * \throw InvalidData At the end of the stream.
         */

        void getULongLong (OCPI::OS::uint64_t & value);

        /**
         * Unmarshal a CORBA string.
         *
         * \param[out] value The string value.
         *
         * \throw InvalidData At the end of the stream.
         */

        void getString (std::string & value);

        /**
         * Unmarshal a sequence of octets.
         *
         * \param[out] value The octet sequence.
         *
         * \throw InvalidData At the end of the stream.
         */

        void getOctetSeq (std::string & value);

        //@}

      protected:
        bool m_dataByteorder;
        bool m_nativeByteorder;
        unsigned long m_pos;
        unsigned long m_len;
        const char * m_data;
      };

    }
  }
}

/*
 * Inline implementation of copyswap2(), copyswap4() and copyswap8().
 * Hardly worth optimizing, as long as we don't deal with sequences.
 */

inline
void
OCPI::Util::CDR::
copyswap2 (char * pdest, const char * psrc)

{
  *pdest++ = psrc[1];
  *pdest = psrc[0];
}

inline
void
OCPI::Util::CDR::
copyswap4 (char * pdest, const char * psrc)

{
  psrc += 3;
  *pdest++ = *psrc--;
  *pdest++ = *psrc--;
  *pdest++ = *psrc--;
  *pdest = *psrc;
}

inline
void
OCPI::Util::CDR::
copyswap8 (char * pdest, const char * psrc)

{
  copyswap4 (pdest, psrc+4);
  copyswap4 (pdest+4, psrc);
}

#endif
