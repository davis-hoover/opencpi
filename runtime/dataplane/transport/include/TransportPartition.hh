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

#ifndef OCPI_Transport_Partition_H_
#define OCPI_Transport_Partition_H_

#include "XferEndPoint.h"

namespace OCPI {
namespace DataTransport {

// Forward references
class Port;
class PortSet;
class Buffer;

struct DataPartitionMetaData {
  DataPartitionMetaData();
  enum PartitionType {
    INDIVISIBLE,
    BLOCK
  };
  enum ScalarType {
    CHAR,
    UCHAR,
    SHORT,
    USHORT,
    INTEGER,
    UINTEGER,
    LONG,
    ULONG,
    FLOAT,
    DOUBLE
  };

  uint32_t minAlignment;
  uint32_t minSize;
  uint32_t maxSize;
  uint32_t moduloSize;
  uint32_t elementCount;
  uint32_t numberOfDims;
  uint32_t scalarsPerElem;
  ScalarType scalarType;
  PartitionType dataPartType;
  uint32_t blockSize;
};

class DataPartition {
public:
  struct BufferInfo {
    DtOsDataTypes::Offset output_offset;
    DtOsDataTypes::Offset input_offset;
    uint32_t length;
    BufferInfo *next;
    BufferInfo();
    ~BufferInfo();
    //Add another structure
    void add(BufferInfo *bi);
  };
private:
  // Our data partition meta data
  DataPartitionMetaData* m_data;
public:
  DataPartition();  // Default is whole distribution
  DataPartition(DataPartitionMetaData *md);
  virtual ~DataPartition();
  // Given the inherit distribution and partition information
  // calculate the offsets into the requested buffers for distribution.
  // returns 0 on success.
  //
  // Note: It is the responsibility of the caller to "delete" the allocated 
  // BufferInfo structure.
  virtual void calculateBufferOffsets(uint32_t     sequence,        // In - Transfer sequence
				      Buffer      *src_buf,         // In - Output buffer
				      Buffer      *input_buf,       // In - Input buffer
				      BufferInfo **input_buf_info); // Out
  // Get the total number of individual transfers that are needed to transfer
  // all of the parts from the output to the inputs.
  uint32_t getTransferCount(PortSet *src_ps,    // In - Output port set
			    PortSet *input_ps); // In - Input port set
  // Get the total number of parts that make up the whole for this distribution.
  uint32_t getPartsCount(PortSet *src_ps,    // In - Output port set
			 PortSet *input_ps); // In - Input port set
  // Given the parts sequence, calculate the offset into output buffer
  uint32_t getOutputOffset(PortSet *src_ps,    // In - Output port set
			   PortSet *input_ps,  // In - Input port set
			   uint32_t sequence); // In - The sequence within the set
  DataPartitionMetaData *getData() {return m_data; }
protected:
  void calculateWholeToParts(uint32_t    sequence,  // In - Transfer sequence
			     Buffer     *src_buf,   // In - Output buffer
			     Buffer     *input_buf, // In - Input buffer
			     BufferInfo *buf_info); // InOut - Buffer info
  void calculatePartsToWhole(uint32_t    sequence,  // In - Transfer sequence
			     Buffer     *src_buf,   // In - Output buffer
			     Buffer     *input_buf, // In - Input buffer
			     BufferInfo *buf_info); // InOut - Buffer info
  void calculatePartsToParts(uint32_t    sequence,  // In - Transfer sequence
			     Buffer     *src_buf,   // In - Output buffer
			     Buffer     *input_buf, // In - Input buffer
			     BufferInfo *buf_info); // InOut - Buffer info
};

class IndivisiblePartition : public DataPartition {
public:
  IndivisiblePartition();
  virtual ~IndivisiblePartition();
  virtual void calculateBufferOffsets(uint32_t    sequence,
				      Buffer     *src_buf,
				      Buffer     *input_buf,
				      BufferInfo **input_buf_info);
};

class BlockPartition : public DataPartition {
public:
  BlockPartition();
  virtual ~BlockPartition();
  virtual void calculateBufferOffsets(uint32_t    sequence,          // In - Transfer sequence
				      Buffer     *src_buf,           // In - Source buffer
				      Buffer     *target_buf,        // In - Target buffer
				      BufferInfo **target_buf_info); // Out
};
}
}
#endif
