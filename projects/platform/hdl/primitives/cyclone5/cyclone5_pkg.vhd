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
  constant C_F2H_AXI_COUNT : natural := 1;
  constant C_H2F_AXI_COUNT : natural := 1;

  type hps_in_t is record
    CLK  : std_logic;
  end record hps_in_t;

  type hps_out_t is record
    h2f_rst_n        : std_logic;
    h2f_cold_rst_n   : std_logic;
    h2f_user0_clk    : std_logic;
  end record hps_out_t;

  component cyclone5_hps is
    port    (hps_in        : in  hps_in_t;
             hps_out       : out hps_out_t;
             -- master
             h2f_axi_in    : in  axi.cyclone5_h2f.axi_s2m_array_t(0 to C_H2F_AXI_COUNT-1);
             h2f_axi_out   : out axi.cyclone5_h2f.axi_m2s_array_t(0 to C_H2F_AXI_COUNT-1);
             -- slave
             f2h_axi_in    : in  axi.cyclone5_f2h.axi_m2s_array_t(0 to C_F2H_AXI_COUNT-1);
             f2h_axi_out   : out axi.cyclone5_f2h.axi_s2m_array_t(0 to C_F2H_AXI_COUNT-1)
             );
  end component cyclone5_hps;

end package cyclone5_pkg;
