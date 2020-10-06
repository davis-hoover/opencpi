#!/bin/bash

# Discover our interface used to communicate with the pluto
echo "Detecting which interface to use to communicate with pluto at $OCPI_SERVER_ADDRESSES"

# Try and make this as "false positive" proof as possible without over doing it
OCPI_SOCKET_INTERFACE=$(
  ip route get ${OCPI_SERVER_ADDRESSES%:*} \
  | head -n 1 \
  | awk '{
    if ($2 == "dev") {
      print($3)
    }
  }')

if [ -z "$OCPI_SOCKET_INTERFACE" ]; then
  echo "\
Error: did not discover an interface that can communicate directly
   with $OCPI_SERVER_ADDRESSES. You will need to manually set
   OCPI_SOCKET_INTERFACE to an interface that can communicate directly with the
   pluto device.
   Ex: export OCPI_SERVER_ADDRESSES=<interface>"
else
  echo "\
Setting OCPI_SOCKET_INTERFACE=$OCPI_SOCKET_INTERFACE"
  export OCPI_SOCKET_INTERFACE
fi

# Run any commands passed in
$@

exit 0
