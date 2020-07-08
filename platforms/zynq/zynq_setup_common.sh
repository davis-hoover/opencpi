set_tool_platform() { 
  if test "$OCPI_TOOL_PLATFORM" == ""; then
    for m in /mnt/card /run/media/mmcblk0p1; do
      [ -d $m/opencpi ] && OCPI_DIR=$m/opencpi
    done
    if test -f release; then  # checks to see if xilinx13_4 platform is being ran
      read OCPI_RELEASE OCPI_TOOL_PLATFORM HDL_PLATFORM < release
    else
      echo Error: OCPI_TOOL_PLATFORM not set properly, $OCPI_DIR/release not found
      break  
    fi
  fi
}

set_time() {
  if test "$1" != -; then
    echo Attempting to set time from the time server
    # Calling ntpd without any options will run it as a dameon
    OPTS=""
    BUSYBOX_PATH="$OCPI_DIR/$OCPI_TOOL_PLATFORM/bin"
    TIMEOUT=20
    MSG="Succeeded in setting the time from $OCPI_DIR/ntp.conf"
    if [ ! -e $OCPI_DIR/ntp.conf ]; then
      OPTS="-p $1"
      MSG="Succeeded in setting the time from $1"
    fi
    # AV-5422 Timeout ntpd command after $TIMEOUT in seconds
    if $BUSYBOX_PATH/busybox timeout -t $TIMEOUT $BUSYBOX_PATH/ntpd -nq $OPTS > /dev/null 2>&1; then
      echo $MSG
	elif rdate -p time.nist.gov; then
	  rdate -s time.nist.gov
	  echo time set from time.nist.gov server
    else
      echo ====YOU HAVE NO NETWORK CONNECTION and NO HARDWARE CLOCK====
      echo Set the time using the '"date YYYY.MM.DD-HH:MM[:SS]"' command.
    fi
  fi
}

set_tool_platform
set_time
