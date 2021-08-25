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

--------------------------------------------------------------------------------
-- Generalized module for pcie based FPGA platforms
--------------------------------------------------------------------------------

library IEEE; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library axi;
library generic_pcie; use generic_pcie.generic_pcie_pkg.all;
library unisim; use unisim.vcomponents.all;
library cdc;

entity generic_pcie is
  generic (
      VENDOR_ID   : natural;
      DEVICE_ID   : natural;
      CLASS_CODE  : natural
  );
  port (
    axi_clk     : out std_logic;
    axi_resetn  : out std_logic;
    axi_reset   : out std_logic;

    pcie_in     : in  pcie_in_t;
    pcie_out    : out pcie_out_t;

    global_in   : in  global_in_t;
    global_out  : out global_out_t;

    msi_in      : in  msi_in_t;
    msi_out     : out msi_out_t;

    -- Master (x1)
    m_axi_in  : in  axi.pcie_m.axi_s2m_t;
    m_axi_out : out axi.pcie_m.axi_m2s_t;
    -- Slave (x1)
    s_axi_in  : in  axi.pcie_s.axi_m2s_t;
    s_axi_out : out axi.pcie_s.axi_s2m_t
  );
end entity generic_pcie;

architecture rtl of generic_pcie is
  -- We need this unfortunate redundant component declaration for two reasons:
  -- 1. Vivado claims that you must have a component declaration to instance verilog from vhdl
  -- 2. This relieves any ordering dependency between the verilog module and this file.

component axi_pcie_0
  port (
    axi_aresetn       : in std_logic;
    user_link_up      : out STD_LOGIC;
    axi_aclk_out      : out std_logic;
    axi_ctl_aclk_out  : out std_logic;
    mmcm_lock         : out std_logic;
    interrupt_out     : out std_logic;
    INTX_MSI_Request  : in std_logic;
    INTX_MSI_Grant    : out std_logic;
    MSI_enable        : out std_logic;
    MSI_Vector_Num    : in std_logic_vector(4 downto 0);
    MSI_Vector_Width  : out std_logic_vector(2 downto 0);
    s_axi_awid        : in std_logic_vector(5 downto 0);
    s_axi_awaddr      : in std_logic_vector(31 downto 0);
    s_axi_awregion    : in std_logic_vector(3 downto 0);
    s_axi_awlen       : in std_logic_vector(7 downto 0);
    s_axi_awsize      : in std_logic_vector(2 downto 0);
    s_axi_awburst     : in std_logic_vector(1 downto 0);
    s_axi_awvalid     : in std_logic;
    s_axi_awready     : out std_logic;
    s_axi_wdata       : in std_logic_vector(63 downto 0);
    s_axi_wstrb       : in std_logic_vector(7 downto 0);
    s_axi_wlast       : in std_logic;
    s_axi_wvalid      : in std_logic;
    s_axi_wready      : out std_logic;
    s_axi_bid         : out std_logic_vector(5 downto 0);
    s_axi_bresp       : out std_logic_vector(1 downto 0);
    s_axi_bvalid      : out std_logic;
    s_axi_bready      : in std_logic;
    s_axi_arid        : in std_logic_vector(5 downto 0);
    s_axi_araddr      : in std_logic_vector(31 downto 0);
    s_axi_arregion    : in std_logic_vector(3 downto 0);
    s_axi_arlen       : in std_logic_vector(7 downto 0);
    s_axi_arsize      : in std_logic_vector(2 downto 0);
    s_axi_arburst     : in std_logic_vector(1 downto 0);
    s_axi_arvalid     : in std_logic;
    s_axi_arready     : out std_logic;
    s_axi_rid         : out std_logic_vector(5 downto 0);
    s_axi_rdata       : out std_logic_vector(63 downto 0);
    s_axi_rresp       : out std_logic_vector(1 downto 0);
    s_axi_rlast       : out std_logic;
    s_axi_rvalid      : out std_logic;
    s_axi_rready      : in std_logic;
    m_axi_awaddr      : out std_logic_vector(31 downto 0);
    m_axi_awlen       : out std_logic_vector(7 downto 0);
    m_axi_awsize      : out std_logic_vector(2 downto 0);
    m_axi_awburst     : out std_logic_vector(1 downto 0);
    m_axi_awprot      : out std_logic_vector(2 downto 0);
    m_axi_awvalid     : out std_logic;
    m_axi_awready     : in std_logic;
    m_axi_awlock      : out std_logic;
    m_axi_awcache     : out std_logic_vector(3 downto 0);
    m_axi_wdata       : out std_logic_vector(63 downto 0);
    m_axi_wstrb       : out std_logic_vector(7 downto 0);
    m_axi_wlast       : out std_logic;
    m_axi_wvalid      : out std_logic;
    m_axi_wready      : in std_logic;
    m_axi_bresp       : in std_logic_vector(1 downto 0);
    m_axi_bvalid      : in std_logic;
    m_axi_bready      : out std_logic;
    m_axi_araddr      : out std_logic_vector(31 downto 0);
    m_axi_arlen       : out std_logic_vector(7 downto 0);
    m_axi_arsize      : out std_logic_vector(2 downto 0);
    m_axi_arburst     : out std_logic_vector(1 downto 0);
    m_axi_arprot      : out std_logic_vector(2 downto 0);
    m_axi_arvalid     : out std_logic;
    m_axi_arready     : in std_logic;
    m_axi_arlock      : out std_logic;
    m_axi_arcache     : out std_logic_vector(3 downto 0);
    m_axi_rdata       : in std_logic_vector(63 downto 0);
    m_axi_rresp       : in std_logic_vector(1 downto 0);
    m_axi_rlast       : in std_logic;
    m_axi_rvalid      : in std_logic;
    m_axi_rready      : out std_logic;
    pci_exp_txp       : out std_logic_vector(0 downto 0);
    pci_exp_txn       : out std_logic_vector(0 downto 0);
    pci_exp_rxp       : in std_logic_vector(0 downto 0);
    pci_exp_rxn       : in std_logic_vector(0 downto 0);
    REFCLK            : in std_logic;
    s_axi_ctl_awaddr  : in std_logic_vector(31 downto 0);
    s_axi_ctl_awvalid : in std_logic;
    s_axi_ctl_awready : out std_logic;
    s_axi_ctl_wdata   : in std_logic_vector(31 downto 0);
    s_axi_ctl_wstrb   : in std_logic_vector(3 downto 0);
    s_axi_ctl_wvalid  : in std_logic;
    s_axi_ctl_wready  : out std_logic;
    s_axi_ctl_bresp   : out std_logic_vector(1 downto 0);
    s_axi_ctl_bvalid  : out std_logic;
    s_axi_ctl_bready  : in std_logic;
    s_axi_ctl_araddr  : in std_logic_vector(31 downto 0);
    s_axi_ctl_arvalid : in std_logic;
    s_axi_ctl_arready : out std_logic;
    s_axi_ctl_rdata   : out std_logic_vector(31 downto 0);
    s_axi_ctl_rresp   : out std_logic_vector(1 downto 0);
    s_axi_ctl_rvalid  : out std_logic;
    s_axi_ctl_rready : in std_logic
  );
end component;

component axi_dwidth_converter_0
  port (
    s_axi_aclk        : in std_logic;
    s_axi_aresetn     : in std_logic;
    s_axi_awid        : in std_logic_vector(5 downto 0);
    s_axi_awaddr      : in std_logic_vector(31 downto 0);
    s_axi_awlen       : in std_logic_vector(7 downto 0);
    s_axi_awsize      : in std_logic_vector(2 downto 0);
    s_axi_awburst     : in std_logic_vector(1 downto 0);
    s_axi_awlock      : in std_logic_vector(0 downto 0);
    s_axi_awcache     : in std_logic_vector(3 downto 0);
    s_axi_awprot      : in std_logic_vector(2 downto 0);
    s_axi_awregion    : in std_logic_vector(3 downto 0);
    s_axi_awqos       : in std_logic_vector(3 downto 0);
    s_axi_awvalid     : in std_logic;
    s_axi_awready     : out std_logic;
    s_axi_wdata       : in std_logic_vector(63 downto 0);
    s_axi_wstrb       : in std_logic_vector(7 downto 0);
    s_axi_wlast       : in std_logic;
    s_axi_wvalid      : in std_logic;
    s_axi_wready      : out std_logic;
    s_axi_bid         : out std_logic_vector(5 downto 0);
    s_axi_bresp       : out std_logic_vector(1 downto 0);
    s_axi_bvalid      : out std_logic;
    s_axi_bready      : in std_logic;
    s_axi_arid        : in std_logic_vector(5 downto 0);
    s_axi_araddr      : in std_logic_vector(31 downto 0);
    s_axi_arlen       : in std_logic_vector(7 downto 0);
    s_axi_arsize      : in std_logic_vector(2 downto 0);
    s_axi_arburst     : in std_logic_vector(1 downto 0);
    s_axi_arlock      : in std_logic_vector(0 downto 0);
    s_axi_arcache     : in std_logic_vector(3 downto 0);
    s_axi_arprot      : in std_logic_vector(2 downto 0);
    s_axi_arregion    : in std_logic_vector(3 downto 0);
    s_axi_arqos       : in std_logic_vector(3 downto 0);
    s_axi_arvalid     : in std_logic;
    s_axi_arready     : out std_logic;
    s_axi_rid         : out std_logic_vector(5 downto 0);
    s_axi_rdata       : out std_logic_vector(63 downto 0);
    s_axi_rresp       : out std_logic_vector(1 downto 0);
    s_axi_rlast       : out std_logic;
    s_axi_rvalid      : out std_logic;
    s_axi_rready      : in std_logic;
    m_axi_awaddr      : out std_logic_vector(31 downto 0);
    m_axi_awlen       : out std_logic_vector(7 downto 0);
    m_axi_awsize      : out std_logic_vector(2 downto 0);
    m_axi_awburst     : out std_logic_vector(1 downto 0);
    m_axi_awlock      : out std_logic_vector(0 downto 0);
    m_axi_awcache     : out std_logic_vector(3 downto 0);
    m_axi_awprot      : out std_logic_vector(2 downto 0);
    m_axi_awregion    : out std_logic_vector(3 downto 0);
    m_axi_awqos       : out std_logic_vector(3 downto 0);
    m_axi_awvalid     : out std_logic;
    m_axi_awready     : in std_logic;
    m_axi_wdata       : out std_logic_vector(31 downto 0);
    m_axi_wstrb       : out std_logic_vector(3 downto 0);
    m_axi_wlast       : out std_logic;
    m_axi_wvalid      : out std_logic;
    m_axi_wready      : in std_logic;
    m_axi_bresp       : in std_logic_vector(1 downto 0);
    m_axi_bvalid      : in std_logic;
    m_axi_bready      : out std_logic;
    m_axi_araddr      : out std_logic_vector(31 downto 0);
    m_axi_arlen       : out std_logic_vector(7 downto 0);
    m_axi_arsize      : out std_logic_vector(2 downto 0);
    m_axi_arburst     : out std_logic_vector(1 downto 0);
    m_axi_arlock      : out std_logic_vector(0 downto 0);
    m_axi_arcache     : out std_logic_vector(3 downto 0);
    m_axi_arprot      : out std_logic_vector(2 downto 0);
    m_axi_arregion    : out std_logic_vector(3 downto 0);
    m_axi_arqos       : out std_logic_vector(3 downto 0);
    m_axi_arvalid     : out std_logic;
    m_axi_arready     : in std_logic;
    m_axi_rdata       : in std_logic_vector(31 downto 0);
    m_axi_rresp       : in std_logic_vector(1 downto 0);
    m_axi_rlast       : in std_logic;
    m_axi_rvalid      : in std_logic;
    m_axi_rready      : out std_logic
  );
end component;


-- ------------------------------------------------
-- Accommodate for internal differences in ID width 
-- ------------------------------------------------

-- Data Width adaptation signals (converts m_axi_in/out 64-bits to 32-bits)
-- axi_pcie's m_axi_in/out interface connects to the slave side of the axi_dwidth_converter_0 module
signal m_axi_in_int  : axi.pcie_s.axi_s2m_t; -- slave side is 64bit data width
signal m_axi_out_int : axi.pcie_s.axi_m2s_t; --

signal axi_clk_int   : std_logic;
signal reset_n_int   : std_logic;

signal mmcm_lock_int : std_logic;
-- signal axi_aclk_int  : std_logic;
signal axi_aclk      : std_logic;

signal reset_sync    : std_logic;
signal reset_n_sync  : std_logic;

begin

-- ------------------------------------------------
m_axi_out.A.RESETn <= reset_n_sync;
m_axi_out.A.CLK    <= axi_aclk;

--s_axi_out.A.RESETn <= reset_n_sync;
--s_axi_out.A.CLK    <= axi_aclk;

axi_clk    <= axi_aclk;
axi_resetn <= reset_n_sync;
axi_reset  <= reset_sync;

-- -- ------------------------------------------------
-- -- Use a global clock buffer for this clock used for both control and data
-- clkbuf : BUFG 
--   port map( 
--     I => axi_aclk_int,
--     O => axi_aclk
-- );

sr : cdc.cdc.reset
  generic map(
    SRC_RST_VALUE => '0',
    RST_DELAY => 17 
  )
  port map (
    src_rst   => mmcm_lock_int,
    dst_clk   => axi_aclk,
    dst_rst   => reset_sync,
    dst_rst_n => reset_n_sync
);

--
-- Width Adaptation 
--
adapt_64m_to_32s : axi_dwidth_converter_0
  PORT MAP (
    s_axi_aclk     => axi_aclk,
    s_axi_aresetn  => reset_n_sync,
    --
    --
    s_axi_awid     => (others => '0'),
    s_axi_awaddr   => m_axi_out_int.AW.ADDR,
    s_axi_awregion => (others => '0'),
    s_axi_awlen    => m_axi_out_int.AW.LEN,
    s_axi_awsize   => m_axi_out_int.AW.SIZE,
    s_axi_awburst  => m_axi_out_int.AW.BURST,
    s_axi_awlock   => m_axi_out_int.AW.LOCK(0 to 0),
    s_axi_awcache  => m_axi_out_int.AW.CACHE,
    s_axi_awprot   => m_axi_out_int.AW.PROT,
    s_axi_awqos    => (others => '0'),
    s_axi_awvalid  => m_axi_out_int.AW.VALID,
    s_axi_awready  => m_axi_in_int.AW.READY,
    --
    -- AXI Slave Write Address Channel
    s_axi_wdata    => m_axi_out_int.W.DATA,
    s_axi_wstrb    => m_axi_out_int.W.STRB,
    s_axi_wlast    => m_axi_out_int.W.LAST,
    s_axi_wvalid   => m_axi_out_int.W.VALID,
    s_axi_wready   => m_axi_in_int.W.READY,
    --
    -- AXI Slave Write Response Channel
    s_axi_bid      => open, 
    s_axi_bresp    => m_axi_in_int.B.RESP,
    s_axi_bvalid   => m_axi_in_int.B.VALID,
    s_axi_bready   => m_axi_out_int.B.READY,
    --
    -- AXI Slave Read Address Channel
    s_axi_arid     => (others => '0'),
    s_axi_araddr   => m_axi_out_int.AR.ADDR,
    s_axi_arlen    => m_axi_out_int.AR.LEN,
    s_axi_arsize   => m_axi_out_int.AR.SIZE,
    s_axi_arburst  => m_axi_out_int.AR.BURST,
    s_axi_arlock   => m_axi_out_int.AR.LOCK(0 to 0),
    s_axi_arcache  => m_axi_out_int.AR.CACHE,
    s_axi_arprot   => m_axi_out_int.AR.PROT,
    s_axi_arregion => (others => '0'),
    s_axi_arqos    => (others => '0'),
    s_axi_arvalid  => m_axi_out_int.AR.VALID,
    s_axi_arready  => m_axi_in_int.AR.READY,
    --
    -- AXI Slave Read Data Channel
    s_axi_rid      => open,
    s_axi_rdata    => m_axi_in_int.R.DATA,
    s_axi_rresp    => m_axi_in_int.R.RESP,
    s_axi_rlast    => m_axi_in_int.R.LAST,
    s_axi_rvalid   => m_axi_in_int.R.VALID,
    s_axi_rready   => m_axi_out_int.R.READY,
    --
    -- AXI Master Write Address Channel
    m_axi_awaddr   => m_axi_out.AW.ADDR,
    m_axi_awlen    => m_axi_out.AW.LEN,
    m_axi_awsize   => m_axi_out.AW.SIZE,
    m_axi_awburst  => m_axi_out.AW.BURST,
    m_axi_awlock   => m_axi_out.AW.LOCK(0 to 0),
    m_axi_awcache  => m_axi_out.AW.CACHE,
    m_axi_awprot   => m_axi_out.AW.PROT,
    m_axi_awregion => m_axi_out.AW.REGION,
    m_axi_awqos    => m_axi_out.AW.QOS,
    m_axi_awvalid  => m_axi_out.AW.VALID,
    m_axi_awready  => m_axi_in.AW.READY,
    --
    -- AXI Master Write Data Channel
    m_axi_wdata    => m_axi_out.W.DATA,
    m_axi_wstrb    => m_axi_out.W.STRB,
    m_axi_wlast    => m_axi_out.W.LAST,
    m_axi_wvalid   => m_axi_out.W.VALID,
    m_axi_wready   => m_axi_in.W.READY,
    --
    -- AXI Master Write Response Channel
    m_axi_bresp    => m_axi_in.B.RESP,
    m_axi_bvalid   => m_axi_in.B.VALID,
    m_axi_bready   => m_axi_out.B.READY,
    --
    -- AXI Master Read Address Channel
    m_axi_araddr   => m_axi_out.AR.ADDR,
    m_axi_arlen    => m_axi_out.AR.LEN,
    m_axi_arsize   => m_axi_out.AR.SIZE,
    m_axi_arburst  => m_axi_out.AR.BURST,
    m_axi_arprot   => m_axi_out.AR.PROT,
    m_axi_arregion => m_axi_out.AR.REGION,
    m_axi_arqos    => m_axi_out.AR.QOS,
    m_axi_arvalid  => m_axi_out.AR.VALID,
    m_axi_arready  => m_axi_in.AR.READY,
    m_axi_arlock   => m_axi_out.AR.LOCK(0 to 0),
    m_axi_arcache  => m_axi_out.AR.CACHE,
    --
    -- AXI Master Read Data Channel
    m_axi_rdata    => m_axi_in.R.DATA,
    m_axi_rresp    => m_axi_in.R.RESP,
    m_axi_rlast    => m_axi_in.R.LAST,
    m_axi_rvalid   => m_axi_in.R.VALID,
    m_axi_rready   => m_axi_out.R.READY
  );


  axi_pcie_inst : axi_pcie_0 
  port map (

    -- PCI Express (pci_exp) Interface
    -- Tx
    pci_exp_txp => pcie_out.pcie_txp,
    pci_exp_txn => pcie_out.pcie_txn,
    -- Rx
    pci_exp_rxp => pcie_in.pcie_rxp,
    pci_exp_rxn => pcie_in.pcie_rxn,

    -- AXI Global
    REFCLK            => global_in.refclk,
--  axi_aclk          => global_in.axi_aclk,       -- AXI clock
    axi_aresetn       => global_in.axi_aresetn,    -- AXI active low synchronous reset
    axi_aclk_out      => axi_aclk, --axi_aclk_int,             -- 
--  axi_ctl_aclk      => global_in.axi_ctl_aclk,   -- AXI LITE clock
    axi_ctl_aclk_out  => global_out.axi_ctl_aclk_out,  -- PCIe clock for AXI LITE clock
    mmcm_lock         => mmcm_lock_int,            -- 
    interrupt_out     => global_out.interrupt_out, -- active high interrupt out
    user_link_up      => global_out.user_link_up,  -- Indicates PCIe link is in L0 state
    INTX_MSI_Request  => msi_in.intx_msi_request,  -- Legacy interrupt/initiate MSI (Endpoint only)
    INTX_MSI_Grant    => msi_out.intx_msi_grant,   -- Legacy interrupt/MSI Grant signal (Endpoint only)
    MSI_enable        => msi_out.msi_enable,       -- 1 = MSI, 0 = INTX
    MSI_Vector_Num    => msi_in.msi_vector_num,    -- 
    MSI_Vector_Width  => msi_out.msi_vector_width, -- 
    --
    -- AXI Slave Write Address Channel
    s_axi_awid        => s_axi_in.AW.ID,
    s_axi_awaddr      => s_axi_in.AW.ADDR,
    s_axi_awregion    => s_axi_in.AW.REGION,
    s_axi_awlen       => s_axi_in.AW.LEN,
    s_axi_awsize      => s_axi_in.AW.SIZE,
    s_axi_awburst     => s_axi_in.AW.BURST,
    s_axi_awvalid     => s_axi_in.AW.VALID,
    s_axi_awready     => s_axi_out.AW.READY,
    --
    -- AXI Slave Write Data Channel
    s_axi_wdata       => s_axi_in.W.DATA,
    s_axi_wstrb       => s_axi_in.W.STRB,
    s_axi_wlast       => s_axi_in.W.LAST,
    s_axi_wvalid      => s_axi_in.W.VALID,
    s_axi_wready      => s_axi_out.W.READY,
    --
    -- AXI Slave Write Response Channel
    s_axi_bid         => s_axi_out.B.ID,
    s_axi_bresp       => s_axi_out.B.RESP,
    s_axi_bvalid      => s_axi_out.B.VALID,
    s_axi_bready      => s_axi_in.B.READY,
    --
    -- AXI Slave Read Address Channel
    s_axi_arid        => s_axi_in.AR.ID,
    s_axi_araddr      => s_axi_in.AR.ADDR,
    s_axi_arregion    => (others => '0'), --s_axi_in.AR.REGION,
    s_axi_arlen       => s_axi_in.AR.LEN,
    s_axi_arsize      => s_axi_in.AR.SIZE,
    s_axi_arburst     => s_axi_in.AR.BURST,
    s_axi_arvalid     => s_axi_in.AR.VALID,
    s_axi_arready     => s_axi_out.AR.READY,
    --
    -- AXI Slave Read Data Channel
    s_axi_rid         => s_axi_out.R.ID,
    s_axi_rdata       => s_axi_out.R.DATA,
    s_axi_rresp       => s_axi_out.R.RESP,
    s_axi_rlast       => s_axi_out.R.LAST,
    s_axi_rvalid      => s_axi_out.R.VALID,
    s_axi_rready      => s_axi_in.R.READY,
    --
    -- AXI Master Write Address Channel
    m_axi_awaddr      => m_axi_out_int.AW.ADDR,
    m_axi_awlen       => m_axi_out_int.AW.LEN,
    m_axi_awsize      => m_axi_out_int.AW.SIZE,
    m_axi_awburst     => m_axi_out_int.AW.BURST,
    m_axi_awprot      => m_axi_out_int.AW.PROT,
    m_axi_awvalid     => m_axi_out_int.AW.VALID,
    m_axi_awready     => m_axi_in_int.AW.READY,
    --m_axi_awid              : out std_logic_vector(C_M_AXI_THREAD_ID_WIDTH-1 downto 0);
    m_axi_awlock      => m_axi_out_int.AW.LOCK(0),
    m_axi_awcache     => m_axi_out_int.AW.CACHE,  -- not listed in pg055-axi-bridge-pcie_v1.06.a.pdf    
    --
    -- AXI Master Write Data Channel
    m_axi_wdata       => m_axi_out_int.W.DATA,
    m_axi_wstrb       => m_axi_out_int.W.STRB,
    m_axi_wlast       => m_axi_out_int.W.LAST,
    m_axi_wvalid      => m_axi_out_int.W.VALID,
    m_axi_wready      => m_axi_in_int.W.READY,
    --
    -- AXI Master Write Response Channel
    m_axi_bresp       => m_axi_in_int.B.RESP,
    m_axi_bvalid      => m_axi_in_int.B.VALID,
    m_axi_bready      => m_axi_out_int.B.READY,
    --
    -- AXI Master Read Address Channel
    m_axi_araddr      => m_axi_out_int.AR.ADDR,
    m_axi_arlen       => m_axi_out_int.AR.LEN,
    m_axi_arsize      => m_axi_out_int.AR.SIZE,
    m_axi_arburst     => m_axi_out_int.AR.BURST,
    m_axi_arprot      => m_axi_out_int.AR.PROT,
    m_axi_arvalid     => m_axi_out_int.AR.VALID,
    m_axi_arready     => m_axi_in_int.AR.READY,
    m_axi_arlock      => m_axi_out_int.AR.LOCK(0),
    m_axi_arcache     => m_axi_out_int.AR.CACHE,
    --
    -- AXI Master Read Data Channel
    m_axi_rdata       => m_axi_in_int.R.DATA,
    m_axi_rresp       => m_axi_in_int.R.RESP,
    m_axi_rlast       => m_axi_in_int.R.LAST,
    m_axi_rvalid      => m_axi_in_int.R.VALID,
    m_axi_rready      => m_axi_out_int.R.READY,
    --
    --
    -- AXI -Lite Interface - CFG Block
    s_axi_ctl_awaddr  => (others => '0'),  --: in  std_logic_vector(31 downto 0); -- AXI Lite Write address
    s_axi_ctl_awvalid => '0',  --: in  std_logic;                     -- AXI Lite Write Address Valid
    s_axi_ctl_awready => open,  --: out std_logic;                     -- AXI Lite Write Address Core ready
    s_axi_ctl_wdata   => (others => '0'),  --: in  std_logic_vector(31 downto 0); -- AXI Lite Write Data
    s_axi_ctl_wstrb   => (others => '0'),  --: in  std_logic_vector(3 downto 0);  -- AXI Lite Write Data strobe
    s_axi_ctl_wvalid  => '0',  --: in  std_logic;                     -- AXI Lite Write data Valid
    s_axi_ctl_wready  => open,  --: out std_logic;                     -- AXI Lite Write Data Core ready
    s_axi_ctl_bresp   => open,  --: out std_logic_vector(1 downto 0);  -- AXI Lite Write Data strobe
    s_axi_ctl_bvalid  => open,  --: out std_logic;                     -- AXI Lite Write data Valid
    s_axi_ctl_bready  => '0',  --: in  std_logic;                     -- AXI Lite Write Data Core ready

    s_axi_ctl_araddr  => (others => '0'),  --: in  std_logic_vector(31 downto 0); -- AXI Lite Read address
    s_axi_ctl_arvalid => '0',  --: in  std_logic;                     -- AXI Lite Read Address Valid
    s_axi_ctl_arready => open,  --: out std_logic;                     -- AXI Lite Read Address Core ready
    s_axi_ctl_rdata   => open,  --: out std_logic_vector(31 downto 0); -- AXI Lite Read Data
    s_axi_ctl_rresp   => open,  --: out std_logic_vector(1 downto 0);  -- AXI Lite Read Data strobe
    s_axi_ctl_rvalid  => open,  --: out std_logic;                     -- AXI Lite Read data Valid
    s_axi_ctl_rready  => '0'  --: in  std_logic                     -- AXI Lite Read Data Core ready
    );

end rtl;
