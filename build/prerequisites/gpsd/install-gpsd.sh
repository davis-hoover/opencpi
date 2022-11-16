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

[ -z "$OCPI_CDK_DIR" ] && echo 'Environment variable OCPI_CDK_DIR not set' && exit 1

target_platform="$1"
name=gpsd
# NOTE: when updating gpsd version, "${OcpiCrossCompile}ar"
# command below may be affected.
version=3.23.1  # latest as of 09/21/2021
pkg_name="$name-$version"
description='GPS (Global Positioning System) daemon'
dl_url="http://download-mirror.savannah.gnu.org/releases/$name/${pkg_name}.tar.gz"
extracted_dir="$pkg_name"
cross_build=1

# Download and extract source
source "$OCPI_CDK_DIR/scripts/setup-prerequisite.sh" \
       "$target_platform" \
       "$name" \
       "$description" \
       "${dl_url%/*}" \
       "${dl_url##*/}" \
       "$extracted_dir" \
       "$cross_build"

# GPSd does not support separate build directories yet, even though scons does,
# so we have to copy everything, per-platform, to the build directory for the
# platform
here="$(basename "$PWD")"
echo "Making a copy of gpsd for platform $platform because gpsd does not yet \
support separate build directories."
(cd ..; for i in *; do [[ "$i" != ocpi-build-* ]] && cp -Rp "$i" "$here"; done)

# Framework will error out w/ "recompile with -fPIC" if these aren't included
export CFLAGS="-fPIC"
export CXXFLAGS="-fPIC"

# For more info on scons options see SConstruct file in gpsd.git.
# shared=False is necessary because framework prerequisites must be statically
#              linkable.
# nostrip=True is necessary to avoid framework error during build: "error
#              adding symbols: Archive has no index; run ranlib to add one".
echo "OcpiCrossCompile=$OcpiCrossCompile"
echo "OcpiCrossHost=$OcpiCrossHost"

# Figure out how a potentially python3-compatible version of SCons
# is invoked on $OCPI_TOOL_PLATFORM.  As of 12 May 2020, there are
# two known possibilities.  If and/or when it becomes necessary to
# check for others, the preferred order is from "least likely" to
# "most likely", i.e., the sensible default of "scons" should be
# the last possibility checked.
SCONS="$(command -v scons-3 || command -v scons)"
if [ -z "$SCONS" ]; then
  echo "Error: cannot find scons or scons-3 which are required to build $name"
  exit 1
fi

"$SCONS" prefix="$OcpiInstallExecDir" target="$OcpiCrossHost" \
         libgpsmm=False ncurses=False qt=False python=False \
         usb=False bluez=False ntp=False manbuild=False shared=False \
         nostrip=True debug=True dbus_export=False
"$SCONS" install

# Because OpenCPI prerequisites must be statically compiled into a single
# archive, and the scons build produces both libgps.a and libgpsd.a, a single
# archive is manually constructed. The arguments to pass to ar were determined
# by: 1) run scons build, 2) observe two ar commands sent to stdout, 3) combine
# ar commands into one, 4) replace all *.a with a single libtmp.a
"${OcpiCrossCompile}ar" rc libtmp.a \
    ${pkg_name}/libgps/ais_json.o ${pkg_name}/libgps/bits.o \
    ${pkg_name}/libgps/gpsdclient.o ${pkg_name}/libgps/gps_maskdump.o \
    ${pkg_name}/libgps/gpsutils.o ${pkg_name}/libgps/hex.o \
    ${pkg_name}/libgps/json.o ${pkg_name}/libgps/libgps_core.o \
    ${pkg_name}/libgps/libgps_dbus.o ${pkg_name}/libgps/libgps_json.o \
    ${pkg_name}/libgps/libgps_shm.o ${pkg_name}/libgps/libgps_sock.o \
    ${pkg_name}/libgps/netlib.o ${pkg_name}/libgps/os_compat.o \
    ${pkg_name}/libgps/rtcm2_json.o ${pkg_name}/libgps/rtcm3_json.o \
    ${pkg_name}/libgps/shared_json.o ${pkg_name}/libgps/timespec_str.o \
    ${pkg_name}/gpsd/bsd_base64.o ${pkg_name}/gpsd/crc24q.o \
    ${pkg_name}/drivers/driver_ais.o ${pkg_name}/drivers/driver_evermore.o \
    ${pkg_name}/drivers/driver_garmin.o ${pkg_name}/drivers/driver_garmin_txt.o \
    ${pkg_name}/drivers/driver_geostar.o ${pkg_name}/drivers/driver_greis.o \
    ${pkg_name}/drivers/driver_greis_checksum.o ${pkg_name}/drivers/driver_italk.o \
    ${pkg_name}/drivers/driver_navcom.o ${pkg_name}/drivers/driver_nmea0183.o \
    ${pkg_name}/drivers/driver_nmea2000.o ${pkg_name}/drivers/driver_oncore.o \
    ${pkg_name}/drivers/driver_rtcm2.o ${pkg_name}/drivers/driver_rtcm3.o \
    ${pkg_name}/drivers/drivers.o ${pkg_name}/drivers/driver_sirf.o \
    ${pkg_name}/drivers/driver_skytraq.o ${pkg_name}/drivers/driver_superstar2.o \
    ${pkg_name}/drivers/driver_tsip.o ${pkg_name}/drivers/driver_ubx.o \
    ${pkg_name}/drivers/driver_zodiac.o ${pkg_name}/gpsd/geoid.o \
    ${pkg_name}/gpsd/gpsd_json.o ${pkg_name}/gpsd/isgps.o \
    ${pkg_name}/gpsd/libgpsd_core.o ${pkg_name}/gpsd/matrix.o \
    ${pkg_name}/gpsd/net_dgpsip.o ${pkg_name}/gpsd/net_gnss_dispatch.o \
    ${pkg_name}/gpsd/net_ntrip.o ${pkg_name}/gpsd/ntpshmread.o \
    ${pkg_name}/gpsd/ntpshmwrite.o ${pkg_name}/gpsd/packet.o \
    ${pkg_name}/gpsd/ppsthread.o ${pkg_name}/gpsd/pseudoais.o \
    ${pkg_name}/gpsd/pseudonmea.o ${pkg_name}/gpsd/serial.o \
    ${pkg_name}/gpsd/subframe.o ${pkg_name}/gpsd/timebase.o
"${OcpiCrossCompile}ranlib" libtmp.a

rm -rf "${OcpiInstallExecDir:?}/lib/*"
cp libtmp.a "$OcpiInstallExecDir/lib/libgpsd.a"

echo 'copying lower level headers which are necessary for use of libgpsd \
directly...'
# FIXME: header list sufficiency not tested for 3.23.1.
headers=(include/gpsd.h include/compiler.h ${pkg_name}/include/gpsd_config.h \
  include/gps.h include/ppsthread.h include/os_compat.h include/timespec.h)
for header in "${headers[@]}"; do
  echo "...copying $header to $OcpiInstallExecDir/include/"
  cp "$header" "$OcpiInstallExecDir/include/"
done
