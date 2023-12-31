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

# This server is unavailable:       https://ftp.gnu.org/gnu/gmp
# Since we don't look at multiple URLs/mirrors (yet)
# The one below is one of the advertised mirrors

[ -z "$OCPI_CDK_DIR" ] && echo 'Environment variable OCPI_CDK_DIR not set' && exit 1

target_platform="$1"
name=gpsd
version=3.18 # NOTE: when updating gpsd version, "${OcpiCrossCompile}ar"
             # command below may be affected
#version=3.21  # latest as of 09/02/2020
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

patchfile=compiler.patch
patch -p0 < "$OcpiThisPrerequisiteDir/$patchfile" || {
  echo '*******************************************************' >&2
  echo "ERROR: patch applied by $patchfile failed!!" >&2
  echo '*******************************************************' >&2
  exit 1
}

# Framework will error out w/ "recompile with -fPIC" if these aren't included
export CFLAGS="-fPIC"
export CXXFLAGS="-fPIC"

# For more info on scons options see SConstruct file in gpsd.git.
# shared=False is necessary because framework prerequisites must be statically
#              linkable.
# nostrip=True is necessary to avoid frameworker error during build: "error
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
"${OcpiCrossCompile}ar" rc libtmp.a ais_json.o bits.o gpsdclient.o \
    gps_maskdump.o gpsutils.o \
    hex.o json.o libgps_core.o libgps_dbus.o libgps_json.o \
    libgps_shm.o libgps_sock.o netlib.o os_compat.o \
    rtcm2_json.o rtcm3_json.o shared_json.o bsd_base64.o \
    crc24q.o \
    driver_ais.o driver_evermore.o driver_garmin.o driver_garmin_txt.o \
    driver_geostar.o driver_greis.o driver_greis_checksum.o \
    driver_italk.o driver_navcom.o driver_nmea0183.o \
    driver_nmea2000.o driver_oncore.o driver_rtcm2.o driver_rtcm3.o \
    drivers.o driver_sirf.o \
    driver_skytraq.o driver_superstar2.o driver_tsip.o driver_ubx.o \
    driver_zodiac.o \
    geoid.o gpsd_json.o isgps.o libgpsd_core.o matrix.o net_dgpsip.o \
    net_gnss_dispatch.o net_ntrip.o ntpshmread.o ntpshmwrite.o packet.o \
    ppsthread.o pseudoais.o pseudonmea.o serial.o subframe.o timebase.o \
    timespec_str.o
"${OcpiCrossCompile}ranlib" libtmp.a

rm -rf "${OcpiInstallExecDir:?}/lib/*"
cp libtmp.a "$OcpiInstallExecDir/lib/libgpsd.a"

echo 'copying lower level headers which are necessary for use of libgpsd \
directly...'
headers=(gpsd.h compiler.h gpsd_config.h gps.h ppsthread.h os_compat.h)
for header in "${headers[@]}"; do
  echo "...copying $header to $OcpiInstallExecDir/include/"
  cp "$header" "$OcpiInstallExecDir/include/"
done
