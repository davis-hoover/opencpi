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

-- This file contains cyclone v specific definitions that have nothing to do with the
-- particulars of the zed or any other platform.
-- THe processor interface just has I/O ports that OpenCPI uses.

library ieee; use IEEE.std_logic_1164.all; use ieee.numeric_std.all;
library axi;
package cyclone5_pkg is
  constant C_M_AXI_COUNT : natural := 1;
  constant C_S_AXI_COUNT : natural := 1;

  type pl2hps_t is record
    CLK  : std_logic;
    oct_rzqin : std_logic;
    --F2H_IRQ0  : std_logic_vector(31 downto 0);
    --F2H_IRQ1  : std_logic_vector(31 downto 0);
  end record pl2hps_t;

  type hps2pl_t is record
    RESET_N   : std_logic;
    COLD_RST  : std_logic;
    DBG_RST   : std_logic;
    WARM_RST  : std_logic;
  end record hps2pl_t;

  type hps_io_t is record
    hps_io_emac1_inst_MDIO   : std_logic;
    hps_io_qspi_inst_IO0     : std_logic;
    hps_io_qspi_inst_IO1     : std_logic;
    hps_io_qspi_inst_IO2     : std_logic;
    hps_io_qspi_inst_IO3     : std_logic;
    hps_io_sdio_inst_CMD     : std_logic;
    hps_io_sdio_inst_D0      : std_logic;
    hps_io_sdio_inst_D1      : std_logic;
    hps_io_sdio_inst_D2      : std_logic;
    hps_io_sdio_inst_D3      : std_logic;
    hps_io_usb1_inst_D0      : std_logic;
    hps_io_usb1_inst_D1      : std_logic;
    hps_io_usb1_inst_D2      : std_logic;
    hps_io_usb1_inst_D3      : std_logic;
    hps_io_usb1_inst_D4      : std_logic;
    hps_io_usb1_inst_D5      : std_logic;
    hps_io_usb1_inst_D6      : std_logic;
    hps_io_usb1_inst_D7      : std_logic;
    hps_io_gpio_inst_GPIO09  : std_logic;
    hps_io_gpio_inst_GPIO35  : std_logic;
    hps_io_gpio_inst_GPIO41  : std_logic;
    hps_io_gpio_inst_GPIO42  : std_logic;
    hps_io_gpio_inst_GPIO43  : std_logic;
    hps_io_gpio_inst_GPIO44  : std_logic;
  end record hps_io_t;

  component cyclone5_hps is
    port    (hps_in        : in  pl2hps_t;
             hps_out       : out hps2pl_t;
             hps_inout     : inout hps_io_t;
             m_h2f_axi_in  : in  axi.cyclone5_m.axi_s2m_array_t(0 to C_M_AXI_COUNT-1);
             m_h2f_axi_out : out axi.cyclone5_m.axi_m2s_array_t(0 to C_M_AXI_COUNT-1);
             s_f2h_axi_in  : in  axi.cyclone5_s.axi_m2s_array_t(0 to C_S_AXI_COUNT-1);
             s_f2h_axi_out : out axi.cyclone5_s.axi_s2m_array_t(0 to C_S_AXI_COUNT-1)
             );
  end component cyclone5_hps;

end package cyclone5_pkg;
