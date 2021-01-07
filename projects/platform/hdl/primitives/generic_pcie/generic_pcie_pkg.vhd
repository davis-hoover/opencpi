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

library IEEE; use IEEE.std_logic_1164.all, ieee.numeric_std.all;
--library ocpi; use ocpi.types.all;
library axi; use axi.axi_pkg.all;
package generic_pcie_pkg is

-- axi_pcie IP component 
component axi_pcie_0 is
   generic(
      --Family Generics
      C_PCIE_BLK_LOCN               : string  := "0";
      C_XLNX_REF_BOARD              : string  := "NONE";
      C_FAMILY                      : string  := "virtex6";
      C_INSTANCE                    : string  := "AXI_PCIe";
      C_S_AXI_ID_WIDTH              : integer := 4;
      -- C_M_AXI_THREAD_ID_WIDTH       : integer := 4;
      C_S_AXI_ADDR_WIDTH            : integer := 32;
      C_S_AXI_DATA_WIDTH            : integer := 32;
      C_M_AXI_ADDR_WIDTH            : integer := 32;
      C_M_AXI_DATA_WIDTH            : integer := 32;
    
      --PCIe Generics
      C_NO_OF_LANES                 : integer := 1;
      C_MAX_LINK_SPEED              : integer := 0;
                             -- 0 = 2.5 GT/s, 1 = 5.0 GT/s
      C_PCIE_USE_MODE               : string  := "1.0";
      C_DEVICE_ID                   : std_logic_vector := x"0000";
      C_VENDOR_ID                   : std_logic_vector := x"0000";
      C_CLASS_CODE                  : std_logic_vector := x"000000";
      C_REF_CLK_FREQ                : integer := 0;
                             --0 - 100 MHz, 1 - 125 MHz, 2 - 250 MHz
      C_REV_ID                      : std_logic_vector := x"00";
      C_SUBSYSTEM_ID                : std_logic_vector := x"0000";
      C_SUBSYSTEM_VENDOR_ID         : std_logic_vector := x"0000";
      C_PCIE_CAP_SLOT_IMPLEMENTED   : integer := 0;
      C_NUM_MSI_REQ                 : integer := 0;
      C_INTERRUPT_PIN               : integer := 0;
      C_COMP_TIMEOUT                : integer := 0;
      C_INCLUDE_RC                  : integer := 0;
      C_S_AXI_SUPPORTS_NARROW_BURST : integer := 1;
      C_EP_LINK_PARTNER_RCB         : integer := 0;
      C_INCLUDE_BAROFFSET_REG       : integer := 1;
      C_BASEADDR                    : std_logic_vector := x"FFFF_FFFF";
      C_HIGHADDR                    : std_logic_vector := x"0000_0000";
      C_AXIBAR_NUM                  : integer := 6;
      C_AXIBAR2PCIEBAR_0            : std_logic_vector :=x"00000000";
      C_AXIBAR2PCIEBAR_1            : std_logic_vector :=x"00000000";
      C_AXIBAR2PCIEBAR_2            : std_logic_vector :=x"00000000";
      C_AXIBAR2PCIEBAR_3            : std_logic_vector :=x"00000000";
      C_AXIBAR2PCIEBAR_4            : std_logic_vector :=x"00000000";
      C_AXIBAR2PCIEBAR_5            : std_logic_vector :=x"00000000";
      C_AXIBAR_AS_0                 : integer := 0;
      C_AXIBAR_AS_1                 : integer := 0;
      C_AXIBAR_AS_2                 : integer := 0;
      C_AXIBAR_AS_3                 : integer := 0;
      C_AXIBAR_AS_4                 : integer := 0;
      C_AXIBAR_AS_5                 : integer := 0;
      C_AXIBAR_0                    : std_logic_vector := x"FFFF_FFFF";
      C_AXIBAR_HIGHADDR_0           : std_logic_vector := x"0000_0000";
      C_AXIBAR_1                    : std_logic_vector := x"FFFF_FFFF";
      C_AXIBAR_HIGHADDR_1           : std_logic_vector := x"0000_0000";
      C_AXIBAR_2                    : std_logic_vector := x"FFFF_FFFF";
      C_AXIBAR_HIGHADDR_2           : std_logic_vector := x"0000_0000";
      C_AXIBAR_3                    : std_logic_vector := x"FFFF_FFFF";
      C_AXIBAR_HIGHADDR_3           : std_logic_vector := x"0000_0000";
      C_AXIBAR_4                    : std_logic_vector := x"FFFF_FFFF";
      C_AXIBAR_HIGHADDR_4           : std_logic_vector := x"0000_0000";
      C_AXIBAR_5                    : std_logic_vector := x"FFFF_FFFF";
      C_AXIBAR_HIGHADDR_5           : std_logic_vector := x"0000_0000";
      C_PCIEBAR_NUM                 : integer := 3;
      C_PCIEBAR_AS                  : integer := 1;
      C_PCIEBAR_LEN_0               : integer := 16;
      C_PCIEBAR2AXIBAR_0            : std_logic_vector(0 to 31) :=x"00000000";
      C_PCIEBAR2AXIBAR_0_SEC        : integer := 1;
      C_PCIEBAR_LEN_1               : integer := 16;
      C_PCIEBAR2AXIBAR_1            : std_logic_vector(0 to 31) :=x"00000000";
      C_PCIEBAR2AXIBAR_1_SEC        : integer := 1;
      C_PCIEBAR_LEN_2               : integer := 16;
      C_PCIEBAR2AXIBAR_2            : std_logic_vector(0 to 31) :=x"00000000";
      C_PCIEBAR2AXIBAR_2_SEC        : integer := 1
   );
   port(
      -- AXI Global
--      axi_aclk                : in  std_logic; -- AXI clock
      axi_aresetn             : in  std_logic; -- AXI active low synchronous reset
      axi_aclk_out            : out std_logic; -- PCIe clock for AXI clock
--      axi_ctl_aclk            : in  std_logic; -- AXI LITE clock
      axi_ctl_aclk_out        : out std_logic; -- PCIe clock for AXI LITE clock
      mmcm_lock               : out std_logic := '1'; -- MMCM lock signal output
      interrupt_out           : out std_logic; -- active high interrupt out
      INTX_MSI_Request        : in  std_logic; -- Legacy interrupt/initiate MSI (Endpoint only)
      INTX_MSI_Grant          : out std_logic; -- Legacy interrupt/MSI Grant signal (Endpoint only)
      MSI_enable              : out std_logic; -- 1 = MSI, 0 = INTX
      MSI_Vector_Num          : in  std_logic_vector(4 downto 0);
      MSI_Vector_Width        : out std_logic_vector(2 downto 0);

      -- AXI Slave Write Address Channel
      s_axi_awid              : in  std_logic_vector(C_S_AXI_ID_WIDTH-1 downto 0);
      s_axi_awaddr            : in  std_logic_vector(C_S_AXI_ADDR_WIDTH-1 downto 0);
      s_axi_awregion          : in  std_logic_vector(3 downto 0);
      s_axi_awlen             : in  std_logic_vector(7 downto 0);
      s_axi_awsize            : in  std_logic_vector(2 downto 0);
      s_axi_awburst           : in  std_logic_vector(1 downto 0);
      s_axi_awvalid           : in  std_logic;
      s_axi_awready           : out std_logic;

      -- AXI Slave Write Data Channel
      s_axi_wdata             : in  std_logic_vector(C_S_AXI_DATA_WIDTH-1 downto 0);
      s_axi_wstrb             : in  std_logic_vector(C_S_AXI_DATA_WIDTH/8-1 downto 0);
      s_axi_wlast             : in  std_logic;
      s_axi_wvalid            : in  std_logic;
      s_axi_wready            : out std_logic;

      -- AXI Slave Write Response Channel
      s_axi_bid               : out std_logic_vector(C_S_AXI_ID_WIDTH-1 downto 0);
      s_axi_bresp             : out std_logic_vector(1 downto 0);
      s_axi_bvalid            : out std_logic;
      s_axi_bready            : in  std_logic;

      -- AXI Slave Read Address Channel
      s_axi_arid              : in  std_logic_vector(C_S_AXI_ID_WIDTH-1 downto 0);
      s_axi_araddr            : in  std_logic_vector(C_S_AXI_ADDR_WIDTH-1 downto 0);
      s_axi_arregion          : in  std_logic_vector(3 downto 0);
      s_axi_arlen             : in  std_logic_vector(7 downto 0);
      s_axi_arsize            : in  std_logic_vector(2 downto 0);
      s_axi_arburst           : in  std_logic_vector(1 downto 0);
      s_axi_arvalid           : in  std_logic;
      s_axi_arready           : out std_logic;

      -- AXI Slave Read Data Channel
      s_axi_rid               : out std_logic_vector(C_S_AXI_ID_WIDTH-1 downto 0);
      s_axi_rdata             : out std_logic_vector(C_S_AXI_DATA_WIDTH-1 downto 0);
      s_axi_rresp             : out std_logic_vector(1 downto 0);
      s_axi_rlast             : out std_logic;
      s_axi_rvalid            : out std_logic;
      s_axi_rready            : in  std_logic;

      -- AXI Master Write Address Channel
      m_axi_awaddr            : out std_logic_vector(C_M_AXI_ADDR_WIDTH-1 downto 0);
      m_axi_awlen             : out std_logic_vector(7 downto 0);
      m_axi_awsize            : out std_logic_vector(2 downto 0);
      m_axi_awburst           : out std_logic_vector(1 downto 0);
      m_axi_awprot            : out std_logic_vector(2 downto 0);
      m_axi_awvalid           : out std_logic;
      m_axi_awready           : in  std_logic;
      --m_axi_awid              : out std_logic_vector(C_M_AXI_THREAD_ID_WIDTH-1 downto 0);
      m_axi_awlock            : out std_logic;
      m_axi_awcache           : out std_logic_vector(3 downto 0);

      -- AXI Master Write Data Channel
      m_axi_wdata             : out std_logic_vector(C_M_AXI_DATA_WIDTH-1 downto 0);
      m_axi_wstrb             : out std_logic_vector(C_M_AXI_DATA_WIDTH/8-1 downto 0);
      m_axi_wlast             : out std_logic;
      m_axi_wvalid            : out std_logic;
      m_axi_wready            : in  std_logic;

      -- AXI Master Write Response Channel
      m_axi_bresp             : in  std_logic_vector(1 downto 0);
      m_axi_bvalid            : in  std_logic;
      m_axi_bready            : out std_logic;

      -- AXI Master Read Address Channel
      --m_axi_arid              : out std_logic_vector(C_M_AXI_THREAD_ID_WIDTH-1 downto 0);
      m_axi_araddr            : out std_logic_vector(C_M_AXI_ADDR_WIDTH-1 downto 0);
      m_axi_arlen             : out std_logic_vector(7 downto 0);
      m_axi_arsize            : out std_logic_vector(2 downto 0);
      m_axi_arburst           : out std_logic_vector(1 downto 0);
      m_axi_arprot            : out std_logic_vector(2 downto 0);
      m_axi_arvalid           : out std_logic;
      m_axi_arready           : in  std_logic;
      m_axi_arlock            : out std_logic;
      m_axi_arcache           : out std_logic_vector(3 downto 0);

      -- AXI Master Read Data Channel
      m_axi_rdata             : in  std_logic_vector(C_M_AXI_DATA_WIDTH-1 downto 0);
      m_axi_rresp             : in  std_logic_vector(1 downto 0);
      m_axi_rlast             : in  std_logic;
      m_axi_rvalid            : in  std_logic;
      m_axi_rready            : out std_logic;

      -- PCI Express (pci_exp) Interface
      -- Tx
      pci_exp_txp             : out std_logic_vector(C_NO_OF_LANES-1 downto 0);
      pci_exp_txn             : out std_logic_vector(C_NO_OF_LANES-1 downto 0);
      -- Rx
      pci_exp_rxp             : in  std_logic_vector(C_NO_OF_LANES-1 downto 0);
      pci_exp_rxn             : in  std_logic_vector(C_NO_OF_LANES-1 downto 0);
      REFCLK                  : in  std_logic;
      

      -- AXI -Lite Interface - CFG Block
      s_axi_ctl_awaddr        : in  std_logic_vector(31 downto 0); -- AXI Lite Write address
      s_axi_ctl_awvalid       : in  std_logic;                     -- AXI Lite Write Address Valid
      s_axi_ctl_awready       : out std_logic;                     -- AXI Lite Write Address Core ready
      s_axi_ctl_wdata         : in  std_logic_vector(31 downto 0); -- AXI Lite Write Data
      s_axi_ctl_wstrb         : in  std_logic_vector(3 downto 0);  -- AXI Lite Write Data strobe
      s_axi_ctl_wvalid        : in  std_logic;                     -- AXI Lite Write data Valid
      s_axi_ctl_wready        : out std_logic;                     -- AXI Lite Write Data Core ready
      s_axi_ctl_bresp         : out std_logic_vector(1 downto 0);  -- AXI Lite Write Data strobe
      s_axi_ctl_bvalid        : out std_logic;                     -- AXI Lite Write data Valid
      s_axi_ctl_bready        : in  std_logic;                     -- AXI Lite Write Data Core ready

      s_axi_ctl_araddr        : in  std_logic_vector(31 downto 0); -- AXI Lite Read address
      s_axi_ctl_arvalid       : in  std_logic;                     -- AXI Lite Read Address Valid
      s_axi_ctl_arready       : out std_logic;                     -- AXI Lite Read Address Core ready
      s_axi_ctl_rdata         : out std_logic_vector(31 downto 0); -- AXI Lite Read Data
      s_axi_ctl_rresp         : out std_logic_vector(1 downto 0);  -- AXI Lite Read Data strobe
      s_axi_ctl_rvalid        : out std_logic;                     -- AXI Lite Read data Valid
      s_axi_ctl_rready        : in  std_logic                     -- AXI Lite Read Data Core ready
   );
end component axi_pcie_0;
-- END

type pcie_out_t is record
  pcie_txp     : std_logic_vector(0 downto 0);      -- PCIe transmit TODO: Generalize num lanes
  pcie_txn     : std_logic_vector(0 downto 0);      -- PCIe transmit TODO: Generalize num lanes
end record pcie_out_t;

type pcie_in_t is record
  pcie_rxp     : std_logic_vector(0 downto 0);      -- PCIe receive TODO: Generalize num lanes
  pcie_rxn     : std_logic_vector(0 downto 0);      -- PCIe receive TODO: Generalize num lanes
end record pcie_in_t;

type msi_in_t is record
  -- TODO: Generalize the MSI support
  intx_msi_request        : std_logic;                    -- Legacy interrupt/initiate MSI (Endpoint only)
  msi_vector_num          : std_logic_vector(4 downto 0);
end record msi_in_t;

type msi_out_t is record
  -- TODO: Generalize the MSI support
  intx_msi_grant          : std_logic;                    -- Legacy interrupt/MSI Grant signal (Endpoint only)
  msi_enable              : std_logic;                    -- 1 = MSI, 0 = INTX
  msi_vector_width        : std_logic_vector(2 downto 0);
end record msi_out_t;

type global_in_t is record
  refclk                  : std_logic;
  axi_aresetn             : std_logic; 
end record global_in_t;

type global_out_t is record
  axi_aclk_out            : std_logic;
  axi_ctl_aclk_out        : std_logic;
  mmcm_lock           : std_logic;
  interrupt_out       : std_logic;
end record global_out_t;

end package generic_pcie_pkg;
