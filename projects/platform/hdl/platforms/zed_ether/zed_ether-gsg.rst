.. zed_ether Getting Started Guide Documentation


.. _zed_ether-gsg:

``zed_ether`` Getting Started Guide
===================================
This is a reference platform to demonstrate use of the OpenCPI Ethernet interface.
It is based around an Avnet Zedboard (Xilinx Zynq 7020) and an
`Avnet FMC Ethernet card <https://www.avnet.com/shop/us/products/avnet-engineering-services/aes-fmc-netw1-g-3074457345635205181/>`_
to provide dual RGMII Ethernet interfaces connected to the FPGA fabric.

Note that since the FMC connector is used to provide Ethernet connectivity,
it is integral to the platform and not available for other uses. Therefore this
platform does not declare a slot for the FMC connector, and the platform worker
and XDC file are written assuming that the Ethernet card is always present.

The Zynq PS and attached devices (e.g. on-board Ethernet interface) are not used
in this platform. The bitstream will not boot without the FMC card attached as the
125MHz oscillator on the FMC card is used to derive all clocks.

The MAC address for the Ethernet interface is read from the EEPROM associated with
Ethernet Port 1. If the second Ethernet interface is enabled, a bonded configuration
is used so the same MAC address is used for both interfaces, and outbound packets
are dispatched in a round-robin fashion. See `Connect the host PC to the device`_
for details on how to set up the host to work in this mode.

Revision History
----------------

.. csv-table:: zed_ether Getting Started Guide: Revision History
   :header: "Revision", "Description of Change", "Date"
   :widths: 10,30,10
   :class: tight-table

   "v1.0", "Initial Release", "2nd March 2022"
   "v1.1", "Change zed_ether to a built-in platform", "24th June 2022"

Software Prerequisites
----------------------
A Linux host PC with a Vivado 2019.2 installation (Lab Edition at a minimum to
run applications, Design Edition or Webpack to build a bitstream) and an
OpenCPI installation.

The Ethernet interfaces use raw sockets to communicate with the device, which
requires the ``CAP_NET_RAW`` capability. This can be accomplished either by running
as root, or (preferably) by setting this capability on the application executable.
For example, to work through the rest of this guide, run

.. code-block:: bash

   $ sudo setcap CAP_NET_RAW+eip $(readlink -f $(which ocpihdl))
   $ sudo setcap CAP_NET_RAW+eip $(readlink -f $(which ocpirun))

to enable raw sockets for ``ocpihdl`` and ``ocpirun``. Note that to use an ACI
application rather than ``ocpirun``, the capability needs to be set on the
application binary as part of the installation process. If you want to debug
an application, the ``gdb`` and ``bash`` executables also need the capability.

.. code-block:: bash

   $ sudo setcap CAP_NET_RAW+eip $(readlink -f $(which gdb))
   $ sudo setcap CAP_NET_RAW+eip $(readlink -f $(which bash))
   $ gdb --args ocpirun -d -l 8 <application>.xml

Hardware Prerequisites
----------------------
* Avnet Zedboard with VAUX select jumper J18 set to 2V5 (the default)
* `Avnet FMC Ethernet card <https://www.avnet.com/shop/us/products/avnet-engineering-services/aes-fmc-netw1-g-3074457345635205181/>`_, modified as described below.
* Host PC with one or two 1Gb Ethernet interfaces

The Q1 transistor on the Ethernet card **must be removed** to resolve
`a PCB erratum <https://www.avnet.com/opasdata/d120001/medias/docus/198/Network_FMC_Errata_200213.pdf>`_
which makes the stock PCB incompatible with the Zedboard (the transistor drives
the Power Good LED but the required base current is too high for the Zedboard's
Power Good output to supply - if the fix is not applied, the Zedboard will not
come out of reset).

Note that the date code information in the errata appears to be incorrect. We have
an affected board with date code “2019” (according to the document the errata
should not applied to this board).

Platform details
----------------

This platform provides one dataplane transport called ``ether``, which can be
used to connect input and output ports in the container XML file.

The ``dgrdma_config_dev`` device worker (from ``opencpi/projects/core/components``)
must be included in the container in order for the runtime to properly configure
the DG-RDMA component. The easiest way to do this is to specify the ``dgrdma_dev``
platform configuration (rather than ``base``) in the container XML file. An example
minimal ``container.xml`` is shown below.

.. code-block:: xml

   <HdlContainer Platform="zed_ether" Config="dgrdma_dev">
      <Connection External="in_1" Interconnect="ether"/>
      <Connection External="out_1" Interconnect="ether"/>
   </HdlContainer>

The switches and LEDs on the board are not made available to the application;
instead they are used for debug outputs from the platform worker. SW[2:0] are used
to select the LED display mode (SW[0] and LED[0] are nearest the FMC connector).

.. csv-table:: Switch and LED functions
   :header: "SW[2:0]", "LED function",
   :class: tight-table

   "000", "[0]: 1Hz heartbeat, [1]: MAC address successfully read, [2]: MAC address read error, [4:3] ETH1 MAC speed (00=10M, 01=100M, 10=1000M), [6:5] ETH2 MAC speed"
   "001", "mac_addr[47:40]"
   "010", "mac_addr[39:32]"
   "011", "mac_addr[31:24]"
   "100", "mac_addr[23:16]"
   "101", "mac_addr[15:8]"
   "110", "mac_addr[7:0]"
   "111", "constant 0xaa"

Setup Guide
-----------

In order to set up a host system to run applications on this platform, the
following steps need to be completed:

1. Build a test bitstream to be used for autodiscovery and configuration

2. Connect the host PC to the device

3. Set up the JTAG cable drivers

4. Write a system.xml file specifying the system configuration

5. Load the bitstream

Build a test bitstream to be used for autodiscovery and configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install the platform by running:

.. code-block:: bash

   $ ocpiadmin install platform zed_ether --minimal

To create and build a test project with a minimal assembly.

.. code-block:: bash

   $ ocpidev create project zed_ether_test -K local.zed_ether_test -y ocpi.platform
   $ cd zed_ether_test
   $ touch hdl/assemblies/bias_loopback/zed_ether_container.xml
   $ ocpidev create application -X loopback


Edit the assembly ``hdl/assemblies/bias_loopback/bias_loopback.xml``.

.. code-block:: xml

   <hdlassembly defaultcontainers="" containers="zed_ether_container">
     <connection name="fpga_in" external="consumer">
       <port instance="bias_vhdl" name="in"/>
     </connection>
     <instance worker="bias_vhdl"/>
     <connection name="fpga_out" external="producer">
       <port instance="bias_vhdl" name="out"/>
     </connection>
   </hdlassembly>

Edit the container ``hdl/assemblies/bias_loopback/zed_ether_container.xml``.

.. code-block:: xml

   <hdlcontainer platform="zed_ether" config="dgrdma_dev">
     <connection External="fpga_in" interconnect="ether"/>
     <connection External="fpga_out" interconnect="ether"/>
   </hdlcontainer>

Edit the application ``applications/loopback.xml``.

.. code-block:: xml

   <application package="ocpi.core" finished="file_write">
     <instance component="ocpi.core.dgrdma_config_proxy"/>
     <instance component="ocpi.core.file_read" connect="bias">
       <property name="fileName" value="in_file.bin" />
       <property name="messagesInFile" value="false"/>
     </instance>
     <instance component="ocpi.core.bias" connect="file_write"/>
     <instance component="ocpi.core.file_write">
       <property name="fileName" value="out_file.bin"/>
     </instance>
   </application>

Build the assembly:

.. code-block:: bash

   $ ocpidev build project --hdl-platform zed_ether --workers-as-needed


Connect the host PC to the device
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Connect a USB cable from the host PC to the PROG port on the Zedboard (next to
the power connector). Connect the FMC card to the FMC connector on the Zedboard,
and apply power. The red LED on the Ethernet card should illuminate indicating
that the correct VAUX voltage (2V5) has been selected; if the LED is green or
orange, check the J18 jumper on the Zedboard.

If using a single Ethernet connection, connect it to port 1 on the Zedboard and
note the name of the network interface.

If using two Ethernet interfaces, connect them both to the Zedboard.  The OpenCPI DGRDMA
functionality requires both ethernet interfaces to be bonded together to form a single
aggregated link.  Packets sent between the zed_ether hardware and the PC are then able to use
both physical ethernet interfaces. Treating them as a single link.

Create a Linux bonded interface as follows. *Note that this will need repeating after a reboot*.

Run the following commands **as root** to create a Linux bonded interface (assuming the
two interfaces on the PC are named ``eth1`` and ``eth2``):

.. code-block:: bash

   $ ip link add bond0 type bond
   $ echo balance-rr > /sys/class/net/bond0/bonding/mode
   $ echo 100 > /sys/class/net/bond0/bonding/miimon
   $ ip link set eth1 down
   $ ip link set eth2 down
   $ ip link set eth1 master bond0
   $ ip link set eth2 master bond0
   $ ip link set bond0 up

This creates a bonded network interface called ``bond0`` using the ``balance-rr``
method (which uses a round-robin algorithm to dispatch outbound packets on the
two interfaces). The bonded interface name and MAC address should be used for all
OpenCPI configuration as described below (usually the MAC address of the first
physical interface added is used, ``eth1`` in this case).

If you wish to use an interface MTU larger than the default of 1500 bytes, it
must be configured on the network interface.

To verify that networking is properly configured, manually load the example OpenCPI
bitstream (built in `Build a test bitstream to be used for autodiscovery and configuration`_) into
the device using Vivado Hardware Manager. Verify that the network interface is up and visible to OpenCPI:

.. code-block:: bash

   $ ocpihdl ethers
    1. lo: MAC address none, up, connected, loopback, IP address: 127.0.0.1
    2. ens36: MAC address 00:0c:29:e2:30:24, up, connected

Then perform discovery:

.. code-block:: bash

   $ export OCPI_ENABLE_HDL_NETWORK_DISCOVERY=1
   $ ocpihdl search
   OpenCPI HDL device found: 'Ether:ens36/80:1f:12:7c:d7:fa': bitstream date Thu Mar  3 08:08:11 2022, platform "zed_ether", part "xc7z020", UUID 1fbbe888-9b0c-11ec-a9eb-dbc5900fab1a

This requires raw socket access: either run as ``root`` or set the ``CAP_NET_RAW``
capability on the ``ocpihdl`` executable as described in `Software Prerequisites`_.
The ``OCPI_ENABLE_HDL_NETWORK_DISCOVERY`` environment variable must be set to
search for Ethernet devices as shown above.  The ``OCPI_SYSTEM_CONFIG`` environment
variable must **not** be set.

If no devices were found, refer to `Troubleshooting`_ section.

Set up the JTAG cable drivers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Ensure that the cable drivers are installed - once Vivado is installed, a separate
script needs to be run to install drivers on Linux:

.. code-block:: bash

   $ cd /tools/Xilinx/Vivado_Lab/2019.2/data/xicom/cable_drivers/lin64/install_script/install_drivers
   $ ./install_drivers.sh

for Lab Edition, or

.. code-block:: bash

   $ cd /tools/Xilinx/Vivado/2019.2/data/xicom/cable_drivers/lin64/install_script/install_drivers
   $ ./install_drivers.sh

for Design Edition. Then change to the platform directory, and run:

.. code-block:: bash

   $ cd ($OCPI_CDK_DIR)/../projects/platform/hdl/platforms/zed_ether
   $ ./jtagSupport_zed_ether cables temp
   localhost:3121/xilinx_tcf/Digilent/210248B1880E=210248B1880E~

The text between the ``=`` and the ``~`` is the ESN (cable serial number),
``210248B1880E`` in this example, which is used for writing the ``system.xml``
file below. If this does not work, ensure that the cable drivers are installed
and that the USB cable is connected from the host PC to the PROG port on the
Zedboard.

Write a ``system.xml`` file specifying the system configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The configuration of an Ethernet-connected system is quite complex and cannot
be fully discovered at runtime by OpenCPI. However, the autodiscovery functionality
can be used to easily put together the ``system.xml`` file. Note that

Information you will need (note that properties are named from the FPGA's perspective):

* ID of the HDL device in the format ``Ether:<ifname>/<fpga_mac_addr>`` (found using
  ``ocpihdl search`` as described above)
* MAC address of the local interface (if using dual-Ethernet configuration,
  use the MAC address of the bonded interface) (found using ``ifconfig``)
* MAC address of the FPGA (discover using ``ocpihdl search`` as described in `Connect the host PC to the device`_)
* ``esn``: JTAG cable serial number (discover using Vivado, see above)

Optional configurable parameters:

* ``interface_mtu``: MTU used by the FPGA. This is independent of the MTU used by
  the PC and should be set to the actual MTU of the Ethernet hardware for best
  performance [default: 1500 bytes]
* ``ack_wait``: How long the FPGA waits before sending an ACK if there is no outgoing traffic
  [default: 187500 = 1.5ms @ 125MHz]
* ``max_acks_outstanding``: Maximum number of ACKs accumulated in the FPGA if there
  is no outgoing traffic [default: 32 packets]
* ``coalesce_wait``: How long the FPGA waits before sending a partially-empty frame
  (should be <= ack_wait). Set to zero to disable message coalescence
  [default: 125000 = 1ms @ 125MHz]
* ``dual_ethernet``: set to 1 to enable second Ethernet interface, or 0 otherwise
  [default: 0]
* ``remote_dst_id``: [default: 1]
* ``local_src_id``: [default: 1]

Wait parameters are clock cycles at the OpenCPI application clock rate, which is
125MHz for this platform.

An example ``system.xml`` file is shown below. To run an application, set the
``OCPI_SYSTEM_CONFIG`` environment variable to the path to this file as described
below, assuming that:

* The FPGA is connected on the ``bond0`` interface which has MAC address ``00:e0:4c:70:de:e2``
  (the configuration property requires this as a 48-bit hex number in network
  byte order: ``0x00e04c70dee2``)
* The FPGA's MAC address is ``80:1f:12:7c:79:04``
* The link MTU is configured to 8kB
* The cable ESN is ``210248B1880E``
* Dual-Ethernet is enabled
* All other parameters are left at their default values

.. code-block:: xml

   <opencpi>
      <container>
         <rcc load='1'/>
         <hdl load='1' discovery='static'>
            <device name="Ether:bond0/80:1f:12:7c:79:04" device="xc7z020" platform="zed_ether" esn="210248B1880E" static="true">
              <instance worker='dgrdma_config_dev'>
               <property name="remote_mac_addr_d" value="0x00e04c70dee2"/>
               <property name="interface_mtu_d" value="1500"/>
               <property name="dual_ethernet_d" value="1"/>
              </instance>
            </device>
         </hdl>
      </container>
      <transfer smbsize='128K'>
         <pio load='1'/>
         <datagram2-ether load='1'/>
      </transfer>
   </opencpi>

This selects the new ``datagram2`` transfer driver. This is a rewrite of the
existing ``datagram`` transfer driver to improve performance. It does not
implement some features of DG-RDMA which are not used by the FPGA implementation
(e.g. ACK generation). For more details, refer to the design documentation for
the ``datagram2`` driver at ``opencpi/runtime/xfer/drivers/datagram2/README.md``.

To use the old driver instead, replace the line

.. code-block:: xml

   <datagram2-ether load='1'/>

with

.. code-block:: xml

   <datagram-datagram_ether load='1'/>


Loading a bitstream via ``ocpihdl load`` (optional)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once you have a ``system.xml`` file which specifies the JTAG cable ESN, you can
use ``ocpihdl load`` to load a bitstream into the FPGA. This is not required to
run an applicaton (``ocpirun`` or an ACI application will automatically load the
FPGA bitstream is required), but may be useful to test the JTAG connection and to
do other low-level programming via ``ocpihdl``.

.. code-block:: bash

   $ ocpihdl load -d Ether:bond0/80:1f:12:7c:79:04 /path/to/artifact.bitz

Running an Application
----------------------
Ensure that you have a valid ``system.xml`` file. Ensure that  the following environment
variables are set:

.. csv-table:: Environment variables
   :header: "Name", "Value", "Remarks"
   :class: tight-table

   "``OCPI_ENABLE_HDL_NETWORK_DISCOVERY``", "1", "Required to find network devices"
   "``OCPI_ETHER_INTERFACE``", "name of local Ethernet interface", "Used by transfer driver"
   "``OCPI_MAX_ETHER_PAYLOAD_SIZE``", "MTU for packets sent by the PC", "Optional; if not present, the default (1498) will be used. This must not be set larger than the actual MTU configured in the Linux network interface."
   "``OCPI_SYSTEM_CONFIG``", "Path to ``system.xml``", "Required by OpenCPI framework"
   "``OCPI_LIBRARY_PATH``", "Colon-separated list of artifact paths", "Required by OpenCPI framework. dgrdma_config_proxy is in ocpi.core."

Now you can run the ``bias_loopback`` application created earlier:

.. code-block:: bash

   $ cd zed_ether_test/applications
   $ dd if=/dev/urandom of=in_file.bin bs=65536 count=1
   $ ocpirun -d -P bias=zed_ether loopback.xml
   $ diff in_file.bin out_file.bin

This configures the FPGA as a loopback. It creates a file ``in_file.bin``
containing 16kB of binary data and sends it to the FPGA, saving the result in
``out_file.bin`` (which should be identical). You can send a larger block
of data, e.g.

.. code-block:: bash

   $ dd if=/dev/urandom of=in_file.bin bs=65536 count=100

If OpenCPI reports that the HDL device is not found, ensure that:

* The USB cable is connected and the correct cable ESN is configured in ``system.xml``
* The Ethernet interface(s) are connected to the FPGA and up
* The correct Ethernet interface(s) and MAC address(es) are configured in ``system.xml``

The other applications in this directory can be used to make more detailed
performance measurements of the Ethernet link using the ``perftest`` HDL worker
(documentation TODO).

Troubleshooting
---------------

There are several things that need to be configured correctly for the Ethernet
interface to work. The recommended approach is to get the demo loopback
application working first, then use the same ``system.xml`` and environment to
run your real application (whether via ``ocpirun`` or as an ACI app).

**Problem: Vivado fails to program the FPGA, even though the JTAG USB cable is connected**

Determine whether the FPGA can be programmed *without* the FMC card attached. If
so, apply the PCB modification described in `Hardware prerequisites`_ above.

When the FPGA is configured and the Zedboard switches are all set to '0', LED[0]
should flash at about 1Hz (as long as the FMC card is connected - as all clocks
are derived from oscillators on the card).

**Problem: ocpihdl/ocpirun fails to program the FPGA**

* Ensure that the cable ESN is set in ``system.xml``
* Kill any stale Vivado hardware server process (`killall hw_server; killall cs_server`)
  before programming

**Problem: ocpihdl search does not find any devices**

* Check that the device is turned on, configured with an OpenCPI bitstream, and
  not in reset
* If using single-Ethernet connection:  check that Ethernet cable is connected to
  'Port 1' on the FMC card
* If using dual-Ethernet connection: check that both Ethernet cables are connected
  and the bonded interface is up
* Ensure that the FMC Ethernet card is properly connected, and the VAUX jumper on
  the Zedboard is correctly set to 2V5 (the red LED on the FMC card should be on).
* Ensure that you are running as root, or with the ``CAP_NET_RAW`` capability set
  on the executable (see `Software Prerequisites`_ above)
* Ensure that the ``OCPI_ENABLE_HDL_NETWORK_DISCOVERY`` environment variable is set
  to 1

If the above steps do not solve the problem, further debugging steps include:

* Set the ``OCPI_LOG_LEVEL`` environment variable to 10 before running ``ocpihdl``
  and look through the output for lines relating to the network interface in use
* Capture a Wireshark trace on the network interface. During ``ocpihdl search``
  you should see one outgoing DCP frame (``Ethertype=0xf040``) sent to the broadcast
  address ``ff:ff:ff:ff:ff:ff``, and one incoming frame from the FPGA.

  - Wireshark dissectors for DCP and DG-RDMA are in the main OpenCPI repo under
    ``tools/wireshark-dissectors``. Include these on your Wireshark plugin path to
    help debugging issues at the protocol level. This requires a build of Wireshark
    that supports Lua protocol dissectors. You can find the Lua plugin path by
    opening the Wireshark about box and looking in the 'Folders' tab
  - If the outgoing frame is not present, it is most likely a problem with the PC
    network configuration or the permissions on ``ocpihdl``.
  - If the response is not present, it is most likely a problem with the Ethernet
    connection or the FPGA configuration

**Problem: ocpirun fails opening raw socket**

E.g.

.. code-block:: bash

   $ ocpirun -d -P bias=zed_ether loopback.xml
   OCPI( 2:176.0297): HDL driver, got error opening static device: opening raw socket (Operation not permitted [1])
   Available containers are:  0: rcc0 [model: rcc os: linux platform: ubuntu18_04]

Run as root, or ensure that the ``CAP_NET_RAW`` capability is set on the ``ocpirun``
executable (or application executable, if using an ACI app).

**Problem: the test application starts, but no data is sent to or from the FPGA**

Check that:

* the ``OCPI_ETHER_INTERFACE`` is correctly set
* the ``remote_mac_addr_d`` property is set to the MAC address of the PC in
  ``system.xml``
* the ``interface_mtu_d`` property is set to a value supported by the PC's network
  interface (if in doubt, get things working with the default 1500 bytes before
  increasing).
* if set, the ``OCPI_MAX_ETHER_PAYLOAD_SIZE`` environment variable is set to a
  value less than or equal to the actual configured MTU of the PC network interface
  (if in doubt, get things working with the default 1500 bytes before increasing).

**Problem: the demo application works, but my application doesn't**

Check that:

* Your bitstream includes the ``dgrdma_config_dev`` device worker (by using the
  ``dgrdma_dev`` configuration or directly instantiating it in the container XML)
* Your application XML includes the ``ocpi.core.dgrdma_config_proxy`` worker

Using the zed_ether Platform with UDP transport
-----------------------------------------------
OpenCPI contains support for using DGRDMA with a UDP transport. By default DGRDMA packets are carried using raw Ethernet,
with the Ether Type field in the transport MAC layer being used to identify Control-Plane and Data-Plane packets.

When using UDP the same physical ethernet interface is used. However, at present dual ethernet operation is not
supported.  Only packets sent to the zed_ether hardware with Ether-Type IP (0x0800) and ARP (0x0806) are processed.
Packets with other Ether-Types values are ignored. The UDP Port number is used to distinguish between Control-Plane and Data-Plane packets.
Packets sent to other UDP ports will be ignored by the zed_ether hardware.

The ethernet / UDP components used in the FPGA filter received packets based on destination MAC address, IP destination address 
and destination UDP port. 

Packets with the following MAC destination addresses will be processed:
   - Destination MAC = LOCAL_MAC_ADDR 
   - Destination MAC = Broadcast MAC (0xffffffffffff)
   - Destination MAC in multicast address group (01-00-5E-00-00-00 through 01-00-5E-7F-FF-FF)

Packets with the following IP destination addresses will be processed:
   - Destination IP Address = LOCAL_IP_ADDR
   - Destination IP Address = multicast group (224.0.0.0 to 224.255.255.255)

Note the FPGA components do not "join" a multicast group. Care has to be taken in the network as the FPGA will process
packets sent to the multicast Destination MAC / multicast IP Address / UDP Port = 18077 if these packets are present on the
ethernet link connected to the zed_ether.

By default the zed_ether platform uses the following port numbers:
  
.. csv-table:: UDP Port Mapping
   :header: "Port Number", "Remarks"
   :class: tight-table

   "`18077`", "Control Plane UDP Port (destination UDP port of packets sent to the hardware)"
   "`18078`", "Data Plane UDP Port (destination UDP port of Data-Plane packets sent to the hardware)"

The PC's network interface used for communicating with the hardware needs to be assigned an IP address.
For example:

.. code-block::

   ip addr add 192.168.50.1/24 dev enp4s0f0

The platform dgrdma config device will need its ``remote_ip_addr_d`` property set to this address in the system.xml file.

The following additional environment variables also need to be specified:

.. csv-table:: UDP Environment variables
   :header: "Name", "Value", "Remarks"
   :class: tight-table

   "`OCPI_TRANSFER_IP_ADDRESS`", "192.168.50.1", "Specifies the local PC network interface to use"
   "`OCPI_UDP_TRANSFER_PORT`", "41000", "Specifies the PC's UDP port number"

The port number specified by ``OCPI_UDP_TRANSFER_PORT`` is used by the OpenCPI runtime software to listen for
Data-Plane packets sent to it by the hardware. It is also the port from which Data-Plane packets are
sent to the hardware. The platform dgrdma config device ``remote_udp_port_d`` property needs to be set to
the same value in the system.xml file.

The use of UDP transport is specified in the system.xml file being used by the running application.
An example system.xml for use with UDP is shown below:

.. code-block:: xml

   <opencpi>
      <container>
         <rcc load="1"/>
         <hdl load='1' discovery="static">
            <device name="udp:192.168.50.2:18077" device="xc7k410t" platform="zed_ether" esn="2516350FA134A" static="true">
               <instance worker='dgrdma_config_dev'>
                  <property name="dual_ethernet_d"   value="0" />
                  <property name="remote_mac_addr_d" value="0x90e2bad43a98"/>
                  <Property name="remote_ip_addr_d"  value="0xc0a83201"/>
                  <Property name="remote_udp_port_d" value="41000"/>
                  <Property name="interface_mtu_d"   value="1400"/>
               </instance>
            </device>
         </hdl>
      </container>
      <transfer smbsize="10M">
         <datagram2-ether load="1"/>
      </transfer>
   </opencpi>

The device name "udp:192.168.50.2:18077" specifies that UDP transport is to be used by the HDL container,
the destination (zed_ether) IP address to send packets to is "192.168.50.2" and the port number
to send Control-Plane packets to it 18077. Data-Plane packets will be sent to 18078.
The device, platform, esn and static values are used in the same way as for the raw Ethernet case.

The dgrdma config device properties specified in the system.xml are:

+----------------------+-----------------------+-------------------------------------------------------+
| Property             | Value                 | Usage                                                 |
+======================+=======================+=======================================================+
| dual_ethernet_d      | 0                     | Specifies single ethernet interface is to be used.    |
|                      |                       | Dual ethernet operation is not supported for UDP      |
+----------------------+-----------------------+-------------------------------------------------------+
| remote_mac_addr_d    | 0x90e2bad43a98        | The MAC address of the PC ethernet interface.         |
|                      |                       | The hardware sends Data-Plane packets to this         |
|                      |                       | address                                               |
+----------------------+-----------------------+-------------------------------------------------------+
| remote_ip_addr_d     | 0xc0a83201            | The IP address of the PC ethernet interface.          |
|                      |                       | The hardware sends Data-Plane packets to this         |
|                      |                       | address                                               |
+----------------------+-----------------------+-------------------------------------------------------+
| remote_udp_port_d    | 41000                 | The UDP Port the PC listens on for Data-Plane packets |
|                      |                       | This must match the value specified by                |
|                      |                       | OCPI_UDP_TRANSFER_PORT                                |
+----------------------+-----------------------+-------------------------------------------------------+
| interface_mtu_d      | 1400                  | This value is used by the FPGA when packing           |
|                      |                       | DGRDMA messages into UDP packets.                     |
|                      |                       | Its value needs to be <actual-MTU> - IP header size - |
|                      |                       | UDP header size                                       |
+----------------------+-----------------------+-------------------------------------------------------+

Note that the hardware IP address, sub-net mask and default gateway are manually assigned and are hardcoded into the
FPGA bit-stream. These values are set by constants in the platform worker
(``ocpi_root_dir/projects/platform/hdl/platforms/zed_ether/zed_ether.vhd``).  The zed_ether (UDP) implementation
includes an ARP implementation. This is used to obtain the MAC address of the ethernet interface sending it
Control-Plane commands.

The default value for these parameters are:

+----------------------+-----------------------+-------------------------------------------------------+
| Parameter            | Value                 | Usage                                                 |
+======================+=======================+=======================================================+
| LOCAL_MAC_ADDR       | 0x0050c2853fff        | The MAC address of the zed_ether ethernet interface   |
+----------------------+-----------------------+-------------------------------------------------------+
| LOCAL_IP_ADDR        | 192.168.50.2          | The IP address of the zed_ether ethernet interface    |
+----------------------+-----------------------+-------------------------------------------------------+
| LOCAL_SUBNET_MASK    | 255.255.255.0         | The subnet mask of the zed_ether ethernet interface   |
+----------------------+-----------------------+-------------------------------------------------------+
| LOCAL_GATEWAY_IP     | 192.168.50.1          | The subnet mask of the zed_ether ethernet interface   |
+----------------------+-----------------------+-------------------------------------------------------+
| UDP_CP_PORT          | 18077                 | Control-Plane UDP Port Number                         |
+----------------------+-----------------------+-------------------------------------------------------+
| UDP_SDP_PORT         | 18078                 | Data-Plane UDP Port Number                            |
+----------------------+-----------------------+-------------------------------------------------------+

A bit-stream that supports UDP transport needs to be built. The use of UDP is enabled by setting
the platform property ``udp_enable`` to ``true`` in a platform configuration.  Additionally
``sdp_width`` must be ``1`` (not ``2`` or ``4``), as per the valid build configurations in
``zed_ether-build.xml``.

The application does not need to include anything UDP specific in its .xml file in order
to use UDP transport. The same applications can be used for raw Ethernet and UDP transports.
However, care needs to be taken to ensure that artifacts (bit-streams) do not exist for both
raw Ethernet and UDP transports containing the same assembly, as this can result in the
OpenCPI framework selected the wrong bit-stream, and communication between the zed_ether FPGA
and the PC software will fail.

Known Issues
------------
