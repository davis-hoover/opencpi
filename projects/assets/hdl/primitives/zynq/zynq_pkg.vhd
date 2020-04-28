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

-- This file contains zynq-specific definitions that have nothing to do with the
-- particulars of the zed or any other platform.
-- THe processor interface just has I/O ports that OpenCPI uses.

library IEEE; use IEEE.std_logic_1164.all, ieee.numeric_std.all;
library axi;
package zynq_pkg is

constant C_M_AXI_GP_COUNT : natural := 2;
constant C_S_AXI_HP_COUNT : natural := 4;

type ps2pl_t is record
  FCLK         : std_logic_vector(3 downto 0);
  FCLKRESET_N  : std_logic;
end record ps2pl_t;
type pl2ps_t is record
  DEBUG        : std_logic_vector(31 downto 0); --     FTMT_F2P_DEBUG
end record pl2ps_t;

component zynq_ps is
  generic (package_name : string  := "clg484";
           dq_width     : natural := 32);
  port    (ps_in        : in  pl2ps_t;
           ps_out       : out ps2pl_t;
           m_axi_gp_in  : in  axi.zynq_7000_m_gp.axi_s2m_array_t(0 to C_M_AXI_GP_COUNT-1);
           m_axi_gp_out : out axi.zynq_7000_m_gp.axi_m2s_array_t(0 to C_M_AXI_GP_COUNT-1);
           s_axi_hp_in  : in  axi.zynq_7000_s_hp.axi_m2s_array_t(0 to C_S_AXI_HP_COUNT-1);
           s_axi_hp_out : out axi.zynq_7000_s_hp.axi_s2m_array_t(0 to C_S_AXI_HP_COUNT-1));
end component zynq_ps;

end package zynq_pkg;
