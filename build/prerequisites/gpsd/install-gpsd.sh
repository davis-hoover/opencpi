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

# This server is unavailable:       https://ftp.gnu.org/gnu/gmp
# Since we don't look at multiple URLs/mirrors (yet)
# The one below is one of the advertised mirrors
me=gpsd

[ -z "$OCPI_CDK_DIR" ] && echo Environment variable OCPI_CDK_DIR not set && exit 1
source $OCPI_CDK_DIR/scripts/setup-prerequisite.sh \
       "$1" \
       $me \
       "GPS (Global Positioning System) daemon" \
       https://git.savannah.gnu.org/git/gpsd.git \
       release-3.14 \
       $me \
       1

cd ..

# framework will error out w/ "recompile with -fPIC" if these aren't included
export CFLAGS="-fPIC"
export CXXFLAGS="-fPIC"

# For more info on scons options see SConstruct file in gpsd.git.
# shared=False is necessary because framework prerequisites must be statically
#              linkable.
# nostrip=True is necessary to avoid frameworker error during build: "error
#              adding symbols: Archive has no index; run ranlib to add one".
echo OcpiCrossCompile=$OcpiCrossCompile
echo OcpiCrossHost=$OcpiCrossHost
sysroot=/
[ ! -z $OcpiCrossHost ] && sysroot=$(echo $OcpiCrossCompile | sed "s|/bin[^/]*/$OcpiCrossHost-||")/$OcpiCrossHost/libc
scons prefix=$OcpiInstallExecDir target=$OcpiCrossHost sysroot=$sysroot libgpsmm=True ncurses=False qt=False python=False usb=False bluez=False ntp=False manbuild=False shared=False nostrip=True debug=True
scons install
ar rc libtmp.a ais_json.o bits.o clock_gettime.o daemon.o gpsutils.o gpsdclient.o gps_maskdump.o hex.o json.o libgps_core.o libgps_dbus.o libgps_json.o libgps_shm.o libgps_sock.o netlib.o ntpshmread.o ntpshmwrite.o rtcm2_json.o rtcm3_json.o shared_json.o strl.o libgpsmm.o bsd_base64.o crc24q.o gpsd_json.o geoid.o isgps.o libgpsd_core.o matrix.o net_dgpsip.o net_gnss_dispatch.o net_ntrip.o ppsthread.o packet.o pseudonmea.o pseudoais.o serial.o subframe.o timebase.o timespec_str.o drivers.o driver_ais.o driver_evermore.o driver_garmin.o driver_garmin_txt.o driver_geostar.o driver_italk.o driver_navcom.o driver_nmea0183.o driver_nmea2000.o driver_oncore.o driver_rtcm2.o driver_rtcm3.o driver_sirf.o driver_superstar2.o driver_tsip.o driver_ubx.o driver_zodiac.o
ranlib libtmp.a
rm -rf $OcpiInstallExecDir/lib/*
cp libtmp.a $OcpiInstallExecDir/lib/libgpsd.a

echo "copying lower level headers which are necessary for use of libgpsd directly..."
headers=(gpsd.h compiler.h gpsd_config.h gps.h ppsthread.h)
for header in "${headers[@]}"; do
  echo "...copying $header to $OcpiInstallExecDir/include/"
  cp $header $OcpiInstallExecDir/include/
done

#cp $OcpiThisPrerequisiteDir/prerequisites/$me/etc_initd_gpsd $OcpiInstallExecDir/bin
