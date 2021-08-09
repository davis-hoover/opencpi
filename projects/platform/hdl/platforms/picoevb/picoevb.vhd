-- This file is protected by Copyright. Please refer to the COPYRIGHT file
-- distributed with this source distribution.
--
-- This file is part of OpenCPI <http://www.opencpi.org>
--
-- OpenCPI is free software: you can redistribute it and/or modify it under the
-- terms of the GNU Lesser General Public License as published by the Free
-- Software Foundation, either version 3 of the License, or (at your option) any
-- later version.
--
-- OpenCPI is distributed in the hope that it will be useful, but WITHOUT ANY
-- WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
-- A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
-- details.
--
-- You should have received a copy of the GNU Lesser General Public License
-- along with this program. If not, see <http://www.gnu.org/licenses/>.

library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library ocpi; use ocpi.types.all; -- remove this to avoid all ocpi name collisions
library platform; use platform.pci_pkg.all, platform.platform_pkg.all;
library axi;
library generic_pcie; use generic_pcie.generic_pcie_pkg.all;
library unisim; use unisim.vcomponents.all;
library sdp; use sdp.sdp.all;

architecture rtl of worker is
  -- user/app clock and reset
  signal clk               : std_logic;
  signal reset             : std_logic;
  signal reset_n           : std_logic;
  signal sys_clk           : std_logic;

  --
  signal global_in         : global_in_t;
  signal global_out        : global_out_t;
  signal msi_in            : msi_in_t;
  signal msi_out           : msi_out_t;
  signal pcie_in           : pcie_in_t;
  signal pcie_out          : pcie_out_t;
  
  -- AXI interfaces
  -- Master
  signal m_axi_in          : axi.pcie_m.axi_s2m_t;  -- Control plane
  signal m_axi_out         : axi.pcie_m.axi_m2s_t;  -- Control plane
  -- Slave
  signal s_axi_in          : axi.pcie_s.axi_m2s_t;  -- Data plane
  signal s_axi_out         : axi.pcie_s.axi_s2m_t;  -- Data plane

  -- General IO/Debug signals
  signal fast_count        : std_logic_vector(31 downto 0) := (others => '0');
  signal slow_count        : std_logic_vector(3 downto 0) := (others => '0');

  signal my_sdp_out        : interconnect_out_array_t;
  signal my_sdp_out_data   : interconnect_out_data_array_t;

  signal dbg_state         : ulonglong_array_t(0 to 3);
  signal dbg_state1        : ulonglong_array_t(0 to 3);
  signal dbg_state2        : ulonglong_array_t(0 to 3);

begin

-- -------------------------------------------
-- clocks/resets etc.
-- -------------------------------------------
  
-- Drive metadata interface - boiler plate
metadata_out.clk     <= clk;
metadata_out.romAddr <= props_in.romAddr;
metadata_out.romEn   <= props_in.romData_read;

-- Drive timekeepping interface - depends on which clock, and whether there is a PPS input
timebase_out.clk      <= clk;
timebase_out.PPS      <= '0';
timebase_out.usingPPS <= '0'; -- When not using PPS, drive usingPPS low

-- MSI related signals inputs.  Currently unused.
msi_in.intx_msi_request <= '0';
msi_in.msi_vector_num   <= "00000";

-- --------------------------------------------
-- PCIe pcie reference and perstn connections :
-- --------------------------------------------
--    Note: This differential IO buffer must be explicitly instantiated per the
-- Xilinx 7 Series FPGAs GTX/GTH Transceivers User Guide

-- (* LOC="IBUFDS_GTE2_X0Y0" *)
pcie_ref_clk_buffer : IBUFDS_GTE2
  generic map (
    CLKCM_CFG    => true,
    CLKRCV_TRST  => true,
    CLKSWING_CFG => "11"
  ) 
  port map (
    O     => sys_clk,
    CEB   => '0',      
    I     => sys_clkp,
    IB    => sys_clkn
  );

global_in.refclk      <= sys_clk;   -- 100Mhz reference input clock
global_in.axi_aresetn <= sys_rst_n; -- perst_n

-- PCIe transceiver connections
pcie_in.pcie_rxp(0) <= pcie_rxp;
pcie_in.pcie_rxn(0) <= pcie_rxn;
pcie_txp            <= pcie_out.pcie_txp(0);
pcie_txn            <= pcie_out.pcie_txn(0);

bridge_pcie_axi : generic_pcie.generic_pcie_pkg.generic_pcie
  generic map(
    VENDOR_ID  => pci_vendor_id_c, -- the vendor ID for OpenCPI
    DEVICE_ID  => pci_device_id_t'pos(pci_device_id), -- the enum value from the OWD
    CLASS_CODE => pci_class_code_c -- the pci class code for OpenCPI
  )
  port map(
    -- 
    axi_clk     => clk,
    axi_resetn  => open, --reset_n,
    axi_reset   => reset,

    pcie_in     => pcie_in,
    pcie_out    => pcie_out,

    global_in   => global_in,
    global_out  => global_out,

    msi_in      => msi_in,
    msi_out     => msi_out,

    -- Master (x1)
    m_axi_in    => m_axi_in,
    m_axi_out   => m_axi_out,
    -- Slave (x1)
    s_axi_in    => s_axi_in,
    s_axi_out   => s_axi_out
  );

interconnect_out       <= my_sdp_out;
interconnect_out_data  <= my_sdp_out_data; 
props_out.sdpDropCount <= interconnect_in(0).dropCount;

-- We use one sdp2axi adapter foreach of the pcie's slave axi channels
dp : axi.pcie_s.sdp2axi_pcie_s
  generic map(
    ocpi_debug => true,
    sdp_width  => to_integer(sdp_width)
  )
  port map(
    clk          => clk,
    reset        => reset,
    sdp_in       => interconnect_in(0),
    sdp_in_data  => interconnect_in_data(0),
    sdp_out      => my_sdp_out(0),
    sdp_out_data => my_sdp_out_data(0),
    axi_in       => s_axi_out,
    axi_out      => s_axi_in,
    axi_error    => props_out.axi_error(0),
    dbg_state    => dbg_state(0),
    dbg_state1   => dbg_state1(0),
    dbg_state2   => dbg_state2(0)
   );

-- Adapt the axi master from the pcie I/F to be a CP Master
cp : axi.pcie_m.axi2cp_pcie_m
  port map(
    clk     => clk,
    reset   => reset,
    axi_in  => m_axi_out, -- criss-cross
    axi_out => m_axi_in,
    cp_in   => cp_in,
    cp_out  => cp_out
  );
cp_out.clk   <= clk;
--cp_out.reset <= reset;

-- Output/readable properties
props_out.dna             <= (others => '0');
props_out.switches        <= (others => '0');
props_out.memories_length <= to_ulong(1);
props_out.memories        <= (others => to_ulong(0));
props_out.UUID            <= metadata_in.UUID;
props_out.romData         <= metadata_in.romData;

-- Counter for blinking LED
watchdog_count : process(clk)
begin
  if rising_edge(clk) then
    if (reset = '1') then
      fast_count <= (others => '0'); 
      slow_count <= (others => '0');
    else
      if (fast_count = x"01DC_D650") then
        fast_count <= x"0000_0000";
        slow_count <= std_logic_vector(unsigned(slow_count) + 1);
      else 
        fast_count <= std_logic_vector(unsigned(fast_count) + 1); 
        slow_count <= slow_count;
      end if;
    end if;
   end if;
end process;

-- Visual indicator that the platform is alive.
leds(0)  <= slow_count(0) and global_out.user_link_up; -- Fast LED will only blink after the link is established.
leds(1)  <= slow_count(1);
leds(2)  <= slow_count(2);

clkreq_n <= '0';


end rtl;
