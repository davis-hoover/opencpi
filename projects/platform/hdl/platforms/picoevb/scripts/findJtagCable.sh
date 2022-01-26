#!/bin/bash --noprofile
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

dir=`dirname $0`

# optional arg 1 is the devices iSerial that were looking for 
serial=$1
logfile=/tmp/_lsusb.log
rm -f $logfile

echo Looking for FT230X cables on development host. 
lsusb -d 0403:6015 > $logfile
cables=`grep "" -c $logfile`
echo Detected $cables cable/s 1>&2

# no cables found
if [ "$cables" == "0" ] 
then
  echo No FT230X devices found. 1>&2
  exit 1
fi

# multiple cables detected no iSerial given
if [ $cables -gt 1 ] && [ -z "$1" ] 
then
  echo Multiple cables detected. Please specific iSerial to associate with correct jtag cable. 1>&2
  exit 1
fi

# only one cable is found and no serial provided assume its the right cable 
if [ "$cables" == "1" ] && [ -z "$1" ] 
then
  echo No iSerial provided, assuming cable found is the right FT230X cable. 1>&2
  exit 0
fi

# ensure specific cable is available 
lsusb -v -d 0403:6015 | grep $serial > $logfile 
isAvailable=`grep "" -c $logfile`
if [ "$isAvailable" == "1" ] 
then
  echo Discovered FT230X cable with iSerial $serial 1>&2
  exit 0
fi

echo Can not find cable with iSerial=$serial 1>&2
exit 1
