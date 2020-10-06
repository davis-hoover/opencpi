#!/bin/bash

NFS_IP=10.11.0.1
NFS_MOUNT=/opt/Xilinx
NFS_DRIVE="${NFS_IP}:${NFS_MOUNT}"
MOUNT_POINT=/opt/Xilinx
VPN_CONF=opencpi-test.net.conf

clean_vpn=
if [ -f "/openvpn/${VPN_CONF}" ]; then
  logfile=/tmp/openvpn.log
  cd /openvpn || exit
  echo "Establishing VPN connection (log file: ${logfile})"
  openvpn --config "${VPN_CONF}" --log "${logfile}" &
  sleep 2
  disown
  cd - &> /dev/null || exit

  # Get IP address of tun0 interface
  if ip a show dev tun0 &> /dev/null; then
    my_ip=$(ip a show dev tun0 | awk '/inet / {print $2}')
    my_ip="${my_ip%/*}"
    echo "Setting OCPI_TRANSFER_IP_ADDRESS=${my_ip}"
    export OCPI_TRANSFER_IP_ADDRESS="${my_ip}"
    echo "Setting OCPI_SOCKET_INTERFACE=tun0"
    export OCPI_SOCKET_INTERFACE=tun0
    clean_vpn=1
  else
    echo "Failed to establish VPN connection."
    echo "  config file: ${VPN_CONF}"
    echo "  log file:    ${logfile}"
  fi
fi

clean_nfs=
if [ -d "${MOUNT_POINT}/Vivado" ]; then
  echo "NFS mount point '${MOUNT_POINT}' already exists. Skipping NFS mounting..."
elif getpcaps $$ 2>&1 | grep -q cap_sys_admin; then
  # Only mount if VPN is up
  if [ -n "${clean_vpn}" ]; then
    echo "Mounting NFS drive ${NFS_DRIVE} to ${MOUNT_POINT}"
    mkdir -p "${MOUNT_POINT}"
    mount -t nfs4 \
          -o nfsvers=4.1,ro,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport,_netdev,nolock \
          "${NFS_DRIVE}" "${MOUNT_POINT}"
    clean_nfs=1
  fi
fi

echo "Setting up OpenCPI environment"
echo "source /opencpi/cdk/opencpi-setup.sh -r" >> ~/.bashrc

# Run any commands passed in
"$@"

echo "Cleaning up..."

if [ -n "${clean_nfs}" ]; then
  echo "Unmounting NFS drive"
  umount -f "${MOUNT_POINT}"
fi

if [ -n "${clean_vpn}" ]; then
  echo "Closing VPN connection"
  killall openvpn
fi

exit 0
