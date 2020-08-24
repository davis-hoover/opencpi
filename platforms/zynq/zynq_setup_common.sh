# expects to find the opencpi diretory in one of those two directories
# make sure that the release text file is also present
set_tool_platform() { 
  if test "$OCPI_TOOL_PLATFORM" == ""; then
    for m in /mnt/card /run/media/mmcblk0p1; do
      [ -d $m/opencpi ] && export OCPI_DIR=$m/opencpi
    done
    if test -f release; then  # checks to see if xilinx13_4 platform is being ran
      read OCPI_RELEASE OCPI_TOOL_PLATFORM HDL_PLATFORM < $OCPI_DIR/release
	  export OCPI_RELEASE OCPI_TOOL_PLATFORM HDL_PLATFORM
    else
      echo Error: OCPI_TOOL_PLATFORM not set properly, $OCPI_DIR/release not found
      break  
    fi
  fi
}

# Set time using ntpd
# If ntpd fails because it could not find ntp.conf fall back on time server
# passed in as the first parameter
set_time() {
  if test "$1" != -; then
    echo Attempting to set time from $1
    # Calling ntpd without any options will run it as a dameon
    OPTS=""
    BUSYBOX_PATH="$OCPI_DIR/$OCPI_TOOL_PLATFORM/bin"
    TIMEOUT=5
    MSG="Succeeded in setting the time from $OCPI_DIR/ntp.conf"
    if [ ! -e $OCPI_DIR/ntp.conf ]; then
      OPTS="-p $1"
      MSG="Succeeded in setting the time from $1"
    fi
    # AV-5422 Timeout ntpd command after $TIMEOUT in seconds
    if $BUSYBOX_PATH/busybox timeout -t $TIMEOUT $BUSYBOX_PATH/ntpd -nq $OPTS > /dev/null 2>&1; then
      echo $MSG
	elif rdate -s $1; then
	  echo time set from $1 server
    else
      echo ====YOU HAVE NO NETWORK CONNECTION and NO HARDWARE CLOCK====
      echo Set the time using the '"date YYYY.MM.DD-HH:MM[:SS]"' command.
    fi
  fi
}

if test "$1" = "set_tool_platform"; then
  set_tool_platform
fi

if test "$2" = "set_time"; then
  set_time $3
fi

