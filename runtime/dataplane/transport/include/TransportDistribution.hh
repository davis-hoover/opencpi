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

#ifndef OCPI_Transport_Distribution_H_
#define OCPI_Transport_Distribution_H_

#include <cstddef>

namespace OCPI {
namespace DataTransport {

class DataPartition;
struct DataDistributionMetaData {
  enum DistributionType {
    parallel,
    sequential
  };
  enum DistributionSubType {
    round_robin,
    random_even,
    random_statistical,
    first_available,
    least_busy
  };
  DataDistributionMetaData(DataPartition *part);
  DataDistributionMetaData();
  virtual ~DataDistributionMetaData();
  enum DistributionType distType;
  enum DistributionSubType distSubType;
  DataPartition *partition;
};

// The data distribution interface whose implementation is responsible for performing the setup
// and perhaps the actual distribution of the data.

class Circuit;
class DataDistribution {
protected:
  DataDistributionMetaData *m_metaData;
  // Our circuit, we need this since we need to get the other Data distribution
  // information from it
  Circuit *m_circuit;
public:
  DataDistribution(DataDistributionMetaData *meta_data, Circuit *circuit);
  DataDistribution();
  virtual ~DataDistribution();
  void setDataPartition(DataPartition *part) { m_metaData->partition = part; }
  DataPartition *getDataPartition() { return m_metaData->partition; }
  DataDistributionMetaData *getMetaData() { return m_metaData; }
};

class ParallelDataDistribution : public DataDistribution {
public:
  ParallelDataDistribution(DataDistributionMetaData *data,
			   Circuit *circuit);
  // This is used for test
  ParallelDataDistribution(DataPartition *parts = NULL);
  virtual ~ParallelDataDistribution();
};

class SequentialDataDistribution : public DataDistribution {
public:
  SequentialDataDistribution(DataDistributionMetaData * data,
			     Circuit *circuit);
  SequentialDataDistribution(DataDistributionMetaData::DistributionSubType sub_type);
};

}
}

#endif
