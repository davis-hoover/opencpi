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

################################################################################
# This startup file is for running a minimal, relocatable, server configuration
# It is executed before running the server, usually via ssh
# It is the "server control script" that performs functions to manage the server
# in the server's system

function do_stop() {
  echo ocpiserve is running. sending SIGINT >&2
  kill -s INT $pid
  sleep 2
  kill -s CONT $pid > /dev/null 2>&1 && {
    echo ocpiserve is still running after SIGINT. Trying SIGTERM. >&2
    kill -s TERM $pid > /dev/null 2>&1 || :
    sleep 2
    kill -s CONT $pid > /dev/null 2>&1 && {
      echo ocpiserve is still running after SIGTERM. Trying SIGKILL. >&2
      kill -s KILL $pid >/dev/null 2>&1 || :
    }
  }
  rm ocpiserve.pid
}

# We are being run in a sandbox directory.
# We'll write a file here in case someone also wants to do env setup
cat >setup.sh <<'EOF'
export OCPI_CDK_DIR=`pwd`
export OCPI_TOOL_PLATFORM=$(cat swplatform)
export OCPI_TOOL_OS=linux
export OCPI_TOOL_DIR=$OCPI_TOOL_PLATFORM
PATH=$OCPI_CDK_DIR/$OCPI_TOOL_PLATFORM/bin:$PATH
export OCPI_SYSTEM_CONFIG=$OCPI_CDK_DIR/system.xml
export LD_LIBRARY_PATH=$OCPI_TOOL_PLATFORM/sdk/lib
EOF
source ./setup.sh
platform=$OCPI_TOOL_PLATFORM

echo Executing remote configuration command: $* 
action=$1; shift

while getopts u:l:w:a:p:s:d:o:P:BVh o
do 
  case "$o" in 
    u) user=$OPTARG ;;
    l) logopt="-l $OPTARG" ;;
    w) passwd=$OPTARG ;;
    a) host=$OPTARG ;;
    p) port=$OPTARG ;;
    s) sshopts=$OPTARG ;;
    d) rdir=$OPTARG ;;
    h) help ;;
    o) options=$OPTARG ;; 
    P) platform=$OPTARG ;;
    B) bs=-B ;;
    V) vg=-V ;;
  esac 
done
case $action in
start)
  if [ -f ocpiserve.pid ] && kill -s CONT $(cat ocpiserve.pid); then
    echo ocpiserve is still running. >&2
    exit 1
  fi
  set -e
  ocpidriver unload >&2 || : # in case it was loaded from a different version
  ocpidriver load >&2

  if [ -n "$bs" ]; then
    echo "Loading opencpi bitstream"
    HDL_PLATFORM=$(cat hwplatform)
    ocpihdl load -d pl:0 $OCPI_CDK_DIR/$HDL_PLATFORM/*.bitz
  fi
  
  log=$(date +%Y%m%d-%H%M%S).log

  if [ -n "$vg" ]; then
    export PATH=$PATH:prerequisites/valgrind/$platform/bin
    export VALGRIND_LIB=prerequisites/valgrind/$platform/lib/valgrind
    ldso=$(shopt -s nullglob && echo /lib/ld-*.so)
    echo $ldso
    sdk=$platform/lib/sdk/lib/$(basename $ldso)
    echo $PWD/$sdk
    [ -f $ldso -a -f $sdk ] && cp -v $sdk $ldso
  fi
  echo PATH=$PATH >&2
  echo LD_LIBRARY_PATH=$LD_LIBRARY_PATH >&2
  echo nohup ${vg:+valgrind --leak-check=full} ocpiserve -v $logopt -p $(cat port) \> $log >&2
  nohup ${vg:+valgrind --leak-check=full} ocpiserve -v $logopt -p $(cat port) >$log 2>&1 &
  pid=$!
  sleep 1
  if kill -s CONT $pid; then
    echo ocpiserve running with pid: $pid >&2
    echo $pid >ocpiserve.pid
    head $log
  else
    wait $pid
    echo Could not start ocpiserve: exit status $?, here is the last 10 lines of the log: >&2
    tail -10 $log >&2
    exit 1
  fi
  ;;
stop)
  if [ ! -f ocpiserve.pid ]; then
    echo No ocpiserve appears to be running: no pid file >&2
    exit 1
  fi
  pid=$(cat ocpiserve.pid)
  if ! kill -s CONT $pid; then
    echo No ocpiserve appears to be running \(pid $pid\). Process does not exist. >&2
    exit 1
  fi
  do_stop
  ;;
stop_if)
  [ -f ocpiserve.pid ] && {
    pid=$(cat ocpiserve.pid)
    kill -s CONT $pid && (do_stop || :)
    rm ocpiserve.pid
  } || :
  ;;
log) 
  for log_file in ./*.log ; do 
    if [ -e "$log_file" ] ; then
      logs=$(echo *.log)
      break
    fi 
  done 
  if [ -z "$logs" ]; then
    echo No logs found. >&2
    exit 1
  fi
  for log_file in ./*.log ; do 
    last=$log_file
  done
  if [ -f ocpiserve.pid ]; then
    pid=$(cat ocpiserve.pid)
    if kill -s CONT $(cat ocpiserve.pid); then
      echo Log is $last, pid is $pid >&2
      tail +0 -f $last
    fi
  fi
  echo No server running, dumping last log: $last >&2
  cat $last >&2
  ;;
status)
  if [ ! -f ocpiserve.pid ]; then
    echo No ocpiserve appears to be running: no pid file >&2
    exit 1
  fi
  pid=$(cat ocpiserve.pid)
  if ! kill -s CONT $pid; then
    echo No ocpiserve appears to be running \(pid $pid\). Process does not exist. >&2
    exit 1
  fi
  echo Server is running with port: $(cat port) and pid: $pid
  ;;
mount)
  for i in /mnt/card /media/card /run/media/mmc*; do
      echo Trying $i...
      if [ -r $i/u-boot.elf ]; then
	  echo Found $i...
	  rm -f /mnt/opencpi-boot
	  ln -s $i /mnt/opencpi-boot
          exit 0
      fi
  done
  echo Nothing found.  Trying to mount /dev/mmcblk0p1 on /mnt/card
  if [ -b /dev/mmcblk0p1 ]; then
      mkdir -o /mnt/card
      mount /dev/mmcblk0p1 /mnt/card
      rm -f /mnt/opencpi-boot
      ln -s /mnt/card /mnt/opencpi-boot
  fi
esac
