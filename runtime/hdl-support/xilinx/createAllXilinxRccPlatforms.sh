#!/bin/bash
# This file is protected by Copyright. Please refer to the COPYRIGHT file
# distributed with this source distribution.
#
# This file is part of OpenCPI <http://www.opencpi.org>
#
# OpenCPI is free software: you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# OpenCPI is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.

####################################################################################################
# Create all xilinx software platforms
function create {
  yq=${2#20}
  version=${yq/\./_}
  platform=xilinx${version}_$3
  rm -r -f exports/$platform exports/runtime/$platform projects/$1/exports/rcc/platforms/$platform projects/$1/rcc/platforms/$platform
  $OCPI_CDK_DIR/scripts/xilinx/createXilinxRccPlatform.sh $1 $2 $3 $4 $5
  ./scripts/install-platform.sh $platform
  # This is a nice idea, but it depends on zed being built
  # ./scripts/deploy-opencpi.sh zed $platform
}
set -e
# Note we have extracted the non-standard xilinx linux repo tags that go with their releases.
# These are mentioned on their wiki page for the various releases.
#create core 2013.4 arm
#create core 2014.1 arm
#create core 2014.2 arm xilinx-v2014.2.01
#create core 2014.3 arm
#create core 2014.4 arm
#create core 2015.1 aarch32
#create core 2015.2 aarch32 xilinx-v2015.2.01
#create core 2015.4 aarch32
#create core 2016.1 arm xilinx-v2016.1.01
#create core 2016.1 arm xilinx-v2016.1.01
#create core 2016.2 arm
#create core 2016.3 arm
#create core 2016.4 arm
#create core 2017.1 aarch32
#create core 2017.1 aarch64
create core 2017.2 aarch32
create core 2017.2 aarch64
#create core 2017.3 aarch32
#create core 2017.3 aarch64
#create core 2017.4 aarch32
#create core 2017.4 aarch64
#create core 2018.1 aarch32
#create core 2018.1 aarch64
#create core 2018.2 aarch32
#create core 2018.2 aarch64
#create core 2018.3 aarch32
#create core 2018.3 aarch64
#create core 2019.1 aarch32 xlnx_rebase_v4.19_2019.1
#create core 2019.1 aarch64 xlnx_rebase_v4.19_2019.1
#create core 2019.2 aarch32 xilinx-v2019.2.01
#create core 2019.2 aarch64 xilinx-v2019.2.01


