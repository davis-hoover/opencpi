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

#include "TransportPartition.hh"
#include "TransportDistribution.hh"

namespace OCPI {
namespace DataTransport {

DataDistributionMetaData::
DataDistributionMetaData(DataPartition *){}

DataDistributionMetaData::
DataDistributionMetaData(){}

DataDistributionMetaData::
~DataDistributionMetaData(){}

DataDistribution::
DataDistribution(DataDistributionMetaData *data, Circuit *circuit)
  : m_metaData(data), m_circuit(circuit){}

// Used for test
DataDistribution::
DataDistribution() {
  m_metaData = new DataDistributionMetaData();
}

DataDistribution::~DataDistribution() {
  delete m_metaData;
}

ParallelDataDistribution::
ParallelDataDistribution(DataDistributionMetaData *data,
			 Circuit *circuit)
  : DataDistribution(data, circuit) {
}

// Default is parallel/whole
ParallelDataDistribution::
ParallelDataDistribution(DataPartition *parts) {
  // Distribution type
  m_metaData->distType = DataDistributionMetaData::parallel;

  // Distribution sub-type
  // m_metaData->distSubType; // not used for parallel distribution

  // Our partition object, default is whole distribution
  if (!parts)
    m_metaData->partition = new IndivisiblePartition();
  else
    m_metaData->partition = parts;
}

ParallelDataDistribution::
~ParallelDataDistribution() {
  delete  m_metaData->partition;
}

SequentialDataDistribution::
SequentialDataDistribution(DataDistributionMetaData *data,
			   Circuit *circuit)
  : DataDistribution(data, circuit) {
}

// Default is sequential/round robin
SequentialDataDistribution::
SequentialDataDistribution(DataDistributionMetaData::DistributionSubType sub_type) {
  // Distribution type
  m_metaData->distType = DataDistributionMetaData::sequential;

  // Distribution sub-type
  m_metaData->distSubType = sub_type;

  // Our partition object, default is whole distribution
  m_metaData->partition = new IndivisiblePartition();
}

}
}
