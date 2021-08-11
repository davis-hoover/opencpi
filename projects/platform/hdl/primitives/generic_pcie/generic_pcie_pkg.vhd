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
  mmcm_lock               : std_logic;
  interrupt_out           : std_logic;
  user_link_up            : std_logic;                    -- Indicates PCIe link is in L0 state 
end record global_out_t;

component generic_pcie is
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
    m_axi_in    : in  axi.pcie_m.axi_s2m_t;
    m_axi_out   : out axi.pcie_m.axi_m2s_t;
    -- Slave (x1)
    s_axi_in    : in  axi.pcie_s.axi_m2s_t;
    s_axi_out   : out axi.pcie_s.axi_s2m_t
  );
end component generic_pcie;

end package generic_pcie_pkg;
